import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  credentials = { username: '', password: '' };
  errorMessage = signal('');
  mensaje = signal('');
  enviando = signal(false);

  constructor(private authService: AuthService, private router: Router) {}

  onLogin(): void {
    this.errorMessage.set('');
    this.enviando.set(true);

    this.authService.login(this.credentials).subscribe({
      next: (response: any) => {
        const token = response.access_token || response.token;
        if (token) {
          this.authService.guardarToken(token);
          this.mensaje.set('¡Ingreso exitoso!');
          this.router.navigate([this.authService.rutaInicio()]);
        }
      },
      error: (err: any) => {
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