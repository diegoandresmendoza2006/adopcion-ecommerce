import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet, RouterLink } from '@angular/router';
import { NgIcon } from '@ng-icons/core';
import { AuthService } from './services/auth.service';
import { CarritoService } from './services/carrito.service';
import { ROL_ADMIN, ROL_ENCARGADO } from './services/api.config';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, NgIcon],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App {
  title = 'Paws&Shop';
  ROL_ADMIN = ROL_ADMIN;
  ROL_ENCARGADO = ROL_ENCARGADO;

  constructor(public auth: AuthService, public carrito: CarritoService, private router: Router) {}

  esStaff(): boolean {
    const rol = this.auth.rolId();
    return rol === ROL_ADMIN || rol === ROL_ENCARGADO;
  }

  esUsuario(): boolean {
    return !this.esStaff();
  }

  salir(): void {
    this.auth.cerrarSesion();
    this.router.navigate(['/login']);
  }
}