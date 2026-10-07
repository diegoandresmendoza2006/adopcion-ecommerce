from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 1. Importa el middleware aquí
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

# 2. Agrega esta configuración de CORS justo aquí
app.add_middleware(
    CORSMiddleware,
        allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],  # Permite que Angular se conecte
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