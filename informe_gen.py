"""
informe_gen.py — Informe de lectura y valoración profesional Editorial Numancia.
Diseño tipo Penguin Random House / Planeta: serif elegante, cabecera crema con logo color,
evaluación expandida y carta personal de la asesora al autor.

CAMBIO 15/05/2026 (Fix Parse error EJEMPLO DETECTADO):
  El replace ciego de «»  por <b></b> en los ejemplos del análisis
  ortotipográfico podía generar tags huérfanos cuando el LLM o un PDF
  convertido devolvían comillas desbalanceadas → ValueError de ReportLab.
  Fix:
    1) _resaltar_comillas_balanceadas() solo resalta pares completos
    2) _sanitizar_rl_html() colapsa tags duplicados como red final
    3) _safe_paragraph() reintenta sin tags si el parser falla
"""

import io, os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                  TableStyle, HRFlowable, Image, KeepTogether,
                                  PageBreak)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# Paleta editorial sobria
CREMA       = colors.HexColor('#F8F4EC')
NEGRO       = colors.HexColor('#1A1A1A')
GRIS_OSC    = colors.HexColor('#3A3A3A')
GRIS        = colors.HexColor('#666666')
GRIS_CL     = colors.HexColor('#B5B5B5')
GRIS_LINEA  = colors.HexColor('#D4CEC2')
DORADO      = colors.HexColor('#A88838')
DORADO_CL   = colors.HexColor('#E8DDB8')
ROJO_ED     = colors.HexColor('#7A1F1F')
VERDE_ED    = colors.HexColor('#1F4D2C')
BLANCO      = colors.white
GRIS_MEDIO  = colors.HexColor('#6B6B6B')

_HERE = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = next((p for p in [
    os.path.join(_HERE, 'fotos', 'logo_numancia.png'),
    os.path.join(_HERE, 'logo_numancia.png'),
    os.path.join(_HERE, 'logotipo-editorial-numancia-apaisado-color-hexadecimal.png'),
    os.path.join(_HERE, 'fotos', 'logo_numancia_bn.png'),
    os.path.join(_HERE, 'logo_numancia_bn.png'),
] if os.path.isfile(p)), None)

FAVICON_PATH = next((p for p in [
    os.path.join(_HERE, 'fotos', 'favicon_numancia.png'),
    os.path.join(_HERE, 'favicon_numancia.png'),
] if os.path.isfile(p)), None)

W_DOC = A4[0] - 36*mm

def S(name, font='Helvetica', size=9, leading=12, color=NEGRO, align=TA_LEFT, **kw):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                          textColor=color, alignment=align, **kw)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS DE SANEAMIENTO HTML PARA REPORTLAB (Fix Parse error EJEMPLO DETECTADO)
# ══════════════════════════════════════════════════════════════════════════════

def _resaltar_comillas_balanceadas(texto: str,
                                    apertura: str = '<font color="#7A1F1F"><b>',
                                    cierre: str = '</b></font>') -> str:
    """
    Convierte solo los pares COMPLETOS de comillas angulares «...» en HTML
    de resaltado para ReportLab. Los « o » huérfanos (sin pareja) se dejan
    como entidades HTML (&laquo; / &raquo;) para que el parser no se rompa.

    El texto de entrada debe venir ya escapado para HTML (sin '<' ni '>').
    """
    if not texto:
        return ''
    pattern = re.compile(r'«([^«»]*?)»')
    resaltado = pattern.sub(f'{apertura}\\1{cierre}', texto)
    resaltado = resaltado.replace('«', '&laquo;').replace('»', '&raquo;')
    return resaltado


def _sanitizar_rl_html(html: str) -> str:
    """
    Última red de seguridad: colapsa tags duplicados que podrían haberse
    generado por concatenación. No corrige todo, pero atrapa los patrones
    más frecuentes (<b><b>...</b></b>, </b></b>, <font><font>).
    """
    if not html:
        return ''
    html = re.sub(r'<b>(\s*<b>)+', '<b>', html)
    html = re.sub(r'(</b>\s*)+</b>', '</b>', html)
    return html


def _safe_paragraph(text: str, style):
    """
    Crea un Paragraph defensivo: si el parser de ReportLab falla por HTML
    malformado, lo intenta de nuevo con la versión sin tags (texto plano
    escapado). Así el informe no se cae entero por una sola incidencia
    con comillas malformadas.
    """
    try:
        return Paragraph(text, style)
    except Exception as e:
        print(f'[informe] ⚠️  Paragraph parse error ({e}); '
              f'reintentando sin tags', flush=True)
        plano = re.sub(r'<[^>]+>', '', text or '')
        plano = (plano.replace('&amp;', '&')
                       .replace('&lt;', '<')
                       .replace('&gt;', '>')
                       .replace('&laquo;', '«')
                       .replace('&raquo;', '»'))
        plano_esc = (plano.replace('&', '&amp;')
                          .replace('<', '&lt;')
                          .replace('>', '&gt;'))
        return Paragraph(plano_esc, style)


# ── Capitalización inteligente de nombres ─────────────────────────────────────
_PARTICULAS = {'de', 'del', 'la', 'las', 'los', 'y', 'e', 'da', 'do', 'dos',
                'das', 'di', 'van', 'von', 'der', 'den'}

def _capitalizar_nombre(nombre: str) -> str:
    if not nombre:
        return ''
    s = str(nombre).strip()
    if not s:
        return ''
    if not (s.isupper() or s.islower()):
        pass
    palabras = s.split()
    resultado = []
    for i, p in enumerate(palabras):
        p_low = p.lower()
        if i > 0 and p_low in _PARTICULAS:
            resultado.append(p_low)
        elif '.' in p and len(p.replace('.','')) <= 3:
            resultado.append(p.upper())
        else:
            resultado.append(p_low[:1].upper() + p_low[1:])
    return ' '.join(resultado)


# ── Registro de DejaVuSans para estrellas ─────────────────────────────────────
_STAR_FONT = None
def _registrar_fuente_estrellas():
    global _STAR_FONT
    if _STAR_FONT is not None:
        return _STAR_FONT
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        fonts_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        ttf_path = os.path.join(fonts_dir, 'DejaVuSans.ttf')
        if os.path.exists(ttf_path):
            try:
                pdfmetrics.registerFont(TTFont('DejaVuStars', ttf_path))
                _STAR_FONT = 'DejaVuStars'
                return _STAR_FONT
            except Exception as e:
                print(f'[informe] Error registrando DejaVuSans: {e}')
        for path in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                     '/usr/share/fonts/dejavu/DejaVuSans.ttf']:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('DejaVuStars', path))
                _STAR_FONT = 'DejaVuStars'
                return _STAR_FONT
    except Exception as e:
        print(f'[informe] No se pudo registrar fuente de estrellas: {e}')
    _STAR_FONT = 'Helvetica'
    return _STAR_FONT

def _estrellas(pts_str):
    s = str(pts_str).strip()
    n = 0
    if '★' in s:
        n = s.count('★')
    elif '☆' in s and '★' not in s:
        n = 0
    else:
        m = re.search(r'[0-5]', s)
        if m:
            try:
                n = int(m.group())
            except:
                n = 0
        else:
            palabras = {'cinco':5,'cuatro':4,'tres':3,'dos':2,'uno':1,'una':1,'cero':0}
            for k, v in palabras.items():
                if k in s.lower():
                    n = v; break
    n = max(0, min(5, n))
    fuente = _registrar_fuente_estrellas()
    print(f'[informe] _estrellas({pts_str!r}) → n={n} (fuente={fuente})', flush=True)
    return (
        f'<font name="{fuente}" size="14" color="#A88838">'
        f'{"\u2605" * n}{"\u2606" * (5 - n)}</font>'
        f'<br/><font name="Helvetica-Oblique" size="6.5" color="#888888">{n} de 5</font>'
    )

def _veredicto_color(v):
    v = (v or '').upper()
    if 'PUBLICABLE' in v and 'CON' not in v:
        return VERDE_ED
    if 'CON MEJORAS' in v:
        return DORADO
    return ROJO_ED

# ── Cabecera editorial profesional ────────────────────────────────────────────
def _cabecera(d):
    if LOGO_PATH:
        try:
            from PIL import Image as PIL
            with PIL.open(LOGO_PATH) as _i:
                ratio = _i.width / _i.height
            alto = 13*mm
            ancho = alto * ratio
            ancho_max = W_DOC * 0.42
            if ancho > ancho_max:
                ancho = ancho_max
                alto = ancho / ratio
            logo = Image(LOGO_PATH, width=ancho, height=alto)
            logo.hAlign = 'LEFT'
        except Exception:
            logo = Paragraph(
                '<font name="Times-Bold" size="15" color="#1A1A1A">Editorial Numancia</font><br/>'
                '<font name="Helvetica" size="7.5" color="#666666">Grupo Printcolorweb.com</font>',
                S('lh','Helvetica',12,15,NEGRO))
    else:
        logo = Paragraph(
            '<font name="Times-Bold" size="15" color="#1A1A1A">Editorial Numancia</font><br/>'
            '<font name="Helvetica" size="7.5" color="#666666">Grupo Printcolorweb.com</font>',
            S('lh','Helvetica',12,15,NEGRO))

    der = Paragraph(
        '<font name="Times-Italic" size="7.5" color="#A88838">— S E L L O   E D I T O R I A L —</font><br/>'
        '<font name="Times-Bold" size="11" color="#1A1A1A">INFORME DE LECTURA</font><br/>'
        '<font name="Times-Bold" size="11" color="#1A1A1A">Y VALORACIÓN</font><br/>'
        '<font name="Helvetica-Oblique" size="6.5" color="#888888">Documento confidencial · uso interno</font>',
        S('rh','Helvetica',9,12,NEGRO,TA_RIGHT))

    cab = Table([[logo, der]], colWidths=[W_DOC*0.50, W_DOC*0.50])
    cab.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), CREMA),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),12),
        ('RIGHTPADDING',(0,0),(-1,-1),12),
        ('TOPPADDING',(0,0),(-1,-1),10),
        ('BOTTOMPADDING',(0,0),(-1,-1),10),
        ('LINEBELOW',(0,0),(-1,-1),0.8, DORADO),
    ]))
    return cab


def _linea_valoracion(numero_presupuesto: str):
    num = (numero_presupuesto or '').strip()
    if not num:
        return None
    num_esc = num.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    p = Paragraph(
        f'<font name="Times-Roman" size="9" color="#6B6B6B">Valoración nº {num_esc}</font>',
        S('valnum','Times-Roman', 9, 11, GRIS_MEDIO, TA_RIGHT,
          spaceBefore=2, spaceAfter=2)
    )
    t = Table([[p]], colWidths=[W_DOC])
    t.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1), 0),
        ('RIGHTPADDING',(0,0),(-1,-1), 12),
        ('TOPPADDING',(0,0),(-1,-1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1), 3),
        ('ALIGN',(0,0),(-1,-1),'RIGHT'),
    ]))
    return t


def _banda_meta(d):
    txt = (
        f'<font name="Helvetica-Bold" size="7.5" color="#A88838">ASESORA EDITORIAL</font>  '
        f'<font name="Helvetica" size="7.5" color="#1A1A1A">{d.get("evaluado_por","")}</font>'
        f'<font name="Helvetica" size="7" color="#B5B5B5">     ·     </font>'
        f'<font name="Helvetica-Bold" size="7.5" color="#A88838">FECHA</font>  '
        f'<font name="Helvetica" size="7.5" color="#1A1A1A">{d.get("fecha","")}</font>'
    )
    p = Paragraph(txt, S('mt','Helvetica',7.5,11))
    t = Table([[p]], colWidths=[W_DOC])
    t.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),12),
        ('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LINEBELOW',(0,0),(-1,-1),0.3, GRIS_LINEA),
    ]))
    return t

def _seccion(titulo, color=NEGRO):
    txt = f'<font name="Helvetica-Bold" size="8" color="#A88838" >{titulo.upper()}</font>'
    p = Paragraph(txt, S('s','Helvetica-Bold',8,11,DORADO,letterSpacing=3))
    t = Table([[p]], colWidths=[W_DOC])
    t.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LINEBELOW',(0,0),(-1,-1),1.2, DORADO),
    ]))
    return t

def _ficha(rows):
    data = []
    for k, v in rows:
        if v:
            data.append([
                Paragraph(f'<font name="Helvetica" size="7" color="#888888" >{k.upper()}</font>',
                          S('fk','Helvetica',7,10,GRIS,letterSpacing=1)),
                Paragraph(f'<font name="Times-Roman" size="10" color="#1A1A1A">{v}</font>',
                          S('fv','Times-Roman',10,13))
            ])
    if not data: return None
    t = Table(data, colWidths=[35*mm, W_DOC - 35*mm])
    t.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LINEBELOW',(0,0),(-1,-2),0.3, GRIS_LINEA),
    ]))
    return t


def _tabla_publico_objetivo(lector_primario, lector_secundario, comparable, precio=''):
    lp = (lector_primario or '').strip()
    ls = (lector_secundario or '').strip()
    cp = (comparable or '').strip()
    pr = (precio or '').strip()

    cab = [
        Paragraph('<font name="Helvetica-Bold" size="7" color="#A88838">CATEGORÍA</font>',
                  S('puh1','Helvetica-Bold',7,10,DORADO,letterSpacing=1)),
        Paragraph('<font name="Helvetica-Bold" size="7" color="#A88838">DESCRIPCIÓN</font>',
                  S('puh2','Helvetica-Bold',7,10,DORADO,letterSpacing=1)),
    ]

    def _fila(label, valor):
        return [
            Paragraph(
                f'<font name="Helvetica-Bold" size="8.5" color="#3A3A3A">{label}</font>',
                S('pul','Helvetica-Bold',8.5,12,GRIS_OSC,letterSpacing=0.5)
            ),
            Paragraph(
                f'<font name="Times-Roman" size="11" color="#1A1A1A">{valor}</font>' if valor else '',
                S('puv','Times-Roman',11,13.2,NEGRO,TA_JUSTIFY)
            ),
        ]

    rows = [cab,
            _fila('Lector primario',   lp),
            _fila('Lector secundario', ls),
            _fila('Comparable',        cp),
            _fila('Precio sugerido',   pr)]

    col1 = W_DOC * 0.35
    col2 = W_DOC * 0.65
    t = Table(rows, colWidths=[col1, col2])
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0,0),(-1,0),  CREMA),
        ('LINEABOVE',   (0,1),(-1,1),  0.6, DORADO),
        ('BACKGROUND',  (0,1),(0,-1),  colors.HexColor('#F5F2EC')),
        ('LINEBELOW',   (0,0),(-1,-1), 0.3, GRIS_LINEA),
        ('LEFTPADDING', (0,0),(-1,-1), 6),
        ('RIGHTPADDING',(0,0),(-1,-1), 6),
        ('TOPPADDING',  (0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('VALIGN',      (0,0),(-1,-1), 'TOP'),
        ('MINSIZE',     (0,1),(-1,-1), 18),
    ]))
    return t

def _tabla_evaluacion(eval_list):
    rows = [[
        Paragraph('<font name="Helvetica-Bold" size="7" color="#A88838" >CRITERIO</font>',
                  S('eh','Helvetica-Bold',7,10,DORADO,letterSpacing=1)),
        Paragraph('<font name="Helvetica-Bold" size="7" color="#A88838" >VALORACIÓN</font>',
                  S('ev','Helvetica-Bold',7,10,DORADO,TA_CENTER,letterSpacing=1)),
        Paragraph('<font name="Helvetica-Bold" size="7" color="#A88838" >OBSERVACIÓN DE LA ASESORA</font>',
                  S('eo','Helvetica-Bold',7,10,DORADO,letterSpacing=1)),
    ]]
    for e in (eval_list or []):
        rows.append([
            Paragraph(f'<font name="Times-Bold" size="9.5" color="#1A1A1A">{e.get("criterio","")}</font>',
                      S('ec','Times-Bold',9.5,12)),
            Paragraph(_estrellas(e.get('estrellas','0/5')),
                      S('es','Helvetica',13,16,align=TA_CENTER)),
            Paragraph(f'<font name="Times-Italic" size="9" color="#3A3A3A">{e.get("obs","")}</font>',
                      S('eob','Times-Italic',9,12.5,GRIS_OSC,TA_JUSTIFY)),
        ])
    t = Table(rows, colWidths=[36*mm, 28*mm, W_DOC - 36*mm - 28*mm],
              repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), CREMA),
        ('LEFTPADDING',(0,0),(-1,-1),6),
        ('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),7),
        ('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEBELOW',(0,0),(-1,-1),0.3, GRIS_LINEA),
        ('LINEABOVE',(0,1),(-1,1),0.6, DORADO),
    ]))
    return t

def _bloque_veredicto(veredicto, justificacion):
    color = _veredicto_color(veredicto)
    icono = '✓' if 'PUBLICABLE' in (veredicto or '').upper() and 'CON' not in (veredicto or '').upper() else \
            ('★' if 'CON MEJORAS' in (veredicto or '').upper() else '!')
    cab = Paragraph(
        f'<font name="Helvetica-Bold" size="8" color="#FFFFFF" >VEREDICTO EDITORIAL</font>',
        S('vh','Helvetica-Bold',8,11,BLANCO,TA_CENTER,letterSpacing=3))
    nucleo = Paragraph(
        f'<font name="Helvetica" size="22" color="#FFFFFF">{icono}</font>'
        f'  <font name="Times-Bold" size="20" color="#FFFFFF">{veredicto}</font>',
        S('vn','Helvetica',20,24,BLANCO,TA_CENTER))
    just = Paragraph(
        f'<font name="Times-Italic" size="10" color="#FFFFFF">{justificacion}</font>',
        S('vj','Times-Italic',10,14,BLANCO,TA_JUSTIFY,
          leftIndent=8*mm, rightIndent=8*mm, spaceBefore=4))
    t = Table([[cab],[nucleo],[just]], colWidths=[W_DOC])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), color),
        ('LEFTPADDING',(0,0),(-1,-1),12),
        ('RIGHTPADDING',(0,0),(-1,-1),12),
        ('TOPPADDING',(0,0),(0,0),8),
        ('TOPPADDING',(0,1),(0,1),4),
        ('TOPPADDING',(0,2),(0,2),0),
        ('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))
    return t


def _hacer_footer_callback(numero_presupuesto: str):
    num = (numero_presupuesto or '').strip()

    def _draw_footer(canvas, doc):
        canvas.saveState()
        page_w, page_h = A4
        margen_x = 18*mm
        y_footer = 8*mm

        texto_corp = ('Editorial Numancia · Grupo Printcolorweb.com · '
                      'C/ Numancia 187, planta -1 · 08034 Barcelona')
        texto_conf = 'DOCUMENTO CONFIDENCIAL — USO INTERNO EXCLUSIVO'

        if num:
            num_esc = num.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            prefijo = f'Valoración nº {num_esc} · '
            canvas.setFont('Times-Italic', 8)
            canvas.setFillColor(GRIS_MEDIO)
            canvas.drawString(margen_x, y_footer + 6, prefijo + texto_corp)
        else:
            canvas.setFont('Times-Italic', 7.5)
            canvas.setFillColor(GRIS)
            canvas.drawCentredString(page_w / 2, y_footer + 6, texto_corp)

        canvas.setFont('Helvetica', 6.5)
        canvas.setFillColor(DORADO)
        canvas.drawCentredString(page_w / 2, y_footer - 2, texto_conf)

        canvas.restoreState()

    return _draw_footer


def _construir_bloque_carta(d):
    carta = (d.get('carta_autor') or '').strip()
    if not carta:
        return None

    carta_html = ''
    for parrafo in carta.split('\n\n'):
        parrafo = parrafo.strip()
        if not parrafo:
            continue
        parrafo_esc = parrafo.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        carta_html += (
            f'<font name="Times-Italic" size="11" color="#1A1A1A">{parrafo_esc}</font>'
            '<br/><br/>'
        )

    asesora = d.get('evaluado_por') or d.get('asesora_nombre') or 'La asesora editorial'

    import unicodedata

    def _norm(s):
        s = (s or '').lower().strip()
        return ''.join(
            c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) != 'Mn'
        )

    FOTO_MAP = {
        'nancy': 'nancy-circ.png',
        'editorial numancia': 'nancy-circ.png',
        'debora': 'debora-circ.png',
        'debora tomas': 'debora-circ.png',
        'juan': 'juan-circ.png',
        'juan munoz': 'juan-circ.png',
        'laura': 'laura-circ.png',
        'laura vega ugarte': 'laura-circ.png',
    }

    nkey = _norm(asesora)
    foto_file = (FOTO_MAP.get(nkey) or FOTO_MAP.get(nkey.split(' ')[0])) if nkey else None
    foto_path = os.path.join(os.path.dirname(__file__), 'fotos', foto_file) if foto_file else None

    contenido_carta = Paragraph(
        carta_html,
        S('car', 'Times-Italic', 11, 16, NEGRO, TA_JUSTIFY,
          leftIndent=2*mm, rightIndent=2*mm, spaceAfter=4)
    )

    firma_texto = Paragraph(
        f'<font name="Times-Italic" size="10" color="#666666">— {asesora}</font><br/>'
        f'<font name="Helvetica" size="6.5" color="#A88838">EDITORIAL NUMANCIA</font>',
        S('fma', 'Times-Italic', 10, 13, GRIS, TA_RIGHT,
          rightIndent=0, spaceAfter=2)
    )

    firma_flow = []
    if foto_path and os.path.exists(foto_path):
        from reportlab.platypus import Image as RLImage
        foto_img = RLImage(foto_path, width=18*mm, height=18*mm)
        foto_img.hAlign = 'RIGHT'
        firma_flow.append(foto_img)
        firma_flow.append(Spacer(1, 2*mm))
    firma_flow.append(firma_texto)

    firma_tbl = Table([[firma_flow]], colWidths=[42*mm], hAlign='RIGHT')
    firma_tbl.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    tbl_carta = Table([[contenido_carta], [firma_tbl]], colWidths=[W_DOC])
    tbl_carta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CREMA),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (0, 0), 12),
        ('BOTTOMPADDING', (0, 0), (0, 0), 4),
        ('TOPPADDING', (0, 1), (0, 1), 6),
        ('BOTTOMPADDING', (0, 1), (0, 1), 10),
        ('ALIGN', (0, 1), (0, 1), 'RIGHT'),
        ('VALIGN', (0, 1), (0, 1), 'TOP'),
        ('LINEBELOW', (0, -1), (-1, -1), 0.6, DORADO),
        ('LINEABOVE', (0, 0), (-1, 0), 0.6, DORADO),
    ]))

    return KeepTogether([
        _seccion('Una nota personal de la asesora'),
        Spacer(1, 8),
        tbl_carta,
    ])


# ── Generador principal ───────────────────────────────────────────────────────
def generar_informe(d: dict) -> bytes:
    buf = io.BytesIO()

    d = dict(d)
    if d.get('autor'):
        d['autor'] = _capitalizar_nombre(d['autor'])

    numero_presupuesto = (d.get('numero_presupuesto') or '').strip()
    if numero_presupuesto:
        print(f'[informe] numero_presupuesto={numero_presupuesto!r}', flush=True)

    titulo_pdf = f"Informe de lectura · {d.get('titulo','')}"
    if numero_presupuesto:
        titulo_pdf += f" · Valoración nº {numero_presupuesto}"

    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=12*mm, bottomMargin=18*mm,
        title=titulo_pdf,
        author='Editorial Numancia',
        subject=f"Informe editorial de {d.get('titulo','')}",
        creator='Editorial Numancia · Grupo Printcolorweb.com',
        producer='Editorial Numancia')

    footer_callback = _hacer_footer_callback(numero_presupuesto)

    story = []
    story.append(_cabecera(d))

    linea_val = _linea_valoracion(numero_presupuesto)
    if linea_val is not None:
        story.append(linea_val)

    story.append(_banda_meta(d))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        f'<font name="Times-Bold" size="30" color="#1A1A1A">{d.get("titulo","")}</font>',
        S('tit','Times-Bold',30,34,NEGRO,TA_LEFT,spaceBefore=2)))
    if d.get('autor'):
        story.append(Paragraph(
            f'<font name="Times-Italic" size="13" color="#666666">{d["autor"]}</font>',
            S('aut','Times-Italic',13,16,GRIS,TA_LEFT,spaceBefore=2)))
    story.append(Paragraph(
        f'<font name="Helvetica" size="8" color="#A88838" >{d.get("genero","").upper()}</font>',
        S('gen','Helvetica',8,11,DORADO,TA_LEFT,letterSpacing=2,spaceBefore=4,spaceAfter=8)))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRIS_LINEA, spaceAfter=10))

    story.append(_seccion('Ficha técnica'))
    story.append(Spacer(1, 4))
    f = _ficha([
        ('Título',          d.get('titulo','')),
        ('Autor/a',         d.get('autor','')),
        ('Género',          d.get('genero','')),
        ('Extensión',       d.get('extension','')),
        ('Ambientación',    d.get('ambientacion','')),
        ('Fecha recepción', d.get('fecha','')),
        ('Evaluado por',    d.get('evaluado_por','')),
    ])
    if f: story.append(f)
    story.append(Spacer(1, 10))

    if any(d.get(k) for k in ('sinopsis_i','sinopsis_ii','sinopsis_iii')):
        story.append(_seccion('Sinopsis'))
        story.append(Spacer(1, 6))
        SIN = S('sin','Times-Italic',10.5,15,NEGRO,TA_JUSTIFY,
                leftIndent=8*mm, rightIndent=4*mm, spaceAfter=5, spaceBefore=2,
                firstLineIndent=4*mm)
        for k in ('sinopsis_i','sinopsis_ii','sinopsis_iii'):
            if d.get(k):
                story.append(Paragraph(d[k], SIN))
        story.append(Spacer(1, 10))

    # ── PÁGINA 2: Veredicto + Evaluación editorial + Notas ──────────────────
    story.append(PageBreak())

    story.append(KeepTogether([
        _bloque_veredicto(
            d.get('veredicto','CON MEJORAS'),
            d.get('veredicto_texto','')),
    ]))
    story.append(Spacer(1, 14))

    story.append(KeepTogether([
        _seccion('Evaluación editorial'),
        Spacer(1, 4),
    ]))
    story.append(_tabla_evaluacion(d.get('eval', [])))
    story.append(Spacer(1, 12))

    if d.get('notas'):
        story.append(KeepTogether([
            _seccion('Notas editoriales'),
            Spacer(1, 6),
        ]))
        for i, n in enumerate(d.get('notas', []), 1):
            if n:
                story.append(KeepTogether([
                    Paragraph(
                        f'<font name="Times-Bold" size="10" color="#A88838">{i}.</font>  '
                        f'<font name="Times-Roman" size="10" color="#1A1A1A">{n}</font>',
                        S('nt','Times-Roman',10,14,NEGRO,TA_JUSTIFY,
                          leftIndent=6*mm, spaceAfter=4)),
                ]))

    # ── PÁGINA 3: Análisis ortotipográfico preliminar ───────────────────────
    orto = d.get('ortotipo')
    if orto and orto.get('total_incidencias', 0) >= 0 and orto.get('incidencias'):
        story.append(PageBreak())
        total = orto.get('total_incidencias', 0)
        cats  = orto.get('categorias_afectadas', 0)
        cifras = Table([[
            Paragraph(
                f'<font name="Times-Bold" size="22" color="#A88838">{total}</font><br/>'
                f'<font name="Helvetica" size="7" color="#666666">incidencias</font>',
                S('cn1','Helvetica',9,12,NEGRO,TA_CENTER)),
            Paragraph(
                f'<font name="Times-Bold" size="22" color="#A88838">{cats}</font><br/>'
                f'<font name="Helvetica" size="7" color="#666666">categorías afectadas</font>',
                S('cn2','Helvetica',9,12,NEGRO,TA_CENTER)),
            Paragraph(
                f'<font name="Times-Italic" size="9.5" color="#3A3A3A">{orto.get("resumen_corrector","")}</font>',
                S('cn3','Times-Italic',9.5,13,GRIS_OSC,TA_JUSTIFY)),
        ]], colWidths=[28*mm, 36*mm, W_DOC - 28*mm - 36*mm])
        cifras.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), CREMA),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),8),
            ('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),10),
            ('BOTTOMPADDING',(0,0),(-1,-1),10),
            ('LINEBELOW',(0,0),(-1,-1),0.4, DORADO),
        ]))
        story.append(KeepTogether([
            _seccion('Análisis ortotipográfico preliminar'),
            Spacer(1, 6),
            cifras,
        ]))
        story.append(Spacer(1, 8))

        rows = [[
            Paragraph('<font name="Helvetica-Bold" size="7" color="#A88838">CATEGORÍA</font>',
                      S('och','Helvetica-Bold',7,10,DORADO)),
            Paragraph('<font name="Helvetica-Bold" size="7" color="#A88838">CASOS</font>',
                      S('ocn','Helvetica-Bold',7,10,DORADO,TA_CENTER)),
            Paragraph('<font name="Helvetica-Bold" size="7" color="#A88838">EJEMPLO DETECTADO Y RECOMENDACIÓN</font>',
                      S('oce','Helvetica-Bold',7,10,DORADO)),
        ]]

        def _esc(s):
            return (s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

        for inc in orto.get('incidencias', []):
            ejemplo_txt = ''
            if inc.get('ejemplos'):
                # ── Fix Parse error: replace seguro con regex balanceada ──
                ej = _esc(inc['ejemplos'][0])
                ej = _resaltar_comillas_balanceadas(ej)
                ejemplo_txt = (
                    '<font name="Helvetica-Bold" size="6.5" color="#A88838">EJEMPLO DETECTADO</font><br/>'
                    f'<font name="Times-Italic" size="8.5" color="#3A3A3A">{ej}</font><br/><br/>'
                )
            reco  = _esc(inc.get('recomendacion',''))
            norma = _esc(inc.get('norma',''))
            nota  = _esc(inc.get('nota',''))
            celda_derecha = (
                ejemplo_txt
                + '<font name="Helvetica-Bold" size="6.5" color="#A88838">RECOMENDACIÓN</font><br/>'
                + f'<font name="Helvetica" size="8" color="#1A1A1A">{reco}</font><br/><br/>'
                + (f'<font name="Helvetica-Bold" size="6.5" color="#A88838">NORMA DE REFERENCIA</font><br/>'
                   f'<font name="Times-Italic" size="7.5" color="#3A3A3A">{norma}</font><br/><br/>' if norma else '')
                + (f'<font name="Helvetica-Bold" size="6.5" color="#A88838">NOTA</font><br/>'
                   f'<font name="Helvetica" size="7.5" color="#666666">{nota}</font>' if nota else '')
            )
            # ── Red de seguridad final: si aún hubiera doble <b> o </b> ──
            celda_derecha = _sanitizar_rl_html(celda_derecha)
            rows.append([
                Paragraph(
                    f'<font name="Times-Bold" size="9.5" color="#1A1A1A">{_esc(inc.get("categoria",""))}</font><br/>'
                    f'<font name="Helvetica" size="7" color="#666666">{_esc(inc.get("descripcion",""))}</font>',
                    S('oct','Helvetica',8,11,NEGRO)),
                Paragraph(
                    f'<font name="Times-Bold" size="14" color="#A88838">{inc.get("ocurrencias","")}</font><br/>'
                    f'<font name="Helvetica" size="6" color="#888888">casos</font>',
                    S('ocnv','Helvetica-Bold',14,16,DORADO,TA_CENTER)),
                # ── _safe_paragraph: si el HTML aún rompe, reintenta sin tags ──
                _safe_paragraph(
                    celda_derecha,
                    S('oer','Helvetica',8,11,GRIS_OSC,TA_JUSTIFY)),
            ])

        tbl = Table(rows, colWidths=[42*mm, 16*mm, W_DOC - 42*mm - 16*mm],
                    repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), CREMA),
            ('LEFTPADDING',(0,0),(-1,-1),6),
            ('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),6),
            ('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LINEBELOW',(0,0),(-1,-1),0.3, GRIS_LINEA),
            ('LINEABOVE',(0,1),(-1,1),0.6, DORADO),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            '<font name="Times-Italic" size="7.5" color="#666666">'
            'Análisis basado en la <b>Ortografía RAE 2010</b>, el <b>DLE 23.ª edición</b> y los criterios de '
            '<b>Martínez de Sousa</b>. La corrección completa se realiza en una fase posterior, '
            'tras la aprobación del autor del proyecto editorial.'
            '</font>',
            S('orf','Helvetica',7.5,11,GRIS,TA_JUSTIFY,
              leftIndent=4*mm, rightIndent=4*mm)))
        story.append(Spacer(1, 12))

    # ── PÁGINA 4: Público objetivo ──────────────────────────────────────────
    story.append(PageBreak())

    pub_nested = d.get('publico') if isinstance(d.get('publico'), dict) else {}
    if not pub_nested and isinstance(d.get('publico_objetivo'), dict):
        pub_nested = d.get('publico_objetivo')

    def _pub_get(*claves):
        for k in claves:
            v = pub_nested.get(k) if isinstance(pub_nested, dict) else None
            if v: return v
        for k in claves:
            v = d.get(k)
            if v: return v
        return ''

    def _aplanar(v):
        if isinstance(v, list):
            return ' · '.join(str(x).strip() for x in v if x)
        if isinstance(v, dict):
            return ' · '.join(str(x).strip() for x in v.values() if x)
        return str(v).strip() if v else ''

    lector_primario   = _aplanar(_pub_get('lector_primario', 'primario', 'lectores_primarios', 'primary_reader', 'primary_audience'))
    lector_secundario = _aplanar(_pub_get('lector_secundario', 'secundario', 'lectores_secundarios', 'secondary_reader', 'secondary_audience'))
    comparable        = _aplanar(_pub_get('comparable', 'comparables', 'titulos_comparables', 'comparable_titles', 'referentes'))
    precio            = _aplanar(_pub_get('precio', 'precio_sugerido', 'precio_recomendado', 'price', 'suggested_price'))

    if not (lector_primario and lector_secundario and comparable and precio):
        print(f'[informe] ⚠️  Público objetivo incompleto. '
              f'primario={bool(lector_primario)}, secundario={bool(lector_secundario)}, '
              f'comparable={bool(comparable)}, precio={bool(precio)}.',
              flush=True)
    else:
        print(f'[informe] ✅ Público objetivo completo (4/4 campos)', flush=True)

    story.append(KeepTogether([
        _seccion('Público objetivo'),
        Spacer(1, 4),
        _tabla_publico_objetivo(
            lector_primario   = lector_primario,
            lector_secundario = lector_secundario,
            comparable        = comparable,
            precio            = precio,
        ),
    ]))
    story.append(Spacer(1, 16))

    _BLOQUE_CARTA = _construir_bloque_carta(d)
    if _BLOQUE_CARTA is not None:
        story.append(_BLOQUE_CARTA)

    story.append(HRFlowable(width='100%', thickness=0.4, color=DORADO, spaceAfter=4))

    doc.build(story,
              onFirstPage=footer_callback,
              onLaterPages=footer_callback)

    pdf_bytes = buf.getvalue()
    if FAVICON_PATH:
        try:
            pdf_bytes = _embed_thumbnail(pdf_bytes, FAVICON_PATH)
        except Exception as e:
            print(f'[informe_gen] Thumbnail no embebido: {e}')
    return pdf_bytes


def _embed_thumbnail(pdf_bytes: bytes, icon_path: str) -> bytes:
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import (NameObject, NumberObject, ByteStringObject,
                                    DictionaryObject, IndirectObject)
        from PIL import Image as PILImage
        import io as _io

        img = PILImage.open(icon_path).convert('RGB')
        img.thumbnail((128, 128), PILImage.LANCZOS)
        buf = _io.BytesIO()
        img.save(buf, 'JPEG', quality=85)
        jpg_data = buf.getvalue()
        w, h = img.size

        reader = PdfReader(_io.BytesIO(pdf_bytes))
        writer = PdfWriter(clone_from=reader)

        from pypdf.generic import StreamObject
        thumb_stream = StreamObject()
        thumb_stream._data = jpg_data
        thumb_stream.update({
            NameObject('/Type'):             NameObject('/XObject'),
            NameObject('/Subtype'):          NameObject('/Image'),
            NameObject('/Width'):            NumberObject(w),
            NameObject('/Height'):           NumberObject(h),
            NameObject('/ColorSpace'):       NameObject('/DeviceRGB'),
            NameObject('/BitsPerComponent'): NumberObject(8),
            NameObject('/Filter'):           NameObject('/DCTDecode'),
        })
        thumb_ref = writer._add_object(thumb_stream)
        page = writer.pages[0]
        page[NameObject('/Thumb')] = thumb_ref

        out = _io.BytesIO()
        writer.write(out)
        return out.getvalue()
    except ImportError:
        return pdf_bytes
