import { Component, OnDestroy, OnInit, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpParams } from '@angular/common/http';
import { RouterLink } from '@angular/router';
import { NgIcon } from '@ng-icons/core';
import { Subscription } from 'rxjs';
import { API_URL } from '../../services/api.config';
import { edadTexto, estaDisponible } from '../../services/formato';
import { PaginacionComponent } from '../paginacion/paginacion.component';
import { Mascota, Pagina } from '../../models/modelos';

// Rangos de edad del filtro (el backend trabaja en MESES)
const RANGOS_EDAD: Record<string, { min?: number; max?: number }> = {
  '': {},
  cachorro: { max: 11 },          // menos de 1 año
  joven: { min: 12, max: 35 },    // 1 a 2 años
  adulto: { min: 36, max: 95 },   // 3 a 7 años
  senior: { min: 96 }             // 8 años o más
};

@Component({
  selector: 'app-catalogo',
  standalone: true,
  imports: [CommonModule, RouterLink, NgIcon, PaginacionComponent],
  templateUrl: './catalogo.component.html',
  styleUrls: ['./catalogo.component.css']
})
export class CatalogoComponent implements OnInit, OnDestroy {
  // Signals: la app es "zoneless", así que Angular solo refresca la pantalla
  // cuando cambia un signal (una propiedad normal NO actualiza la vista).
  mascotas = signal<Mascota[]>([]);
  total = signal(0);
  paginas = signal(1);
  cargando = signal(true);
  error = signal('');

  // Filtros, orden y página actual
  raza = signal('');
  especie = signal('');
  rangoEdad = signal('');
  soloDisponibles = signal(false);
  orden = signal('recientes');
  pagina = signal(1);
  readonly porPagina = 12;

  hayFiltros = computed(() => !!(this.raza().trim() || this.especie() || this.rangoEdad() || this.soloDisponibles()));

  private temporizador?: ReturnType<typeof setTimeout>;
  private peticion?: Subscription;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.buscar();
  }

  ngOnDestroy(): void {
    clearTimeout(this.temporizador);
    this.peticion?.unsubscribe();
  }

  // ---- eventos de los filtros (todos vuelven a la página 1) ----
  alEscribirRaza(valor: string) {
    this.raza.set(valor);
    clearTimeout(this.temporizador);            // espera 350 ms a que termines de escribir
    this.temporizador = setTimeout(() => this.reiniciarYBuscar(), 350);
  }

  setEspecie(valor: string) { this.especie.set(valor); this.reiniciarYBuscar(); }
  setEdad(valor: string) { this.rangoEdad.set(valor); this.reiniciarYBuscar(); }
  setOrden(valor: string) { this.orden.set(valor); this.reiniciarYBuscar(); }
  setSoloDisponibles(marcado: boolean) { this.soloDisponibles.set(marcado); this.reiniciarYBuscar(); }

  limpiar() {
    this.raza.set('');
    this.especie.set('');
    this.rangoEdad.set('');
    this.soloDisponibles.set(false);
    this.reiniciarYBuscar();
  }

  irAPagina(n: number) {
    this.pagina.set(n);
    this.buscar();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  private reiniciarYBuscar() {
    this.pagina.set(1);
    this.buscar();
  }

  // Pide SOLO un bloque de mascotas al servidor
  buscar(): void {
    let params = new HttpParams()
      .set('orden', this.orden())
      .set('pagina', this.pagina())
      .set('por_pagina', this.porPagina);

    if (this.raza().trim()) params = params.set('raza', this.raza().trim());
    if (this.especie()) params = params.set('especie', this.especie());
    if (this.soloDisponibles()) params = params.set('estado', 'Disponible');
    const rango = RANGOS_EDAD[this.rangoEdad()] ?? {};
    if (rango.min !== undefined) params = params.set('edad_min', rango.min);
    if (rango.max !== undefined) params = params.set('edad_max', rango.max);

    this.peticion?.unsubscribe();               // si había una búsqueda anterior en curso, se descarta
    this.cargando.set(true);
    this.error.set('');
    this.peticion = this.http.get<Pagina<Mascota>>(`${API_URL}/mascotas/buscar`, { params }).subscribe({
      next: (r) => {
        this.mascotas.set(r.items);
        this.total.set(r.total);
        this.paginas.set(r.paginas);
        this.pagina.set(r.pagina);
        this.cargando.set(false);
      },
      error: (err) => {
        console.error('ERROR AL CARGAR MASCOTAS:', err);
        this.cargando.set(false);
        this.error.set('No se pudo cargar el catálogo. Verifica que el backend esté encendido en ' + API_URL);
      }
    });
  }

  edadTexto(m: Mascota): string {
    return edadTexto(m.edad_meses);
  }

  disponible(m: Mascota): boolean {
    return estaDisponible(m);
  }

  esAdoptada(m: Mascota): boolean {
    return m.estado_adopcion === 'Adoptada';
  }

  enProceso(m: Mascota): boolean {
    return m.estado_adopcion === 'En Proceso';
  }
}
