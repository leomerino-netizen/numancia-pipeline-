"""
Genera la Propuesta Editorial A4 — Editorial Numancia / Grupo Printcolorweb.com

Estilo limpio basado en el lenguaje visual de Printcolorweb (rev. 14-05-2026):
- Paleta sobria: navy #1F3D6B + grises. Sin azules vivos, sin naranjas, sin cremas.
- Tipografía única: Helvetica (Regular / Bold / Oblique).
- Tablas con bordes sutiles, etiquetas con fondo #F4F6F8, sin recuadros estridentes.
- Paginación real "Página X/N" en footer (canvas callback).
- Conserva los bloques diferenciadores del Numancia: asesora, amortización,
  recompra, notas adicionales y cómo aceptar.

Convención de emails:
- Asesoras del equipo (Laura, Débora, Juan): sin punto entre nombre y apellido.
"""
import io, os, math
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable


# ── Paleta y constantes ──────────────────────────────────────────────────────
NAVY        = colors.HexColor('#1F3D6B')
NAVY_DK     = colors.HexColor('#162E52')
GREY_L      = colors.HexColor('#E8ECEF')
GREY_BG     = colors.HexColor('#F4F6F8')
GREY_BORD   = colors.HexColor('#C8C8C8')
GREY_LINE   = colors.HexColor('#DCDCDC')
GREY_TXT    = colors.HexColor('#666666')
GREY_STRIKE = colors.HexColor('#555555')
TEXT        = colors.HexColor('#222222')
BLANCO      = colors.white

AW, AH = A4
LM = 18*mm
RM = 18*mm
TM = 15*mm
BM = 18*mm
W_DOC = AW - LM - RM   # 174 mm


# ── Botón clicable ───────────────────────────────────────────────────────────
class BotonEnlace(Flowable):
    def __init__(self, texto, url, w, h=10*mm, bg=NAVY, fg=BLANCO, fontsize=9):
        super().__init__()
        self.texto = texto; self.url = url
        self.bw = w; self.bh = h; self.bg = bg; self.fg = fg
        self.fontsize = fontsize

    def wrap(self, *a):
        return self.bw, self.bh

    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.roundRect(0, 0, self.bw, self.bh, 2, fill=1, stroke=0)
        c.setFillColor(self.fg)
        c.setFont('Helvetica-Bold', self.fontsize)
        c.drawCentredString(self.bw / 2, self.bh / 2 - self.fontsize * 0.36,
                            self.texto)
        c.linkURL(self.url, (0, 0, self.bw, self.bh), relative=1, thickness=0)


# ── Helpers de archivos ──────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))

def _find(candidates):
    for c in candidates:
        p = os.path.join(_HERE, c)
        if os.path.isfile(p):
            return p
    return ''


def _normalizar_asesora_slug(asesora):
    if not asesora:
        return 'laura'
    s = str(asesora).strip().lower()
    if s in {'laura', 'debora', 'juan', 'nancy'}:
        return s
    if 'laura' in s:  return 'laura'
    if 'débora' in s or 'debora' in s: return 'debora'
    if 'juan'  in s:  return 'juan'
    if 'nancy' in s:  return 'nancy'
    return 'laura'


LOGO_CANDIDATES = [
    'fotos/logo_numancia.png',
    'logo_numancia.png',
    'fotos/logotipo_editorial_numancia-1024x187-1.png',
    'logotipo_editorial_numancia-1024x187-1.png',
    'logotipo-editorial-numancia-apaisado-color-hexadecimal.png',
    'Fotos/logotipo-editorial-numancia-apaisado-color-hexadecimal.png',
]

def _find_logo():
    """
    Localiza el archivo del logo de Editorial Numancia.
    Estrategia:
      1. Probar nombres conocidos exactos (lista LOGO_CANDIDATES).
      2. Si no aparece, buscar con glob cualquier *logo*numancia*.png
         en la raíz del proyecto o en fotos/.
    Devuelve '' si no encuentra nada.
    """
    import glob as _glob
    for c in LOGO_CANDIDATES:
        p = os.path.join(_HERE, c)
        if os.path.isfile(p):
            return p
    for pat in ('*logo*numancia*.png', 'fotos/*logo*numancia*.png',
                'Fotos/*logo*numancia*.png'):
        matches = _glob.glob(os.path.join(_HERE, pat))
        if matches:
            return matches[0]
    return ''


LOGO_PATH = _find_logo()


ASESORAS = {
    'laura': {
        'nombre': 'Laura Vega Ugarte', 'iniciales': 'LV', 'ext': '282-283',
        'email': 'lauravega@editorialnumancia.com',
        'horario': 'Lunes a viernes · 9:00 a 14:00 h',
        'foto': _find(['fotos/laura-circ.png', 'fotos/laura.jpg',
                       'laura.jpg',
                       'laura-asesora-editorial-editorial-numancia.jpg']),
        'calendario_url': 'https://printcolorweb.zohobookings.eu/#/laura',
    },
    'debora': {
        'nombre': 'Débora Tómas', 'iniciales': 'DT', 'ext': '287',
        'email': 'deboratomas@editorialnumancia.com',
        'horario': 'Lunes a viernes · 9:00 a 14:00 h',
        'foto': _find(['fotos/debora-circ.png', 'fotos/debora.jpg',
                       'debora.jpg',
                       'debora-asesora-editorial-numancia.jpg']),
        'calendario_url': 'https://printcolorweb.zohobookings.eu/#/debora',
    },
    'juan': {
        'nombre': 'Juan Muñoz', 'iniciales': 'JM', 'ext': '289',
        'email': 'juanmunoz@editorialnumancia.com',
        'horario': 'Lunes a viernes · 17:00 a 20:00 h',
        'foto': _find(['fotos/juan-circ.png', 'fotos/juan.jpg',
                       'juan.jpg',
                       'juan-nunoz-maquetaror-editorial-numancia.jpg']),
        'calendario_url': 'https://printcolorweb.zohobookings.eu/#/juan',
    },
    'nancy': {
        'nombre': 'Nancy', 'iniciales': 'NA', 'ext': '285',
        'email': 'info@editorialnumancia.com',
        'horario': 'Lunes a viernes · 9:00 a 14:00 h',
        'foto': _find(['fotos/nancy-circ.png', 'fotos/nancy.jpg',
                       'nancy.jpg', 'Nancy.jpg']),
        'calendario_url': 'https://printcolorweb.zohobookings.eu/#/nancy',
    },
}

def _resolver_asesora(key):
    return ASESORAS.get(_normalizar_asesora_slug(key), ASESORAS['laura'])


def _aplicar_mascara_circular(ruta_foto, diametro_px=400):
    from PIL import Image as PILImage, ImageDraw
    with PILImage.open(ruta_foto) as im:
        if im.mode != 'RGBA':
            im = im.convert('RGBA')
        iw, ih = im.size
        ya_circular = (iw == ih and ruta_foto.lower().endswith('-circ.png'))
        if ya_circular:
            buf = io.BytesIO(); im.save(buf, format='PNG')
            return buf.getvalue()
        if iw > ih:
            left = (iw - ih) // 2
            im = im.crop((left, 0, left + ih, ih))
        elif ih > iw:
            top = (ih - iw) // 2
            im = im.crop((0, top, iw, top + iw))
        im = im.resize((diametro_px, diametro_px), PILImage.LANCZOS)
        mascara = PILImage.new('L', (diametro_px, diametro_px), 0)
        ImageDraw.Draw(mascara).ellipse(
            (0, 0, diametro_px, diametro_px), fill=255)
        resultado = PILImage.new('RGBA',
            (diametro_px, diametro_px), (255, 255, 255, 0))
        resultado.paste(im, (0, 0), mascara)
        buf = io.BytesIO(); resultado.save(buf, format='PNG')
        return buf.getvalue()


def _logo_con_fondo_transparente(path, tolerancia=10):
    """
    Devuelve bytes PNG del logo con el fondo opaco uniforme convertido en
    transparente. Útil cuando el logo viene como RGB sin canal alpha.

    Algoritmo:
      1. Si el PNG ya tiene canal alpha (RGBA), se devuelve sin cambios.
      2. Si es RGB, se mira el color de las 4 esquinas. Si son uniformes
         (mismo color con la tolerancia dada), ese es el color de fondo
         y se convierten todos los píxeles parecidos a transparentes.
      3. Si las esquinas no son uniformes, no se modifica (no es seguro
         deducir el fondo).

    La tolerancia es deliberadamente baja (10) para no comerse contenido
    interno del logo de tonalidades parecidas (por ejemplo, sombras
    oscuras dentro de un icono).
    """
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        if im.mode == 'RGBA':
            buf = io.BytesIO(); im.save(buf, format='PNG')
            return buf.getvalue()
        im = im.convert('RGBA')
        w, h = im.size
        esquinas = [
            im.getpixel((0, 0)),
            im.getpixel((w - 1, 0)),
            im.getpixel((0, h - 1)),
            im.getpixel((w - 1, h - 1)),
        ]
        r0, g0, b0 = esquinas[0][:3]
        uniforme = all(
            abs(c[0] - r0) <= tolerancia and
            abs(c[1] - g0) <= tolerancia and
            abs(c[2] - b0) <= tolerancia
            for c in esquinas
        )
        if not uniforme:
            buf = io.BytesIO(); im.save(buf, format='PNG')
            return buf.getvalue()
        # Aplicar transparencia a píxeles dentro de la tolerancia del fondo
        pixels = im.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if (abs(r - r0) <= tolerancia and
                    abs(g - g0) <= tolerancia and
                    abs(b - b0) <= tolerancia):
                    pixels[x, y] = (r, g, b, 0)
        buf = io.BytesIO(); im.save(buf, format='PNG')
        return buf.getvalue()


def S(name, font='Helvetica', size=9, leading=12, color=TEXT,
      align=TA_LEFT, **kw):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                          textColor=color, alignment=align, **kw)


def _fmt_eur(v):
    return f'€ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


# Mapeo de nombres canónicos de formato a sus dimensiones reales en cm.
# Si el formato contiene dimensiones embebidas (p.ej. "21x21" o "17×24"),
# se extraen con regex; este dict solo cubre los nombres no numéricos.
_DIMENSIONES_FORMATO = {
    'a4':       '21 × 29,7 cm',
    'a5':       '14,8 × 21 cm',
    'a6':       '10,5 × 14,8 cm',
    'b5':       '17,6 × 25 cm',
    'bolsillo': '11 × 18 cm',
}


def _get_formato(d):
    """
    Lectura tolerante del campo 'formato' del payload.
    Acepta varios alias por si Lovable cambia el nombre del campo o lo manda
    anidado dentro de 'especificaciones'.

    Orden de búsqueda:
      1. d['formato']
      2. d['especificaciones']['formato']
      3. d['tamano'] / d['tamaño']
      4. d['size']
    """
    if not isinstance(d, dict):
        return ''
    for key in ('formato', 'tamano', 'tamaño', 'size'):
        v = d.get(key)
        if v:
            return str(v).strip()
    specs = d.get('especificaciones') or {}
    if isinstance(specs, dict):
        for key in ('formato', 'tamano', 'tamaño', 'size'):
            v = specs.get(key)
            if v:
                return str(v).strip()
    return ''


def _dimensiones_formato(formato_str):
    """
    Devuelve las dimensiones del libro en cm a partir del nombre del formato.

    Ejemplos:
      'A5'              → '14,8 × 21 cm'
      '21x21'           → '21 × 21 cm'
      '17×24'           → '17 × 24 cm'
      'Cuadrado 21x21'  → '21 × 21 cm'  (extrae dimensiones embebidas)
      'A5 (14,8x21)'    → '14,8 × 21 cm'
      'Bolsillo'        → '11 × 18 cm'

    Si no reconoce ni puede parsear las dimensiones, devuelve '' (en cuyo
    caso el llamador no debe mostrar el paréntesis).
    """
    if not formato_str:
        return ''
    f = str(formato_str).strip().lower()
    # 1) Si contiene dimensiones embebidas (NxM o N×M), extraerlas
    import re as _re
    m = _re.search(
        r'(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)', f)
    if m:
        a, b = m.group(1), m.group(2)
        return f'{a} × {b} cm'
    # 2) Coincidencia directa con la tabla de canónicos
    if f in _DIMENSIONES_FORMATO:
        return _DIMENSIONES_FORMATO[f]
    # 3) Coincidencia parcial (formato="Tapa dura A5", etc.)
    for k, v in _DIMENSIONES_FORMATO.items():
        if k in f:
            return v
    return ''


def _calcular_totales(d):
    """
    Centraliza el cálculo de todos los importes del presupuesto.
    Devuelve dict con los importes desglosados y totales.

    Altas en canales de venta (precios fijos):
    - Alta Librería Numancia sola: 25 €
    - Alta Amazon sola: 50 €
    - Pack Librería + Amazon: 65 € (en lugar de 25 + 50 por separado)
    - Gestión Sello Editorial Numancia: 45 € (si sello_editorial=true)
    """
    pu_imp = d['precio_unitario']
    cant   = d['cantidad']
    dto    = d.get('descuento_pct', 0) or 0
    pm     = d.get('precio_maquetacion', 0) or 0
    pl     = d.get('precio_legal', 0) or 0
    pc     = d.get('precio_correccion', 0) or 0

    # Maquetación con descuento (tachado)
    aplicar_dto_maq = bool(d.get('aplicar_descuento_maquetacion', False))
    pm_tarifa       = d.get('precio_maquetacion_tarifa', 0) or 0
    mostrar_tachado_maq = aplicar_dto_maq and pm_tarifa > pm

    # ── Altas en canales de venta (precios fijos, lógica pack) ──────────
    vl_cant = int(d.get('venta_libreria_cantidad', 0) or 0)
    va_cant = int(d.get('venta_amazon_cantidad', 0) or 0)
    tiene_alta_libreria = vl_cant > 0
    tiene_alta_amazon   = va_cant > 0
    alta_combinada      = tiene_alta_libreria and tiene_alta_amazon

    if alta_combinada:
        pack_alta_cost     = 65.0
        alta_libreria_cost = 0
        alta_amazon_cost   = 0
    else:
        pack_alta_cost     = 0
        alta_libreria_cost = 25.0 if tiene_alta_libreria else 0
        alta_amazon_cost   = 50.0 if tiene_alta_amazon else 0

    # ── Gestión Sello Editorial Numancia ────────────────────────────────
    sello_editorial      = bool(d.get('sello_editorial', False))
    sello_editorial_cost = 45.0 if sello_editorial else 0

    altas_total = pack_alta_cost + alta_libreria_cost + alta_amazon_cost + sello_editorial_cost

    impresion_full = round(pu_imp * cant, 2)
    subtotal_full  = round(impresion_full + pm + pl + pc + altas_total, 2)
    descuento_eur  = round(subtotal_full * dto / 100, 2) if dto else 0
    total_final    = round(subtotal_full - descuento_eur, 2)

    return {
        'impresion_full':        impresion_full,
        'maquetacion':           pm,
        'maquetacion_tarifa':    pm_tarifa,
        'mostrar_tachado_maq':   mostrar_tachado_maq,
        'legales':               pl,
        'correccion':            pc,
        # Altas y sello
        'tiene_alta_libreria':   tiene_alta_libreria,
        'tiene_alta_amazon':     tiene_alta_amazon,
        'alta_combinada':        alta_combinada,
        'pack_alta_cost':        pack_alta_cost,
        'alta_libreria_cost':    alta_libreria_cost,
        'alta_amazon_cost':      alta_amazon_cost,
        'venta_libreria_cant':   vl_cant,
        'venta_amazon_cant':     va_cant,
        'sello_editorial':       sello_editorial,
        'sello_editorial_cost':  sello_editorial_cost,
        # Totales
        'subtotal_full':         subtotal_full,
        'descuento_pct':         dto,
        'descuento_eur':         descuento_eur,
        'total_final':           total_final,
        'precio_unit_full':      round(subtotal_full / cant, 2) if cant else 0,
        'precio_unit_dto':       round(total_final / cant, 2) if cant else 0,
        'precio_unit_impresion': round(pu_imp * (1 - dto / 100), 2) if dto else pu_imp,
    }


# ── Canvas con paginación X/N ────────────────────────────────────────────────
class _NumberedCanvas(canvas.Canvas):
    footer_text = ''

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _draw_footer(self, total_paginas):
        self.saveState()
        self.setStrokeColor(GREY_LINE)
        self.setLineWidth(0.4)
        self.line(LM, 11*mm, AW - RM, 11*mm)
        self.setFont('Helvetica', 8)
        self.setFillColor(GREY_TXT)
        self.drawString(LM, 7.5*mm, self.footer_text)
        self.drawRightString(AW - RM, 7.5*mm,
            f'Página {self._pageNumber}/{total_paginas}')
        self.restoreState()


def _hacer_canvas(num_presupuesto, cliente):
    texto = f'Presupuesto Nº {num_presupuesto} · {cliente}'
    return type('_NumberedCanvasInst', (_NumberedCanvas,),
                {'footer_text': texto})


# ── Cabecera ─────────────────────────────────────────────────────────────────
def _cabecera(asesora, num_presupuesto, fecha, con_logo=True):
    items = []

    izq = None
    if con_logo and LOGO_PATH and os.path.isfile(LOGO_PATH):
        logo_h = 16*mm
        try:
            from PIL import Image as PIL
            with PIL.open(LOGO_PATH) as _i:
                ratio = _i.width / _i.height
            logo_w = min(logo_h * ratio, W_DOC * 0.50)
            # Procesar el PNG para añadir transparencia si tiene fondo opaco.
            logo_bytes = _logo_con_fondo_transparente(LOGO_PATH)
            izq = Image(io.BytesIO(logo_bytes),
                        width=logo_w, height=logo_h)
        except Exception as e:
            print(f'[presupuesto] error procesando logo ({e}), '
                  f'fallback a texto', flush=True)
            izq = None

    if izq is None:
        izq = Paragraph(
            '<font name="Helvetica-Bold" size="14" color="#1F3D6B">'
            'Editorial Numancia</font><br/>'
            '<font name="Helvetica" size="8" color="#666666">'
            'Grupo Printcolorweb.com</font>',
            S('cabL', 'Helvetica', 14, 17, NAVY))

    der = Paragraph(
        f'<font name="Helvetica-Bold" size="11" color="#1F3D6B">'
        f'Presupuesto Nº {num_presupuesto}</font><br/>'
        f'<font name="Helvetica" size="8.5" color="#666666">{fecha}</font><br/>'
        '<font name="Helvetica-Bold" size="8.5" color="#222222">'
        'FULLCOLOR PRINTCOLOR, S.L.</font><br/>'
        '<font name="Helvetica" size="8" color="#666666">'
        'CIF B83969014<br/>'
        'Tel. 93 580 81 32 · info@editorialnumancia.com<br/>'
        'Horario taller: 9:00 a 17:00 h</font>',
        S('cabR', 'Helvetica', 8.5, 11.5, TEXT, TA_RIGHT))

    tabla = Table([[izq, der]], colWidths=[W_DOC*0.50, W_DOC*0.50])
    tabla.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
    ]))
    items.append(tabla)
    items.append(Spacer(1, 6))
    items.append(HRFlowable(width='100%', thickness=0.8, color=NAVY,
                             spaceBefore=0, spaceAfter=8))
    return items


def _bloque_cliente_asesora(d, asesora):
    fmt = _get_formato(d)
    izq = Paragraph(
        f'<font name="Helvetica" size="8" color="#666666">CLIENTE</font><br/>'
        f'<font name="Helvetica-Bold" size="11" color="#222222">{d["cliente"]}</font><br/>'
        f'<font name="Helvetica" size="8.5" color="#222222">'
        f'Obra: <b>{d["obra"]}</b> · {d["genero"]} · {d["paginas"]} págs · '
        f'Formato {fmt}</font>',
        S('cli','Helvetica',8.5,12,TEXT))
    der = Paragraph(
        f'<font name="Helvetica" size="8" color="#666666">ASESORA EDITORIAL</font><br/>'
        f'<font name="Helvetica-Bold" size="11" color="#1F3D6B">{asesora["nombre"]}</font><br/>'
        f'<font name="Helvetica" size="8.5" color="#222222">'
        f'93 580 81 32 ext. {asesora["ext"]} · {asesora["email"]}</font>',
        S('ase','Helvetica',8.5,12,TEXT,TA_RIGHT))
    t = Table([[izq, der]], colWidths=[W_DOC*0.55, W_DOC*0.45])
    t.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
    ]))
    return t


def _headline_precio(d):
    """Headline con precio unitario TOTAL (incluye servicios y corrección)."""
    t = _calcular_totales(d)
    pu_full = t['precio_unit_full']
    pu_dto  = t['precio_unit_dto']
    dto     = t['descuento_pct']

    if dto and pu_dto < pu_full:
        precio_html = (
            f'<font color="#555555"><strike><b>{_fmt_eur(pu_full)}</b></strike></font>'
            f'  <font color="#1F3D6B"><b>{_fmt_eur(pu_dto)}</b></font>')
    else:
        precio_html = f'<font color="#1F3D6B"><b>{_fmt_eur(pu_full)}</b></font>'

    return Paragraph(
        f'<font name="Helvetica-Bold" size="13" color="#222222">'
        f'Tu libro te sale a</font> '
        f'<font size="13">{precio_html}</font> '
        f'<font name="Helvetica" size="11" color="#666666">'
        f'por ejemplar (IVA 4% incluido · todo incluido)</font>',
        S('hl','Helvetica-Bold',13,18,TEXT,TA_LEFT,spaceBefore=4,spaceAfter=4))


def _tabla_producto(d):
    """
    Tabla principal: SOLO impresión y encuadernación.
    Las especificaciones del libro se construyen línea a línea.
    Cada campo (papel, cubierta, laminado, encuadernación, lomo, color
    interior) aparece SOLO si viene del payload con valor no vacío.
    No hay defaults hardcodeados para evitar mostrar datos incorrectos
    (p.ej. 'fresada' cuando es tapa dura).
    """
    pu = d['precio_unitario']
    cant = d['cantidad']
    impresion_total = round(pu * cant, 2)
    IVA_PCT = 0.04
    base    = round(impresion_total / (1 + IVA_PCT), 2)
    iva_eur = round(base * IVA_PCT, 2)
    total   = round(base + iva_eur, 2)

    specs = d.get('especificaciones', {})
    def _spec(key):
        """Lectura tolerante: primero 'especificaciones' anidado, luego raíz."""
        v = specs.get(key) or d.get(key)
        if v is None:
            return ''
        v = str(v).strip()
        return v

    color_int = _spec('color_interior')
    papel     = _spec('papel')
    cubierta  = _spec('cubierta')
    laminado  = _spec('laminado')
    enc       = _spec('encuadernacion')
    lomo      = _spec('lomo')
    impresion_tipo = _spec('tipo_impresion') or 'Digital profesional'

    # Construir el detalle línea a línea, solo con campos no vacíos
    lineas = [f'<b>Título del libro:</b> {d["obra"]}']

    fmt_partes = []
    fmt_val = _get_formato(d)
    if fmt_val:
        dim = _dimensiones_formato(fmt_val)
        if dim:
            fmt_partes.append(f'<b>Formato:</b> {fmt_val} ({dim})')
        else:
            fmt_partes.append(f'<b>Formato:</b> {fmt_val}')
    if color_int:
        fmt_partes.append(f'<b>Interior:</b> {color_int}')
    if fmt_partes:
        lineas.append(' · '.join(fmt_partes))

    if d.get('paginas'):
        lineas.append(f'<b>Páginas:</b> {d["paginas"]}')
    if impresion_tipo:
        lineas.append(f'<b>Tipo de impresión:</b> {impresion_tipo}')
    if papel:
        lineas.append(f'<b>Papel interior:</b> {papel}')

    cub_partes = []
    if cubierta:
        cub_partes.append(f'<b>Cubierta:</b> {cubierta}')
    if laminado:
        cub_partes.append(f'<b>Laminado:</b> {laminado}')
    if cub_partes:
        lineas.append(' · '.join(cub_partes))

    enc_partes = []
    if enc:
        enc_partes.append(f'<b>Encuadernación:</b> {enc}')
    if lomo:
        enc_partes.append(f'<b>Lomo:</b> {lomo}')
    if enc_partes:
        lineas.append(' · '.join(enc_partes))

    detalle_html = '<br/>'.join(lineas)
    detalle = Paragraph(detalle_html,
        S('det','Helvetica',9,13,TEXT,TA_LEFT))

    hdr = lambda txt, align=TA_LEFT: Paragraph(
        f'<font name="Helvetica-Bold" size="9" color="#FFFFFF">{txt}</font>',
        S('h','Helvetica-Bold',9,11,BLANCO,align))

    cant_p  = Paragraph(f'<b>{cant}</b>', S('cnt','Helvetica',10,13,TEXT,TA_CENTER))
    base_p  = Paragraph(_fmt_eur(base),   S('bs','Helvetica',9.5,12,TEXT,TA_CENTER))
    iva_p   = Paragraph(_fmt_eur(iva_eur),S('iv','Helvetica',9.5,12,TEXT,TA_CENTER))
    total_p = Paragraph(f'<b>{_fmt_eur(total)}</b>',
                S('to','Helvetica-Bold',10,13,TEXT,TA_CENTER))

    W_CONCEPTO = 78*mm; W_UDS = 22*mm; W_BASE = 25*mm; W_IVA = 22*mm; W_TOTAL = 27*mm

    data = [
        [hdr('Impresión y encuadernación'),
         hdr('Uds.', TA_CENTER),
         hdr('Base imponible', TA_CENTER),
         hdr('IVA 4%', TA_CENTER),
         hdr('Total', TA_CENTER)],
        [detalle, cant_p, base_p, iva_p, total_p],
    ]
    tabla = Table(data, colWidths=[W_CONCEPTO, W_UDS, W_BASE, W_IVA, W_TOTAL])
    tabla.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), NAVY),
        ('TOPPADDING',(0,0),(-1,0),7),('BOTTOMPADDING',(0,0),(-1,0),7),
        ('LEFTPADDING',(0,0),(-1,0),8),('RIGHTPADDING',(0,0),(-1,0),8),
        ('VALIGN',(0,1),(0,1),'TOP'),
        ('VALIGN',(1,1),(-1,1),'MIDDLE'),
        ('TOPPADDING',(0,1),(-1,1),10),('BOTTOMPADDING',(0,1),(-1,1),10),
        ('LEFTPADDING',(0,1),(-1,1),10),('RIGHTPADDING',(0,1),(-1,1),10),
        ('BOX',(0,0),(-1,-1),0.4,GREY_BORD),
        ('LINEAFTER',(0,0),(-2,-1),0.3,GREY_LINE),
    ]))
    return tabla


def _bloque_servicios(d):
    """
    Solo se muestra si vienen servicios del JSON.
    NO hay valores por defecto: Lovable es responsable de enviar los items.
    Cada caja se muestra solo si su lista no está vacía.
    """
    maq_items = d.get('servicios_maquetacion') or []
    leg_items = d.get('servicios_legales') or []
    pm = d.get('precio_maquetacion', 0) or 0
    pl = d.get('precio_legal', 0) or 0

    # Si no hay ni un solo servicio en ninguna caja, no mostrar el bloque
    mostrar_maq = bool(maq_items) and pm > 0
    mostrar_leg = pl > 0          # antes: bool(leg_items) and pl > 0
    if mostrar_leg and not leg_items:
        leg_items = [
            'Pack de promoción y marketing de tu libro'
        ]
    if not (mostrar_maq or mostrar_leg):
        return []

    items = []

    def _serv_box(titulo, lista, precio, w):
        content = [Paragraph(
            f'<font name="Helvetica-Bold" size="9" color="#1F3D6B">{titulo}</font>',
            S('sbt','Helvetica-Bold',9,12,NAVY))]
        content.append(Spacer(1, 4))
        for it in lista:
            content.append(Paragraph(
                f'<font color="#1F3D6B">·</font>  {it}',
                S('sbi','Helvetica',8.5,12,TEXT,spaceBefore=1)))
        content.append(Spacer(1, 8))
        content.append(Paragraph(
            f'<font name="Helvetica" size="8.5" color="#666666">Pago único</font>  '
            f'<font name="Helvetica-Bold" size="10" color="#1F3D6B">'
            f'{_fmt_eur(precio)}</font>',
            S('sbp','Helvetica',8.5,12,TEXT,TA_RIGHT)))
        t = Table([[content]], colWidths=[w])
        t.setStyle(TableStyle([
            ('BOX',(0,0),(-1,-1),0.4,GREY_BORD),
            ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
            ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
        ]))
        return t

    # Si solo hay una caja, ocupa todo el ancho. Si hay dos, mitades.
    if mostrar_maq and mostrar_leg:
        WS = (W_DOC - 5) / 2
        fila = Table([[
            _serv_box('MAQUETACIÓN Y DISEÑO EDITORIAL', maq_items, pm, WS),
            Spacer(5, 1),
            _serv_box('PROMOCIÓN Y MARKETING', leg_items, pl, WS),
        ]], colWidths=[WS, 5, WS])
        fila.setStyle(TableStyle([
            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
        ]))
        items.append(fila)
    elif mostrar_maq:
        items.append(_serv_box('MAQUETACIÓN Y DISEÑO EDITORIAL',
                               maq_items, pm, W_DOC))
    elif mostrar_leg:
        items.append(_serv_box('PROMOCIÓN Y MARKETING',
                               leg_items, pl, W_DOC))
    return items


def _bloque_resumen(d):
    t = _calcular_totales(d)

    rows = [
        [Paragraph(f'Impresión y encuadernación ({d["cantidad"]} ejemplares)',
                   S('r1','Helvetica',9,12,TEXT)),
         Paragraph(_fmt_eur(t['impresion_full']),
                   S('r1r','Helvetica',9,12,TEXT,TA_RIGHT))],
    ]
    if t['maquetacion'] > 0:
        # Maquetación con tachado de la tarifa original si aplica
        if t['mostrar_tachado_maq']:
            maq_html = (
                f'<font color="#555555"><strike><b>{_fmt_eur(t["maquetacion_tarifa"])}</b></strike></font>'
                f'  <font color="#1F3D6B"><b>{_fmt_eur(t["maquetacion"])}</b></font>'
            )
        else:
            maq_html = _fmt_eur(t['maquetacion'])
        rows.append([
            Paragraph('Maquetación y diseño editorial (pago único)',
                      S('r2','Helvetica',9,12,TEXT)),
            Paragraph(maq_html,
                      S('r2r','Helvetica',9,12,TEXT,TA_RIGHT))
        ])
    if t['legales'] > 0:
        rows.append([
            Paragraph('Promoción y marketing (pago único)',
                      S('r3','Helvetica',9,12,TEXT)),
            Paragraph(_fmt_eur(t['legales']),
                      S('r3r','Helvetica',9,12,TEXT,TA_RIGHT))
        ])
    # ── Altas en canales (pack combinado o individuales) ──────────────
    if t['alta_combinada']:
        rows.append([
            Paragraph(f'Pack alta Librería Numancia + Amazon',
                      S('rpack','Helvetica',9,12,TEXT)),
            Paragraph(_fmt_eur(t['pack_alta_cost']),
                      S('rpackr','Helvetica',9,12,TEXT,TA_RIGHT))
        ])
    else:
        if t['tiene_alta_libreria']:
            rows.append([
                Paragraph(f'Alta en Librería Numancia',
                          S('rvl','Helvetica',9,12,TEXT)),
                Paragraph(_fmt_eur(t['alta_libreria_cost']),
                          S('rvlr','Helvetica',9,12,TEXT,TA_RIGHT))
            ])
        if t['tiene_alta_amazon']:
            rows.append([
                Paragraph(f'Alta en Amazon',
                          S('rva','Helvetica',9,12,TEXT)),
                Paragraph(_fmt_eur(t['alta_amazon_cost']),
                          S('rvar','Helvetica',9,12,TEXT,TA_RIGHT))
            ])
    # ── Gestión Sello Editorial ─────────────────────────────────────────
    if t['sello_editorial']:
        rows.append([
            Paragraph('Gestión Sello Editorial Numancia',
                      S('rsello','Helvetica',9,12,TEXT)),
            Paragraph(_fmt_eur(t['sello_editorial_cost']),
                      S('rsellor','Helvetica',9,12,TEXT,TA_RIGHT))
        ])
    if t['correccion'] > 0:
        rows.append([
            Paragraph('Corrección ortotipográfica y de estilo (pago único)',
                      S('r3c','Helvetica',9,12,TEXT)),
            Paragraph(_fmt_eur(t['correccion']),
                      S('r3cr','Helvetica',9,12,TEXT,TA_RIGHT))
        ])

    # Subtotal sólo si hay descuento global del payload (descuento_pct > 0)
    if t['descuento_pct'] > 0:
        rows.append([
            Paragraph('<b>Subtotal</b> (IVA 4% incluido)',
                      S('r4','Helvetica-Bold',9,12,TEXT)),
            Paragraph(f'<b>{_fmt_eur(t["subtotal_full"])}</b>',
                      S('r4r','Helvetica-Bold',9,12,TEXT,TA_RIGHT))
        ])
        rows.append([
            Paragraph(f'Descuento especial · {t["descuento_pct"]}%',
                      S('r5','Helvetica',9,12,GREY_TXT)),
            Paragraph(f'− {_fmt_eur(t["descuento_eur"])}',
                      S('r5r','Helvetica',9,12,GREY_TXT,TA_RIGHT))
        ])
        rows.append([
            Paragraph('<b>TOTAL CON DESCUENTO (IVA 4% incluido)</b>',
                      S('r6','Helvetica-Bold',10,13,TEXT)),
            Paragraph(f'<b>{_fmt_eur(t["total_final"])}</b>',
                      S('r6r','Helvetica-Bold',13,16,NAVY,TA_RIGHT)),
        ])
    else:
        rows.append([
            Paragraph('<b>TOTAL (IVA 4% incluido)</b>',
                      S('r6','Helvetica-Bold',10,13,TEXT)),
            Paragraph(f'<b>{_fmt_eur(t["total_final"])}</b>',
                      S('r6r','Helvetica-Bold',13,16,NAVY,TA_RIGHT)),
        ])

    tabla = Table(rows, colWidths=[W_DOC*0.72, W_DOC*0.28])
    style_cmds = [
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ALIGN',(1,0),(1,-1),'RIGHT'),
        ('LINEABOVE',(0,-1),(-1,-1),0.8,NAVY),
        ('LINEBELOW',(0,-1),(-1,-1),0.8,NAVY),
        ('BACKGROUND',(0,-1),(-1,-1),GREY_L),
    ]
    if t['descuento_pct'] > 0:
        idx_subt = len(rows) - 3
        style_cmds.append(('BACKGROUND',(0,idx_subt),(-1,idx_subt),GREY_BG))
        style_cmds.append(('LINEABOVE',(0,idx_subt),(-1,idx_subt),0.4,GREY_LINE))

    tabla.setStyle(TableStyle(style_cmds))
    return [tabla]


def _bloque_pasos(d, asesora):
    t = _calcular_totales(d)
    items = []
    items.append(Paragraph(
        '<font name="Helvetica-Bold" size="11" color="#1F3D6B">'
        'Cómo aceptar tu propuesta editorial</font>',
        S('pt','Helvetica-Bold',11,14,NAVY,spaceBefore=4,spaceAfter=2)))
    items.append(Paragraph(
        'Un proceso transparente, sin sorpresas y con tu asesora '
        'acompañándote en cada paso.',
        S('pst','Helvetica-Oblique',8.5,12,GREY_TXT,spaceAfter=8)))

    pago30 = round(t['total_final'] * 0.30, 2)
    pago70 = round(t['total_final'] * 0.70, 2)

    # ── Paso 3: cuerpo dinámico según servicios contratados ────────────────
    # IMPORTANTE: el depósito legal se infiere ahora del sello editorial,
    # no de precio_legal (que pasó a representar Promoción y marketing).
    cantidad   = d['cantidad']

    deposito_legal = d.get('deposito_legal')
    if deposito_legal is None:
        deposito_legal = 4 if d.get('sello_editorial') else 0
    deposito_legal = int(deposito_legal or 0)
    tiene_dl   = deposito_legal > 0

    vl_c       = int(d.get('venta_libreria_cantidad', 0) or 0)
    va_c       = int(d.get('venta_amazon_cantidad', 0) or 0)
    tiene_lib  = vl_c > 0
    tiene_amz  = va_c > 0

    bdc_uds = deposito_legal if tiene_dl else 0
    lib_uds = vl_c if tiene_lib else 0
    amz_uds = va_c if tiene_amz else 0
    Y       = cantidad - bdc_uds - lib_uds - amz_uds

    base = (
        'Revisas el ejemplar físico y lo validas como correcto o nos indicas '
        'qué corregir y el porqué. <b>Abonas el 70% restante</b> e imprimimos '
        f'los <b>{cantidad} ejemplares</b> de la tirada. '
    )

    items_reparto = []
    if tiene_dl:
        items_reparto.append(
            f'<b>{deposito_legal} se envían a la Biblioteca de Catalunya</b>'
        )
    if tiene_lib:
        items_reparto.append(f'<b>{lib_uds} a Librería Numancia</b>')
    if tiene_amz:
        items_reparto.append(f'<b>{amz_uds} a Amazon</b>')

    if items_reparto and Y >= 0:
        if len(items_reparto) == 1:
            reparto_str = items_reparto[0]
        elif len(items_reparto) == 2:
            reparto_str = f'{items_reparto[0]} y {items_reparto[1]}'
        else:
            reparto_str = (f'{items_reparto[0]}, {items_reparto[1]} '
                           f'y {items_reparto[2]}')

        preambulo = ('Una vez pagado, gestionamos el <b>ISBN oficial</b> '
                     'y el <b>Depósito Legal</b>: ' if tiene_dl
                     else 'Una vez pagado: ')
        bloque_reparto = (
            f'{preambulo}de los <b>{cantidad} ejemplares</b>, {reparto_str}. '
            f'<b>Recibes en casa los {Y} ejemplares restantes.</b> '
        )
    elif tiene_dl and Y < 0:
        bloque_reparto = ('Una vez pagado, gestionamos el <b>ISBN oficial</b> '
                          'y el <b>Depósito Legal</b>. ')
    else:
        bloque_reparto = ''

    cierre = 'Entrega en 10-15 días laborables en la dirección que indiques.'
    cuerpo_paso3 = base + bloque_reparto + cierre

    pasos = [
        ('1', f'Confirma tu decisión y abona el 30% — <b>{_fmt_eur(pago30)}</b>',
         f'Responde a este presupuesto por email a <b>{asesora["email"]}</b> '
         f'o llama a tu asesora <b>{asesora["nombre"]}</b> al '
         f'<b>93 580 81 32 ext. {asesora["ext"]}</b> '
         f'<font color="#666666">({asesora.get("horario","")})</font>. '
         'En <b>24-48 horas hábiles</b> te enviamos el contrato de servicios '
         'editoriales y el documento para el primer pago del 30%. Recibes la '
         'factura proforma de inmediato y la definitiva tras el cobro.'),
        ('2', 'Maquetación profesional y producción del ejemplar de muestra (galera)',
         'Cuando la maquetación esté lista, producimos un <b>ejemplar físico '
         'de muestra (galera)</b> impreso con las especificaciones reales del '
         'libro definitivo y te lo enviamos por mensajería para que lo revises '
         'con calma en tu domicilio.'),
        ('3', f'Validación de la galera, gestión legal e impresión de la tirada '
              f'— <b>{_fmt_eur(pago70)}</b> (70% restante)',
         cuerpo_paso3),
    ]

    for num, tit, txt in pasos:
        num_p = Paragraph(num,
            S('pn','Helvetica-Bold',18,22,BLANCO,TA_CENTER))
        num_box = Table([[num_p]], colWidths=[12*mm])
        num_box.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),NAVY),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ]))
        tit_p = Paragraph(
            f'<font name="Helvetica-Bold" size="9.5" color="#1F3D6B">{tit}</font>',
            S('ptt','Helvetica-Bold',9.5,13,NAVY))
        txt_p = Paragraph(txt,
            S('ptx','Helvetica',8.5,12,TEXT,spaceBefore=3))
        fila = Table([[num_box, [tit_p, txt_p]]],
                     colWidths=[14*mm, W_DOC - 14*mm])
        fila.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
            ('LEFTPADDING',(1,0),(1,0),8),
            ('LINEBELOW',(0,0),(-1,0),0.3,GREY_LINE),
        ]))
        items.append(KeepTogether([fila, Spacer(1, 6)]))
    return items


def _bloque_garantias():
    items = []
    items.append(Paragraph(
        '<font name="Helvetica-Bold" size="10" color="#1F3D6B">'
        'Garantía editorial Numancia</font>',
        S('gat','Helvetica-Bold',10,13,NAVY,spaceBefore=2,spaceAfter=6)))
    garantias = [
        ('Sin sorpresas',
         'Todo transparente. El precio solo varía si cambian las páginas '
         'a maquetar o la tirada acordada.'),
        ('Acompañamiento',
         'De la primera llamada al libro en tus manos. Tu asesora dedicada, '
         'disponible para cada consulta o duda del proceso editorial.'),
        ('Calidad garantizada',
         'Recibes un libro de muestra antes de la tirada completa para '
         'aprobarlo en tu domicilio.'),
        ('Propiedad protegida',
         'Los derechos de autor son el 100% de tu propiedad. ISBN y Depósito '
         'Legal gestionados por Editorial Numancia.'),
    ]
    WG = W_DOC / 4
    row = []
    for tit, txt in garantias:
        row.append([
            Paragraph(f'<font name="Helvetica-Bold" size="8.5" color="#1F3D6B">'
                      f'{tit}</font>',
                      S('gtt','Helvetica-Bold',8.5,11,NAVY,TA_CENTER)),
            Paragraph(txt,
                      S('gtx','Helvetica',7.5,10.5,TEXT,TA_CENTER,spaceBefore=3)),
        ])
    t = Table([row], colWidths=[WG]*4)
    t.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.4,GREY_BORD),
        ('INNERGRID',(0,0),(-1,-1),0.3,GREY_LINE),
        ('BACKGROUND',(0,0),(-1,-1),GREY_BG),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))
    items.append(t)
    return items


def _bloque_cta_asesora(asesora):
    WL = W_DOC * 0.60; WR = W_DOC * 0.38; GAP = W_DOC * 0.02

    cta_content = [
        Paragraph('<font name="Helvetica-Bold" size="11" color="#1F3D6B">'
                  '¿Aún tienes dudas? Agenda una llamada gratuita</font>',
            S('ct1','Helvetica-Bold',11,14,NAVY)),
        Spacer(1, 5),
        Paragraph(f'Tu asesora <b>{asesora["nombre"]}</b> está a tu disposición '
                  'para resolver cualquier duda sobre el presupuesto, el proceso '
                  'de publicación o los servicios incluidos. Sin compromiso.',
            S('ct2','Helvetica',8.5,12,TEXT)),
        Spacer(1, 8),
        Paragraph('<b>3 formas de contactar:</b>',
            S('ct3','Helvetica-Bold',8.5,11,TEXT)),
        Paragraph(f'1. Llama al <b>93 580 81 32 ext. {asesora["ext"]}</b> '
                  f'<font color="#666666">({asesora.get("horario","")})</font>',
            S('ct4','Helvetica',8.5,12,TEXT,spaceBefore=3)),
        Paragraph(f'2. Email: <b>{asesora["email"]}</b>',
            S('ct5','Helvetica',8.5,12,TEXT,spaceBefore=2)),
        Paragraph('3. Reserva tu hueco con el botón inferior:',
            S('ct6','Helvetica',8.5,12,TEXT,spaceBefore=2)),
        Spacer(1, 6),
        BotonEnlace(
            texto=f'AGENDAR LLAMADA CON {asesora["nombre"].upper()}',
            url=asesora.get('calendario_url', '#'),
            w=WL - 24*mm, h=9*mm,
            bg=NAVY, fg=BLANCO, fontsize=8),
    ]
    t_cta = Table([[cta_content]], colWidths=[WL])
    t_cta.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.4,GREY_BORD),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
        ('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))

    foto_path = asesora.get('foto', '')
    foto_existe = bool(foto_path) and os.path.isfile(foto_path)

    ase_inner = [
        Paragraph('<font name="Helvetica" size="7.5" color="#666666">'
                  'TU ASESORA</font>',
            S('tas','Helvetica',7.5,10,GREY_TXT,TA_CENTER)),
        Spacer(1, 8),
    ]
    if foto_existe:
        try:
            png_bytes = _aplicar_mascara_circular(foto_path, diametro_px=400)
            img_buf = io.BytesIO(png_bytes)
            img = Image(img_buf, width=32*mm, height=32*mm)
            inner_w = WR - 16
            img_wrap = Table([[img]], colWidths=[inner_w])
            img_wrap.setStyle(TableStyle([
                ('ALIGN',(0,0),(-1,-1),'CENTER'),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
                ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
            ]))
            ase_inner.append(img_wrap)
            print(f'[presupuesto] foto circular OK: {foto_path}', flush=True)
        except Exception as e:
            print(f'[presupuesto] error foto circular ({e}), fallback iniciales',
                  flush=True)
            ase_inner.append(Paragraph(
                f'<font color="#1F3D6B">{asesora["iniciales"]}</font>',
                S('ini','Helvetica-Bold',24,30,NAVY,TA_CENTER)))
    else:
        ase_inner.append(Paragraph(
            f'<font color="#1F3D6B">{asesora["iniciales"]}</font>',
            S('ini','Helvetica-Bold',24,30,NAVY,TA_CENTER)))

    ase_inner += [
        Spacer(1, 8),
        Paragraph(f'<font name="Helvetica-Bold" size="10" color="#222222">'
                  f'{asesora["nombre"]}</font>',
            S('an','Helvetica-Bold',10,13,TEXT,TA_CENTER)),
        Paragraph('<font name="Helvetica-Oblique" size="8" color="#666666">'
                  'Asesora editorial</font>',
            S('ar','Helvetica-Oblique',8,11,GREY_TXT,TA_CENTER,spaceBefore=2)),
        Paragraph(f'93 580 81 32 ext. {asesora["ext"]}',
            S('aex','Helvetica',8,11,TEXT,TA_CENTER,spaceBefore=3)),
        Paragraph(f'<font color="#666666">{asesora.get("horario","")}</font>',
            S('aho','Helvetica',7.5,10,GREY_TXT,TA_CENTER,spaceBefore=2)),
    ]
    t_ase = Table([[ase_inner]], colWidths=[WR])
    t_ase.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.4,GREY_BORD),
        ('BACKGROUND',(0,0),(-1,-1),GREY_BG),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))

    t_bottom = Table([[t_cta, Spacer(GAP, 1), t_ase]],
                     colWidths=[WL, GAP, WR])
    t_bottom.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))
    return t_bottom


def _bloque_amortizacion(d):
    """
    PVP del libro editable desde Lovable.
    - Campo principal: `pvp_libreria` (€, IVA 4% INCLUIDO) — se usa tal cual
    - Fallback: `pvp_libro` (€, IVA 4% incluido) para payloads antiguos
    - Sin caché: cada llamada recalcula los valores

    Depósito legal (sello editorial Numancia):
    Cuando el autor contrata el sello, 4 ejemplares se destinan al depósito
    legal de la Biblioteca de Catalunya y NO pueden venderse. El porcentaje
    de amortización se calcula sobre la tirada DISPONIBLE (cantidad − 4),
    no sobre la tirada total.

    El frontend nuevo envía deposito_legal, cantidad_disponible y
    libros_amortizar. Si no llegan (cliente antiguo), se recalculan aquí.
    """
    total_final = d['_total_final']
    cantidad    = d['cantidad']

    # ── Depósito legal + tirada disponible (con fallback de compatibilidad) ──
    deposito_legal = d.get('deposito_legal')
    if deposito_legal is None:
        deposito_legal = 4 if d.get('sello_editorial') else 0
    deposito_legal = int(deposito_legal or 0)

    cantidad_disponible = d.get('cantidad_disponible')
    if cantidad_disponible is None:
        cantidad_disponible = max(0, cantidad - deposito_legal)
    cantidad_disponible = int(cantidad_disponible or 0)

    pvp_autor = d.get('pvp_libreria')
    if pvp_autor is None:
        pvp_autor = d.get('pvp_libro', 20.70)
    pvp_autor = round(float(pvp_autor or 20.70), 2)

    # libros_amortizar viene del frontend; fallback al cálculo local
    libros = d.get('libros_amortizar')
    if libros is None or int(libros or 0) <= 0:
        libros = math.ceil(total_final / pvp_autor) if pvp_autor else 0
    libros = int(libros or 0)

    # Denominador del % de amortización:
    #  - Con sello editorial: cantidad_disponible (excluye los 4 del depósito)
    #  - Sin sello editorial: cantidad total (comportamiento histórico)
    denominador = cantidad_disponible if deposito_legal > 0 else cantidad
    libros      = min(libros, max(denominador, libros))
    pct         = min(100, (libros / denominador) * 100) if denominador else 0
    restantes   = max(0, denominador - libros)
    beneficio_si_vende_todo = round(restantes * pvp_autor, 2)

    items = []
    titulo = Paragraph(
        '<font name="Helvetica-Bold" size="12" color="#1F3D6B">'
        'Amortiza tu publicación en la Librería Numancia</font>',
        S('amt','Helvetica-Bold',12,15,NAVY,spaceBefore=4,spaceAfter=2))
    subtitulo = Paragraph(
        f'<font name="Helvetica-Oblique" size="8.5" color="#666666">'
        f'PVP {_fmt_eur(pvp_autor)} (IVA 4% incluido)</font>',
        S('ams','Helvetica-Oblique',8.5,12,GREY_TXT,spaceAfter=8))

    # Texto interno del hero adaptado según haya o no depósito legal
    if deposito_legal > 0:
        hero_linea_inferior = (f'de tu tirada disponible de {cantidad_disponible} '
                               f'({pct:.0f}% de la edición)')
    else:
        hero_linea_inferior = (f'de los {cantidad} ejemplares de tu tirada '
                               f'({pct:.0f}% de la edición)')

    hero_izq = [
        Paragraph('<font name="Helvetica-Bold" size="8" color="#FFFFFF">'
                  'VENDIENDO SOLO</font>',
            S('h1','Helvetica-Bold',8,11,BLANCO)),
        Paragraph(f'<font name="Helvetica-Bold" size="48" color="#FFFFFF">'
                  f'{libros}</font>',
            S('h2','Helvetica-Bold',48,52,BLANCO,spaceBefore=2)),
        Paragraph(f'<font name="Helvetica" size="8.5" color="#FFFFFF">'
                  f'{hero_linea_inferior}</font>',
            S('h3','Helvetica',8.5,11,BLANCO,spaceBefore=4)),
    ]
    hero_der = [
        Paragraph('<font name="Helvetica-Bold" size="9" color="#FFFFFF">'
                  'RECUPERAS EL 100% DE TU INVERSIÓN</font>',
            S('h4','Helvetica-Bold',9,12,BLANCO)),
        Spacer(1, 6),
        Paragraph(f'<font name="Helvetica" size="8.5" color="#FFFFFF">'
                  f'Inversión total: <b>{_fmt_eur(total_final)}</b></font>',
            S('h5','Helvetica',8.5,12,BLANCO,spaceBefore=2)),
        Paragraph(f'<font name="Helvetica" size="8.5" color="#FFFFFF">'
                  f'PVP autor por libro: <b>{_fmt_eur(pvp_autor)}</b></font>',
            S('h6','Helvetica',8.5,12,BLANCO,spaceBefore=2)),
        Paragraph(f'<font name="Helvetica-Bold" size="9" color="#FFFFFF">'
                  f'{libros} × {_fmt_eur(pvp_autor)} = '
                  f'<u>{_fmt_eur(libros * pvp_autor)}</u></font>',
            S('h7','Helvetica-Bold',9,12,BLANCO,spaceBefore=4)),
    ]
    hero = Table([[hero_izq, hero_der]],
                 colWidths=[W_DOC*0.42, W_DOC*0.58])
    hero.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),NAVY),
        ('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),14),
        ('TOPPADDING',(0,0),(-1,-1),14),('BOTTOMPADDING',(0,0),(-1,-1),14),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEAFTER',(0,0),(0,-1),0.4, colors.HexColor('#3D5680')),
    ]))

    # Frase informativa explícita debajo del hero (solo si hay depósito legal)
    bloque_hero = [titulo, subtitulo, hero]
    if deposito_legal > 0:
        frase_deposito = Paragraph(
            f'Vendiendo solo <b>{libros}</b> ejemplares de tu tirada disponible '
            f'de <b>{cantidad_disponible}</b> (tirada {cantidad} − '
            f'{deposito_legal} depósito legal Biblioteca de Catalunya) '
            f'(<b>{pct:.0f}%</b>) recuperas toda tu inversión.',
            S('dl','Helvetica',8.5,12,TEXT,TA_LEFT,
              spaceBefore=8, spaceAfter=2,
              leftIndent=4, rightIndent=4))
        bloque_hero.append(frase_deposito)

    # Nota destacada — SIEMPRE presente (lleve o no sello editorial).
    # Usa &#160; (nbsp) entre "100" y "%" para mantenerlos juntos en la línea.
    nota_ganancias = Paragraph(
        'El <b>100&#160;%</b> de las ganancias de las ventas en la '
        '<b>Librería Numancia</b> son para el autor.',
        S('nlg','Helvetica',8.5,12,TEXT,TA_LEFT,
          spaceBefore=4, spaceAfter=2,
          leftIndent=4, rightIndent=4))
    bloque_hero.append(nota_ganancias)

    items.append(KeepTogether(bloque_hero))

    if restantes > 0:
        if deposito_legal > 0:
            txt_bonus = (
                f'A partir del ejemplar <b>{libros + 1}</b>, todo lo que vendas '
                f'es <b>beneficio neto para ti</b>. Si vendes los '
                f'<b>{cantidad_disponible}</b> ejemplares disponibles ganarás '
                f'hasta <b>{_fmt_eur(beneficio_si_vende_todo)}</b> adicionales.'
            )
        else:
            txt_bonus = (
                f'A partir del ejemplar <b>{libros + 1}</b>, todo lo que vendas '
                f'es <b>beneficio neto para ti</b>. Si vendes los '
                f'<b>{cantidad}</b> ejemplares de la tirada ganarás hasta '
                f'<b>{_fmt_eur(beneficio_si_vende_todo)}</b> adicionales.'
            )
        bonus = Paragraph(txt_bonus,
            S('bn','Helvetica',8.5,12,TEXT,TA_LEFT,
              spaceBefore=6, spaceAfter=2,
              leftIndent=4, rightIndent=4))
        items.append(bonus)

    return items


def _bloque_recompra(d):
    """
    Bloque "Si necesitas más ejemplares" — opciones de reimpresión.
    La sección SIEMPRE aparece (siempre se ofrece reimpresión al autor).
    """
    meses = d.get('reimpresion_meses', 12) or 12

    dto_pct = d.get('reimpresion_descuento_pct')
    if dto_pct is None:
        dto_pct = d.get('recompra_dto_pct', 15)
    dto_pct = float(dto_pct or 0)

    precio_base = float(d.get('precio_unitario', 0) or 0)

    lista_cants_alt = (d.get('reimpresion_cantidades')
                       or d.get('recompra_uds')
                       or [50, 100])
    precio_unitario_alt = d.get('reimpresion_precio_unitario')

    DEFAULT_CANTS = [50, 100]

    def _resolver_fila(idx, cant_key, precio_key):
        cant = d.get(cant_key)
        if cant is None or cant == '' or int(cant or 0) <= 0:
            if idx < len(lista_cants_alt) and int(lista_cants_alt[idx] or 0) > 0:
                cant = lista_cants_alt[idx]
            else:
                cant = DEFAULT_CANTS[idx] if idx < len(DEFAULT_CANTS) else 50
        cant = int(cant)

        precio = d.get(precio_key)
        if precio is None or precio == '' or float(precio or 0) <= 0:
            if precio_unitario_alt and float(precio_unitario_alt or 0) > 0:
                precio = float(precio_unitario_alt)
            elif precio_base > 0:
                precio = round(precio_base * (1 - dto_pct / 100), 2)
            else:
                precio = 0
        precio = float(precio)
        return cant, precio

    cant1, precio1 = _resolver_fila(0, 'reimpresion_cantidad_1', 'reimpresion_precio_1')
    cant2, precio2 = _resolver_fila(1, 'reimpresion_cantidad_2', 'reimpresion_precio_2')

    items = []
    items.append(Spacer(1, 8))

    titulo = Paragraph(
        '<font name="Helvetica-Bold" size="11" color="#1F3D6B">'
        'Si necesitas más ejemplares</font>',
        S('rct','Helvetica-Bold',11,14,NAVY,spaceBefore=2,spaceAfter=6))

    intro = Paragraph(
        f'Durante los <b>{meses} meses</b> posteriores a la aceptación de esta '
        f'propuesta puedes solicitar reimpresiones adicionales al precio '
        f'unitario de impresión (sin maquetación ni servicios), con un '
        f'<b>descuento del {int(dto_pct) if dto_pct == int(dto_pct) else dto_pct}%</b>.',
        S('rci','Helvetica',9,12.5,TEXT,TA_JUSTIFY,spaceAfter=6))

    dto_label = f'{int(dto_pct)}' if dto_pct == int(dto_pct) else f'{dto_pct}'
    filas = [[
        Paragraph('<font name="Helvetica-Bold" size="9" color="#FFFFFF">Cantidad</font>',
            S('hru','Helvetica-Bold',9,11,BLANCO,TA_CENTER)),
        Paragraph('<font name="Helvetica-Bold" size="9" color="#FFFFFF">Precio impresión</font>',
            S('hrp','Helvetica-Bold',9,11,BLANCO,TA_CENTER)),
        Paragraph(f'<font name="Helvetica-Bold" size="9" color="#FFFFFF">Precio con descuento ({dto_label}%)</font>',
            S('hri','Helvetica-Bold',9,11,BLANCO,TA_CENTER)),
        Paragraph('<font name="Helvetica-Bold" size="9" color="#FFFFFF">Precio por ejemplar</font>',
            S('hrue','Helvetica-Bold',9,11,BLANCO,TA_CENTER)),
    ]]
    for cant, precio in [(cant1, precio1), (cant2, precio2)]:
        importe_bruto = round(precio_base * cant, 2)
        importe_dto   = round(precio * cant, 2)
        filas.append([
            Paragraph(f'<b>{cant} ejemplares</b>',
                S('rcu','Helvetica',10,13,TEXT,TA_CENTER)),
            Paragraph(f'<font color="#555555"><strike><b>{_fmt_eur(importe_bruto)}</b></strike></font>',
                S('rcb','Helvetica-Bold',10,13,colors.HexColor('#555555'),TA_CENTER)),
            Paragraph(f'<font color="#1F3D6B"><b>{_fmt_eur(importe_dto)}</b></font>',
                S('rcd','Helvetica-Bold',10.5,13,NAVY,TA_CENTER)),
            Paragraph(f'<font color="#1F3D6B"><b>{_fmt_eur(precio)}</b></font>',
                S('rce','Helvetica-Bold',10,13,NAVY,TA_CENTER)),
        ])

    W1 = W_DOC * 0.20; W2 = W_DOC * 0.26; W3 = W_DOC * 0.30; W4 = W_DOC * 0.24
    tabla = Table(filas, colWidths=[W1, W2, W3, W4])
    tabla.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),
        ('TOPPADDING',(0,0),(-1,0),7),('BOTTOMPADDING',(0,0),(-1,0),7),
        ('TOPPADDING',(0,1),(-1,-1),9),('BOTTOMPADDING',(0,1),(-1,-1),9),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BOX',(0,0),(-1,-1),0.4,GREY_BORD),
        ('LINEBELOW',(0,0),(-1,0),0.4,GREY_BORD),
        ('LINEBELOW',(0,1),(-1,-2),0.3,GREY_LINE),
    ]))

    nota = Paragraph(
        '<font name="Helvetica-Oblique" size="8" color="#666666">'
        'Importes calculados sobre el precio unitario de impresión '
        '(sin incluir maquetación ni servicios editoriales). IVA 4% incluido.</font>',
        S('rcn','Helvetica-Oblique',8,11,GREY_TXT,TA_LEFT,spaceBefore=4))

    items.append(KeepTogether([titulo, intro, tabla, nota]))
    return items


def _bloque_anotaciones(d):
    """Sección opcional al final del documento."""
    texto = (d.get('anotaciones') or d.get('notas_adicionales') or '').strip()
    if not texto:
        return []
    items = []
    items.append(Spacer(1, 8))
    titulo = Paragraph(
        '<font name="Helvetica-Bold" size="11" color="#1F3D6B">'
        'Anotaciones</font>',
        S('nat','Helvetica-Bold',11,14,NAVY,spaceBefore=2,spaceAfter=6))
    txt_esc = texto.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    cuerpo = Paragraph(txt_esc.replace('\n','<br/>'),
        S('nab','Helvetica',9,12.5,TEXT,TA_JUSTIFY))
    items.append(KeepTogether([titulo, cuerpo]))
    return items


# ── Páginas ──────────────────────────────────────────────────────────────────
def _pagina1(d, asesora):
    story = []
    story += _cabecera(asesora, d['num_presupuesto'], d['fecha'], con_logo=True)
    story.append(_bloque_cliente_asesora(d, asesora))
    story.append(Spacer(1, 12))
    story.append(_headline_precio(d))
    story.append(Spacer(1, 6))
    story.append(_tabla_producto(d))
    story.append(Spacer(1, 14))
    bloque_cierre_p1 = _bloque_resumen(d) + [
        Spacer(1, 8),
        Paragraph(
            '<font name="Helvetica-Oblique" size="8.5" color="#666666">'
            'Este presupuesto tiene una validez de 15 días.</font>',
            S('val','Helvetica-Oblique',8.5,12,GREY_TXT,TA_LEFT)),
    ]
    story.append(KeepTogether(bloque_cierre_p1))
    return story


def _pagina2(d, asesora):
    story = []
    story += _cabecera(asesora, d['num_presupuesto'], d['fecha'], con_logo=True)
    story.extend(_bloque_amortizacion(d))
    story.extend(_bloque_recompra(d))
    return story


def _pagina3(d, asesora):
    story = []
    story += _cabecera(asesora, d['num_presupuesto'], d['fecha'], con_logo=True)
    story.extend(_bloque_pasos(d, asesora))
    story.append(Spacer(1, 8))
    story.extend(_bloque_garantias())
    story.extend(_bloque_anotaciones(d))
    story.append(Spacer(1, 14))
    story.append(_bloque_cta_asesora(asesora))
    return story


# ── Función principal ────────────────────────────────────────────────────────
def generar_presupuesto(d):
    asesora = _resolver_asesora(d.get('asesora', 'laura'))

    # ── Log de diagnóstico: lo que llega del frontend ────────────────────────
    # Útil para depurar si Lovable manda campos con nombres inesperados o
    # valores por defecto incorrectos. Se ve en los logs de Railway.
    print(
        f'[presupuesto] payload recibido: '
        f"asesora={d.get('asesora')!r} "
        f"cliente={d.get('cliente')!r} "
        f"formato={_get_formato(d)!r} "
        f"raw_formato={d.get('formato')!r} "
        f"cantidad={d.get('cantidad')} "
        f"precio_unitario={d.get('precio_unitario')} "
        f"precio_maquetacion={d.get('precio_maquetacion')} "
        f"precio_legal={d.get('precio_legal')} "
        f"precio_correccion={d.get('precio_correccion')} "
        f"sello_editorial={d.get('sello_editorial')} "
        f"deposito_legal={d.get('deposito_legal')} "
        f"pvp_libreria={d.get('pvp_libreria')} "
        f"venta_libreria_cantidad={d.get('venta_libreria_cantidad')} "
        f"venta_amazon_cantidad={d.get('venta_amazon_cantidad')}",
        flush=True)

    t = _calcular_totales(d)
    d['_total_final'] = t['total_final']

    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4,
        leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM)
    frame = Frame(LM, BM, W_DOC, AH - TM - BM,
                  leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id='main', frames=[frame])])

    story = _pagina1(d, asesora)
    story.append(PageBreak())
    story += _pagina2(d, asesora)
    story.append(PageBreak())
    story += _pagina3(d, asesora)

    canv = _hacer_canvas(d['num_presupuesto'], d['cliente'])
    doc.build(story, canvasmaker=canv)
    return buf.getvalue()


if __name__ == '__main__':
    datos = {
        'num_presupuesto':    '10370',
        'fecha':              '13/05/2026',
        'asesora':            'laura',
        'cliente':            'Manuel Muñoz',
        'obra':               'Buscando la Inteligencia',
        'genero':             'Ensayo divulgativo',
        'paginas':            215,
        'formato':            'A5',
        'precio_unitario':    5.20,
        'cantidad':           150,
        'descuento_pct':      0,
        'precio_maquetacion': 160.00,
        'precio_maquetacion_tarifa': 322.39,
        'aplicar_descuento_maquetacion': True,
        'precio_legal':       120.00,
        'precio_correccion':  220.00,
        'venta_libreria_precio':   50.00,
        'venta_libreria_cantidad': 10,
        'venta_amazon_precio':     80.00,
        'venta_amazon_cantidad':   10,
        'papel':              'Papel novela 80 gr',
        'cubierta':           '300 gr · Folding',
        'laminado':           'mate',
        'encuadernacion':     'fresada',
        'lomo':               '12 mm',
        'color_interior':     'B/N',
        'servicios_maquetacion': [
            'Diseño de portada personalizada',
            'Maquetación interior profesional',
        ],
        'servicios_legales': [
            'Gestión del Sello Editorial Numancia',
            'ISBN oficial de Editorial Numancia',
        ],
        'recompra_uds':       [50, 100],
        'recompra_dto_pct':   15,
        'pvp_libreria':       20.70,
        'anotaciones':        '',
    }
    pdf_bytes = generar_presupuesto(datos)
    out = '/mnt/user-data/outputs/presupuesto_test.pdf'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'wb') as f:
        f.write(pdf_bytes)
    print(f'PDF generado: {out} ({len(pdf_bytes)//1024} KB)')
