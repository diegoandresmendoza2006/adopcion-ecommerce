import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { CarritoService } from '../../services/carrito.service';

@Component({
  selector: 'app-tienda',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './tienda.component.html',
  styleUrls: ['./tienda.component.css']
})
export class TiendaComponent implements OnInit {
  productos = signal<any[]>([]);
  cargando = signal(true);
  error = signal('');
  aviso = signal('');

  constructor(private api: ApiService, public carrito: CarritoService) {}

  ngOnInit(): void {
    this.api.get<any[]>('/productos/').subscribe({
      next: (data) => {
        this.productos.set(data);
        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(this.api.mensajeError(err));
      }
    });
  }

  agregarCarrito(producto: any) {
    const problema = this.carrito.agregar(producto);
    this.aviso.set(problema ?? `¡Añadido al carrito: ${producto.nombre}!`);
  }

  agregarFavoritos(producto: any) {
    this.carrito.alternarFavorito(producto);
  }
}