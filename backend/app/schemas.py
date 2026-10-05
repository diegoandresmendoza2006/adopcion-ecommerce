from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# ----------------------------------------
# ESQUEMAS DE USUARIO
# ----------------------------------------

class UsuarioCreate(BaseModel):
    nombre_completo: str
    email: EmailStr
    password: str
    rol_id: int = 3  # Asignamos el ID 3 por defecto (Rol: 'Usuario')
    refugio_id: Optional[int] = None

class UsuarioOut(BaseModel):
    id: int
    nombre_completo: str
    email: EmailStr
    rol_id: int
    fecha_registro: datetime

    class Config:
        from_attributes = True

# ----------------------------------------
# ESQUEMAS DE AUTENTICACIÓN (JWT)
# ----------------------------------------

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None


# ----------------------------------------
# ESQUEMAS DE REFUGIOS
# ----------------------------------------

class RefugioCreate(BaseModel):
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None

class RefugioOut(BaseModel):
    id: int
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------------------------------
# ESQUEMAS DE MASCOTAS
# ----------------------------------------

class MascotaCreate(BaseModel):
    nombre: str
    especie: str
    raza: Optional[str] = None
    edad_meses: Optional[int] = None
    descripcion: Optional[str] = None
    estado_adopcion: str = "Disponible"
    refugio_id: int
    imagen_url: Optional[str] = None  # <-- Añadido

class MascotaOut(BaseModel):
    id: int
    nombre: str
    especie: str
    raza: Optional[str] = None
    edad_meses: Optional[int] = None
    descripcion: Optional[str] = None
    estado_adopcion: str
    refugio_id: int
    imagen_url: Optional[str] = None  # <-- Añadido

    class Config:
        from_attributes = True



# ----------------------------------------
# ESQUEMAS DE SOLICITUDES DE ADOPCIÓN
# ----------------------------------------

class SolicitudAdopcionCreate(BaseModel):
    mascota_id: int

class SolicitudAdopcionOut(BaseModel):
    id: int
    usuario_id: int
    mascota_id: int
    estado: str

    class Config:
        from_attributes = True




# ----------------------------------------
# ESQUEMAS DE E-COMMERCE / PRODUCTOS
# ----------------------------------------

class ProductoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock: int
    categoria_id: int
    imagen_url: Optional[str] = None  # <-- Añadido

class ProductoOut(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock: int
    categoria_id: int
    imagen_url: Optional[str] = None  # <-- Añadido

    class Config:
        from_attributes = True