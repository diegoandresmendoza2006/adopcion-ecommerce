from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from .. import database
from .. import models
from .. import security

router = APIRouter(prefix="/productos", tags=["E-commerce - Productos"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.ProductoOut)
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(database.get_db),
                   _: models.Usuario = Depends(security.require_staff)):
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
    return db.query(models.Producto).order_by(models.Producto.id).all()


@router.get("/categorias", response_model=List[schemas.CategoriaOut])
def obtener_categorias(db: Session = Depends(database.get_db)):
    return db.query(models.CategoriaProducto).order_by(models.CategoriaProducto.nombre).all()