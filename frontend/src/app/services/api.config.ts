// Dirección del backend (FastAPI).
// En tu computador (localhost) usa el backend local; ya publicado, usa el de la nube.
// Después de desplegar el backend, pon aquí SU dirección en lugar de la de ejemplo.
const URL_PRODUCCION = 'https://paws-shop-api.onrender.com';
const enLocal = typeof location !== 'undefined' && ['localhost', '127.0.0.1'].includes(location.hostname);
export const API_URL = enLocal ? 'http://localhost:8000' : URL_PRODUCCION;

// IDs de la tabla adopcion.roles (deben coincidir con tu base de datos)
export const ROL_ADMIN = 1;
export const ROL_ENCARGADO = 2;
export const ROL_USUARIO = 3;


// Cloudinary (alojamiento de fotos). Rellena estos dos valores con los de TU cuenta.
export const CLOUDINARY_CLOUD_NAME: string = 'hbqea1ba';
export const CLOUDINARY_UPLOAD_PRESET: string = 'ml_default';
