from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from .. import database
from .. import models
from .. import security

router = APIRouter(prefix="/adopciones", tags=["Solicitudes de Adopción"])

# Textos de estado. Deben coincidir con la restricción (CHECK) de tu base de datos.
ESTADO_REVISION = "En Revisión"
ESTADO_APROBADA = "Aprobada"
ESTADO_RECHAZADA = "Rechazada"
MASCOTA_ADOPTADA = "Adoptada"


def _consulta_detalle(db: Session):
    return (
        db.query(models.SolicitudAdopcion, models.Mascota, models.Usuario)
        .join(models.Mascota, models.Mascota.id == models.SolicitudAdopcion.mascota_id)
        .join(models.Usuario, models.Usuario.id == models.SolicitudAdopcion.usuario_id)
    )


def _a_detalle(fila) -> schemas.SolicitudDetalleOut:
    s, m, u = fila
    return schemas.SolicitudDetalleOut(
        id=s.id, usuario_id=s.usuario_id, mascota_id=s.mascota_id, estado=s.estado,
        fecha_solicitud=s.fecha_solicitud, mascota_nombre=m.nombre, adoptante_nombre=u.nombre_completo,
        nombre_contacto=s.nombre_contacto, telefono=s.telefono, tipo_vivienda=s.tipo_vivienda, motivo=s.motivo,
    )


def _limpio(texto, largo):
    texto = (texto or "").strip()[:largo]
    return texto or None


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.SolicitudAdopcionOut)
def crear_solicitud(solicitud: schemas.SolicitudAdopcionCreate, db: Session = Depends(database.get_db),
                    usuario: models.Usuario = Depends(security.require_usuario)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == solicitud.mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La mascota no existe")

    if mascota.estado_adopcion.lower() != "disponible":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La mascota no está disponible para adopción")

    # Evitar solicitudes duplicadas del mismo usuario para la misma mascota
    ya_existe = db.query(models.SolicitudAdopcion).filter(
        models.SolicitudAdopcion.usuario_id == usuario.id,
        models.SolicitudAdopcion.mascota_id == mascota.id,
        models.SolicitudAdopcion.estado == ESTADO_REVISION,
    ).first()
    if ya_existe:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya tienes una solicitud en revisión para esta mascota")

    nueva_solicitud = models.SolicitudAdopcion(
        usuario_id=usuario.id, mascota_id=mascota.id, estado=ESTADO_REVISION,
        nombre_contacto=_limpio(solicitud.nombre_contacto, 150),
        telefono=_limpio(solicitud.telefono, 30),
        tipo_vivienda=_limpio(solicitud.tipo_vivienda, 50),
        motivo=_limpio(solicitud.motivo, 1000),
    )
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    return nueva_solicitud


@router.get("/mis", response_model=List[schemas.SolicitudDetalleOut])
def mis_solicitudes(db: Session = Depends(database.get_db), usuario: models.Usuario = Depends(security.require_usuario)):
    filas = (_consulta_detalle(db)
             .filter(models.SolicitudAdopcion.usuario_id == usuario.id)
             .order_by(models.SolicitudAdopcion.id.desc()).all())
    return [_a_detalle(f) for f in filas]


@router.get("/", response_model=List[schemas.SolicitudDetalleOut])
def obtener_solicitudes(db: Session = Depends(database.get_db), usuario: models.Usuario = Depends(security.require_staff)):
    consulta = _consulta_detalle(db)
    if usuario.rol_id == security.ROL_ENCARGADO and usuario.refugio_id:
        consulta = consulta.filter(models.Mascota.refugio_id == usuario.refugio_id)
    return [_a_detalle(f) for f in consulta.order_by(models.SolicitudAdopcion.id.desc()).all()]


@router.patch("/{solicitud_id}", response_model=schemas.SolicitudDetalleOut)
def cambiar_estado(solicitud_id: int, datos: schemas.EstadoUpdate, db: Session = Depends(database.get_db),
                   usuario: models.Usuario = Depends(security.require_staff)):
    if datos.estado not in (ESTADO_APROBADA, ESTADO_RECHAZADA):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estado inválido. Usa '{ESTADO_APROBADA}' o '{ESTADO_RECHAZADA}'")

    fila = _consulta_detalle(db).filter(models.SolicitudAdopcion.id == solicitud_id).first()
    if not fila:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La solicitud no existe")
    s, m, _ = fila

    if usuario.rol_id == security.ROL_ENCARGADO and usuario.refugio_id and m.refugio_id != usuario.refugio_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esta solicitud es de otro refugio")
    if s.estado != ESTADO_REVISION:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta solicitud ya fue resuelta")

    s.estado = datos.estado
    if datos.estado == ESTADO_APROBADA:
        m.estado_adopcion = MASCOTA_ADOPTADA
    db.commit()
    return _a_detalle(_consulta_detalle(db).filter(models.SolicitudAdopcion.id == solicitud_id).first())