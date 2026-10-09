# Despliegue en la nube

La app corre en tres servicios gratuitos. Las fotos ya viven en Cloudinary, así que no se pierden al reiniciar el servidor.

| Pieza | Servicio | Qué guarda o ejecuta |
|---|---|---|
| Base de datos | Neon (PostgreSQL) | Esquema `adopcion` |
| Backend | Render (Web Service) | FastAPI con `uvicorn` |
| Frontend | Render (Static Site) | Angular compilado |
| Fotos | Cloudinary | Imágenes de mascotas y productos |

**Direcciones publicadas**

- Frontend: https://paws-shop.onrender.com
- API: https://paws-shop-api.onrender.com (documentación en `/docs`)

## Variables de entorno del backend (en Render)

| Variable | Valor |
|---|---|
| `DATABASE_URL` | Cadena de Neon con el prefijo `postgresql+psycopg://` y `?sslmode=require` |
| `SECRET_KEY` | Clave nueva de 16 o más caracteres, distinta a la local |
| `CORS_ORIGINS` | Dirección del frontend, sin `/` al final |
| `PYTHON_VERSION` | `3.12.8` |

## Comandos de Render

- **Backend** (Root Directory `backend`): build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Frontend** (Root Directory `frontend`): build `npm install && npm run build`, publish `dist/frontend/browser`, variable `NODE_VERSION=22.22.3`, y una regla Rewrite `/*` a `/index.html` para que funcionen las rutas de Angular.

## Base de datos nueva

1. Importar el esquema sin los permisos del usuario local:
   `grep -v usuario_adopcion schema.sql | grep -v '^\\' > schema_nube.sql` y luego `psql "<cadena de Neon>" -f schema_nube.sql`.
2. Crear roles y administrador: `python scripts/crear_admin.py` desde `backend`, con `DATABASE_URL` apuntando a Neon.

## Nota sobre el plan gratuito

El backend se duerme tras 15 minutos sin tráfico y la primera petición tarda cerca de un minuto en despertarlo.
