"""
maqueta_gen.py — Maqueta A5 según estándares Penguin Random House
Márgenes por sección áurea, Lora 11/13.5, small caps, drop cap 3 líneas,
control viudas/huérfanas, folios esquinas exteriores.
"""
import io, re, os
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
pt = 1  # 1 point = 1 reportlab unit
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, PageBreak, NextPageTemplate, HRFlowable, Image, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ── Fuentes built-in ReportLab (funcionan siempre, sin TTF externos) ─────────
# Intentar Lora/LiberationSerif para uso local; si fallan, usar Times/Helvetica
def _try_reg(n, p):
    try:
        pdfmetrics.registerFont(TTFont(n, p))
        return True
    except: return False

_LORA = (_try_reg('LoraTTF',   '/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf') and
         _try_reg('LoraTTF-I', '/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf'))
_LS   = (_try_reg('LSerifTTF', '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf') and
         _try_reg('LSerifTTF-B','/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf') and
         _try_reg('LSerifTTF-I','/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf') and
         _try_reg('LSerifTTF-BI','/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf'))

if _LORA and _LS:
    # Local: usar Lora/LiberationSerif
    BF, BF_I            = 'LoraTTF', 'LoraTTF-I'
    HF, HF_B, HF_I, HF_BI = 'LSerifTTF', 'LSerifTTF-B', 'LSerifTTF-I', 'LSerifTTF-BI'
    try:
        registerFontFamily('LoraTTF',   normal=BF, bold=HF_B, italic=BF_I, boldItalic=HF_BI)
        registerFontFamily('LSerifTTF', normal=HF, bold=HF_B, italic=HF_I, boldItalic=HF_BI)
    except: pass
else:
    # Producción Railway: built-in ReportLab (Times + Helvetica)
    BF                    = 'Times-Roman'
    BF_I                  = 'Times-Italic'
    HF                    = 'Times-Roman'
    HF_B                  = 'Times-Bold'
    HF_I                  = 'Times-Italic'
    HF_BI                 = 'Times-BoldItalic'
    # Las familias Times y Helvetica YA están registradas por defecto en ReportLab

# ── Dimensiones PRH / A5 ─────────────────────────────────────────────────────
AW, AH   = A5                  # 419.5 × 595.3 pt  (148 × 210 mm)
M_INT    = 22 * mm             # lomo — facilita lectura cerca del pliegue
M_EXT    = 20 * mm             # exterior
M_TOP    = 20 * mm             # superior
M_BOT    = 25 * mm             # inferior > exterior > superior > interior (PRH)
HDR_H    =  6 * mm             # espacio para cornisa superior
FTR_H    =  8 * mm             # espacio para folio inferior

# Caja tipográfica resultante
CUERPO_W = AW - M_INT - M_EXT  # ≈ 106mm — 300pt
CUERPO_H = AH - M_TOP - M_BOT  # ≈ 165mm — 467pt

# Tipografía — simulación Garamond/Sabon con Lora
FS_BODY  = 11          # tamaño cuerpo
LD_BODY  = 13.5        # leading 13.5pt (ratio 1.23 — estándar PRH)
INDENT   = 5 * mm      # sangría 5mm (PRH)
SC_SIZE  = 8.5         # small caps simuladas

# Líneas por página = CUERPO_H / LD_BODY ≈ 34 líneas
LINEAS_PAG = int((CUERPO_H) / (LD_BODY * mm / pt))

# Colores
CT = colors.HexColor('#1A1A1A')
CG = colors.HexColor('#5A5A5A')
CL = colors.HexColor('#C0C0C0')
CO = colors.HexColor('#4A4A4A')


_HERE     = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = next((p for p in [
    os.path.join(_HERE, 'fotos', 'logo_numancia_bn.png'),   # B&N para créditos
    os.path.join(_HERE, 'fotos', 'logo_numancia.png'),
    os.path.join(_HERE, 'logo_numancia.png'),
    os.path.join(_HERE, 'logotipo-editorial-numancia-apaisado-color-hexadecimal.png'),
] if os.path.isfile(p)), None)


# ── Small caps helper ─────────────────────────────────────────────────────────
def _small_caps(texto: str, size: float = SC_SIZE) -> str:
    """
    Simula versalitas: primeras palabras en mayúsculas a tamaño reducido.
    Se aplica hasta el primer punto, coma larga o ~50 caracteres.
    """
    raw = re.sub(r'<[^>]+>', '', texto).strip()
    # Cortar en el primer punto o tras ~50 chars (máx primera frase corta)
    m = re.search(r'[.,:;]', raw[:60])
    corte = m.start() if m else min(len(raw), 55)
    parte_sc   = raw[:corte].upper()
    parte_rest = raw[corte:]
    sc_html = (f'<font name="{HF_B}" size="{size}" '
               f'color="#1A1A1A">{parte_sc}</font>')
    return sc_html + parte_rest


# ── Drop Cap PRH ──────────────────────────────────────────────────────────────
class DropCap(Flowable):
    """
    Capitular de 3 líneas (PRH) + small caps en la apertura del párrafo.
    El flowable reserva exactamente 3×leading para que no haya solapamiento.
    """
    def __init__(self, html: str, ancho: float,
                 sz_cap: float = 38, sz_body: float = FS_BODY,
                 ld: float = LD_BODY, small_caps: bool = True):
        super().__init__()
        self.html       = html
        self.ancho      = ancho
        self.sz_cap     = sz_cap
        self.sz_body    = sz_body
        self.ld         = ld
        self.small_caps = small_caps
        # Alto = 3 líneas exactas (PRH: drop cap de 3 líneas)
        self._3lines    = 3 * ld

    def wrap(self, aw, ah):
        self._aw  = aw
        cap_w     = self.sz_cap * 0.66
        mx        = cap_w + 2 * mm
        aw2       = self.ancho - mx

        # Preparar texto con small caps si procede
        raw  = re.sub(r'<[^>]+>', '', self.html).strip()
        if not raw:
            self._total = self._3lines
            return aw, self._3lines

        resto_html = self._build_resto(raw)
        from reportlab.platypus import Paragraph as RP
        from reportlab.lib.styles import ParagraphStyle as RPS
        st = RPS('dc_w', fontName=BF, fontSize=self.sz_body, leading=self.ld,
                 textColor=CT, alignment=TA_JUSTIFY, firstLineIndent=0)
        _, h = RP(resto_html, st).wrap(aw2, 400)
        self._total = max(self._3lines, h)
        self._h_resto = h
        return aw, self._total

    def _build_resto(self, raw: str) -> str:
        """Texto del párrafo (sin la 1ª letra) con small caps iniciales."""
        body = raw[1:] if raw else ''
        if not self.small_caps or not body:
            return body
        # Small caps para las primeras palabras (hasta primer punto o ~50 chars)
        m = re.search(r'[.,;]', body[:60])
        corte = m.start() if m else min(len(body), 50)
        sc   = f'<font name="{HF_B}" size="{SC_SIZE}">{body[:corte].upper()}</font>'
        rest = body[corte:]
        return sc + rest

    def draw(self):
        c   = self.canv
        raw = re.sub(r'<[^>]+>', '', self.html).strip()
        if not raw: return

        letra = raw[0]
        cap_w = self.sz_cap * 0.66
        mx    = cap_w + 2 * mm
        aw2   = self.ancho - mx

        # Letra capital — base alineada con baseline de 1ª línea
        # En PRH: la capital tiene la base a la misma altura que la línea 1 de texto
        baseline = self._total - self.ld  # ≈ altura 1ª línea desde la base del flowable
        c.saveState()
        c.setFont(HF_B, self.sz_cap)
        c.setFillColor(CT)
        # Ajuste fino: capital ligeramente baja para alinearse con baseline
        c.drawString(0, baseline - self.sz_cap * 0.12, letra)
        c.restoreStore = c.restoreState
        c.restoreState()

        # Texto junto a la capital
        resto = self._build_resto(raw)
        from reportlab.platypus import Paragraph as RP
        from reportlab.lib.styles import ParagraphStyle as RPS
        st = RPS('dc_d', fontName=BF, fontSize=self.sz_body, leading=self.ld,
                 textColor=CT, alignment=TA_JUSTIFY, firstLineIndent=0)
        p   = RP(resto, st)
        _, h = p.wrap(aw2, 400)
        p.drawOn(c, mx, self._total - h)


# ── Estilos tipográficos PRH ──────────────────────────────────────────────────
def S(nm, fn=BF, fs=FS_BODY, ld=LD_BODY, cl=None, al=TA_JUSTIFY, **kw):
    return ParagraphStyle(
        nm, fontName=fn, fontSize=fs, leading=ld,
        textColor=cl or CT, alignment=al,
        allowWidows=0, allowOrphans=0,   # PRH: prohibido viudas y huérfanas
        **kw)

def estilos():
    return {
    # ── Cuerpo ────────────────────────────────────────────────────────────────
    'body':    S('body',  firstLineIndent=INDENT),
    'body0':   S('body0', firstLineIndent=0),      # post-cap o inicio sección
    'dial':    S('dial',  firstLineIndent=0),       # diálogos: sin sangría

    # ── Capítulos ─────────────────────────────────────────────────────────────
    'cap_lbl': S('cap_lbl', HF, 8, 11, CG, TA_CENTER,
                 spaceBefore=30*mm, spaceAfter=1.5*mm, letterSpacing=4),
    'cap_num': S('cap_num', HF_B, 28, 34, CT, TA_CENTER,
                 spaceBefore=2*mm, spaceAfter=3*mm),
    'cap_sub': S('cap_sub', HF_I, 10, 14, CG, TA_CENTER,
                 spaceBefore=0, spaceAfter=10*mm),

    # ── Portadas ──────────────────────────────────────────────────────────────
    'port_t':  S('port_t',  HF_B, 22, 28, CT, TA_CENTER, spaceBefore=46*mm),
    'port_g':  S('port_g',  HF_I, 9,  13, CG, TA_CENTER, spaceBefore=4*mm),
    'port_a':  S('port_a',  HF,        11, 14, CT, TA_CENTER, spaceBefore=38*mm),
    'port_s':  S('port_s',  HF_B, 8,  11, CT, TA_CENTER, spaceBefore=42*mm),

    # ── Créditos ──────────────────────────────────────────────────────────────
    'cred':    S('cred',   BF,  7.5, 11, CT, TA_CENTER, spaceAfter=2),
    'cred_b':  S('cred_b', HF,  7.5, 11, CT, TA_CENTER, spaceAfter=2),
    'cred_g':  S('cred_g', BF,  7,   10, CG, TA_CENTER),

    # ── Prelims literarios ────────────────────────────────────────────────────
    'ded':     S('ded',  BF_I, 10.5, 15, CT, TA_RIGHT,
                 rightIndent=6*mm, spaceBefore=32*mm, spaceAfter=4),
    'epi':     S('epi',  BF_I, 10,   14, CT, TA_RIGHT,
                 rightIndent=6*mm, leftIndent=16*mm, spaceBefore=32*mm, spaceAfter=3),
    'epi_a':   S('epi_a', HF, 8.5, 12, CG, TA_RIGHT,
                 rightIndent=6*mm, spaceAfter=2),

    # ── Separador ornamental ──────────────────────────────────────────────────
    'orn':     S('orn', BF, 12, 18, CO, TA_CENTER, spaceBefore=4, spaceAfter=4),

    # ── Colofón ───────────────────────────────────────────────────────────────
    'col_i':   S('col_i', BF_I, 8, 12, CG, TA_CENTER),
    'col_b':   S('col_b', HF_B, 8, 11, CT, TA_CENTER),
    }


# ── Frames ────────────────────────────────────────────────────────────────────
def mk_frame(recto: bool):
    lm = M_INT if recto else M_EXT
    rm = M_EXT  if recto else M_INT
    return Frame(lm, M_BOT, AW-lm-rm, AH-M_TOP-M_BOT,
                 leftPadding=0, rightPadding=0,
                 topPadding=HDR_H, bottomPadding=FTR_H,
                 showBoundary=0)


# ── Cornisa PRH ───────────────────────────────────────────────────────────────
# Folio en esquina exterior inferior  (PRH standard)
# Título en recto superior exterior, autor en verso superior exterior

def hdr_r(titulo: str):
    """Recto: título en cornisa superior exterior + folio centrado inferior."""
    def fn(c, doc):
        pn = doc.page
        if pn < 7: return
        # Título en cornisa superior exterior (derecha en recto)
        yh = AH - M_TOP + 5
        c.setFont(HF_I, 7.5); c.setFillColor(CG)
        c.drawRightString(AW - M_EXT, yh, titulo[:48].upper())
        c.setStrokeColor(CL); c.setLineWidth(0.35)
        c.line(M_INT, yh - 3, AW - M_EXT, yh - 3)
        # Folio centrado en pie — discreto (Penguin/PRH)
        c.setFont(HF, 8); c.setFillColor(CG)
        c.drawCentredString(AW/2, M_BOT - FTR_H + 2*mm, str(pn))
    return fn

def hdr_v(autor: str):
    """Verso: autor en cornisa superior exterior + folio centrado inferior."""
    def fn(c, doc):
        pn = doc.page
        if pn < 7: return
        yh = AH - M_TOP + 5
        if autor:
            c.setFont(HF_I, 7.5); c.setFillColor(CG)
            c.drawString(M_EXT, yh, autor[:48].upper())
            c.setStrokeColor(CL); c.setLineWidth(0.35)
            c.line(M_EXT, yh - 3, AW - M_INT, yh - 3)
        # Folio centrado en pie — discreto (Penguin/PRH)
        c.setFont(HF, 8); c.setFillColor(CG)
        c.drawCentredString(AW/2, M_BOT - FTR_H + 2*mm, str(pn))
    return fn

def hdr_c(c, doc):
    """Página de capítulo: folio centrado inferior discreto."""
    pn = doc.page
    if pn >= 7:
        c.setFont(HF, 8); c.setFillColor(CG)
        c.drawCentredString(AW/2, M_BOT - FTR_H + 2*mm, str(pn))

def hdr_b(c, doc): pass


# ── Página de créditos con logo ───────────────────────────────────────────────
def _pagina_creditos(story, titulo, autor, anyo, S,
                     papel='Papel offset 90 g/m²',
                     cubierta_tipo='Cartulina 300 g/m²',
                     laminado='Laminado brillante',
                     isbn='', deposito_legal=''):
    story.append(Spacer(1, 6*mm))

    if LOGO_PATH:
        try:
            logo_h = 10*mm
            logo_w = min(logo_h * (1621/337), CUERPO_W * 0.58)
            img    = Image(LOGO_PATH, width=logo_w, height=logo_h)
            from reportlab.platypus import Table, TableStyle
            t = Table([[img]], colWidths=[CUERPO_W])
            t.setStyle(TableStyle([
                ('ALIGN',(0,0),(-1,-1),'CENTER'),
                ('LEFTPADDING',(0,0),(-1,-1),0),
                ('RIGHTPADDING',(0,0),(-1,-1),0),
                ('TOPPADDING',(0,0),(-1,-1),0),
                ('BOTTOMPADDING',(0,0),(-1,-1),0),
            ]))
            story.append(t)
        except Exception:
            story.append(Paragraph('▪ EN ▪', S['cred_b']))
            story.append(Paragraph('Editorial Numancia', S['cred_b']))
    else:
        story.append(Paragraph('▪ EN ▪', S['cred_b']))
        story.append(Paragraph('Editorial Numancia', S['cred_b']))

    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width='55%', thickness=0.4,
                             color=CL, hAlign='CENTER', spaceAfter=5))

    story.append(Paragraph(f'Primera edición: {anyo}', S['cred_b']))
    if autor:
        story.append(Paragraph(f'© {anyo}, {autor}', S['cred_b']))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph(
        'Todos los derechos reservados. Queda rigurosamente '
        'prohibida, sin la autorización escrita de los titulares '
        'del copyright, bajo las sanciones establecidas en las leyes, '
        'la reproducción total o parcial de esta obra por cualquier '
        'medio o procedimiento, ya sea electrónico o mecánico, '
        'el tratamiento informático, el alquiler o cualquier otra '
        'forma de cesión de la obra.',
        ParagraphStyle('leg', fontName=BF, fontSize=6.8, leading=9.5,
                       textColor=CG, alignment=TA_JUSTIFY)))

    story.append(Spacer(1, 4*mm))
    isbn_txt = isbn.strip() if isbn else ''
    dl_txt   = deposito_legal.strip() if deposito_legal else ''
    story.append(Paragraph(f'ISBN: {isbn_txt}' if isbn_txt else 'ISBN: Pendiente de asignación', S['cred_b']))
    story.append(Paragraph(f'Depósito Legal: {dl_txt}' if dl_txt else 'Depósito Legal: Pendiente de asignación', S['cred_b']))

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Corrección y maquetación: Editorial Numancia', S['cred']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('Editado por Editorial Numancia', S['cred_b']))
    story.append(Paragraph('Grupo Printcolorweb.com · Barcelona', S['cred_g']))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('Impreso por Fullcolor Printcolor, S.L.', S['cred_b']))
    story.append(Paragraph('C/ Numancia 187, planta -1 · 08034 Barcelona', S['cred_g']))

    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width='35%', thickness=0.4,
                             color=CL, hAlign='CENTER', spaceAfter=4))
    story.append(Paragraph(
        f'Interior: {papel} · Cubierta: {cubierta_tipo}',
        S['cred_g']))
    story.append(Paragraph(
        f'{laminado} · Encuadernación fresada · Impresión digital',
        S['cred_g']))


# ── Prelims ───────────────────────────────────────────────────────────────────
def prelims(story, titulo, autor, anyo, deds, epis, epi_autor, S,
            papel='Papel offset 90 g/m²',
            cubierta_tipo='Cartulina 300 g/m²',
            laminado='Laminado brillante',
            isbn='', deposito_legal=''):

    story.append(NextPageTemplate('portad')); story.append(PageBreak())
    story.append(Paragraph(titulo, S['port_t']))
    story.append(Paragraph('novela', S['port_g']))

    story.append(NextPageTemplate('portint')); story.append(PageBreak())
    if autor:
        story.append(Paragraph(autor, S['port_a']))
    story.append(Paragraph(titulo,
        ParagraphStyle('ti2', fontName=HF_B, fontSize=17, leading=22,
                       textColor=CT, alignment=TA_CENTER,
                       spaceBefore=46*mm if not autor else 5*mm)))
    story.append(Paragraph('▪ EN ▪', S['port_s']))
    story.append(Paragraph('Editorial Numancia', S['cred_b']))
    story.append(Paragraph('Grupo Printcolorweb.com', S['cred_g']))

    story.append(NextPageTemplate('cred')); story.append(PageBreak())
    _pagina_creditos(story, titulo, autor, anyo, S, papel, cubierta_tipo, laminado,
                     isbn=isbn, deposito_legal=deposito_legal)

    story.append(NextPageTemplate('ded')); story.append(PageBreak())
    for d in deds:
        story.append(Paragraph(d, S['ded']))

    story.append(NextPageTemplate('epi')); story.append(PageBreak())
    for e in epis:
        story.append(Paragraph(e, S['epi']))
    if epi_autor:
        story.append(Paragraph(f'— {epi_autor}', S['epi_a']))


# ── Cuerpo ────────────────────────────────────────────────────────────────────
def cuerpo(story, bloques, S):
    en_cap = False

    for b in bloques:
        t  = b.tipo
        tx = b.texto
        hx = b.html or tx

        if t == 'cap_titulo':
            # Convención editorial PRH/Penguin: cada capítulo abre en página
            # impar (recto/derecha). Si la página actual es par, dejamos blanca
            # la siguiente (sin numeración visible — usa template 'blank').
            story.append(NextPageTemplate('blank'))
            story.append(PageBreak())
            story.append(NextPageTemplate('chap'))
            story.append(_OddPageBreak())

            # Espacio de cortesía superior — el título "respira" en la apertura
            story.append(Spacer(1, 28*mm))

            m = re.match(r'^(CAP[IÍ]TULO)\s+(.+)$', tx, re.IGNORECASE)
            if m:
                story.append(Paragraph(m.group(1).upper(), S['cap_lbl']))
                story.append(Paragraph(m.group(2).upper(), S['cap_num']))
            elif re.match(r'^[IVXLCDM]{1,5}$', tx):
                story.append(Paragraph(tx, S['cap_num']))
            else:
                story.append(Paragraph(tx.upper(), S['cap_lbl']))
            story.append(HRFlowable(width='12%', thickness=0.8, color=CG,
                                     hAlign='CENTER', spaceBefore=3, spaceAfter=10))

            # Aire post-título antes del primer párrafo
            story.append(Spacer(1, 8*mm))

            story.append(NextPageTemplate('recto'))
            en_cap = True

        elif t == 'cap_subtitulo':
            story.append(Paragraph(hx, S['cap_sub']))

        elif t == 'separador':
            story.append(Paragraph('❧', S['orn']))

        elif t in ('parrafo', 'dialogo'):
            if b.primer_parr and en_cap:
                # Drop cap PRH con small caps — solo si es prosa con texto suficiente
                texto_limpio = re.sub(r'<[^>]+>', '', hx).strip()
                es_dialogo   = (t == 'dialogo') or texto_limpio.startswith('—')
                if (not es_dialogo) and len(texto_limpio) >= 8:
                    try:
                        dc = DropCap(hx, CUERPO_W, sz_cap=38,
                                     sz_body=FS_BODY, ld=LD_BODY, small_caps=True)
                        story.append(dc)
                    except Exception:
                        story.append(Paragraph(hx, S['body0']))
                else:
                    story.append(Paragraph(hx, S['body0'] if not es_dialogo else S['dial']))
                en_cap = False

            elif t == 'dialogo':
                story.append(Paragraph(hx, S['dial']))

            elif b.primer_parr:
                # Primer párrafo sin drop cap (tras separador, etc.)
                raw = re.sub(r'<[^>]+>', '', hx).strip()
                sc_html = _small_caps(raw)
                story.append(Paragraph(sc_html, S['body0']))
                en_cap = False

            else:
                story.append(Paragraph(hx, S['body']))


# ── Colofón ───────────────────────────────────────────────────────────────────
def colofonBloque(story, titulo, anyo, S):
    story.append(NextPageTemplate('colofon'))
    story.append(PageBreak())
    story.append(Spacer(1, 80*mm))
    story.append(HRFlowable(width='28%', thickness=0.5, color=CL,
                             hAlign='CENTER', spaceAfter=8))
    story.append(Paragraph(
        f'<i>{titulo}</i> se terminó de imprimir en {anyo}.<br/>'
        f'Impreso en España por Fullcolor Printcolor, S.L.',
        S['col_i']))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph('▪ EN ▪', S['col_b']))
    story.append(Paragraph('Editorial Numancia · Grupo Printcolorweb.com',
        ParagraphStyle('cg2', fontName=BF, fontSize=7, leading=10,
                       textColor=CG, alignment=TA_CENTER)))


# ── API principal ─────────────────────────────────────────────────────────────
def generar_maqueta_completa(
    texto: str = '',
    titulo: str = '',
    autor: str = '',
    anyo: str = '2026',
    dedicatoria: str = '',
    epigrafe: str = '',
    epigrafe_autor: str = '',
    docx_bytes: bytes = None,
    papel: str = 'Papel offset 90 g/m²',
    cubierta_tipo: str = 'Cartulina 300 g/m²',
    laminado: str = 'Laminado brillante',
    isbn: str = '',
    deposito_legal: str = '',
) -> bytes:
    from docx_parser import parsear_docx, Manuscrito

    if docx_bytes:
        ms     = parsear_docx(docx_bytes)
        if titulo: ms.titulo = titulo
        if autor:  ms.autor  = autor
        bloques = ms.bloques
        deds    = ms.dedicatoria or ([dedicatoria] if dedicatoria else [])
        epis    = ms.epigrafe    or ([epigrafe]    if epigrafe    else [])
        epi_a   = ms.epigrafe_autor or epigrafe_autor
    else:
        ms      = Manuscrito(titulo=titulo, autor=autor)
        bloques = _parse_texto(texto)
        deds    = [dedicatoria] if dedicatoria else []
        epis    = [epigrafe]    if epigrafe    else []
        epi_a   = epigrafe_autor

    titulo_real = titulo or ms.titulo or 'Sin título'
    autor_real  = autor  or ms.autor  or ''

    S    = estilos()
    buf  = io.BytesIO()
    on_r = hdr_r(titulo_real)
    on_v = hdr_v(autor_real)

    doc = BaseDocTemplate(buf, pagesize=A5,
        leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)

    fr_r = mk_frame(True); fr_v = mk_frame(False)
    doc.addPageTemplates([
        PageTemplate(id='blank',   frames=[fr_r], onPage=hdr_b),
        PageTemplate(id='portad',  frames=[fr_r], onPage=hdr_b),
        PageTemplate(id='portint', frames=[fr_r], onPage=hdr_b),
        PageTemplate(id='cred',    frames=[fr_v], onPage=hdr_b),
        PageTemplate(id='ded',     frames=[fr_r], onPage=hdr_b),
        PageTemplate(id='epi',     frames=[fr_v], onPage=hdr_b),
        PageTemplate(id='chap',    frames=[fr_r], onPage=hdr_c),
        PageTemplate(id='recto',   frames=[fr_r], onPage=on_r),
        PageTemplate(id='verso',   frames=[fr_v], onPage=on_v),
        PageTemplate(id='colofon', frames=[fr_r], onPage=hdr_b),
    ])

    story = []
    prelims(story, titulo_real, autor_real, anyo,
            deds, epis, epi_a, S, papel, cubierta_tipo, laminado,
            isbn=isbn, deposito_legal=deposito_legal)
    story.append(NextPageTemplate('chap'))
    story.append(PageBreak())
    cuerpo(story, bloques, S)
    colofonBloque(story, titulo_real, anyo, S)
    doc.build(story)
    return buf.getvalue()


def _parse_texto(texto: str):
    from docx_parser import Bloque
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    cap_re = re.compile(r'^(CAP[IÍ]TULO\s+\w[\w\s]{0,30})', re.IGNORECASE)
    cap_s  = re.compile(r'^Cap[ií]tulo\s+[\w]+\s*$', re.IGNORECASE)
    cap_p  = re.compile(r'^Cap[ií]tulo\s+\d+\.\s+\S', re.IGNORECASE)
    bloques = []; contenido = False; primer = True; i = 0
    while i < len(lineas):
        l = lineas[i]
        if '\t' in l: i += 1; continue
        es_cap = False; cn = ''; cs = ''
        if cap_s.match(l) and len(l) < 40:
            cn = l; cs = lineas[i+1] if i+1<len(lineas) and '\t' not in lineas[i+1] else ''
            es_cap = True; i += 2 if cs else 1
        elif cap_p.match(l) and len(l) < 100:
            pts = re.split(r'\.\s+', l, 1); cn = pts[0]; cs = pts[1] if len(pts)>1 else ''
            es_cap = True; i += 1
        elif cap_re.match(l) and len(l) < 80:
            pts = re.split(r'\s*[—\-–]\s*', l, 1); cn = pts[0]; cs = pts[1] if len(pts)>1 else ''
            es_cap = True; i += 1
        else: i += 1
        if es_cap:
            contenido = True; primer = True
            bloques.append(Bloque('cap_titulo', cn.strip(), cn.strip()))
            if cs: bloques.append(Bloque('cap_subtitulo', cs.strip(), cs.strip()))
        elif contenido:
            tipo = 'dialogo' if l.startswith(('—','\u2014')) else 'parrafo'
            bloques.append(Bloque(tipo, l, l, primer_parr=primer)); primer = False
    return bloques


class OddPageBreak(Flowable):
    """
    Fuerza que el siguiente contenido comience en página impar (recto/derecha).
    Si la próxima página sería par, inserta una página en blanco antes.
    Convención editorial estándar PRH/Penguin/Planeta para capítulos.
    """
    width = 0
    height = 0
    def draw(self): pass
    def wrap(self, aw, ah):
        return (0, 0)


def _forzar_impar(story):
    """
    Inserta page breaks suficientes para que el siguiente contenido
    aparezca en página impar. Se evalúa en tiempo de build.
    """
    # Estrategia simple: PageBreak siempre + un OddPageMarker que en build
    # agregará otro PageBreak si quedó en par.
    story.append(_OddBreakSentinel())


class _OddPageBreak(Flowable):
    """
    Si la página actual es PAR (verso), inserta un page break para que
    el siguiente flowable (capítulo) caiga en página IMPAR (recto).
    """
    _ZeroSize = True
    def __init__(self):
        Flowable.__init__(self)
        self.width = 0
        self.height = 0

    def wrap(self, aw, ah):
        return (aw, 0)

    def drawOn(self, canvas, x, y, _sW=0):
        # Comprobar paridad de página actual
        try:
            pn = canvas.getPageNumber()
        except:
            pn = 1
        # Si la página DONDE estamos imprimiendo es par, no necesitamos nada
        # (el siguiente PageBreak nos llevará a impar).
        # Si es impar, el siguiente PageBreak nos llevaría a par → forzamos otro
        # Pero en este punto ya hemos tenido un PageBreak antes, así que:
        # - Si pn es impar: ya estamos donde queremos
        # - Si pn es par: necesitamos saltar una más
        if pn % 2 == 0:
            try:
                canvas.showPage()
            except: pass

    def draw(self):
        pass


_OddBreakSentinel = _OddPageBreak


if __name__ == '__main__':
    with open('/mnt/user-data/uploads/Sara.docx', 'rb') as f:
        docx_b = f.read()
    pdf = generar_maqueta_completa(
        titulo='Sara', autor='', anyo='2025',
        docx_bytes=docx_b,
        papel='Papel novela 80 g/m²',
        cubierta_tipo='Cartulina 300 g/m²',
        laminado='Laminado brillante',
    )
    with open('/mnt/user-data/outputs/Sara_maqueta_PRH.pdf', 'wb') as f:
        f.write(pdf)
    print(f'PDF PRH: {len(pdf)//1024} KB — {LINEAS_PAG} líneas/página teóricas')
