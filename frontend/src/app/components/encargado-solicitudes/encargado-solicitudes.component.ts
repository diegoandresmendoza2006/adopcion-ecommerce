import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgIcon } from '@ng-icons/core';
import { ApiService } from '../../services/api.service';
import { edadDesdeNacimiento, siNo } from '../../services/formato';
import { DecisionSolicitud, EstadoSolicitud, Solicitud } from '../../models/modelos';

@Component({
  selector: 'app-encargado-solicitudes',
  standalone: true,
  imports: [CommonModule, FormsModule, NgIcon],
  templateUrl: './encargado-solicitudes.component.html',
  styleUrls: ['./encargado-solicitudes.component.css']
})
export class EncargadoSolicitudesComponent implements OnInit {
  solicitudes = signal<Solicitud[]>([]);
  abierta = signal<number | null>(null);   // solicitud cuyo formulario se está revisando
  enviando = signal(false);
  error = signal('');
  ok = signal('');

  // Mensaje que el encargado le deja al adoptante (lo verá en "Mis trámites")
  comentario = '';

  // Funciones de formato disponibles para la plantilla
  readonly siNo = siNo;
  readonly edadDesde = edadDesdeNacimiento;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.api.get<Solicitud[]>('/adopciones/').subscribe({
      next: (data) => this.solicitudes.set(data),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  alternar(s: Solicitud) {
    if (this.abierta() === s.id) {
      this.abierta.set(null);
      return;
    }
    this.abierta.set(s.id);
    this.comentario = s.comentario_encargado ?? '';   // si ya había mensaje, se puede corregir
    this.error.set('');
    this.ok.set('');
  }

  tieneFormulario(s: Solicitud): boolean {
    return !!(s.nombre_contacto || s.telefono || s.direccion || s.tipo_vivienda || s.motivo);
  }

  // Datos que merecen la atención del encargado (se resaltan en rojo)
  viviendaNoPermite(s: Solicitud): boolean {
    return s.vivienda_permite_mascotas === false;
  }

  muchasHorasSolo(s: Solicitud): boolean {
    return (s.horas_solo ?? 0) >= 8;
  }

  aprobar(s: Solicitud) {
    this.decidir(s, 'Aprobada');
  }

  rechazar(s: Solicitud) {
    this.decidir(s, 'Rechazada');
  }

  private decidir(s: Solicitud, estado: DecisionSolicitud['estado']) {
    this.error.set('');
    this.ok.set('');
    this.enviando.set(true);
    const cuerpo: DecisionSolicitud = { estado, comentario: this.comentario.trim() || undefined };
    this.api.patch(`/adopciones/${s.id}`, cuerpo).subscribe({
      next: () => {
        this.enviando.set(false);
        this.ok.set(`Solicitud de ${s.adoptante_nombre} para ${s.mascota_nombre}: ${estado}.`);
        this.abierta.set(null);
        this.cargar();
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(this.api.mensajeError(err));
      }
    });
  }

  // Enviar (o corregir) un comentario DESPUÉS de haber resuelto la solicitud
  enviarComentario(s: Solicitud) {
    const texto = this.comentario.trim();
    if (!texto) {
      this.error.set('Escribe el comentario antes de enviarlo.');
      return;
    }
    this.error.set('');
    this.ok.set('');
    this.enviando.set(true);
    this.api.patch(`/adopciones/${s.id}/comentario`, { comentario: texto }).subscribe({
      next: () => {
        this.enviando.set(false);
        this.ok.set(`Comentario enviado a ${s.adoptante_nombre}.`);
        this.cargar();
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(this.api.mensajeError(err));
      }
    });
  }

  claseEstado(estado: EstadoSolicitud): string {
    return estado === 'Aprobada' ? 'aprobada' : estado === 'Rechazada' ? 'rechazada' : 'revision';
  }
}
