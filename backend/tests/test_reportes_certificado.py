"""Certificado PDF, enlaces temporales, historial por meses, Excel y encargados (editar/eliminar)."""
import io
from datetime import datetime

from openpyxl import load_workbook

from app import models, security
from .conftest import _cabecera


def _adopcion_aprobada(client, ana, enc1, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    r = client.patch(f"/adopciones/{sid}", json={"estado": "Aprobada"}, headers=enc1)
    assert r.status_code == 200
    return sid


def _bajar(client, ruta):
    return client.get(ruta)


# ---------- certificado ----------
def test_certificado_pdf_del_adoptante(client, ana, enc1, formulario):
    sid = _adopcion_aprobada(client, ana, enc1, formulario)
    enlace = client.get(f"/adopciones/{sid}/certificado/enlace", headers=ana)
    assert enlace.status_code == 200
    r = _bajar(client, enlace.json()["ruta"])     # sin cabecera de sesión: el token va en la ruta
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
    assert "certificado_adopcion_Rex.pdf" in r.headers["content-disposition"]


def test_certificado_solo_si_esta_aprobada(client, ana, formulario):
    sid = client.post("/adopciones/", json=formulario, headers=ana).json()["id"]
    assert client.get(f"/adopciones/{sid}/certificado/enlace", headers=ana).status_code == 400


def test_certificado_no_es_de_otro_usuario_ni_otro_refugio(client, ana, beto, enc1, enc2, formulario):
    sid = _adopcion_aprobada(client, ana, enc1, formulario)
    assert client.get(f"/adopciones/{sid}/certificado/enlace", headers=beto).status_code == 403
    assert client.get(f"/adopciones/{sid}/certificado/enlace", headers=enc2).status_code == 403
    assert client.get(f"/adopciones/{sid}/certificado/enlace", headers=enc1).status_code == 200


def test_enlace_de_certificado_no_sirve_para_otro_archivo_ni_vencido(client, ana, enc1, formulario):
    sid = _adopcion_aprobada(client, ana, enc1, formulario)
    ruta = client.get(f"/adopciones/{sid}/certificado/enlace", headers=ana).json()["ruta"]
    token = ruta.split("?t=")[1]
    assert client.get(f"/descargas/certificado/{sid + 1}?t={token}").status_code == 401   # otra solicitud
    assert client.get(f"/descargas/reporte?t={token}").status_code == 401                  # otro recurso
    assert client.get(f"/descargas/certificado/{sid}?t=basura").status_code == 401
    # El token de descarga tampoco abre sesión
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


# ---------- historial por meses ----------
def _poner_fechas(db, usuarios, meses_y_ventas):
    for i, (anio, mes, total) in enumerate(meses_y_ventas, start=1):
        db.add(models.OrdenCompra(usuario_id=3, total=total, estado_pedido="Pagado",
                                  fecha_compra=datetime(anio, mes, 5, 10)))
    db.commit()


def test_serie_mensual_llena_los_meses_vacios_y_suma_ventas(client, admin, db):
    _poner_fechas(db, None, [(2026, 9, 10), (2026, 9, 5), (2026, 11, 40)])
    r = client.get("/admin/metricas/meses", headers=admin)
    assert r.status_code == 200
    meses = {m["mes"]: m for m in r.json()}
    assert meses["2026-09"]["pedidos"] == 2 and meses["2026-09"]["ventas"] == 15
    assert meses["2026-10"]["pedidos"] == 0 and meses["2026-10"]["ventas"] == 0   # mes sin movimiento
    assert meses["2026-11"]["ventas"] == 40
    ordenados = [m["mes"] for m in r.json()]
    assert ordenados == sorted(ordenados)
    assert meses["2026-09"]["nombre"] == "Septiembre 2026"
    # el mes actual siempre aparece
    assert f"{datetime.now().year}-{datetime.now().month:02d}" in meses


def test_serie_mensual_solo_admin(client, enc1, ana):
    assert client.get("/admin/metricas/meses", headers=enc1).status_code == 403
    assert client.get("/admin/metricas/meses", headers=ana).status_code == 403


# ---------- Excel ----------
def _libro(contenido):
    return load_workbook(io.BytesIO(contenido))


def test_excel_trae_resumen_historial_y_detalle(client, admin, db):
    _poner_fechas(db, None, [(2026, 9, 10), (2026, 11, 40)])
    r = client.get("/admin/reporte.xlsx?mes=2026-09", headers=admin)
    assert r.status_code == 200
    assert "reporte_pawsshop_2026-09.xlsx" in r.headers["content-disposition"]
    libro = _libro(r.content)
    assert libro.sheetnames == ["Resumen", "Por mes", "Adopciones", "Ventas"]
    por_mes = libro["Por mes"]
    nombres = [por_mes.cell(row=i, column=1).value for i in range(4, 12)]
    assert "Septiembre 2026" in nombres and "Noviembre 2026" in nombres
    assert libro["Ventas"].max_row == 5            # encabezado + 1 pedido de septiembre + total


def test_excel_historico_trae_todos_los_meses(client, admin, db):
    _poner_fechas(db, None, [(2026, 9, 10), (2026, 11, 40)])
    r = client.get("/admin/reporte.xlsx?historico=true", headers=admin)
    assert "historico" in r.headers["content-disposition"]
    ventas = _libro(r.content)["Ventas"]
    totales = [ventas.cell(row=i, column=5).value for i in range(4, 6)]
    assert totales == [10.0, 40.0]


def test_excel_por_enlace_temporal(client, admin):
    enlace = client.get("/admin/reporte/enlace?historico=true", headers=admin)
    assert enlace.status_code == 200
    r = client.get(enlace.json()["ruta"])
    assert r.status_code == 200 and r.content[:2] == b"PK"      # un .xlsx es un zip
    assert client.get("/admin/reporte/enlace", headers=_cabecera(2)).status_code == 403


# ---------- encargados: editar y eliminar ----------
def test_admin_edita_encargado(client, admin):
    r = client.put("/admin/encargados/2", json={"nombre_completo": "Nuevo Nombre", "refugio_id": 2}, headers=admin)
    assert r.status_code == 200
    assert r.json()["nombre_completo"] == "Nuevo Nombre" and r.json()["refugio_nombre"] == "Refugio Dos"


def test_editar_encargado_valida_correo_refugio_y_clave(client, admin, db):
    assert client.put("/admin/encargados/2", json={"email": "enc2@correo.com"}, headers=admin).status_code == 400
    assert client.put("/admin/encargados/2", json={"refugio_id": 99}, headers=admin).status_code == 404
    assert client.put("/admin/encargados/2", json={"password": "corta"}, headers=admin).status_code == 422
    assert client.put("/admin/encargados/3", json={"nombre_completo": "Ana"}, headers=admin).status_code == 404  # es usuario
    ok = client.put("/admin/encargados/2", json={"password": "Otra#Clave99"}, headers=admin)
    assert ok.status_code == 200
    r = client.post("/auth/login", data={"username": "enc1@correo.com", "password": "Otra#Clave99"})
    assert r.status_code == 200


def test_admin_elimina_encargado_sin_historial(client, admin, db):
    assert client.delete("/admin/encargados/5", headers=admin).status_code == 204
    assert db.query(models.Usuario).filter(models.Usuario.id == 5).first() is None


def test_no_se_elimina_encargado_con_historial_sin_forzar(client, admin, db):
    db.add(models.OrdenCompra(usuario_id=2, total=5, estado_pedido="Pagado"))
    db.commit()
    assert client.delete("/admin/encargados/2", headers=admin).status_code == 409
    assert client.delete("/admin/encargados/2?forzar=true", headers=admin).status_code == 204
    assert db.query(models.OrdenCompra).filter(models.OrdenCompra.usuario_id == 2).count() == 0


def test_forzar_elimina_cliente_con_historial_y_libera_la_mascota(client, ana, enc1, admin, formulario, db):
    sid = _adopcion_aprobada(client, ana, enc1, formulario)
    db.add(models.SeguimientoAdopcion(solicitud_id=sid, estado_salud="Bueno"))
    db.add(models.OrdenCompra(usuario_id=3, total=20, estado_pedido="Pagado"))
    db.commit()
    mascota_id = db.query(models.SolicitudAdopcion).get(sid).mascota_id
    assert client.delete("/admin/clientes/3", headers=admin).status_code == 409
    assert client.delete("/admin/clientes/3?forzar=true", headers=admin).status_code == 204
    db.expire_all()
    assert db.query(models.Usuario).filter(models.Usuario.id == 3).first() is None
    assert db.query(models.SolicitudAdopcion).filter(models.SolicitudAdopcion.id == sid).first() is None
    assert db.query(models.SeguimientoAdopcion).count() == 0
    assert db.query(models.Mascota).get(mascota_id).estado_adopcion == "Disponible"


def test_eliminar_encargado_conserva_las_adopciones_que_resolvio(client, ana, enc1, admin, formulario, db):
    sid = _adopcion_aprobada(client, ana, enc1, formulario)
    assert db.query(models.SolicitudAdopcion).get(sid).resuelto_por_id == 2
    assert client.delete("/admin/encargados/2", headers=admin).status_code == 204
    db.expire_all()
    s = db.query(models.SolicitudAdopcion).get(sid)
    assert s is not None and s.resuelto_por_id is None and s.estado == "Aprobada"


def test_el_certificado_lleva_el_nombre_de_quien_aprobo(client, ana, enc1, formulario, monkeypatch):
    from app import certificado
    capturado = {}
    original = certificado.generar_certificado

    def espia(**datos):
        capturado.update(datos)
        return original(**datos)

    monkeypatch.setattr(certificado, "generar_certificado", espia)
    sid = _adopcion_aprobada(client, ana, enc1, formulario)
    ruta = client.get(f"/adopciones/{sid}/certificado/enlace", headers=ana).json()["ruta"]
    assert client.get(ruta).status_code == 200
    assert capturado["aprobado_por"]            # el nombre del encargado que aprobó


def test_encargados_solo_los_gestiona_el_admin(client, enc1, ana):
    assert client.put("/admin/encargados/5", json={"nombre_completo": "X Y"}, headers=enc1).status_code == 403
    assert client.delete("/admin/encargados/5", headers=ana).status_code == 403


# ---------- contraseña fuerte ----------
import pytest

MALAS = [
    ("Corta#1", "mínimo 8 caracteres"),
    ("clave#segura9", "una letra mayúscula"),
    ("ClaveSegura9", "un carácter especial"),
    ("Clave#1234xy", "sin números en secuencia"),
    ("Clave#321xyz", "sin números en secuencia"),
]


@pytest.mark.parametrize("clave,mensaje", MALAS)
def test_registro_rechaza_contrasenas_debiles(client, clave, mensaje):
    r = client.post("/auth/registro", json={"nombre_completo": "Laura Gómez", "email": "laura@correo.com",
                                            "password": clave})
    assert r.status_code == 422
    assert mensaje in r.text


def test_registro_acepta_contrasena_fuerte_y_numeros_no_pegados(client):
    r = client.post("/auth/registro", json={"nombre_completo": "Laura Gómez", "email": "laura@correo.com",
                                            "password": "Clave#1a2b3c"})
    assert r.status_code == 201


def test_cambiar_y_asignar_contrasena_tambien_exigen_la_regla(client, ana, admin):
    assert client.put("/auth/me/password", headers=ana,
                      json={"actual": "Clave#Segura9", "nueva": "Debil1234"}).status_code == 422
    assert client.put("/admin/encargados/2", headers=admin, json={"password": "Debil1234"}).status_code == 422
    assert client.post("/admin/encargados", headers=admin, json={
        "nombre_completo": "Nuevo Enc", "email": "n@correo.com", "password": "debil", "refugio_id": 1}).status_code == 422
