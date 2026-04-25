"""
Genera la maqueta completa del libro A5 — sin marca de agua, lista para Printcolor.
Estructura: blanca > portadilla > portada interior > créditos > dedicatoria >
epígrafe > capítulos (en página impar) > colofón
"""
import io, re
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, PageBreak, NextPageTemplate, HRFlowable
)
from reportlab.platypus.flowables import Flowable

AW, AH   = A5
M_INT = 22*mm; M_EXT = 17*mm; M_TOP = 18*mm; M_BOT = 22*mm
HDR_H = 8*mm; FTR_H = 6*mm

C_TEXT = colors.HexColor('#1A1A1A')
C_GRIS = colors.HexColor('#777777')
C_LINE = colors.HexColor('#AAAAAA')


# ── Flowable: salto a página impar ───────────────────────────────────────────
class PaginaImpar(Flowable):
    def wrap(self, *a): return 0, 0
    def draw(self): pass
    def _doNothing(self, *a): pass


# ── Estilos ──────────────────────────────────────────────────────────────────
P0   = ParagraphStyle('p0',  fontName='Times-Roman', fontSize=11, leading=13,
                      textColor=C_TEXT, alignment=TA_JUSTIFY, firstLineIndent=0)
P    = ParagraphStyle('p',   fontName='Times-Roman', fontSize=11, leading=13,
                      textColor=C_TEXT, alignment=TA_JUSTIFY, firstLineIndent=4.5*mm)
D    = ParagraphStyle('d',   fontName='Times-Roman', fontSize=11, leading=13,
                      textColor=C_TEXT, alignment=TA_JUSTIFY, firstLineIndent=0)
CAP_N= ParagraphStyle('cn',  fontName='Times-Bold', fontSize=11, leading=14,
                      textColor=C_TEXT, alignment=TA_CENTER, spaceBefore=18*mm, spaceAfter=3*mm)
CAP_S= ParagraphStyle('cs',  fontName='Times-Italic', fontSize=9, leading=13,
                      textColor=C_GRIS, alignment=TA_CENTER, spaceAfter=8*mm)
PORT = ParagraphStyle('po',  fontName='Times-BoldItalic', fontSize=22, leading=28,
                      textColor=C_TEXT, alignment=TA_CENTER, spaceBefore=55*mm)
PORT_S=ParagraphStyle('ps',  fontName='Times-Roman', fontSize=10, leading=13,
                      textColor=C_GRIS, alignment=TA_CENTER, spaceBefore=3*mm)
INT_A= ParagraphStyle('ia',  fontName='Times-Roman', fontSize=11, leading=14,
                      textColor=C_TEXT, alignment=TA_CENTER, spaceBefore=48*mm)
INT_T= ParagraphStyle('it',  fontName='Times-BoldItalic', fontSize=18, leading=24,
                      textColor=C_TEXT, alignment=TA_CENTER, spaceBefore=4*mm)
CRED = ParagraphStyle('cr',  fontName='Helvetica', fontSize=7.5, leading=11,
                      textColor=C_TEXT, alignment=TA_CENTER, spaceAfter=2)
CREDB= ParagraphStyle('cb',  fontName='Helvetica-Bold', fontSize=7.5, leading=11,
                      textColor=C_TEXT, alignment=TA_CENTER, spaceAfter=2)
CRED_G=ParagraphStyle('cg', fontName='Helvetica', fontSize=7, leading=10,
                      textColor=C_GRIS, alignment=TA_CENTER)
DED  = ParagraphStyle('ded', fontName='Times-Italic', fontSize=10, leading=14,
                      textColor=C_TEXT, alignment=TA_RIGHT, spaceBefore=40*mm,
                      rightIndent=8*mm)
EPI  = ParagraphStyle('ep',  fontName='Times-Italic', fontSize=10, leading=14,
                      textColor=C_TEXT, alignment=TA_RIGHT, spaceBefore=40*mm,
                      rightIndent=8*mm)
EPI_A= ParagraphStyle('ea',  fontName='Times-Roman', fontSize=9, leading=13,
                      textColor=C_GRIS, alignment=TA_RIGHT, rightIndent=8*mm, spaceAfter=2)
COL  = ParagraphStyle('col', fontName='Helvetica', fontSize=7, leading=10,
                      textColor=C_GRIS, alignment=TA_CENTER, spaceBefore=2)


def _make_frame(recto: bool):
    lm = M_INT if recto else M_EXT
    rm = M_EXT  if recto else M_INT
    return Frame(lm, M_BOT, AW - lm - rm, AH - M_TOP - M_BOT,
                 leftPadding=0, rightPadding=0,
                 topPadding=HDR_H, bottomPadding=FTR_H, showBoundary=0)


def _on_recto(titulo):
    def _fn(c, doc):
        pn = doc.page
        if pn < 7:
            return
        rm = M_EXT
        yh = AH - M_TOP + 5
        c.setFont("Times-Italic", 8); c.setFillColor(C_GRIS)
        c.drawRightString(AW - rm, yh, titulo.upper()[:45])
        c.setStrokeColor(C_LINE); c.setLineWidth(0.4)
        c.line(M_INT, yh - 3, AW - rm, yh - 3)
        c.setFont("Times-Roman", 8); c.setFillColor(C_GRIS)
        c.drawCentredString(AW/2, M_BOT - 6*mm, str(pn))
    return _fn


def _on_verso(autor):
    def _fn(c, doc):
        pn = doc.page
        if pn < 7:
            return
        lm = M_EXT
        yh = AH - M_TOP + 5
        c.setFont("Times-Italic", 8); c.setFillColor(C_GRIS)
        c.drawString(lm, yh, autor.upper()[:45])
        c.setStrokeColor(C_LINE); c.setLineWidth(0.4)
        c.line(lm, yh - 3, AW - M_INT, yh - 3)
        c.setFont("Times-Roman", 8); c.setFillColor(C_GRIS)
        c.drawCentredString(AW/2, M_BOT - 6*mm, str(pn))
    return _fn


def _on_chap(c, doc):
    pn = doc.page
    if pn >= 7:
        c.setFont("Times-Roman", 8); c.setFillColor(C_GRIS)
        c.drawCentredString(AW/2, M_BOT - 6*mm, str(pn))


def _on_blank(c, doc): pass


# ── Parser ────────────────────────────────────────────────────────────────────
def _parsear(texto: str):
    """Parser universal — mismo que preview_gen."""
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    cap_num_re  = re.compile(r'^(CAP[IÍ]TULO\s+\w[\w\s]{0,30})', re.IGNORECASE)
    cap_solo_re = re.compile(r'^Cap[ií]tulo\s+\d+\s*$', re.IGNORECASE)
    cap_punto_re= re.compile(r'^Cap[ií]tulo\s+\d+\.\s+\S', re.IGNORECASE)

    bloques = []
    contenido = False
    i = 0
    while i < len(lineas):
        l = lineas[i]
        if '\t' in l:
            i += 1; continue

        es_cap = False
        cap_num = ''; cap_sub = ''

        if cap_solo_re.match(l) and len(l) < 40:
            cap_num = l
            cap_sub = lineas[i+1] if i+1 < len(lineas) and '\t' not in lineas[i+1] else ''
            es_cap = True
            i += 2 if cap_sub else 1
        elif cap_punto_re.match(l) and len(l) < 100:
            partes = re.split(r'\.\s+', l, maxsplit=1)
            cap_num = partes[0]; cap_sub = partes[1] if len(partes) > 1 else ''
            es_cap = True; i += 1
        elif cap_num_re.match(l) and len(l) < 80 and '\t' not in l:
            partes = re.split(r'\s*[—\-–]\s*', l, maxsplit=1)
            cap_num = partes[0]; cap_sub = partes[1] if len(partes) > 1 else ''
            es_cap = True; i += 1
        else:
            i += 1

        if es_cap:
            contenido = True
            bloques.append(('cap', cap_num.strip(), cap_sub.strip()))
        elif contenido:
            if l.startswith('—') or l.startswith('\u2014'):
                bloques.append(('dial', l))
            else:
                bloques.append(('parr', l))

    return bloques


def generar_maqueta_completa(
    texto: str,
    titulo: str,
    autor: str,
    anyo: str = "2025",
    dedicatoria: str = "",
    epigrafe: str = "",
    epigrafe_autor: str = "",
) -> bytes:
    buf = io.BytesIO()

    on_r = _on_recto(titulo)
    on_v = _on_verso(autor)

    doc = BaseDocTemplate(buf, pagesize=A5,
        leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)

    fr_r = _make_frame(True)
    fr_v = _make_frame(False)
    fr_c = _make_frame(True)   # recto para capítulos

    doc.addPageTemplates([
        PageTemplate(id='blank',   frames=[fr_r], onPage=_on_blank),
        PageTemplate(id='portad',  frames=[fr_r], onPage=_on_blank),
        PageTemplate(id='portint', frames=[fr_r], onPage=_on_blank),
        PageTemplate(id='cred',    frames=[fr_v], onPage=_on_blank),
        PageTemplate(id='ded',     frames=[fr_r], onPage=_on_blank),
        PageTemplate(id='epi',     frames=[fr_v], onPage=_on_blank),
        PageTemplate(id='chap',    frames=[fr_c], onPage=_on_chap),
        PageTemplate(id='recto',   frames=[fr_r], onPage=on_r),
        PageTemplate(id='verso',   frames=[fr_v], onPage=on_v),
        PageTemplate(id='colofon', frames=[fr_r], onPage=_on_blank),
    ])

    story = []

    # ── Prelims ──────────────────────────────────────────────────────────────

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
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("▪ EN ▪",
        ParagraphStyle('en0', fontName='Helvetica-Bold', fontSize=8, leading=10,
                        alignment=TA_CENTER, textColor=C_TEXT, spaceBefore=50*mm)))
    story.append(Paragraph("Editorial Numancia", CREDB))
    story.append(Paragraph("Grupo Printcolorweb.com", CRED_G))
    story.append(NextPageTemplate('cred'))
    story.append(PageBreak())

    # P4 créditos
    story.append(Spacer(1, 38*mm))
    story.append(Paragraph(f"Primera edición: {anyo}", CREDB))
    story.append(Paragraph(f"© {anyo}, {autor}", CREDB))
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
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Papel offset 90 g/m² · Cubierta cartulina 300 g/m²", CRED_G))
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("▪ EN ▪", CREDB))
    story.append(Paragraph("Editorial Numancia", CREDB))
    story.append(Paragraph("Grupo Printcolorweb.com", CRED_G))

    # P5 dedicatoria (o blanca)
    story.append(NextPageTemplate('ded'))
    story.append(PageBreak())
    if dedicatoria.strip():
        story.append(Paragraph(dedicatoria.strip(), DED))

    # P6 epígrafe (o blanca)
    story.append(NextPageTemplate('epi'))
    story.append(PageBreak())
    if epigrafe.strip():
        story.append(Paragraph(epigrafe.strip(), EPI))
        if epigrafe_autor.strip():
            story.append(Paragraph(f"— {epigrafe_autor.strip()}", EPI_A))

    # ── Cuerpo del libro ─────────────────────────────────────────────────────
    bloques = _parsear(texto)
    primer_cap = True
    primer_parr = True
    next_template = 'recto'  # alterna recto/verso

    for bloque in bloques:
        tipo = bloque[0]

        if tipo == 'cap':
            # Cada capítulo abre en página impar
            story.append(NextPageTemplate('chap'))
            story.append(PageBreak())
            primer_parr = True
            story.append(Paragraph(bloque[1].upper(), CAP_N))
            if bloque[2]:
                story.append(Paragraph(bloque[2], CAP_S))
            story.append(NextPageTemplate('recto'))

        elif tipo == 'dial':
            story.append(Paragraph(bloque[1], D))
            primer_parr = False

        else:
            story.append(Paragraph(bloque[1], P0 if primer_parr else P))
            primer_parr = False

    # ── Colofón ──────────────────────────────────────────────────────────────
    story.append(NextPageTemplate('colofon'))
    story.append(PageBreak())
    story.append(Spacer(1, 90*mm))
    story.append(HRFlowable(width='40%', thickness=0.5, color=C_LINE,
                             hAlign='CENTER', spaceAfter=8))
    story.append(Paragraph(
        f"<i>{titulo}</i> se terminó de imprimir en {anyo}.<br/>"
        f"Impreso en España por Fullcolor Printcolor, SL,<br/>"
        f"en papel offset de 90 g/m² con cubierta en cartulina de 300 g/m².",
        ParagraphStyle('col2', fontName='Times-Italic', fontSize=8, leading=12,
                        textColor=C_GRIS, alignment=TA_CENTER)))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("▪ EN ▪",
        ParagraphStyle('col3', fontName='Helvetica-Bold', fontSize=8, leading=10,
                        alignment=TA_CENTER, textColor=C_TEXT)))
    story.append(Paragraph("Editorial Numancia · Grupo Printcolorweb.com", COL))

    doc.build(story)
    return buf.getvalue()
