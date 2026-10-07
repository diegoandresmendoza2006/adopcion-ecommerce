import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { SubirFotoComponent } from '../subir-foto/subir-foto.component';

@Component({
  selector: 'app-encargado-productos',
  standalone: true,
  imports: [CommonModule, FormsModule, SubirFotoComponent],
  templateUrl: './encargado-productos.component.html',
  styleUrls: ['./encargado-productos.component.css']
})
export class EncargadoProductosComponent implements OnInit {
  productos = signal<any[]>([]);
  categorias = signal<any[]>([]);
  mostrarForm = signal(false);
  enviando = signal(false);
  error = signal('');
  ok = signal('');
  fotoUrl = signal('');
  subiendoFoto = signal(false);

  nuevo: any = this.vacio();

  constructor(private api: ApiService) {}

  private vacio() {
    return { nombre: '', descripcion: '', precio: 0, stock: 0, categoria_id: null, imagen_url: '' };
  }

  ngOnInit(): void {
    this.cargar();
    this.api.get<any[]>('/productos/categorias').subscribe(c => this.categorias.set(c));
  }

  cargar(): void {
    this.api.get<any[]>('/productos/').subscribe({
      next: (data) => this.productos.set(data),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  subirProducto() {
    this.mostrarForm.update(v => !v);
    this.ok.set('');
    this.error.set('');
  }

  guardar() {
    this.enviando.set(true);
    this.error.set('');
    const cuerpo = {
      ...this.nuevo,
      precio: Number(this.nuevo.precio),
      stock: Number(this.nuevo.stock),
      imagen_url: this.fotoUrl() || null
    };
    this.api.post('/productos/', cuerpo).subscribe({
      next: () => {
        this.enviando.set(false);
        this.ok.set('Producto creado.');
        this.mostrarForm.set(false);
        this.nuevo = this.vacio();
        this.fotoUrl.set('');
        this.cargar();
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(this.api.mensajeError(err, 'Revisa los datos del formulario.'));
      }
    });
  }
}