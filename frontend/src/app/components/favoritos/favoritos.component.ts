import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { NgIcon } from '@ng-icons/core';
import { CarritoService, ItemFavorito } from '../../services/carrito.service';

@Component({
  selector: 'app-favoritos',
  standalone: true,
  imports: [CommonModule, RouterLink, NgIcon],
  templateUrl: './favoritos.component.html',
  styleUrls: ['./favoritos.component.css']
})
export class FavoritosComponent {
  aviso = signal('');

  constructor(public carrito: CarritoService) {}

  moverAlCarrito(item: ItemFavorito) {
    const problema = this.carrito.agregar(item);
    if (problema) {
      this.aviso.set(problema);
      return;
    }
    this.carrito.quitarFavorito(item.producto_id);
    this.aviso.set(`¡"${item.nombre}" se movió al carrito!`);
  }
}
