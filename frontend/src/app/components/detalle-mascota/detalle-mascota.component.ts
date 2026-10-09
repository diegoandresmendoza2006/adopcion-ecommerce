import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgIcon } from '@ng-icons/core';
import { ApiService } from '../../services/api.service';
import { edadTexto, estaDisponible } from '../../services/formato';
import { Mascota, Refugio } from '../../models/modelos';

@Component({
  selector: 'app-detalle-mascota',
  standalone: true,
  imports: [CommonModule, RouterLink, NgIcon],
  templateUrl: './detalle-mascota.component.html',
  styleUrls: ['./detalle-mascota.component.css']
})
export class DetalleMascotaComponent implements OnInit {
  mascota = signal<Mascota | null>(null);
  refugio = signal<Refugio | null>(null);
  cargando = signal(true);
  error = signal('');

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    this.api.get<Mascota>(`/mascotas/${id}`).subscribe({
      next: (m) => {
        this.mascota.set(m);
        this.cargando.set(false);
        this.cargarRefugio(m.refugio_id);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set((err as { status?: number }).status === 404 ? 'Esta mascota no existe.' : this.api.mensajeError(err));
      }
    });
  }

  // Trae los datos del refugio al que pertenece la mascota (si falla, simplemente no se muestra la tarjeta)
  private cargarRefugio(refugioId: number | undefined): void {
    if (!refugioId) return;
    this.api.get<Refugio[]>('/refugios/').subscribe({
      next: (lista) => this.refugio.set(lista.find(r => r.id === refugioId) ?? null),
      error: () => this.refugio.set(null)
    });
  }

  edadTexto(m: Mascota): string {
    return edadTexto(m.edad_meses);
  }

  disponible(m: Mascota): boolean {
    return estaDisponible(m);
  }
}
