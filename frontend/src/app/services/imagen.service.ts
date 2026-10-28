import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { API_URL } from './api.config';

export type TipoImagen = 'mascotas' | 'productos';

// Las fotos ya NO se suben directo a Cloudinary desde Angular: se le mandan al backend (POST /imagenes/),
// que las sube a una carpeta ordenada y también las borra cuando dejan de usarse.
// La clave secreta de Cloudinary (necesaria para borrar) vive solo en el servidor.
@Injectable({
  providedIn: 'root'
})
export class ImagenService {
  constructor(private http: HttpClient) {}

  /** Sube la foto. `subcarpeta` = raza (mascotas) o categoría (productos); `especie` solo aplica a mascotas. */
  subir(archivo: File, tipo: TipoImagen, subcarpeta = '', especie = ''): Observable<string> {
    const form = new FormData();
    form.append('archivo', archivo);
    form.append('tipo', tipo);
    form.append('subcarpeta', subcarpeta);
    form.append('especie', especie);
    return this.http.post<{ url: string }>(`${API_URL}/imagenes/`, form).pipe(map(r => r.url));
  }

  /** Borra una foto que se subió pero nunca se guardó en una mascota/producto. */
  descartar(url: string): Observable<unknown> {
    return this.http.delete(`${API_URL}/imagenes/`, { params: { url } });
  }

  // Valida el archivo antes de subirlo. Devuelve un texto de error o null si está bien.
  validar(archivo: File): string | null {
    if (!/^image\/(jpeg|png|webp)$/.test(archivo.type)) return 'El archivo debe ser una imagen JPG, PNG o WEBP.';
    if (archivo.size > 5 * 1024 * 1024) return 'La imagen no puede pesar más de 5 MB.';
    return null;
  }
}