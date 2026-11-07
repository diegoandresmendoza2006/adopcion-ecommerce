"""Descargas por enlace temporal: el navegador abre la ruta y el archivo se baja solo.

El enlace lo entrega un endpoint que SÍ exige sesión (p. ej. /adopciones/{id}/certificado/enlace) y
trae un token que vence en pocos minutos y sirve solo para ese archivo.
"""
import re
import unicodedata
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from .. import certificado, database, models, reportes, security
from .adopciones import ESTADO_APROBADA
from .admin import TIPO_XLSX

router = APIRouter(prefix="/descargas", tags=["Descargas"])


def _nombre_seguro(texto: str) -> str:
    limpio = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", limpio).strip("_") or "mascota"


def datos_del_certificado(db: Session, solicitud_id: int):
    """(solicitud, mascota, usuario, refugio) de una adopción APROBADA, o 404/400."""
    S, M, U, R = models.SolicitudAdopcion, models.Mascota, models.Usuario, models.Refugio
    fila = (db.query(S, M, U, R).join(M, M.id == S.mascota_id).join(U, U.id == S.usuario_id)
            .outerjoin(R, R.id == M.refugio_id).filter(S.id == solicitud_id).first())
    if not fila:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La solicitud no existe")
    if fila[0].estado != ESTADO_APROBADA:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="El certificado solo existe para adopciones aprobadas")
    return fila


@router.get("/certificado/{solicitud_id}")
def descargar_certificado(solicitud_id: int, t: str = Query(..., max_length=1000),
                          db: Session = Depends(database.get_db)):
    carga = security.leer_token_descarga(t, "certificado")
    if carga.get("datos", {}).get("solicitud_id") != solicitud_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Enlace inválido")
    s, m, u, r = datos_del_certificado(db, solicitud_id)
    documento = f"{u.tipo_documento} {u.numero_documento}" if u.tipo_documento and u.numero_documento else ""
    aprobador = db.query(models.Usuario).filter(models.Usuario.id == s.resuelto_por_id).first() if s.resuelto_por_id else None
    pdf = certificado.generar_certificado(
        solicitud_id=s.id, adoptante=s.nombre_contacto or u.nombre_completo, documento=documento,
        mascota=m.nombre, especie=m.especie, raza=m.raza, edad_meses=m.edad_meses,
        refugio=r.nombre if r else "Paws&Shop", fecha=s.fecha_respuesta or s.fecha_solicitud or datetime.now(),
        foto_url=m.imagen_url, aprobado_por=aprobador.nombre_completo if aprobador else None)
    return Response(content=pdf, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=certificado_adopcion_{_nombre_seguro(m.nombre)}.pdf"})


@router.get("/reporte")
def descargar_reporte(t: str = Query(..., max_length=1000), db: Session = Depends(database.get_db)):
    carga = security.leer_token_descarga(t, "reporte")
    datos = carga.get("datos", {})
    mes, historico = datos.get("mes"), bool(datos.get("historico"))
    return Response(content=reportes.construir_reporte(db, mes, historico), media_type=TIPO_XLSX, headers={
        "Content-Disposition": f"attachment; filename={reportes.nombre_archivo_reporte(mes, historico)}"})
