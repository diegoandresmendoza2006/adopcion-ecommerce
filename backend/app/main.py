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

@app.get("/")
def read_root():
    return {"mensaje": "¡FastAPI conectado a PostgreSQL exitosamente!"}
