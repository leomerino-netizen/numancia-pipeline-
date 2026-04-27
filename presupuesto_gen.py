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
FOTOS_DIR = os.path.join(_HERE, 'fotos')

ASESORAS = {
    'laura': {
        'nombre':        'Laura Vega Ugarte',
        'iniciales':     'LV',
        'ext':           '282',
        'email':         'laura.vega@editorialnumancia.com',
        'foto':          os.path.join(FOTOS_DIR, 'laura.jpg'),
        'calendario':    'AGENDAR LLAMADA CON LAURA VEGA UGARTE',
        'calendario_url':'https://printcolorweb.zohobookings.eu/#/laura',
    },
    'debora': {
        'nombre':        'Débora Tómas',
        'iniciales':     'DT',
        'ext':           '283',
        'email':         'debora.tomas@editorialnumancia.com',
        'foto':          os.path.join(FOTOS_DIR, 'debora.jpg'),
        'calendario':    'AGENDAR LLAMADA CON DÉBORA TÓMAS',
        'calendario_url':'https://printcolorweb.zohobookings.eu/#/debora',
    },
    'juan': {
        'nombre':        'Juan Muñoz',
        'iniciales':     'JM',
        'ext':           '284',
        'email':         'juan.munoz@editorialnumancia.com',
        'foto':          os.path.join(FOTOS_DIR, 'juan.jpg'),
        'calendario':    'AGENDAR LLAMADA CON JUAN MUÑOZ',
        'calendario_url':'https://printcolorweb.zohobookings.eu/#/juan',
    },
    'nancy': {
        'nombre':        'Nancy',
        'iniciales':     'NA',
        'ext':           '285',
        'email':         'nancy@editorialnumancia.com',
        'foto':          os.path.join(FOTOS_DIR, 'nancy.jpg'),
        'calendario':    'AGENDAR LLAMADA CON NANCY',
        'calendario_url':'https://printcolorweb.zohobookings.eu/#/nancy',
    },
}

def _resolver_asesora(key: str) -> dict:
    """Acepta nombre completo o clave corta."""
    k = key.lower().strip()
    for slug, datos in ASESORAS.items():
        if slug in k or datos['nombre'].lower() in k:
            return datos
    return list(ASESORAS.values())[0]


# ── Helpers de estilo ────────────────────────────────────────────────────────
def S(name, font='Helvetica', size=8, leading=11, color=NEGRO,
      align=TA_LEFT, **kw):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                          textColor=color, alignment=align, **kw)


def _sec(txt, color=AZUL, w=None):
    cw = w or W_DOC
    t = Table([[Paragraph(
        f'<font name="Helvetica-Bold" size="7.5" color="white">{txt}</font>',
        S('sh', 'Helvetica-Bold', 7.5, 10, BLANCO))]],
        colWidths=[cw])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), color),
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
        ('TOPPADDING',   (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0), (-1,-1), 5),
    ]))
    return t


def _kv(rows, col1=42*mm, w=None):
    cw = w or W_DOC
    data = [[Paragraph(k, S('hb','Helvetica-Bold',7.5,11,AZUL)),
             Paragraph(v, S('hn','Helvetica',7.5,11,NEGRO))] for k, v in rows]
    t = Table(data, colWidths=[col1, cw - col1])
    t.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [AZUL_CL, BLANCO]),
        ('LEFTPADDING',  (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING',   (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.3, AZUL_LINEA),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return t


def _fmt_eur(v: float) -> str:
    return f'EUR {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


# ── Ruta del logo ────────────────────────────────────────────────────────────
LOGO_PATH = os.path.join(FOTOS_DIR, 'logo_numancia.png')

# ── Cabecera compartida (p1 y p2) ────────────────────────────────────────────
def _cabecera(asesora: dict) -> list:
    items = []

    # Logo a la izquierda — altura fija 12mm, ancho proporcional
    logo_h = 12 * mm
    logo_w = logo_h * (1621 / 337)   # ratio original
    logo_w = min(logo_w, W_DOC * 0.52)

    if os.path.isfile(LOGO_PATH):
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
        logo_cell = Paragraph(
            '<font name="Helvetica-Bold" size="13" color="#1565C0">Editorial Numancia</font>',
            S('lf','Helvetica-Bold',13,16,AZUL))

    # Dirección + datos de contacto — derecha
    contacto = Paragraph(
        '<font name="Helvetica" size="6.5" color="#555555">'
        'C/ Numancia 187, planta -1 · 08034 Barcelona<br/>'
        'Tel. 93 580 81 32 · info@editorialnumancia.com · www.editorialnumancia.com'
        '</font>',
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

    # Línea divisoria azul corporativa
    items.append(HRFlowable(width='100%', thickness=2.5,
                             color=AZUL, spaceAfter=0, spaceBefore=0))
    return items


# ── Bloque asesora (cabecera secundaria) ─────────────────────────────────────
def _bloque_asesora_header(num: str, fecha: str, asesora: dict) -> Table:
    left = Paragraph(
        f'<font name="Helvetica-Bold" size="8.5" color="#1565C0">PROPUESTA EDITORIAL</font>'
        f'  <font name="Helvetica-Bold" size="8" color="#1A1A1A">N.º {num}</font>'
        f'  <font name="Helvetica" size="7.5" color="#555555">· {fecha}</font><br/>'
        f'<font name="Helvetica" size="6.5" color="#888888">Validez: 15 días desde la emisión</font>',
        S('al','Helvetica',8,11))
    right = Paragraph(
        f'<font name="Helvetica-Bold" size="8" color="#1565C0">{asesora["nombre"]}</font><br/>'
        f'<font name="Helvetica" size="7">93 580 81 32 ext. {asesora["ext"]}</font>'
        f'  <font name="Helvetica" size="7" color="#555555">· {asesora["email"]}</font>',
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


# ── Pie de página ─────────────────────────────────────────────────────────────
def _pie() -> list:
    items = []
    items.append(HRFlowable(width='100%', thickness=2.5,
                             color=AZUL, spaceBefore=0, spaceAfter=4))
    t = Table([[
        Paragraph('<font name="Helvetica" size="6" color="#555555">'
                  'B83969014 FULLCOLOR PRINTCOLOR, S.L. · C/ Numancia 187, -1 · 08034 Barcelona · '
                  'info@editorialnumancia.com · www.editorialnumancia.com</font>',
                  S('p1','Helvetica',6,8,GRIS)),
        Paragraph('<font name="Helvetica" size="6" color="#888888">'
                  'Presupuesto válido 15 días · Precios con IVA al 4%</font>',
                  S('p2','Helvetica',6,8,GRIS,TA_RIGHT)),
    ]], colWidths=[W_DOC*0.65, W_DOC*0.35])
    t.setStyle(TableStyle([
        ('LEFTPADDING',  (0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',   (0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('VALIGN',       (0,0),(-1,-1),'MIDDLE'),
    ]))
    items.append(t)
    return items


# ── PÁGINA 1 ─────────────────────────────────────────────────────────────────
def _pagina1(d: dict, asesora: dict) -> list:
    story = []

    # Cabecera
    story += _cabecera(asesora)
    story.append(_bloque_asesora_header(d['num_presupuesto'], d['fecha'], asesora))
    story.append(Spacer(1, 6))

    # PARA / ASESORA EDITORIAL
    para_left = [
        Paragraph('<font name="Helvetica-Bold" size="6.5" color="#1565C0">PARA</font>',
                  S('pl','Helvetica',6.5,9,AZUL)),
        Paragraph(f'<font name="Helvetica-Bold" size="13">{d["cliente"]}</font>',
                  S('pn','Helvetica-Bold',13,16,NEGRO,spaceBefore=2)),
        Paragraph(f'<font name="Helvetica" size="7.5" color="#555555">'
                  f'Obra: <b>{d["obra"]}</b> | {d["genero"]} | {d["paginas"]} páginas | Formato {d["formato"]}</font>',
                  S('pd','Helvetica',7.5,11,GRIS,spaceBefore=3)),
    ]
    ase_right = [
        Paragraph('<font name="Helvetica-Bold" size="6.5" color="#1565C0">ASESORA EDITORIAL</font>',
                  S('ar2','Helvetica',6.5,9,AZUL,TA_RIGHT)),
        Paragraph(f'<font name="Helvetica-Bold" size="13" color="#1565C0">{asesora["nombre"]}</font>',
                  S('an','Helvetica-Bold',13,16,AZUL,TA_RIGHT,spaceBefore=2)),
        Paragraph(f'<font name="Helvetica" size="7" color="#555555">'
                  f'93 580 81 32 ext. {asesora["ext"]} | {asesora["email"]}</font>',
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
        Paragraph('<font name="Helvetica-Bold" size="7" color="white">PRECIO UNITARIO DE IMPRESIÓN</font>',
                  S('pt','Helvetica-Bold',7,10,BLANCO)),
        Spacer(1, 6),
        Paragraph(f'<font name="Helvetica" size="9.5" color="#BBDEFB"><strike>{_fmt_eur(pu)}</strike>  '
                  f'<b><font color="white" size="11">-{dto}%</font></b></font>',
                  S('pb','Helvetica',9.5,13,BLANCO,spaceBefore=2)),
        Paragraph(f'<font name="Helvetica-Bold" size="22" color="white">{_fmt_eur(pd_val).replace("EUR ", "")}</font><br/>'
                  f'<font name="Helvetica" size="7" color="#BBDEFB">EUR por ejemplar | IVA 4% incluido</font>',
                  S('pv','Helvetica-Bold',22,26,BLANCO,spaceBefore=3)),
        Spacer(1, 6),
        Paragraph(f'<font name="Helvetica-Bold" size="8" color="white">'
                  f'{cant} ejemplares = <strike>{_fmt_eur(pu*cant)}</strike>  '
                  f'<font color="#F9A825">{_fmt_eur(total_imp)}</font></font>',
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
        Paragraph('<font name="Helvetica-Bold" size="7" color="#1565C0">ESPECIFICACIONES DE IMPRESIÓN</font>',
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
        '<i><font name="Helvetica-Bold" size="8" color="#1565C0">Servicios de pago único incluidos en tu propuesta</font></i><br/>'
        '<font name="Helvetica" size="7" color="#555555">Se abonan una sola vez — independientemente de los ejemplares que imprimas en el futuro.</font>',
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
        content = [Paragraph(
            f'<font name="Helvetica-Bold" size="7.5" color="#1565C0">{titulo}</font>',
            S('sb','Helvetica-Bold',7.5,11,AZUL))]
        content.append(Spacer(1,4))
        for it in items:
            content.append(Paragraph(f'+ {it}', S('si','Helvetica',7,10,NEGRO,spaceBefore=1)))
        content.append(Spacer(1,8))
        content.append(Paragraph(
            f'Pago único:   <font name="Helvetica-Bold" size="8">{_fmt_eur(precio)}</font>',
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
    subtotal = round(total_imp + pm + pl, 2)
    descuento_imp = round(total_imp * dto / 100, 2)  # descuento solo sobre impresión
    total_dto = round(subtotal - descuento_imp, 2)

    resumen_data = [
        [Paragraph('Impresión y encuadernación '
                   f'({cant} ejemplares)', S('r1','Helvetica',7.5,11,NEGRO)),
         Paragraph(_fmt_eur(total_imp), S('r1r','Helvetica',7.5,11,NEGRO,TA_RIGHT))],
        [Paragraph('Maquetación y diseño editorial (pago único)',
                   S('r2','Helvetica',7.5,11,NEGRO)),
         Paragraph(_fmt_eur(pm), S('r2r','Helvetica',7.5,11,NEGRO,TA_RIGHT))],
        [Paragraph('Servicios legales y distribución (pago único)',
                   S('r3','Helvetica',7.5,11,NEGRO)),
         Paragraph(_fmt_eur(pl), S('r3r','Helvetica',7.5,11,NEGRO,TA_RIGHT))],
        [Paragraph('<b>Subtotal (IVA 4% incluido)</b>',
                   S('r4','Helvetica-Bold',7.5,11,NEGRO)),
         Paragraph(f'<b>{_fmt_eur(subtotal)}</b>',
                   S('r4r','Helvetica-Bold',7.5,11,NEGRO,TA_RIGHT))],
        [Paragraph(f'Descuento especial {dto}% — Imprime tus libros con descuento',
                   S('r5','Helvetica',7.5,11,NARANJA)),
         Paragraph(f'- {_fmt_eur(descuento_imp)}',
                   S('r5r','Helvetica',7.5,11,NARANJA,TA_RIGHT))],
        [Paragraph('<b>TOTAL CON DESCUENTO (IVA 4% incluido)</b>',
                   S('r6','Helvetica-Bold',8,12,NEGRO)),
         Paragraph(f'<b>{_fmt_eur(total_dto)}</b>',
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

    # Nota final p1
    story.append(Paragraph(
        '<i>Continúa en la página 2 para conocer <b>cómo aceptar el presupuesto</b>, '
        'los detalles del proceso y agendar una llamada gratuita con tu asesora.</i>',
        S('np','Times-Italic',7.5,11,GRIS,TA_CENTER,spaceBefore=4)))

    story.append(Spacer(1, 8))
    story.extend(_pie())
    return story


# ── PÁGINA 2 ─────────────────────────────────────────────────────────────────
def _pagina2(d: dict, asesora: dict) -> list:
    story = []
    story += _cabecera(asesora)
    story.append(_bloque_asesora_header(d['num_presupuesto'], d['fecha'], asesora))
    story.append(Spacer(1, 10))

    # Título
    story.append(Paragraph(
        '<font name="Times-BoldItalic" size="14" color="#1565C0">Cómo aceptar tu propuesta editorial</font>',
        S('tit','Times-BoldItalic',14,18,AZUL)))
    story.append(Paragraph(
        '<i>Un proceso transparente, sin sorpresas y con tu asesora acompañándote en cada paso.</i>',
        S('sub','Times-Italic',8,12,GRIS,spaceBefore=2,spaceAfter=8)))
    story.append(HRFlowable(width='100%', thickness=0.5, color=AZUL_LINEA, spaceAfter=8))

    pago30  = round(d['_total_final'] * 0.30, 2)
    pago70  = round(d['_total_final'] * 0.70, 2)

    pasos = [
        (
            '1',
            'Confirma tu decisión',
            f'Responde a este presupuesto por email a <b>{asesora["email"]}</b> o llama directamente '
            f'a tu asesora <b>{asesora["nombre"]}</b> al <b>93 580 81 32 ext. {asesora["ext"]}</b>.<br/>'
            'En las siguientes 24 horas te enviaremos el <b>contrato de servicios editoriales</b> con todos los detalles '
            'técnicos y jurídicos del proyecto, así como el documento para realizar el primer pago.',
            None
        ),
        (
            '2',
            f'Pago inicial del 30% — {_fmt_eur(pago30)}',
            'Una vez firmado el contrato, abonas el <b>30% del importe total</b> mediante transferencia bancaria. '
            'Recibes la factura proforma de inmediato y la factura definitiva tras el cobro.<br/>'
            '<b>En menos de 48 horas</b> ponemos en marcha tu proyecto: gestión del ISBN, asignación del Depósito Legal, '
            'inicio de la maquetación profesional y diseño de la portada.',
            None
        ),
        (
            '3',
            f'Aprueba la prueba física e imprime tu tirada — {_fmt_eur(pago70)} (70% restante)',
            'Cuando la maquetación está lista, te enviamos por mensajería un <b>ejemplar físico de muestra</b> impreso '
            'con las especificaciones reales del libro definitivo. Lo revisas con calma en tu domicilio.<br/>'
            'Una vez nos confirmas tu <b>aprobación final</b>, abonas el 70% restante e imprimimos la tirada completa '
            f'de {d["cantidad"]} ejemplares. Entrega en <b>10-15 días laborables</b> en la dirección que indiques.',
            None
        ),
    ]

    for num, tit, texto, _ in pasos:
        num_cell = Paragraph(
            f'<font name="Helvetica-Bold" size="22" color="white">{num}</font>',
            S(f'pn{num}','Helvetica-Bold',22,28,BLANCO,TA_CENTER))
        num_box = Table([[num_cell]], colWidths=[14*mm])
        num_box.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),AZUL),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
        ]))
        tit_p = Paragraph(f'<font name="Helvetica-Bold" size="9">{tit}</font>',
                          S(f'pt{num}','Helvetica-Bold',9,13,NEGRO))
        txt_p = Paragraph(f'<font name="Helvetica" size="7.5">{texto}</font>',
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
        '<i><font name="Helvetica-Bold" size="8" color="#1565C0">Garantía editorial Numancia</font></i>',
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
            Paragraph(f'<font name="Helvetica-Bold" size="7.5">{tit}</font>',
                      S(f'gt1','Helvetica-Bold',7.5,11,AZUL,TA_CENTER)),
            Paragraph(f'<font name="Helvetica" size="7">{txt}</font>',
                      S(f'gt2','Helvetica',7,10,NEGRO,TA_CENTER,spaceBefore=2)),
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
        Paragraph('<font name="Times-BoldItalic" size="11" color="#1565C0">'
                  '¿Aún tienes dudas? Agenda una llamada gratuita</font>',
                  S('cta1','Times-BoldItalic',11,15,AZUL)),
        Spacer(1, 6),
        Paragraph(f'Tu asesora <b>{asesora["nombre"]}</b> está a tu disposición para resolver cualquier duda '
                  f'sobre el presupuesto, el proceso de publicación o los servicios incluidos. Sin compromiso ninguno.',
                  S('cta2','Helvetica',7.5,12,NEGRO)),
        Spacer(1, 8),
        Paragraph('<b>3 formas de contactar:</b>',
                  S('cta3','Helvetica-Bold',7.5,11,NEGRO)),
        Paragraph(f'1. Llama al <b>93 580 81 32 ext. {asesora["ext"]}</b>',
                  S('cta4','Helvetica',7.5,11,NEGRO,spaceBefore=3)),
        Paragraph(f'2. Email: <b>{asesora["email"]}</b>',
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

    # Caja asesora con foto
    foto_path = asesora.get('foto', '')
    foto_existe = os.path.isfile(foto_path)

    ase_inner = [
        Paragraph('<font name="Helvetica-Bold" size="7" color="#1565C0">TU ASESORA</font>',
                  S('ta','Helvetica-Bold',7,10,AZUL,TA_CENTER)),
        Spacer(1, 8),
    ]

    if foto_existe:
        from PIL import Image as PILImage
        try:
            with PILImage.open(foto_path) as im:
                iw, ih = im.size
            ratio = iw / ih
            h_foto = 40*mm
            w_foto = h_foto * ratio
            w_max = WR - 16*mm
            if w_foto > w_max:
                w_foto = w_max
                h_foto = w_foto / ratio
            img = Image(foto_path, width=w_foto, height=h_foto)
            # Wrapper centrado: col = ancho disponible de la caja
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
        except Exception:
            ase_inner.append(Paragraph(
                f'<font name="Helvetica-Bold" size="24" color="#1565C0">{asesora["iniciales"]}</font>',
                S('ini','Helvetica-Bold',24,30,AZUL,TA_CENTER)))
    else:
        ase_inner.append(Paragraph(
            f'<font name="Helvetica-Bold" size="24" color="#1565C0">{asesora["iniciales"]}</font>',
            S('ini2','Helvetica-Bold',24,30,AZUL,TA_CENTER)))

    ase_inner += [
        Spacer(1, 8),
        Paragraph(f'<font name="Helvetica-Bold" size="9">{asesora["nombre"]}</font>',
                  S('an2','Helvetica-Bold',9,13,NEGRO,TA_CENTER)),
        Paragraph('<font name="Times-Italic" size="8" color="#555555">Asesora editorial</font>',
                  S('arol','Times-Italic',8,11,GRIS,TA_CENTER,spaceBefore=2)),
        Paragraph(f'<font name="Helvetica" size="7">93 580 81 32 ext. {asesora["ext"]}</font>',
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
    story.append(Spacer(1, 10))

    # Nota página 2 de 2
    story.append(Paragraph(
        f'<font name="Helvetica" size="6.5" color="#555555">Página 2 de 2</font>',
        S('pag','Helvetica',6.5,9,GRIS,TA_CENTER,spaceBefore=4)))
    story.append(Spacer(1, 4))
    story.extend(_pie())
    return story


# ── Función principal ─────────────────────────────────────────────────────────
def generar_presupuesto(d: dict) -> bytes:
    """
    Recibe dict con los datos del presupuesto y devuelve bytes del PDF.

    Campos requeridos:
      num_presupuesto, fecha, asesora (str: 'laura'/'debora'/'juan'/'nancy'),
      cliente, obra, genero, paginas (int), formato,
      precio_unitario (float), precio_descuento (float), cantidad (int),
      descuento_pct (int), precio_maquetacion (float), precio_legal (float)

    Opcionales:
      color_interior, papel, cubierta, laminado, encuadernacion, lomo,
      servicios_maquetacion (list), servicios_legales (list)
    """
    asesora = _resolver_asesora(d.get('asesora', 'laura'))

    # Calcular totales para p2
    pm = d.get('precio_maquetacion', 0)
    pl = d.get('precio_legal', 0)
    total_imp = round(d['precio_descuento'] * d['cantidad'], 2)
    dto = d.get('descuento_pct', 0)
    descuento_imp = round(total_imp * dto / 100, 2) if dto else 0
    # Si el descuento es sobre impresión únicamente (como en el PDF):
    subtotal = round(total_imp + pm + pl, 2)
    total_final = round(subtotal - descuento_imp, 2)
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
        'fecha':           '25 de abril de 2026',
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
    }
    pdf_bytes = generar_presupuesto(datos)
    out = '/mnt/user-data/outputs/presupuesto_test.pdf'
    with open(out, 'wb') as f:
        f.write(pdf_bytes)
    print(f'PDF generado: {out} ({len(pdf_bytes)//1024} KB)')
