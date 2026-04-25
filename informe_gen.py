"""
Genera el informe de viabilidad A4 PDF — estilo corporativo Editorial Numancia.
Azul #1565C0 / Blanco / Estrellas doradas
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

AZUL       = colors.HexColor('#1565C0')
AZUL_MED   = colors.HexColor('#1976D2')
AZUL_CL    = colors.HexColor('#E3F2FD')
AZUL_LINEA = colors.HexColor('#90CAF9')
NEGRO      = colors.HexColor('#1A1A1A')
GRIS       = colors.HexColor('#555555')
BLANCO     = colors.white

W_DOC = A4[0] - 36*mm


def S(name, font='Helvetica', size=8, leading=11, color=NEGRO, align=TA_LEFT, **kw):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                          textColor=color, alignment=align, **kw)


def _estrellas(pts_str):
    """
    Acepta '4/5', '★★★★☆', '4 / 5' o cualquier variante.
    Usa ★ doradas para llenas y puntos grises para vacías (máxima compatibilidad).
    """
    s = str(pts_str).strip()
    if '★' in s or '☆' in s:
        n = s.count('★')
    else:
        try:
            n = int(s.replace(' ','').split('/')[0])
        except:
            n = 0
    n = max(0, min(5, n))
    llenas = '&#9733;' * n
    # Usar guiones cortos como estrellas vacías — compatibles con todas las fuentes
    vacias = '<font color="#DDDDDD">&#9733;</font>' * (5 - n)
    return (
        f'<font name="Helvetica" size="14" color="#F9A825">{llenas}</font>'
        + vacias.replace('<font color=', '<font name="Helvetica" size="14" color=')
        + f'<br/><font name="Helvetica" size="7" color="#888888">{n}/5</font>'
    )


def _sec(txt, color=AZUL):
    t = Table([[Paragraph(
        f'<font name="Helvetica-Bold" size="7.5" color="white">{txt}</font>',
        S('sh', 'Helvetica-Bold', 7.5, 10, BLANCO))]],
        colWidths=[W_DOC])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), color),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    return t


def _kv(rows, col1=42*mm):
    data = [[Paragraph(k, S('hb','Helvetica-Bold',7.5,11,AZUL)),
             Paragraph(v, S('hn','Helvetica',7.5,11,NEGRO))] for k, v in rows]
    t = Table(data, colWidths=[col1, W_DOC - col1])
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


def generar_informe(d: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=14*mm, bottomMargin=16*mm)
    story = []

    # CABECERA
    cab = Table([[
        Paragraph('<font name="Helvetica-Bold" size="14" color="white">Editorial Numancia</font><br/>'
                  '<font name="Helvetica" size="8" color="#BBDEFB">Grupo Printcolorweb.com</font>',
                  S('x1','Helvetica',14,17,BLANCO)),
        Paragraph('<font name="Helvetica-Bold" size="8" color="white">INFORME DE VIABILIDAD EDITORIAL</font><br/>'
                  '<font name="Helvetica" size="7" color="#BBDEFB">Documento confidencial · Uso interno</font>',
                  S('x2','Helvetica',8,11,BLANCO,TA_RIGHT))
    ]], colWidths=[W_DOC*0.55, W_DOC*0.45])
    cab.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),AZUL),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
    ]))
    story.append(cab)

    meta = Table([[
        Paragraph(f'<font name="Helvetica-Bold" size="7" color="#1565C0">Asesora:</font>'
                  f' <font name="Helvetica" size="7">{d.get("evaluado_por","")}</font>',
                  S('m1','Helvetica',7,10)),
        Paragraph(f'<font name="Helvetica-Bold" size="7" color="#1565C0">Fecha:</font>'
                  f' <font name="Helvetica" size="7">{d.get("fecha","")}</font>',
                  S('m2','Helvetica',7,10,align=TA_RIGHT))
    ]], colWidths=[W_DOC*0.6, W_DOC*0.4])
    meta.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),AZUL_CL),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(meta)
    story.append(Spacer(1,6))

    # TÍTULO
    story.append(Paragraph(d.get('titulo',''),
        S('tit','Times-BoldItalic',26,30,NEGRO,spaceBefore=2)))
    story.append(Paragraph(d.get('genero',''),
        S('gen','Times-Italic',10,13,AZUL_MED,spaceBefore=2,spaceAfter=6)))
    story.append(HRFlowable(width='100%',thickness=2,color=AZUL,spaceAfter=6))

    # FICHA
    story.append(_sec('FICHA TÉCNICA'))
    story.append(_kv([
        ('Título',          d.get('titulo','')),
        ('Autor/a',         d.get('autor','')),
        ('Género',          d.get('genero','')),
        ('Extensión',       d.get('extension','')),
        ('Ambientación',    d.get('ambientacion','')),
        ('Fecha recepción', d.get('fecha','')),
        ('Evaluado por',    d.get('evaluado_por','')),
    ]))
    story.append(Spacer(1,6))

    # SINOPSIS
    story.append(_sec('SINOPSIS'))
    SIN = S('sin','Times-Italic',9.5,14,NEGRO,TA_JUSTIFY,
            leftIndent=6*mm,rightIndent=4*mm,spaceAfter=4,spaceBefore=4)
    for key in ('sinopsis_i','sinopsis_ii','sinopsis_iii'):
        if d.get(key):
            story.append(Paragraph(f'<i>{d[key]}</i>', SIN))
    story.append(Spacer(1,6))

    # EVALUACIÓN
    story.append(_sec('EVALUACIÓN EDITORIAL'))
    ev_rows = [[
        Paragraph('<font name="Helvetica-Bold" size="7.5" color="white">Criterio</font>',
                  S('eh','Helvetica-Bold',7.5,11,BLANCO)),
        Paragraph('<font name="Helvetica-Bold" size="7.5" color="white">Valoración</font>',
                  S('ep','Helvetica-Bold',7.5,11,BLANCO,TA_CENTER)),
        Paragraph('<font name="Helvetica-Bold" size="7.5" color="white">Observación</font>',
                  S('eo','Helvetica-Bold',7.5,11,BLANCO)),
    ]]
    for e in d.get('eval', []):
        ev_rows.append([
            Paragraph(e.get('criterio',''), S('ec','Helvetica-Bold',7.5,11,NEGRO)),
            Paragraph(_estrellas(e.get('estrellas','')), S('ep2','Helvetica',14,18,AZUL,TA_CENTER)),
            Paragraph(e.get('obs',''), S('eo2','Helvetica',7.5,11,GRIS)),
        ])
    ev = Table(ev_rows, colWidths=[42*mm, 32*mm, W_DOC-74*mm])
    ev.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),AZUL),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[AZUL_CL,BLANCO]),
        ('FONTSIZE',(0,0),(-1,-1),7.5),('LEADING',(0,0),(-1,-1),11),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('GRID',(0,0),(-1,-1),0.3,AZUL_LINEA),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ALIGN',(1,0),(1,-1),'CENTER'),
    ]))
    story.append(ev)
    story.append(Spacer(1,6))

    # VEREDICTO
    story.append(_sec('VEREDICTO'))
    verd = Table([
        [Paragraph(f'✓ {d.get("veredicto","CON MEJORAS")}',
                   S('vb','Helvetica-Bold',13,16,BLANCO,TA_CENTER))],
        [Paragraph(d.get('veredicto_texto',''),
                   S('vt','Helvetica',8.5,13,NEGRO,TA_JUSTIFY))],
    ], colWidths=[W_DOC])
    verd.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,0),AZUL),
        ('BACKGROUND',(0,1),(0,1),AZUL_CL),
        ('TOPPADDING',(0,0),(0,0),9),('BOTTOMPADDING',(0,0),(0,0),9),
        ('TOPPADDING',(0,1),(0,1),8),('BOTTOMPADDING',(0,1),(0,1),8),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('BOX',(0,0),(-1,-1),1.5,AZUL),
    ]))
    story.append(verd)
    story.append(Spacer(1,6))

    # PÚBLICO
    story.append(_sec('PÚBLICO OBJETIVO'))
    story.append(_kv([
        ('Lector primario',   d.get('lector_primario','')),
        ('Lector secundario', d.get('lector_secundario','')),
        ('Comparable',        d.get('comparable','')),
        ('Precio sugerido',   d.get('precio','')),
    ], col1=40*mm))
    story.append(Spacer(1,6))

    # NOTAS
    notas = d.get('notas', [])
    if notas:
        story.append(_sec('NOTAS EDITORIALES', color=colors.HexColor('#0D47A1')))
        for i, nota in enumerate(notas):
            story.append(Paragraph(
                f'<font name="Helvetica-Bold" color="#1565C0">{i+1}.</font> {nota}',
                S('nota','Helvetica',7.5,12,NEGRO,spaceBefore=3)))
        story.append(Spacer(1,8))

    # PIE
    pie = Table([[
        Paragraph('<font name="Helvetica" size="6.5" color="white">Editorial Numancia · Grupo Printcolorweb.com · Barcelona</font>',
                  S('p1','Helvetica',6.5,9,BLANCO)),
        Paragraph('<font name="Helvetica" size="6.5" color="white">Documento confidencial — uso interno exclusivo</font>',
                  S('p2','Helvetica',6.5,9,BLANCO,TA_RIGHT)),
    ]], colWidths=[W_DOC*0.6, W_DOC*0.4])
    pie.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),AZUL),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(pie)

    doc.build(story)
    return buf.getvalue()
