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
  error = signal('');

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    this.api.get(`/mascotas/${id}`).subscribe({
      next: (m) => {
        this.mascota.set(m);
        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(err.status === 404 ? 'Esta mascota no existe.' : this.api.mensajeError(err));
      }
    });
  }

  edadTexto(m: any): string {
    return edadTexto(m?.edad_meses);
  }

  disponible(m: any): boolean {
    return estaDisponible(m);
  }
}