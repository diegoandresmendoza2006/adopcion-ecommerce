"""CRUD de mascotas y sus reglas de negocio."""


def _nueva(**cambios):
    return {"nombre": "Luna", "especie": "Gato", "edad_meses": 12, "refugio_id": 1, **cambios}


def test_encargado_crea_mascota_en_su_refugio(client, enc1):
    # aunque pida el refugio 2, se guarda en el suyo (1)
    r = client.post("/mascotas/", json=_nueva(refugio_id=2), headers=enc1)
    assert r.status_code == 201 and r.json()["refugio_id"] == 1


def test_edad_maxima_240_meses(client, enc1):
    assert client.post("/mascotas/", json=_nueva(edad_meses=240), headers=enc1).status_code == 201
    assert client.post("/mascotas/", json=_nueva(edad_meses=241), headers=enc1).status_code == 422


def test_edad_no_puede_ser_negativa(client, enc1):
    assert client.post("/mascotas/", json=_nueva(edad_meses=-1), headers=enc1).status_code == 422


def test_edad_maxima_tambien_al_editar(client, enc1):
    assert client.patch("/mascotas/1", json={"edad_meses": 241}, headers=enc1).status_code == 422
    assert client.put("/mascotas/1", json={"nombre": "Rex", "especie": "Perro", "edad_meses": 241},
                      headers=enc1).status_code == 422
    assert client.patch("/mascotas/1", json={"edad_meses": 240}, headers=enc1).status_code == 200


def test_refugio_inexistente_es_404(client, admin):
    assert client.post("/mascotas/", json=_nueva(refugio_id=99), headers=admin).status_code == 404


def test_encargado_no_edita_mascota_de_otro_refugio(client, enc1):
    assert client.patch("/mascotas/2", json={"nombre": "Hackeada"}, headers=enc1).status_code == 403
    assert client.delete("/mascotas/2", headers=enc1).status_code == 403


def test_mascota_inexistente_es_404(client):
    assert client.get("/mascotas/999").status_code == 404


def test_catalogo_es_paginado(client):
    r = client.get("/mascotas/buscar", params={"por_pagina": 1})
    assert r.status_code == 200
    cuerpo = r.json()
    assert set(cuerpo) == {"items", "total", "pagina", "por_pagina", "paginas"}
    assert len(cuerpo["items"]) == 1 and cuerpo["total"] == 2 and cuerpo["paginas"] == 2


def test_inventario_del_encargado_solo_su_refugio(client, enc1):
    r = client.get("/mascotas/gestion/inventario", headers=enc1)
    assert [m["id"] for m in r.json()] == [1]


def test_eliminar_mascota_sin_historial(client, enc1):
    assert client.delete("/mascotas/1", headers=enc1).status_code == 204
    assert client.get("/mascotas/1").status_code == 404


def test_no_se_elimina_mascota_con_solicitudes(client, enc1, ana, formulario):
    assert client.post("/adopciones/", json=formulario, headers=ana).status_code == 201
    assert client.delete("/mascotas/1", headers=enc1).status_code == 409
    # forzar solo lo puede hacer el administrador
    assert client.delete("/mascotas/1?forzar=true", headers=enc1).status_code == 403


def test_admin_puede_forzar_el_borrado(client, admin, ana, formulario):
    client.post("/adopciones/", json=formulario, headers=ana)
    assert client.delete("/mascotas/1?forzar=true", headers=admin).status_code == 204


def test_mascota_adoptada_no_vuelve_a_disponible(client, enc1, ana, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    assert client.patch(f"/adopciones/{sid}", json={"estado": "Aprobada"}, headers=enc1).status_code == 200
    assert client.get("/mascotas/1").json()["estado_adopcion"] == "Adoptada"
    r = client.patch("/mascotas/1", json={"estado_adopcion": "Disponible"}, headers=enc1)
    assert r.status_code == 409
