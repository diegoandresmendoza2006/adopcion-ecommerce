from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from .. import imagenes, models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/imagenes", tags=["Imágenes"])


@router.post("/", response_model=schemas.ImagenSubida, status_code=status.HTTP_201_CREATED)
async def subir_imagen(
    archivo: UploadFile = File(...),
    tipo: str = Form(..., description="mascotas | productos"),
    subcarpeta: str = Form("", max_length=80, description="Raza (mascotas) o categoría (productos)"),
    especie: str = Form("", max_length=30, description="Solo para mascotas"),
    usuario: models.Usuario = Depends(security.require_staff),
):
    if tipo not in imagenes.TIPOS:
        raise HTTPException(status_code=422, detail="El tipo debe ser 'mascotas' o 'productos'")
    if not imagenes.configurado():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="El servidor no tiene configurado Cloudinary (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY y CLOUDINARY_API_SECRET)")

    contenido = await archivo.read(imagenes.MAX_BYTES + 1)
    if len(contenido) > imagenes.MAX_BYTES:
        raise HTTPException(status_code=413, detail="La imagen no puede pesar más de 5 MB")
    if not imagenes.tipo_real(contenido):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Solo se permiten imágenes JPG, PNG o WEBP")

    carpeta = imagenes.carpeta_para(tipo, usuario.id, subcarpeta, especie)
    try:
        url, public_id = imagenes.subir(contenido, carpeta)
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="No se pudo subir la imagen a Cloudinary")
    return {"url": url, "public_id": public_id}


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def descartar_imagen(url: str = Query(..., max_length=500), db: Session = Depends(get_db),
                     _: models.Usuario = Depends(security.require_staff)):
    """Borra una foto que se subió pero NO llegó a guardarse (el usuario la cambió o canceló el formulario).
    Si alguna mascota o producto ya la usa, no se toca."""
    if imagenes.en_uso(db, url):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esa imagen está en uso")
    imagenes.borrar(url)
    return Response(status_code=status.HTTP_204_NO_CONTENT)