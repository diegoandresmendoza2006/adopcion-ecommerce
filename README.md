# Paws&Shop

Plataforma web de **adopción de mascotas y tienda solidaria**. Los usuarios adoptan y compran;
los encargados gestionan su refugio; el administrador supervisa todo el sistema.

- **Frontend:** Angular (standalone, signals, zoneless), iconos con Lucide (`@ng-icons`)
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL (esquema `adopcion`)
- **Fotos:** Cloudinary (subida desde el navegador)
- **Autenticación:** JWT con roles

## Roles

| Rol | Qué puede hacer | Menú |
|---|---|---|
| **Usuario** | Ver catálogo, enviar solicitudes de adopción con formulario completo, comprar en la tienda, favoritos y carrito, ver trámites (con el mensaje del refugio) y seguimientos propios | Catálogo, Tienda, Favs, Carrito, Trámites, Mis Seg. |
| **Encargado** | CRUD de mascotas y productos de su refugio, aprobar/rechazar solicitudes con comentario, ver quién adoptó o aspira a una mascota, registrar seguimientos | Mascotas, Productos, Solicitudes, Ver Seg. |
| **Administrador** | Dashboard con métricas y reporte Excel, gestión de refugios y encargados, auditoría, y borrado total de una mascota con historial | Mascotas, Productos, Refugios, Encargados, Dashboard, Auditoría |

Cada rol entra a su pantalla de inicio: el administrador al Dashboard, el encargado a Mascotas y el usuario al Catálogo.

Mockups de las pantallas: [docs/mockups/mockups.html](docs/mockups/mockups.html) · Base de datos: [docs/base-de-datos.md](docs/base-de-datos.md) · Protocolo de paginación: [docs/paginacion.md](docs/paginacion.md)

## Requisitos
- Python 3.12+ · Node 22+ · PostgreSQL 14+

## Puesta en marcha

### 1. Base de datos
```sql
CREATE DATABASE adopcion_ecommerce;
CREATE USER usuario_adopcion WITH PASSWORD 'tu_clave';
GRANT ALL ON DATABASE adopcion_ecommerce TO usuario_adopcion;
```
Luego carga el esquema y aplica la migración del formulario de adopción:
```bash
psql -U usuario_adopcion -d adopcion_ecommerce -f schema.sql
psql -U postgres -h localhost -d adopcion_ecommerce -f backend/migrations/002_formulario_adopcion.sql
```
La migración agrega a `solicitudes_adopcion` los datos del formulario completo (fecha de nacimiento,
vivienda, entorno, experiencia previa, disponibilidad) y el comentario del encargado. Debe ejecutarla
el **usuario dueño de las tablas** (por ejemplo `postgres`), porque modifica la estructura. Es segura de
repetir y conserva las solicitudes existentes. Si `schema.sql` ya fue generado después de esta
migración, ya incluye esas columnas.

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
Genera una `SECRET_KEY` con:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
Es **obligatoria** (mínimo 16 caracteres): si falta, el backend no arranca. La contraseña de los usuarios exige mínimo 8 caracteres.


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
`npm install` incluye la librería de iconos (`@ng-icons/core` y `@ng-icons/lucide`).
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
| `/adopciones` | `/`, `/mis`, `/mascota/{id}` | `/` | | `/{id}` (aprobar/rechazar), `/{id}/comentario` | |
| `/compras` | `/mis` | `/` | | | |
| `/seguimientos` | `/`, `/mis` | `/` | | | |
| `/admin` | `/metricas`, `/reporte.xlsx`, `/auditoria`, `/encargados` | `/encargados` | | | |

- `GET /adopciones/mascota/{id}`: quién adoptó a una mascota o quiénes aspiran a ella (Encargado y Admin).
- `PATCH /adopciones/{id}/comentario`: dejar o corregir el comentario para el adoptante (Encargado y Admin).
- Las búsquedas `/mascotas/buscar` y `/productos/buscar` son paginadas en el servidor; el contrato de la
  respuesta está en [docs/paginacion.md](docs/paginacion.md).

### Formulario de adopción
`POST /adopciones/` recibe: nombre completo, fecha de nacimiento, teléfono, correo y dirección; tipo de
vivienda (propia o arrendada) y si permite mascotas; patio o jardín, cercas y personas en el hogar;
experiencia previa (si tuvo mascotas, vacunación y esterilización); horas al día que estaría solo el
animal y quién se hace cargo en viajes o emergencias. El motivo es opcional. Los campos obligatorios se
marcan con `*` en el formulario.

### Reglas de negocio
- Una mascota con solicitudes no se elimina (409); solo el admin puede forzarlo.
- Una mascota con adopción aprobada no puede volver a "Disponible".
- La edad de una mascota se guarda en meses y no puede superar 240 (422).
- Un producto que ya está en pedidos no se elimina (409); se deja con stock 0.
- Un refugio con mascotas o usuarios asignados no se elimina (409).
- Un encargado solo gestiona mascotas de su refugio.
- Las compras validan stock y se hacen en una sola transacción.
- Al aprobar una solicitud, la mascota pasa a "Adoptada".
- Solo mayores de 18 años pueden enviar el formulario de adopción (422).
- Si el adoptante ya tuvo mascotas, debe indicar si estaban vacunadas y esterilizadas; si no tuvo, esos datos se descartan.
- Al aprobar una solicitud, las demás solicitudes en revisión de esa misma mascota se rechazan automáticamente con un mensaje (400 si la mascota ya estaba adoptada).
- El encargado puede dejar un comentario al aprobar o rechazar, y corregirlo después; el adoptante lo ve en "Trámites".
- Al cambiar el estado de una mascota a "Adoptada" o "En proceso", el encargado ve quién la adoptó o la lista de aspirantes.

## Pruebas
Las pruebas del backend usan una base SQLite temporal, no tocan tu PostgreSQL:
```bash
cd backend
pip install -r requirements-dev.txt
pytest -v
```
Cubren autenticación, roles, mascotas (incluido el límite de 240 meses), formulario de adopción, comentarios del encargado, aspirantes y compras.


## Estructura
```
backend/app/        main.py, models.py, schemas.py, security.py, routers/
backend/tests/      pruebas con pytest
backend/migrations/ cambios de base de datos sobre schema.sql
frontend/src/app/   components/, services/, models/, guards/, iconos.ts, app.routes.ts
docs/               base-de-datos.md, paginacion.md, mockups/
```

## Base de datos
Esquema `adopcion` con 12 tablas: roles, refugios, usuarios, mascotas, solicitudes_adopcion,
seguimiento_adopciones, categorias_productos, productos, seleccion_productos,
ordenes_compra, detalles_orden y auditoria.

## Autor
Diego — Proyecto de Desarrollo Orientado a Plataformas.