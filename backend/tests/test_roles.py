"""Quién puede hacer qué: protección de endpoints por rol."""


def test_usuario_no_puede_crear_mascota(client, ana):
    r = client.post("/mascotas/", json={"nombre": "X", "especie": "Perro", "refugio_id": 1}, headers=ana)
    assert r.status_code == 403


def test_sin_sesion_no_puede_crear_mascota(client):
    r = client.post("/mascotas/", json={"nombre": "X", "especie": "Perro", "refugio_id": 1})
    assert r.status_code == 401


def test_encargado_no_ve_panel_de_admin(client, enc1):
    assert client.get("/admin/metricas", headers=enc1).status_code == 403
    assert client.get("/admin/auditoria", headers=enc1).status_code == 403
    assert client.get("/admin/encargados", headers=enc1).status_code == 403


def test_usuario_no_ve_panel_de_admin(client, ana):
    assert client.get("/admin/metricas", headers=ana).status_code == 403


def test_admin_ve_metricas(client, admin):
    assert client.get("/admin/metricas", headers=admin).status_code == 200


def test_admin_crea_encargado_con_clave_valida(client, admin):
    datos = {"nombre_completo": "Nuevo Encargado", "email": "nuevo.enc@correo.com", "password": "Clave1234",
             "refugio_id": 1}
    assert client.post("/admin/encargados", json=datos, headers=admin).status_code == 201


def test_admin_no_crea_encargado_con_clave_corta(client, admin):
    datos = {"nombre_completo": "Nuevo Encargado", "email": "nuevo.enc@correo.com", "password": "corta",
             "refugio_id": 1}
    assert client.post("/admin/encargados", json=datos, headers=admin).status_code == 422


def test_solo_usuario_compra(client, enc1, ana):
    cuerpo = {"items": [{"producto_id": 1, "cantidad": 1}]}
    assert client.post("/compras/", json=cuerpo, headers=enc1).status_code == 403
    assert client.post("/compras/", json=cuerpo, headers=ana).status_code == 201
