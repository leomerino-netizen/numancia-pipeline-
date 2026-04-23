"""
Genera el informe de viabilidad A4 PDF — estructura fija Editorial Numancia.
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# ── Colores ──────────────────────────────────────────────────────────────────
NEGRO   = colors.HexColor('#1A1A1A')
GRIS    = colors.HexColor('#777777')
CREMA   = colors.HexColor('#F8F6F2')
BLANCO  = colors.white
GRIS_CL = colors.HexColor('#CCCCCC')

W_DOC = A4[0] - 40*mm


def S(name, font='Helvetica', size=8, leading=11, color=NEGRO, align=TA_LEFT, **kw):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                          textColor=color, alignment=align, **kw)


def generar_informe(d: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=16*mm, bottomMargin=18*mm)

    story = []

    # ── Cabecera bicolumna ────────────────────────────────────────────────────
    cab = Table([[
        Paragraph('<font name="Helvetica-Bold" size="12">Editorial Numancia</font><br/>'
                  '<font name="Helvetica" size="7.5" color="#777777">Grupo Printcolorweb.com</font>',
                  S('x1', 'Helvetica', 12, 15)),
        Paragraph('<font name="Helvetica-Bold" size="8">INFORME DE VIABILIDAD EDITORIAL</font><br/>'
                  '<font name="Helvetica" size="7" color="#777777">Uso interno · Confidencial</font>',
                  S('x2', 'Helvetica', 8, 11, align=TA_RIGHT))
    ]], colWidths=[W_DOC * 0.5, W_DOC * 0.5])
    cab.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(cab)
    story.append(HRFlowable(width='100%', thickness=2, color=NEGRO, spaceAfter=4))

    # asesora + fecha
    meta = Table([[
        Paragraph(f'<font name="Helvetica-Bold" size="7">Asesora:</font>'
                  f' <font name="Helvetica" size="7">{d.get("evaluado_por","")}</font>',
                  S('m1', size=7)),
        Paragraph(f'<font name="Helvetica-Bold" size="7">Fecha:</font>'
                  f' <font name="Helvetica" size="7">{d.get("fecha","")}</font>',
                  S('m2', size=7, align=TA_RIGHT))
    ]], colWidths=[W_DOC * 0.5, W_DOC * 0.5])
    meta.setStyle(TableStyle([
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta)

    # ── Título 28pt Times-BoldItalic ─────────────────────────────────────────
    story.append(Paragraph(d.get('titulo', ''), S('tit', 'Times-BoldItalic', 28, 32, spaceBefore=2)))
    story.append(Paragraph(d.get('genero', ''),
        S('sub', 'Times-Italic', 10, 13, color=GRIS, spaceBefore=2, spaceAfter=8)))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRIS_CL, spaceAfter=6))

    SEC = S('sec', 'Helvetica-Bold', 7.5, 10, spaceBefore=8, spaceAfter=3)
    HB  = S('hb',  'Helvetica-Bold', 7.5, 11)
    HN  = S('hn',  'Helvetica',      7.5, 11)

    def tabla_kv(rows, col1=42*mm):
        t = Table([[Paragraph(k, HB), Paragraph(v, HN)] for k, v in rows],
                  colWidths=[col1, W_DOC - col1])
        t.setStyle(TableStyle([
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [CREMA, BLANCO]),
            ('LEFTPADDING',  (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING',   (0,0), (-1,-1), 3),
            ('BOTTOMPADDING',(0,0), (-1,-1), 3),
            ('GRID', (0,0), (-1,-1), 0.3, GRIS_CL),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        return t

    # ── FICHA TÉCNICA ─────────────────────────────────────────────────────────
    story.append(Paragraph('FICHA TÉCNICA', SEC))
    story.append(tabla_kv([
        ('Título',          d.get('titulo', '')),
        ('Autor/a',         d.get('autor', '')),
        ('Género',          d.get('genero', '')),
        ('Extensión',       d.get('extension', '')),
        ('Ambientación',    d.get('ambientacion', '')),
        ('Fecha recepción', d.get('fecha', '')),
        ('Evaluado por',    d.get('evaluado_por', '')),
    ]))

    # ── SINOPSIS ──────────────────────────────────────────────────────────────
    SIN = S('sin', 'Times-Italic', 9.5, 13, color=NEGRO, align=TA_JUSTIFY,
            leftIndent=8*mm, rightIndent=4*mm, spaceAfter=5)
    story.append(Paragraph('SINOPSIS', SEC))
    for key in ('sinopsis_i', 'sinopsis_ii', 'sinopsis_iii'):
        story.append(Paragraph(f'<i>{d.get(key, "")}</i>', SIN))

    # ── EVALUACIÓN ────────────────────────────────────────────────────────────
    story.append(Paragraph('EVALUACIÓN EDITORIAL', SEC))
    eval_rows = [['Criterio', 'Valoración', 'Observación']]
    for e in d.get('eval', []):
        eval_rows.append([e.get('criterio',''), e.get('estrellas',''), e.get('obs','')])
    ev = Table(
        [[Paragraph(r[0], S('eh', 'Helvetica-Bold', 7.5, 11) if i == 0 else HB),
          Paragraph(r[1], S('ec', 'Helvetica', 7.5, 11, align=TA_CENTER)),
          Paragraph(r[2], HN)]
         for i, r in enumerate(eval_rows)],
        colWidths=[40*mm, 24*mm, W_DOC - 64*mm]
    )
    ev.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), NEGRO),
        ('TEXTCOLOR',   (0,0), (-1,0), BLANCO),
        ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 7.5),
        ('LEADING',     (0,0), (-1,-1), 11),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [CREMA, BLANCO]),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING',(0,0), (-1,-1), 5),
        ('TOPPADDING',  (0,0), (-1,-1), 3),
        ('BOTTOMPADDING',(0,0), (-1,-1), 3),
        ('GRID', (0,0), (-1,-1), 0.3, GRIS_CL),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,1), (1,-1), 'CENTER'),
    ]))
    story.append(ev)

    # ── VEREDICTO — caja negra texto blanco ───────────────────────────────────
    story.append(Spacer(1, 6))
    story.append(Paragraph('VEREDICTO', SEC))
    story.append(Spacer(1, 3))
    verd_box = Table([
        [Paragraph(f'✓ {d.get("veredicto","CON MEJORAS")}',
                   S('vb', 'Helvetica-Bold', 12, 15, color=BLANCO, align=TA_CENTER))],
        [Paragraph(d.get('veredicto_texto', ''),
                   S('vt', 'Helvetica', 8, 12, color=NEGRO, align=TA_JUSTIFY,
                     spaceBefore=0, spaceAfter=4))],
    ], colWidths=[W_DOC])
    verd_box.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (0,0), NEGRO),
        ('BACKGROUND',    (0,1), (0,1), BLANCO),
        ('BOX',           (0,0), (-1,-1), 2, NEGRO),
        ('TOPPADDING',    (0,0), (0,0), 8),
        ('BOTTOMPADDING', (0,0), (0,0), 8),
        ('TOPPADDING',    (0,1), (0,1), 7),
        ('BOTTOMPADDING', (0,1), (0,1), 7),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
    ]))
    story.append(verd_box)

    # ── PÚBLICO OBJETIVO ──────────────────────────────────────────────────────
    story.append(Paragraph('PÚBLICO OBJETIVO', SEC))
    story.append(tabla_kv([
        ('Lector primario',   d.get('lector_primario', '')),
        ('Lector secundario', d.get('lector_secundario', '')),
        ('Comparable',        d.get('comparable', '')),
        ('Precio sugerido',   d.get('precio', '')),
    ], col1=40*mm))

    # ── NOTAS ─────────────────────────────────────────────────────────────────
    notas = d.get('notas', [])
    if notas:
        story.append(Paragraph('NOTAS', SEC))
        notas_html = ''.join(f'<b>{i+1}.</b> {n}<br/>' for i, n in enumerate(notas))
        story.append(Paragraph(notas_html,
            S('not', 'Helvetica', 7.5, 11, color=NEGRO)))

    # ── Pie confidencial ──────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', thickness=0.5, color=GRIS_CL, spaceAfter=4))
    story.append(Paragraph(
        'Editorial Numancia · Grupo Printcolorweb.com · Barcelona · '
        'Documento de uso interno — confidencial. Prohibida su distribución sin autorización expresa.',
        S('pie', 'Helvetica', 6.5, 9, color=GRIS, align=TA_CENTER)))

    doc.build(story)
    return buf.getvalue()
