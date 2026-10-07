from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from .. import database
from .. import models
from .. import security

router = APIRouter(prefix="/compras", tags=["E-commerce - Compras"])

# Debe coincidir con la restricción (CHECK) de tu columna ordenes_compra.estado_pedido
ESTADO_PEDIDO_INICIAL = "Pagada"


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.OrdenOut)
def procesar_compra(compra: schemas.CompraCreate, db: Session = Depends(database.get_db),
                    usuario: models.Usuario = Depends(security.require_usuario)):
    # Juntar productos repetidos
    cantidades = {}
    for item in compra.items:
        cantidades[item.producto_id] = cantidades.get(item.producto_id, 0) + item.cantidad

    productos = (db.query(models.Producto)
                 .filter(models.Producto.id.in_(cantidades.keys()))
                 .with_for_update().all())
    por_id = {p.id: p for p in productos}

    total = Decimal("0")
    for producto_id, cantidad in cantidades.items():
        p = por_id.get(producto_id)
        if not p:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El producto {producto_id} no existe")
        if p.stock < cantidad:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Stock insuficiente de '{p.nombre}' (quedan {p.stock})")
        total += Decimal(str(p.precio)) * cantidad

    orden = models.OrdenCompra(usuario_id=usuario.id, total=total, estado_pedido=ESTADO_PEDIDO_INICIAL)
    db.add(orden)
    db.flush()  # para obtener orden.id

    for producto_id, cantidad in cantidades.items():
        p = por_id[producto_id]
        db.add(models.DetalleOrden(orden_id=orden.id, producto_id=p.id, cantidad=cantidad, precio_unitario=p.precio))
        p.stock -= cantidad  # descontar inventario

    db.commit()
    db.refresh(orden)
    return orden


@router.get("/mis", response_model=List[schemas.OrdenOut])
def mis_compras(db: Session = Depends(database.get_db), usuario: models.Usuario = Depends(security.require_usuario)):
    return (db.query(models.OrdenCompra)
            .filter(models.OrdenCompra.usuario_id == usuario.id)
            .order_by(models.OrdenCompra.id.desc()).all())