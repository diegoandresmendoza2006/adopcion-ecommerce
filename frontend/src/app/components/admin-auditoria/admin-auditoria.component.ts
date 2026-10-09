import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { RegistroAuditoria } from '../../models/modelos';

@Component({
  selector: 'app-admin-auditoria',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './admin-auditoria.component.html',
  styleUrls: ['./admin-auditoria.component.css']
})
export class AdminAuditoriaComponent implements OnInit {
  registrosAuditoria = signal<RegistroAuditoria[]>([]);
  error = signal('');

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.get<RegistroAuditoria[]>('/admin/auditoria').subscribe({
      next: (data) => this.registrosAuditoria.set(data),
      error: (err) => this.error.set(this.api.mensajeError(err))
    });
  }
}
