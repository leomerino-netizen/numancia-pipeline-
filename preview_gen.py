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
    AW, AH, M_INT, M_EXT, M_TOP, M_BOT, _OddPageBreak,
    _pagina_creditos
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
                    docx_bytes: bytes = None, bloques=None,
                    dedicatoria: str = '',
                    epigrafe: str = '',
                    epigrafe_autor: str = '') -> bytes:
    from docx_parser import parsear_docx, Manuscrito

    if bloques is not None:
        # Bloques pre-parseados (ej. desde PDF)
        ms = Manuscrito(titulo=titulo, autor=autor)
        ms.bloques = bloques
    elif docx_bytes:
        ms = parsear_docx(docx_bytes)
        if titulo: ms.titulo = titulo
        if autor:  ms.autor  = autor
        bloques = ms.bloques
    else:
        ms = Manuscrito(titulo=titulo, autor=autor)
        bloques = _parse_texto(texto)

    titulo_real = titulo or ms.titulo or 'Sin título'
    autor_real  = autor  or ms.autor  or ''
    # Heredar dedicatoria/epígrafe del docx si no vienen explícitos
    if not dedicatoria and getattr(ms, 'dedicatoria', None):
        dedicatoria = ' '.join(ms.dedicatoria) if isinstance(ms.dedicatoria, list) else str(ms.dedicatoria)
    if not epigrafe and getattr(ms, 'epigrafe', None):
        epigrafe = ' '.join(ms.epigrafe) if isinstance(ms.epigrafe, list) else str(ms.epigrafe)

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
    # P1 blanca (guarda exterior)
    story.append(NextPageTemplate('portad')); story.append(PageBreak())
    # P2 blanca (cortesía)
    story.append(NextPageTemplate('portad')); story.append(PageBreak())
    # P3 portadilla — solo el título, centrado vertical
    story.append(NextPageTemplate('portad'))
    story.append(Spacer(1, 75*mm))
    story.append(Paragraph(titulo_real, S['port_t']))
    # P4 créditos completos (mismo bloque que maqueta)
    story.append(NextPageTemplate('cred')); story.append(PageBreak())
    _pagina_creditos(story, titulo_real, autor_real, '2026', S)
    # P5 portada interior (autor + título + sello editorial)
    story.append(NextPageTemplate('portint')); story.append(PageBreak())
    if autor_real:
        story.append(Paragraph(autor_real, S['port_a']))
    story.append(Paragraph(titulo_real,
        ParagraphStyle('pti2', fontName=HF_B, fontSize=17, leading=22,
                       textColor=CT, alignment=TA_CENTER,
                       spaceBefore=46*mm if not autor_real else 5*mm)))
    story.append(Paragraph('▪ EN ▪', S['port_s']))
    story.append(Paragraph('Editorial Numancia', S['cred_b']))
    story.append(Paragraph('Grupo Printcolorweb.com', S['cred_g']))

    # Estilo para placeholders de páginas reservadas
    placeholder_style = ParagraphStyle(
        'placeholder', fontName=HF_I, fontSize=10, leading=14,
        textColor=CG, alignment=TA_CENTER,
        leftIndent=20*mm, rightIndent=20*mm)

    # P6 blanca (verso de portada interior)
    story.append(NextPageTemplate('portad')); story.append(PageBreak())

    # P7 página reservada para DEDICATORIA (recto/derecha)
    story.append(NextPageTemplate('portad')); story.append(PageBreak())
    if dedicatoria and str(dedicatoria).strip():
        story.append(Spacer(1, 70*mm))
        ded_style = ParagraphStyle('ded', fontName=HF_I, fontSize=11.5, leading=16,
                                    textColor=CT, alignment=TA_CENTER,
                                    leftIndent=15*mm, rightIndent=15*mm)
        story.append(Paragraph(str(dedicatoria).strip(), ded_style))
    else:
        story.append(Spacer(1, 90*mm))
        story.append(Paragraph(
            '— Página reservada para la <b>dedicatoria</b> —<br/>'
            '<font size="8">Se completará al aprobar la maquetación</font>',
            placeholder_style))

    # P8 blanca (verso de dedicatoria)
    story.append(NextPageTemplate('portad')); story.append(PageBreak())

    # P9 página reservada para EPÍGRAFE (recto/derecha)
    story.append(NextPageTemplate('portad')); story.append(PageBreak())
    if epigrafe and str(epigrafe).strip():
        story.append(Spacer(1, 70*mm))
        epi_style = ParagraphStyle('epi', fontName=HF_I, fontSize=10.5, leading=15,
                                    textColor=CT, alignment=TA_CENTER,
                                    leftIndent=20*mm, rightIndent=20*mm)
        story.append(Paragraph(f'«{str(epigrafe).strip()}»', epi_style))
        if epigrafe_autor and str(epigrafe_autor).strip():
            story.append(Spacer(1, 4*mm))
            epi_a_style = ParagraphStyle('epi_a', fontName=HF, fontSize=9, leading=12,
                                          textColor=CG, alignment=TA_CENTER)
            story.append(Paragraph(f'— {str(epigrafe_autor).strip()}', epi_a_style))
    else:
        story.append(Spacer(1, 90*mm))
        story.append(Paragraph(
            '— Página reservada para el <b>epígrafe</b> —<br/>'
            '<font size="8">Se completará al aprobar la maquetación</font>',
            placeholder_style))

    # P10 blanca (verso de epígrafe) → cuerpo arranca en P11 impar

    # Filtrar páginas en blanco al inicio de la lista (no tienen sentido
    # antes del primer contenido). Luego se procesan donde correspondan.
    while bloques and bloques[0].tipo == 'pagina_blanca':
        bloques = bloques[1:]

    # Si el primer bloque NO es un capítulo (es prólogo/párrafo suelto),
    # añadimos un PageBreak para que arranque en la siguiente página.
    # Si es cap_titulo, el propio bucle ya lo hace.
    if bloques and bloques[0].tipo != 'cap_titulo':
        story.append(NextPageTemplate('chap'))
        story.append(PageBreak())

    en_cap = False
    # Estimación de páginas A5 acumuladas para limitar el preview a 20 pág.
    paginas_acum    = 0.0
    MAX_PAGINAS     = 18     # heurística conservadora — el render puede añadir 1-2 más
    PARR_POR_PAG    = 5.5
    caps_vistos     = 0

    for b in bloques:
        if paginas_acum >= MAX_PAGINAS: break
        t = b.tipo; tx = b.texto; hx = b.html or tx

        # Página en blanco insertada manualmente por la asesora
        if t == 'pagina_blanca':
            paginas_acum += 1.0   # consume una página completa
            story.append(NextPageTemplate('blanca'))
            story.append(PageBreak())
            story.append(NextPageTemplate('recto'))
            continue

        if t == 'cap_titulo':
            caps_vistos += 1
            # Apertura de capítulo: nueva página + posible blanca par.
            # Coste estimado: 1.5 páginas (la blanca para impar + la apertura).
            paginas_acum += 1.5
            # Convención editorial PRH/Penguin/Planeta: TODOS los capítulos
            # abren SIEMPRE en página impar (recto/derecha al abrir el libro),
            # incluido el primero. Si la página actual cae par, se inserta
            # una blanca automática para forzar el salto al siguiente recto.
            story.append(NextPageTemplate('blanca'))
            story.append(PageBreak())
            story.append(_OddPageBreak())
            story.append(NextPageTemplate('chap'))

            # Espacio mínimo superior — capítulo arranca cerca del margen
            story.append(Spacer(1, 8*mm))

            m = re.match(r'^(CAP[IÍ]TULO)\s+(.+)$', tx, re.IGNORECASE)
            if m:
                story.append(Paragraph(m.group(1).upper(), S['cap_lbl']))
                story.append(Paragraph(m.group(2).upper(), S['cap_num']))
            elif re.match(r'^[IVXLCDM]{1,5}$', tx):
                story.append(Paragraph(tx, S['cap_num']))
            else:
                story.append(Paragraph(tx.upper(), S['cap_lbl']))
            story.append(HRFlowable(width='14%', thickness=1, color=CG,
                                     hAlign='CENTER', spaceBefore=2, spaceAfter=6))

            # Espacio post-título mínimo
            story.append(Spacer(1, 4*mm))

            story.append(NextPageTemplate('recto'))
            en_cap = True

        elif t == 'cap_subtitulo':
            story.append(Paragraph(hx, S['cap_sub']))

        elif t == 'separador':
            story.append(Paragraph('❧', S['orn']))

        elif t in ('parrafo', 'dialogo'):
            if b.primer_parr and en_cap:
                # DropCap solo si es un párrafo de prosa con texto suficiente
                # (no diálogo, mínimo 8 caracteres). Si no, párrafo normal.
                texto_limpio = re.sub(r'<[^>]+>', '', hx).strip()
                es_dialogo   = (t == 'dialogo') or texto_limpio.startswith('—')
                if (not es_dialogo) and len(texto_limpio) >= 8:
                    try:
                        story.append(DropCap(hx, CUERPO_W, sz_cap=38, sz_body=11, ld=13.5))
                    except Exception:
                        # Fallback: párrafo normal sin sangría
                        story.append(Paragraph(hx, S['body0']))
                else:
                    story.append(Paragraph(hx, S['body0'] if not es_dialogo else S['dial']))
                en_cap = False
            elif t == 'dialogo':
                story.append(Paragraph(hx, S['dial']))
            elif b.primer_parr:
                story.append(Paragraph(hx, S['body0'])); en_cap = False
            else:
                story.append(Paragraph(hx, S['body']))
            # Cada párrafo o diálogo consume aproximadamente 1/PARR_POR_PAG de página.
            # Diálogos cortos cuentan menos.
            if t == 'dialogo':
                paginas_acum += 1.0 / (PARR_POR_PAG * 1.5)
            else:
                # Párrafo largo cuenta como 1.5 unidades, normal 1.
                long_factor = 1.5 if len(tx) > 350 else 1.0
                paginas_acum += long_factor / PARR_POR_PAG

    try:
        doc.build(story)
        return buf.getvalue()
    except Exception as e:
        # Fallback: si falla por algún DropCap, regenerar sustituyendo
        # los DropCap por párrafos normales con small caps
        print(f'[preview] doc.build() falló: {e}. Regenerando sin DropCap...')
        story_safe = []
        for item in story:
            # Sustituir DropCap por Paragraph normal con la misma firmeza visual
            if 'DropCap' in type(item).__name__:
                try:
                    raw = re.sub(r'<[^>]+>', '', item.html).strip()
                    sc_html = (
                        f'<font name="{HF_B}" size="11">{raw[:40].upper()}</font>'
                        f'{raw[40:] if len(raw) > 40 else ""}'
                    ) if len(raw) > 40 else f'<font name="{HF_B}" size="11">{raw.upper()}</font>'
                    story_safe.append(Paragraph(sc_html, S['body0']))
                except Exception:
                    pass
            else:
                story_safe.append(item)

        # Reset doc
        buf = io.BytesIO()
        doc = BaseDocTemplate(buf, pagesize=A5,
            leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)
        fr_r = mk_frame(True); fr_v = mk_frame(False)
        doc.addPageTemplates([
            PageTemplate(id='recto',  frames=[fr_r], onPage=wm_c),
            PageTemplate(id='verso',  frames=[fr_v], onPage=wm_c),
            PageTemplate(id='blanca', frames=[fr_r], onPage=wm_b),
            PageTemplate(id='portad', frames=[fr_r], onPage=wm_b),
            PageTemplate(id='portint',frames=[fr_r], onPage=wm_b),
            PageTemplate(id='cred',   frames=[fr_r], onPage=wm_b),
            PageTemplate(id='chap',   frames=[fr_r], onPage=wm_c),
        ])
        doc.build(story_safe)
        return buf.getvalue()


if __name__ == '__main__':
    with open('/mnt/user-data/uploads/Sara.docx', 'rb') as f:
        docx_b = f.read()
    pdf = generar_preview('', 'Sara', '', docx_bytes=docx_b)
    out = '/mnt/user-data/outputs/Sara_preview.pdf'
    with open(out, 'wb') as f: f.write(pdf)
    print(f'Preview: {len(pdf)//1024} KB')
