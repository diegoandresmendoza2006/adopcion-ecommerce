import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

// Servicio genérico para hablar con el backend desde cualquier componente.
@Injectable({
  providedIn: 'root'
})
export class ApiService {
  constructor(private http: HttpClient) {}

  get<T = any>(ruta: string): Observable<T> {
    return this.http.get<T>(`${API_URL}${ruta}`);
  }

  post<T = any>(ruta: string, cuerpo: any): Observable<T> {
    return this.http.post<T>(`${API_URL}${ruta}`, cuerpo);
  }

  patch<T = any>(ruta: string, cuerpo: any): Observable<T> {
    return this.http.patch<T>(`${API_URL}${ruta}`, cuerpo);
  }

  descargar(ruta: string): Observable<Blob> {
    return this.http.get(`${API_URL}${ruta}`, { responseType: 'blob' });
  }

  // Convierte el error del backend en un texto legible
  mensajeError(err: any, porDefecto = 'Ocurrió un error. Inténtalo de nuevo.'): string {
    if (err?.status === 0) return 'No se pudo conectar con el servidor. ¿Está encendido el backend?';
    const detalle = err?.error?.detail;
    return typeof detalle === 'string' ? detalle : porDefecto;
  }
}