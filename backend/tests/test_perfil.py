"""Documento, perfil, foto, doble rol, clientes del admin, favoritos, paginación y sonda."""
from app import imagenes, models
from .conftest import CLAVE

BASE = dict(nombre_completo="Laura Gómez", email="laura@correo.com", password="Clave#Segura9",
            fecha_nacimiento="1998-05-20", telefono="3001234567", direccion="Calle 10 # 5-20",
            tipo_documento="CC", numero_documento="1012345678")


def registrar(client, **cambios):
    return client.post("/auth/registro", json={**BASE, **cambios})


# ---------- documento ----------
def test_registro_guarda_documento(client):
    r = registrar(client)
    assert r.status_code == 201
    assert r.json()["tipo_documento"] == "CC" and r.json()["numero_documento"] == "1012345678"


def test_documento_incompleto_o_invalido_422(client):
    assert registrar(client, numero_documento=None).status_code == 422
    assert registrar(client, numero_documento="12").status_code == 422
    assert registrar(client, tipo_documento="XX").status_code == 422


def test_documento_de_otra_persona_400(client):
    assert registrar(client).status_code == 201
    r = registrar(client, email="otra@correo.com")
    assert r.status_code == 400 and "documento" in r.json()["detail"]


def test_correo_repetido_como_usuario_400(client):
    registrar(client)
    assert registrar(client, numero_documento="999999999").status_code == 400


# ---------- doble rol ----------
def test_encargado_crea_cuenta_de_usuario_con_su_misma_clave(client):
    # enc1@correo.com ya es Encargado (clave Clave#Segura9)
    r = registrar(client, email="enc1@correo.com", nombre_completo="Enc Prueba")
    assert r.status_code == 201 and r.json()["rol_id"] == 3


def test_encargado_con_otra_clave_no_puede_crear_cuenta_de_usuario(client):
    r = registrar(client, email="enc1@correo.com", password="Otra#Clave99")
    assert r.status_code == 400 and "misma contraseña" in r.json()["detail"]


def test_login_con_dos_cuentas_las_devuelve_y_se_puede_cambiar(client):
    registrar(client, email="enc1@correo.com")
    t = client.post("/auth/login", data={"username": "enc1@correo.com", "password": CLAVE}).json()
    assert {c["rol_id"] for c in t["cuentas"]} == {2, 3}
    # entra por defecto con la de más privilegio (Encargado)
    h = {"Authorization": f"Bearer {t['access_token']}"}
    assert client.get("/auth/me", headers=h).json()["rol_id"] == 2
    usuario = next(c for c in t["cuentas"] if c["rol_id"] == 3)
    t2 = client.post("/auth/cambiar-rol", json={"usuario_id": usuario["usuario_id"]}, headers=h).json()
    h2 = {"Authorization": f"Bearer {t2['access_token']}"}
    assert client.get("/auth/me", headers=h2).json()["rol_id"] == 3
    assert len(t2["cuentas"]) == 2          # desde ahí puede volver a Encargado
    assert len(client.get("/auth/cuentas", headers=h2).json()) == 2


def test_login_con_una_sola_cuenta_trae_una(client):
    t = client.post("/auth/login", data={"username": "ana@correo.com", "password": CLAVE}).json()
    assert len(t["cuentas"]) == 1


def test_no_se_puede_cambiar_a_una_cuenta_ajena(client, ana):
    r = client.post("/auth/cambiar-rol", json={"usuario_id": 1}, headers=ana)   # 1 = admin
    assert r.status_code == 403


def test_registrar_con_correo_de_admin_y_otra_clave_no_da_acceso(client):
    r = registrar(client, email="admin@correo.com", password="Hacker#Clave9")
    assert r.status_code == 400


def test_admin_crea_encargado_para_un_usuario_existente_y_comparte_clave(client, admin):
    r = client.post("/admin/encargados", headers=admin, json={
        "nombre_completo": "Ana Prueba", "email": "ana@correo.com", "password": "Otra#Clave9", "refugio_id": 1})
    assert r.status_code == 201
    t = client.post("/auth/login", data={"username": "ana@correo.com", "password": CLAVE}).json()
    assert {c["rol_id"] for c in t["cuentas"]} == {2, 3}


# ---------- perfil ----------
def test_editar_perfil(client, ana):
    r = client.put("/auth/me", headers=ana, json={"nombre_completo": "Ana Nueva", "telefono": "3109876543",
                                                  "tipo_documento": "CE", "numero_documento": "ab12345"})
    assert r.status_code == 200
    assert r.json()["nombre_completo"] == "Ana Nueva" and r.json()["numero_documento"] == "AB12345"


def test_usuario_no_puede_cambiar_documento_ni_fecha_una_vez_registrados(client, ana):
    assert client.put("/auth/me", headers=ana, json={"tipo_documento": "CC", "numero_documento": "12345678",
                                                     "fecha_nacimiento": "1995-05-05"}).status_code == 200
    r = client.put("/auth/me", headers=ana, json={"numero_documento": "99999999", "tipo_documento": "CC"})
    assert r.status_code == 403
    assert client.put("/auth/me", headers=ana, json={"fecha_nacimiento": "1990-01-01"}).status_code == 403
    # reenviar los mismos valores no es un cambio: se aceptan los datos básicos
    r = client.put("/auth/me", headers=ana, json={"tipo_documento": "CC", "numero_documento": "12345678",
                                                  "telefono": "3112223344"})
    assert r.status_code == 200 and r.json()["telefono"] == "3112223344"


def test_encargado_tampoco_cambia_su_documento_pero_el_admin_si(client, enc1, admin):
    client.put("/auth/me", headers=enc1, json={"tipo_documento": "CC", "numero_documento": "70707070"})
    assert client.put("/auth/me", headers=enc1, json={"tipo_documento": "CC", "numero_documento": "80808080"}).status_code == 403
    r = client.put("/auth/me", headers=admin, json={"tipo_documento": "CC", "numero_documento": "10101010"})
    assert r.status_code == 200
    r = client.put("/auth/me", headers=admin, json={"tipo_documento": "CC", "numero_documento": "20202020"})
    assert r.status_code == 200 and r.json()["numero_documento"] == "20202020"


def test_admin_cambia_el_documento_de_un_cliente(client, admin, ana):
    client.put("/auth/me", headers=ana, json={"tipo_documento": "CC", "numero_documento": "12345678"})
    r = client.put("/admin/clientes/3", headers=admin, json={"tipo_documento": "CE", "numero_documento": "ZZ12345"})
    assert r.status_code == 200 and r.json()["numero_documento"] == "ZZ12345"


def test_editar_perfil_documento_ajeno_400(client, ana, beto):
    client.put("/auth/me", headers=ana, json={"tipo_documento": "CC", "numero_documento": "55555555"})
    r = client.put("/auth/me", headers=beto, json={"tipo_documento": "CC", "numero_documento": "55555555"})
    assert r.status_code == 400


def test_editar_perfil_valida_mayoria_de_edad(client, ana):
    assert client.put("/auth/me", headers=ana, json={"fecha_nacimiento": "2020-01-01"}).status_code == 422


def test_cambiar_contrasena(client, ana):
    mal = client.put("/auth/me/password", headers=ana, json={"actual": "Equivocada1", "nueva": "Nueva#Clave99"})
    assert mal.status_code == 400
    ok = client.put("/auth/me/password", headers=ana, json={"actual": CLAVE, "nueva": "Nueva#Clave99"})
    assert ok.status_code == 204
    assert client.post("/auth/login", data={"username": "ana@correo.com", "password": "Nueva#Clave99"}).status_code == 200
    assert client.post("/auth/login", data={"username": "ana@correo.com", "password": CLAVE}).status_code == 401


PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 50


def test_foto_de_perfil_subir_cambiar_y_quitar(client, ana, monkeypatch):
    borradas, contador = [], iter(range(1, 10))
    monkeypatch.setattr(imagenes, "configurado", lambda: True)
    monkeypatch.setattr(imagenes, "subir", lambda c, carpeta: (f"https://res.cloudinary.com/x/image/upload/{carpeta}/{next(contador)}.png", "id"))
    monkeypatch.setattr(imagenes, "borrar", lambda url: borradas.append(url) or True)

    r1 = client.post("/auth/me/foto", headers=ana, files={"archivo": ("a.png", PNG, "image/png")})
    assert r1.status_code == 200 and "perfiles/user_3" in r1.json()["foto_url"]
    primera = r1.json()["foto_url"]

    r2 = client.post("/auth/me/foto", headers=ana, files={"archivo": ("b.png", PNG, "image/png")})
    assert r2.json()["foto_url"] != primera and borradas == [primera]      # la vieja se borra

    r3 = client.delete("/auth/me/foto", headers=ana)
    assert r3.json()["foto_url"] is None and len(borradas) == 2


def test_foto_de_perfil_rechaza_archivos_que_no_son_imagen(client, ana, monkeypatch):
    monkeypatch.setattr(imagenes, "configurado", lambda: True)
    r = client.post("/auth/me/foto", headers=ana, files={"archivo": ("a.png", b"hola mundo", "image/png")})
    assert r.status_code == 415


# ---------- clientes (admin) ----------
def test_admin_lista_busca_y_pagina_clientes(client, admin):
    r = client.get("/admin/clientes", headers=admin)
    assert r.status_code == 200 and r.json()["total"] == 2         # ana y beto (los rol 3)
    assert client.get("/admin/clientes?buscar=beto", headers=admin).json()["total"] == 1
    p = client.get("/admin/clientes?por_pagina=1&pagina=2", headers=admin).json()
    assert len(p["items"]) == 1 and p["paginas"] == 2


def test_clientes_solo_para_admin(client, enc1, ana):
    assert client.get("/admin/clientes", headers=enc1).status_code == 403
    assert client.get("/admin/clientes", headers=ana).status_code == 403


def test_admin_ve_y_edita_cliente(client, admin):
    assert client.get("/admin/clientes/3", headers=admin).json()["email"] == "ana@correo.com"
    assert client.get("/admin/clientes/2", headers=admin).status_code == 404    # 2 es encargado, no cliente
    r = client.put("/admin/clientes/3", headers=admin, json={"nombre_completo": "Ana Editada", "telefono": "3001112222"})
    assert r.status_code == 200 and r.json()["nombre_completo"] == "Ana Editada"
    assert client.put("/admin/clientes/3", headers=admin, json={"email": "beto@correo.com"}).status_code == 400


def test_admin_elimina_cliente_sin_historial(client, admin, db):
    assert client.delete("/admin/clientes/4", headers=admin).status_code == 204
    assert client.get("/admin/clientes/4", headers=admin).status_code == 404


def test_admin_no_elimina_cliente_con_historial(client, admin, ana, formulario):
    assert client.post("/adopciones/", headers=ana, json=formulario).status_code == 201
    r = client.delete("/admin/clientes/3", headers=admin)
    assert r.status_code == 409


# ---------- favoritos ----------
def test_favoritos_de_mascotas(client, ana, beto):
    assert client.put("/favoritos/mascotas/1", headers=ana).status_code == 204
    assert client.put("/favoritos/mascotas/1", headers=ana).status_code == 204      # repetir no duplica
    assert client.put("/favoritos/mascotas/99", headers=ana).status_code == 404
    assert client.get("/favoritos/mascotas/ids", headers=ana).json() == [1]
    assert client.get("/favoritos/mascotas", headers=ana).json()["total"] == 1
    assert client.get("/favoritos/mascotas", headers=beto).json()["total"] == 0      # son de cada usuario
    assert client.delete("/favoritos/mascotas/1", headers=ana).status_code == 204
    assert client.get("/favoritos/mascotas/ids", headers=ana).json() == []


def test_favoritos_de_productos(client, ana):
    assert client.put("/favoritos/productos/1", headers=ana).status_code == 204
    assert [p["nombre"] for p in client.get("/favoritos/productos", headers=ana).json()] == ["Croquetas"]
    client.delete("/favoritos/productos/1", headers=ana)
    assert client.get("/favoritos/productos", headers=ana).json() == []


def test_favoritos_exigen_sesion(client):
    assert client.get("/favoritos/mascotas").status_code == 401


# ---------- paginación opcional + búsqueda ----------
def test_solicitudes_paginadas_y_con_total(client, ana, enc1, formulario):
    client.post("/adopciones/", headers=ana, json=formulario)
    r = client.get("/adopciones/?pagina=1&por_pagina=1", headers=enc1)
    assert r.status_code == 200 and len(r.json()) == 1 and r.headers["x-total-count"] == "1"
    assert client.get("/adopciones/?pagina=2&por_pagina=1", headers=enc1).json() == []
    assert len(client.get("/adopciones/?buscar=rex", headers=enc1).json()) == 1
    assert client.get("/adopciones/?buscar=zzz", headers=enc1).json() == []
    assert len(client.get("/adopciones/?estado=En Revisión", headers=enc1).json()) == 1
    assert len(client.get("/adopciones/", headers=enc1).json()) == 1               # sin pagina: todo, como antes


def test_auditoria_con_filtros(client, admin, db):
    db.add_all([models.Auditoria(nombre_usuario="Ana", accion="INSERT", tabla_afectada="mascotas"),
                models.Auditoria(nombre_usuario="Beto", accion="DELETE", tabla_afectada="productos")])
    db.commit()
    assert len(client.get("/admin/auditoria?accion=delete", headers=admin).json()) == 1
    assert len(client.get("/admin/auditoria?buscar=ana", headers=admin).json()) == 1
    r = client.get("/admin/auditoria?pagina=1&por_pagina=1", headers=admin)
    assert len(r.json()) == 1 and r.headers["x-total-count"] == "2"


def test_inventario_con_busqueda(client, enc1):
    assert len(client.get("/mascotas/gestion/inventario?buscar=rex", headers=enc1).json()) == 1
    assert client.get("/mascotas/gestion/inventario?buscar=misi", headers=enc1).json() == []


def test_inventario_del_admin_filtra_por_refugio(client, admin, enc1):
    todas = client.get("/mascotas/gestion/inventario", headers=admin).json()
    solo_1 = client.get("/mascotas/gestion/inventario?refugio_id=1", headers=admin).json()
    assert len(todas) == 2 and [m["refugio_id"] for m in solo_1] == [1]
    # el encargado no puede salirse de su refugio con ese filtro
    del_enc = client.get("/mascotas/gestion/inventario?refugio_id=2", headers=enc1).json()
    assert all(m["refugio_id"] == 1 for m in del_enc)


# ---------- sonda ----------
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"estado": "ok", "base_de_datos": "ok"}
