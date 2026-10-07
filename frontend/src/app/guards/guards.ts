import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

// Solo usuarios con sesión iniciada (sin importar el rol)
export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.logueado() ? true : inject(Router).createUrlTree(['/login']);
};

// Solo usuarios con uno de estos roles. Ej: rolGuard(ROL_ADMIN)
// Si entras a una página que no es de tu rol, te manda a TU página de inicio.
export const rolGuard = (...roles: number[]): CanActivateFn => () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.logueado()) return router.createUrlTree(['/login']);
  const rol = auth.rolId();
  return rol !== null && roles.includes(rol) ? true : router.createUrlTree([auth.rutaInicio()]);
};