import { Component, forwardRef, input, signal } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { NgIcon } from '@ng-icons/core';

// Campo de contraseña con el "ojito" para mostrar u ocultar lo que escribes.
// Funciona igual que un <input> normal con ngModel:
//   <app-campo-password inputId="clave" name="password" [(ngModel)]="datos.password" required minlength="6" />
@Component({
  selector: 'app-campo-password',
  standalone: true,
  imports: [NgIcon],
  providers: [{ provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => CampoPasswordComponent), multi: true }],
  template: `
    <div class="caja">
      <input [id]="inputId()" [type]="visible() ? 'text' : 'password'" [value]="valor()"
             [placeholder]="placeholder()" [attr.autocomplete]="autocomplete()" [disabled]="deshabilitado()"
             (input)="alEscribir($event)" (blur)="alSalir()">
      <button type="button" class="ojo" (click)="visible.set(!visible())"
              [attr.aria-label]="visible() ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              [attr.aria-pressed]="visible()" [disabled]="deshabilitado()">
        <ng-icon [name]="visible() ? 'lucideEyeOff' : 'lucideEye'" size="18" />
      </button>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .caja { position: relative; }
    input { width: 100%; padding: 12px 44px 12px 14px; border: 1px solid #d1d5db; border-radius: 8px;
            box-sizing: border-box; font-size: 15px; outline: none; font-family: inherit;
            transition: border-color .15s, box-shadow .15s; }
    input:focus { border-color: #28a745; box-shadow: 0 0 0 3px rgba(40, 167, 69, .18); }
    .ojo { position: absolute; top: 0; right: 0; height: 100%; width: 42px; display: flex; align-items: center;
           justify-content: center; border: none; background: transparent; color: #6b7280; cursor: pointer; }
    .ojo:hover:not(:disabled) { color: #28a745; }
  `]
})
export class CampoPasswordComponent implements ControlValueAccessor {
  inputId = input('clave');
  placeholder = input('');
  autocomplete = input('current-password');

  valor = signal('');
  visible = signal(false);
  deshabilitado = signal(false);

  private alCambiar: (v: string) => void = () => {};
  private alTocar: () => void = () => {};

  // ----- ControlValueAccessor: así ngModel / formularios hablan con este campo -----
  writeValue(v: string | null): void { this.valor.set(v ?? ''); }
  registerOnChange(fn: (v: string) => void): void { this.alCambiar = fn; }
  registerOnTouched(fn: () => void): void { this.alTocar = fn; }
  setDisabledState(d: boolean): void { this.deshabilitado.set(d); }

  alEscribir(e: Event) {
    const v = (e.target as HTMLInputElement).value;
    this.valor.set(v);
    this.alCambiar(v);
  }

  alSalir() { this.alTocar(); }
}
