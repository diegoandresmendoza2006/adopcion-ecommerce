import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { EstadoSalud, Seguimiento, SeguimientoNuevo, Solicitud } from '../../models/modelos';

@Component({
  selector: 'app-panel-seguimiento',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-seguimiento.component.html',
  styleUrls: ['./panel-seguimiento.component.css']
})
export class PanelSeguimientoComponent implements OnInit {
  seguimientos = signal<Seguimiento[]>([]);
  adopciones = signal<Solicitud[]>([]);   // solo las aprobadas
  mostrarForm = signal(false);
  enviando = signal(false);
  error = signal('');
  ok = signal('');

  estados: EstadoSalud[] = ['Excelente', 'Bueno', 'Regular', 'Delicado'];
  nuevo: SeguimientoNuevo = { solicitud_id: null, estado_salud: 'Excelente', observaciones_texto: '' };

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargar();
    this.api.get<Solicitud[]>('/adopciones/mis').subscribe({
      next: (data) => this.adopciones.set(data.filter(s => s.estado === 'Aprobada')),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  cargar(): void {
    this.api.get<Seguimiento[]>('/seguimientos/mis').subscribe({
      next: (data) => this.seguimientos.set(data),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  enviarReporte() {
    this.mostrarForm.update(v => !v);
    this.ok.set('');
    this.error.set('');
  }

  guardar() {
    if (!this.nuevo.solicitud_id) {
      this.error.set('Elige la mascota adoptada.');
      return;
    }
    this.enviando.set(true);
    this.error.set('');
    this.api.post('/seguimientos/', this.nuevo).subscribe({
      next: () => {
        this.enviando.set(false);
        this.ok.set('¡Reporte enviado!');
        this.mostrarForm.set(false);
        this.nuevo = { solicitud_id: null, estado_salud: 'Excelente', observaciones_texto: '' };
        this.cargar();
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(this.api.mensajeError(err));
      }
    });
  }
}
