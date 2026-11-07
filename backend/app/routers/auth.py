import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import imagenes, models, schemas, security
from ..database import get_db

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticación"])

NOMBRE_ROL = {security.ROL_ADMIN: "Administrador", security.ROL_ENCARGADO: "Encargado", security.ROL_USUARIO: "Usuario"}


def _cuenta(u: models.Usuario) -> schemas.CuentaOut:
    return schemas.CuentaOut(usuario_id=u.id, rol_id=u.rol_id, rol=NOMBRE_ROL.get(u.rol_id, "Usuario"),
                             refugio_id=u.refugio_id)


def _token_para(usuario: models.Usuario, cuentas: List[models.Usuario]) -> dict:
    token = security.create_access_token(
        data={"usuario_id": usuario.id, "rol_id": usuario.rol_id, "cuentas": [c.id for c in cuentas]})
    return {"access_token": token, "token_type": "bearer", "cuentas": [_cuenta(c) for c in cuentas]}


def _documento_ocupado(db: Session, tipo: Optional[str], numero: Optional[str], email: str) -> bool:
    """¿Ese documento ya lo usa OTRA persona (otro correo)? Dos cuentas con el mismo correo son la misma persona."""
    if not tipo or not numero:
        return False
    return db.query(models.Usuario.id).filter(
        models.Usuario.tipo_documento == tipo, models.Usuario.numero_documento == numero.upper(),
        models.Usuario.email != email).first() is not None


@router.post("/registro", status_code=status.HTTP_201_CREATED, response_model=schemas.UsuarioOut)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    # 1. ¿El correo ya existe?
    existentes = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).all()
    if any(u.rol_id == security.ROL_USUARIO for u in existentes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado")
    if existentes:
        # Doble rol: este correo es de un Encargado/Administrador que quiere crear TAMBIÉN su cuenta de
        # Usuario. Para probar que es él, debe escribir la misma contraseña de su cuenta actual.
        if not security.verify_password(usuario.password, existentes[0].password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este correo ya tiene una cuenta de personal. Para crear también tu cuenta de usuario "
                       "escribe la misma contraseña de esa cuenta.")

    # 2. Un documento solo puede pertenecer a una persona
    numero = usuario.numero_documento.upper() if usuario.numero_documento else None
    if _documento_ocupado(db, usuario.tipo_documento, numero, usuario.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ese documento ya está registrado con otro correo")

    # 3. Guardar. SEGURIDAD: el registro público SIEMPRE crea un "Usuario" normal;
    #    ignoramos el rol_id/refugio_id que llegue desde fuera (si no, cualquiera se haría admin).
    nuevo_usuario = models.Usuario(
        nombre_completo=usuario.nombre_completo,
        email=usuario.email,
        password_hash=security.hash_password(usuario.password),
        rol_id=security.ROL_USUARIO,
        refugio_id=None,
        fecha_nacimiento=usuario.fecha_nacimiento,
        telefono=usuario.telefono,
        direccion=usuario.direccion,
        tipo_documento=usuario.tipo_documento,
        numero_documento=numero,
        # Si ya tenía una cuenta de personal, conserva su foto
        foto_url=existentes[0].foto_url if existentes else None,
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.post("/login", response_model=schemas.Token)
def login(credenciales: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    todas = db.query(models.Usuario).filter(models.Usuario.email == credenciales.username).all()
    validas = [u for u in todas if security.verify_password(credenciales.password, u.password_hash)]
    if not validas:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Entra por defecto con la cuenta de más privilegio (1 = admin ... 3 = usuario);
    # si hay más de una, la app deja elegir con /auth/cambiar-rol.
    validas.sort(key=lambda u: u.rol_id)
    return _token_para(validas[0], validas)


@router.get("/me", response_model=schemas.UsuarioOut)
def mi_perfil(usuario: models.Usuario = Depends(security.get_current_user)):
    return usuario


@router.get("/cuentas", response_model=List[schemas.CuentaOut])
def mis_cuentas(ids: List[int] = Depends(security.cuentas_del_token), db: Session = Depends(get_db)):
    cuentas = db.query(models.Usuario).filter(models.Usuario.id.in_(ids)).order_by(models.Usuario.rol_id).all()
    return [_cuenta(c) for c in cuentas]


@router.post("/cambiar-rol", response_model=schemas.Token)
def cambiar_rol(datos: schemas.CambiarRol, ids: List[int] = Depends(security.cuentas_del_token),
                db: Session = Depends(get_db)):
    """Cambia de cuenta (p. ej. de Encargado a Usuario) sin volver a escribir la contraseña.
    Solo sirve para cuentas con las que ya se inició sesión (van dentro del token)."""
    if datos.usuario_id not in ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esa cuenta no es tuya")
    cuentas = db.query(models.Usuario).filter(models.Usuario.id.in_(ids)).order_by(models.Usuario.rol_id).all()
    elegida = next((c for c in cuentas if c.id == datos.usuario_id), None)
    if not elegida:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La cuenta no existe")
    return _token_para(elegida, cuentas)


# ----------------------------------------------------------------------------
# PERFIL: editar datos personales, contraseña y foto
# Los cambios se aplican a TODAS las cuentas de la persona (mismo correo y contraseña).
# ----------------------------------------------------------------------------
def _mis_cuentas(db: Session, ids: List[int]) -> List[models.Usuario]:
    return db.query(models.Usuario).filter(models.Usuario.id.in_(ids)).all()


@router.put("/me", response_model=schemas.UsuarioOut)
def editar_perfil(datos: schemas.PerfilUpdate, usuario: models.Usuario = Depends(security.get_current_user),
                  ids: List[int] = Depends(security.cuentas_del_token), db: Session = Depends(get_db)):
    cambios = {k: v for k, v in datos.model_dump(exclude_unset=True).items()
               if v is not None or k in ("telefono", "direccion", "fecha_nacimiento")}
    tipo = cambios.get("tipo_documento", usuario.tipo_documento)
    numero = cambios.get("numero_documento", usuario.numero_documento)
    if ("tipo_documento" in cambios) != ("numero_documento" in cambios):
        raise HTTPException(status_code=422, detail="Indica el tipo y el número de documento")
    if numero:
        numero = numero.upper()
        cambios["numero_documento"] = numero
    if "numero_documento" in cambios and _documento_ocupado(db, tipo, numero, usuario.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ese documento ya está registrado con otro correo")
    for cuenta in _mis_cuentas(db, ids):
        for campo, valor in cambios.items():
            setattr(cuenta, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_password(datos: schemas.CambioPassword, usuario: models.Usuario = Depends(security.get_current_user),
                     ids: List[int] = Depends(security.cuentas_del_token), db: Session = Depends(get_db)):
    if not security.verify_password(datos.actual, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La contraseña actual no es correcta")
    nueva = security.hash_password(datos.nueva)
    for cuenta in _mis_cuentas(db, ids):
        # Solo se cambia en las cuentas que compartían la contraseña actual
        if security.verify_password(datos.actual, cuenta.password_hash):
            cuenta.password_hash = nueva
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/me/foto", response_model=schemas.UsuarioOut)
async def subir_foto_perfil(archivo: UploadFile = File(...),
                            usuario: models.Usuario = Depends(security.get_current_user),
                            ids: List[int] = Depends(security.cuentas_del_token), db: Session = Depends(get_db)):
    """Pone (o cambia) la foto de perfil. La foto anterior se borra de Cloudinary."""
    if not imagenes.configurado():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="El servidor no tiene configurado Cloudinary")
    contenido = await archivo.read(imagenes.MAX_BYTES + 1)
    if len(contenido) > imagenes.MAX_BYTES:
        raise HTTPException(status_code=413, detail="La imagen no puede pesar más de 5 MB")
    if not imagenes.tipo_real(contenido):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Solo se permiten imágenes JPG, PNG o WEBP")
    try:
        url, _ = imagenes.subir(contenido, imagenes.carpeta_para("perfiles", usuario.id))
    except Exception as e:
        log.exception("Falló la subida de la foto de perfil")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"No se pudo subir la imagen ({type(e).__name__})")
    vieja = usuario.foto_url
    for cuenta in _mis_cuentas(db, ids):
        cuenta.foto_url = url
    db.commit()
    db.refresh(usuario)
    imagenes.limpiar(db, vieja)
    return usuario


@router.delete("/me/foto", response_model=schemas.UsuarioOut)
def quitar_foto_perfil(usuario: models.Usuario = Depends(security.get_current_user),
                       ids: List[int] = Depends(security.cuentas_del_token), db: Session = Depends(get_db)):
    vieja = usuario.foto_url
    for cuenta in _mis_cuentas(db, ids):
        cuenta.foto_url = None
    db.commit()
    db.refresh(usuario)
    imagenes.limpiar(db, vieja)
    return usuario
