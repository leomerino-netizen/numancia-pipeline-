"""
Genera la Propuesta Editorial A4 — 2 páginas con foto de asesora.
Estilo corporativo Editorial Numancia / Grupo Printcolorweb.com
"""
import io, os, math
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak, NextPageTemplate, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus.flowables import Flowable


# ── Botón clicable como Flowable ─────────────────────────────────────────────
class BotonEnlace(Flowable):
    """Rectángulo clicable con texto centrado y linkURL para PDF."""
    def __init__(self, texto, url, w, h=9*mm, bg=None, fg=None, fontsize=8):
        super().__init__()
        self.texto    = texto
        self.url      = url
        self.bw       = w
        self.bh       = h
        self.bg       = bg
        self.fg       = fg
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


# ── Paleta ───────────────────────────────────────────────────────────────────
AZUL      = colors.HexColor('#1565C0')
AZUL_MED  = colors.HexColor('#1976D2')
AZUL_CL   = colors.HexColor('#E3F2FD')
AZUL_LINEA= colors.HexColor('#90CAF9')
NARANJA   = colors.HexColor('#F57C00')
NARANJA_CL= colors.HexColor('#FFF3E0')
VERDE     = colors.HexColor('#2E7D32')
VERDE_CL  = colors.HexColor('#E8F5E9')
NEGRO     = colors.HexColor('#1A1A1A')
GRIS      = colors.HexColor('#555555')
GRIS_CL   = colors.HexColor('#F5F5F5')
BLANCO    = colors.white

AW = A4[0]; AH = A4[1]
LM = 18*mm; RM = 18*mm
TM = 14*mm; BM = 16*mm
W_DOC = AW - LM - RM

# ── Directorio de fotos ──────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))

def _find(candidates: list) -> str:
    """Devuelve la primera ruta que existe, o cadena vacía."""
    for c in candidates:
        p = os.path.join(_HERE, c)
        if os.path.isfile(p):
            return p
    return ''


# ── Normalizador de slug de asesora ──────────────────────────────────────────
def _normalizar_asesora_slug(asesora: str) -> str:
    """
    Normaliza la entrada (slug o nombre completo) al slug canónico.
    Lovable a veces manda 'laura' y otras 'Laura Vega Ugarte' — los aceptamos todos.
    """
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


LOGO_PATH = _find([
    'fotos/logo_numancia.png',
    'logo_numancia.png',
    'logotipo-editorial-numancia-apaisado-color-hexadecimal.png',
    'Fotos/logotipo-editorial-numancia-apaisado-color-hexadecimal.png',
])

# ── Catálogo de asesoras ─────────────────────────────────────────────────────
ASESORAS = {
    'laura': {
        'nombre':        'Laura Vega Ugarte',
        'iniciales':     'LV',
        'ext':           '282-283',
        'email':         'lauravega@editorialnumancia.com',
        'foto':          _find(['fotos/laura-circ.png', 'fotos/laura.jpg',
                                'laura.jpg',
                                'laura-asesora-editorial-editorial-numancia.jpg']),
        'calendario':    'AGENDAR LLAMADA CON LAURA VEGA UGARTE',
        'calendario_url':'https://printcolorweb.zohobookings.eu/#/laura',
    },
    'debora': {
        'nombre':        'Débora Tómas',
        'iniciales':     'DT',
        'ext':           '287',
        'email':         'deboratomas@editorialnumancia.com',
        'foto':          _find(['fotos/debora-circ.png', 'fotos/debora.jpg',
                                'debora.jpg',
                                'debora-asesora-editorial-numancia.jpg']),
        'calendario':    'AGENDAR LLAMADA CON DÉBORA TÓMAS',
        'calendario_url':'https://printcolorweb.zohobookings.eu/#/debora',
    },
    'juan': {
        'nombre':        'Juan Muñoz',
        'iniciales':     'JM',
        'ext':           '289',
        'email':         'juanmunoz@editorialnumancia.com',
        'foto':          _find(['fotos/juan-circ.png', 'fotos/juan.jpg',
                                'juan.jpg',
                                'juan-nunoz-maquetaror-editorial-numancia.jpg']),
        'calendario':    'AGENDAR LLAMADA CON JUAN MUÑOZ',
        'calendario_url':'https://printcolorweb.zohobookings.eu/#/juan',
    },
    'nancy': {
        'nombre':        'Nancy',
        'iniciales':     'NA',
        'ext':           '285',
        'email':         'info@editorialnumancia.com',
        'foto':          _find(['fotos/nancy-circ.png', 'fotos/nancy.jpg',
                                'nancy.jpg', 'Nancy.jpg']),
        'calendario':    'AGENDAR LLAMADA CON NANCY',
        'calendario_url':'https://printcolorweb.zohobookings.eu/#/nancy',
    },
}

def _resolver_asesora(key: str) -> dict:
    slug = _normalizar_asesora_slug(key)
    return ASESORAS.get(slug, ASESORAS['laura'])


# ── Helper: convertir cualquier foto a PNG circular ─────────────────────────
def _aplicar_mascara_circular(ruta_foto: str, diametro_px: int = 400) -> bytes:
    from PIL import Image as PILImage, ImageDraw
    with PILImage.open(ruta_foto) as im:
        if im.mode != 'RGBA':
            im = im.convert('RGBA')
        iw, ih = im.size
        ya_circular = (iw == ih and ruta_foto.lower().endswith('-circ.png'))
        if ya_circular:
            buf = io.BytesIO()
            im.save(buf, format='PNG')
            return buf.getvalue()
        if iw > ih:
            left = (iw - ih) // 2
            im = im.crop((left, 0, left + ih, ih))
        elif ih > iw:
            top = (ih - iw) // 2
            im = im.crop((0, top, iw, top + iw))
        im = im.resize((diametro_px, diametro_px), PILImage.LANCZOS)
        mascara = PILImage.new('L', (diametro_px, diametro_px), 0)
        draw = ImageDraw.Draw(mascara)
        draw.ellipse((0, 0, diametro_px, diametro_px), fill=255)
        resultado = PILImage.new('RGBA', (diametro_px, diametro_px), (255, 255, 255, 0))
        resultado.paste(im, (0, 0), mascara)
        buf = io.BytesIO()
        resultado.save(buf, format='PNG')
        return buf.getvalue()


# ── Helpers de estilo ────────────────────────────────────────────────────────
def S(name, font='Helvetica', size=8, leading=11, color=NEGRO,
      align=TA_LEFT, **kw):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                          textColor=color, alignment=align, **kw)


def _fmt_eur(v: float) -> str:
    return f'EUR {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


# ── Cabecera compartida (p1 y p2) ────────────────────────────────────────────
def _cabecera(asesora: dict, con_logo: bool = True) -> list:
    """
    Cabecera del documento.
    - con_logo=True  (p1): logo + datos de contacto. Línea decorativa azul abajo.
    - con_logo=False (p2+): solo "Editorial Numancia" en texto + datos de contacto.
      Mantiene la línea azul para coherencia visual.
    """
    items = []

    logo_h = 12 * mm
    logo_w = logo_h * (1621 / 337)
    logo_w = min(logo_w, W_DOC * 0.52)

    if con_logo and os.path.isfile(LOGO_PATH):
        logo_img = Image(LOGO_PATH, width=logo_w, height=logo_h)
        logo_cell = Table([[logo_img]], colWidths=[logo_w + 4*mm])
        logo_cell.setStyle(TableStyle([
            ('VALIGN',       (0,0),(-1,-1),'MIDDLE'),
            ('ALIGN',        (0,0),(-1,-1),'LEFT'),
            ('LEFTPADDING',  (0,0),(-1,-1),0),
            ('RIGHTPADDING', (0,0),(-1,-1),0),
            ('TOPPADDING',   (0,0),(-1,-1),0),
            ('BOTTOMPADDING',(0,0),(-1,-1),0),
        ]))
    else:
        # Fallback / página secundaria: texto en lugar de logo
        logo_cell = Paragraph(
            'Editorial Numancia',
            S('lf','Helvetica-Bold',13,16,AZUL))

    contacto = Paragraph(
        'C/ Numancia 187, planta -1 · 08034 Barcelona<br/>'
        'Tel. 93 580 81 32 · info@editorialnumancia.com · www.editorialnumancia.com',
        S('cc','Helvetica',6.5,9,GRIS,TA_RIGHT))

    cab = Table([[logo_cell, contacto]],
                colWidths=[logo_w + 6*mm, W_DOC - logo_w - 6*mm])
    cab.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1), BLANCO),
        ('VALIGN',       (0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',  (0,0),(-1,-1),0),
        ('RIGHTPADDING', (0,0),(-1,-1),0),
        ('TOPPADDING',   (0,0),(-1,-1),8),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    items.append(cab)

    items.append(HRFlowable(width='100%', thickness=2.5,
                             color=AZUL, spaceAfter=0, spaceBefore=0))
    return items


def _bloque_asesora_header(num: str, fecha: str, asesora: dict) -> Table:
    left = Paragraph(
        f'PROPUESTA EDITORIAL '
        f'N.º {num} · {fecha}<br/>'
        f'Validez: 15 días desde la emisión',
        S('al','Helvetica',8,11))
    right = Paragraph(
        f'{asesora["nombre"]}<br/>'
        f'93 580 81 32 ext. {asesora["ext"]} · {asesora["email"]}',
        S('ar','Helvetica',7,10,align=TA_RIGHT))
    t = Table([[left, right]], colWidths=[W_DOC*0.55, W_DOC*0.45])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1), AZUL_CL),
        ('LEFTPADDING',  (0,0),(-1,-1), 10),
        ('RIGHTPADDING', (0,0),(-1,-1), 10),
        ('TOPPADDING',   (0,0),(-1,-1), 6),
        ('BOTTOMPADDING',(0,0),(-1,-1), 6),
        ('VALIGN',       (0,0),(-1,-1),'MIDDLE'),
        ('LINEBELOW',    (0,0),(-1,-1), 0.5, AZUL_LINEA),
    ]))
    return t


def _pie() -> list:
    items = []
    items.append(HRFlowable(width='100%', thickness=2.5,
                             color=AZUL, spaceBefore=0, spaceAfter=4))
    t = Table([[
        Paragraph('B83969014 FULLCOLOR PRINTCOLOR, S.L. · C/ Numancia 187, -1 · 08034 Barcelona · '
                  'info@editorialnumancia.com · www.editorialnumancia.com',
                  S('p1','Helvetica',6,8,GRIS)),
        Paragraph('Presupuesto válido 15 días · Precios con IVA al 4%',
                  S('p2','Helvetica',6,8,GRIS,TA_RIGHT)),
    ]], colWidths=[W_DOC*0.65, W_DOC*0.35])
    t.setStyle(TableStyle([
        ('LEFTPADDING',  (0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',   (0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('VALIGN',       (0,0),(-1,-1),'MIDDLE'),
    ]))
    items.append(t)
    return items


# ── Bloque AMORTIZACIÓN (marketiniano) ───────────────────────────────────────
def _bloque_amortizacion(total_final: float, cantidad: int) -> list:
    PVP_BASE = 19.90
    IVA      = 0.04
    pvp_autor = round(PVP_BASE * (1 + IVA), 2)
    libros    = math.ceil(total_final / pvp_autor) if pvp_autor else 0
    libros    = min(libros, max(cantidad, libros))
    pct       = min(100, (libros / cantidad) * 100) if cantidad else 0
    restantes = max(0, cantidad - libros)
    beneficio_si_vende_todo = round(restantes * pvp_autor, 2)

    items = []
    titulo_amort = Paragraph(
        'Amortiza tu publicación en la Librería Numancia',
        S('amt','Times-BoldItalic',13,17,AZUL,spaceBefore=4,spaceAfter=4))
    subtitulo_amort = Paragraph(
        '100 % de las ventas para el autor · PVP 19,90 € (IVA 4 % incluido)',
        S('amsub','Times-Italic',8,12,GRIS,spaceBefore=0,spaceAfter=8))

    hero_left = [
        Paragraph('VENDIENDO SOLO',
                  S('amh1','Helvetica-Bold',7.5,11,BLANCO)),
        Paragraph(f'{libros}',
                  S('amh2','Helvetica-Bold',54,58,BLANCO,spaceBefore=2)),
        Paragraph(f'de los {cantidad} ejemplares de tu tirada',
                  S('amh3','Helvetica',8,11,BLANCO,spaceBefore=2)),
        Paragraph(f'({pct:.0f} % de la edición)',
                  S('amh4','Helvetica-Bold',9,12,BLANCO,spaceBefore=2)),
    ]
    hero_right = [
        Paragraph('RECUPERAS EL 100 %',
                  S('amr1','Helvetica-Bold',8,12,BLANCO)),
        Paragraph('DE TU INVERSIÓN',
                  S('amr2','Helvetica-Bold',13,16,BLANCO,spaceBefore=2)),
        Spacer(1, 8),
        Paragraph(f'Inversión total: <b>{_fmt_eur(total_final)}</b>',
                  S('amr3','Helvetica',8,12,BLANCO,spaceBefore=2)),
        Paragraph(f'PVP autor por libro: <b>{_fmt_eur(pvp_autor)}</b>',
                  S('amr4','Helvetica',8,12,BLANCO,spaceBefore=2)),
        Paragraph(f'{libros} × {_fmt_eur(pvp_autor)} = <b>{_fmt_eur(libros * pvp_autor)}</b>',
                  S('amr5','Helvetica-Bold',8.5,12,BLANCO,spaceBefore=2)),
    ]

    t_hero = Table([[hero_left, hero_right]],
                   colWidths=[W_DOC*0.42, W_DOC*0.58])
    t_hero.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1), AZUL),
        ('LINEAFTER',    (0,0),(0,-1), 0.6, AZUL_CL),
        ('LEFTPADDING',  (0,0),(-1,-1), 14),
        ('RIGHTPADDING', (0,0),(-1,-1), 14),
        ('TOPPADDING',   (0,0),(-1,-1), 12),
        ('BOTTOMPADDING',(0,0),(-1,-1), 12),
        ('VALIGN',       (0,0),(-1,-1),'MIDDLE'),
    ]))

    # KeepTogether: título + subtítulo + hero viajan SIEMPRE juntos.
    # Si no caben en lo que queda de página, saltan los tres juntos a la siguiente.
    items.append(KeepTogether([titulo_amort, subtitulo_amort, t_hero]))

    if restantes > 0:
        bonus = Table([[
            Paragraph(
                f'A partir del ejemplar <b>{libros + 1}</b>, todo lo que vendas es '
                f'<b>beneficio neto para ti</b>. Si vendes los <b>{cantidad}</b> ejemplares de la tirada '
                f'ganarás hasta <b>{_fmt_eur(beneficio_si_vende_todo)}</b> adicionales.',
                S('ambo','Helvetica',7.5,11,VERDE,TA_CENTER))
        ]], colWidths=[W_DOC])
        bonus.setStyle(TableStyle([
            ('BACKGROUND',   (0,0),(-1,-1), VERDE_CL),
            ('LINEABOVE',    (0,0),(-1,-1), 0.4, VERDE),
            ('LINEBELOW',    (0,0),(-1,-1), 0.4, VERDE),
            ('LEFTPADDING',  (0,0),(-1,-1), 10),
            ('RIGHTPADDING', (0,0),(-1,-1), 10),
            ('TOPPADDING',   (0,0),(-1,-1), 6),
            ('BOTTOMPADDING',(0,0),(-1,-1), 6),
        ]))
        items.append(bonus)

    return items


# ── Bloque RECOMPRA de ejemplares (nuevo · 13-05-2026) ──────────────────────
def _bloque_recompra(precio_unitario: float, cantidad: int) -> list:
    """
    Bloque informativo: durante 12 meses desde la aceptación de la propuesta,
    el autor puede pedir reimpresiones (>=25 ejemplares) al mismo precio unitario.
    El ejemplo usa los valores reales del presupuesto: una recompra-tipo de
    aproximadamente la mitad de la tirada inicial, redondeada a múltiplo de 25
    (mínimo 25), y muestra el cálculo total en euros.
    Estilo sobrio: título serif azul corporativo + cuerpo serif negro.
    Sin recuadros ni fondos. Pensado para ir tras el bloque de amortización.
    """
    items = []
    items.append(Spacer(1, 6))

    # Cantidad de ejemplo: ~50% de la tirada inicial, redondeado a múltiplo de 25,
    # con mínimo 25. Así el ejemplo siempre es realista respecto al presupuesto.
    ejemplo_uds = max(25, round(cantidad / 50) * 25)
    importe_ejemplo = round(ejemplo_uds * precio_unitario, 2)

    titulo = Paragraph(
        'Servicio de recompra de ejemplares',
        S('rc_tit', 'Times-Bold', 11, 15, AZUL, spaceBefore=2, spaceAfter=6))

    cuerpo = Paragraph(
        f'Durante los <b>12 meses</b> posteriores a la aceptación de esta propuesta, '
        f'el autor puede solicitar reimpresiones adicionales a partir de '
        f'<b>25 ejemplares</b> al mismo precio unitario de la tirada inicial.',
        S('rc_p1', 'Times-Roman', 9, 12, NEGRO, TA_JUSTIFY, spaceAfter=4))

    ejemplo = Paragraph(
        f'<i>Ejemplo aplicado a tu presupuesto:</i> si dentro de unos meses decides '
        f'reimprimir <b>{ejemplo_uds} ejemplares más</b>, pagarás '
        f'<b>{ejemplo_uds} × {_fmt_eur(precio_unitario)} = {_fmt_eur(importe_ejemplo)}</b>, '
        f'manteniendo el mismo precio unitario que tu tirada inicial de '
        f'<b>{cantidad} ejemplares</b>, sin recargo por tirada corta.',
        S('rc_p2', 'Times-Roman', 9, 12, NEGRO, TA_JUSTIFY, spaceAfter=4))

    ventaja = Paragraph(
        '<b>Ventaja:</b> no necesitas almacenar stock y conservas el precio reducido '
        'de la tirada grande durante todo el primer año.',
        S('rc_p3', 'Times-Roman', 9, 12, NEGRO, TA_JUSTIFY))

    # KeepTogether para que el bloque no se parta entre páginas
    items.append(KeepTogether([titulo, cuerpo, ejemplo, ventaja]))
    return items


# ── Bloque NOTAS ADICIONALES (opcional · 13-05-2026) ────────────────────────
def _bloque_notas_adicionales(texto: str) -> list:
    """
    Bloque opcional al final del presupuesto con notas libres de la asesora.
    Solo se renderiza si `texto` no está vacío. Respeta saltos de línea.
    """
    texto = (texto or '').strip()
    if not texto:
        return []

    items = []
    items.append(Spacer(1, 6))

    titulo = Paragraph(
        'Notas adicionales',
        S('na_tit', 'Times-Bold', 11, 15, AZUL, spaceBefore=2, spaceAfter=6))

    # Cada salto de línea doble (párrafo) o simple (línea) se respeta
    # convirtiendo \n a <br/> dentro de un único Paragraph.
    # Escapamos caracteres HTML peligrosos.
    txt_esc = (texto.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;'))
    txt_html = txt_esc.replace('\n', '<br/>')

    cuerpo = Paragraph(
        txt_html,
        S('na_body', 'Times-Roman', 9, 12, NEGRO, TA_JUSTIFY))

    # KeepTogether de título + cuerpo para que el título no quede huérfano.
    # Si el cuerpo es muy largo, ReportLab partirá el cuerpo conservando el título arriba.
    items.append(KeepTogether([titulo, cuerpo]))
    return items


# ── PÁGINA 1 ─────────────────────────────────────────────────────────────────
def _pagina1(d: dict, asesora: dict) -> list:
    story = []

    # Logo + datos de contacto en la cabecera de la PRIMERA página
    story += _cabecera(asesora, con_logo=True)
    story.append(_bloque_asesora_header(d['num_presupuesto'], d['fecha'], asesora))
    story.append(Spacer(1, 6))

    # PARA / ASESORA EDITORIAL
    para_left = [
        Paragraph('PARA',
                  S('pl','Helvetica',6.5,9,AZUL)),
        Paragraph(f'{d["cliente"]}',
                  S('pn','Helvetica-Bold',13,16,NEGRO,spaceBefore=2)),
        Paragraph(f'Obra: {d["obra"]} | {d["genero"]} | {d["paginas"]} páginas | Formato {d["formato"]}',
                  S('pd','Helvetica',7.5,11,GRIS,spaceBefore=3)),
    ]
    ase_right = [
        Paragraph('ASESORA EDITORIAL',
                  S('ar2','Helvetica',6.5,9,AZUL,TA_RIGHT)),
        Paragraph(f'{asesora["nombre"]}',
                  S('an','Helvetica-Bold',13,16,AZUL,TA_RIGHT,spaceBefore=2)),
        Paragraph(f'93 580 81 32 ext. {asesora["ext"]} | {asesora["email"]}',
                  S('ae','Helvetica',7,10,GRIS,TA_RIGHT,spaceBefore=3)),
    ]
    t_para = Table([[para_left, ase_right]], colWidths=[W_DOC*0.52, W_DOC*0.48])
    t_para.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(t_para)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width='100%', thickness=0.5, color=AZUL_LINEA, spaceAfter=8))

    # PRECIO + ESPECIFICACIONES
    pu = d['precio_unitario']
    pd_val = d['precio_descuento']
    cant = d['cantidad']
    dto = d['descuento_pct']
    total_imp = round(pd_val * cant, 2)

    precio_content = [
        Paragraph('PRECIO UNITARIO DE IMPRESIÓN',
                  S('pt','Helvetica-Bold',7,10,BLANCO)),
        Spacer(1, 6),
        Paragraph(f'{_fmt_eur(pu)}  -{dto}%',
                  S('pb','Helvetica',9.5,13,BLANCO,spaceBefore=2)),
        Paragraph(f'{_fmt_eur(pd_val).replace("EUR ", "")}<br/>'
                  f'EUR por ejemplar | IVA 4% incluido',
                  S('pv','Helvetica-Bold',22,26,BLANCO,spaceBefore=3)),
        Spacer(1, 6),
        Paragraph(f'{cant} ejemplares = {_fmt_eur(pu*cant)}  '
                  f'{_fmt_eur(total_imp)}',
                  S('pc','Helvetica-Bold',8,12,BLANCO)),
        Spacer(1, 4),
    ]

    specs = d.get('especificaciones', {})
    color_int = specs.get('color_interior', d.get('color_interior', 'B/N'))
    papel = specs.get('papel', d.get('papel', 'Papel novela 80 gr'))
    cubierta = specs.get('cubierta', d.get('cubierta', '300gr'))
    laminado = specs.get('laminado', d.get('laminado', 'brillante'))
    enc = specs.get('encuadernacion', d.get('encuadernacion', 'fresada'))
    lomo = specs.get('lomo', d.get('lomo', '10mm'))

    spec_content = [
        Paragraph('ESPECIFICACIONES DE IMPRESIÓN',
                  S('st','Helvetica-Bold',7,10,AZUL)),
        Spacer(1, 8),
        Paragraph(f'Formato {d["formato"]} (14,8 x 21 cm)  |  Interior en {color_int}  |  Cubierta a color',
                  S('sl1','Helvetica',8,12,NEGRO,spaceBefore=3)),
        Paragraph(f'{d["paginas"]} páginas  |  {papel}  |  Cubierta {cubierta}',
                  S('sl2','Helvetica',8,12,NEGRO,spaceBefore=3)),
        Paragraph(f'Laminado {laminado} en portada  |  Encuadernación {enc}',
                  S('sl3','Helvetica',8,12,NEGRO,spaceBefore=3)),
        Paragraph(f'Lomo {lomo}  |  Impresión digital profesional',
                  S('sl4','Helvetica',8,12,NEGRO,spaceBefore=3)),
    ]

    W1 = W_DOC * 0.40
    W2 = W_DOC * 0.58
    GAP = W_DOC * 0.02

    t_precio = Table([[precio_content]], colWidths=[W1])
    t_precio.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),AZUL),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))

    t_spec = Table([[spec_content]], colWidths=[W2])
    t_spec.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,AZUL_LINEA),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))

    t_row = Table([[t_precio, Spacer(GAP,1), t_spec]], colWidths=[W1, GAP, W2])
    t_row.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))
    story.append(t_row)
    story.append(Spacer(1, 10))

    # SERVICIOS DE PAGO ÚNICO
    story.append(Paragraph(
        'Servicios de pago único incluidos en tu propuesta<br/>'
        'Se abonan una sola vez — independientemente de los ejemplares que imprimas en el futuro.',
        S('sp','Helvetica',8,12,NEGRO,spaceBefore=2,spaceAfter=6)))

    pm = d.get('precio_maquetacion', 0)
    pl = d.get('precio_legal', 0)

    maq_items = d.get('servicios_maquetacion', [
        'Diseño de portada personalizada',
        'Maquetación interior profesional',
        'Formato ePub para venta digital',
        'Hasta 2 rondas de correcciones',
        'Archivos listos para imprenta',
    ])
    leg_items = d.get('servicios_legales', [
        'Gestión del Sello Editorial propio',
        'ISBN oficial — registro permanente',
        'Depósito Legal — Biblioteca Nacional',
        'Alta Librería Printcolorweb (10 uds)',
        'Alta y venta en Amazon.es (10 uds)',
    ])

    def _serv_box(titulo, items, precio, w):
        content = [Paragraph(titulo,
            S('sb','Helvetica-Bold',7.5,11,AZUL))]
        content.append(Spacer(1,4))
        for it in items:
            content.append(Paragraph(f'+ {it}', S('si','Helvetica',7,10,NEGRO,spaceBefore=1)))
        content.append(Spacer(1,8))
        content.append(Paragraph(
            f'Pago único:   {_fmt_eur(precio)}',
            S('sp2','Helvetica',7.5,11,NEGRO,TA_RIGHT)))
        t = Table([[content]], colWidths=[w])
        t.setStyle(TableStyle([
            ('BOX',(0,0),(-1,-1),0.5,AZUL_LINEA),
            ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
            ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
        ]))
        return t

    WS = (W_DOC - 6) / 2
    t_serv = Table([[
        _serv_box('MAQUETACIÓN Y DISEÑO EDITORIAL', maq_items, pm, WS),
        Spacer(6,1),
        _serv_box('SERVICIOS LEGALES Y DISTRIBUCIÓN', leg_items, pl, WS),
    ]], colWidths=[WS, 6, WS])
    t_serv.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))
    story.append(t_serv)
    story.append(Spacer(1, 10))

    # RESUMEN ECONÓMICO
    total_imp_full = round(pu * cant, 2)
    subtotal       = round(total_imp_full + pm + pl, 2)
    descuento_eur  = round(subtotal * dto / 100, 2)
    total_dto      = round(subtotal - descuento_eur, 2)

    resumen_data = [
        [Paragraph(f'Impresión y encuadernación ({cant} ejemplares)',
                   S('r1','Helvetica',7.5,11,NEGRO)),
         Paragraph(_fmt_eur(total_imp_full), S('r1r','Helvetica',7.5,11,NEGRO,TA_RIGHT))],
        [Paragraph('Maquetación y diseño editorial (pago único)',
                   S('r2','Helvetica',7.5,11,NEGRO)),
         Paragraph(_fmt_eur(pm), S('r2r','Helvetica',7.5,11,NEGRO,TA_RIGHT))],
        [Paragraph('Servicios legales y distribución (pago único)',
                   S('r3','Helvetica',7.5,11,NEGRO)),
         Paragraph(_fmt_eur(pl), S('r3r','Helvetica',7.5,11,NEGRO,TA_RIGHT))],
        [Paragraph('Subtotal (IVA 4% incluido)',
                   S('r4','Helvetica-Bold',7.5,11,NEGRO)),
         Paragraph(f'{_fmt_eur(subtotal)}',
                   S('r4r','Helvetica-Bold',7.5,11,NEGRO,TA_RIGHT))],
        [Paragraph(f'Descuento especial {dto}% — Imprime tus libros con descuento',
                   S('r5','Helvetica',7.5,11,NARANJA)),
         Paragraph(f'- {_fmt_eur(descuento_eur)}',
                   S('r5r','Helvetica',7.5,11,NARANJA,TA_RIGHT))],
        [Paragraph('TOTAL CON DESCUENTO (IVA 4% incluido)',
                   S('r6','Helvetica-Bold',8,12,NEGRO)),
         Paragraph(f'{_fmt_eur(total_dto)}',
                   S('r6r','Helvetica-Bold',10,13,NEGRO,TA_RIGHT))],
    ]
    t_res = Table(resumen_data, colWidths=[W_DOC*0.72, W_DOC*0.28])
    t_res.setStyle(TableStyle([
        ('ROWBACKGROUNDS',(0,0),(-1,2),[GRIS_CL, BLANCO, GRIS_CL]),
        ('BACKGROUND',(0,3),(-1,3),AZUL_CL),
        ('BACKGROUND',(0,4),(-1,4),NARANJA_CL),
        ('BACKGROUND',(0,5),(-1,5),AZUL_CL),
        ('LINEBELOW',(0,2),(-1,2),0.5,AZUL_LINEA),
        ('LINEBELOW',(0,4),(-1,4),0.5,AZUL_LINEA),
        ('LINEABOVE',(0,5),(-1,5),1.5,AZUL),
        ('LINEBELOW',(0,5),(-1,5),1.5,AZUL),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ALIGN',(1,0),(1,-1),'RIGHT'),
    ]))
    story.append(t_res)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        'Continúa en la página siguiente para conocer cómo aceptar el presupuesto, '
        'los detalles del proceso y agendar una llamada gratuita con tu asesora.',
        S('np','Times-Italic',7.5,11,GRIS,TA_CENTER,spaceBefore=4)))

    story.append(Spacer(1, 8))
    story.extend(_pie())
    return story


# ── PÁGINA 2 ─────────────────────────────────────────────────────────────────
def _pagina2(d: dict, asesora: dict) -> list:
    story = []
    # SIN LOGO en la página 2 (igual que el informe editorial)
    story += _cabecera(asesora, con_logo=False)
    story.append(_bloque_asesora_header(d['num_presupuesto'], d['fecha'], asesora))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        'Cómo aceptar tu propuesta editorial',
        S('tit','Times-BoldItalic',14,18,AZUL)))
    story.append(Paragraph(
        'Un proceso transparente, sin sorpresas y con tu asesora acompañándote en cada paso.',
        S('sub','Times-Italic',8,12,GRIS,spaceBefore=2,spaceAfter=8)))
    story.append(HRFlowable(width='100%', thickness=0.5, color=AZUL_LINEA, spaceAfter=8))

    pago30  = round(d['_total_final'] * 0.30, 2)
    pago70  = round(d['_total_final'] * 0.70, 2)

    pasos = [
        (
            '1',
            'Confirma tu decisión',
            f'Responde a este presupuesto por email a {asesora["email"]} o llama directamente '
            f'a tu asesora {asesora["nombre"]} al 93 580 81 32 ext. {asesora["ext"]}.<br/>'
            'En las siguientes 24 horas te enviaremos el contrato de servicios editoriales con todos los detalles '
            'técnicos y jurídicos del proyecto, así como el documento para realizar el primer pago.',
            None
        ),
        (
            '2',
            f'Pago inicial del 30% — {_fmt_eur(pago30)}',
            'Una vez firmado el contrato, abonas el 30% del importe total mediante transferencia bancaria. '
            'Recibes la factura proforma de inmediato y la factura definitiva tras el cobro.<br/>'
            'En menos de 48 horas ponemos en marcha tu proyecto: gestión del ISBN, asignación del Depósito Legal, '
            'inicio de la maquetación profesional y diseño de la portada.',
            None
        ),
        (
            '3',
            f'Aprueba la prueba física e imprime tu tirada — {_fmt_eur(pago70)} (70% restante)',
            'Cuando la maquetación está lista, te enviamos por mensajería un ejemplar físico de muestra impreso '
            'con las especificaciones reales del libro definitivo. Lo revisas con calma en tu domicilio.<br/>'
            'Una vez nos confirmas tu aprobación final, abonas el 70% restante e imprimimos la tirada completa '
            f'de {d["cantidad"]} ejemplares. Entrega en 10-15 días laborables en la dirección que indiques.',
            None
        ),
    ]

    for num, tit, texto, _ in pasos:
        num_cell = Paragraph(num,
            S(f'pn{num}','Helvetica-Bold',22,28,BLANCO,TA_CENTER))
        num_box = Table([[num_cell]], colWidths=[14*mm])
        num_box.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),AZUL),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
        ]))
        tit_p = Paragraph(tit,
                          S(f'pt{num}','Helvetica-Bold',9,13,NEGRO))
        txt_p = Paragraph(texto,
                          S(f'px{num}','Helvetica',7.5,11,NEGRO,spaceBefore=3))
        content_cell = [tit_p, txt_p]
        row = Table([[num_box, content_cell]], colWidths=[16*mm, W_DOC - 16*mm])
        row.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
            ('LEFTPADDING',(1,0),(1,0),8),
            ('LINEBELOW',(0,0),(-1,0),0.3,AZUL_LINEA),
        ]))
        story.append(row)
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 4))

    # GARANTÍAS
    story.append(Paragraph(
        'Garantía editorial Numancia',
        S('gt','Helvetica-Bold',8,12,AZUL,spaceBefore=4,spaceAfter=6)))

    garantias = [
        ('Sin sorpresas', 'Precio final. Sin costes ocultos.'),
        ('Acompañamiento', 'Tu asesora contigo en todo el proceso.'),
        ('Calidad garantizada', 'Si la prueba no cumple, la repetimos sin coste.'),
        ('Propiedad protegida', 'ISBN y Depósito Legal a tu nombre.'),
    ]
    WG = W_DOC / 4
    gar_row = [[]]
    for tit, txt in garantias:
        cell = [
            Paragraph(tit,
                      S('gt1','Helvetica-Bold',7.5,11,AZUL,TA_CENTER)),
            Paragraph(txt,
                      S('gt2','Helvetica',7,10,NEGRO,TA_CENTER,spaceBefore=2)),
        ]
        gar_row[0].append(cell)
    t_gar = Table(gar_row, colWidths=[WG]*4)
    t_gar.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,AZUL_LINEA),
        ('INNERGRID',(0,0),(-1,-1),0.3,AZUL_LINEA),
        ('BACKGROUND',(0,0),(-1,-1),AZUL_CL),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))
    story.append(t_gar)
    story.append(Spacer(1, 10))

    # CTA + FOTO ASESORA
    WL = W_DOC * 0.60
    WR = W_DOC * 0.38
    GAP = W_DOC * 0.02

    cta_content = [
        Paragraph('¿Aún tienes dudas? Agenda una llamada gratuita',
                  S('cta1','Times-BoldItalic',11,15,AZUL)),
        Spacer(1, 6),
        Paragraph(f'Tu asesora {asesora["nombre"]} está a tu disposición para resolver cualquier duda '
                  f'sobre el presupuesto, el proceso de publicación o los servicios incluidos. Sin compromiso ninguno.',
                  S('cta2','Helvetica',7.5,12,NEGRO)),
        Spacer(1, 8),
        Paragraph('3 formas de contactar:',
                  S('cta3','Helvetica-Bold',7.5,11,NEGRO)),
        Paragraph(f'1. Llama al 93 580 81 32 ext. {asesora["ext"]}',
                  S('cta4','Helvetica',7.5,11,NEGRO,spaceBefore=3)),
        Paragraph(f'2. Email: {asesora["email"]}',
                  S('cta5','Helvetica',7.5,11,NEGRO,spaceBefore=2)),
        Paragraph(f'3. Reserva tu hueco en el calendario de {asesora["nombre"].split()[0]} con el botón inferior:',
                  S('cta6','Helvetica',7.5,11,NEGRO,spaceBefore=2)),
        Spacer(1, 8),
    ]
    cta_content.append(BotonEnlace(
        texto=f'>> {asesora["calendario"]}',
        url=asesora.get('calendario_url', '#'),
        w=WL - 24*mm,
        h=10*mm,
        bg=NARANJA,
        fg=BLANCO,
        fontsize=8,
    ))

    t_cta = Table([[cta_content]], colWidths=[WL])
    t_cta.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.5,AZUL_LINEA),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
        ('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))

    foto_path = asesora.get('foto', '')
    foto_existe = bool(foto_path) and os.path.isfile(foto_path)

    ase_inner = [
        Paragraph('TU ASESORA',
                  S('ta','Helvetica-Bold',7,10,AZUL,TA_CENTER)),
        Spacer(1, 8),
    ]

    if foto_existe:
        try:
            png_bytes = _aplicar_mascara_circular(foto_path, diametro_px=400)
            img_buf = io.BytesIO(png_bytes)
            tam_foto = 32 * mm
            img = Image(img_buf, width=tam_foto, height=tam_foto)
            t_foto = Table([[img]], colWidths=[WR - 16*mm])
            t_foto.setStyle(TableStyle([
                ('ALIGN',        (0,0),(-1,-1),'CENTER'),
                ('VALIGN',       (0,0),(-1,-1),'MIDDLE'),
                ('LEFTPADDING',  (0,0),(-1,-1),0),
                ('RIGHTPADDING', (0,0),(-1,-1),0),
                ('TOPPADDING',   (0,0),(-1,-1),0),
                ('BOTTOMPADDING',(0,0),(-1,-1),0),
            ]))
            ase_inner.append(t_foto)
            print(f'[presupuesto] foto circular OK: {foto_path}', flush=True)
        except Exception as e:
            print(f'[presupuesto] error procesando foto circular ({e}), '
                  f'fallback a iniciales', flush=True)
            ase_inner.append(Paragraph(asesora["iniciales"],
                S('ini','Helvetica-Bold',24,30,AZUL,TA_CENTER)))
    else:
        print(f'[presupuesto] sin foto disponible para asesora, '
              f'usando iniciales {asesora["iniciales"]!r}', flush=True)
        ase_inner.append(Paragraph(asesora["iniciales"],
            S('ini2','Helvetica-Bold',24,30,AZUL,TA_CENTER)))

    ase_inner += [
        Spacer(1, 8),
        Paragraph(asesora["nombre"],
                  S('an2','Helvetica-Bold',9,13,NEGRO,TA_CENTER)),
        Paragraph('Asesora editorial',
                  S('arol','Times-Italic',8,11,GRIS,TA_CENTER,spaceBefore=2)),
        Paragraph(f'93 580 81 32 ext. {asesora["ext"]}',
                  S('aext','Helvetica',7,10,NEGRO,TA_CENTER,spaceBefore=4)),
    ]

    t_ase = Table([[ase_inner]], colWidths=[WR])
    t_ase.setStyle(TableStyle([
        ('BOX',          (0,0),(-1,-1),0.5,AZUL_LINEA),
        ('BACKGROUND',   (0,0),(-1,-1),AZUL_CL),
        ('ALIGN',        (0,0),(-1,-1),'CENTER'),
        ('LEFTPADDING',  (0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',   (0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ('VALIGN',       (0,0),(-1,-1),'TOP'),
    ]))

    t_bottom = Table([[t_cta, Spacer(GAP,1), t_ase]], colWidths=[WL, GAP, WR])
    t_bottom.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))
    story.append(t_bottom)
    story.append(Spacer(1, 12))

    # ── BLOQUE AMORTIZACIÓN MARKETINIANO ────────────────────────────────────
    story.extend(_bloque_amortizacion(d['_total_final'], d['cantidad']))
    story.append(Spacer(1, 8))

    # ── BLOQUE SERVICIO DE RECOMPRA (nuevo · 13-05-2026) ────────────────────
    story.extend(_bloque_recompra(d['precio_descuento'], d['cantidad']))

    # ── BLOQUE NOTAS ADICIONALES (opcional · 13-05-2026) ────────────────────
    # Solo se renderiza si llega texto en d['notas_adicionales'].
    story.extend(_bloque_notas_adicionales(d.get('notas_adicionales', '')))

    story.append(Spacer(1, 8))
    story.extend(_pie())
    return story


# ── Función principal ─────────────────────────────────────────────────────────
def generar_presupuesto(d: dict) -> bytes:
    asesora = _resolver_asesora(d.get('asesora', 'laura'))

    pm = d.get('precio_maquetacion', 0)
    pl = d.get('precio_legal', 0)
    total_imp = round(d['precio_descuento'] * d['cantidad'], 2)
    dto = d.get('descuento_pct', 0)
    total_imp_full = round(d['precio_unitario'] * d['cantidad'], 2)
    subtotal       = round(total_imp_full + pm + pl, 2)
    descuento_eur  = round(subtotal * dto / 100, 2) if dto else 0
    total_final    = round(subtotal - descuento_eur, 2)
    d['_total_final'] = total_final

    buf = io.BytesIO()

    doc = BaseDocTemplate(buf, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=TM, bottomMargin=BM)

    frame = Frame(LM, BM, AW-LM-RM, AH-TM-BM,
                  leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id='main', frames=[frame])])

    story = _pagina1(d, asesora)
    story.append(PageBreak())
    story += _pagina2(d, asesora)

    doc.build(story)
    return buf.getvalue()


# ── Demo ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    datos = {
        'num_presupuesto': '10212',
        'fecha':           '13 de mayo de 2026',
        'asesora':         'laura',
        'cliente':         'Sara Libro Test',
        'obra':            'Sara',
        'genero':          'Novela',
        'paginas':         200,
        'formato':         'A5',
        'precio_unitario':  4.52,
        'precio_descuento': 3.84,
        'cantidad':         100,
        'descuento_pct':    15,
        'precio_maquetacion': 322.39,
        'precio_legal':       114.40,
        'papel':      'Papel novela 80 gr',
        'cubierta':   '300gr',
        'laminado':   'brillante',
        'encuadernacion': 'fresada',
        'lomo':       '10mm',
        'color_interior': 'B/N',
        # Nuevo campo opcional: si está vacío, no se renderiza el bloque.
        'notas_adicionales': '',
    }
    pdf_bytes = generar_presupuesto(datos)
    out = '/mnt/user-data/outputs/presupuesto_test.pdf'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'wb') as f:
        f.write(pdf_bytes)
    print(f'PDF generado: {out} ({len(pdf_bytes)//1024} KB)')
