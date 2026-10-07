import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from './auth.service';
import { API_URL } from './api.config';

// Agrega el token a TODAS las peticiones al backend y, si el token venció (401), cierra la sesión.
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.token();

  if (token && req.url.startsWith(API_URL) && !req.headers.has('Authorization')) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }

  return next(req).pipe(
    catchError((err) => {
            if (err.status === 401 && req.url.startsWith(API_URL) && !req.url.includes('/auth/login')) {
        auth.cerrarSesion();
        router.navigate(['/login']);
      }
      return throwError(() => err);
    })
  );
};