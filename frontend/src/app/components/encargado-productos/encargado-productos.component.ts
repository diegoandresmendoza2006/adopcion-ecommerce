import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgIcon } from '@ng-icons/core';
import { ApiService } from '../../services/api.service';
import { editadoPrimero, irAlFormulario } from '../../services/ui';
import { Categoria, Producto, ProductoForm } from '../../models/modelos';
import { SubirFotoComponent } from '../subir-foto/subir-foto.component';

@Component({
  selector: 'app-encargado-productos',
  standalone: true,
  imports: [CommonModule, FormsModule, NgIcon, SubirFotoComponent],
  templateUrl: './encargado-productos.component.html',
  styleUrls: ['./encargado-productos.component.css']
})
export class EncargadoProductosComponent implements OnInit {
  productos = signal<Producto[]>([]);
  categorias = signal<Categoria[]>([]);
  mostrarForm = signal(false);
  enviando = signal(false);
  error = signal('');
  ok = signal('');

  // Foto del formulario (la maneja <app-subir-foto>)
  fotoUrl = signal('');
  subiendoFoto = signal(false);

  // null = creando; con número = editando ese producto
  editandoId = signal<number | null>(null);
  // id del producto que está pidiendo confirmación para eliminarse
  confirmandoId = signal<number | null>(null);
  // último producto editado: aparece de primero en la lista
  ultimoEditadoId = signal<number | null>(null);

  nuevo: ProductoForm = this.vacio();

  constructor(private api: ApiService) {}

  private vacio(): ProductoForm {
    return { nombre: '', descripcion: '', precio: 0, stock: 0, categoria_id: null };
  }

  ngOnInit(): void {
    this.cargar();
    this.api.get<Categoria[]>('/productos/categorias').subscribe(c => this.categorias.set(c));
  }

  cargar(): void {
    this.api.get<Producto[]>('/productos/').subscribe({
      next: (data) => this.productos.set(editadoPrimero(data, this.ultimoEditadoId())),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  nombreCategoria(id: number): string {
    return this.categorias().find(c => c.id === id)?.nombre ?? '';
  }

  // ---------- Abrir / cerrar el formulario ----------
  subirProducto() {
    if (this.mostrarForm()) {
      this.cerrarForm();
    } else {
      this.nuevo = this.vacio();
      this.fotoUrl.set('');
      this.editandoId.set(null);
      this.mostrarForm.set(true);
      irAlFormulario('campo-nombre');
    }
    this.ok.set('');
    this.error.set('');
  }

  private cerrarForm() {
    this.mostrarForm.set(false);
    this.editandoId.set(null);
    this.nuevo = this.vacio();
    this.fotoUrl.set('');
  }

  // ---------- EDITAR ----------
  editar(p: Producto) {
    this.nuevo = {
      nombre: p.nombre,
      descripcion: p.descripcion ?? '',
      precio: p.precio,
      stock: p.stock,
      categoria_id: p.categoria_id
    };
    this.fotoUrl.set(p.imagen_url ?? '');
    this.editandoId.set(p.id);
    this.confirmandoId.set(null);
    this.mostrarForm.set(true);
    this.ok.set('');
    this.error.set('');
    irAlFormulario('campo-nombre');
  }

  guardar() {
    this.enviando.set(true);
    this.error.set('');
    const cuerpo = {
      ...this.nuevo,
      descripcion: this.nuevo.descripcion || null,
      precio: Number(this.nuevo.precio),
      stock: Number(this.nuevo.stock),
      imagen_url: this.fotoUrl() || null
    };
    const id = this.editandoId();
    const peticion = id === null
      ? this.api.post<Producto>('/productos/', cuerpo)
      : this.api.put<Producto>(`/productos/${id}`, cuerpo);

    peticion.subscribe({
      next: (guardado) => {
        this.enviando.set(false);
        this.ok.set(id === null ? 'Producto creado.' : 'Producto actualizado.');
        this.ultimoEditadoId.set(guardado.id);   // el producto guardado sube al primer lugar
        this.cerrarForm();
        this.cargar();
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(this.api.mensajeError(err, 'Revisa los datos del formulario.'));
      }
    });
  }

  // ---------- Cambio rápido de stock (PATCH) ----------
  agotar(p: Producto) {
    this.error.set('');
    this.ok.set('');
    this.api.patch(`/productos/${p.id}`, { stock: 0 }).subscribe({
      next: () => { this.ok.set(`"${p.nombre}" quedó agotado.`); this.ultimoEditadoId.set(p.id); this.cargar(); },
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  // ---------- ELIMINAR (con confirmación en la misma fila) ----------
  pedirEliminar(p: Producto) {
    this.confirmandoId.set(p.id);
    this.ok.set('');
    this.error.set('');
  }

  cancelarEliminar() {
    this.confirmandoId.set(null);
  }

  eliminar(p: Producto) {
    this.api.delete(`/productos/${p.id}`).subscribe({
      next: () => {
        this.confirmandoId.set(null);
        this.ok.set(`"${p.nombre}" fue eliminado.`);
        if (this.editandoId() === p.id) this.cerrarForm();
        this.cargar();
      },
      error: (err) => {
        this.confirmandoId.set(null);
        this.error.set(this.api.mensajeError(err, 'No se pudo eliminar.'));
      }
    });
  }
}
