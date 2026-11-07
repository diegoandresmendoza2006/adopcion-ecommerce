"""Certificado de adopción en PDF (hoja A4 horizontal, listo para imprimir o compartir)."""
import io
import urllib.request
from datetime import datetime
from typing import Optional

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

VERDE = HexColor("#1B5E20")
VERDE_CLARO = HexColor("#E8F5E9")
VERDE_MEDIO = HexColor("#43A047")
DORADO = HexColor("#C9A227")
CREMA = HexColor("#FFFDF6")
GRIS = HexColor("#555555")

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


# Letra manuscrita (Great Vibes, licencia OFL) para las firmas; si el archivo falta se usa cursiva normal.
_FUENTE_FIRMA = "Times-BoldItalic"
try:
    from pathlib import Path
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("Firma", str(Path(__file__).parent / "fonts" / "GreatVibes-Regular.ttf")))
    _FUENTE_FIRMA = "Firma"
except Exception:
    pass


def _t(texto) -> str:
    """Las fuentes estándar del PDF solo traen Latin-1: lo que no se pueda dibujar se cambia por '?'."""
    return str(texto or "").encode("cp1252", "replace").decode("cp1252")


def fecha_larga(f: datetime) -> str:
    return f"{f.day} de {MESES[f.month - 1]} de {f.year}"


def edad_texto(meses: Optional[int]) -> str:
    if meses is None:
        return ""
    if meses < 12:
        return f"{meses} {'mes' if meses == 1 else 'meses'}"
    anios = meses // 12
    return f"{anios} {'año' if anios == 1 else 'años'}"


def _foto(url: Optional[str]):
    """Descarga la foto de la mascota (si hay y es https). Si algo falla, el certificado sale sin foto."""
    if not url or not url.lower().startswith("https://"):
        return None
    try:
        with urllib.request.urlopen(url, timeout=4) as r:   # noqa: S310 (la URL viene de nuestra base de datos)
            datos = r.read(5 * 1024 * 1024 + 1)
        if len(datos) > 5 * 1024 * 1024:
            return None
        return ImageReader(io.BytesIO(datos))
    except Exception:
        return None


def _huella(c, cx, cy, escala, color):
    """Huellita: una almohadilla grande y cuatro deditos."""
    c.setFillColor(color)
    c.ellipse(cx - 17 * escala, cy - 15 * escala, cx + 17 * escala, cy + 8 * escala, stroke=0, fill=1)
    for dx, dy, r in ((-24, 14, 7), (-9, 26, 7.5), (9, 26, 7.5), (24, 14, 7)):
        c.circle(cx + dx * escala, cy + dy * escala, r * escala, stroke=0, fill=1)


def _marco(c, ancho, alto):
    c.setFillColor(CREMA)
    c.rect(0, 0, ancho, alto, stroke=0, fill=1)
    c.setStrokeColor(VERDE)
    c.setLineWidth(4)
    c.roundRect(22, 22, ancho - 44, alto - 44, 14, stroke=1, fill=0)
    c.setStrokeColor(DORADO)
    c.setLineWidth(1.2)
    c.roundRect(32, 32, ancho - 64, alto - 64, 10, stroke=1, fill=0)
    # Franja verde arriba y abajo, recortadas con las esquinas redondeadas del marco (sin sobresalir)
    c.saveState()
    recorte = c.beginPath()
    recorte.roundRect(22, 22, ancho - 44, alto - 44, 14)
    c.clipPath(recorte, stroke=0, fill=0)
    c.setFillColor(VERDE)
    c.rect(22, alto - 64, ancho - 44, 42, stroke=0, fill=1)
    c.rect(22, 22, ancho - 44, 18, stroke=0, fill=1)
    c.restoreState()
    # Huellitas decorativas de fondo
    for x, y, e in ((95, alto - 150, 1.0), (ancho - 95, alto - 150, 1.0)):   # lejos de las firmas
        _huella(c, x, y, e, VERDE_CLARO)


def generar_certificado(*, solicitud_id: int, adoptante: str, documento: str, mascota: str, especie: str,
                        raza: Optional[str], edad_meses: Optional[int], refugio: str, fecha: datetime,
                        foto_url: Optional[str] = None, aprobado_por: Optional[str] = None) -> bytes:
    ancho, alto = landscape(A4)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.setTitle(_t(f"Certificado de adopción - {mascota}"))
    c.setAuthor("Paws&Shop")
    _marco(c, ancho, alto)

    # Encabezado
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(ancho / 2, alto - 50, _t("PAWS&SHOP  ·  ADOPCIÓN RESPONSABLE"))
    _huella(c, ancho / 2, alto - 100, 0.9, VERDE_MEDIO)

    c.setFillColor(VERDE)
    c.setFont("Times-Bold", 40)
    c.drawCentredString(ancho / 2, alto - 165, _t("Certificado de Adopción"))
    c.setStrokeColor(DORADO)
    c.setLineWidth(1.5)
    c.line(ancho / 2 - 120, alto - 178, ancho / 2 + 120, alto - 178)

    # Foto (si hay) a la izquierda; el texto se centra en el resto de la hoja
    foto = _foto(foto_url)
    centro = ancho / 2
    if foto is not None:
        radio, fx, fy = 62, 150, alto / 2 - 20
        c.setStrokeColor(DORADO)
        c.setLineWidth(4)
        c.circle(fx, fy, radio + 4, stroke=1, fill=0)
        c.saveState()
        recorte = c.beginPath()
        recorte.circle(fx, fy, radio)
        c.clipPath(recorte, stroke=0, fill=0)
        iw, ih = foto.getSize()
        escala = max(2 * radio / iw, 2 * radio / ih)
        c.drawImage(foto, fx - iw * escala / 2, fy - ih * escala / 2, iw * escala, ih * escala, mask="auto")
        c.restoreState()
        centro = (ancho + 150 + radio) / 2

    c.setFillColor(GRIS)
    c.setFont("Times-Italic", 15)
    c.drawCentredString(centro, alto - 212, "Se certifica que")
    c.setFillColor(HexColor("#222222"))
    c.setFont("Times-BoldItalic", 30)
    c.drawCentredString(centro, alto - 250, _t(adoptante))
    if documento:
        c.setFillColor(GRIS)
        c.setFont("Helvetica", 11)
        c.drawCentredString(centro, alto - 268, _t(documento))

    c.setFont("Times-Italic", 15)
    c.drawCentredString(centro, alto - 298, "ha adoptado con amor a")
    c.setFillColor(VERDE)
    c.setFont("Times-Bold", 34)
    c.drawCentredString(centro, alto - 338, _t(mascota))
    detalle = "  ·  ".join(x for x in (especie, raza or "", edad_texto(edad_meses)) if x)
    c.setFillColor(GRIS)
    c.setFont("Helvetica", 12)
    c.drawCentredString(centro, alto - 358, _t(detalle))

    c.setFont("Times-Roman", 14)
    c.drawCentredString(centro, alto - 386, _t(f"en {refugio}, el {fecha_larga(fecha)}."))

    # Compromiso
    c.setFillColor(GRIS)
    c.setFont("Times-Italic", 11)
    compromiso = ("El adoptante se compromete a brindar alimento, atención veterinaria, cariño y un hogar seguro, "
                  "y a compartir el seguimiento de su compañero con el refugio.")
    y = alto - 412
    for linea in simpleSplit(_t(compromiso), "Times-Italic", 11, 470):
        c.drawCentredString(centro, y, linea)
        y -= 14

    # Firmas
    base = 96
    c.setStrokeColor(GRIS)
    c.setLineWidth(0.8)
    firmantes = ((ancho * 0.28, "Por el refugio", refugio, "Representante del refugio"),
                 (ancho * 0.72, "Por Paws&Shop", "Diego Mendoza", "Gerente General"))
    for x, rotulo, nombre, cargo in firmantes:
        # La firma va en cursiva grande sobre la línea; debajo, el cargo/entidad
        c.setFillColor(HexColor("#1F3A5F"))
        tam = 30
        while tam > 12 and c.stringWidth(_t(nombre), _FUENTE_FIRMA, tam) > 215:
            tam -= 1                      # nombres de refugio largos se achican para caber
        c.setFont(_FUENTE_FIRMA, tam)
        c.drawCentredString(x, base + 22, _t(nombre))
        c.line(x - 115, base + 16, x + 115, base + 16)
        c.setFillColor(GRIS)
        c.setFont("Helvetica", 10)
        c.drawCentredString(x, base, _t(cargo))
    _huella(c, ancho / 2, base + 12, 0.7, VERDE_MEDIO)

    # Pie
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(ancho / 2, 28, _t(f"Certificado N.º PS-{solicitud_id:06d}  ·  Generado el {fecha_larga(datetime.now())}"))

    c.showPage()
    c.save()
    return buffer.getvalue()
