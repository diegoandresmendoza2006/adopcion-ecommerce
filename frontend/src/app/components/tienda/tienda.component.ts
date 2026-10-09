import { Component, OnDestroy, OnInit, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpParams } from '@angular/common/http';
import { NgIcon } from '@ng-icons/core';
import { Subscription } from 'rxjs';
import { ApiService } from '../../services/api.service';
import { CarritoService } from '../../services/carrito.service';
import { PaginacionComponent } from '../paginacion/paginacion.component';
import { Categoria, Pagina, Producto } from '../../models/modelos';

@Component({
  selector: 'app-tienda',
  standalone: true,
  imports: [CommonModule, NgIcon, PaginacionComponent],
  templateUrl: './tienda.component.html',
  styleUrls: ['./tienda.component.css']
})
export class TiendaComponent implements OnInit, OnDestroy {
  productos = signal<Producto[]>([]);
  categorias = signal<Categoria[]>([]);
  total = signal(0);
  paginas = signal(1);
  cargando = signal(true);
  error = signal('');
  aviso = signal('');

  // Filtros, orden y página actual
  texto = signal('');
  categoriaId = signal('');     // '' = todas
  precioMin = signal('');
  precioMax = signal('');
  soloConStock = signal(false);
  orden = signal('recientes');
  pagina = signal(1);
  readonly porPagina = 12;

  hayFiltros = computed(() => !!(this.texto().trim() || this.categoriaId() || this.precioMin() || this.precioMax() || this.soloConStock()));

  private temporizador?: ReturnType<typeof setTimeout>;
  private peticion?: Subscription;

  constructor(private api: ApiService, public carrito: CarritoService) {}

  ngOnInit(): void {
    this.api.get<Categoria[]>('/productos/categorias').subscribe({
      next: (c) => this.categorias.set(c),
      error: () => {}   // si falla, simplemente no se ofrece el filtro de categoría
    });
    this.buscar();
  }

  ngOnDestroy(): void {
    clearTimeout(this.temporizador);
    this.peticion?.unsubscribe();
  }

  // ---- eventos de los filtros (todos vuelven a la página 1) ----
  alEscribir(campo: 'texto' | 'precioMin' | 'precioMax', valor: string) {
    this[campo].set(valor);
    clearTimeout(this.temporizador);            // espera 400 ms a que termines de escribir
    this.temporizador = setTimeout(() => this.reiniciarYBuscar(), 400);
  }

  setCategoria(valor: string) { this.categoriaId.set(valor); this.reiniciarYBuscar(); }
  setOrden(valor: string) { this.orden.set(valor); this.reiniciarYBuscar(); }
  setSoloConStock(marcado: boolean) { this.soloConStock.set(marcado); this.reiniciarYBuscar(); }

  limpiar() {
    this.texto.set('');
    this.categoriaId.set('');
    this.precioMin.set('');
    this.precioMax.set('');
    this.soloConStock.set(false);
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

  // Pide SOLO un bloque de productos al servidor
  buscar(): void {
    const min = this.precioMin().trim();
    const max = this.precioMax().trim();
    if (min !== '' && max !== '' && Number(min) > Number(max)) {
      this.error.set('El precio mínimo no puede ser mayor que el máximo.');
      return;
    }

    let params = new HttpParams()
      .set('orden', this.orden())
      .set('pagina', this.pagina())
      .set('por_pagina', this.porPagina);

    if (this.texto().trim()) params = params.set('q', this.texto().trim());
    if (this.categoriaId()) params = params.set('categoria_id', this.categoriaId());
    if (min !== '' && Number(min) >= 0) params = params.set('precio_min', min);
    if (max !== '' && Number(max) >= 0) params = params.set('precio_max', max);
    if (this.soloConStock()) params = params.set('solo_con_stock', 'true');

    this.peticion?.unsubscribe();               // si había una búsqueda anterior en curso, se descarta
    this.cargando.set(true);
    this.error.set('');
    this.peticion = this.api.get<Pagina<Producto>>(`/productos/buscar?${params.toString()}`).subscribe({
      next: (r) => {
        this.productos.set(r.items);
        this.total.set(r.total);
        this.paginas.set(r.paginas);
        this.pagina.set(r.pagina);
        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(this.api.mensajeError(err));
      }
    });
  }

  agregarCarrito(producto: Producto) {
    const problema = this.carrito.agregar(producto);
    this.aviso.set(problema ?? `¡Añadido al carrito: ${producto.nombre}!`);
  }

  agregarFavoritos(producto: Producto) {
    this.carrito.alternarFavorito(producto);
  }
}
