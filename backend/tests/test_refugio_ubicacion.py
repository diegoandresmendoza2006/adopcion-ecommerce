"""El administrador guarda la ubicación del refugio (latitud y longitud) elegida en el mapa."""


def test_admin_crea_refugio_con_ubicacion(client, admin):
    r = client.post("/refugios/", json={"nombre": "Patitas", "direccion": "Calle 1 # 2-3",
                                        "latitud": 4.711, "longitud": -74.072}, headers=admin)
    assert r.status_code == 201
    assert r.json()["latitud"] == 4.711
    assert r.json()["longitud"] == -74.072
    lista = client.get("/refugios/").json()
    assert any(x["nombre"] == "Patitas" and x["latitud"] == 4.711 for x in lista)


def test_refugio_sin_ubicacion_devuelve_null(client, admin):
    r = client.post("/refugios/", json={"nombre": "Sin mapa"}, headers=admin)
    assert r.status_code == 201
    assert r.json()["latitud"] is None and r.json()["longitud"] is None


def test_admin_edita_la_ubicacion(client, admin):
    r = client.put("/refugios/1", json={"nombre": "Refugio Uno", "latitud": 6.2442, "longitud": -75.5812},
                   headers=admin)
    assert r.status_code == 200
    assert r.json()["latitud"] == 6.2442 and r.json()["longitud"] == -75.5812
    r = client.patch("/refugios/1", json={"latitud": 3.4516, "longitud": -76.532}, headers=admin)
    assert r.status_code == 200 and r.json()["latitud"] == 3.4516


def test_ubicacion_fuera_de_rango_se_rechaza(client, admin):
    r = client.post("/refugios/", json={"nombre": "Malo", "latitud": 95, "longitud": 10}, headers=admin)
    assert r.status_code == 422
    r = client.post("/refugios/", json={"nombre": "Malo", "latitud": 10, "longitud": -200}, headers=admin)
    assert r.status_code == 422


def test_usuario_no_cambia_la_ubicacion(client, ana):
    r = client.patch("/refugios/1", json={"latitud": 1, "longitud": 1}, headers=ana)
    assert r.status_code == 403
