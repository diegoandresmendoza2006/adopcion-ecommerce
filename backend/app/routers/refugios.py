from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from .. import models
from ..database import get_db

router = APIRouter(prefix="/refugios", tags=["Refugios"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.RefugioOut)
def crear_refugio(refugio: schemas.RefugioCreate, db: Session = Depends(get_db)):
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
    refugios = db.query(models.Refugio).all()
    return refugios