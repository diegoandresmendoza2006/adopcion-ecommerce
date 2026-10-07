import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { LoginComponent } from './components/login/login.component';
import { CatalogoComponent } from './components/catalogo/catalogo.component';
import { RegisterComponent } from './components/register/register.component';
import { TiendaComponent } from './components/tienda/tienda.component';
import { FavoritosComponent } from './components/favoritos/favoritos.component';
import { CarritoComponent } from './components/carrito/carrito.component';
import { MisSolicitudesComponent } from './components/mis-solicitudes/mis-solicitudes.component';
import { PanelSeguimientoComponent } from './components/panel-seguimiento/panel-seguimiento.component';
import { SolicitudAdopcionComponent } from './components/solicitud-adopcion/solicitud-adopcion.component';
import { DetalleMascotaComponent } from './components/detalle-mascota/detalle-mascota.component';
import { EncargadoMascotasComponent } from './components/encargado-mascotas/encargado-mascotas.component';
import { EncargadoProductosComponent } from './components/encargado-productos/encargado-productos.component';
import { EncargadoSolicitudesComponent } from './components/encargado-solicitudes/encargado-solicitudes.component';
import { EncargadoVerSeguimientosComponent } from './components/encargado-ver-seguimientos/encargado-ver-seguimientos.component';
import { AdminDashboardComponent } from './components/admin-dashboard/admin-dashboard.component';
import { AdminEncargadosComponent } from './components/admin-encargados/admin-encargados.component';
import { AdminAuditoriaComponent } from './components/admin-auditoria/admin-auditoria.component';

import { rolGuard } from './guards/guards';
import { AuthService } from './services/auth.service';
import { ROL_ADMIN, ROL_ENCARGADO, ROL_USUARIO } from './services/api.config';

export const routes: Routes = [
  // Públicas
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegisterComponent },

  // Solo USUARIO (adoptante / comprador)
  { path: 'catalogo', component: CatalogoComponent, canActivate: [rolGuard(ROL_USUARIO)] },
  { path: 'detalle-mascota/:id', component: DetalleMascotaComponent, canActivate: [rolGuard(ROL_USUARIO)] },
  { path: 'solicitud', component: SolicitudAdopcionComponent, canActivate: [rolGuard(ROL_USUARIO)] },
  { path: 'mis-solicitudes', component: MisSolicitudesComponent, canActivate: [rolGuard(ROL_USUARIO)] },
  { path: 'seguimientos', component: PanelSeguimientoComponent, canActivate: [rolGuard(ROL_USUARIO)] },
  { path: 'tienda', component: TiendaComponent, canActivate: [rolGuard(ROL_USUARIO)] },
  { path: 'favoritos', component: FavoritosComponent, canActivate: [rolGuard(ROL_USUARIO)] },
  { path: 'carrito', component: CarritoComponent, canActivate: [rolGuard(ROL_USUARIO)] },

  // Solo ENCARGADO de refugio
  { path: 'encargado-mascotas', component: EncargadoMascotasComponent, canActivate: [rolGuard(ROL_ENCARGADO)] },
  { path: 'encargado-productos', component: EncargadoProductosComponent, canActivate: [rolGuard(ROL_ENCARGADO)] },
  { path: 'encargado-solicitudes', component: EncargadoSolicitudesComponent, canActivate: [rolGuard(ROL_ENCARGADO)] },
  { path: 'encargado-ver-seguimientos', component: EncargadoVerSeguimientosComponent, canActivate: [rolGuard(ROL_ENCARGADO)] },

  // Solo ADMINISTRADOR
  { path: 'admin-dashboard', component: AdminDashboardComponent, canActivate: [rolGuard(ROL_ADMIN)] },
  { path: 'admin-encargados', component: AdminEncargadosComponent, canActivate: [rolGuard(ROL_ADMIN)] },
  { path: 'admin-auditoria', component: AdminAuditoriaComponent, canActivate: [rolGuard(ROL_ADMIN)] },

  // Cualquier otra dirección te lleva a la página de inicio de TU rol
  { path: '', pathMatch: 'full', redirectTo: () => inject(AuthService).rutaInicio() },
  { path: '**', redirectTo: () => inject(AuthService).rutaInicio() }
];