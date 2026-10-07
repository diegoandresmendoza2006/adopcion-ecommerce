from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from .. import database
from .. import models
from .. import security
from .adopciones import ESTADO_APROBADA

router = APIRouter(prefix="/seguimientos", tags=["Seguimiento post-adopción"])


def _consulta(db: Session):
    return (
        db.query(models.SeguimientoAdopcion, models.SolicitudAdopcion, models.Mascota, models.Usuario)
        .join(models.SolicitudAdopcion, models.SolicitudAdopcion.id == models.SeguimientoAdopcion.solicitud_id)
        .join(models.Mascota, models.Mascota.id == models.SolicitudAdopcion.mascota_id)
        .join(models.Usuario, models.Usuario.id == models.SolicitudAdopcion.usuario_id)
    )


def _a_out(fila) -> schemas.SeguimientoOut:
    seg, _, m, u = fila
    return schemas.SeguimientoOut(
        id=seg.id, solicitud_id=seg.solicitud_id, fecha_reporte=seg.fecha_reporte,
        estado_salud=seg.estado_salud, observaciones_texto=seg.observaciones_texto,
        mascota_nombre=m.nombre, adoptante_nombre=u.nombre_completo,
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.SeguimientoOut)
def crear_seguimiento(datos: schemas.SeguimientoCreate, db: Session = Depends(database.get_db),
                      usuario: models.Usuario = Depends(security.require_usuario)):
    solicitud = db.query(models.SolicitudAdopcion).filter(models.SolicitudAdopcion.id == datos.solicitud_id).first()
    if not solicitud or solicitud.usuario_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    if solicitud.estado != ESTADO_APROBADA:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo puedes reportar seguimiento de adopciones aprobadas")

    nuevo = models.SeguimientoAdopcion(
        solicitud_id=solicitud.id, estado_salud=datos.estado_salud, observaciones_texto=datos.observaciones_texto
    )
    db.add(nuevo)
    db.commit()
    return _a_out(_consulta(db).filter(models.SeguimientoAdopcion.id == nuevo.id).first())


@router.get("/mis", response_model=List[schemas.SeguimientoOut])
def mis_seguimientos(db: Session = Depends(database.get_db), usuario: models.Usuario = Depends(security.require_usuario)):
    filas = (_consulta(db).filter(models.SolicitudAdopcion.usuario_id == usuario.id)
             .order_by(models.SeguimientoAdopcion.id.desc()).all())
    return [_a_out(f) for f in filas]


@router.get("/", response_model=List[schemas.SeguimientoOut])
def todos_los_seguimientos(db: Session = Depends(database.get_db), usuario: models.Usuario = Depends(security.require_staff)):
    consulta = _consulta(db)
    if usuario.rol_id == security.ROL_ENCARGADO and usuario.refugio_id:
        consulta = consulta.filter(models.Mascota.refugio_id == usuario.refugio_id)
    return [_a_out(f) for f in consulta.order_by(models.SeguimientoAdopcion.id.desc()).all()]