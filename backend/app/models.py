from sqlalchemy import Column, Integer, String, Text, ForeignKey, Numeric, TIMESTAMP, JSON, Boolean, Date
from sqlalchemy.sql import func
from .database import Base

class Rol(Base):
    __tablename__ = "roles"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False, unique=True)

class Refugio(Base):
    __tablename__ = "refugios"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(255))
    telefono = Column(String(20))

class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey("adopcion.roles.id"), nullable=False)
    refugio_id = Column(Integer, ForeignKey("adopcion.refugios.id"))
    fecha_registro = Column(TIMESTAMP, server_default=func.now())

class Mascota(Base):
    __tablename__ = "mascotas"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    especie = Column(String(50), nullable=False)
    raza = Column(String(50))
    edad_meses = Column(Integer)
    descripcion = Column(Text)
    estado_adopcion = Column(String(50), nullable=False)
    refugio_id = Column(Integer, ForeignKey("adopcion.refugios.id"), nullable=False)
    imagen_url = Column(Text)  # <-- Añadido

class SolicitudAdopcion(Base):
    __tablename__ = "solicitudes_adopcion"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("adopcion.usuarios.id"), nullable=False)
    mascota_id = Column(Integer, ForeignKey("adopcion.mascotas.id"), nullable=False)
    estado = Column(String(50), nullable=False)
    fecha_solicitud = Column(TIMESTAMP, server_default=func.now())
    # --- Formulario del adoptante: datos personales ---
    nombre_contacto = Column(String(150))
    fecha_nacimiento = Column(Date)
    telefono = Column(String(30))
    email_contacto = Column(String(100))
    direccion = Column(String(255))
    # --- Vivienda, entorno y espacio ---
    tipo_vivienda = Column(String(50))              # 'Propia' | 'Arrendada'
    vivienda_permite_mascotas = Column(Boolean)
    tiene_patio = Column(Boolean)
    tiene_cercas = Column(Boolean)
    personas_hogar = Column(Integer)
    # --- Experiencia previa ---
    tuvo_mascotas = Column(Boolean)
    mascotas_vacunadas = Column(Boolean)
    mascotas_esterilizadas = Column(Boolean)
    # --- Disponibilidad y estilo de vida ---
    horas_solo = Column(Integer)
    responsable_viajes = Column(Text)
    motivo = Column(Text)
    # --- Respuesta del encargado (la ve el adoptante) ---
    comentario_encargado = Column(Text)
    fecha_respuesta = Column(TIMESTAMP)


class SeguimientoAdopcion(Base):
    __tablename__ = "seguimiento_adopciones"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(Integer, ForeignKey("adopcion.solicitudes_adopcion.id"), nullable=False)
    fecha_reporte = Column(TIMESTAMP, server_default=func.now())
    estado_salud = Column(String(50), nullable=False)
    observaciones_texto = Column(Text)

class CategoriaProducto(Base):
    __tablename__ = "categorias_productos"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)

class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False)
    categoria_id = Column(Integer, ForeignKey("adopcion.categorias_productos.id"), nullable=False)
    imagen_url = Column(Text)  # <-- Añadido

class SeleccionProducto(Base):
    __tablename__ = "seleccion_productos"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("adopcion.usuarios.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("adopcion.productos.id"), nullable=False)
    tipo_lista = Column(String(20), nullable=False)
    cantidad = Column(Integer, nullable=False)

class OrdenCompra(Base):
    __tablename__ = "ordenes_compra"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("adopcion.usuarios.id"), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    estado_pedido = Column(String(50), nullable=False)
    fecha_compra = Column(TIMESTAMP, server_default=func.now())

class DetalleOrden(Base):
    __tablename__ = "detalles_orden"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("adopcion.ordenes_compra.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("adopcion.productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)

class Auditoria(Base):
    __tablename__ = "auditoria"
    __table_args__ = {'schema': 'adopcion'}
    id = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(100), nullable=False)
    accion = Column(String(20), nullable=False)
    tabla_afectada = Column(String(50), nullable=False)
    detalle_cambios = Column(JSON)
    fecha_accion = Column(TIMESTAMP, server_default=func.now())