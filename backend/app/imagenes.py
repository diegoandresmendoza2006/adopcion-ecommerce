"""Manejo de fotos en Cloudinary desde el SERVIDOR (firmado con la clave secreta).

Por qué aquí y no en Angular: borrar una imagen en Cloudinary exige la API Secret, y esa clave
jamás puede viajar al navegador. Por eso Angular le manda la foto al backend, y el backend:
  1. la sube a una carpeta ordenada (jerarquía abajo),
  2. borra la foto vieja cuando se reemplaza o se quita,
  3. borra la foto cuando se elimina la mascota o el producto.
Así no quedan imágenes huérfanas ("basura") en Cloudinary.

Jerarquía de carpetas (todo cuelga de content/pawsshop):
    content/pawsshop/mascotas/<especie>/<raza>/user_<id>/<uuid>
    content/pawsshop/productos/<categoria>/user_<id>/<uuid>
"""
import logging
import os
import re
import unicodedata
import uuid
from typing import Optional, Tuple
from urllib.parse import unquote

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from . import models

load_dotenv()
log = logging.getLogger(__name__)

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
RAIZ = os.getenv("CLOUDINARY_ROOT_FOLDER", "content/pawsshop").strip("/")

TIPOS = ("mascotas", "productos")
MAX_BYTES = 5 * 1024 * 1024


def configurado() -> bool:
    return bool(CLOUD_NAME and API_KEY and API_SECRET)


def _cloudinary():
    """Importa el SDK y lo configura solo cuando de verdad se necesita."""
    import cloudinary
    import cloudinary.uploader
    cloudinary.config(cloud_name=CLOUD_NAME, api_key=API_KEY, api_secret=API_SECRET, secure=True)
    return cloudinary.uploader


def slug(texto: Optional[str], por_defecto: str = "sin-clasificar") -> str:
    """'Pastor Alemán' -> 'pastor-aleman' (carpetas sin tildes, espacios ni símbolos)."""
    if not texto:
        return por_defecto
    limpio = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    limpio = re.sub(r"[^a-zA-Z0-9]+", "-", limpio).strip("-").lower()
    return limpio[:40] or por_defecto


def carpeta_para(tipo: str, usuario_id: int, subcarpeta: Optional[str] = None, especie: Optional[str] = None) -> str:
    if tipo == "mascotas":
        return f"{RAIZ}/mascotas/{slug(especie, 'otro')}/{slug(subcarpeta, 'mestizo')}/user_{usuario_id}"
    return f"{RAIZ}/productos/{slug(subcarpeta)}/user_{usuario_id}"


def tipo_real(contenido: bytes) -> Optional[str]:
    """Mira los primeros bytes (no confía en la extensión ni en lo que diga el navegador)."""
    if contenido.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if contenido.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "webp"
    return None


def subir(contenido: bytes, carpeta: str) -> Tuple[str, str]:
    """Sube la imagen y devuelve (url_https, public_id)."""
    public_id = f"{carpeta}/{uuid.uuid4().hex}"
    r = _cloudinary().upload(contenido, public_id=public_id, asset_folder=carpeta,
                             resource_type="image", overwrite=False)
    return r["secure_url"], r["public_id"]


def public_id_de(url: Optional[str]) -> Optional[str]:
    """Saca el public_id de una URL de NUESTRA cuenta de Cloudinary. Con cualquier otra URL devuelve None."""
    if not url or not CLOUD_NAME:
        return None
    m = re.match(rf"^https?://res\.cloudinary\.com/{re.escape(CLOUD_NAME)}/image/upload/(?:v\d+/)?(.+?)(?:\.[A-Za-z0-9]+)?$", url.split("?")[0])
    return unquote(m.group(1)) if m else None


def en_uso(db: Session, url: str) -> bool:
    return bool(db.query(models.Mascota.id).filter(models.Mascota.imagen_url == url).first()
                or db.query(models.Producto.id).filter(models.Producto.imagen_url == url).first())


def borrar(url: Optional[str]) -> bool:
    """Borra la imagen en Cloudinary. Nunca lanza error: si falla, queda en el log y la app sigue."""
    pid = public_id_de(url)
    if not pid or not configurado():
        return False
    try:
        r = _cloudinary().destroy(pid, resource_type="image", invalidate=True)
        return r.get("result") in ("ok", "not found")
    except Exception:   # la API de Cloudinary no debe tumbar un guardado/borrado que sí funcionó
        log.exception("No se pudo borrar la imagen %s", pid)
        return False


def limpiar(db: Session, url_vieja: Optional[str]) -> None:
    """Borra la foto vieja SOLO si ya nadie la usa (llamar después del commit)."""
    if url_vieja and not en_uso(db, url_vieja):
        borrar(url_vieja)