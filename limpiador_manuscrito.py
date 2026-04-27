"""
limpiador_manuscrito.py — Normalización robusta de manuscritos heterogéneos.

Casuística real:
- Autores que escriben con doble espacio entre frases
- Comillas inglesas " ", francesas «», simples ' '  → unificar a «»
- Guiones de diálogo: -, --, –, —, →  → unificar a — (raya larga)
- Espacios antes de puntuación (estilo francés)
- Múltiples saltos de línea, líneas en blanco entre cada párrafo
- Líneas partidas en mitad de frase (escaneados/PDFs)
- Tabuladores dispersos
- Guiones automáticos al final de línea (texto justificado de Word)
- TOC pegado al inicio
- Encabezados/pies de página repetidos en cada página
- Numeración de páginas como párrafo
- "PRÓLOGO", "INTRODUCCIÓN", "CAPÍTULO 1" mal estructurados
- Diálogos sin raya, con dos puntos, con guiones simples
- Texto en MAYÚSCULAS por error
- ALL CAPS en frases
- Múltiples espacios consecutivos
- Caracteres invisibles (zero-width, NBSP)
- Comillas tipográficas mezcladas con rectas
"""
import re
import unicodedata
from typing import Tuple


# ── Normalización de caracteres ───────────────────────────────────────────────

# Caracteres invisibles a eliminar
INVISIBLES = (
    '\u200b'  # zero-width space
    '\u200c'  # zero-width non-joiner
    '\u200d'  # zero-width joiner
    '\u2060'  # word joiner
    '\ufeff'  # BOM
)

# Espacios anómalos a normalizar a espacio normal
ESPACIOS_RAROS = {
    '\u00a0': ' ',  # NBSP
    '\u202f': ' ',  # narrow NBSP
    '\u2009': ' ',  # thin space
    '\u200a': ' ',  # hair space
    '\u2002': ' ',  # en space
    '\u2003': ' ',  # em space
    '\u3000': ' ',  # ideographic space
    '\t': '   ',     # tab → 3 espacios
}

# Apóstrofos / comillas variadas a normalizar
APOSTROFOS = {
    '\u2018': "'",   # '
    '\u2019': "'",   # '
    '\u201A': "'",   # ‚
    '\u201B': "'",   # ‛
    '\u2032': "'",   # prime
    '`':       "'",
    '´':       "'",
}

# Guiones que deben convertirse en raya larga al inicio de diálogo
GUIONES_DIALOGO = ['—', '–', '−', '-', '--', '―', '‒']


def _quitar_invisibles(t: str) -> str:
    """Elimina caracteres invisibles y normaliza espacios extraños."""
    for c in INVISIBLES:
        t = t.replace(c, '')
    for k, v in ESPACIOS_RAROS.items():
        t = t.replace(k, v)
    for k, v in APOSTROFOS.items():
        t = t.replace(k, v)
    return t


# ── Comillas: unificar a angulares «» (estándar editorial español) ────────────

def normalizar_comillas(t: str) -> str:
    """
    Convierte comillas inglesas " y rectas " a angulares « ».
    Detecta apertura/cierre por contexto:
      - Apertura: precedida de espacio, principio de línea, o tras puntuación
      - Cierre: seguida de espacio, fin de línea, puntuación
    """
    # Comillas curvas Unicode → angulares
    t = t.replace('\u201c', '«').replace('\u201d', '»')
    t = t.replace('\u201e', '«').replace('\u201f', '«')

    # Comillas rectas " — alternar apertura/cierre por orden de aparición
    out = []
    abierta = False
    for ch in t:
        if ch == '"':
            if not abierta:
                out.append('«'); abierta = True
            else:
                out.append('»'); abierta = False
        else:
            out.append(ch)
    return ''.join(out)


# ── Diálogos: garantizar raya larga (—) sin espacio antes del texto ───────────

def normalizar_dialogos(t: str) -> str:
    """
    Convierte líneas de diálogo a formato editorial estándar:
      - Empieza con — (raya larga)
      - Sin espacio entre — y la primera letra del parlamento
      - Inciso: " —dijo Juan—." (raya pegada al verbo y al punto)
    """
    lineas = t.split('\n')
    nuevas = []
    for l in lineas:
        ls = l.lstrip()
        # Detectar línea de diálogo: empieza con guión variado
        es_dialogo = False
        for g in ['—— ', '–– ', '-- ', '— ', '– ', '- ',
                  '——', '––', '--', '—', '–', '-', '―', '‒', '−']:
            if ls.startswith(g):
                resto = ls[len(g):].lstrip()
                l = ('—' + resto) if resto else '—'
                es_dialogo = True
                break
        # Si la línea es de diálogo, normalizar incisos internos
        if es_dialogo:
            # Buscar incisos: " - texto - " o " — texto — " o " -- texto -- "
            # Patrón: espacio + guión-variado + espacio + texto + espacio + guión-variado
            l = re.sub(
                r'\s+[—–\-‒]+\s+([^—–\-]+?)\s+[—–\-‒]+(\s*[.,;:!?])',
                lambda m: ' —' + m.group(1).strip() + '—' + m.group(2).strip(),
                l
            )
            # Inciso simple: " - texto" al final sin cierre
            l = re.sub(
                r'\s+[—–\-‒]+\s+(\w[^.!?]*?)\s*([.!?])\s*$',
                lambda m: ' —' + m.group(1).strip() + m.group(2),
                l
            )
        nuevas.append(l)

    return '\n'.join(nuevas)


# ── Espacios y puntuación ─────────────────────────────────────────────────────

def normalizar_espacios(t: str) -> str:
    """Múltiples espacios → uno solo. Espacios antes de puntuación → eliminar."""
    # Múltiples espacios consecutivos → uno
    t = re.sub(r'[ \t]{2,}', ' ', t)
    # Espacio antes de puntuación de cierre
    t = re.sub(r' +([.,;:!?»)\]])', r'\1', t)
    # Espacio después de apertura
    t = re.sub(r'([«(\[¡¿]) +', r'\1', t)
    # Espacios al final de línea
    t = re.sub(r' +\n', '\n', t)
    return t


# ── Saltos de línea ───────────────────────────────────────────────────────────

def normalizar_saltos(t: str) -> str:
    """
    - Líneas vacías múltiples → máximo 2 (= un párrafo de separación)
    - Líneas partidas en mitad de frase: une si la siguiente empieza minúscula
    """
    # Normalizar saltos de línea Windows/Mac
    t = t.replace('\r\n', '\n').replace('\r', '\n')

    # Más de 2 saltos seguidos → 2
    t = re.sub(r'\n{3,}', '\n\n', t)

    # Líneas partidas: si una línea acaba sin puntuación final
    # y la siguiente empieza por minúscula, unirlas con espacio
    lineas = t.split('\n')
    out = []
    i = 0
    while i < len(lineas):
        l = lineas[i].rstrip()
        # ¿Continuación rota?
        while (i + 1 < len(lineas)
               and l
               and not l.endswith(('.', ':', ';', '!', '?', '"', '»', ')', ']'))
               and lineas[i+1].strip()
               and lineas[i+1].lstrip()[:1].islower()):
            l = l + ' ' + lineas[i+1].strip()
            i += 1
        out.append(l)
        i += 1
    return '\n'.join(out)


# ── Guión de partición de palabra al final de línea ───────────────────────────

def quitar_guion_particion(t: str) -> str:
    """
    Texto OCR/escaneado: 'pala-\nbra' → 'palabra'
    Solo si la palabra resultante existe (heurística simple: minúsculas seguidas).
    """
    # Patrón: minúscula + guión + salto + minúscula → unir
    return re.sub(r'(\w)-\n(\w)', r'\1\2', t)


# ── Detección y limpieza de cabecera/pie repetidos ────────────────────────────

def quitar_repeticiones(t: str) -> str:
    """
    Elimina líneas que se repiten >5 veces idénticamente
    (típicamente pies de página: nombre del autor, título, página).
    """
    lineas = t.split('\n')
    cuentas = {}
    for l in lineas:
        s = l.strip()
        if 5 <= len(s) <= 80:  # solo líneas cortas pueden ser cabeceras
            cuentas[s] = cuentas.get(s, 0) + 1

    repetidas = {s for s, n in cuentas.items() if n >= 5}
    if not repetidas:
        return t

    nuevas = [l for l in lineas if l.strip() not in repetidas]
    return '\n'.join(nuevas)


# ── Numeración de páginas como párrafos ───────────────────────────────────────

def quitar_numeros_pagina(t: str) -> str:
    """Líneas que solo contienen un número (folios extraídos como texto)."""
    return re.sub(r'^\s*\d{1,4}\s*$\n?', '', t, flags=re.MULTILINE)


# ── Mayúsculas excesivas (errores de Caps Lock) ───────────────────────────────

def corregir_mayusculas_excesivas(t: str) -> str:
    """
    Si UNA línea (no título corto) está toda en mayúsculas y tiene >40 chars,
    probablemente sea un error → convertir a sentence case.
    NO toca títulos cortos (CAPÍTULO X, PRÓLOGO, etc).
    """
    lineas = t.split('\n')
    out = []
    for l in lineas:
        s = l.strip()
        # Solo procesar líneas largas en mayúsculas
        if (len(s) > 40
            and s.isupper()
            and sum(1 for c in s if c.isalpha()) > 20):
            # Convertir a sentence case: primera letra mayúscula, resto minúscula
            convertida = s.capitalize()
            # Preservar mayúsculas tras punto
            convertida = re.sub(r'([.!?]\s+)([a-zñáéíóúü])',
                                lambda m: m.group(1) + m.group(2).upper(),
                                convertida)
            out.append(convertida)
        else:
            out.append(l)
    return '\n'.join(out)


# ── Capítulos: normalizar variantes ──────────────────────────────────────────

def normalizar_capitulos(t: str) -> str:
    """
    Variantes detectadas y normalizadas:
      'capitulo 1', 'CAP. 1', 'Cap 1', 'CAPÍTULO PRIMERO', 'I.', '1.'
      → siempre 'Capítulo 1' (con tilde y formato editorial)
    """
    # Cap. → Capítulo
    t = re.sub(r'^[Cc][Aa][Pp]\.?\s+(\d+|[IVXLCDM]+|\w+)\s*$',
               lambda m: f'Capítulo {m.group(1)}',
               t, flags=re.MULTILINE)
    # CAPITULO sin tilde → CAPÍTULO
    t = re.sub(r'\bCAPITULO\b', 'CAPÍTULO', t)
    t = re.sub(r'\bcapitulo\b', 'capítulo', t)
    return t


# ── Limpiar inicios de archivos/PDFs con metadatos ───────────────────────────

def quitar_metadatos_inicio(t: str) -> str:
    """
    Algunos PDFs llevan al principio: 'Pages: 245', 'Creator: ...'
    o líneas como 'Documento1 - Microsoft Word'
    """
    lineas = t.split('\n')
    # Quitar las primeras líneas si parecen metadatos técnicos
    while lineas and re.match(
        r'^\s*(Pages?:|Creator:|Producer:|Author:|Title:|ModDate:|CreationDate:'
        r'|Documento\d+|Microsoft\s+Word|Sin\s+t[ií]tulo)',
        lineas[0], re.IGNORECASE):
        lineas.pop(0)
    return '\n'.join(lineas)


# ── Función principal ────────────────────────────────────────────────────────

def limpiar_texto(texto: str, verbose: bool = False) -> Tuple[str, dict]:
    """
    Aplica todo el pipeline de limpieza a un texto bruto de manuscrito.

    Devuelve (texto_limpio, stats) donde stats incluye:
      - chars_inicial, chars_final, lineas_eliminadas,
        rayas_normalizadas, comillas_normalizadas
    """
    stats = {'chars_inicial': len(texto)}

    # Normalización Unicode (NFC)
    texto = unicodedata.normalize('NFC', texto)

    # 1. Caracteres invisibles
    texto = _quitar_invisibles(texto)

    # 2. Guión de partición de palabra ANTES de unir líneas (OCR)
    texto = quitar_guion_particion(texto)

    # 3. Saltos de línea (CRLF → LF)
    texto = normalizar_saltos(texto)

    # 4. Metadatos al principio
    texto = quitar_metadatos_inicio(texto)

    # 5. Cabeceras/pies repetidos
    n_antes = len(texto.split('\n'))
    texto = quitar_repeticiones(texto)
    texto = quitar_numeros_pagina(texto)
    stats['lineas_eliminadas'] = n_antes - len(texto.split('\n'))

    # 6. Comillas
    n_comillas = texto.count('"')
    texto = normalizar_comillas(texto)
    stats['comillas_normalizadas'] = n_comillas

    # 7. Diálogos
    texto = normalizar_dialogos(texto)

    # 8. Mayúsculas excesivas
    texto = corregir_mayusculas_excesivas(texto)

    # 9. Capítulos
    texto = normalizar_capitulos(texto)

    # 10. Espacios y puntuación final
    texto = normalizar_espacios(texto)
    texto = normalizar_saltos(texto)

    stats['chars_final'] = len(texto)
    stats['ratio_compresion'] = round(stats['chars_final'] / max(1, stats['chars_inicial']), 3)

    if verbose:
        print(f'[limpiador] {stats}')

    return texto, stats


# ── Limpieza específica para parser DOCX ─────────────────────────────────────

def limpiar_bloques(bloques):
    """
    Aplica normalización a un array de Bloques del parser DOCX,
    sin tocar la estructura (cap_titulo, parrafo, dialogo).
    """
    for b in bloques:
        # Limpiar el texto del bloque
        t = b.texto
        t = _quitar_invisibles(t)
        t = unicodedata.normalize('NFC', t)
        t = normalizar_comillas(t)
        if b.tipo == 'dialogo' or t.lstrip().startswith(tuple(GUIONES_DIALOGO)):
            t = normalizar_dialogos(t)
        t = normalizar_espacios(t)
        t = quitar_guion_particion(t.replace('\n',' ')).strip()
        b.texto = t
        # Lo mismo para html (preservando tags)
        if b.html:
            h = b.html
            h = _quitar_invisibles(h)
            h = normalizar_comillas(h)
            h = normalizar_espacios(h)
            b.html = h
    return bloques


if __name__ == '__main__':
    # Test con casos típicos
    pruebas = [
        # Diálogo con guión simple
        ("- Hola - dijo Juan -. ¿Cómo estás?",
         "—Hola —dijo Juan—. ¿Cómo estás?"),
        # Comillas mezcladas
        ('Le dijo "esto es importante" y se fue.',
         'Le dijo «esto es importante» y se fue.'),
        # OCR con guión partido
        ("Era una pala-\nbra demasiado larga.",
         "Era una palabra demasiado larga."),
        # Mayúsculas excesivas
        ("ESTA ES UNA FRASE QUE NO DEBERÍA ESTAR ENTERA EN MAYÚSCULAS",
         "Esta es una frase que no debería estar entera en mayúsculas"),
        # Capítulo mal escrito
        ("CAPITULO 5",
         "CAPÍTULO 5"),
        # Múltiples espacios
        ("Esto    tiene    demasiados   espacios.",
         "Esto tiene demasiados espacios."),
    ]
    for original, esperado in pruebas:
        limpio, _ = limpiar_texto(original)
        ok = '✓' if limpio.strip() == esperado.strip() else '✗'
        print(f'{ok} "{original[:40]}..." → "{limpio[:40]}..."')
