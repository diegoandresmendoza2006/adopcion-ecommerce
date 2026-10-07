import { Component, model, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ImagenService } from '../../services/imagen.service';

// Zona para ARRASTRAR una foto o hacer clic para SELECCIONARLA.
// Uso:  <app-subir-foto [(url)]="fotoUrl" (subiendoChange)="subiendoFoto.set($event)"></app-subir-foto>
@Component({
  selector: 'app-subir-foto',
  standalone: true,
  imports: [CommonModule],
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
          <div class="icono">⏳</div>
          <p><strong>Subiendo foto...</strong></p>
        } @else {
          <div class="icono">📷</div>
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
             (input)="url.set($any($event.target).value)">
    }
  `,
  styles: [`
    :host { display: block; }
    .zona { border: 2px dashed #9aa5b1; border-radius: 10px; padding: 24px 12px; text-align: center;
            cursor: pointer; background: #fafbfc; transition: all .15s; }
    .zona:hover, .zona:focus { border-color: #28a745; background: #f1faf3; outline: none; }
    .zona.activa { border-color: #28a745; background: #e3f6e8; transform: scale(1.01); }
    .zona.ocupada { cursor: progress; opacity: .8; }
    .icono { font-size: 34px; }
    .zona p { margin: 4px 0; }
    .sub { color: #666; font-size: 12px; }
    .vista { display: flex; align-items: center; gap: 14px; }
    .vista img { max-height: 140px; max-width: 200px; border-radius: 8px; object-fit: contain; background: #f4f6f8; border: 1px solid #ddd; }
    .acciones { display: flex; flex-direction: column; gap: 6px; }
    .acciones button { padding: 6px 12px; border-radius: 4px; border: 1px solid #28a745; background: #fff; color: #28a745; cursor: pointer; }
    .acciones .quitar { border-color: #b42318; color: #b42318; }
    .enlace { margin: 8px 0 0; font-size: 12px; }
    .campo-url { width: 100%; box-sizing: border-box; margin-top: 6px; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
  `]
})
export class SubirFotoComponent {
  url = model<string>('');
  subiendoChange = output<boolean>();

  arrastrando = signal(false);
  subiendo = signal(false);
  error = signal('');
  verUrl = signal(false);

  constructor(private imagenes: ImagenService) {}

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
    if (!this.imagenes.configurado()) {
      this.error.set('Falta configurar Cloudinary: pon tu Cloud name y tu Upload preset en services/api.config.ts. Mientras tanto puedes pegar el enlace de una imagen.');
      this.verUrl.set(true);
      return;
    }

    this.subiendo.set(true);
    this.subiendoChange.emit(true);
    this.imagenes.subir(archivo).subscribe({
      next: (url) => {
        this.url.set(url);
        this.subiendo.set(false);
        this.subiendoChange.emit(false);
      },
      error: () => {
        this.subiendo.set(false);
        this.subiendoChange.emit(false);
        this.error.set('No se pudo subir la foto. Revisa que el Cloud name y el Upload preset sean correctos y que el preset sea "Unsigned".');
      }
    });
  }
}