import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
  import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
    imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent {
  // El rol NO se envía: el backend siempre crea cuentas de "Usuario" (por seguridad)
  usuario = {
    nombre_completo: '',
    email: '',
    password: ''
  };

  errorMessage = signal('');
  mensaje = signal('');
  enviando = signal(false);

  constructor(private authService: AuthService, private router: Router) {}

  onRegister() {
    this.errorMessage.set('');
    this.enviando.set(true);

    this.authService.registro(this.usuario).subscribe({
      next: () => {
        this.mensaje.set('¡Cuenta creada con éxito! Redirigiendo al login...');
        setTimeout(() => this.router.navigate(['/login']), 1500);
      },
      error: (err) => {
        console.error('Error en el registro', err);
        this.enviando.set(false);
        const detalle = err.error?.detail;
        this.errorMessage.set(
          err.status === 0
            ? 'No se pudo conectar con el servidor. ¿Está encendido el backend?'
            : typeof detalle === 'string'
              ? detalle
              : 'Revisa los datos: correo válido y contraseña.'
        );
      }
    });
  }
}