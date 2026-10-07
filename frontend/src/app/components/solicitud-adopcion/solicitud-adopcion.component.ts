import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-solicitud-adopcion',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './solicitud-adopcion.component.html',
  styleUrls: ['./solicitud-adopcion.component.css']
})
export class SolicitudAdopcionComponent implements OnInit {
  mascota = signal<any | null>(null);
  error = signal('');
  ok = signal('');
  enviando = signal(false);

  // Lo que escribe el adoptante: el ENCARGADO lo verá al revisar la solicitud
  datos = { nombre_contacto: '', telefono: '', tipo_vivienda: 'Casa propia', motivo: '' };

  constructor(private route: ActivatedRoute, private api: ApiService, private router: Router) {}

  ngOnInit(): void {
    const id = this.route.snapshot.queryParamMap.get('mascota');
    if (!id) {
      this.error.set('Primero elige una mascota en el catálogo y pulsa "Adoptar".');
      return;
    }
    this.api.get(`/mascotas/${id}`).subscribe({
      next: (m) => this.mascota.set(m),
      error: (err) => this.error.set(this.api.mensajeError(err, 'No se encontró la mascota.'))
    });
  }

  enviarSolicitud() {
    const m = this.mascota();
    if (!m) return;

    this.error.set('');
    this.enviando.set(true);
    this.api.post('/adopciones/', { mascota_id: m.id, ...this.datos }).subscribe({
      next: () => {
        this.ok.set('¡Solicitud enviada con éxito! Un encargado revisará tu formulario.');
        setTimeout(() => this.router.navigate(['/mis-solicitudes']), 1500);
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(this.api.mensajeError(err));
      }
    });
  }
}