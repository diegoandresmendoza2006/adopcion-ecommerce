from datetime import datetime
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

# Campos del formulario que se copian tal cual desde la petición a la tabla
CAMPOS_FORMULARIO = (
    "nombre_contacto", "fecha_nacimiento", "telefono", "email_contacto", "direccion",
    "tipo_vivienda", "vivienda_permite_mascotas", "tiene_patio", "tiene_cercas", "personas_hogar",
    "tuvo_mascotas", "mascotas_vacunadas", "mascotas_esterilizadas",
    "horas_solo", "responsable_viajes", "motivo",
)


def _consulta_detalle(db: Session):
    return (
        db.query(models.SolicitudAdopcion, models.Mascota, models.Usuario)
        .join(models.Mascota, models.Mascota.id == models.SolicitudAdopcion.mascota_id)
        .join(models.Usuario, models.Usuario.id == models.SolicitudAdopcion.usuario_id)
    )


def _a_detalle(fila) -> schemas.SolicitudDetalleOut:
    s, m, u = fila
    datos = schemas.SolicitudDetalleOut.model_validate(s)   # copia todas las columnas de la solicitud
    datos.mascota_nombre = m.nombre
    datos.adoptante_nombre = u.nombre_completo
    return datos


def _limpio(texto):
    texto = (texto or "").strip()
    return texto or None


def _solicitud_del_personal(db: Session, solicitud_id: int, usuario: models.Usuario):
    """Busca la solicitud y comprueba que este miembro del personal pueda gestionarla."""
    fila = _consulta_detalle(db).filter(models.SolicitudAdopcion.id == solicitud_id).first()
    if not fila:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La solicitud no existe")
    if usuario.rol_id == security.ROL_ENCARGADO and usuario.refugio_id and fila[1].refugio_id != usuario.refugio_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esta solicitud es de otro refugio")
    return fila


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.SolicitudAdopcionOut)
def crear_solicitud(solicitud: schemas.SolicitudAdopcionCreate, db: Session = Depends(database.get_db),
                    usuario: models.Usuario = Depends(security.get_current_user)):
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

    datos = solicitud.model_dump(include=set(CAMPOS_FORMULARIO))
    for campo in ("motivo",):
        datos[campo] = _limpio(datos[campo])
    nueva_solicitud = models.SolicitudAdopcion(usuario_id=usuario.id, mascota_id=mascota.id,
                                               estado=ESTADO_REVISION, **datos)
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    return nueva_solicitud


@router.get("/mis", response_model=List[schemas.SolicitudDetalleOut])
def mis_solicitudes(db: Session = Depends(database.get_db), usuario: models.Usuario = Depends(security.get_current_user)):
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


@router.get("/mascota/{mascota_id}", response_model=List[schemas.SolicitanteOut])
def solicitantes_de_mascota(mascota_id: int, db: Session = Depends(database.get_db),
                            usuario: models.Usuario = Depends(security.require_staff)):
    """Quién adoptó a la mascota o quiénes están aspirando a ella (para el encargado)."""
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La mascota no existe")
    if usuario.rol_id == security.ROL_ENCARGADO and usuario.refugio_id and mascota.refugio_id != usuario.refugio_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esa mascota pertenece a otro refugio")

    filas = (_consulta_detalle(db)
             .filter(models.SolicitudAdopcion.mascota_id == mascota_id)
             .order_by(models.SolicitudAdopcion.id).all())
    return [schemas.SolicitanteOut(solicitud_id=s.id, adoptante_nombre=s.nombre_contacto or u.nombre_completo,
                                   estado=s.estado, fecha_solicitud=s.fecha_solicitud, telefono=s.telefono)
            for s, _, u in filas]


@router.patch("/{solicitud_id}", response_model=schemas.SolicitudDetalleOut)
def cambiar_estado(solicitud_id: int, datos: schemas.EstadoUpdate, db: Session = Depends(database.get_db),
                   usuario: models.Usuario = Depends(security.require_staff)):
    if datos.estado not in (ESTADO_APROBADA, ESTADO_RECHAZADA):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Estado inválido. Usa '{ESTADO_APROBADA}' o '{ESTADO_RECHAZADA}'")

    s, m, _ = _solicitud_del_personal(db, solicitud_id, usuario)
    if s.estado != ESTADO_REVISION:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta solicitud ya fue resuelta")

    if datos.estado == ESTADO_APROBADA and m.estado_adopcion == MASCOTA_ADOPTADA:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta mascota ya fue adoptada por otra persona")

    s.estado = datos.estado
    s.comentario_encargado = _limpio(datos.comentario)
    s.fecha_respuesta = datetime.now()

    if datos.estado == ESTADO_APROBADA:
        m.estado_adopcion = MASCOTA_ADOPTADA
        # Regla de negocio: al adoptarse, las demás solicitudes pendientes de esa mascota se rechazan
        otras = (db.query(models.SolicitudAdopcion)
                 .filter(models.SolicitudAdopcion.mascota_id == m.id,
                         models.SolicitudAdopcion.id != s.id,
                         models.SolicitudAdopcion.estado == ESTADO_REVISION).all())
        for otra in otras:
            otra.estado = ESTADO_RECHAZADA
            otra.comentario_encargado = f"{m.nombre} fue adoptada por otra persona. ¡Gracias por tu interés!"
            otra.fecha_respuesta = datetime.now()
    db.commit()
    return _a_detalle(_consulta_detalle(db).filter(models.SolicitudAdopcion.id == solicitud_id).first())


@router.patch("/{solicitud_id}/comentario", response_model=schemas.SolicitudDetalleOut)
def enviar_comentario(solicitud_id: int, datos: schemas.ComentarioUpdate, db: Session = Depends(database.get_db),
                      usuario: models.Usuario = Depends(security.require_staff)):
    """El encargado deja (o corrige) un mensaje para el adoptante, aunque la solicitud ya esté resuelta."""
    s, _, _ = _solicitud_del_personal(db, solicitud_id, usuario)
    s.comentario_encargado = datos.comentario.strip()
    s.fecha_respuesta = datetime.now()
    db.commit()
    return _a_detalle(_consulta_detalle(db).filter(models.SolicitudAdopcion.id == solicitud_id).first())
