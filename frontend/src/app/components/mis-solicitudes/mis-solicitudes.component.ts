import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgIcon } from '@ng-icons/core';
import { ApiService } from '../../services/api.service';
import { Solicitud } from '../../models/modelos';

@Component({
  selector: 'app-mis-solicitudes',
  standalone: true,
  imports: [CommonModule, NgIcon],
  templateUrl: './mis-solicitudes.component.html',
  styleUrls: ['./mis-solicitudes.component.css']
})
export class MisSolicitudesComponent implements OnInit {
  solicitudes = signal<Solicitud[]>([]);
  cargando = signal(true);
  error = signal('');

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.get<Solicitud[]>('/adopciones/mis').subscribe({
      next: (data) => {
        this.solicitudes.set(data);
        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(this.api.mensajeError(err));
      }
    });
  }

  private esc(t: string | null): string {
    const reemplazos: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    return (t || '').replace(/[&<>"']/g, c => reemplazos[c]);
  }

  // Abre el certificado en otra pestaña y el diálogo de impresión (ahí eliges "Guardar como PDF")
  descargarCertificado(s: Solicitud) {
    const w = window.open('', '_blank');
    if (!w) {
      this.error.set('Tu navegador bloqueó la ventana emergente. Permítela e inténtalo otra vez.');
      return;
    }
    const fecha = new Date().toLocaleDateString('es-CO', { year: 'numeric', month: 'long', day: 'numeric' });
    w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>Certificado de Adopción</title>
      <style>body{font-family:Georgia,serif;text-align:center;padding:60px;border:8px double #28a745;margin:30px}
      h1{color:#28a745}p{font-size:20px;line-height:1.6}.firma{margin-top:80px;font-size:14px;color:#555}</style></head>
      <body><h1>Certificado de Adopción</h1><p>Paws&amp;Shop certifica que</p>
      <h2>${this.esc(s.adoptante_nombre)}</h2><p>adoptó oficialmente a</p><h2>${this.esc(s.mascota_nombre)}</h2>
      <p>Solicitud N.º ${s.id} · Expedido el ${fecha}</p>
      <p class="firma">Gracias por darle un hogar a quien más lo necesita.</p></body></html>`);
    w.document.close();
    setTimeout(() => { w.focus(); w.print(); }, 400);
  }
}
