from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator, model_validator
from datetime import date, datetime
from typing import Literal, Optional


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
    """Formulario de adopción. Los campos sin valor por defecto son OBLIGATORIOS."""
    model_config = ConfigDict(str_strip_whitespace=True)

    mascota_id: int
    # Datos personales
    nombre_contacto: str = Field(min_length=3, max_length=150)
    fecha_nacimiento: date
    telefono: str = Field(min_length=7, max_length=30)
    email_contacto: EmailStr
    direccion: str = Field(min_length=5, max_length=255)
    # Vivienda
    tipo_vivienda: Literal["Propia", "Arrendada"]
    vivienda_permite_mascotas: bool
    # Entorno y espacio
    tiene_patio: bool
    tiene_cercas: bool
    personas_hogar: int = Field(ge=1, le=30)
    # Experiencia previa (vacunación y esterilización solo si ha tenido mascotas)
    tuvo_mascotas: bool
    mascotas_vacunadas: Optional[bool] = None
    mascotas_esterilizadas: Optional[bool] = None
    # Disponibilidad y estilo de vida
    horas_solo: int = Field(ge=0, le=24)
    responsable_viajes: str = Field(min_length=3, max_length=500)
    motivo: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("fecha_nacimiento")
    @classmethod
    def mayor_de_edad(cls, v: date) -> date:
        hoy = date.today()
        edad = hoy.year - v.year - ((hoy.month, hoy.day) < (v.month, v.day))
        if edad < 18:
            raise ValueError("Debes ser mayor de 18 años para adoptar")
        if edad > 110:
            raise ValueError("La fecha de nacimiento no es válida")
        return v

    @model_validator(mode="after")
    def coherencia_experiencia(self):
        if self.tuvo_mascotas:
            if self.mascotas_vacunadas is None or self.mascotas_esterilizadas is None:
                raise ValueError("Indica si tus mascotas anteriores estaban vacunadas y esterilizadas")
        else:
            self.mascotas_vacunadas = None
            self.mascotas_esterilizadas = None
        return self


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
    # Formulario (opcionales: las solicitudes antiguas no lo tienen)
    nombre_contacto: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    telefono: Optional[str] = None
    email_contacto: Optional[str] = None
    direccion: Optional[str] = None
    tipo_vivienda: Optional[str] = None
    vivienda_permite_mascotas: Optional[bool] = None
    tiene_patio: Optional[bool] = None
    tiene_cercas: Optional[bool] = None
    personas_hogar: Optional[int] = None
    tuvo_mascotas: Optional[bool] = None
    mascotas_vacunadas: Optional[bool] = None
    mascotas_esterilizadas: Optional[bool] = None
    horas_solo: Optional[int] = None
    responsable_viajes: Optional[str] = None
    motivo: Optional[str] = None
    # Respuesta del encargado
    comentario_encargado: Optional[str] = None
    fecha_respuesta: Optional[datetime] = None



class EstadoUpdate(BaseModel):
    estado: str
    comentario: Optional[str] = Field(default=None, max_length=500)


class ComentarioUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    comentario: str = Field(min_length=1, max_length=500)


class SolicitanteOut(BaseModel):
    """Una persona que pidió (o adoptó) una mascota. Lo ve el personal al cambiar el estado."""
    solicitud_id: int
    adoptante_nombre: str
    estado: str
    fecha_solicitud: Optional[datetime] = None
    telefono: Optional[str] = None



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




# ----------------------------------------
# PÁGINAS DE RESULTADOS (búsqueda + paginación)
# ----------------------------------------
class PaginaMascotas(BaseModel):
    items: List[MascotaOut]
    total: int
    pagina: int
    por_pagina: int
    paginas: int


class PaginaProductos(BaseModel):
    items: List[ProductoOut]
    total: int
    pagina: int
    por_pagina: int
    paginas: int


# ----------------------------------------------------------------------------
# CRUD: editar (PUT = reemplazo completo, PATCH = cambios parciales)
# ----------------------------------------------------------------------------
from typing import Literal
from pydantic import Field

EstadoMascota = Literal["Disponible", "En Proceso", "Adoptada"]


class MascotaPut(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    especie: str = Field(min_length=1, max_length=50)
    raza: Optional[str] = Field(None, max_length=50)
    edad_meses: Optional[int] = Field(None, ge=0, le=600)
    descripcion: Optional[str] = None
    estado_adopcion: EstadoMascota = "Disponible"
    refugio_id: Optional[int] = None      # solo lo respeta el administrador
    imagen_url: Optional[str] = None


class MascotaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    especie: Optional[str] = Field(None, min_length=1, max_length=50)
    raza: Optional[str] = Field(None, max_length=50)
    edad_meses: Optional[int] = Field(None, ge=0, le=600)
    descripcion: Optional[str] = None
    estado_adopcion: Optional[EstadoMascota] = None
    refugio_id: Optional[int] = None
    imagen_url: Optional[str] = None


class ProductoPut(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: Optional[str] = None
    precio: float = Field(ge=0)
    stock: int = Field(ge=0)
    categoria_id: int
    imagen_url: Optional[str] = None


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = None
    precio: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    categoria_id: Optional[int] = None
    imagen_url: Optional[str] = None


class RefugioPut(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    direccion: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)


class RefugioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    direccion: Optional[str] = Field(None, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)