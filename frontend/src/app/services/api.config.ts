// Dirección del backend (FastAPI). Si cambias el puerto, cámbialo SOLO aquí.
export const API_URL = 'http://localhost:8000';

// IDs de la tabla adopcion.roles (deben coincidir con tu base de datos)
export const ROL_ADMIN = 1;
export const ROL_ENCARGADO = 2;
export const ROL_USUARIO = 3;


// Cloudinary (alojamiento de fotos). Rellena estos dos valores con los de TU cuenta.
export const CLOUDINARY_CLOUD_NAME: string = 'hbqea1ba';
export const CLOUDINARY_UPLOAD_PRESET: string = 'ml_default';