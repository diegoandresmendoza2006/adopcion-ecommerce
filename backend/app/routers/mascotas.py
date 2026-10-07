from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import schemas
from .. import models
from .. import security
from ..database import get_db

router = APIRouter(prefix="/mascotas", tags=["Mascotas"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.MascotaOut)
def crear_mascota(mascota: schemas.MascotaCreate, db: Session = Depends(get_db),
                  usuario: models.Usuario = Depends(security.require_staff)):
    # Un encargado solo puede registrar mascotas en SU refugio
    refugio_id = mascota.refugio_id
    if usuario.rol_id == security.ROL_ENCARGADO and usuario.refugio_id:
        refugio_id = usuario.refugio_id

    refugio = db.query(models.Refugio).filter(models.Refugio.id == refugio_id).first()
    if not refugio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El refugio especificado no existe")

    nueva_mascota = models.Mascota(
        nombre=mascota.nombre,
        especie=mascota.especie,
        raza=mascota.raza,
        edad_meses=mascota.edad_meses,
        descripcion=mascota.descripcion,
        estado_adopcion=mascota.estado_adopcion,
        refugio_id=refugio_id,
        imagen_url=mascota.imagen_url
    )
    db.add(nueva_mascota)
    db.commit()
    db.refresh(nueva_mascota)
    return nueva_mascota


@router.get("/", response_model=List[schemas.MascotaOut])
def obtener_mascotas(especie: Optional[str] = None, estado: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Mascota)
    if especie:
        query = query.filter(models.Mascota.especie.ilike(f"%{especie}%"))
    if estado:
        query = query.filter(models.Mascota.estado_adopcion.ilike(f"%{estado}%"))
    return query.order_by(models.Mascota.id).all()


# IMPORTANTE: esta ruta fija va ANTES de "/{mascota_id}" para que no se confunda con un id
@router.get("/gestion/inventario", response_model=List[schemas.MascotaOut])
def inventario_del_refugio(db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.require_staff)):
    query = db.query(models.Mascota)
    if usuario.rol_id == security.ROL_ENCARGADO and usuario.refugio_id:
        query = query.filter(models.Mascota.refugio_id == usuario.refugio_id)
    return query.order_by(models.Mascota.id).all()


@router.get("/{mascota_id}", response_model=schemas.MascotaOut)
def obtener_mascota(mascota_id: int, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La mascota no existe")
    return mascota