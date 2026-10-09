import { ChangeDetectorRef, Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { NgIcon } from '@ng-icons/core';
import { ApiService } from '../../services/api.service';
import { edadDesdeNacimiento } from '../../services/formato';
import { FormularioAdopcion, Mascota, Usuario } from '../../models/modelos';

@Component({
  selector: 'app-solicitud-adopcion',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, NgIcon],
  templateUrl: './solicitud-adopcion.component.html',
  styleUrls: ['./solicitud-adopcion.component.css']
})
export class SolicitudAdopcionComponent implements OnInit {
  mascota = signal<Mascota | null>(null);
  error = signal('');
  ok = signal('');
  enviando = signal(false);

  // Lo que escribe el adoptante: el ENCARGADO lo verá al revisar la solicitud.
  // null = todavía no ha contestado (las preguntas Sí/No empiezan sin marcar).
  datos: FormularioAdopcion = {
    nombre_contacto: '',
    fecha_nacimiento: '',
    telefono: '',
    email_contacto: '',
    direccion: '',
    tipo_vivienda: '',
    vivienda_permite_mascotas: null,
    tiene_patio: null,
    tiene_cercas: null,
    personas_hogar: null,
    tuvo_mascotas: null,
    mascotas_vacunadas: null,
    mascotas_esterilizadas: null,
    horas_solo: null,
    responsable_viajes: '',
    motivo: ''
  };

  // Fecha máxima del calendario: hace 18 años (solo mayores de edad pueden adoptar)
  readonly maxNacimiento = (() => {
    const d = new Date();
    d.setFullYear(d.getFullYear() - 18);
    return d.toISOString().slice(0, 10);
  })();

  constructor(private route: ActivatedRoute, private api: ApiService, private router: Router, private cd: ChangeDetectorRef) {}

  ngOnInit(): void {
    const id = this.route.snapshot.queryParamMap.get('mascota');
    if (!id) {
      this.error.set('Primero elige una mascota en el catálogo y pulsa "Adoptar".');
      return;
    }
    this.api.get<Mascota>(`/mascotas/${id}`).subscribe({
      next: (m) => this.mascota.set(m),
      error: (err) => this.error.set(this.api.mensajeError(err, 'No se encontró la mascota.'))
    });

    // Adelantamos trabajo: rellenamos nombre y correo con los de su cuenta (puede cambiarlos)
    this.api.get<Usuario>('/auth/me').subscribe({
      next: (u) => {
        if (!this.datos.nombre_contacto) this.datos.nombre_contacto = u.nombre_completo;
        if (!this.datos.email_contacto) this.datos.email_contacto = u.email;
        this.cd.markForCheck();   // app "zoneless": avisamos que `datos` cambió para que se pinte en pantalla
      },
      error: () => {}   // si falla, simplemente queda vacío
    });
  }

  // Edad calculada para avisar antes de enviar (el backend vuelve a validarla)
  edad(): number | null {
    return edadDesdeNacimiento(this.datos.fecha_nacimiento);
  }

  esMenor(): boolean {
    const e = this.edad();
    return e !== null && e < 18;
  }

  enviarSolicitud() {
    const m = this.mascota();
    if (!m || this.esMenor()) return;

    const d = this.datos;
    const sinMascotasPrevias = d.tuvo_mascotas === false;
    const cuerpo = {
      ...d,
      mascota_id: m.id,
      // Si nunca tuvo mascotas, estas dos preguntas no aplican
      mascotas_vacunadas: sinMascotasPrevias ? null : d.mascotas_vacunadas,
      mascotas_esterilizadas: sinMascotasPrevias ? null : d.mascotas_esterilizadas,
      motivo: d.motivo.trim() || null
    };

    this.error.set('');
    this.enviando.set(true);
    this.api.post('/adopciones/', cuerpo).subscribe({
      next: () => {
        this.ok.set('¡Solicitud enviada con éxito! Un encargado revisará tu formulario.');
        setTimeout(() => this.router.navigate(['/mis-solicitudes']), 1500);
      },
      error: (err) => {
        this.enviando.set(false);
        this.error.set(this.api.mensajeError(err));
        if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  }
}
