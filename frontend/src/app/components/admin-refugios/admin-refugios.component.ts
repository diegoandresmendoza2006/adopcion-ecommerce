import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-admin-refugios',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-refugios.component.html'
})
export class AdminRefugiosComponent implements OnInit {
  refugios = signal<any[]>([]);
  mostrarForm = signal(false);
  enviando = signal(false);
  error = signal('');
  ok = signal('');
  editandoId = signal<number | null>(null);
  confirmandoId = signal<number | null>(null);

  form: any = this.vacio();

  constructor(private api: ApiService) {}

  private vacio() {
    return { nombre: '', direccion: '', telefono: '' };
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.api.get<any[]>('/refugios/').subscribe({
      next: (data) => this.refugios.set(data),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  nuevo() {
    if (this.mostrarForm()) {
      this.cerrarForm();
    } else {
      this.form = this.vacio();
      this.editandoId.set(null);
      this.mostrarForm.set(true);
    }
    this.ok.set('');
    this.error.set('');
  }

  private cerrarForm() {
    this.mostrarForm.set(false);
    this.editandoId.set(null);
    this.form = this.vacio();
  }

  editar(r: any) {
    this.form = { nombre: r.nombre, direccion: r.direccion ?? '', telefono: r.telefono ?? '' };
    this.editandoId.set(r.id);
    this.confirmandoId.set(null);
    this.mostrarForm.set(true);
    this.ok.set('');
    this.error.set('');
  }

  guardar() {
    this.enviando.set(true);
    this.error.set('');
    const cuerpo = {
      nombre: this.form.nombre,
      direccion: this.form.direccion || null,
      telefono: this.form.telefono || null
    };
    const id = this.editandoId();
    const peticion = id === null
      ? this.api.post('/refugios/', cuerpo)
      : this.api.put(`/refugios/${id}`, cuerpo);

    peticion.subscribe({
      next: () => {
        this.enviando.set(false);
        this.ok.set(id === null ? 'Refugio creado.' : 'Refugio actualizado.');
        this.cerrarForm();
        this.cargar();
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(this.api.mensajeError(err, 'Revisa los datos del formulario.'));
      }
    });
  }

  pedirEliminar(r: any) {
    this.confirmandoId.set(r.id);
    this.ok.set('');
    this.error.set('');
  }

  cancelarEliminar() {
    this.confirmandoId.set(null);
  }

  eliminar(r: any) {
    this.api.delete(`/refugios/${r.id}`).subscribe({
      next: () => {
        this.confirmandoId.set(null);
        this.ok.set(`"${r.nombre}" fue eliminado.`);
        if (this.editandoId() === r.id) this.cerrarForm();
        this.cargar();
      },
      error: (err) => {
        this.confirmandoId.set(null);
        this.error.set(this.api.mensajeError(err, 'No se pudo eliminar.'));
      }
    });
  }
}