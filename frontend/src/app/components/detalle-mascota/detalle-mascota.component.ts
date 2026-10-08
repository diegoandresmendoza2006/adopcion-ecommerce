import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { edadTexto, estaDisponible } from '../../services/formato';

@Component({
  selector: 'app-detalle-mascota',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './detalle-mascota.component.html',
  styleUrls: ['./detalle-mascota.component.css']
})
export class DetalleMascotaComponent implements OnInit {
  mascota = signal<any | null>(null);
  cargando = signal(true);
  refugio = signal<any | null>(null);
  error = signal('');

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    this.api.get(`/mascotas/${id}`).subscribe({
        next: (m) => {
        this.mascota.set(m);
        this.cargando.set(false);
        this.cargarRefugio(m?.refugio_id);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(err.status === 404 ? 'Esta mascota no existe.' : this.api.mensajeError(err));
      }
    });
  }
    // Trae los datos del refugio al que pertenece la mascota (si falla, simplemente no se muestra la tarjeta)
  private cargarRefugio(refugioId: number | undefined): void {
    if (!refugioId) return;
    this.api.get<any[]>('/refugios/').subscribe({
      next: (lista) => this.refugio.set(lista.find(r => r.id === refugioId) ?? null),
      error: () => this.refugio.set(null)
    });
  }
  edadTexto(m: any): string {
    return edadTexto(m?.edad_meses);
  }

  disponible(m: any): boolean {
    return estaDisponible(m);
  }
}