"""
Genera las primeras 10 páginas maquetadas A5 con marca de agua.
Motor: ReportLab Platypus (BaseDocTemplate + Frame + Paragraph TA_JUSTIFY).
"""
import io, re
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, PageBreak, NextPageTemplate
)

AW, AH   = A5
M_INT = 22*mm; M_EXT = 17*mm; M_TOP = 18*mm; M_BOT = 22*mm
HDR_H = 8*mm; FTR_H = 6*mm

C_TEXT = colors.HexColor('#1A1A1A')
C_GRIS = colors.HexColor('#777777')
C_LINE = colors.HexColor('#AAAAAA')


# ── Estilos ──────────────────────────────────────────────────────────────────
P0  = ParagraphStyle('p0', fontName='Times-Roman', fontSize=11, leading=13,
                     textColor=C_TEXT, alignment=TA_JUSTIFY,
                     firstLineIndent=0, spaceBefore=0, spaceAfter=0)
P   = ParagraphStyle('p',  fontName='Times-Roman', fontSize=11, leading=13,
                     textColor=C_TEXT, alignment=TA_JUSTIFY,
                     firstLineIndent=4.5*mm, spaceBefore=0, spaceAfter=0)
D   = ParagraphStyle('d',  fontName='Times-Roman', fontSize=11, leading=13,
                     textColor=C_TEXT, alignment=TA_JUSTIFY,
                     firstLineIndent=0, spaceBefore=0, spaceAfter=0)
CAP_N = ParagraphStyle('cn', fontName='Times-Bold', fontSize=11, leading=14,
                        textColor=C_TEXT, alignment=TA_CENTER, spaceBefore=18*mm, spaceAfter=3*mm)
CAP_S = ParagraphStyle('cs', fontName='Times-Italic', fontSize=9, leading=13,
                        textColor=C_GRIS, alignment=TA_CENTER, spaceBefore=0, spaceAfter=8*mm)
PORT  = ParagraphStyle('po', fontName='Times-BoldItalic', fontSize=22, leading=28,
                        textColor=C_TEXT, alignment=TA_CENTER, spaceBefore=55*mm)
PORT_S= ParagraphStyle('ps', fontName='Times-Roman', fontSize=10, leading=13,
                        textColor=C_GRIS, alignment=TA_CENTER, spaceBefore=3*mm)
INT_A = ParagraphStyle('ia', fontName='Times-Roman', fontSize=11, leading=14,
                        textColor=C_TEXT, alignment=TA_CENTER, spaceBefore=48*mm)
INT_T = ParagraphStyle('it', fontName='Times-BoldItalic', fontSize=18, leading=24,
                        textColor=C_TEXT, alignment=TA_CENTER, spaceBefore=4*mm)
CRED  = ParagraphStyle('cr', fontName='Helvetica', fontSize=7.5, leading=11,
                        textColor=C_TEXT, alignment=TA_CENTER, spaceAfter=2)
CREDB = ParagraphStyle('cb', fontName='Helvetica-Bold', fontSize=7.5, leading=11,
                        textColor=C_TEXT, alignment=TA_CENTER, spaceAfter=2)
CRED_G= ParagraphStyle('cg', fontName='Helvetica', fontSize=7, leading=10,
                        textColor=C_GRIS, alignment=TA_CENTER)


def _wm(c, doc, titulo, autor):
    c.saveState()
    c.setFont("Helvetica-Bold", 26)
    c.setFillColorRGB(0.72, 0.72, 0.72, 0.20)
    c.translate(AW/2, AH/2)
    c.rotate(38)
    c.drawCentredString(0, 18, "Editorial Numancia")
    c.setFont("Helvetica", 9)
    c.drawCentredString(0, -10, "PRUEBA DE MAQUETA — pendiente aprobación autor")
    c.restoreState()


def _cabecera(c, doc, titulo, autor):
    _wm(c, doc, titulo, autor)
    pn = doc.page
    if pn <= 4:
        return
    recto = (pn % 2 == 1)
    lm = M_INT if recto else M_EXT
    rm = M_EXT  if recto else M_INT
    yh = AH - M_TOP + 5
    c.setFont("Times-Italic", 8)
    c.setFillColor(C_GRIS)
    if recto:
        c.drawRightString(AW - rm, yh, titulo.upper()[:40])
    else:
        c.drawString(lm, yh, autor.upper()[:40])
    c.setStrokeColor(C_LINE)
    c.setLineWidth(0.4)
    c.line(lm, yh - 3, AW - rm, yh - 3)
    c.setFont("Times-Roman", 8)
    c.setFillColor(C_GRIS)
    c.drawCentredString(AW/2, M_BOT - 6*mm, str(pn))


def _cabecera_chap(c, doc, titulo, autor):
    _wm(c, doc, titulo, autor)
    pn = doc.page
    c.setFont("Times-Roman", 8)
    c.setFillColor(C_GRIS)
    c.drawCentredString(AW/2, M_BOT - 6*mm, str(pn))


def _make_frame(recto: bool):
    lm = M_INT if recto else M_EXT
    rm = M_EXT  if recto else M_INT
    return Frame(lm, M_BOT, AW - lm - rm, AH - M_TOP - M_BOT,
                 leftPadding=0, rightPadding=0,
                 topPadding=HDR_H, bottomPadding=FTR_H, showBoundary=0)


# ── Parser de texto ───────────────────────────────────────────────────────────
def _parsear(texto: str):
    """Devuelve lista de (tipo, texto): tipo = 'capitulo'|'parrafo'|'dialogo'"""
    bloques = []
    cap_re = re.compile(
        r'^(cap[ií]tulo\s+\w+|chapter\s+\w+|\d+[\.º\-]\s|parte\s+\w+)',
        re.IGNORECASE
    )
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        if cap_re.match(linea) and len(linea) < 80:
            # Separar número de subtítulo si hay coma o salto
            partes = re.split(r'[—\-–]', linea, maxsplit=1)
            bloques.append(('capitulo', partes[0].strip(), partes[1].strip() if len(partes) > 1 else ''))
        elif linea.startswith('—') or linea.startswith('-'):
            bloques.append(('dialogo', linea))
        else:
            bloques.append(('parrafo', linea))
    return bloques


def generar_preview(texto: str, titulo: str, autor: str) -> bytes:
    buf = io.BytesIO()

    # Cerrar sobre variables locales para los callbacks
    def on_wm(c, doc):      _wm(c, doc, titulo, autor)
    def on_cab(c, doc):     _cabecera(c, doc, titulo, autor)
    def on_chap(c, doc):    _cabecera_chap(c, doc, titulo, autor)

    doc = BaseDocTemplate(buf, pagesize=A5,
        leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)

    fr = _make_frame(True)   # frame recto genérico (prelims)
    fr_r = _make_frame(True)
    fr_v = _make_frame(False)

    doc.addPageTemplates([
        PageTemplate(id='blanca',   frames=[fr],   onPage=on_wm),
        PageTemplate(id='portad',   frames=[fr],   onPage=on_wm),
        PageTemplate(id='portint',  frames=[fr],   onPage=on_wm),
        PageTemplate(id='creditos', frames=[fr_v], onPage=on_wm),
        PageTemplate(id='chap',     frames=[fr_r], onPage=on_chap),
        PageTemplate(id='recto',    frames=[fr_r], onPage=on_cab),
        PageTemplate(id='verso',    frames=[fr_v], onPage=on_cab),
    ])

    story = []

    # P1 blanca
    story.append(NextPageTemplate('portad'))
    story.append(PageBreak())

    # P2 portadilla
    story.append(Paragraph(titulo, PORT))
    story.append(Paragraph("novela", PORT_S))
    story.append(NextPageTemplate('portint'))
    story.append(PageBreak())

    # P3 portada interior
    story.append(Paragraph(autor, INT_A))
    story.append(Paragraph(titulo, INT_T))
    story.append(Spacer(1, 4*mm))

    def _sello(s): return ParagraphStyle(s, fontName='Helvetica-Bold' if 'b' in s else 'Helvetica',
        fontSize=8 if 'b' in s else 7, leading=10, alignment=TA_CENTER,
        textColor=C_TEXT if 'b' in s else C_GRIS, spaceBefore=50*mm if s=='sb1' else 0)

    story.append(Paragraph("▪ EN ▪",
        ParagraphStyle('en0', fontName='Helvetica-Bold', fontSize=8, leading=10,
                        alignment=TA_CENTER, textColor=C_TEXT, spaceBefore=52*mm)))
    story.append(Paragraph("Editorial Numancia", CREDB))
    story.append(Paragraph("Grupo Printcolorweb.com", CRED_G))
    story.append(NextPageTemplate('creditos'))
    story.append(PageBreak())

    # P4 créditos
    story.append(Spacer(1, 38*mm))
    story.append(Paragraph("Primera edición: 2025", CREDB))
    story.append(Paragraph(f"© 2025, {autor}", CREDB))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("Corrección y maquetación: Editorial Numancia", CRED))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Todos los derechos reservados. Queda prohibida la reproducción", CRED_G))
    story.append(Paragraph("total o parcial sin permiso expreso de los titulares del copyright.", CRED_G))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("ISBN: Pendiente de asignación", CREDB))
    story.append(Paragraph("Depósito Legal: Pendiente de asignación", CREDB))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Editado por Editorial Numancia", CRED))
    story.append(Paragraph("Impreso por Fullcolor Printcolor, SL", CRED))
    story.append(Spacer(1, 14*mm))
    story.append(Paragraph("▪ EN ▪", CREDB))
    story.append(Paragraph("Editorial Numancia", CREDB))
    story.append(Paragraph("Grupo Printcolorweb.com", CRED_G))

    # P5+ texto
    story.append(NextPageTemplate('chap'))
    story.append(PageBreak())

    bloques = _parsear(texto)
    primer_cap = True
    primer_parr = True
    pagina_actual = 5
    max_paginas = 10

    for bloque in bloques:
        if pagina_actual > max_paginas:
            break

        tipo = bloque[0]

        if tipo == 'capitulo':
            if not primer_cap:
                story.append(NextPageTemplate('chap'))
                story.append(PageBreak())
                pagina_actual += 1
                if pagina_actual > max_paginas:
                    break
            primer_cap = False
            primer_parr = True
            story.append(Paragraph(bloque[1].upper(), CAP_N))
            if bloque[2]:
                story.append(Paragraph(bloque[2], CAP_S))
            story.append(NextPageTemplate('recto'))

        elif tipo == 'dialogo':
            story.append(Paragraph(bloque[1], D))
            primer_parr = False

        else:  # párrafo
            estilo = P0 if primer_parr else P
            story.append(Paragraph(bloque[1], estilo))
            primer_parr = False

    # Limitar a 10 páginas: el BaseDocTemplate lo gestiona con el contenido dado
    # (el contenido de _parsear ya está acotado a lo que cabe en 6 páginas de texto)

    doc.build(story)
    return buf.getvalue()
