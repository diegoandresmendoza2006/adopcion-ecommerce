import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { SubirFotoComponent } from '../subir-foto/subir-foto.component';
import { AuthService } from '../../services/auth.service';
import { ROL_ADMIN } from '../../services/api.config';
import { edadTexto } from '../../services/formato';

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
  fotoUrl = signal('');
  subiendoFoto = signal(false);

  nueva: any = this.vacia();

  constructor(private api: ApiService, private auth: AuthService) {
    this.esAdmin = this.auth.rolId() === ROL_ADMIN;
  }

  private vacia() {
    return { nombre: '', especie: 'Perro', raza: '', edad_meses: 12, descripcion: '', imagen_url: '', refugio_id: null, estado_adopcion: 'Disponible' };
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

  registrarMascota() {
    this.mostrarForm.update(v => !v);
    this.ok.set('');
    this.error.set('');
  }

  guardar() {
    this.enviando.set(true);
    this.error.set('');
    const cuerpo = {
      ...this.nueva,
      edad_meses: Number(this.nueva.edad_meses),
      imagen_url: this.fotoUrl() || null,
      // el backend ignora este valor si eres encargado
      refugio_id: this.nueva.refugio_id ?? 0
    };
    this.api.post('/mascotas/', cuerpo).subscribe({
      next: () => {
        this.enviando.set(false);
        this.ok.set('Mascota registrada.');
        this.mostrarForm.set(false);
        this.nueva = this.vacia();
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