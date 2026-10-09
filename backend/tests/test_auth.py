"""Registro, login y protección de endpoints."""
from tests.conftest import CLAVE


def test_registro_crea_usuario_normal(client):
    r = client.post("/auth/registro", json={"nombre_completo": "Nuevo Usuario", "email": "nuevo@correo.com",
                                            "password": "Clave1234"})
    assert r.status_code == 201
    assert r.json()["rol_id"] == 3
    assert "password" not in r.json() and "password_hash" not in r.json()


def test_registro_no_permite_hacerse_admin(client):
    """Aunque el cliente mande rol_id=1, el backend lo ignora."""
    r = client.post("/auth/registro", json={"nombre_completo": "Intruso", "email": "intruso@correo.com",
                                            "password": "Clave1234", "rol_id": 1, "refugio_id": 1})
    assert r.status_code == 201
    assert r.json()["rol_id"] == 3


def test_registro_correo_repetido(client):
    r = client.post("/auth/registro", json={"nombre_completo": "Otra Ana", "email": "ana@correo.com",
                                            "password": "Clave1234"})
    assert r.status_code == 400


def test_registro_contrasena_corta(client):
    r = client.post("/auth/registro", json={"nombre_completo": "Nuevo", "email": "n@correo.com", "password": "corta"})
    assert r.status_code == 422


def test_registro_correo_invalido(client):
    r = client.post("/auth/registro", json={"nombre_completo": "Nuevo", "email": "no-es-correo",
                                            "password": "Clave1234"})
    assert r.status_code == 422


def test_login_correcto_devuelve_token(client):
    r = client.post("/auth/login", data={"username": "ana@correo.com", "password": CLAVE})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer" and r.json()["access_token"]


def test_login_clave_incorrecta_es_401(client):
    r = client.post("/auth/login", data={"username": "ana@correo.com", "password": "otra-clave"})
    assert r.status_code == 401


def test_login_usuario_inexistente_es_401(client):
    r = client.post("/auth/login", data={"username": "nadie@correo.com", "password": CLAVE})
    assert r.status_code == 401


def test_me_sin_token_es_401(client):
    assert client.get("/auth/me").status_code == 401


def test_me_con_token_falso_es_401(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer token.falso.123"})
    assert r.status_code == 401


def test_me_devuelve_el_usuario_logueado(client, ana):
    r = client.get("/auth/me", headers=ana)
    assert r.status_code == 200 and r.json()["email"] == "ana@correo.com"
