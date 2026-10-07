import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .database import get_db
from . import models

load_dotenv()

# La clave ahora sale del archivo backend/.env  (agrega la línea SECRET_KEY=lo-que-quieras)
SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esta-clave-en-el-archivo-env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# IDs de la tabla adopcion.roles  (verifica que coincidan con tu base de datos)
ROL_ADMIN = 1
ROL_ENCARGADO = 2
ROL_USUARIO = 3

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.Usuario:
    """Valida el token JWT y devuelve el usuario logueado."""
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión inválida o expirada",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = payload.get("usuario_id")
    except JWTError:
        raise error
    if usuario_id is None:
        raise error
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise error
    return usuario


def require_roles(*roles: int):
    """Uso: Depends(require_roles(ROL_ADMIN, ROL_ENCARGADO))"""
    def checker(usuario: models.Usuario = Depends(get_current_user)) -> models.Usuario:
        if usuario.rol_id not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para esta acción")
        return usuario
    return checker


require_staff = require_roles(ROL_ADMIN, ROL_ENCARGADO)
require_admin = require_roles(ROL_ADMIN)
require_usuario = require_roles(ROL_USUARIO)