import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import schemas
from .. import models
from .. import security
from ..database import get_db

router = APIRouter(prefix="/mascotas", tags=["Mascotas"])


def _like(texto: str) -> str:
    """Convierte lo que escribe el usuario en un patrón LIKE seguro (los % y _ se tratan como texto normal)."""
    seguro = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{seguro}%"


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.MascotaOut)
def crear_mascota(mascota: schemas.MascotaCreate, db: Session = Depends(get_db),
                  usuario: models.Usuario = Depends(security.require_staff)):
    # Un encargado solo puede registrar mascotas en SU refugio
    refugio_id = mascota.refugio_id
    if usuario.rol_id == security.ROL_ENCARGADO and usuario.refugio_id:
        refugio_id = usuario.refugio_id

    refugio = db.query(models.Refugio).filter(models.Refugio.id == refugio_id).first()
    if not refugio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El refugio especificado no existe")

    nueva_mascota = models.Mascota(
        nombre=mascota.nombre,
        especie=mascota.especie,
        raza=mascota.raza,
        edad_meses=mascota.edad_meses,
        descripcion=mascota.descripcion,
        estado_adopcion=mascota.estado_adopcion,
        refugio_id=refugio_id,
        imagen_url=mascota.imagen_url
    )
    db.add(nueva_mascota)
    db.commit()
    db.refresh(nueva_mascota)
    return nueva_mascota


@router.get("/", response_model=List[schemas.MascotaOut])
def obtener_mascotas(especie: Optional[str] = None, estado: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Mascota)
    if especie:
        query = query.filter(models.Mascota.especie.ilike(f"%{especie}%"))
    if estado:
        query = query.filter(models.Mascota.estado_adopcion.ilike(f"%{estado}%"))
    return query.order_by(models.Mascota.id).all()


# Catálogo: filtros + orden + paginación. El servidor devuelve solo UN bloque de resultados.
# IMPORTANTE: las rutas fijas (/buscar, /gestion/inventario) van ANTES de "/{mascota_id}".
@router.get("/buscar", response_model=schemas.PaginaMascotas)
def buscar_mascotas(
    raza: Optional[str] = Query(None, max_length=60),
    especie: Optional[str] = Query(None, max_length=30),
    estado: Optional[str] = Query(None, max_length=30),
    edad_min: Optional[int] = Query(None, ge=0, description="Edad mínima en MESES"),
    edad_max: Optional[int] = Query(None, ge=0, description="Edad máxima en MESES"),
    orden: str = Query("recientes", pattern="^(recientes|nombre|edad_asc|edad_desc)$"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    if edad_min is not None and edad_max is not None and edad_min > edad_max:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La edad mínima no puede ser mayor que la máxima")

    M = models.Mascota
    consulta = db.query(M)
    if raza and raza.strip():
        consulta = consulta.filter(M.raza.ilike(_like(raza.strip()), escape="\\"))
    if especie and especie.strip():
        consulta = consulta.filter(func.lower(M.especie) == especie.strip().lower())
    if estado and estado.strip():
        consulta = consulta.filter(M.estado_adopcion == estado.strip())
    if edad_min is not None:
        consulta = consulta.filter(M.edad_meses >= edad_min)
    if edad_max is not None:
        consulta = consulta.filter(M.edad_meses <= edad_max)

    total = consulta.count()

    # Siempre: disponibles primero, "En Proceso" después y "Adoptada" al final. Luego el orden elegido.
    prioridad = case((M.estado_adopcion == "Adoptada", 2), (M.estado_adopcion == "En Proceso", 1), else_=0)
    criterios = {
        "recientes": [M.id.desc()],
        "nombre": [func.lower(M.nombre).asc(), M.id.asc()],
        "edad_asc": [M.edad_meses.asc().nulls_last(), M.id.desc()],
        "edad_desc": [M.edad_meses.desc().nulls_last(), M.id.desc()],
    }
    items = (consulta.order_by(prioridad, *criterios[orden])
             .offset((pagina - 1) * por_pagina).limit(por_pagina).all())

    return {"items": items, "total": total, "pagina": pagina, "por_pagina": por_pagina,
            "paginas": max(1, math.ceil(total / por_pagina))}


@router.get("/gestion/inventario", response_model=List[schemas.MascotaOut])
def inventario_del_refugio(db: Session = Depends(get_db), usuario: models.Usuario = Depends(security.require_staff)):
    query = db.query(models.Mascota)
    if usuario.rol_id == security.ROL_ENCARGADO and usuario.refugio_id:
        query = query.filter(models.Mascota.refugio_id == usuario.refugio_id)
    return query.order_by(models.Mascota.id).all()


@router.get("/{mascota_id}", response_model=schemas.MascotaOut)
def obtener_mascota(mascota_id: int, db: Session = Depends(get_db)):
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La mascota no existe")
    return mascota



# ----------------------------------------------------------------------------
# EDITAR y ELIMINAR  (PUT = reemplazo completo, PATCH = cambio parcial, DELETE)
# ----------------------------------------------------------------------------
from sqlalchemy.exc import IntegrityError

# Estados de una solicitud que significan "esta mascota ya fue entregada a alguien"
_ESTADOS_ADOPCION_CERRADA = ("Aprobada", "Entregada", "En Seguimiento", "Cerrada")


def _mascota_editable(db: Session, mascota_id: int, usuario: models.Usuario) -> models.Mascota:
    """Busca la mascota y comprueba que este usuario pueda tocarla.
    Administrador: cualquiera. Encargado: solo las de SU refugio."""
    mascota = db.query(models.Mascota).filter(models.Mascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La mascota no existe")
    if usuario.rol_id == security.ROL_ENCARGADO and mascota.refugio_id != usuario.refugio_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esa mascota pertenece a otro refugio")
    return mascota


def _aplicar_cambios(db: Session, mascota: models.Mascota, cambios: dict, usuario: models.Usuario) -> models.Mascota:
    # Un encargado no puede mover mascotas a otro refugio
    if usuario.rol_id == security.ROL_ENCARGADO:
        cambios.pop("refugio_id", None)
    elif "refugio_id" in cambios:
        if cambios["refugio_id"] is None:
            cambios.pop("refugio_id")
        elif not db.query(models.Refugio).filter(models.Refugio.id == cambios["refugio_id"]).first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El refugio especificado no existe")

    # Regla de negocio: si ya fue adoptada de verdad, no se puede "des-adoptar" editando
    nuevo_estado = cambios.get("estado_adopcion")
    if nuevo_estado and nuevo_estado != "Adoptada" and mascota.estado_adopcion == "Adoptada":
        cerrada = (db.query(models.SolicitudAdopcion)
                   .filter(models.SolicitudAdopcion.mascota_id == mascota.id,
                           models.SolicitudAdopcion.estado.in_(_ESTADOS_ADOPCION_CERRADA)).count())
        if cerrada:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Esta mascota ya tiene una adopción aprobada; no se puede volver a ponerla disponible")

    for campo, valor in cambios.items():
        setattr(mascota, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Los datos no cumplen las reglas de la base de datos")
    db.refresh(mascota)
    return mascota


@router.put("/{mascota_id}", response_model=schemas.MascotaOut)
def reemplazar_mascota(mascota_id: int, datos: schemas.MascotaPut, db: Session = Depends(get_db),
                       usuario: models.Usuario = Depends(security.require_staff)):
    mascota = _mascota_editable(db, mascota_id, usuario)
    return _aplicar_cambios(db, mascota, datos.model_dump(), usuario)


@router.patch("/{mascota_id}", response_model=schemas.MascotaOut)
def actualizar_mascota(mascota_id: int, datos: schemas.MascotaUpdate, db: Session = Depends(get_db),
                       usuario: models.Usuario = Depends(security.require_staff)):
    mascota = _mascota_editable(db, mascota_id, usuario)
    cambios = datos.model_dump(exclude_unset=True)
    # En PATCH estos campos son NOT NULL en la base: si llegan vacíos se ignoran
    for obligatorio in ("nombre", "especie", "estado_adopcion"):
        if obligatorio in cambios and cambios[obligatorio] is None:
            cambios.pop(obligatorio)
    return _aplicar_cambios(db, mascota, cambios, usuario)


@router.delete("/{mascota_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_mascota(mascota_id: int, forzar: bool = False, db: Session = Depends(get_db),
                     usuario: models.Usuario = Depends(security.require_staff)):
    mascota = _mascota_editable(db, mascota_id, usuario)
    solicitudes = db.query(models.SolicitudAdopcion).filter(models.SolicitudAdopcion.mascota_id == mascota_id).all()

    if solicitudes and not forzar:
        # Regla de negocio: por defecto se conserva el historial
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"No se puede eliminar: tiene {len(solicitudes)} solicitud(es) de adopción registradas. "
                                   "Márcala como 'Adoptada' para conservar el historial (el administrador puede forzar el borrado)")

    if solicitudes and forzar:
        # Borrado forzado: SOLO administrador. Borra también solicitudes y seguimientos de esta mascota.
        if usuario.rol_id != security.ROL_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Solo el administrador puede eliminar una mascota con historial de solicitudes")
        ids = [s.id for s in solicitudes]
        db.query(models.SeguimientoAdopcion).filter(models.SeguimientoAdopcion.solicitud_id.in_(ids)).delete(synchronize_session=False)
        db.query(models.SolicitudAdopcion).filter(models.SolicitudAdopcion.id.in_(ids)).delete(synchronize_session=False)

    db.delete(mascota)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se puede eliminar: hay datos que dependen de esta mascota")