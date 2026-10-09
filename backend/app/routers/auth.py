from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from .. import security
from .. import models
from .. import schemas
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/registro", status_code=status.HTTP_201_CREATED, response_model=schemas.UsuarioOut)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    # 1. Verificar si el correo ya existe
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )


    # 2. Encriptar la contraseña
    hashed_pwd = security.hash_password(usuario.password)

    # 3. Guardar el usuario. SEGURIDAD: el registro público SIEMPRE crea un "Usuario" normal;
    #    ignoramos el rol_id/refugio_id que llegue desde fuera (si no, cualquiera se haría admin).
    nuevo_usuario = models.Usuario(
        nombre_completo=usuario.nombre_completo,
        email=usuario.email,
        password_hash=hashed_pwd,
        rol_id=security.ROL_USUARIO,
        refugio_id=None
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.post("/login", response_model=schemas.Token)
def login(credenciales: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == credenciales.username).first()
    if not usuario or not security.verify_password(credenciales.password, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Credenciales incorrectas")

    access_token = security.create_access_token(data={"usuario_id": usuario.id, "rol_id": usuario.rol_id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UsuarioOut)
def mi_perfil(usuario: models.Usuario = Depends(security.get_current_user)):
    return usuario