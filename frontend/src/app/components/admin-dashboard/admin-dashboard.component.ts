import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { Metricas } from '../../models/modelos';

const NOMBRES_MES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

function mesActual(): string {
  const hoy = new Date();
  return `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}`;
}

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-dashboard.component.html',
  styleUrls: ['./admin-dashboard.component.css']
})
export class AdminDashboardComponent implements OnInit {
  readonly maxMes = mesActual();
  mes = signal(mesActual());   // formato AAAA-MM
  metricas = signal<Metricas | null>(null);
  error = signal('');
  descargando = signal(false);

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.cargar();
  }

  nombreMes(): string {
    const [anio, num] = this.mes().split('-');
    return `${NOMBRES_MES[Number(num) - 1]} de ${anio}`;
  }

  cambiarMes(valor: string) {
    if (!valor) return;
    this.mes.set(valor);
    this.cargar();
  }

  cargar(): void {
    this.error.set('');
    this.api.get<Metricas>(`/admin/metricas?mes=${this.mes()}`).subscribe({
      next: (m) => this.metricas.set(m),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  exportarReporte() {
    this.descargando.set(true);
    this.error.set('');
    this.api.descargar(`/admin/reporte.xlsx?mes=${this.mes()}`).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reporte_pawsshop_${this.mes()}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
        this.descargando.set(false);
      },
      error: (err) => {
        this.descargando.set(false);
        this.error.set(this.api.mensajeError(err, 'No se pudo descargar el reporte.'));
      }
    });
  }
}
