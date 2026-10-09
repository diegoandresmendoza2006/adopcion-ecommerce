import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgIcon } from '@ng-icons/core';
import { ApiService } from '../../services/api.service';
import { editadoPrimero, irAlFormulario } from '../../services/ui';
import { Refugio, RefugioForm } from '../../models/modelos';

@Component({
  selector: 'app-admin-refugios',
  standalone: true,
  imports: [CommonModule, FormsModule, NgIcon],
  templateUrl: './admin-refugios.component.html'
})
export class AdminRefugiosComponent implements OnInit {
  refugios = signal<Refugio[]>([]);
  mostrarForm = signal(false);
  enviando = signal(false);
  error = signal('');
  ok = signal('');
  editandoId = signal<number | null>(null);
  confirmandoId = signal<number | null>(null);
  // último refugio editado: aparece de primero en la lista
  ultimoEditadoId = signal<number | null>(null);

  form: RefugioForm = this.vacio();

  constructor(private api: ApiService) {}

  private vacio(): RefugioForm {
    return { nombre: '', direccion: '', telefono: '' };
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.api.get<Refugio[]>('/refugios/').subscribe({
      next: (data) => this.refugios.set(editadoPrimero(data, this.ultimoEditadoId())),
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
      irAlFormulario('campo-nombre');
    }
    this.ok.set('');
    this.error.set('');
  }

  private cerrarForm() {
    this.mostrarForm.set(false);
    this.editandoId.set(null);
    this.form = this.vacio();
  }

  editar(r: Refugio) {
    this.form = { nombre: r.nombre, direccion: r.direccion ?? '', telefono: r.telefono ?? '' };
    this.editandoId.set(r.id);
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
      nombre: this.form.nombre,
      direccion: this.form.direccion || null,
      telefono: this.form.telefono || null
    };
    const id = this.editandoId();
    const peticion = id === null
      ? this.api.post<Refugio>('/refugios/', cuerpo)
      : this.api.put<Refugio>(`/refugios/${id}`, cuerpo);

    peticion.subscribe({
      next: (guardado) => {
        this.enviando.set(false);
        this.ok.set(id === null ? 'Refugio creado.' : 'Refugio actualizado.');
        this.ultimoEditadoId.set(guardado.id);   // el refugio guardado sube al primer lugar
        this.cerrarForm();
        this.cargar();
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(this.api.mensajeError(err, 'Revisa los datos del formulario.'));
      }
    });
  }

  pedirEliminar(r: Refugio) {
    this.confirmandoId.set(r.id);
    this.ok.set('');
    this.error.set('');
  }

  cancelarEliminar() {
    this.confirmandoId.set(null);
  }

  eliminar(r: Refugio) {
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
