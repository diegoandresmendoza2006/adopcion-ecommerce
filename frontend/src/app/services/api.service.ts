import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { ErrorApi } from '../models/modelos';

// Servicio genérico para hablar con el backend desde cualquier componente.
// El tipo <T> es lo que RESPONDE el backend: this.api.get<Mascota[]>('/mascotas/')
@Injectable({
  providedIn: 'root'
})
export class ApiService {
  constructor(private http: HttpClient) {}

  get<T>(ruta: string): Observable<T> {
    return this.http.get<T>(`${API_URL}${ruta}`);
  }

  post<T = unknown>(ruta: string, cuerpo: object): Observable<T> {
    return this.http.post<T>(`${API_URL}${ruta}`, cuerpo);
  }

  patch<T = unknown>(ruta: string, cuerpo: object): Observable<T> {
    return this.http.patch<T>(`${API_URL}${ruta}`, cuerpo);
  }

  put<T = unknown>(ruta: string, cuerpo: object): Observable<T> {
    return this.http.put<T>(`${API_URL}${ruta}`, cuerpo);
  }

  delete<T = unknown>(ruta: string): Observable<T> {
    return this.http.delete<T>(`${API_URL}${ruta}`);
  }

  descargar(ruta: string): Observable<Blob> {
    return this.http.get(`${API_URL}${ruta}`, { responseType: 'blob' });
  }

  // Convierte el error del backend en un texto legible
  mensajeError(err: unknown, porDefecto = 'Ocurrió un error. Inténtalo de nuevo.'): string {
    const e = err as ErrorApi;
    if (e?.status === 0) return 'No se pudo conectar con el servidor. ¿Está encendido el backend?';
    const detalle = e?.error?.detail;
    if (typeof detalle === 'string') return detalle;
    // FastAPI devuelve una lista cuando falla la validación (422): mostramos el primer mensaje
    if (Array.isArray(detalle) && detalle.length > 0) {
      const primero = detalle[0] as { msg?: string };
      if (primero?.msg) return primero.msg.replace(/^Value error, /, '');
    }
    return porDefecto;
  }
}
