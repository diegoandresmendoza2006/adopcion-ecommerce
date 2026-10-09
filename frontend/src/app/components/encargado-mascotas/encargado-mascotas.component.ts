import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgIcon } from '@ng-icons/core';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';
import { ROL_ADMIN } from '../../services/api.config';
import { edadTexto } from '../../services/formato';
import { editadoPrimero, irAlFormulario } from '../../services/ui';
import { EstadoMascota, Mascota, MascotaForm, Refugio, Solicitante } from '../../models/modelos';
import { SubirFotoComponent } from '../subir-foto/subir-foto.component';

// Estados de una solicitud que significan "esta mascota ya fue entregada a alguien"
const ESTADOS_ADOPCION_CERRADA = ['Aprobada', 'Entregada', 'En Seguimiento', 'Cerrada'];

@Component({
  selector: 'app-encargado-mascotas',
  standalone: true,
  imports: [CommonModule, FormsModule, NgIcon, SubirFotoComponent],
  templateUrl: './encargado-mascotas.component.html',
  styleUrls: ['./encargado-mascotas.component.css']
})
export class EncargadoMascotasComponent implements OnInit {
  mascotas = signal<Mascota[]>([]);
  refugios = signal<Refugio[]>([]);
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
  // última mascota editada: aparece de primera en la lista
  ultimaEditadaId = signal<number | null>(null);

  // Cambio de estado pendiente de confirmar (se muestra quién adoptó / quiénes aspiran)
  cambioPendiente = signal<{ mascota: Mascota; nuevoEstado: EstadoMascota } | null>(null);
  solicitantes = signal<Solicitante[]>([]);
  cargandoSolicitantes = signal(false);
  // Lo mismo pero para el formulario de edición
  solicitantesEdicion = signal<Solicitante[]>([]);

  readonly estados: EstadoMascota[] = ['Disponible', 'En Proceso', 'Adoptada'];

  nueva: MascotaForm = this.vacia();

  constructor(private api: ApiService, private auth: AuthService) {
    this.esAdmin = this.auth.rolId() === ROL_ADMIN;
  }

  private vacia(): MascotaForm {
    return { nombre: '', especie: 'Perro', raza: '', edad_meses: 12, descripcion: '', refugio_id: null, estado_adopcion: 'Disponible' };
  }

  ngOnInit(): void {
    this.cargar();
    // El admin elige el refugio; el encargado usa automáticamente el suyo
    if (this.esAdmin) {
      this.api.get<Refugio[]>('/refugios/').subscribe(r => this.refugios.set(r));
    }
  }

  cargar(): void {
    this.api.get<Mascota[]>('/mascotas/gestion/inventario').subscribe({
      next: (data) => this.mascotas.set(editadoPrimero(data, this.ultimaEditadaId())),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }

  edadTexto(m: Mascota): string {
    return edadTexto(m.edad_meses);
  }

  // ---------- Quién adoptó / quiénes aspiran ----------
  /** Persona que adoptó a la mascota (solicitud aprobada) */
  adoptante(lista: Solicitante[]): Solicitante | undefined {
    return lista.find(s => ESTADOS_ADOPCION_CERRADA.includes(s.estado));
  }

  /** Personas con una solicitud todavía en revisión */
  aspirantes(lista: Solicitante[]): Solicitante[] {
    return lista.filter(s => s.estado === 'En Revisión');
  }

  private traerSolicitantes(m: Mascota, destino: (lista: Solicitante[]) => void) {
    this.api.get<Solicitante[]>(`/adopciones/mascota/${m.id}`).subscribe({
      next: destino,
      error: () => destino([])
    });
  }

  // ---------- Abrir / cerrar el formulario ----------
  registrarMascota() {
    if (this.mostrarForm()) {
      this.cerrarForm();
    } else {
      this.nueva = this.vacia();
      this.fotoUrl.set('');
      this.editandoId.set(null);
      this.solicitantesEdicion.set([]);
      this.mostrarForm.set(true);
      irAlFormulario('campo-nombre');
    }
    this.ok.set('');
    this.error.set('');
  }

  private cerrarForm() {
    this.mostrarForm.set(false);
    this.editandoId.set(null);
    this.nueva = this.vacia();
    this.fotoUrl.set('');
    this.solicitantesEdicion.set([]);
  }

  // ---------- EDITAR ----------
  editar(m: Mascota) {
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
    this.cambioPendiente.set(null);
    this.mostrarForm.set(true);
    this.ok.set('');
    this.error.set('');
    // Si la mascota ya está adoptada o en proceso, mostramos quién está involucrado
    this.solicitantesEdicion.set([]);
    if (m.estado_adopcion !== 'Disponible') this.traerSolicitantes(m, l => this.solicitantesEdicion.set(l));
    irAlFormulario('campo-nombre');
  }

  guardar() {
    this.enviando.set(true);
    this.error.set('');
    const edad = this.nueva.edad_meses;
    const cuerpo = {
      ...this.nueva,
      raza: this.nueva.raza || null,
      descripcion: this.nueva.descripcion || null,
      edad_meses: edad === null || edad === undefined ? null : Number(edad),
      imagen_url: this.fotoUrl() || null,
      // el backend ignora este valor si eres encargado
      refugio_id: this.nueva.refugio_id ?? 0
    };
    const id = this.editandoId();
    const peticion = id === null
      ? this.api.post<Mascota>('/mascotas/', cuerpo)
      : this.api.put<Mascota>(`/mascotas/${id}`, cuerpo);

    peticion.subscribe({
      next: (guardada) => {
        this.enviando.set(false);
        this.ok.set(id === null ? 'Mascota registrada.' : 'Mascota actualizada.');
        this.ultimaEditadaId.set(guardada.id);   // la mascota guardada sube al primer lugar
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
  // Si la mascota ya estaba "Adoptada" o "En Proceso" primero mostramos quién está involucrado
  // y pedimos confirmación. Si estaba "Disponible", cambia directo.
  pedirCambioEstado(m: Mascota, nuevo: string, selector: HTMLSelectElement) {
    const estado = nuevo as EstadoMascota;
    selector.value = m.estado_adopcion;       // el selector no cambia hasta que se confirme
    if (estado === m.estado_adopcion) return;
    this.error.set('');
    this.ok.set('');

    if (m.estado_adopcion === 'Disponible') {
      this.aplicarEstado(m, estado);
      return;
    }
    this.cambioPendiente.set({ mascota: m, nuevoEstado: estado });
    this.solicitantes.set([]);
    this.cargandoSolicitantes.set(true);
    this.traerSolicitantes(m, lista => {
      this.solicitantes.set(lista);
      this.cargandoSolicitantes.set(false);
    });
  }

  /** ¿La mascota ya tiene una adopción aprobada? Entonces no puede volver a otro estado. */
  bloqueado(): boolean {
    const c = this.cambioPendiente();
    return !!c && c.mascota.estado_adopcion === 'Adoptada' && c.nuevoEstado !== 'Adoptada'
      && !!this.adoptante(this.solicitantes());
  }

  confirmarCambio() {
    const c = this.cambioPendiente();
    if (!c || this.bloqueado()) return;
    this.cambioPendiente.set(null);
    this.aplicarEstado(c.mascota, c.nuevoEstado);
  }

  cancelarCambio() {
    this.cambioPendiente.set(null);
  }

  private aplicarEstado(m: Mascota, estado: EstadoMascota) {
    this.api.patch(`/mascotas/${m.id}`, { estado_adopcion: estado }).subscribe({
      next: () => {
        this.ok.set(`${m.nombre} ahora está "${estado}".`);
        this.ultimaEditadaId.set(m.id);
        this.cargar();
      },
      error: (err) => { this.error.set(this.api.mensajeError(err)); this.cargar(); }
    });
  }

  // ---------- ELIMINAR (con confirmación en la misma fila) ----------
  pedirEliminar(m: Mascota) {
    this.confirmandoId.set(m.id);
    this.forzarId.set(null);
    this.ok.set('');
    this.error.set('');
  }

  cancelarEliminar() {
    this.confirmandoId.set(null);
  }

  eliminar(m: Mascota) {
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
        if ((err as { status?: number }).status === 409 && this.esAdmin) this.forzarId.set(m.id);
      }
    });
  }

  // Solo administrador: borra la mascota Y sus solicitudes/seguimientos
  eliminarForzado(m: Mascota) {
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
