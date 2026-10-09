import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { NgIcon } from '@ng-icons/core';
import { ApiService } from '../../services/api.service';
import { CarritoService } from '../../services/carrito.service';
import { CompraNueva, Orden } from '../../models/modelos';

@Component({
  selector: 'app-carrito',
  standalone: true,
  imports: [CommonModule, RouterLink, NgIcon],
  templateUrl: './carrito.component.html',
  styleUrls: ['./carrito.component.css']
})
export class CarritoComponent {
  pagando = signal(false);
  error = signal('');
  ok = signal('');

  constructor(public carrito: CarritoService, private api: ApiService) {}

  pagarPedido() {
    const items = this.carrito.items();
    if (items.length === 0) return;

    this.error.set('');
    this.ok.set('');
    this.pagando.set(true);

    const cuerpo: CompraNueva = { items: items.map(i => ({ producto_id: i.producto_id, cantidad: i.cantidad })) };
    this.api.post<Orden>('/compras/', cuerpo).subscribe({
      next: (orden) => {
        this.carrito.vaciar();
        this.pagando.set(false);
        this.ok.set(`¡Compra realizada con éxito! Pedido #${orden.id} por $${Number(orden.total).toFixed(2)}.`);
      },
      error: (err) => {
        this.pagando.set(false);
        this.error.set(this.api.mensajeError(err, 'No se pudo procesar la compra.'));
      }
    });
  }
}
