from fastapi import FastAPI
from . import models
from .database import engine
from .routers import productos
from .routers import auth
from .routers import refugios
from .routers import mascotas
from .routers import adopciones

app = FastAPI(title="API - Adopción y E-commerce")

# Incluimos todos los routers incluyendo productos
app.include_router(auth.router)
app.include_router(refugios.router)
app.include_router(mascotas.router)
app.include_router(adopciones.router)
app.include_router(productos.router)

@app.get("/")
def read_root():
    return {"mensaje": "¡FastAPI conectado a PostgreSQL exitosamente!"}