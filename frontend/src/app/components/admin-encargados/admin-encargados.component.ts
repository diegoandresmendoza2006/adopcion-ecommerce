import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgIcon } from '@ng-icons/core';
import { ApiService } from '../../services/api.service';
import { Encargado, EncargadoNuevo, Refugio } from '../../models/modelos';
import { CampoPasswordComponent } from '../campo-password/campo-password.component';

@Component({
  selector: 'app-admin-encargados',
  standalone: true,
  imports: [CommonModule, FormsModule, NgIcon, CampoPasswordComponent],
  templateUrl: './admin-encargados.component.html',
  styleUrls: ['./admin-encargados.component.css']
})
export class AdminEncargadosComponent implements OnInit {
  encargados = signal<Encargado[]>([]);
  refugios = signal<Refugio[]>([]);
  mostrarForm = signal(false);
  enviando = signal(false);
  error = signal('');
  ok = signal('');

  nuevo: EncargadoNuevo = { nombre_completo: '', email: '', password: '', refugio_id: null };

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargar();
    this.api.get<Refugio[]>('/refugios/').subscribe(r => this.refugios.set(r));
  }

  cargar(): void {
    this.api.get<Encargado[]>('/admin/encargados').subscribe({
      next: (data) => this.encargados.set(data),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  crearEncargado() {
    this.mostrarForm.update(v => !v);
    this.ok.set('');
    this.error.set('');
  }

  guardar() {
    this.enviando.set(true);
    this.error.set('');
    this.api.post('/admin/encargados', this.nuevo).subscribe({
      next: () => {
        this.enviando.set(false);
        this.ok.set('Encargado creado.');
        this.mostrarForm.set(false);
        this.nuevo = { nombre_completo: '', email: '', password: '', refugio_id: null };
        this.cargar();
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(this.api.mensajeError(err, 'Revisa los datos (correo válido, contraseña de 6+ caracteres y refugio).'));
      }
    });
  }
}
