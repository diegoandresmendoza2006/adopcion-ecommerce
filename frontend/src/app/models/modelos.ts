// =============================================================================
// Modelos (interfaces) de Paws&Shop.
// Describen EXACTAMENTE lo que responde el backend (schemas.py), así TypeScript
// avisa en tiempo de compilación si usas un campo que no existe.
// =============================================================================

// ---------- Valores permitidos ----------
export type EstadoMascota = 'Disponible' | 'En Proceso' | 'Adoptada';
export type EstadoSolicitud = 'En Revisión' | 'Aprobada' | 'Rechazada';
export type TipoVivienda = 'Propia' | 'Arrendada';
export type EstadoSalud = 'Excelente' | 'Bueno' | 'Regular' | 'Delicado';

// ---------- Paginación (misma forma para mascotas y productos) ----------
export interface Pagina<T> {
  items: T[];
  total: number;
  pagina: number;
  por_pagina: number;
  paginas: number;
}

// ---------- Autenticación ----------
export interface Credenciales {
  username: string;
  password: string;
}

export interface RespuestaLogin {
  access_token: string;
  token_type: string;
}

export interface RegistroUsuario {
  nombre_completo: string;
  email: string;
  password: string;
}

export interface Usuario {
  id: number;
  nombre_completo: string;
  email: string;
  rol_id: number;
  fecha_registro: string;
}

/** Lo que viaja dentro del token JWT */
export interface PayloadToken {
  usuario_id: number;
  rol_id: number;
  exp: number;
}

// ---------- Refugios ----------
export interface Refugio {
  id: number;
  nombre: string;
  direccion: string | null;
  telefono: string | null;
}

export interface RefugioForm {
  nombre: string;
  direccion: string;
  telefono: string;
}

// ---------- Mascotas ----------
export interface Mascota {
  id: number;
  nombre: string;
  especie: string;
  raza: string | null;
  edad_meses: number | null;
  descripcion: string | null;
  estado_adopcion: EstadoMascota;
  refugio_id: number;
  imagen_url: string | null;
}

/** Lo que se edita en el formulario del encargado */
export interface MascotaForm {
  nombre: string;
  especie: string;
  raza: string;
  edad_meses: number | null;
  descripcion: string;
  refugio_id: number | null;
  estado_adopcion: EstadoMascota;
}

// ---------- Productos ----------
export interface Categoria {
  id: number;
  nombre: string;
}

export interface Producto {
  id: number;
  nombre: string;
  descripcion: string | null;
  precio: number;
  stock: number;
  categoria_id: number;
  imagen_url: string | null;
}

export interface ProductoForm {
  nombre: string;
  descripcion: string;
  precio: number;
  stock: number;
  categoria_id: number | null;
}

// ---------- Compras ----------
export interface CompraItem {
  producto_id: number;
  cantidad: number;
}

export interface CompraNueva {
  items: CompraItem[];
}

export interface Orden {
  id: number;
  total: number;
  estado_pedido: string;
  fecha_compra: string | null;
}

// ---------- Solicitudes de adopción ----------
/** Lo que llena el adoptante en el formulario */
export interface FormularioAdopcion {
  // Datos personales
  nombre_contacto: string;
  fecha_nacimiento: string;           // AAAA-MM-DD
  telefono: string;
  email_contacto: string;
  direccion: string;
  // Vivienda
  tipo_vivienda: TipoVivienda | '';
  vivienda_permite_mascotas: boolean | null;
  // Entorno y espacio
  tiene_patio: boolean | null;
  tiene_cercas: boolean | null;
  personas_hogar: number | null;
  // Experiencia previa
  tuvo_mascotas: boolean | null;
  mascotas_vacunadas: boolean | null;
  mascotas_esterilizadas: boolean | null;
  // Disponibilidad y estilo de vida
  horas_solo: number | null;
  responsable_viajes: string;
  motivo: string;
}

/** Solicitud tal como la devuelve el backend (los campos del formulario son null en solicitudes antiguas) */
export interface Solicitud {
  id: number;
  usuario_id: number;
  mascota_id: number;
  estado: EstadoSolicitud;
  fecha_solicitud: string | null;
  mascota_nombre: string | null;
  adoptante_nombre: string | null;
  nombre_contacto: string | null;
  fecha_nacimiento: string | null;
  telefono: string | null;
  email_contacto: string | null;
  direccion: string | null;
  tipo_vivienda: string | null;
  vivienda_permite_mascotas: boolean | null;
  tiene_patio: boolean | null;
  tiene_cercas: boolean | null;
  personas_hogar: number | null;
  tuvo_mascotas: boolean | null;
  mascotas_vacunadas: boolean | null;
  mascotas_esterilizadas: boolean | null;
  horas_solo: number | null;
  responsable_viajes: string | null;
  motivo: string | null;
  comentario_encargado: string | null;
  fecha_respuesta: string | null;
}

/** Quién adoptó (o aspira a adoptar) a una mascota */
export interface Solicitante {
  solicitud_id: number;
  adoptante_nombre: string;
  estado: EstadoSolicitud;
  fecha_solicitud: string | null;
  telefono: string | null;
}

export interface DecisionSolicitud {
  estado: 'Aprobada' | 'Rechazada';
  comentario?: string;
}

// ---------- Seguimientos ----------
export interface Seguimiento {
  id: number;
  solicitud_id: number;
  fecha_reporte: string | null;
  estado_salud: EstadoSalud;
  observaciones_texto: string | null;
  mascota_nombre: string | null;
  adoptante_nombre: string | null;
}

export interface SeguimientoNuevo {
  solicitud_id: number | null;
  estado_salud: EstadoSalud;
  observaciones_texto: string;
}

// ---------- Administración ----------
export interface Encargado {
  id: number;
  nombre_completo: string;
  email: string;
  refugio_id: number | null;
  refugio_nombre: string | null;
}

export interface EncargadoNuevo {
  nombre_completo: string;
  email: string;
  password: string;
  refugio_id: number | null;
}

export interface RegistroAuditoria {
  id: number;
  nombre_usuario: string;
  accion: string;
  tabla_afectada: string;
  fecha_accion: string | null;
}

export interface Metricas {
  mes: string;
  solicitudes_mes: number;
  adopciones_mes: number;
  pedidos_mes: number;
  ventas_mes: number;
  ventas_totales: number;
  usuarios_registrados: number;
  usuarios_nuevos_mes: number;
  mascotas_disponibles: number;
  mascotas_adoptadas: number;
}

// ---------- Errores del backend ----------
/** Forma del error HTTP que usa ApiService.mensajeError */
export interface ErrorApi {
  status?: number;
  error?: { detail?: unknown };
}
