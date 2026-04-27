"""
preview_gen.py — Preview 10 páginas con marca de agua, mismo motor que maqueta_gen.
"""
import io, re
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, PageBreak, NextPageTemplate, HRFlowable
)
from maqueta_gen import (
    mk_frame, hdr_b, hdr_c, estilos, DropCap, _parse_texto,
    BF, BF_I, HF, HF_B, HF_I, HF_BI, CT, CG, CL, CUERPO_W,
    AW, AH, M_INT, M_EXT, M_TOP, M_BOT
)

def _wm(titulo, autor):
    def fn(c, doc):
        c.saveState()
        c.setFont(HF_B, 22)
        c.setFillColorRGB(0.72, 0.72, 0.72, 0.16)
        c.translate(AW/2, AH/2)
        c.rotate(36)
        c.drawCentredString(0, 12, 'Editorial Numancia')
        c.setFont(HF, 7.5)
        c.drawCentredString(0, -8, 'PRUEBA DE MAQUETA — pendiente aprobación autor')
        c.restoreState()
        pn = doc.page
        if pn >= 5:
            c.setFont(HF, 7.5); c.setFillColor(CG)
            c.drawCentredString(AW/2, M_BOT-5*mm, str(pn))
    return fn

def _wm_cab(titulo, autor):
    def fn(c, doc):
        _wm(titulo, autor)(c, doc)
        pn = doc.page
        if pn >= 5:
            recto = (pn % 2 == 1)
            lm = M_INT if recto else M_EXT
            rm = M_EXT  if recto else M_INT
            yh = AH - M_TOP + 4
            c.setFont(HF_I, 7.5); c.setFillColor(CG)
            if recto:
                c.drawRightString(AW-rm, yh, titulo[:50].upper())
            elif autor:
                c.drawString(lm, yh, autor[:50].upper())
            if recto or autor:
                c.setStrokeColor(CL); c.setLineWidth(0.4)
                c.line(lm, yh-2.5, AW-rm, yh-2.5)
    return fn


def generar_preview(texto: str, titulo: str, autor: str,
                    docx_bytes: bytes = None) -> bytes:
    from docx_parser import parsear_docx, Manuscrito

    if docx_bytes:
        ms = parsear_docx(docx_bytes)
        if titulo: ms.titulo = titulo
        if autor:  ms.autor  = autor
        bloques = ms.bloques
    else:
        ms = Manuscrito(titulo=titulo, autor=autor)
        bloques = _parse_texto(texto)

    titulo_real = titulo or ms.titulo or 'Sin título'
    autor_real  = autor  or ms.autor  or ''

    S   = estilos()
    buf = io.BytesIO()
    wm_b = _wm(titulo_real, autor_real)
    wm_c = _wm_cab(titulo_real, autor_real)

    doc = BaseDocTemplate(buf, pagesize=A5,
        leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)

    fr_r = mk_frame(True); fr_v = mk_frame(False)
    doc.addPageTemplates([
        PageTemplate(id='blanca',  frames=[fr_r], onPage=wm_b),
        PageTemplate(id='portad',  frames=[fr_r], onPage=wm_b),
        PageTemplate(id='portint', frames=[fr_r], onPage=wm_b),
        PageTemplate(id='cred',    frames=[fr_v], onPage=wm_b),
        PageTemplate(id='chap',    frames=[fr_r], onPage=wm_b),
        PageTemplate(id='recto',   frames=[fr_r], onPage=wm_c),
        PageTemplate(id='verso',   frames=[fr_v], onPage=wm_c),
    ])

    story = []
    # P1 blanca
    story.append(NextPageTemplate('portad')); story.append(PageBreak())
    # P2 portadilla
    story.append(Paragraph(titulo_real, S['port_t']))
    story.append(Paragraph('novela', S['port_g']))
    story.append(NextPageTemplate('portint')); story.append(PageBreak())
    # P3 portada interior
    if autor_real:
        story.append(Paragraph(autor_real, S['port_a']))
    story.append(Paragraph(titulo_real,
        ParagraphStyle('pti2', fontName=HF_B, fontSize=17, leading=22,
                       textColor=CT, alignment=TA_CENTER,
                       spaceBefore=48*mm if not autor_real else 5*mm)))
    story.append(Paragraph('▪ EN ▪', S['port_s']))
    story.append(Paragraph('Editorial Numancia', S['cred_b']))
    story.append(Paragraph('Grupo Printcolorweb.com', S['cred_g']))
    story.append(NextPageTemplate('cred')); story.append(PageBreak())
    # P4 créditos mínimos
    story.append(Spacer(1, 38*mm))
    story.append(Paragraph('PRUEBA DE MAQUETA — documento confidencial', S['cred_b']))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('Corrección y maquetación: Editorial Numancia', S['cred']))
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph('▪ EN ▪', S['cred_b']))
    story.append(Paragraph('Editorial Numancia', S['cred_b']))
    story.append(Paragraph('Grupo Printcolorweb.com', S['cred_g']))

    # Primer capítulo
    story.append(NextPageTemplate('chap')); story.append(PageBreak())

    en_cap = False; parrs = 0; MAX_P = 90

    for b in bloques:
        if parrs >= MAX_P: break
        t = b.tipo; tx = b.texto; hx = b.html or tx

        if t == 'cap_titulo':
            if en_cap: break  # solo primer capítulo
            m = re.match(r'^(CAP[IÍ]TULO)\s+(.+)$', tx, re.IGNORECASE)
            if m:
                story.append(Paragraph(m.group(1).upper(), S['cap_lbl']))
                story.append(Paragraph(m.group(2).upper(), S['cap_num']))
            else:
                story.append(Paragraph(tx.upper(), S['cap_lbl']))
            story.append(HRFlowable(width='14%', thickness=1, color=CG,
                                     hAlign='CENTER', spaceBefore=2, spaceAfter=8))
            story.append(NextPageTemplate('recto'))
            en_cap = True

        elif t == 'cap_subtitulo':
            story.append(Paragraph(hx, S['cap_sub']))

        elif t == 'separador':
            story.append(Paragraph('❧', S['orn']))

        elif t in ('parrafo', 'dialogo'):
            if b.primer_parr and en_cap:
                story.append(DropCap(hx, CUERPO_W, sz_cap=38, sz_body=11, ld=13.5))
                en_cap = False
            elif t == 'dialogo':
                story.append(Paragraph(hx, S['dial']))
            elif b.primer_parr:
                story.append(Paragraph(hx, S['body0'])); en_cap = False
            else:
                story.append(Paragraph(hx, S['body']))
            parrs += 1

    doc.build(story)
    return buf.getvalue()


if __name__ == '__main__':
    with open('/mnt/user-data/uploads/Sara.docx', 'rb') as f:
        docx_b = f.read()
    pdf = generar_preview('', 'Sara', '', docx_bytes=docx_b)
    out = '/mnt/user-data/outputs/Sara_preview.pdf'
    with open(out, 'wb') as f: f.write(pdf)
    print(f'Preview: {len(pdf)//1024} KB')
