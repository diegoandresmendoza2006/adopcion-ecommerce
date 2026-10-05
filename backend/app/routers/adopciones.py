from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import schemas
from .. import database
from .. import models

router = APIRouter(prefix="/adopciones", tags=["Solicitudes de Adopción"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.SolicitudAdopcionOut)
def crear_solicitud(
    solicitud: schemas.SolicitudAdopcionCreate, 
    db: Session = Depends(database.get_db)
):
    # 1. Verificar si la mascota existe
    mascota = db.query(models.Mascota).filter(models.Mascota.id == solicitud.mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La mascota no existe")
    
    # 2. Verificar que la mascota esté disponible
    if mascota.estado_adopcion.lower() != "disponible":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La mascota no está disponible para adopción")

    # Usamos exactamente el texto permitido por la restricción de la BD
    nueva_solicitud = models.SolicitudAdopcion(
        usuario_id=1,  
        mascota_id=solicitud.mascota_id,
        estado="En Revisión"
    )
    
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    return nueva_solicitud

@router.get("/", response_model=List[schemas.SolicitudAdopcionOut])
def obtener_solicitudes(db: Session = Depends(database.get_db)):
    solicitudes = db.query(models.SolicitudAdopcion).all()
    return solicitudes