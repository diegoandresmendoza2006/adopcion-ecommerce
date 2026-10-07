import { Component, OnInit, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router, RouterLink } from '@angular/router';
import { API_URL } from '../../services/api.config';
import { edadTexto, estaDisponible } from '../../services/formato';

@Component({
  selector: 'app-catalogo',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './catalogo.component.html',
  styleUrls: ['./catalogo.component.css']
})
export class CatalogoComponent implements OnInit {
  // Signals: la app es "zoneless", así que Angular solo refresca la pantalla
  // cuando cambia un signal (una propiedad normal NO actualiza la vista).
  mascotas = signal<any[]>([]);
  cargando = signal(true);
  error = signal('');

  // Primero las disponibles, luego las "en proceso" y al final las ya adoptadas
  ordenadas = computed(() =>
    [...this.mascotas()].sort((a, b) => this.prioridad(a) - this.prioridad(b) || a.id - b.id)
  );

  apiUrl = `${API_URL}/mascotas/`;

  constructor(private http: HttpClient, private router: Router) {}

  ngOnInit(): void {
    this.cargarMascotas();
  }

  cargarMascotas(): void {
    // El token lo agrega solo el interceptor (auth.interceptor.ts)
    this.http.get<any>(this.apiUrl).subscribe({
      next: (data) => {
        this.mascotas.set(Array.isArray(data) ? data : []);
        this.cargando.set(false);
      },
      error: (err) => {
        console.error('ERROR AL CARGAR MASCOTAS:', err);
        this.cargando.set(false);
        this.error.set('No se pudo cargar el catálogo. Verifica que el backend esté encendido en ' + API_URL);
      }
    });
  }

  private prioridad(m: any): number {
    if (this.esAdoptada(m)) return 2;
    if (this.enProceso(m)) return 1;
    return 0;
  }

  edadTexto(m: any): string {
    return edadTexto(m?.edad_meses);
  }

  disponible(m: any): boolean {
    return estaDisponible(m);
  }

  esAdoptada(m: any): boolean {
    return (m?.estado_adopcion || '').toLowerCase() === 'adoptada';
  }

  enProceso(m: any): boolean {
    return (m?.estado_adopcion || '').toLowerCase() === 'en proceso';
  }
}