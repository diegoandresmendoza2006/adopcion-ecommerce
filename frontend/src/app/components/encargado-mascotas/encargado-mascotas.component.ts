import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ROL_ADMIN } from '../../services/api.config';
import { edadTexto } from '../../services/formato';
import { SubirFotoComponent } from '../subir-foto/subir-foto.component';

@Component({
  selector: 'app-encargado-mascotas',
  standalone: true,
  imports: [CommonModule, FormsModule, SubirFotoComponent],
  templateUrl: './encargado-mascotas.component.html',
  styleUrls: ['./encargado-mascotas.component.css']
})
export class EncargadoMascotasComponent implements OnInit {
  mascotas = signal<any[]>([]);
  refugios = signal<any[]>([]);
  mostrarForm = signal(false);
  enviando = signal(false);
  error = signal('');
  ok = signal('');
  esAdmin = false;

  // Foto del formulario (la maneja <app-subir-foto>)
  fotoUrl = signal('');
  subiendoFoto = signal(false);

  // null = estamos creando; con número = estamos editando esa mascota
  editandoId = signal<number | null>(null);
  // id de la mascota que está pidiendo confirmación para eliminarse
  confirmandoId = signal<number | null>(null);
    // id de la mascota que tiene historial y el admin puede borrar a la fuerza
  forzarId = signal<number | null>(null);

  readonly estados = ['Disponible', 'En Proceso', 'Adoptada'];

  nueva: any = this.vacia();

  constructor(private api: ApiService, private auth: AuthService) {
    this.esAdmin = this.auth.rolId() === ROL_ADMIN;
  }

  private vacia() {
    return { nombre: '', especie: 'Perro', raza: '', edad_meses: 12, descripcion: '', refugio_id: null, estado_adopcion: 'Disponible' };
  }

  ngOnInit(): void {
    this.cargar();
    // El admin elige el refugio; el encargado usa automáticamente el suyo
    if (this.esAdmin) {
      this.api.get<any[]>('/refugios/').subscribe(r => this.refugios.set(r));
    }
  }

  cargar(): void {
    this.api.get<any[]>('/mascotas/gestion/inventario').subscribe({
      next: (data) => this.mascotas.set(data),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  edadTexto(m: any): string {
    return edadTexto(m?.edad_meses);
  }

  // ---------- Abrir / cerrar el formulario ----------
  registrarMascota() {
    if (this.mostrarForm()) {
      this.cerrarForm();
    } else {
      this.nueva = this.vacia();
      this.fotoUrl.set('');
      this.editandoId.set(null);
      this.mostrarForm.set(true);
    }
    this.ok.set('');
    this.error.set('');
  }

  private cerrarForm() {
    this.mostrarForm.set(false);
    this.editandoId.set(null);
    this.nueva = this.vacia();
    this.fotoUrl.set('');
  }

  // ---------- EDITAR ----------
  editar(m: any) {
    this.nueva = {
      nombre: m.nombre,
      especie: m.especie,
      raza: m.raza ?? '',
      edad_meses: m.edad_meses,
      descripcion: m.descripcion ?? '',
      refugio_id: m.refugio_id,
      estado_adopcion: m.estado_adopcion
    };
    this.fotoUrl.set(m.imagen_url ?? '');
    this.editandoId.set(m.id);
    this.confirmandoId.set(null);
    this.mostrarForm.set(true);
    this.ok.set('');
    this.error.set('');
    if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  guardar() {
    this.enviando.set(true);
    this.error.set('');
    const edad = this.nueva.edad_meses;
    const cuerpo = {
      ...this.nueva,
      raza: this.nueva.raza || null,
      descripcion: this.nueva.descripcion || null,
      edad_meses: edad === null || edad === '' || edad === undefined ? null : Number(edad),
      imagen_url: this.fotoUrl() || null,
      // el backend ignora este valor si eres encargado
      refugio_id: this.nueva.refugio_id ?? 0
    };
    const id = this.editandoId();
    const peticion = id === null
      ? this.api.post('/mascotas/', cuerpo)
      : this.api.put(`/mascotas/${id}`, cuerpo);

    peticion.subscribe({
      next: () => {
        this.enviando.set(false);
        this.ok.set(id === null ? 'Mascota registrada.' : 'Mascota actualizada.');
        this.cerrarForm();
        this.cargar();
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(this.api.mensajeError(err, 'Revisa los datos del formulario.'));
      }
    });
  }

  // ---------- Cambio rápido de estado (PATCH) ----------
  cambiarEstado(m: any, estado: string) {
    if (estado === m.estado_adopcion) return;
    this.error.set('');
    this.ok.set('');
    this.api.patch(`/mascotas/${m.id}`, { estado_adopcion: estado }).subscribe({
      next: () => { this.ok.set(`${m.nombre} ahora está "${estado}".`); this.cargar(); },
      error: (err) => { this.error.set(this.api.mensajeError(err)); this.cargar(); }
    });
  }

  // ---------- ELIMINAR (con confirmación en la misma fila) ----------
  pedirEliminar(m: any) {
    this.confirmandoId.set(m.id);
    this.ok.set('');
    this.error.set('');
  }

  cancelarEliminar() {
    this.confirmandoId.set(null);
  }

  eliminar(m: any) {
    this.api.delete(`/mascotas/${m.id}`).subscribe({
      next: () => {
        this.confirmandoId.set(null);
        this.ok.set(`${m.nombre} fue eliminada.`);
        if (this.editandoId() === m.id) this.cerrarForm();
        this.cargar();
      },
            error: (err) => {
        this.confirmandoId.set(null);
        this.error.set(this.api.mensajeError(err, 'No se pudo eliminar.'));
        // Si tiene historial de solicitudes, el administrador puede borrarla a la fuerza
        if (err?.status === 409 && this.esAdmin) this.forzarId.set(m.id);
      }
    });
    
  }
    // Solo administrador: borra la mascota Y sus solicitudes/seguimientos
  eliminarForzado(m: any) {
    this.api.delete(`/mascotas/${m.id}?forzar=true`).subscribe({
      next: () => {
        this.forzarId.set(null);
        this.error.set('');
        this.ok.set(`${m.nombre} y su historial fueron eliminados.`);
        this.cargar();
      },
      error: (err) => {
        this.forzarId.set(null);
        this.error.set(this.api.mensajeError(err, 'No se pudo eliminar.'));
      }
    });
    
  }
    cancelarForzado() {
    this.forzarId.set(null);
    this.error.set('');
  }
  
}