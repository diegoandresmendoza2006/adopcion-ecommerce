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
# La clave sale de backend/.env (línea SECRET_KEY=...). Es OBLIGATORIA: sin ella cualquiera
# podría fabricar tokens válidos, así que la app se niega a arrancar si falta o es corta.
SECRET_KEY = os.getenv("SECRET_KEY", "")
if len(SECRET_KEY) < 16:
    raise RuntimeError(
        "Falta SECRET_KEY en backend/.env (mínimo 16 caracteres). "
        "Genera una con: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )

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


# ---------- Enlaces temporales de descarga ----------
# El navegador no puede mandar la cabecera Authorization al abrir un enlace, así que el servidor
# entrega una ruta con un token de vida muy corta que sirve SOLO para ese archivo (no abre sesión).
MINUTOS_DESCARGA = 5


def crear_token_descarga(recurso: str, usuario_id: int, datos: dict = None) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_DESCARGA)
    return jwt.encode({"descarga": recurso, "uid": usuario_id, "datos": datos or {}, "exp": expira},
                      SECRET_KEY, algorithm=ALGORITHM)


def leer_token_descarga(token: str, recurso: str) -> dict:
    """Devuelve {'uid':..., 'datos':...} o lanza 401 si el enlace venció o es de otro archivo."""
    try:
        carga = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        carga = {}
    if carga.get("descarga") != recurso:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="El enlace de descarga venció. Vuelve a pedirlo desde la app.")
    return carga


def cuentas_del_token(token: str = Depends(oauth2_scheme)) -> list:
    """Ids de las cuentas que esta sesión puede usar (la persona inició sesión con la contraseña de todas)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida o expirada",
                            headers={"WWW-Authenticate": "Bearer"})
    ids = payload.get("cuentas")
    if not ids and payload.get("usuario_id") is not None:
        ids = [payload["usuario_id"]]
    return [int(i) for i in (ids or [])]


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