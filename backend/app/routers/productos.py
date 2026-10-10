import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import schemas
from .. import database
from .. import models
from .. import security

router = APIRouter(prefix="/productos", tags=["E-commerce - Productos"])


def _like(texto: str) -> str:
    seguro = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{seguro}%"


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


# Tienda: filtros + orden + paginación. El servidor devuelve solo UN bloque de resultados.
@router.get("/buscar", response_model=schemas.PaginaProductos)
def buscar_productos(
    q: Optional[str] = Query(None, max_length=80, description="Texto a buscar en el nombre"),
    categoria_id: Optional[int] = Query(None, ge=1),
    precio_min: Optional[float] = Query(None, ge=0),
    precio_max: Optional[float] = Query(None, ge=0),
    solo_con_stock: bool = False,
    orden: str = Query("recientes", pattern="^(recientes|precio_asc|precio_desc|nombre)$"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(12, ge=1, le=50),
    db: Session = Depends(database.get_db),
):
    if precio_min is not None and precio_max is not None and precio_min > precio_max:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El precio mínimo no puede ser mayor que el máximo")

    P = models.Producto
    consulta = db.query(P)
    if q and q.strip():
        consulta = consulta.filter(P.nombre.ilike(_like(q.strip()), escape="\\"))
    if categoria_id is not None:
        consulta = consulta.filter(P.categoria_id == categoria_id)
    if precio_min is not None:
        consulta = consulta.filter(P.precio >= precio_min)
    if precio_max is not None:
        consulta = consulta.filter(P.precio <= precio_max)
    if solo_con_stock:
        consulta = consulta.filter(P.stock > 0)

    total = consulta.count()

    # Los agotados siempre al final; dentro de cada grupo, el orden elegido
    agotado = case((P.stock > 0, 0), else_=1)
    criterios = {
        "recientes": [P.id.desc()],
        "precio_asc": [P.precio.asc(), P.id.desc()],
        "precio_desc": [P.precio.desc(), P.id.desc()],
        "nombre": [func.lower(P.nombre).asc(), P.id.asc()],
    }
    items = (consulta.order_by(agotado, *criterios[orden])
             .offset((pagina - 1) * por_pagina).limit(por_pagina).all())

    return {"items": items, "total": total, "pagina": pagina, "por_pagina": por_pagina,
            "paginas": max(1, math.ceil(total / por_pagina))}



# ----------------------------------------------------------------------------
# EDITAR y ELIMINAR  (PUT = reemplazo completo, PATCH = cambio parcial, DELETE)
# ----------------------------------------------------------------------------
from sqlalchemy.exc import IntegrityError


def _producto_o_404(db: Session, producto_id: int) -> models.Producto:
    producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El producto no existe")
    return producto


def _guardar_producto(db: Session, producto: models.Producto, cambios: dict) -> models.Producto:
    if "categoria_id" in cambios:
        if cambios["categoria_id"] is None:
            cambios.pop("categoria_id")
        elif not db.query(models.CategoriaProducto).filter(models.CategoriaProducto.id == cambios["categoria_id"]).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La categoría no existe")
    for campo, valor in cambios.items():
        setattr(producto, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Los datos no cumplen las reglas de la base de datos")
    db.refresh(producto)
    return producto


@router.put("/{producto_id}", response_model=schemas.ProductoOut)
def reemplazar_producto(producto_id: int, datos: schemas.ProductoPut, db: Session = Depends(database.get_db),
                        _: models.Usuario = Depends(security.require_staff)):
    producto = _producto_o_404(db, producto_id)
    return _guardar_producto(db, producto, datos.model_dump())


@router.patch("/{producto_id}", response_model=schemas.ProductoOut)
def actualizar_producto(producto_id: int, datos: schemas.ProductoUpdate, db: Session = Depends(database.get_db),
                        _: models.Usuario = Depends(security.require_staff)):
    producto = _producto_o_404(db, producto_id)
    cambios = datos.model_dump(exclude_unset=True)
    for obligatorio in ("nombre", "precio", "stock"):   # NOT NULL en la base
        if obligatorio in cambios and cambios[obligatorio] is None:
            cambios.pop(obligatorio)
    return _guardar_producto(db, producto, cambios)


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_producto(producto_id: int, db: Session = Depends(database.get_db),
                      _: models.Usuario = Depends(security.require_staff)):
    producto = _producto_o_404(db, producto_id)
    # Regla de negocio: un producto que ya se vendió se conserva (el historial de ventas lo necesita)
    ventas = db.query(models.DetalleOrden).filter(models.DetalleOrden.producto_id == producto_id).count()
    if ventas:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="No se puede eliminar: ya forma parte de pedidos. Ponle stock 0 para que aparezca como agotado")
    # Lo que sí se limpia: carritos y favoritos de usuarios que lo tenían guardado
    db.query(models.SeleccionProducto).filter(models.SeleccionProducto.producto_id == producto_id).delete()
    db.delete(producto)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se puede eliminar: hay datos que dependen de este producto")