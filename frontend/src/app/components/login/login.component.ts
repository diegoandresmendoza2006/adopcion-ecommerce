import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NgIcon } from '@ng-icons/core';
import { AuthService } from '../../services/auth.service';
import { Credenciales, RespuestaLogin } from '../../models/modelos';
import { CampoPasswordComponent } from '../campo-password/campo-password.component';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, NgIcon, CampoPasswordComponent],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  credentials: Credenciales = { username: '', password: '' };
  errorMessage = signal('');
  mensaje = signal('');
  enviando = signal(false);

  constructor(private authService: AuthService, private router: Router) {}

  onLogin(): void {
    this.errorMessage.set('');
    this.enviando.set(true);

    this.authService.login(this.credentials).subscribe({
      next: (response: RespuestaLogin) => {
        if (response.access_token) {
          this.authService.guardarToken(response.access_token);
          this.mensaje.set('¡Ingreso exitoso!');
          this.router.navigate(['/catalogo']);
        }
      },
      error: (err: { status?: number }) => {
        console.error('Error en el login', err);
        this.enviando.set(false);
        this.errorMessage.set(
          err.status === 0
            ? 'No se pudo conectar con el servidor. ¿Está encendido el backend?'
            : 'Correo o contraseña incorrectos.'
        );
      }
    });
  }
}
