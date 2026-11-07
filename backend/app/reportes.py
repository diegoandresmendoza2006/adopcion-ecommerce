"""Números del negocio: métricas de un mes, serie mes a mes y el reporte de Excel.

El administrador ve (en la app y en el Excel) el mes que elija y también todo el historial:
si la tienda empezó a usarse en noviembre, aparece noviembre; cuando llegue diciembre, aparece
diciembre y así sucesivamente, sin que nadie tenga que configurar nada.
"""
import io
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from . import models, schemas
from .routers.adopciones import ESTADO_APROBADA

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
         "Septiembre", "Octubre", "Noviembre", "Diciembre"]
PATRON_MES = r"^\d{4}-(0[1-9]|1[0-2])$"
MAX_MESES = 120   # la serie nunca pasa de 10 años hacia atrás


def rango_mes(mes: Optional[str]):
    """'2026-10' -> (1 oct 2026, 1 nov 2026, '2026-10'). Sin dato = mes actual."""
    if mes is None:
        hoy = datetime.now()
        anio, num = hoy.year, hoy.month
    else:
        anio, num = int(mes[:4]), int(mes[5:7])
    inicio = datetime(anio, num, 1)
    fin = datetime(anio + 1, 1, 1) if num == 12 else datetime(anio, num + 1, 1)
    return inicio, fin, f"{anio}-{num:02d}"


def nombre_del_mes(etiqueta: str) -> str:
    """'2026-11' -> 'Noviembre 2026'."""
    return f"{MESES[int(etiqueta[5:7]) - 1]} {etiqueta[:4]}"


def calcular_metricas(db: Session, mes: Optional[str]) -> schemas.MetricasOut:
    inicio, fin, etiqueta = rango_mes(mes)
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


# ---------------- serie mes a mes ----------------
def _por_mes(db: Session, columna_fecha, valor, *filtros) -> Dict[str, float]:
    """Agrupa [valor] por mes de [columna_fecha]: {'2026-11': 3, ...}."""
    anio, mes = extract("year", columna_fecha), extract("month", columna_fecha)
    filas = (db.query(anio, mes, valor).filter(columna_fecha.isnot(None), *filtros)
             .group_by(anio, mes).all())
    return {f"{int(a)}-{int(m):02d}": float(v or 0) for a, m, v in filas}


def serie_mensual(db: Session) -> List[schemas.MesOut]:
    """Todos los meses desde el primer movimiento hasta el mes actual (los vacíos salen en cero)."""
    S, O, U = models.SolicitudAdopcion, models.OrdenCompra, models.Usuario
    solicitudes = _por_mes(db, S.fecha_solicitud, func.count(S.id))
    adopciones = _por_mes(db, S.fecha_solicitud, func.count(S.id), S.estado == ESTADO_APROBADA)
    pedidos = _por_mes(db, O.fecha_compra, func.count(O.id))
    ventas = _por_mes(db, O.fecha_compra, func.coalesce(func.sum(O.total), 0))
    nuevos = _por_mes(db, U.fecha_registro, func.count(U.id))

    hoy = datetime.now()
    actual = f"{hoy.year}-{hoy.month:02d}"
    con_datos = set(solicitudes) | set(pedidos) | set(nuevos)
    primero = min(con_datos | {actual})
    ultimo = max(con_datos | {actual})

    meses: List[str] = []
    anio, num = int(primero[:4]), int(primero[5:7])
    while f"{anio}-{num:02d}" <= ultimo:
        meses.append(f"{anio}-{num:02d}")
        num += 1
        if num == 13:
            anio, num = anio + 1, 1
    meses = meses[-MAX_MESES:]
    return [schemas.MesOut(
        mes=m, nombre=nombre_del_mes(m),
        solicitudes=int(solicitudes.get(m, 0)), adopciones=int(adopciones.get(m, 0)),
        pedidos=int(pedidos.get(m, 0)), ventas=ventas.get(m, 0.0), usuarios_nuevos=int(nuevos.get(m, 0)),
    ) for m in meses]


# ---------------- Excel ----------------
VERDE = "28A745"
BORDE = Border(*(Side(style="thin", color="D0D5DA"),) * 4)
DINERO = '"$"#,##0.00'
FECHA = "dd/mm/yyyy hh:mm"


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


def _titulo(hoja, texto, tamano=14):
    hoja["A1"] = texto
    hoja["A1"].font = Font(size=tamano, bold=True, color=VERDE)


def nombre_archivo_reporte(mes: Optional[str], historico: bool) -> str:
    if historico:
        return "reporte_pawsshop_historico.xlsx"
    return f"reporte_pawsshop_{rango_mes(mes)[2]}.xlsx"


def construir_reporte(db: Session, mes: Optional[str] = None, historico: bool = False) -> bytes:
    """Libro de Excel con: Resumen, Por mes (todo el historial), Adopciones y Ventas.

    [mes] elige el mes de las hojas de detalle; con [historico] el detalle trae todos los meses.
    """
    inicio, fin, etiqueta = rango_mes(mes)
    periodo = "Todo el historial" if historico else nombre_del_mes(etiqueta)
    serie = serie_mensual(db)
    m = calcular_metricas(db, etiqueta)
    if historico:
        sol, ado = sum(s.solicitudes for s in serie), sum(s.adopciones for s in serie)
        ped, ven = sum(s.pedidos for s in serie), sum(s.ventas for s in serie)
        nue = sum(s.usuarios_nuevos for s in serie)
    else:
        sol, ado, ped, ven, nue = (m.solicitudes_mes, m.adopciones_mes, m.pedidos_mes, m.ventas_mes,
                                   m.usuarios_nuevos_mes)

    wb = Workbook()

    # ---- Hoja 1: Resumen
    h = wb.active
    h.title = "Resumen"
    h.sheet_view.showGridLines = False
    _titulo(h, "Paws&Shop · Reporte", 18)
    h["A2"] = f"Periodo: {periodo}"
    h["A2"].font = Font(size=12, bold=True)
    h["A3"] = f"Generado el {datetime.now():%d/%m/%Y a las %H:%M}"
    h["A3"].font = Font(italic=True, color="666666")
    _encabezado(h, 5, ["Indicador", "Valor"])
    filas = [
        (f"Solicitudes de adopción ({periodo})", sol, None),
        (f"Adopciones aprobadas ({periodo})", ado, None),
        (f"Pedidos de la tienda ({periodo})", ped, None),
        (f"Ventas ({periodo})", ven, DINERO),
        (f"Usuarios nuevos ({periodo})", nue, None),
        ("Ventas acumuladas (todos los meses)", m.ventas_totales, DINERO),
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
    h.column_dimensions["A"].width = 52
    h.column_dimensions["B"].width = 22

    # ---- Hoja 2: Por mes (histórico completo)
    h = wb.create_sheet("Por mes")
    _titulo(h, "Historial mes a mes")
    _encabezado(h, 3, ["Mes", "Solicitudes", "Adopciones", "Pedidos", "Ventas", "Usuarios nuevos"])
    for i, s in enumerate(serie, start=4):
        for col, v in enumerate([s.nombre, s.solicitudes, s.adopciones, s.pedidos, s.ventas, s.usuarios_nuevos],
                                start=1):
            c = h.cell(row=i, column=col, value=v)
            c.border = BORDE
            if col == 5:
                c.number_format = DINERO
    ultima = 3 + len(serie)
    h.cell(row=ultima + 1, column=1, value="TOTAL").font = Font(bold=True)
    for col in range(2, 7):
        letra = get_column_letter(col)
        t = h.cell(row=ultima + 1, column=col, value=f"=SUM({letra}4:{letra}{ultima})")
        t.font = Font(bold=True)
        t.border = BORDE
        if col == 5:
            t.number_format = DINERO
    h.freeze_panes = "A4"
    grafico = BarChart()
    grafico.title = "Ventas por mes"
    grafico.y_axis.title = "Ventas"
    grafico.add_data(Reference(h, min_col=5, min_row=3, max_row=ultima), titles_from_data=True)
    grafico.set_categories(Reference(h, min_col=1, min_row=4, max_row=ultima))
    grafico.legend = None
    grafico.height, grafico.width = 8, 16
    h.add_chart(grafico, "H3")
    h.column_dimensions["A"].width = 22
    for letra in "BCDEF":
        h.column_dimensions[letra].width = 16

    # ---- Hoja 3: Adopciones
    h = wb.create_sheet("Adopciones")
    _titulo(h, f"Solicitudes de adopción · {periodo}")
    _encabezado(h, 3, ["Fecha", "Adoptante", "Mascota", "Refugio", "Estado", "Teléfono", "Vivienda"])
    S, M, U, R, O = (models.SolicitudAdopcion, models.Mascota, models.Usuario, models.Refugio, models.OrdenCompra)
    consulta = (db.query(S, M, U, R).join(M, M.id == S.mascota_id).join(U, U.id == S.usuario_id)
                .outerjoin(R, R.id == M.refugio_id))
    if not historico:
        consulta = consulta.filter(S.fecha_solicitud >= inicio, S.fecha_solicitud < fin)
    adopciones = consulta.order_by(S.fecha_solicitud).all()
    for i, (s, mas, usu, ref) in enumerate(adopciones, start=4):
        valores = [s.fecha_solicitud, usu.nombre_completo, mas.nombre, ref.nombre if ref else "", s.estado,
                   s.telefono or "", s.tipo_vivienda or ""]
        for col, v in enumerate(valores, start=1):
            c = h.cell(row=i, column=col, value=v)
            c.border = BORDE
            if col == 1:
                c.number_format = FECHA
    if not adopciones:
        h["A4"] = "Sin solicitudes en este periodo."
        h["A4"].font = Font(italic=True, color="666666")
    else:
        h.auto_filter.ref = f"A3:G{3 + len(adopciones)}"
    h.freeze_panes = "A4"
    _ajustar_columnas(h)

    # ---- Hoja 4: Ventas
    h = wb.create_sheet("Ventas")
    _titulo(h, f"Ventas de la tienda · {periodo}")
    _encabezado(h, 3, ["N.º pedido", "Fecha", "Cliente", "Estado", "Total"])
    consulta = db.query(O, U).join(U, U.id == O.usuario_id)
    if not historico:
        consulta = consulta.filter(O.fecha_compra >= inicio, O.fecha_compra < fin)
    ordenes = consulta.order_by(O.fecha_compra).all()
    for i, (o, usu) in enumerate(ordenes, start=4):
        for col, v in enumerate([o.id, o.fecha_compra, usu.nombre_completo, o.estado_pedido, float(o.total)], start=1):
            c = h.cell(row=i, column=col, value=v)
            c.border = BORDE
            if col == 2:
                c.number_format = FECHA
            if col == 5:
                c.number_format = DINERO
    if ordenes:
        ultima = 3 + len(ordenes)
        h.cell(row=ultima + 1, column=4, value="TOTAL").font = Font(bold=True)
        t = h.cell(row=ultima + 1, column=5, value=f"=SUM(E4:E{ultima})")
        t.font = Font(bold=True)
        t.number_format = DINERO
        h.auto_filter.ref = f"A3:E{ultima}"
    else:
        h["A4"] = "Sin ventas en este periodo."
        h["A4"].font = Font(italic=True, color="666666")
    h.freeze_panes = "A4"
    _ajustar_columnas(h)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
