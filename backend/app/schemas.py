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
    nombre_contacto: Optional[str] = None
    telefono: Optional[str] = None
    tipo_vivienda: Optional[str] = None
    motivo: Optional[str] = None

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



# ----------------------------------------
# ESQUEMAS NUEVOS (adopciones detalladas, compras, seguimientos, admin)
# ----------------------------------------
from typing import List
from pydantic import ConfigDict, Field


class SolicitudDetalleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    usuario_id: int
    mascota_id: int
    estado: str
    fecha_solicitud: Optional[datetime] = None
    mascota_nombre: Optional[str] = None
    adoptante_nombre: Optional[str] = None
    nombre_contacto: Optional[str] = None
    telefono: Optional[str] = None
    tipo_vivienda: Optional[str] = None
    motivo: Optional[str] = None


class EstadoUpdate(BaseModel):
    estado: str


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str


class CompraItem(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0)


class CompraCreate(BaseModel):
    items: List[CompraItem] = Field(min_length=1)


class OrdenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    total: float
    estado_pedido: str
    fecha_compra: Optional[datetime] = None


class SeguimientoCreate(BaseModel):
    solicitud_id: int
    estado_salud: str
    observaciones_texto: Optional[str] = None


class SeguimientoOut(BaseModel):
    id: int
    solicitud_id: int
    fecha_reporte: Optional[datetime] = None
    estado_salud: str
    observaciones_texto: Optional[str] = None
    mascota_nombre: Optional[str] = None
    adoptante_nombre: Optional[str] = None


class EncargadoCreate(BaseModel):
    nombre_completo: str
    email: EmailStr
    password: str = Field(min_length=6)
    refugio_id: int


class EncargadoOut(BaseModel):
    id: int
    nombre_completo: str
    email: EmailStr
    refugio_id: Optional[int] = None
    refugio_nombre: Optional[str] = None


class AuditoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre_usuario: str
    accion: str
    tabla_afectada: str
    fecha_accion: Optional[datetime] = None


class MetricasOut(BaseModel):
    mes: str
    solicitudes_mes: int
    adopciones_mes: int
    pedidos_mes: int
    ventas_mes: float
    ventas_totales: float
    usuarios_registrados: int
    usuarios_nuevos_mes: int
    mascotas_disponibles: int
    mascotas_adoptadas: int