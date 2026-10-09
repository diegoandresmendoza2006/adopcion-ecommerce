"""Formulario de adopción, revisión del encargado, comentarios y aspirantes."""


def test_crear_solicitud_completa(client, ana, formulario):
    r = client.post("/adopciones/", json=formulario, headers=ana)
    assert r.status_code == 201
    assert r.json()["estado"] == "En Revisión"


def test_solo_usuarios_envian_solicitudes(client, enc1, formulario):
    assert client.post("/adopciones/", json=formulario, headers=enc1).status_code == 403


def test_no_se_repite_la_solicitud_en_revision(client, ana, formulario):
    assert client.post("/adopciones/", json=formulario, headers=ana).status_code == 201
    assert client.post("/adopciones/", json=formulario, headers=ana).status_code == 400


def test_formulario_vacio_es_422(client, ana):
    assert client.post("/adopciones/", json={"mascota_id": 1}, headers=ana).status_code == 422


def test_mascota_inexistente_es_404(client, ana, formulario):
    assert client.post("/adopciones/", json={**formulario, "mascota_id": 99}, headers=ana).status_code == 404


def test_debe_ser_mayor_de_edad(client, ana, formulario):
    r = client.post("/adopciones/", json={**formulario, "fecha_nacimiento": "2015-01-01"}, headers=ana)
    assert r.status_code == 422


def test_campos_invalidos(client, ana, formulario):
    invalidos = [("email_contacto", "no-es-correo"), ("horas_solo", 30), ("horas_solo", -1),
                 ("personas_hogar", 0), ("tipo_vivienda", "Prestada"), ("telefono", "12"),
                 ("responsable_viajes", ""), ("direccion", "x")]
    for campo, valor in invalidos:
        r = client.post("/adopciones/", json={**formulario, campo: valor}, headers=ana)
        assert r.status_code == 422, f"{campo}={valor!r} debió ser rechazado"


def test_si_tuvo_mascotas_debe_indicar_vacunacion(client, ana, formulario):
    r = client.post("/adopciones/", json={**formulario, "mascotas_vacunadas": None}, headers=ana)
    assert r.status_code == 422


def test_sin_mascotas_previas_se_descarta_vacunacion(client, enc1, ana, formulario):
    cuerpo = {**formulario, "tuvo_mascotas": False, "mascotas_vacunadas": True, "mascotas_esterilizadas": True}
    assert client.post("/adopciones/", json=cuerpo, headers=ana).status_code == 201
    fila = client.get("/adopciones/", headers=enc1).json()[0]
    assert fila["mascotas_vacunadas"] is None and fila["mascotas_esterilizadas"] is None


def test_encargado_ve_el_formulario_completo(client, enc1, ana, formulario):
    client.post("/adopciones/", json=formulario, headers=ana)
    fila = client.get("/adopciones/", headers=enc1).json()[0]
    assert fila["direccion"] == "Calle 1 # 2-3" and fila["horas_solo"] == 6
    assert fila["adoptante_nombre"] == "Ana Prueba"


def test_encargado_solo_ve_solicitudes_de_su_refugio(client, enc2, ana, formulario):
    client.post("/adopciones/", json=formulario, headers=ana)   # mascota 1 = refugio 1
    assert client.get("/adopciones/", headers=enc2).json() == []


def test_usuario_ve_solo_las_suyas(client, ana, beto, formulario):
    client.post("/adopciones/", json=formulario, headers=ana)
    assert len(client.get("/adopciones/mis", headers=ana).json()) == 1
    assert client.get("/adopciones/mis", headers=beto).json() == []


def test_aprobar_con_comentario_lo_ve_el_usuario(client, enc1, ana, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    r = client.patch(f"/adopciones/{sid}", json={"estado": "Aprobada", "comentario": "Pasa el lunes"}, headers=enc1)
    assert r.status_code == 200
    assert r.json()["estado"] == "Aprobada" and r.json()["fecha_respuesta"]
    mia = client.get("/adopciones/mis", headers=ana).json()[0]
    assert mia["comentario_encargado"] == "Pasa el lunes"


def test_rechazar_con_comentario(client, enc1, ana, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    client.patch(f"/adopciones/{sid}", json={"estado": "Rechazada", "comentario": "Falta espacio"}, headers=enc1)
    mia = client.get("/adopciones/mis", headers=ana).json()[0]
    assert mia["estado"] == "Rechazada" and mia["comentario_encargado"] == "Falta espacio"
    # al rechazar, la mascota sigue disponible
    assert client.get("/mascotas/1").json()["estado_adopcion"] == "Disponible"


def test_aprobar_marca_la_mascota_como_adoptada(client, enc1, ana, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    client.patch(f"/adopciones/{sid}", json={"estado": "Aprobada"}, headers=enc1)
    assert client.get("/mascotas/1").json()["estado_adopcion"] == "Adoptada"


def test_al_aprobar_se_rechazan_las_demas_con_aviso(client, enc1, ana, beto, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    client.post("/adopciones/", json={**formulario, "nombre_contacto": "Beto Prueba"}, headers=beto)
    client.patch(f"/adopciones/{sid}", json={"estado": "Aprobada"}, headers=enc1)
    otra = client.get("/adopciones/mis", headers=beto).json()[0]
    assert otra["estado"] == "Rechazada" and "adoptada por otra" in otra["comentario_encargado"]


def test_solicitud_ya_resuelta_no_se_decide_de_nuevo(client, enc1, ana, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    client.patch(f"/adopciones/{sid}", json={"estado": "Aprobada"}, headers=enc1)
    assert client.patch(f"/adopciones/{sid}", json={"estado": "Rechazada"}, headers=enc1).status_code == 400


def test_encargado_de_otro_refugio_no_decide(client, enc2, ana, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    assert client.patch(f"/adopciones/{sid}", json={"estado": "Aprobada"}, headers=enc2).status_code == 403


def test_usuario_no_decide_solicitudes(client, ana, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    assert client.patch(f"/adopciones/{sid}", json={"estado": "Aprobada"}, headers=ana).status_code == 403


def test_comentario_se_puede_corregir_despues(client, enc1, ana, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    client.patch(f"/adopciones/{sid}", json={"estado": "Aprobada"}, headers=enc1)
    r = client.patch(f"/adopciones/{sid}/comentario", json={"comentario": "Lleva la cédula"}, headers=enc1)
    assert r.status_code == 200 and r.json()["comentario_encargado"] == "Lleva la cédula"


def test_comentario_vacio_se_rechaza(client, enc1, ana, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    assert client.patch(f"/adopciones/{sid}/comentario", json={"comentario": "   "}, headers=enc1).status_code == 422


def test_aspirantes_de_una_mascota(client, enc1, ana, beto, formulario):
    client.post("/adopciones/", json=formulario, headers=ana)
    client.post("/adopciones/", json={**formulario, "nombre_contacto": "Beto Prueba"}, headers=beto)
    r = client.get("/adopciones/mascota/1", headers=enc1)
    assert r.status_code == 200 and len(r.json()) == 2
    assert {x["estado"] for x in r.json()} == {"En Revisión"}


def test_aspirantes_permisos(client, enc2, ana, admin):
    assert client.get("/adopciones/mascota/1", headers=enc2).status_code == 403   # otro refugio
    assert client.get("/adopciones/mascota/1", headers=ana).status_code == 403    # usuario
    assert client.get("/adopciones/mascota/1", headers=admin).status_code == 200
    assert client.get("/adopciones/mascota/99", headers=admin).status_code == 404
