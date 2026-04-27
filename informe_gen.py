"""
informe_gen.py — Informe de lectura y valoración profesional Editorial Numancia.
Diseño tipo Penguin Random House / Planeta: serif elegante, cabecera crema con logo color,
evaluación expandida y carta personal de la asesora al autor.
"""
import io, os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                  TableStyle, HRFlowable, Image, KeepTogether,
                                  PageBreak)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# Paleta editorial sobria
CREMA       = colors.HexColor('#F8F4EC')   # fondo cabecera
NEGRO       = colors.HexColor('#1A1A1A')   # texto principal
GRIS_OSC    = colors.HexColor('#3A3A3A')
GRIS        = colors.HexColor('#666666')
GRIS_CL     = colors.HexColor('#B5B5B5')
GRIS_LINEA  = colors.HexColor('#D4CEC2')   # tono crema oscuro
DORADO      = colors.HexColor('#A88838')   # detalle elegante
DORADO_CL   = colors.HexColor('#E8DDB8')
ROJO_ED     = colors.HexColor('#7A1F1F')   # rojo editorial Penguin
VERDE_ED    = colors.HexColor('#1F4D2C')   # verde Planeta
BLANCO      = colors.white

_HERE = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = next((p for p in [
    os.path.join(_HERE, 'fotos', 'logo_numancia.png'),
    os.path.join(_HERE, 'logo_numancia.png'),
    os.path.join(_HERE, 'logotipo-editorial-numancia-apaisado-color-hexadecimal.png'),
    os.path.join(_HERE, 'fotos', 'logo_numancia_bn.png'),
    os.path.join(_HERE, 'logo_numancia_bn.png'),
] if os.path.isfile(p)), None)

W_DOC = A4[0] - 36*mm


def S(name, font='Helvetica', size=9, leading=12, color=NEGRO, align=TA_LEFT, **kw):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                          textColor=color, alignment=align, **kw)


# ── Estrellas elegantes (doradas + huecas grises) ─────────────────────────────
def _estrellas(pts_str):
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
    vacias = '&#9734;' * (5 - n)
    return (
        f'<font name="Helvetica" size="13" color="#A88838">{llenas}</font>'
        f'<font name="Helvetica" size="13" color="#D4CEC2">{vacias}</font>'
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
    """
    Cabecera estilo Penguin/Planeta:
    - Fondo crema con logo color a la izquierda
    - Texto elegante a la derecha
    - Sin recargos visuales
    """
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

    cab = Table([[logo, der]],
                colWidths=[W_DOC*0.50, W_DOC*0.50])
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


# ── Banda de meta (asesora · fecha · ref) ─────────────────────────────────────
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


# ── Sección elegante con título ───────────────────────────────────────────────
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


# ── Ficha técnica ─────────────────────────────────────────────────────────────
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


# ── Tabla evaluación con observaciones expandidas ─────────────────────────────
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
            Paragraph(
                f'<font name="Times-Bold" size="9.5" color="#1A1A1A">{e.get("criterio","")}</font>',
                S('ec','Times-Bold',9.5,12)),
            Paragraph(_estrellas(e.get('estrellas','0/5')),
                      S('es','Helvetica',13,16,align=TA_CENTER)),
            Paragraph(
                f'<font name="Times-Italic" size="9" color="#3A3A3A">{e.get("obs","")}</font>',
                S('eob','Times-Italic',9,12.5,GRIS_OSC,TA_JUSTIFY)),
        ])
    t = Table(rows, colWidths=[36*mm, 28*mm, W_DOC - 36*mm - 28*mm])
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


# ── Bloque veredicto ──────────────────────────────────────────────────────────
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


# ── Generador principal ───────────────────────────────────────────────────────
def generar_informe(d: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=12*mm, bottomMargin=14*mm,
        title=f"Informe de lectura · {d.get('titulo','')}",
        author='Editorial Numancia')
    story = []

    # ── 1. Cabecera editorial ────────────────────────────────────────────────
    story.append(_cabecera(d))
    story.append(_banda_meta(d))
    story.append(Spacer(1, 10))

    # ── 2. Título de la obra ─────────────────────────────────────────────────
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

    # ── 3. Ficha técnica ─────────────────────────────────────────────────────
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

    # ── 4. Sinopsis ──────────────────────────────────────────────────────────
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

    # ── 5. Evaluación editorial ──────────────────────────────────────────────
    story.append(_seccion('Evaluación editorial'))
    story.append(Spacer(1, 4))
    story.append(_tabla_evaluacion(d.get('eval', [])))
    story.append(Spacer(1, 10))

    # ── 6. Veredicto destacado ───────────────────────────────────────────────
    story.append(_bloque_veredicto(
        d.get('veredicto','CON MEJORAS'),
        d.get('veredicto_texto','')))
    story.append(Spacer(1, 12))

    # ── 7. Público objetivo y comparables ────────────────────────────────────
    story.append(_seccion('Encaje en el mercado'))
    story.append(Spacer(1, 4))
    pub = _ficha([
        ('Lector primario',   d.get('lector_primario','')),
        ('Lector secundario', d.get('lector_secundario','')),
        ('Comparables',       d.get('comparable','')),
        ('Precio sugerido',   d.get('precio','')),
    ])
    if pub: story.append(pub)
    story.append(Spacer(1, 10))

    # ── 8. Notas editoriales ─────────────────────────────────────────────────
    if d.get('notas'):
        story.append(_seccion('Notas editoriales'))
        story.append(Spacer(1, 6))
        for i, n in enumerate(d.get('notas', []), 1):
            if n:
                story.append(Paragraph(
                    f'<font name="Times-Bold" size="10" color="#A88838">{i}.</font>  '
                    f'<font name="Times-Roman" size="10" color="#1A1A1A">{n}</font>',
                    S('nt','Times-Roman',10,14,NEGRO,TA_JUSTIFY,
                      leftIndent=6*mm, spaceAfter=4)))
        story.append(Spacer(1, 12))

    # ── 9. Carta de la asesora al autor (NUEVO) ──────────────────────────────
    carta = d.get('carta_autor', '').strip()
    if carta:
        story.append(_seccion('Una nota personal para el autor'))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f'<font name="Times-Italic" size="11" color="#1A1A1A">{carta}</font>',
            S('car','Times-Italic',11,16,NEGRO,TA_JUSTIFY,
              leftIndent=8*mm, rightIndent=8*mm, spaceAfter=4)))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f'<font name="Times-Italic" size="10" color="#666666">— {d.get("evaluado_por","La asesora")}</font>',
            S('fma','Times-Italic',10,13,GRIS,TA_RIGHT,
              rightIndent=8*mm, spaceAfter=4)))
        story.append(Spacer(1, 12))

    # ── 10. Pie ──────────────────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=0.4, color=DORADO, spaceAfter=4))
    story.append(Paragraph(
        '<font name="Times-Italic" size="7.5" color="#888888">'
        'Editorial Numancia · Grupo Printcolorweb.com · C/ Numancia 187, planta -1 · 08034 Barcelona'
        '</font><br/>'
        '<font name="Helvetica" size="6.5" color="#A88838" >'
        'DOCUMENTO CONFIDENCIAL — USO INTERNO EXCLUSIVO'
        '</font>',
        S('pie','Helvetica',7.5,10,GRIS,TA_CENTER)))

    doc.build(story)
    return buf.getvalue()


if __name__ == '__main__':
    datos = {
        'titulo': 'SARA',
        'autor': 'Ángel Rodríguez Poe',
        'genero': 'Novela negra contemporánea',
        'extension': '38.362 palabras · 21 capítulos · aprox. 153 págs. A5',
        'ambientacion': 'Madrid contemporáneo, ámbitos urbanos nocturnos',
        'fecha': '27 de abril de 2026',
        'evaluado_por': 'Laura Vega Ugarte',
        'sinopsis_i': 'Sara Reyes es inspectora de Homicidios en Madrid. De lunes a viernes resuelve crímenes con la frialdad metódica de quien lleva doce años viendo cadáveres. Los sábados, en cambio, cruza la puerta de un club discreto sin nombre y se transforma en otra mujer.',
        'sinopsis_ii': 'En ese espacio donde las reglas del exterior quedan suspendidas, Sara encuentra una libertad que su vida diurna no le permite. La novela retrata con sensibilidad y crudeza los rituales de un universo invisible para la mayoría: cuerpos que se encuentran, máscaras que caen, identidades que se redefinen.',
        'sinopsis_iii': 'Hasta que una noche, alguien le habla por primera vez. Alguien que conoce las reglas pero hace tiempo que no las usa. Una novela elegante y descarnada sobre las máscaras que llevamos y los espacios donde podemos quitárnoslas.',
        'eval': [
            {'criterio': 'Originalidad',       'estrellas': '4/5',
             'obs': 'Tratamiento maduro y poco explorado en la narrativa española contemporánea del doble juego entre identidades públicas e íntimas. La protagonista funciona como espejo de muchas mujeres profesionales que se debaten entre rol social y deseo personal.'},
            {'criterio': 'Calidad narrativa',  'estrellas': '5/5',
             'obs': 'Prosa ágil, con economía descriptiva notable. La autora maneja el ritmo con maestría, alternando pasajes contemplativos y diálogos cortantes. Se nota un trabajo serio de pulido en cada escena.'},
            {'criterio': 'Estructura',         'estrellas': '4/5',
             'obs': 'Articulación clara en 21 capítulos breves que sostienen el ritmo. La alternancia entre la vida diurna y nocturna de Sara está bien dosificada. Se podría reforzar el arco final.'},
            {'criterio': 'Estilo y voz',       'estrellas': '5/5',
             'obs': 'Voz narrativa con personalidad reconocible: medida, irónica y a la vez vulnerable. El narrador consigue intimidad sin sentimentalismo. Esta es la mayor fortaleza del manuscrito.'},
            {'criterio': 'Viabilidad comercial','estrellas': '4/5',
             'obs': 'Encaje claro en el mercado de novela negra adulta con perspectiva femenina, segmento al alza en España desde el éxito de Redondo y García Sáenz. Tema con gancho mediático bien manejado.'},
        ],
        'veredicto': 'PUBLICABLE',
        'veredicto_texto': 'El manuscrito presenta una propuesta narrativa sólida, madura y comercialmente viable. La protagonista funciona como eje vertebrador y la voz narrativa sostiene el interés del lector durante toda la lectura. Editorial Numancia considera esta obra apta para integrarse en su catálogo con un proceso editorial estándar.',
        'lector_primario':   'Mujer adulta, 35-55 años, lectora habitual de narrativa contemporánea española y novela negra con perspectiva femenina',
        'lector_secundario': 'Lector general de narrativa española actual y consumidor de thriller psicológico',
        'comparable':        'Dolores Redondo · "El guardián invisible" / Eva García Sáenz · "El silencio de la ciudad blanca"',
        'precio':            '19,90 € — 21,90 € (rústica con solapas)',
        'notas': [
            'Recomiendo mantener la voz narrativa actual sin intervenciones mayores; es el principal activo del manuscrito.',
            'Sería aconsejable revisar la coherencia temporal entre los capítulos 8-12, donde se detectan dos pequeñas inconsistencias en la cronología interna.',
            'Considerar campaña dirigida a clubes de lectura femeninos y librerías independientes con enfoque en novela negra de autora.',
        ],
        'carta_autor': (
            'Ángel, leer tu manuscrito ha sido uno de esos momentos que '
            'recuerdan por qué dedicamos nuestra vida a los libros. Sara es '
            'una protagonista compleja, profundamente humana, y has construido '
            'su mundo con un cuidado que no abunda en la narrativa actual. '
            'Editorial Numancia cree firmemente en proyectos como el tuyo: '
            'voces nuevas que merecen llegar al lector con todo el respaldo '
            'editorial que la obra exige. Si decides publicar con nosotros, '
            'no editamos un libro: te acompañamos en cada paso del camino, '
            'desde la corrección final hasta la presentación pública. '
            'Estaremos encantadas de seguir conversando.'
        ),
    }
    pdf = generar_informe(datos)
    with open('/mnt/user-data/outputs/Informe_NUEVO_premium.pdf','wb') as f:
        f.write(pdf)
    print(f'PDF: {len(pdf)//1024} KB · LOGO_PATH: {LOGO_PATH}')
