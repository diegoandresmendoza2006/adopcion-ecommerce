import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';

@Injectable({
  providedIn: 'root'
})
export class TiendaService {
  private apiUrl = API_URL;

  constructor(private http: HttpClient) {}

  // Obtener la lista de productos de la tienda
  getProductos(): Observable<any> {
    return this.http.get(`${this.apiUrl}/productos/`);
  }

  // Enviar la compra del carrito: { items: [{ producto_id, cantidad }] }
  procesarCompra(compraData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/compras/`, compraData);
  }
}