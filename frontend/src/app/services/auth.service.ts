import { Injectable, computed, signal } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL, ROL_ADMIN, ROL_ENCARGADO, ROL_USUARIO } from './api.config';

function leerToken(): string | null {
  const t = localStorage.getItem('token') || localStorage.getItem('access_token');
  return t ? t.replace(/["']/g, '').trim() : null;
}

function decodificar(token: string | null): any {
  if (!token) return null;
  try {
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = API_URL;

  // Signals: la app es "zoneless", así el menú se actualiza solo al entrar/salir
  private _token = signal<string | null>(leerToken());
  readonly logueado = computed(() => !!this._token());
  readonly rolId = computed<number | null>(() => decodificar(this._token())?.rol_id ?? null);
  readonly usuarioId = computed<number | null>(() => decodificar(this._token())?.usuario_id ?? null);

  constructor(private http: HttpClient) {}

  // Página de inicio según el rol (también es a donde se manda a quien entra a una página que no es suya)
  rutaInicio(): string {
    if (!this.logueado()) return '/login';
    switch (this.rolId()) {
      case ROL_ADMIN: return '/admin-dashboard';
      case ROL_ENCARGADO: return '/encargado-solicitudes';
      case ROL_USUARIO: return '/catalogo';
      default: return '/login';
    }
  }

  token(): string | null {
    return this._token();
  }

  guardarToken(token: string): void {
    const limpio = token.replace(/["']/g, '').trim();
    localStorage.setItem('token', limpio);
    this._token.set(limpio);
  }

  cerrarSesion(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    this._token.set(null);
  }

  login(credentials: any): Observable<any> {
    const body = new URLSearchParams();
    body.set('username', credentials.username || credentials.email);
    body.set('password', credentials.password);

    const headers = new HttpHeaders({
      'Content-Type': 'application/x-www-form-urlencoded'
    });

    return this.http.post(`${this.apiUrl}/auth/login`, body.toString(), { headers });
  }

  registro(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/registro`, userData);
  }
}