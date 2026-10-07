import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-encargado-solicitudes',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './encargado-solicitudes.component.html',
  styleUrls: ['./encargado-solicitudes.component.css']
})
export class EncargadoSolicitudesComponent implements OnInit {
  solicitudes = signal<any[]>([]);
  abierta = signal<number | null>(null);   // solicitud cuyo formulario se está revisando
  error = signal('');
  ok = signal('');

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.api.get<any[]>('/adopciones/').subscribe({
      next: (data) => this.solicitudes.set(data),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  alternar(id: number) {
    this.abierta.update(actual => (actual === id ? null : id));
  }

  tieneFormulario(s: any): boolean {
    return !!(s.nombre_contacto || s.telefono || s.tipo_vivienda || s.motivo);
  }

  aprobar(s: any) {
    this.cambiar(s, 'Aprobada');
  }

  rechazar(s: any) {
    this.cambiar(s, 'Rechazada');
  }

  private cambiar(s: any, estado: string) {
    this.error.set('');
    this.ok.set('');
    this.api.patch(`/adopciones/${s.id}`, { estado }).subscribe({
      next: () => {
        this.ok.set(`Solicitud de ${s.adoptante_nombre} para ${s.mascota_nombre}: ${estado}.`);
        this.abierta.set(null);
        this.cargar();
      },
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }
}