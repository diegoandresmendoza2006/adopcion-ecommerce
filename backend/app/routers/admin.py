import io
import math
import re
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import Response
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from sqlalchemy import func
from sqlalchemy.orm import Session
from .. import schemas
from .. import database
from .. import models
from .. import imagenes
from .. import security
from ..paginacion import like, paginar
from .adopciones import ESTADO_APROBADA

router = APIRouter(prefix="/admin", tags=["Administración"], dependencies=[Depends(security.require_admin)])

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
         "Septiembre", "Octubre", "Noviembre", "Diciembre"]
PATRON_MES = r"^\d{4}-(0[1-9]|1[0-2])$"


def _rango_mes(mes: Optional[str]):
    """'2026-10' -> (1 oct 2026, 1 nov 2026, '2026-10'). Sin dato = mes actual."""
    if mes is None:
        hoy = datetime.now()
        anio, num = hoy.year, hoy.month
    else:
        anio, num = int(mes[:4]), int(mes[5:7])
    inicio = datetime(anio, num, 1)
    fin = datetime(anio + 1, 1, 1) if num == 12 else datetime(anio, num + 1, 1)
    return inicio, fin, f"{anio}-{num:02d}"


def _calcular_metricas(db: Session, mes: Optional[str]) -> schemas.MetricasOut:
    inicio, fin, etiqueta = _rango_mes(mes)
    S, O, U, M = models.SolicitudAdopcion, models.OrdenCompra, models.Usuario, models.Mascota

    def contar(consulta):
        return consulta.scalar() or 0

    en_mes_sol = (S.fecha_solicitud >= inicio, S.fecha_solicitud < fin)
    en_mes_ord = (O.fecha_compra >= inicio, O.fecha_compra < fin)
    return schemas.MetricasOut(
        mes=etiqueta,
        solicitudes_mes=contar(db.query(func.count(S.id)).filter(*en_mes_sol)),
        adopciones_mes=contar(db.query(func.count(S.id)).filter(S.estado == ESTADO_APROBADA, *en_mes_sol)),
        pedidos_mes=contar(db.query(func.count(O.id)).filter(*en_mes_ord)),
        ventas_mes=float(db.query(func.coalesce(func.sum(O.total), 0)).filter(*en_mes_ord).scalar() or 0),
        ventas_totales=float(db.query(func.coalesce(func.sum(O.total), 0)).scalar() or 0),
        usuarios_registrados=contar(db.query(func.count(U.id))),
        usuarios_nuevos_mes=contar(db.query(func.count(U.id)).filter(U.fecha_registro >= inicio, U.fecha_registro < fin)),
        mascotas_disponibles=contar(db.query(func.count(M.id)).filter(M.estado_adopcion == "Disponible")),
        mascotas_adoptadas=contar(db.query(func.count(M.id)).filter(M.estado_adopcion == "Adoptada")),
    )


@router.get("/metricas", response_model=schemas.MetricasOut)
def metricas(mes: Optional[str] = Query(None, pattern=PATRON_MES), db: Session = Depends(database.get_db)):
    return _calcular_metricas(db, mes)


# ---------- Reporte en Excel (con formato) ----------
VERDE = "28A745"
BORDE = Border(*(Side(style="thin", color="D0D5DA"),) * 4)


def _encabezado(hoja, fila, titulos):
    for col, titulo in enumerate(titulos, start=1):
        c = hoja.cell(row=fila, column=col, value=titulo)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=VERDE)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = BORDE


def _ajustar_columnas(hoja, minimo=12, maximo=45):
    for col in hoja.columns:
        largo = max((len(str(c.value)) for c in col if c.value is not None and c.row > 4), default=minimo)
        hoja.column_dimensions[get_column_letter(col[0].column)].width = max(minimo, min(maximo, largo + 3))


@router.get("/reporte.xlsx")
def reporte_excel(mes: Optional[str] = Query(None, pattern=PATRON_MES), db: Session = Depends(database.get_db)):
    inicio, fin, etiqueta = _rango_mes(mes)
    m = _calcular_metricas(db, etiqueta)
    nombre_mes = f"{MESES[inicio.month - 1]} {inicio.year}"
    dinero = '"$"#,##0.00'
    fecha_fmt = "dd/mm/yyyy hh:mm"

    wb = Workbook()

    # ---- Hoja 1: Resumen
    h = wb.active
    h.title = "Resumen"
    h.sheet_view.showGridLines = False
    h["A1"] = "Paws&Shop · Reporte mensual"
    h["A1"].font = Font(size=18, bold=True, color=VERDE)
    h["A2"] = f"Periodo: {nombre_mes}"
    h["A2"].font = Font(size=12, bold=True)
    h["A3"] = f"Generado el {datetime.now():%d/%m/%Y a las %H:%M}"
    h["A3"].font = Font(italic=True, color="666666")
    _encabezado(h, 5, ["Indicador", "Valor"])
    filas = [
        (f"Solicitudes de adopción ({nombre_mes})", m.solicitudes_mes, None),
        (f"Adopciones aprobadas ({nombre_mes})", m.adopciones_mes, None),
        (f"Pedidos de la tienda ({nombre_mes})", m.pedidos_mes, None),
        (f"Ventas de {nombre_mes}", m.ventas_mes, dinero),
        ("Ventas acumuladas (todos los meses)", m.ventas_totales, dinero),
        (f"Usuarios nuevos ({nombre_mes})", m.usuarios_nuevos_mes, None),
        ("Usuarios registrados (total)", m.usuarios_registrados, None),
        ("Mascotas disponibles hoy", m.mascotas_disponibles, None),
        ("Mascotas adoptadas (total)", m.mascotas_adoptadas, None),
    ]
    for i, (texto, valor, fmt) in enumerate(filas, start=6):
        a, b = h.cell(row=i, column=1, value=texto), h.cell(row=i, column=2, value=valor)
        a.border = b.border = BORDE
        b.alignment = Alignment(horizontal="right")
        if fmt:
            b.number_format = fmt
        if i % 2 == 1:
            a.fill = b.fill = PatternFill("solid", fgColor="F3F8F4")
    h.column_dimensions["A"].width = 48
    h.column_dimensions["B"].width = 20

    # ---- Hoja 2: Adopciones del mes
    h = wb.create_sheet("Adopciones")
    h["A1"] = f"Solicitudes de adopción · {nombre_mes}"
    h["A1"].font = Font(size=14, bold=True, color=VERDE)
    _encabezado(h, 3, ["Fecha", "Adoptante", "Mascota", "Refugio", "Estado", "Teléfono", "Vivienda"])
    S, M, U, R = models.SolicitudAdopcion, models.Mascota, models.Usuario, models.Refugio
    filas = (db.query(S, M, U, R)
             .join(M, M.id == S.mascota_id).join(U, U.id == S.usuario_id)
             .outerjoin(R, R.id == M.refugio_id)
             .filter(S.fecha_solicitud >= inicio, S.fecha_solicitud < fin)
             .order_by(S.fecha_solicitud).all())
    for i, (s, mas, usu, ref) in enumerate(filas, start=4):
        valores = [s.fecha_solicitud, usu.nombre_completo, mas.nombre, ref.nombre if ref else "", s.estado,
                   s.telefono or "", s.tipo_vivienda or ""]
        for col, v in enumerate(valores, start=1):
            c = h.cell(row=i, column=col, value=v)
            c.border = BORDE
            if col == 1:
                c.number_format = fecha_fmt
    if not filas:
        h["A4"] = "Sin solicitudes en este periodo."
        h["A4"].font = Font(italic=True, color="666666")
    h.freeze_panes = "A4"
    if filas:
        h.auto_filter.ref = f"A3:G{3 + len(filas)}"
    _ajustar_columnas(h)

    # ---- Hoja 3: Ventas del mes
    h = wb.create_sheet("Ventas")
    h["A1"] = f"Ventas de la tienda · {nombre_mes}"
    h["A1"].font = Font(size=14, bold=True, color=VERDE)
    _encabezado(h, 3, ["N.º pedido", "Fecha", "Cliente", "Estado", "Total"])
    O = models.OrdenCompra
    ordenes = (db.query(O, U).join(U, U.id == O.usuario_id)
               .filter(O.fecha_compra >= inicio, O.fecha_compra < fin).order_by(O.fecha_compra).all())
    for i, (o, usu) in enumerate(ordenes, start=4):
        for col, v in enumerate([o.id, o.fecha_compra, usu.nombre_completo, o.estado_pedido, float(o.total)], start=1):
            c = h.cell(row=i, column=col, value=v)
            c.border = BORDE
            if col == 2:
                c.number_format = fecha_fmt
            if col == 5:
                c.number_format = dinero
    if ordenes:
        ultima = 3 + len(ordenes)
        h.cell(row=ultima + 1, column=4, value="TOTAL").font = Font(bold=True)
        t = h.cell(row=ultima + 1, column=5, value=f"=SUM(E4:E{ultima})")
        t.font = Font(bold=True)
        t.number_format = dinero
        h.auto_filter.ref = f"A3:E{ultima}"
    else:
        h["A4"] = "Sin ventas en este periodo."
        h["A4"].font = Font(italic=True, color="666666")
    h.freeze_panes = "A4"
    _ajustar_columnas(h)

    buffer = io.BytesIO()
    wb.save(buffer)
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=reporte_pawsshop_{etiqueta}.xlsx"},
    )


@router.get("/auditoria", response_model=List[schemas.AuditoriaOut])
def auditoria(response: Response, buscar: Optional[str] = Query(None, max_length=60),
              accion: Optional[str] = Query(None, max_length=20), tabla: Optional[str] = Query(None, max_length=50),
              pagina: Optional[int] = Query(None, ge=1), por_pagina: int = Query(20, ge=1, le=100),
              db: Session = Depends(database.get_db)):
    """Sin ?pagina devuelve los últimos 200 (como antes). Con ?pagina=N devuelve un bloque (scroll infinito)."""
    A = models.Auditoria
    consulta = db.query(A)
    if buscar and buscar.strip():
        consulta = consulta.filter(A.nombre_usuario.ilike(like(buscar.strip()), escape="\\"))
    if accion and accion.strip():
        consulta = consulta.filter(A.accion == accion.strip().upper())
    if tabla and tabla.strip():
        consulta = consulta.filter(A.tabla_afectada == tabla.strip())
    consulta = consulta.order_by(A.id.desc())
    if pagina is None:
        return consulta.limit(200).all()
    return paginar(consulta, response, pagina, por_pagina)


@router.get("/encargados", response_model=List[schemas.EncargadoOut])
def listar_encargados(response: Response, buscar: Optional[str] = Query(None, max_length=60),
                      pagina: Optional[int] = Query(None, ge=1), por_pagina: int = Query(20, ge=1, le=100),
                      db: Session = Depends(database.get_db)):
    consulta = (db.query(models.Usuario, models.Refugio)
                .outerjoin(models.Refugio, models.Refugio.id == models.Usuario.refugio_id)
                .filter(models.Usuario.rol_id == security.ROL_ENCARGADO))
    if buscar and buscar.strip():
        patron = like(buscar.strip())
        consulta = consulta.filter(models.Usuario.nombre_completo.ilike(patron, escape="\\")
                                   | models.Usuario.email.ilike(patron, escape="\\"))
    filas = paginar(consulta.order_by(models.Usuario.id), response, pagina, por_pagina)
    return [schemas.EncargadoOut(id=u.id, nombre_completo=u.nombre_completo, email=u.email,
                                 refugio_id=u.refugio_id, refugio_nombre=r.nombre if r else None) for u, r in filas]


@router.post("/encargados", status_code=status.HTTP_201_CREATED, response_model=schemas.EncargadoOut)
def crear_encargado(datos: schemas.EncargadoCreate, db: Session = Depends(database.get_db)):
    existentes = db.query(models.Usuario).filter(models.Usuario.email == datos.email).all()
    if any(u.rol_id != security.ROL_USUARIO for u in existentes):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo ya está registrado")
    refugio = db.query(models.Refugio).filter(models.Refugio.id == datos.refugio_id).first()
    if not refugio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El refugio no existe")

    # Si esa persona ya tiene cuenta de Usuario, la cuenta de Encargado comparte su contraseña y sus datos:
    # al iniciar sesión el sistema detecta las dos cuentas y le deja elegir cómo entrar.
    previa = existentes[0] if existentes else None
    nuevo = models.Usuario(
        nombre_completo=previa.nombre_completo if previa else datos.nombre_completo, email=datos.email,
        password_hash=previa.password_hash if previa else security.hash_password(datos.password),
        rol_id=security.ROL_ENCARGADO, refugio_id=refugio.id,
        fecha_nacimiento=previa.fecha_nacimiento if previa else None,
        telefono=previa.telefono if previa else None, direccion=previa.direccion if previa else None,
        tipo_documento=previa.tipo_documento if previa else None,
        numero_documento=previa.numero_documento if previa else None,
        foto_url=previa.foto_url if previa else None,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return schemas.EncargadoOut(id=nuevo.id, nombre_completo=nuevo.nombre_completo, email=nuevo.email,
                                refugio_id=refugio.id, refugio_nombre=refugio.nombre)


# ---------- Clientes (usuarios con rol "Usuario"): ver, buscar, editar y eliminar ----------
def _cliente_o_404(db: Session, cliente_id: int) -> models.Usuario:
    c = db.query(models.Usuario).filter(models.Usuario.id == cliente_id,
                                        models.Usuario.rol_id == security.ROL_USUARIO).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El cliente no existe")
    return c


@router.get("/clientes", response_model=schemas.PaginaClientes)
def listar_clientes(buscar: Optional[str] = Query(None, max_length=60), pagina: int = Query(1, ge=1),
                    por_pagina: int = Query(20, ge=1, le=100), db: Session = Depends(database.get_db)):
    """Consulta de clientes: busca por nombre, correo, documento o teléfono."""
    U = models.Usuario
    consulta = db.query(U).filter(U.rol_id == security.ROL_USUARIO)
    if buscar and buscar.strip():
        patron = like(buscar.strip())
        consulta = consulta.filter(U.nombre_completo.ilike(patron, escape="\\") | U.email.ilike(patron, escape="\\")
                                   | U.numero_documento.ilike(patron, escape="\\") | U.telefono.ilike(patron, escape="\\"))
    total = consulta.count()
    items = consulta.order_by(U.id.desc()).offset((pagina - 1) * por_pagina).limit(por_pagina).all()
    return {"items": items, "total": total, "pagina": pagina, "por_pagina": por_pagina,
            "paginas": max(1, math.ceil(total / por_pagina))}


@router.get("/clientes/{cliente_id}", response_model=schemas.UsuarioOut)
def ver_cliente(cliente_id: int, db: Session = Depends(database.get_db)):
    return _cliente_o_404(db, cliente_id)


@router.put("/clientes/{cliente_id}", response_model=schemas.UsuarioOut)
def editar_cliente(cliente_id: int, datos: schemas.ClienteUpdate, db: Session = Depends(database.get_db)):
    cliente = _cliente_o_404(db, cliente_id)
    cambios = {k: v for k, v in datos.model_dump(exclude_unset=True).items()
               if v is not None or k in ("telefono", "direccion", "fecha_nacimiento")}
    if ("tipo_documento" in cambios) != ("numero_documento" in cambios):
        raise HTTPException(status_code=422, detail="Indica el tipo y el número de documento")
    nuevo_correo = cambios.get("email", cliente.email)
    if nuevo_correo != cliente.email and db.query(models.Usuario.id).filter(
            models.Usuario.email == nuevo_correo, models.Usuario.rol_id == security.ROL_USUARIO).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ese correo ya está registrado")
    if "numero_documento" in cambios:
        cambios["numero_documento"] = cambios["numero_documento"].upper()
        if db.query(models.Usuario.id).filter(
                models.Usuario.tipo_documento == cambios["tipo_documento"],
                models.Usuario.numero_documento == cambios["numero_documento"],
                models.Usuario.email != nuevo_correo).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ese documento ya está registrado con otro correo")
    for campo, valor in cambios.items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/clientes/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(cliente_id: int, db: Session = Depends(database.get_db)):
    cliente = _cliente_o_404(db, cliente_id)
    tiene_historial = (db.query(models.SolicitudAdopcion.id).filter(models.SolicitudAdopcion.usuario_id == cliente.id).first()
                       or db.query(models.OrdenCompra.id).filter(models.OrdenCompra.usuario_id == cliente.id).first())
    if tiene_historial:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Este cliente tiene solicitudes de adopción o compras registradas; no se puede eliminar")
    foto = cliente.foto_url
    db.query(models.FavoritoMascota).filter(models.FavoritoMascota.usuario_id == cliente.id).delete()
    db.query(models.SeleccionProducto).filter(models.SeleccionProducto.usuario_id == cliente.id).delete()
    db.delete(cliente)
    db.commit()
    imagenes.limpiar(db, foto)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
