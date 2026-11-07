import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine
from .routers import productos
from .routers import auth
from .routers import refugios
from .routers import mascotas
from .routers import adopciones
from .routers import compras
from .routers import seguimientos
from .routers import admin
from .routers import imagenes
from .routers import favoritos
from .routers import descargas
from sqlalchemy import text
from .database import SessionLocal

app = FastAPI(title="API - Adopción y E-commerce")

# Orígenes (páginas web) que pueden llamar a esta API.
# Local: Angular en localhost:4200. En producción define CORS_ORIGINS en el servidor con la
# dirección de tu frontend, separando varias con comas. Ej: https://paws-shop.onrender.com
_origenes = ["http://localhost:4200", "http://127.0.0.1:4200"]
_origenes += [o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origenes,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],   # la app móvil lee el total de filas de esta cabecera
)

# Incluimos todos los routers incluyendo productos
app.include_router(auth.router)
app.include_router(refugios.router)
app.include_router(mascotas.router)
app.include_router(adopciones.router)
app.include_router(productos.router)
app.include_router(compras.router)
app.include_router(seguimientos.router)
app.include_router(admin.router)
app.include_router(imagenes.router)
app.include_router(favoritos.router)
app.include_router(descargas.router)

@app.get("/health", tags=["Sonda"])
def health():
    """Sonda de salud. La consulta un programador (GitHub Actions / UptimeRobot) a la hora o intervalo que quieras:
    despierta el servidor de Render y la base de datos de Neon antes de que alguien abra la app."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"estado": "ok", "base_de_datos": "ok"}
    except Exception:
        return {"estado": "ok", "base_de_datos": "sin conexion"}


@app.get("/")
def read_root():
    return {"mensaje": "¡FastAPI conectado a PostgreSQL exitosamente!"}
