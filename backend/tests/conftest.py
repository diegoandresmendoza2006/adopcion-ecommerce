"""Configuración de las pruebas.

Las pruebas NO tocan tu PostgreSQL: usan una base SQLite temporal que imita el esquema
`adopcion`. Cada prueba empieza con datos limpios (3 roles, 2 refugios, usuarios de ejemplo).

Ejecutar (desde la carpeta backend, con el venv activo):
    pip install -r requirements-dev.txt
    pytest -v
"""
import os
import sys
import tempfile

# Variables de entorno ANTES de importar la app (security.py y database.py las leen al importarse)
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/main.db"
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas-0123456789"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app import database, models, security
from app.main import app


@event.listens_for(database.engine, "connect")
def _adjuntar_esquema(conexion, _):
    # SQLite no tiene esquemas: "adopcion" se simula con un segundo archivo adjunto
    conexion.execute(f"ATTACH DATABASE '{_tmp}/adopcion.db' AS adopcion")


CLAVE = "Clave1234"
_HASH = security.hash_password(CLAVE)   # se calcula una sola vez (bcrypt es lento a propósito)

# id -> (rol, refugio)
USUARIOS = {
    1: ("admin", 1, None),
    2: ("enc1", 2, 1),     # encargado del refugio 1
    3: ("ana", 3, None),
    4: ("beto", 3, None),
    5: ("enc2", 2, 2),     # encargado del refugio 2
}


@pytest.fixture()
def db():
    database.Base.metadata.drop_all(database.engine)
    database.Base.metadata.create_all(database.engine)
    sesion = database.SessionLocal()
    sesion.add_all([models.Rol(id=1, nombre="Administrador"), models.Rol(id=2, nombre="Encargado"),
                    models.Rol(id=3, nombre="Usuario"),
                    models.Refugio(id=1, nombre="Refugio Uno"), models.Refugio(id=2, nombre="Refugio Dos")])
    sesion.commit()
    sesion.add_all([
        models.Usuario(id=i, nombre_completo=f"{nombre.capitalize()} Prueba", email=f"{nombre}@correo.com",
                       password_hash=_HASH, rol_id=rol, refugio_id=refugio)
        for i, (nombre, rol, refugio) in USUARIOS.items()
    ])
    sesion.add_all([
        models.Mascota(id=1, nombre="Rex", especie="Perro", estado_adopcion="Disponible", refugio_id=1),
        models.Mascota(id=2, nombre="Misi", especie="Gato", estado_adopcion="Disponible", refugio_id=2),
        models.CategoriaProducto(id=1, nombre="Alimento"),
    ])
    sesion.commit()
    sesion.add(models.Producto(id=1, nombre="Croquetas", precio=10, stock=2, categoria_id=1))
    sesion.commit()
    yield sesion
    sesion.close()


@pytest.fixture()
def client(db):
    return TestClient(app)


def _cabecera(usuario_id: int) -> dict:
    _, rol, _ = USUARIOS[usuario_id]
    token = security.create_access_token({"usuario_id": usuario_id, "rol_id": rol})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin():
    return _cabecera(1)


@pytest.fixture()
def enc1():
    return _cabecera(2)


@pytest.fixture()
def enc2():
    return _cabecera(5)


@pytest.fixture()
def ana():
    return _cabecera(3)


@pytest.fixture()
def beto():
    return _cabecera(4)


@pytest.fixture()
def formulario():
    """Un formulario de adopción válido; cada prueba cambia solo el campo que quiere probar."""
    return dict(
        mascota_id=1,
        nombre_contacto="Ana Prueba", fecha_nacimiento="1995-04-10", telefono="3001234567",
        email_contacto="ana@correo.com", direccion="Calle 1 # 2-3", tipo_vivienda="Arrendada",
        vivienda_permite_mascotas=True, tiene_patio=True, tiene_cercas=False, personas_hogar=3,
        tuvo_mascotas=True, mascotas_vacunadas=True, mascotas_esterilizadas=False,
        horas_solo=6, responsable_viajes="Mi mamá", motivo="Quiero compañía",
    )
