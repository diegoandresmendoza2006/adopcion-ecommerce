import { TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideZonelessChangeDetection(), provideRouter([]), provideHttpClient()],
    }).compileComponents();
  });

  it('se crea la app', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('sin sesión el menú solo muestra Login y Registro', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const texto = fixture.nativeElement.textContent;
    expect(texto).toContain('Login');
    expect(texto).toContain('Registro');
    expect(texto).not.toContain('Carrito');
  });
});