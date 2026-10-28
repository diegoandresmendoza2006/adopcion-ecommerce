import { Component, OnDestroy, effect, input, model, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgIcon } from '@ng-icons/core';
import { ImagenService, TipoImagen } from '../../services/imagen.service';

// Zona para ARRASTRAR una foto o hacer clic para SELECCIONARLA.
// Uso:  <app-subir-foto tipo="mascotas" [subcarpeta]="raza" [especie]="especie" [(url)]="fotoUrl"
//                       (subiendoChange)="subiendoFoto.set($event)"></app-subir-foto>
// La foto se sube al BACKEND (que la guarda en Cloudinary, en carpetas ordenadas). Si el usuario la cambia, la quita
// o cierra el formulario SIN guardar, esa foto se descarta en el servidor para no dejar basura.
// Cuando el formulario se guarda bien, el padre llama a confirmar() para que la foto ya no se descarte.
@Component({
  selector: 'app-subir-foto',
  standalone: true,
  imports: [CommonModule, NgIcon],
  template: `
    @if (url()) {
      <div class="vista">
        <img [src]="url()" alt="Vista previa">
        <div class="acciones">
          <button type="button" (click)="entrada.click()">Cambiar foto</button>
          <button type="button" class="quitar" (click)="quitar()">Quitar</button>
        </div>
      </div>
    } @else {
      <div class="zona" [class.activa]="arrastrando()" [class.ocupada]="subiendo()"
           tabindex="0" role="button" aria-label="Subir foto"
           (click)="entrada.click()" (keydown.enter)="entrada.click()"
           (dragover)="alArrastrar($event)" (dragleave)="alSalir($event)" (drop)="alSoltar($event)">
        @if (subiendo()) {
          <div class="icono"><ng-icon name="lucideClock" size="34" /></div>
          <p><strong>Subiendo foto...</strong></p>
        } @else {
          <div class="icono"><ng-icon name="lucideCamera" size="34" /></div>
          <p><strong>Arrastra una foto aquí</strong></p>
          <p class="sub">o haz clic para seleccionarla</p>
          <p class="sub">JPG, PNG o WEBP · máximo 5 MB</p>
        }
      </div>
    }

    <input #entrada type="file" accept="image/*" hidden (change)="alSeleccionar($event)">

    @if (error()) { <p class="msg-error">{{ error() }}</p> }

    <p class="enlace">
      <a href="#" (click)="$event.preventDefault(); verUrl.set(!verUrl())">
        {{ verUrl() ? 'Ocultar enlace' : '¿Prefieres pegar el enlace de una imagen?' }}
      </a>
    </p>
    @if (verUrl()) {
      <input class="campo-url" type="text" placeholder="https://..." [value]="url()"
             (input)="alEscribirUrl($event)">
    }
  `,
  styles: [`
    :host { display: block; }
    .zona { border: 2px dashed #9aa5b1; border-radius: 10px; padding: 24px 12px; text-align: center;
            cursor: pointer; background: #fafbfc; transition: all .15s; }
    .zona:hover, .zona:focus { border-color: #28a745; background: #f1faf3; outline: none; }
    .zona.activa { border-color: #28a745; background: #e3f6e8; transform: scale(1.01); }
    .zona.ocupada { cursor: progress; opacity: .8; }
    .icono { color: #6b7280; line-height: 1; }
    .zona p { margin: 4px 0; }
    .sub { color: #666; font-size: 12px; }
    .vista { display: flex; align-items: center; gap: 14px; }
    .vista img { max-height: 120px; max-width: 180px; border-radius: 8px; object-fit: cover; border: 1px solid #ddd; }
    .acciones { display: flex; flex-direction: column; gap: 6px; }
    .acciones button { padding: 6px 12px; border-radius: 4px; border: 1px solid #28a745; background: #fff; color: #28a745; cursor: pointer; }
    .acciones .quitar { border-color: #b42318; color: #b42318; }
    .enlace { margin: 8px 0 0; font-size: 12px; }
    .campo-url { width: 100%; box-sizing: border-box; margin-top: 6px; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
  `]
})
export class SubirFotoComponent implements OnDestroy {
  url = model<string>('');
  subiendoChange = output<boolean>();

  // Dónde se organiza la foto en Cloudinary
  tipo = input<TipoImagen>('mascotas');
  subcarpeta = input<string>('');   // raza (mascotas) o categoría (productos)
  especie = input<string>('');      // solo mascotas

  // Foto subida en esta sesión que todavía NO se guardó en la base de datos
  private pendiente: string | null = null;

  arrastrando = signal(false);
  subiendo = signal(false);
  error = signal('');
  verUrl = signal(false);

  constructor(private imagenes: ImagenService) {
    // Si la foto pendiente deja de ser la actual (la cambiaron, la quitaron o el formulario cargó otra), se descarta
    effect(() => {
      const actual = this.url();
      if (this.pendiente && actual !== this.pendiente) this.descartarPendiente();
    });
  }

  /** El formulario se guardó bien: la foto ya pertenece a una mascota/producto y no debe descartarse. */
  confirmar() {
    this.pendiente = null;
  }

  ngOnDestroy() {
    this.descartarPendiente();   // formulario cerrado sin guardar
  }

  private descartarPendiente() {
    const url = this.pendiente;
    this.pendiente = null;
    if (url) this.imagenes.descartar(url).subscribe({ error: () => {} });
  }

  alArrastrar(e: DragEvent) {
    e.preventDefault();
    this.arrastrando.set(true);
  }

  alSalir(e: DragEvent) {
    e.preventDefault();
    this.arrastrando.set(false);
  }

  alSoltar(e: DragEvent) {
    e.preventDefault();
    this.arrastrando.set(false);
    const archivo = e.dataTransfer?.files?.[0];
    if (archivo) this.procesar(archivo);
  }

  alSeleccionar(e: Event) {
    const input = e.target as HTMLInputElement;
    const archivo = input.files?.[0];
    if (archivo) this.procesar(archivo);
    input.value = ''; // permite volver a elegir el mismo archivo
  }

  alEscribirUrl(e: Event) {
    this.url.set((e.target as HTMLInputElement).value);
  }

  quitar() {
    this.url.set('');
    this.error.set('');
  }

  private procesar(archivo: File) {
    this.error.set('');
    const problema = this.imagenes.validar(archivo);
    if (problema) {
      this.error.set(problema);
      return;
    }
    this.subiendo.set(true);
    this.subiendoChange.emit(true);
    this.imagenes.subir(archivo, this.tipo(), this.subcarpeta(), this.especie()).subscribe({
      next: (url) => {
        this.descartarPendiente();   // si ya había una foto sin guardar, se borra antes de poner la nueva
        this.pendiente = url;
        this.url.set(url);
        this.subiendo.set(false);
        this.subiendoChange.emit(false);
      },
      error: (err) => {
        this.subiendo.set(false);
        this.subiendoChange.emit(false);
        const detalle = err?.error?.detail;
        this.error.set(typeof detalle === 'string' ? detalle : 'No se pudo subir la foto. Inténtalo de nuevo.');
        if (err?.status === 503) this.verUrl.set(true);   // servidor sin Cloudinary: se puede pegar un enlace
      }
    });
  }
}