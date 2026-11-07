import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from .. import schemas
from .. import database
from .. import models
from .. import imagenes
from .. import reportes
from .adopciones import ESTADO_APROBADA
from .. import security
from ..paginacion import like, paginar

router = APIRouter(prefix="/admin", tags=["Administración"], dependencies=[Depends(security.require_admin)])

PATRON_MES = reportes.PATRON_MES
TIPO_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/metricas", response_model=schemas.MetricasOut)
def metricas(mes: Optional[str] = Query(None, pattern=PATRON_MES), db: Session = Depends(database.get_db)):
    return reportes.calcular_metricas(db, mes)


@router.get("/metricas/meses", response_model=List[schemas.MesOut])
def metricas_por_mes(db: Session = Depends(database.get_db)):
    """Mes a mes desde el primer movimiento hasta hoy (para el panel con historial)."""
    return reportes.serie_mensual(db)


@router.get("/reporte.xlsx")
def reporte_excel(mes: Optional[str] = Query(None, pattern=PATRON_MES), historico: bool = Query(False),
                  db: Session = Depends(database.get_db)):
    return Response(
        content=reportes.construir_reporte(db, mes, historico), media_type=TIPO_XLSX,
        headers={"Content-Disposition": f"attachment; filename={reportes.nombre_archivo_reporte(mes, historico)}"})


@router.get("/reporte/enlace", response_model=schemas.EnlaceOut)
def enlace_reporte(mes: Optional[str] = Query(None, pattern=PATRON_MES), historico: bool = Query(False),
                   admin: models.Usuario = Depends(security.require_admin)):
    """Enlace temporal (5 min) para bajar el Excel desde el navegador, sin pasar el token de sesión."""
    token = security.crear_token_descarga("reporte", admin.id, {"mes": mes, "historico": historico})
    return schemas.EnlaceOut(ruta=f"/descargas/reporte?t={token}", expira_en=security.MINUTOS_DESCARGA * 60)


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


def _eliminar_usuario(db: Session, u: models.Usuario, forzar: bool, quien: str) -> None:
    """Elimina una cuenta. Con historial (adopciones o compras) solo si [forzar]: en ese caso se borra
    TODO lo suyo (solicitudes con sus seguimientos, pedidos con su detalle) y las mascotas que había
    adoptado vuelven a quedar disponibles."""
    S, O = models.SolicitudAdopcion, models.OrdenCompra
    solicitudes = db.query(S).filter(S.usuario_id == u.id).all()
    ordenes = db.query(O).filter(O.usuario_id == u.id).all()
    if (solicitudes or ordenes) and not forzar:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"{quien} tiene solicitudes de adopción o compras registradas; "
                                   "no se puede eliminar sin borrar también ese historial")
    for s in solicitudes:
        db.query(models.SeguimientoAdopcion).filter(models.SeguimientoAdopcion.solicitud_id == s.id).delete()
        if s.estado == ESTADO_APROBADA:
            mascota = db.query(models.Mascota).filter(models.Mascota.id == s.mascota_id).first()
            if mascota and mascota.estado_adopcion == "Adoptada":
                mascota.estado_adopcion = "Disponible"
        db.delete(s)
    for o in ordenes:
        db.query(models.DetalleOrden).filter(models.DetalleOrden.orden_id == o.id).delete()
        db.delete(o)
    # Lo que esta persona resolvió como encargado se conserva (sin su nombre)
    db.query(S).filter(S.resuelto_por_id == u.id).update({S.resuelto_por_id: None})
    db.query(models.FavoritoMascota).filter(models.FavoritoMascota.usuario_id == u.id).delete()
    db.query(models.SeleccionProducto).filter(models.SeleccionProducto.usuario_id == u.id).delete()
    foto = u.foto_url
    db.delete(u)
    db.commit()
    imagenes.limpiar(db, foto)


def _encargado_o_404(db: Session, encargado_id: int) -> models.Usuario:
    e = db.query(models.Usuario).filter(models.Usuario.id == encargado_id,
                                        models.Usuario.rol_id == security.ROL_ENCARGADO).first()
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El encargado no existe")
    return e


def _encargado_out(db: Session, e: models.Usuario) -> schemas.EncargadoOut:
    refugio = db.query(models.Refugio).filter(models.Refugio.id == e.refugio_id).first() if e.refugio_id else None
    return schemas.EncargadoOut(id=e.id, nombre_completo=e.nombre_completo, email=e.email,
                                refugio_id=e.refugio_id, refugio_nombre=refugio.nombre if refugio else None)


@router.put("/encargados/{encargado_id}", response_model=schemas.EncargadoOut)
def editar_encargado(encargado_id: int, datos: schemas.EncargadoUpdate, db: Session = Depends(database.get_db)):
    e = _encargado_o_404(db, encargado_id)
    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    if "email" in cambios and cambios["email"] != e.email and db.query(models.Usuario.id).filter(
            models.Usuario.email == cambios["email"], models.Usuario.rol_id == security.ROL_ENCARGADO).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ese correo ya está registrado")
    if "refugio_id" in cambios and not db.query(models.Refugio.id).filter(
            models.Refugio.id == cambios["refugio_id"]).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El refugio no existe")
    if "password" in cambios:
        e.password_hash = security.hash_password(cambios.pop("password"))
    for campo, valor in cambios.items():
        setattr(e, campo, valor)
    db.commit()
    db.refresh(e)
    return _encargado_out(db, e)


@router.delete("/encargados/{encargado_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_encargado(encargado_id: int, forzar: bool = Query(False), db: Session = Depends(database.get_db)):
    _eliminar_usuario(db, _encargado_o_404(db, encargado_id), forzar, "Este encargado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
def eliminar_cliente(cliente_id: int, forzar: bool = Query(False), db: Session = Depends(database.get_db)):
    _eliminar_usuario(db, _cliente_o_404(db, cliente_id), forzar, "Este cliente")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
