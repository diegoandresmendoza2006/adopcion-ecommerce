"""Favoritos del usuario: mascotas y productos.

Se guardan en el servidor para que no se pierdan al cambiar de celular.
 - Mascotas  -> tabla adopcion.favoritos_mascotas
 - Productos -> tabla adopcion.seleccion_productos con tipo_lista = 'FAVORITO'
(El carrito de compras vive en la app y solo la COMPRA llega al backend, igual que en Angular.)
"""
import math
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/favoritos", tags=["Favoritos"])
FAVORITO = "FAVORITO"


# ---------- Mascotas ----------
@router.get("/mascotas", response_model=schemas.PaginaMascotas)
def mis_mascotas_favoritas(pagina: int = Query(1, ge=1), por_pagina: int = Query(12, ge=1, le=50),
                           db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.get_current_user)):
    consulta = (db.query(models.Mascota)
                .join(models.FavoritoMascota, models.FavoritoMascota.mascota_id == models.Mascota.id)
                .filter(models.FavoritoMascota.usuario_id == usuario.id))
    total = consulta.count()
    items = (consulta.order_by(models.FavoritoMascota.fecha.desc(), models.Mascota.id.desc())
             .offset((pagina - 1) * por_pagina).limit(por_pagina).all())
    return {"items": items, "total": total, "pagina": pagina, "por_pagina": por_pagina,
            "paginas": max(1, math.ceil(total / por_pagina))}


@router.get("/mascotas/ids", response_model=List[int])
def ids_de_mascotas_favoritas(db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.get_current_user)):
    filas = db.query(models.FavoritoMascota.mascota_id).filter(models.FavoritoMascota.usuario_id == usuario.id).all()
    return [f[0] for f in filas]


@router.put("/mascotas/{mascota_id}", status_code=status.HTTP_204_NO_CONTENT)
def marcar_mascota_favorita(mascota_id: int, db: Session = Depends(get_db),
                            usuario: models.Usuario = Depends(security.get_current_user)):
    if not db.query(models.Mascota.id).filter(models.Mascota.id == mascota_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La mascota no existe")
    ya = db.query(models.FavoritoMascota).filter_by(usuario_id=usuario.id, mascota_id=mascota_id).first()
    if not ya:
        db.add(models.FavoritoMascota(usuario_id=usuario.id, mascota_id=mascota_id))
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/mascotas/{mascota_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_mascota_favorita(mascota_id: int, db: Session = Depends(get_db),
                            usuario: models.Usuario = Depends(security.get_current_user)):
    db.query(models.FavoritoMascota).filter_by(usuario_id=usuario.id, mascota_id=mascota_id).delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Productos ----------
@router.get("/productos", response_model=List[schemas.ProductoOut])
def mis_productos_favoritos(db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.get_current_user)):
    return (db.query(models.Producto)
            .join(models.SeleccionProducto, models.SeleccionProducto.producto_id == models.Producto.id)
            .filter(models.SeleccionProducto.usuario_id == usuario.id, models.SeleccionProducto.tipo_lista == FAVORITO)
            .order_by(models.SeleccionProducto.id.desc()).all())


@router.put("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def marcar_producto_favorito(producto_id: int, db: Session = Depends(get_db),
                             usuario: models.Usuario = Depends(security.get_current_user)):
    if not db.query(models.Producto.id).filter(models.Producto.id == producto_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El producto no existe")
    ya = db.query(models.SeleccionProducto).filter_by(usuario_id=usuario.id, producto_id=producto_id, tipo_lista=FAVORITO).first()
    if not ya:
        db.add(models.SeleccionProducto(usuario_id=usuario.id, producto_id=producto_id, tipo_lista=FAVORITO, cantidad=1))
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_producto_favorito(producto_id: int, db: Session = Depends(get_db),
                             usuario: models.Usuario = Depends(security.get_current_user)):
    db.query(models.SeleccionProducto).filter_by(usuario_id=usuario.id, producto_id=producto_id, tipo_lista=FAVORITO).delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
