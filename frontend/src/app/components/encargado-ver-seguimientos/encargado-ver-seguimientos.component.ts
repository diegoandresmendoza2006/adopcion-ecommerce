import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { Seguimiento } from '../../models/modelos';

@Component({
  selector: 'app-encargado-ver-seguimientos',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './encargado-ver-seguimientos.component.html',
  styleUrls: ['./encargado-ver-seguimientos.component.css']
})
export class EncargadoVerSeguimientosComponent implements OnInit {
  seguimientosRecibidos = signal<Seguimiento[]>([]);
  error = signal('');

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.get<Seguimiento[]>('/seguimientos/').subscribe({
      next: (data) => this.seguimientosRecibidos.set(data),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }
}
