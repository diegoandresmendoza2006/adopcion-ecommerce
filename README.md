# 🐾 Paws&Shop

Plataforma web de **adopción de mascotas y tienda solidaria**. Los usuarios adoptan y compran;
los encargados gestionan su refugio; el administrador supervisa todo el sistema.

- **Frontend:** Angular (standalone, signals, zoneless)
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL (esquema `adopcion`)
- **Fotos:** Cloudinary (subida desde el navegador)
- **Autenticación:** JWT con roles

## Roles

| Rol | Qué puede hacer |
|---|---|
| **Usuario** | Ver catálogo, enviar solicitudes de adopción, comprar en la tienda, favoritos y carrito, ver trámites y seguimientos propios |
| **Encargado** | CRUD de mascotas y productos de su refugio, aprobar/rechazar solicitudes, registrar seguimientos |
| **Administrador** | Dashboard con métricas y reporte Excel, gestión de refugios y encargados, auditoría, y borrado total de una mascota con historial |

## Requisitos
- Python 3.12+ · Node 22+ · PostgreSQL 14+

## Puesta en marcha

### 1. Base de datos
```sql
CREATE DATABASE adopcion_ecommerce;
CREATE USER usuario_adopcion WITH PASSWORD 'tu_clave';
GRANT ALL ON DATABASE adopcion_ecommerce TO usuario_adopcion;
```
Luego carga el esquema: `psql -U usuario_adopcion -d adopcion_ecommerce -f schema.sql`

### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
```
Crea `backend/.env`:
```
DATABASE_URL=postgresql+psycopg://usuario_adopcion:tu_clave@localhost:5432/adopcion_ecommerce
SECRET_KEY=una-clave-larga-y-aleatoria
```
Arranca:
```bash
uvicorn app.main:app --reload
```
Documentación interactiva: http://localhost:8000/docs

### 3. Frontend
```bash
cd frontend
npm install
ng serve
```
Abre http://localhost:4200

### 4. Fotos (Cloudinary)
En `frontend/src/app/services/api.config.ts` pon tu `CLOUDINARY_CLOUD_NAME` y tu
`CLOUDINARY_UPLOAD_PRESET` (preset **Unsigned**).

## API REST

Todas las rutas protegidas usan `Authorization: Bearer <token>`.

| Recurso | GET | POST | PUT | PATCH | DELETE |
|---|---|---|---|---|---|
| `/auth` | `/me` | `/registro`, `/login` | | | |
| `/mascotas` | `/`, `/buscar`, `/{id}`, `/gestion/inventario` | `/` | `/{id}` | `/{id}` | `/{id}` (`?forzar=true` solo admin) |
| `/productos` | `/`, `/buscar`, `/categorias` | `/` | `/{id}` | `/{id}` | `/{id}` |
| `/refugios` | `/` | `/` | `/{id}` | `/{id}` | `/{id}` |
| `/adopciones` | `/`, `/mis` | `/` | | `/{id}` (aprobar/rechazar) | |
| `/compras` | `/mis` | `/` | | | |
| `/seguimientos` | `/`, `/mis` | `/` | | | |
| `/admin` | `/metricas`, `/reporte.xlsx`, `/auditoria`, `/encargados` | `/encargados` | | | |

### Reglas de negocio
- Una mascota con solicitudes no se elimina (409); solo el admin puede forzarlo.
- Una mascota con adopción aprobada no puede volver a "Disponible".
- Un producto que ya está en pedidos no se elimina (409); se deja con stock 0.
- Un refugio con mascotas o usuarios asignados no se elimina (409).
- Un encargado solo gestiona mascotas de su refugio.
- Las compras validan stock y se hacen en una sola transacción.
- Al aprobar una solicitud, la mascota pasa a "Adoptada".

## Estructura
```
backend/app/    main.py, models.py, schemas.py, security.py, routers/
frontend/src/app/   components/, services/, guards/, app.routes.ts
```

## Base de datos
Esquema `adopcion` con 12 tablas: roles, refugios, usuarios, mascotas, solicitudes_adopcion,
seguimiento_adopciones, categorias_productos, productos, seleccion_productos,
ordenes_compra, detalles_orden y auditoria.

## Autor
Diego — Proyecto de Desarrollo Orientado a Plataformas.