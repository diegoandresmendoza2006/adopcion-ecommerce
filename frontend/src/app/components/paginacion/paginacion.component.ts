import { Component, computed, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgIcon } from '@ng-icons/core';

// Barra de páginas reutilizable (catálogo y tienda).
// Uso: <app-paginacion [pagina]="pagina()" [paginas]="paginas()" [total]="total()" [porPagina]="12" (cambiar)="irAPagina($event)">
@Component({
  selector: 'app-paginacion',
  standalone: true,
  imports: [CommonModule, NgIcon],
  template: `
    @if (total() > 0) {
      <div class="pag">
        <span class="info">Mostrando {{ desde() }}–{{ hasta() }} de {{ total() }}</span>

        @if (paginas() > 1) {
          <nav aria-label="Páginas">
            <button type="button" (click)="ir(pagina() - 1)" [disabled]="pagina() <= 1" class="flecha"><ng-icon name="lucideChevronLeft" size="16" /> Anterior</button>
            @for (n of numeros(); track $index) {
              @if (n === 0) {
                <span class="puntos">…</span>
              } @else {
                <button type="button" [class.actual]="n === pagina()" [attr.aria-current]="n === pagina() ? 'page' : null" (click)="ir(n)">{{ n }}</button>
              }
            }
            <button type="button" (click)="ir(pagina() + 1)" [disabled]="pagina() >= paginas()" class="flecha">Siguiente <ng-icon name="lucideChevronRight" size="16" /></button>
          </nav>
        }
      </div>
    }
  `,
  styles: [`
    .pag { display: flex; flex-direction: column; align-items: center; gap: 10px; margin: 26px 0 10px; }
    .info { color: #666; font-size: 13px; }
    nav { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; }
    button { min-width: 38px; padding: 8px 12px; border: 1px solid #cbd5e1; background: #fff; color: #334155;
             border-radius: 6px; cursor: pointer; font-size: 14px; }
    button:hover:not(:disabled):not(.actual) { background: #f1f5f9; }
    button.actual { background: #28a745; border-color: #28a745; color: #fff; font-weight: bold; cursor: default; }
    button:disabled { opacity: .45; cursor: not-allowed; }
    .flecha { display: inline-flex; align-items: center; gap: 4px; }
    .puntos { align-self: center; color: #94a3b8; padding: 0 4px; }
  `]
})
export class PaginacionComponent {
  pagina = input.required<number>();
  paginas = input.required<number>();
  total = input.required<number>();
  porPagina = input.required<number>();
  cambiar = output<number>();

  desde = computed(() => (this.pagina() - 1) * this.porPagina() + 1);
  hasta = computed(() => Math.min(this.total(), this.pagina() * this.porPagina()));

  // 1 … 4 5 6 … 20   (el 0 representa los "…")
  numeros = computed(() => {
    const ultima = this.paginas();
    const actual = this.pagina();
    const visibles = [...new Set([1, ultima, actual - 1, actual, actual + 1])]
      .filter(n => n >= 1 && n <= ultima)
      .sort((a, b) => a - b);
    const resultado: number[] = [];
    visibles.forEach((n, i) => {
      if (i > 0 && n - visibles[i - 1] > 1) resultado.push(0);
      resultado.push(n);
    });
    return resultado;
  });

  ir(n: number) {
    if (n < 1 || n > this.paginas() || n === this.pagina()) return;
    this.cambiar.emit(n);
  }
}
