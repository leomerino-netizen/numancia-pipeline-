"""
pdf_a_texto.py — Extrae texto y estructura de PDFs de manuscritos.
Soporta: PDFs nativos (texto seleccionable) y escaneados (OCR no — solo aviso).
"""
import io
import pdfplumber
import re
from limpiador_manuscrito import limpiar_texto


def extraer_texto_pdf(pdf_bytes: bytes) -> dict:
    """
    Extrae texto de un PDF y devuelve:
      - texto: texto plano completo, ya limpio
      - paginas: número de páginas reales del PDF
      - palabras: conteo de palabras
      - tiene_texto: True si el PDF es nativo (no escaneado)
      - aviso: mensaje si el PDF parece escaneado
    """
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        n_pags = len(pdf.pages)
        textos = []
        chars_total = 0
        for p in pdf.pages:
            t = p.extract_text() or ''
            textos.append(t)
            chars_total += len(t)

        texto_bruto = '\n\n'.join(textos)
        # Si extrajo muy poco texto comparado con el número de páginas,
        # probablemente sea un PDF escaneado
        chars_por_pag = chars_total / max(1, n_pags)
        es_escaneado = chars_por_pag < 100

        if es_escaneado:
            return {
                'texto':        texto_bruto,
                'paginas_pdf':  n_pags,
                'palabras':     0,
                'tiene_texto':  False,
                'aviso':        f'El PDF parece escaneado o está hecho con imágenes ({chars_por_pag:.0f} chars/página). Se recomienda solicitar al autor el archivo en .docx.',
            }

        # Limpieza editorial
        texto_limpio, stats = limpiar_texto(texto_bruto)
        palabras = len(texto_limpio.split())

        return {
            'texto':        texto_limpio,
            'paginas_pdf':  n_pags,
            'palabras':     palabras,
            'tiene_texto':  True,
            'aviso':        '',
            'stats':        stats,
        }


def texto_a_bloques(texto: str):
    """
    Convierte texto plano limpio en lista de Bloques compatible con docx_parser.
    Estrategia robusta para PDFs:
      - Cada salto de línea es candidato a inicio de párrafo
      - Une líneas que claramente continúan (acaban sin punto + minúscula siguiente)
      - Detecta capítulos por patrón
      - Detecta diálogos por —
    """
    from docx_parser import Bloque

    cap_re   = re.compile(r"^(CAP[IÍ]TULO|Cap[ií]tulo)\s+\S", re.IGNORECASE)
    parte_re = re.compile(r"^(PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA)\s+PARTE\b|^PARTE\s+(I{1,3}|IV|V|VI{0,3}|\d+)\b", re.IGNORECASE)
    pro_re   = re.compile(r"^(PR[OÓ]LOGO|EP[IÍ]LOGO|INTRODUCCI[OÓ]N|PREFACIO|AGRADECIMIENTOS|EPIGRAFE|EP[IÍ]GRAFE)\s*$", re.IGNORECASE)
    titulo_likely_re = re.compile(r"^[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\dIVXLCDM]{2,60}$")

    # 1. Para PDFs cada \n es separador de párrafo (no hay dobles saltos fiables).
    #    Dividimos por TODOS los saltos de línea (simples o múltiples).
    parrafos_brutos = re.split(r"\n+", texto)

    # 2. Re-pegar líneas que son CLARAMENTE continuación de párrafo:
    #    la anterior no acaba en puntuación final Y la siguiente empieza con minúscula
    fin_parrafo = (".", ":", ";", "!", "?", "»", '"', "\u201d")
    parrafos = []
    for p in parrafos_brutos:
        p = p.strip()
        if not p:
            continue
        es_continuacion = (
            parrafos
            and not parrafos[-1].rstrip().endswith(fin_parrafo)
            and len(p) > 1
            and p[0].islower()
        )
        if es_continuacion:
            parrafos[-1] += " " + p
        else:
            parrafos.append(p)

    # 3. Convertir a bloques
    bloques = []
    primer_parr_de_cap = False
    titulo_visto = False

    for p in parrafos:
        p = re.sub(r"\s+", " ", p).strip()
        if not p:
            continue

        # Capítulo / parte / prólogo
        if (cap_re.match(p) or parte_re.match(p) or pro_re.match(p)) and len(p) < 100:
            bloques.append(Bloque("cap_titulo", p, p))
            primer_parr_de_cap = True
            continue

        # Línea aislada en mayúsculas que parece título de sección
        if (titulo_likely_re.match(p) and len(p) < 60
            and titulo_visto  # ya pasamos el título del libro
            and len(p.split()) <= 5):
            bloques.append(Bloque("cap_titulo", p, p))
            primer_parr_de_cap = True
            continue

        # Diálogo
        if p.startswith("—"):
            bloques.append(Bloque("dialogo", p, p,
                                  primer_parr=primer_parr_de_cap))
            primer_parr_de_cap = False
            titulo_visto = True
            continue

        # Párrafo normal
        bloques.append(Bloque("parrafo", p, p,
                              primer_parr=primer_parr_de_cap))
        primer_parr_de_cap = False
        titulo_visto = True

    return bloques


def parsear_pdf(pdf_bytes: bytes):
    """
    Devuelve un Manuscrito completo a partir de bytes de PDF.
    Compatible con la salida de docx_parser.parsear_docx.
    """
    from docx_parser import Manuscrito

    info = extraer_texto_pdf(pdf_bytes)

    if not info['tiene_texto']:
        # PDF escaneado — devolvemos manuscrito vacío con aviso
        ms = Manuscrito()
        ms.notas_autor.append(info['aviso'])
        return ms, info

    texto = info['texto']

    # Detectar título (primera línea no vacía si no es estructural)
    NO_TITULOS = {
        'PRÓLOGO','PROLOGO','INTRODUCCIÓN','INTRODUCCION',
        'EPÍLOGO','EPILOGO','CAPÍTULO','CAPITULO','PREFACIO',
        'AGRADECIMIENTOS','DEDICATORIA','ÍNDICE','INDICE',
        'NOVELA','POESÍA','POESIA','ENSAYO',
    }
    titulo = ''
    autor  = ''
    primeras = [l.strip() for l in texto.split('\n')[:15] if l.strip()]
    for i, l in enumerate(primeras):
        l_norm = l.upper().strip()
        if l_norm in NO_TITULOS or any(l_norm.startswith(p) for p in NO_TITULOS):
            continue
        if l.isupper() and 2 <= len(l) < 80:
            titulo = l
            # ¿Siguiente es autor?
            if i + 1 < len(primeras):
                sig = primeras[i+1]
                if (not sig.isupper() and len(sig) < 80
                    and sig.upper() not in NO_TITULOS):
                    autor = sig
            break

    ms = Manuscrito(titulo=titulo, autor=autor)
    ms.bloques = texto_a_bloques(texto)
    return ms, info


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'rb') as f: data = f.read()
        ms, info = parsear_pdf(data)
        print(f'Título: {ms.titulo!r}')
        print(f'Autor: {ms.autor!r}')
        print(f'Páginas PDF: {info["paginas_pdf"]}')
        print(f'Palabras: {info["palabras"]:,}')
        print(f'Bloques: {len(ms.bloques)}')
        caps = [b for b in ms.bloques if b.tipo == 'cap_titulo']
        print(f'Capítulos detectados: {len(caps)}')
        if info.get('aviso'): print(f'⚠ {info["aviso"]}')
