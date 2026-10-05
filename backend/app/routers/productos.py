from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import schemas
from .. import database
from .. import models

router = APIRouter(prefix="/productos", tags=["E-commerce - Productos"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.ProductoOut)
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(database.get_db)):
    nuevo_producto = models.Producto(
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio=producto.precio,
        stock=producto.stock,
        categoria_id=producto.categoria_id,
        imagen_url=producto.imagen_url
    )
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

@router.get("/", response_model=List[schemas.ProductoOut])
def obtener_productos(db: Session = Depends(database.get_db)):
    productos = db.query(models.Producto).all()
    return productos