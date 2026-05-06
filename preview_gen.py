"""
preview_gen.py — Preview 10 páginas con marca de agua, mismo motor que maqueta_gen.
"""
import io, re, os
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, PageBreak, NextPageTemplate, HRFlowable, CondPageBreak
)
from maqueta_gen import (
    mk_frame, hdr_b, hdr_c, estilos, DropCap, _parse_texto,
    BF, BF_I, HF, HF_B, HF_I, HF_BI, CT, CG, CL, CUERPO_W,
    AW, AH, M_INT, M_EXT, M_TOP, M_BOT, _OddPageBreak,
    _pagina_creditos
)

# ── Fotos circulares de las asesoras ──────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))


def _normalizar_asesora_slug(asesora: str) -> str:
    """
    Normaliza la entrada (slug o nombre completo) al slug canónico.
    Lovable a veces manda 'laura' y otras 'Laura Vega Ugarte' — los
    aceptamos todos.
    """
    if not asesora:
        return 'laura'
    s = asesora.strip().lower()
    # Si ya es un slug válido, devolverlo
    if s in {'laura', 'debora', 'juan', 'nancy'}:
        return s
    # Si es nombre completo, detectar por la primera palabra reconocida
    if 'laura' in s:  return 'laura'
    if 'débora' in s or 'debora' in s: return 'debora'
    if 'juan'  in s:  return 'juan'
    if 'nancy' in s:  return 'nancy'
    return 'laura'  # fallback


def _foto_asesora(slug: str):
    """Devuelve el path al PNG circular de la asesora si existe, o None."""
    candidatos = [
        os.path.join(_HERE, 'fotos', f'{slug}-circ.png'),
        os.path.join(_HERE, 'fotos', f'{slug}.png'),
        os.path.join(_HERE, 'fotos', f'{slug}.jpg'),
        os.path.join(_HERE, f'{slug}-circ.png'),
    ]
    return next((p for p in candidatos if os.path.isfile(p)), None)


# ── Mapper UI Lovable → campos de _pagina_creditos ───────────────────────────
def _mapear_papel_acabado(tipo_papel: str, acabado: str):
    """
    Convierte los textos del editable de Lovable
        - tipo_papel: "Papel novela ahuesado de 80 g/m²" / "Papel offset crema 90..." / etc.
        - acabado:    "Tapa blanda con solapas, encuadernación fresada" / etc.
    en los 3 campos que espera _pagina_creditos:
        papel, cubierta_tipo, laminado
    """
    # Interior (papel del bloque) → tal cual lo seleccionó el asesor
    papel = (tipo_papel or 'Papel offset 90 g/m²').strip()

    # Cubierta + laminado → derivar del tipo de acabado
    a = (acabado or '').strip().lower()

    if 'tapa dura' in a:
        cubierta_tipo = 'Cartoné con sobrecubierta'
        laminado      = 'Laminado mate · Encuadernación cartoné'
    elif 'rústica cosida' in a or 'rustica cosida' in a or 'cosida' in a:
        cubierta_tipo = 'Cartulina 300 g/m²'
        laminado      = 'Laminado mate · Encuadernación rústica cosida'
    elif 'sin solapas' in a:
        cubierta_tipo = 'Cartulina 300 g/m²'
        laminado      = 'Laminado brillante · Encuadernación fresada'
    elif 'con solapas' in a:
        cubierta_tipo = 'Cartulina 300 g/m² con solapas'
        laminado      = 'Laminado brillante · Encuadernación fresada'
    elif a:
        # Personalizado: el asesor escribió texto libre → usarlo en cubierta
        cubierta_tipo = (acabado or 'Cartulina 300 g/m²').strip()
        laminado      = 'Encuadernación fresada'
    else:
        # Sin acabado especificado → defaults
        cubierta_tipo = 'Cartulina 300 g/m²'
        laminado      = 'Laminado brillante · Encuadernación fresada'

    return papel, cubierta_tipo, laminado


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
        # NOTA IMPORTANTE: doc.page de ReportLab parece ir 1 unidad por debajo
        # del número físico de página. Cap I empieza en física 11 → pn=10.
        # Por eso usamos umbral 10 y mostramos pn+1 como folio "humano".
        pn = doc.page
        if pn >= 10:
            c.saveState()
            c.setFont(HF, 9)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawCentredString(AW/2, 12*mm, str(pn))
            c.restoreState()
    return fn

def _wm_chap(titulo, autor):
    """Apertura de capítulo: marca de agua + folio (sin cornisa). El folio
    ya viene de _wm cuando pn >= 11."""
    def fn(c, doc):
        _wm(titulo, autor)(c, doc)
    return fn

def _wm_cab(titulo, autor):
    """Páginas normales del cuerpo: marca + folio + cornisa superior."""
    def fn(c, doc):
        _wm(titulo, autor)(c, doc)
        pn = doc.page
        if pn >= 10:
            recto = (pn % 2 == 1)
            lm = M_INT if recto else M_EXT
            rm = M_EXT  if recto else M_INT
            yh = AH - M_TOP + 4
            c.setFont(HF_I, 7.5); c.setFillColor(CG)
            if recto:
                c.drawRightString(AW-rm, yh, (titulo or '')[:50].upper())
            elif autor:
                c.drawString(lm, yh, (autor or '')[:50].upper())
            if recto or autor:
                c.setStrokeColor(CL); c.setLineWidth(0.4)
                c.line(lm, yh-2.5, AW-rm, yh-2.5)
    return fn


def generar_preview(texto: str, titulo: str, autor: str,
                    docx_bytes: bytes = None, bloques=None,
                    dedicatoria: str = '',
                    epigrafe: str = '',
                    epigrafe_autor: str = '',
                    asesora: str = 'laura',
                    tipo_papel: str = 'Papel novela ahuesado de 80 g/m²',
                    acabado: str = 'Tapa blanda con solapas, encuadernación fresada') -> bytes:
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

    # Mapear UI Lovable → campos página de créditos
    papel_creditos, cubierta_tipo_creditos, laminado_creditos = _mapear_papel_acabado(
        tipo_papel, acabado
    )
    print(f'[preview] créditos: papel={papel_creditos!r} '
          f'cubierta={cubierta_tipo_creditos!r} '
          f'laminado={laminado_creditos!r}', flush=True)

    S   = estilos()
    buf = io.BytesIO()
    wm_b    = _wm(titulo_real, autor_real)
    wm_c    = _wm_cab(titulo_real, autor_real)
    wm_chap = _wm_chap(titulo_real, autor_real)

    doc = BaseDocTemplate(buf, pagesize=A5,
        leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)

    fr_r = mk_frame(True); fr_v = mk_frame(False)

    # Frame especial para apertura de capítulo: altura reducida en 30mm
    # para garantizar aire abajo y que el folio sea visible.
    from reportlab.platypus import Frame as RFrame
    fr_chap = RFrame(
        M_INT,                                       # x
        M_BOT + 30*mm,                               # y → 30mm más arriba
        AW - M_INT - M_EXT,                          # ancho normal
        AH - M_TOP - M_BOT - 30*mm - 20*mm,          # alto: -30mm abajo, -20mm arriba (cortesía título)
        leftPadding=0, rightPadding=0,
        topPadding=20*mm,                            # 20mm sangría arriba
        bottomPadding=5*mm,                          # 5mm de margen para que ReportLab corte
        showBoundary=0)

    doc.addPageTemplates([
        PageTemplate(id='blanca',  frames=[fr_r], onPage=wm_b),
        PageTemplate(id='portad',  frames=[fr_r], onPage=wm_b),
        PageTemplate(id='portint', frames=[fr_r], onPage=wm_b),
        PageTemplate(id='cred',    frames=[fr_v], onPage=wm_b),
        PageTemplate(id='chap',    frames=[fr_r], onPage=wm_chap),
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
    # P4 créditos completos (mismo bloque que maqueta) — con papel/acabado del asesor
    story.append(NextPageTemplate('cred')); story.append(PageBreak())
    _pagina_creditos(story, titulo_real, autor_real, '2026', S,
                     papel=papel_creditos,
                     cubierta_tipo=cubierta_tipo_creditos,
                     laminado=laminado_creditos)
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
    story.append(NextPageTemplate('portad')); story.append(PageBreak())

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
    # Variables de control para apertura de capítulo
    en_cap_pagina   = False  # ¿estamos rellenando la pág apertura del cap?
    chars_cap_pag   = 0      # caracteres acumulados desde la apertura
    # En la pág apertura del cap caben ~700 caracteres por el aire superior (~25mm)
    # y la cortesía inferior (~25mm). Si superamos eso, forzamos salto.
    LIMITE_CHARS_CAP_PAG = 700
    # PREVIEW = MÍNIMO 20, MÁXIMO 30 PÁGINAS TOTAL (prelims + cuerpo)
    # Las prelims consumen 10 páginas (blancas + portadilla + créditos + portada
    # + blanca + dedi + blanca + epi + blanca). Eso deja 10-20 páginas útiles
    # de cuerpo para que el autor vea cómo se ven los primeros capítulos.
    paginas_acum    = 10.0   # prelims consumidas hasta aquí
    MIN_PAGINAS     = 20     # mínimo deseable
    MAX_PAGINAS     = 28     # tope efectivo (render real ≈ +1-2 páginas extra por blancas auto)
    PARR_POR_PAG    = 5.5
    caps_vistos     = 0

    for b in bloques:
        # Tope duro: nunca pasar de 30 páginas
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
            paginas_acum += 1.5
            # El primer capítulo ya cae en impar gracias a P10 (blanca verso epígrafe).
            # Para los siguientes, asegurar impar con OddPageBreak.
            if caps_vistos == 1:
                story.append(NextPageTemplate('chap'))
                story.append(PageBreak())
            else:
                story.append(NextPageTemplate('blanca'))
                story.append(_OddPageBreak())
                story.append(NextPageTemplate('chap'))
                story.append(PageBreak())

            # El frame especial 'chap' ya da el aire superior (25mm). Aquí solo
            # ponemos un pequeño aire visual antes del título.
            story.append(Spacer(1, 4*mm))

            m = re.match(r'^(CAP[IÍ]TULO)\s+(.+)$', tx, re.IGNORECASE)
            if m:
                story.append(Paragraph(m.group(1).upper(), S['cap_lbl']))
                story.append(Paragraph(m.group(2).upper(), S['cap_num']))
            elif re.match(r'^[IVXLCDM]{1,5}$', tx.strip()):
                # Numeral romano solo (I, II, III...) → mostrar "CAPÍTULO" + número
                story.append(Paragraph('CAPÍTULO', S['cap_lbl']))
                story.append(Paragraph(tx.strip(), S['cap_num']))
            else:
                story.append(Paragraph(tx.upper(), S['cap_lbl']))
            story.append(HRFlowable(width='14%', thickness=1, color=CG,
                                     hAlign='CENTER', spaceBefore=2, spaceAfter=8))

            # Aire post-título antes del primer párrafo
            story.append(Spacer(1, 8*mm))

            # Importante: la siguiente página del capítulo usa 'recto' (con cornisa)
            story.append(NextPageTemplate('recto'))
            en_cap = True
            # Activar control de overflow en página apertura del cap
            en_cap_pagina = True
            chars_cap_pag = 0

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

                # FIX SANGRADO INFERIOR: si el primer párrafo es muy largo,
                # solo el primer trozo (~500 chars) entra en la página apertura
                # con DropCap. El resto va como párrafo normal (que sí splitea
                # naturalmente al saltar de página).
                LIMITE_DROPCAP = 500
                if (not es_dialogo) and len(texto_limpio) > LIMITE_DROPCAP:
                    # Buscar el final de la primera frase u oración cerca del límite
                    corte = LIMITE_DROPCAP
                    for marca in ['. ', '; ', ': ']:
                        idx = texto_limpio.find(marca, LIMITE_DROPCAP - 100, LIMITE_DROPCAP + 100)
                        if idx > 0:
                            corte = idx + len(marca)
                            break
                    parte1 = texto_limpio[:corte].strip()
                    parte2 = texto_limpio[corte:].strip()
                    # Parte 1: con DropCap (entra en la apertura)
                    try:
                        story.append(DropCap(parte1, CUERPO_W, sz_cap=38, sz_body=11, ld=13.5))
                    except Exception:
                        story.append(Paragraph(parte1, S['body0']))
                    # PageBreak forzado para garantizar el aire inferior
                    if parte2:
                        story.append(PageBreak())
                        # Parte 2: párrafo normal en pág siguiente (sin sangría)
                        story.append(Paragraph(parte2, S['body0']))
                elif (not es_dialogo) and len(texto_limpio) >= 8:
                    try:
                        story.append(DropCap(hx, CUERPO_W, sz_cap=38, sz_body=11, ld=13.5))
                    except Exception:
                        story.append(Paragraph(hx, S['body0']))
                else:
                    story.append(Paragraph(hx, S['body0'] if not es_dialogo else S['dial']))
                en_cap = False
                en_cap_pagina = False  # ya gestionado el corte arriba
            elif t == 'dialogo':
                story.append(Paragraph(hx, S['dial']))
            elif b.primer_parr:
                story.append(Paragraph(hx, S['body0'])); en_cap = False
            else:
                story.append(Paragraph(hx, S['body']))
            # Estimación realista: una página A5 cabe ~1500 caracteres de prosa
            CHARS_POR_PAG = 1500
            if t == 'dialogo':
                paginas_acum += max(len(tx) / CHARS_POR_PAG, 0.05)
            else:
                paginas_acum += max(len(tx) / CHARS_POR_PAG, 0.10)

            # Si estamos en la página apertura del capítulo, contar chars
            # acumulados y forzar PageBreak antes de que el texto desborde
            # la zona de cortesía inferior (donde va el folio).
            if en_cap_pagina:
                chars_cap_pag += len(tx)
                if chars_cap_pag >= LIMITE_CHARS_CAP_PAG:
                    story.append(PageBreak())
                    en_cap_pagina = False
                    chars_cap_pag = 0

    # ─── PÁGINA MOTIVADORA FINAL (CTA comercial) ────────────────────────────
    # Normalizar el input ANTES de buscar nada
    _slug_norm = _normalizar_asesora_slug(asesora)
    try:
        from presupuesto_gen import ASESORAS
        ases = ASESORAS.get(_slug_norm, ASESORAS['laura'])
        ases_nombre = ases['nombre']
        ases_email  = ases['email']
        ases_url    = ases.get('calendario_url', '')
        # Detectar género según el slug normalizado
        es_hombre = _slug_norm == 'juan'
        ases_titulo_full = 'asesor editorial' if es_hombre else 'asesora editorial'
        ases_acomp_full  = 'tu asesor editorial' if es_hombre else 'tu asesora editorial'
    except Exception:
        ases_nombre = 'Editorial Numancia'
        ases_email  = 'info@editorialnumancia.com'
        ases_url    = 'https://printcolorweb.zohobookings.eu'
        ases_titulo_full = 'asesor/a editorial'
        ases_acomp_full  = 'tu asesor/a editorial'

    # Logo Editorial Numancia (mismo de la página de créditos)
    try:
        from maqueta_gen import LOGO_PATH
        logo_path_cta = LOGO_PATH
    except Exception:
        logo_path_cta = None

    # Foto circular de la asesora (slug ya normalizado arriba)
    asesora_slug = _slug_norm
    foto_asesora_path = _foto_asesora(asesora_slug)
    print(f'[preview] CTA: asesora_input={asesora!r} '
          f'slug={asesora_slug!r} foto={foto_asesora_path!r}', flush=True)

    # Salto a página nueva con template 'portad' (sin folio ni cornisa)
    story.append(NextPageTemplate('portad'))
    story.append(PageBreak())

    # Estilos de la página motivadora — compactos para entrar todo en 1 pág
    cta_titulo_style = ParagraphStyle(
        'cta_titulo', fontName=HF_B, fontSize=16, leading=21,
        textColor=CT, alignment=TA_CENTER,
        leftIndent=8*mm, rightIndent=8*mm)
    cta_subtitulo_style = ParagraphStyle(
        'cta_sub', fontName=HF_I, fontSize=10, leading=14,
        textColor=CG, alignment=TA_CENTER,
        leftIndent=12*mm, rightIndent=12*mm,
        spaceBefore=2*mm)
    cta_body_style = ParagraphStyle(
        'cta_body', fontName=BF, fontSize=9.5, leading=13,
        textColor=CT, alignment=TA_LEFT,
        leftIndent=12*mm, rightIndent=12*mm,
        spaceBefore=1*mm)
    cta_firma_style = ParagraphStyle(
        'cta_firma', fontName=HF_I, fontSize=9.5, leading=13,
        textColor=CT, alignment=TA_CENTER,
        spaceBefore=1*mm)

    # Saludo personalizado al autor
    autor_pila = (autor_real.split()[0] if autor_real else '').strip()
    saludo = f'Estimado/a {autor_pila}' if autor_pila else 'Estimado autor'

    story.append(Spacer(1, 6*mm))
    # ── TÍTULO MARKETINERO (frase nueva: "De manuscrito a libro publicado") ──
    story.append(Paragraph(
        'De manuscrito<br/>a libro publicado',
        cta_titulo_style))
    story.append(Paragraph(
        'Editorial Numancia te acompaña',
        cta_subtitulo_style))
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width='22%', thickness=1.0,
                             color=colors.HexColor('#A88838'),
                             hAlign='CENTER', spaceBefore=1, spaceAfter=4))
    story.append(Spacer(1, 1*mm))

    # Saludo + lead — más conciso
    story.append(Paragraph(
        f'<b>{saludo}</b>, esta muestra es solo una pequeña parte '
        f'de cómo lucirá tu obra publicada con nosotros. La versión '
        f'final <b>podrá incluir</b>:',
        cta_body_style))
    story.append(Spacer(1, 1.5*mm))

    # Beneficios — compactos, leading reducido
    beneficios_html = (
        '<font color="#A88838">▪</font> &nbsp;Maquetación profesional completa de tu manuscrito<br/>'
        '<font color="#A88838">▪</font> &nbsp;Corrección ortotipográfica según norma RAE<br/>'
        '<font color="#A88838">▪</font> &nbsp;Diseño de cubierta a medida<br/>'
        f'<font color="#A88838">▪</font> &nbsp;{tipo_papel}<br/>'
        f'<font color="#A88838">▪</font> &nbsp;{acabado}<br/>'
        '<font color="#A88838">▪</font> &nbsp;ISBN, depósito legal y registro<br/>'
        '<font color="#A88838">▪</font> &nbsp;Distribución y catálogo editorial<br/>'
        f'<font color="#A88838">▪</font> &nbsp;Acompañamiento personal de <b>{ases_nombre}</b>'
    )
    cta_lista_style = ParagraphStyle(
        'cta_lista', fontName=BF, fontSize=9, leading=12.5,
        textColor=CT, alignment=TA_LEFT,
        leftIndent=14*mm, rightIndent=12*mm)
    story.append(Paragraph(beneficios_html, cta_lista_style))
    story.append(Spacer(1, 3*mm))

    # CTA: caja destacada con enlace embebido a Zoho Bookings — compacta
    cta_caja_style = ParagraphStyle(
        'cta_caja', fontName=HF_B, fontSize=10, leading=13,
        textColor=colors.HexColor('#A88838'), alignment=TA_CENTER,
        leftIndent=14*mm, rightIndent=14*mm,
        spaceBefore=1*mm, spaceAfter=1*mm,
        borderColor=colors.HexColor('#A88838'), borderWidth=0.7,
        borderPadding=8, borderRadius=4,
        backColor=colors.HexColor('#FAF6EC'))
    cta_link_text = (
        f'<link href="{ases_url}" color="#A88838">'
        f'<b>Programa una llamada con {ases_acomp_full}</b><br/>'
        f'<font size="8.5">para comentar tu publicación y distribución</font>'
        f'</link>'
    )
    story.append(Paragraph(cta_link_text, cta_caja_style))
    story.append(Spacer(1, 3*mm))

    # ── FOTO CIRCULAR DE LA ASESORA + DATOS (compactos) ────────────────────
    if foto_asesora_path:
        try:
            from reportlab.platypus import Image as RLImage, Table, TableStyle
            foto_size = 18*mm   # antes 22mm
            foto = RLImage(foto_asesora_path,
                           width=foto_size, height=foto_size,
                           kind='proportional')
            t_foto = Table([[foto]], colWidths=[CUERPO_W])
            t_foto.setStyle(TableStyle([
                ('ALIGN',        (0,0),(-1,-1), 'CENTER'),
                ('LEFTPADDING',  (0,0),(-1,-1), 0),
                ('RIGHTPADDING', (0,0),(-1,-1), 0),
                ('TOPPADDING',   (0,0),(-1,-1), 0),
                ('BOTTOMPADDING',(0,0),(-1,-1), 0),
            ]))
            story.append(t_foto)
            story.append(Spacer(1, 1*mm))
        except Exception as e:
            print(f'[preview] error foto asesora: {e}')

    # Datos de contacto de la asesora/asesor
    story.append(Paragraph(
        f'<b>{ases_nombre}</b> &middot; <i>{ases_titulo_full}</i>',
        cta_firma_style))
    story.append(Paragraph(
        f'{ases_email}',
        ParagraphStyle('email', fontName=HF, fontSize=8.5, leading=11,
                       textColor=CT, alignment=TA_CENTER)))
    story.append(Spacer(1, 4*mm))

    # ── LOGO DE EDITORIAL NUMANCIA AL PIE (compacto) ───────────────────────
    if logo_path_cta:
        try:
            from reportlab.platypus import Image as RLImage, Table, TableStyle
            try:
                from PIL import Image as PILImage
                _w, _h = PILImage.open(logo_path_cta).size
                ratio_logo = _h / _w
            except Exception:
                ratio_logo = 337 / 1621  # fallback al ratio que conocemos
            logo_w_cta = 24*mm   # antes 28mm
            logo_h_cta = logo_w_cta * ratio_logo
            logo_img = RLImage(logo_path_cta, width=logo_w_cta, height=logo_h_cta)
            t_logo = Table([[logo_img]], colWidths=[CUERPO_W])
            t_logo.setStyle(TableStyle([
                ('ALIGN',        (0,0),(-1,-1), 'CENTER'),
                ('LEFTPADDING',  (0,0),(-1,-1), 0),
                ('RIGHTPADDING', (0,0),(-1,-1), 0),
                ('TOPPADDING',   (0,0),(-1,-1), 0),
                ('BOTTOMPADDING',(0,0),(-1,-1), 0),
            ]))
            story.append(t_logo)
        except Exception as e:
            print(f'[preview] error logo Numancia CTA: {e}')

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
            PageTemplate(id='chap',   frames=[fr_r], onPage=wm_chap),
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
