"""Fotos: se suben a carpetas ordenadas y NO quedan huérfanas en Cloudinary.

Cloudinary se reemplaza por un doble falso (FakeUploader): las pruebas no salen a internet.
"""
import pytest

from app import imagenes, models

NUBE = "demo"
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 50


def url_de(pid: str) -> str:
    return f"https://res.cloudinary.com/{NUBE}/image/upload/v123/{pid}.png"


class FakeUploader:
    def __init__(self):
        self.subidas, self.borradas = [], []

    def upload(self, contenido, public_id, asset_folder, **_):
        self.subidas.append(public_id)
        return {"secure_url": url_de(public_id), "public_id": public_id}

    def destroy(self, public_id, **_):
        self.borradas.append(public_id)
        return {"result": "ok"}


@pytest.fixture()
def nube(monkeypatch):
    fake = FakeUploader()
    monkeypatch.setattr(imagenes, "CLOUD_NAME", NUBE)
    monkeypatch.setattr(imagenes, "API_KEY", "k")
    monkeypatch.setattr(imagenes, "API_SECRET", "s")
    monkeypatch.setattr(imagenes, "_cloudinary", lambda: fake)
    return fake


def _subir(client, headers, contenido=PNG, **datos):
    datos = {"tipo": "mascotas", **datos}
    return client.post("/imagenes/", data=datos, files={"archivo": ("f.png", contenido, "image/png")}, headers=headers)


# ---------- utilidades ----------
def test_slug_quita_tildes_y_simbolos():
    assert imagenes.slug("Pastor Alemán") == "pastor-aleman"
    assert imagenes.slug("  ") == "sin-clasificar"
    assert imagenes.slug("../../etc") == "etc"


def test_public_id_solo_de_nuestra_cuenta(monkeypatch):
    monkeypatch.setattr(imagenes, "CLOUD_NAME", NUBE)
    assert imagenes.public_id_de(url_de("content/pawsshop/a b")) == "content/pawsshop/a b"
    assert imagenes.public_id_de("https://res.cloudinary.com/otra/image/upload/v1/x.png") is None
    assert imagenes.public_id_de("https://example.com/foto.png") is None
    assert imagenes.public_id_de(None) is None


# ---------- subir ----------
def test_subida_usa_jerarquia_por_raza_y_usuario(client, nube, enc1):
    r = _subir(client, enc1, subcarpeta="Pastor Alemán", especie="Perro")
    assert r.status_code == 201
    assert nube.subidas[0].startswith("content/pawsshop/mascotas/perro/pastor-aleman/user_2/")
    assert r.json()["url"] == url_de(nube.subidas[0])


def test_subida_de_producto_va_por_categoria(client, nube, admin):
    _subir(client, admin, tipo="productos", subcarpeta="Alimento")
    assert nube.subidas[0].startswith("content/pawsshop/productos/alimento/user_1/")


def test_usuario_normal_no_sube(client, nube, ana):
    assert _subir(client, ana).status_code == 403
    assert nube.subidas == []


def test_sin_token_es_401(client, nube):
    assert _subir(client, {}).status_code == 401


def test_rechaza_archivo_que_no_es_imagen(client, nube, enc1):
    assert _subir(client, enc1, contenido=b"<script>alert(1)</script>").status_code == 415


def test_rechaza_mas_de_5mb(client, nube, enc1):
    assert _subir(client, enc1, contenido=PNG + b"0" * (5 * 1024 * 1024)).status_code == 413


def test_tipo_invalido(client, nube, enc1):
    assert _subir(client, enc1, tipo="otro").status_code == 422


def test_sin_cloudinary_configurado_es_503(client, enc1, monkeypatch):
    monkeypatch.setattr(imagenes, "API_SECRET", "")
    assert _subir(client, enc1).status_code == 503


# ---------- borrar al reemplazar / quitar / eliminar ----------
def _producto_con_foto(db, pid="content/pawsshop/productos/alimento/user_1/viejo"):
    db.query(models.Producto).filter(models.Producto.id == 1).update({"imagen_url": url_de(pid)})
    db.commit()
    return pid


def test_reemplazar_foto_borra_la_anterior(client, db, nube, admin):
    viejo = _producto_con_foto(db)
    r = client.patch("/productos/1", json={"imagen_url": url_de("content/pawsshop/productos/alimento/user_1/nuevo")}, headers=admin)
    assert r.status_code == 200 and nube.borradas == [viejo]


def test_quitar_foto_borra_la_anterior(client, db, nube, admin):
    viejo = _producto_con_foto(db)
    assert client.patch("/productos/1", json={"imagen_url": None}, headers=admin).status_code == 200
    assert nube.borradas == [viejo]


def test_put_con_la_misma_foto_no_borra_nada(client, db, nube, admin):
    pid = _producto_con_foto(db)
    cuerpo = {"nombre": "Croquetas", "precio": 12, "stock": 2, "categoria_id": 1, "imagen_url": url_de(pid)}
    assert client.put("/productos/1", json=cuerpo, headers=admin).status_code == 200
    assert nube.borradas == []


def test_editar_otro_campo_no_toca_la_foto(client, db, nube, admin):
    _producto_con_foto(db)
    assert client.patch("/productos/1", json={"stock": 9}, headers=admin).status_code == 200
    assert nube.borradas == []


def test_eliminar_producto_borra_su_foto(client, db, nube, admin):
    pid = _producto_con_foto(db)
    assert client.delete("/productos/1", headers=admin).status_code == 204
    assert nube.borradas == [pid]


def test_eliminar_mascota_borra_su_foto(client, db, nube, admin):
    pid = "content/pawsshop/mascotas/perro/mestizo/user_2/rex"
    db.query(models.Mascota).filter(models.Mascota.id == 1).update({"imagen_url": url_de(pid)})
    db.commit()
    assert client.delete("/mascotas/1", headers=admin).status_code == 204
    assert nube.borradas == [pid]


def test_cambiar_foto_de_mascota_borra_la_anterior(client, db, nube, enc1):
    viejo = "content/pawsshop/mascotas/perro/mestizo/user_2/rex"
    db.query(models.Mascota).filter(models.Mascota.id == 1).update({"imagen_url": url_de(viejo)})
    db.commit()
    r = client.patch("/mascotas/1", json={"imagen_url": url_de("content/pawsshop/mascotas/perro/mestizo/user_2/rex2")}, headers=enc1)
    assert r.status_code == 200 and nube.borradas == [viejo]


def test_no_borra_una_foto_que_otro_registro_todavia_usa(client, db, nube, admin):
    pid = _producto_con_foto(db)
    db.query(models.Mascota).filter(models.Mascota.id == 1).update({"imagen_url": url_de(pid)})
    db.commit()
    assert client.delete("/productos/1", headers=admin).status_code == 204
    assert nube.borradas == []


def test_foto_externa_pegada_como_enlace_no_se_toca(client, db, nube, admin):
    db.query(models.Producto).filter(models.Producto.id == 1).update({"imagen_url": "https://example.com/a.jpg"})
    db.commit()
    assert client.delete("/productos/1", headers=admin).status_code == 204
    assert nube.borradas == []


def test_si_cloudinary_falla_el_borrado_igual_funciona(client, db, nube, admin, monkeypatch):
    _producto_con_foto(db)
    def roto(*a, **k):
        raise RuntimeError("sin red")
    monkeypatch.setattr(nube, "destroy", roto)
    assert client.delete("/productos/1", headers=admin).status_code == 204


# ---------- descartar una foto subida que no se guardó ----------
def test_descartar_foto_sin_usar(client, nube, enc1):
    pid = "content/pawsshop/mascotas/perro/mestizo/user_2/suelta"
    assert client.delete("/imagenes/", params={"url": url_de(pid)}, headers=enc1).status_code == 204
    assert nube.borradas == [pid]


def test_no_descarta_una_foto_en_uso(client, db, nube, enc1):
    pid = _producto_con_foto(db)
    assert client.delete("/imagenes/", params={"url": url_de(pid)}, headers=enc1).status_code == 409
    assert nube.borradas == []


def test_usuario_normal_no_descarta(client, nube, ana):
    assert client.delete("/imagenes/", params={"url": url_de("x")}, headers=ana).status_code == 403