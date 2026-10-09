import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { CLOUDINARY_CLOUD_NAME, CLOUDINARY_UPLOAD_PRESET } from './api.config';

// Sube una foto a Cloudinary y devuelve la URL pública (https://res.cloudinary.com/...)
@Injectable({
  providedIn: 'root'
})
export class ImagenService {
  constructor(private http: HttpClient) {}

  // ¿Ya pusiste tus datos de Cloudinary en api.config.ts?
  configurado(): boolean {
    return CLOUDINARY_CLOUD_NAME !== 'TU_CLOUD_NAME' && CLOUDINARY_UPLOAD_PRESET !== 'TU_UPLOAD_PRESET';
  }

  subir(archivo: File): Observable<string> {
    const form = new FormData();
    form.append('file', archivo);
    form.append('upload_preset', CLOUDINARY_UPLOAD_PRESET);

    return this.http
      .post<{ secure_url: string }>(`https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/image/upload`, form)
      .pipe(map(r => r.secure_url));
  }

  // Valida el archivo antes de subirlo. Devuelve un texto de error o null si está bien.
  validar(archivo: File): string | null {
    if (!archivo.type.startsWith('image/')) return 'El archivo debe ser una imagen (JPG, PNG o WEBP).';
    if (archivo.size > 5 * 1024 * 1024) return 'La imagen no puede pesar más de 5 MB.';
    return null;
  }
}
