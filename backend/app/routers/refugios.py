from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from .. import models
from .. import security
from ..database import get_db

router = APIRouter(prefix="/refugios", tags=["Refugios"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.RefugioOut)
def crear_refugio(refugio: schemas.RefugioCreate, db: Session = Depends(get_db),
                  _: models.Usuario = Depends(security.require_admin)):
    nuevo_refugio = models.Refugio(
        nombre=refugio.nombre,
        direccion=refugio.direccion,
        telefono=refugio.telefono
    )
    db.add(nuevo_refugio)
    db.commit()
    db.refresh(nuevo_refugio)
    return nuevo_refugio


@router.get("/", response_model=List[schemas.RefugioOut])
def obtener_refugios(db: Session = Depends(get_db)):
    return db.query(models.Refugio).order_by(models.Refugio.id).all()


def _refugio_o_404(db: Session, refugio_id: int) -> models.Refugio:
    refugio = db.query(models.Refugio).filter(models.Refugio.id == refugio_id).first()
    if not refugio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El refugio no existe")
    return refugio


def _guardar(db: Session, refugio: models.Refugio, cambios: dict) -> models.Refugio:
    for campo, valor in cambios.items():
        setattr(refugio, campo, valor)
    db.commit()
    db.refresh(refugio)
    return refugio


@router.put("/{refugio_id}", response_model=schemas.RefugioOut)
def reemplazar_refugio(refugio_id: int, datos: schemas.RefugioPut, db: Session = Depends(get_db),
                       _: models.Usuario = Depends(security.require_admin)):
    return _guardar(db, _refugio_o_404(db, refugio_id), datos.model_dump())


@router.patch("/{refugio_id}", response_model=schemas.RefugioOut)
def actualizar_refugio(refugio_id: int, datos: schemas.RefugioUpdate, db: Session = Depends(get_db),
                       _: models.Usuario = Depends(security.require_admin)):
    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios and cambios["nombre"] is None:
        cambios.pop("nombre")
    return _guardar(db, _refugio_o_404(db, refugio_id), cambios)


@router.delete("/{refugio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_refugio(refugio_id: int, db: Session = Depends(get_db),
                     _: models.Usuario = Depends(security.require_admin)):
    refugio = _refugio_o_404(db, refugio_id)
    # Regla de negocio: un refugio con mascotas o encargados asignados no se puede borrar
    mascotas = db.query(models.Mascota).filter(models.Mascota.refugio_id == refugio_id).count()
    personal = db.query(models.Usuario).filter(models.Usuario.refugio_id == refugio_id).count()
    if mascotas or personal:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"No se puede eliminar: tiene {mascotas} mascota(s) y {personal} usuario(s) asignados. Reasígnalos primero")
    db.delete(refugio)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No se puede eliminar: hay datos que dependen de este refugio")