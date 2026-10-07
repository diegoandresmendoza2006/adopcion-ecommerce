import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet, RouterLink } from '@angular/router';
import { AuthService } from './services/auth.service';
import { CarritoService } from './services/carrito.service';
import { ROL_ADMIN, ROL_ENCARGADO, ROL_USUARIO } from './services/api.config';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App {
  title = 'Paws&Shop';
  ROL_ADMIN = ROL_ADMIN;
  ROL_ENCARGADO = ROL_ENCARGADO;
  ROL_USUARIO = ROL_USUARIO;

  constructor(public auth: AuthService, public carrito: CarritoService, private router: Router) {}

  salir(): void {
    this.auth.cerrarSesion();
    this.router.navigate(['/login']);
  }
}