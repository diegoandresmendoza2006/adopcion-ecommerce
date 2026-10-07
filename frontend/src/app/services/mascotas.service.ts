import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

@Injectable({
  providedIn: 'root'
})
export class MascotasService {
  private apiUrl = API_URL;

  constructor(private http: HttpClient) {}

  // Obtener todas las mascotas del catálogo
  getMascotas(): Observable<any> {
    return this.http.get(`${this.apiUrl}/mascotas/`);
  }

  // Obtener el detalle de una mascota por su ID
  getMascotaById(id: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/mascotas/${id}`);
  }

  // Enviar una solicitud de adopción
  enviarSolicitudAdopcion(solicitudData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/adopciones/`, solicitudData);
  }
}