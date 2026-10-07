import { Injectable, computed, effect, signal } from '@angular/core';
import { AuthService } from './auth.service';

export interface ItemCarrito {
  producto_id: number;
  nombre: string;
  precio: number;
  cantidad: number;
  stock: number;
  imagen_url?: string | null;
}

export interface ItemFavorito {
  producto_id: number;
  nombre: string;
  precio: number;
  stock: number;
  imagen_url?: string | null;
}

const KEY_CARRITO = 'pawsshop_carrito';
const KEY_FAVS = 'pawsshop_favoritos';

function leer<T>(clave: string): T[] {
  try {
    return JSON.parse(localStorage.getItem(clave) || '[]');
  } catch {
    return [];
  }
}

// Carrito y favoritos viven en el navegador (localStorage). Solo la COMPRA va al backend.
@Injectable({
  providedIn: 'root'
})
export class CarritoService {
  readonly items = signal<ItemCarrito[]>(leer<ItemCarrito>(KEY_CARRITO));
  readonly favoritos = signal<ItemFavorito[]>(leer<ItemFavorito>(KEY_FAVS));
  readonly total = computed(() => this.items().reduce((acc, i) => acc + i.precio * i.cantidad, 0));
  readonly cantidadTotal = computed(() => this.items().reduce((acc, i) => acc + i.cantidad, 0));

  constructor(private auth: AuthService) {
    // Al cerrar sesión se vacía todo, para que otro usuario no vea tu carrito
    effect(() => {
      if (!this.auth.logueado()) {
        this.items.set([]);
        this.favoritos.set([]);
        localStorage.removeItem(KEY_CARRITO);
        localStorage.removeItem(KEY_FAVS);
      }
    });
  }

  private guardar(): void {
    localStorage.setItem(KEY_CARRITO, JSON.stringify(this.items()));
    localStorage.setItem(KEY_FAVS, JSON.stringify(this.favoritos()));
  }

  agregar(p: { id?: number; producto_id?: number; nombre: string; precio: number; stock: number; imagen_url?: string | null }, cantidad = 1): string | null {
    const id = (p.producto_id ?? p.id) as number;
    const actual = this.items().find(i => i.producto_id === id);
    const nueva = (actual?.cantidad ?? 0) + cantidad;
    if (nueva > p.stock) return `Solo quedan ${p.stock} unidades de "${p.nombre}"`;

    if (actual) {
      this.items.update(lista => lista.map(i => i.producto_id === id ? { ...i, cantidad: nueva, stock: p.stock } : i));
    } else {
      this.items.update(lista => [...lista, { producto_id: id, nombre: p.nombre, precio: Number(p.precio), cantidad, stock: p.stock, imagen_url: p.imagen_url }]);
    }
    this.guardar();
    return null;
  }

  cambiarCantidad(id: number, delta: number): void {
    this.items.update(lista => lista
      .map(i => i.producto_id === id ? { ...i, cantidad: Math.min(i.stock, i.cantidad + delta) } : i)
      .filter(i => i.cantidad > 0));
    this.guardar();
  }

  quitar(id: number): void {
    this.items.update(lista => lista.filter(i => i.producto_id !== id));
    this.guardar();
  }

  vaciar(): void {
    this.items.set([]);
    this.guardar();
  }

  esFavorito(id: number): boolean {
    return this.favoritos().some(f => f.producto_id === id);
  }

  alternarFavorito(p: { id: number; nombre: string; precio: number; stock: number; imagen_url?: string | null }): void {
    if (this.esFavorito(p.id)) {
      this.quitarFavorito(p.id);
      return;
    }
    this.favoritos.update(lista => [...lista, { producto_id: p.id, nombre: p.nombre, precio: Number(p.precio), stock: p.stock, imagen_url: p.imagen_url }]);
    this.guardar();
  }

  quitarFavorito(id: number): void {
    this.favoritos.update(lista => lista.filter(f => f.producto_id !== id));
    this.guardar();
  }
}