"""
estructura_ia.py — Deteccion de estructura del manuscrito con Claude (Fable 5).
Fase 1: detecta jerarquia mayor (partes, capitulos, epigrafes, separadores de
escena) mediante CLASIFICACION POR INDICE DE LINEA, sin reescribir el texto.
La IA solo devuelve, para cada linea no vacia, su tipo. El texto se reconstruye
desde el original, garantizando que no se altera ni una palabra del manuscrito.
Si la IA falla, el llamador (maqueta_gen._parse_texto) usa el fallback de regex.
"""
import os, json, re
from anthropic import Anthropic
from docx_parser import Bloque

_ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

# Tipos validos que la IA puede asignar a una linea
_TIPOS = {'parte', 'cap_titulo', 'cap_subtitulo', 'epigrafe',
          'separador', 'dialogo', 'parrafo'}

PROMPT_ESTRUCTURA = """Eres un maquetador editorial experto. Te paso el texto de un manuscrito con cada linea numerada (formato "N: contenido"). Debes CLASIFICAR cada linea segun su funcion estructural. NO reescribas, traduzcas ni resumas nada: solo clasificas.

Devuelve EXCLUSIVAMENTE un objeto JSON con esta forma exacta:
{{"lineas": [{{"n": 0, "tipo": "cap_titulo"}}, {{"n": 1, "tipo": "parrafo"}}]}}

Tipos posibles (usa EXACTAMENTE estas etiquetas):
- "parte": divisiones mayores por encima de capitulos (ej. "PRIMERA PARTE", "Libro I").
- "cap_titulo": linea que inicia un capitulo, AUNQUE no este numerada (ej. "Uno", "El despertar", "I", "Capitulo 3").
- "cap_subtitulo": subtitulo que aparece justo debajo de un cap_titulo.
- "epigrafe": cita breve de apertura de capitulo o libro (suele llevar autor).
- "separador": salto de escena dentro de un capitulo (ej. "* * *", "---").
- "dialogo": linea de dialogo (empieza por raya o guion).
- "parrafo": prosa normal (el caso por defecto).

REGLAS:
- Incluye en "lineas" TODAS las lineas que recibas, con su numero "n" original.
- No inventes ni omitas numeros de linea.
- Ante la duda, usa "parrafo".
- Devuelve solo el JSON, sin texto adicional ni markdown.

LINEAS DEL MANUSCRITO:
{lineas}
"""


def estructura_bloques(texto: str) -> list:
    """Devuelve list[Bloque] reconstruida desde el texto original.
    Lanza excepcion si la IA falla, para que el llamador use el fallback."""
    if not _ANTHROPIC_KEY:
        raise RuntimeError("estructura_ia: sin ANTHROPIC_API_KEY")

    # 1) Lineas no vacias del original, con su indice estable
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    if not lineas:
        raise ValueError("estructura_ia: texto vacio")

    numeradas = "\n".join(f"{i}: {l}" for i, l in enumerate(lineas))
    prompt = PROMPT_ESTRUCTURA.format(lineas=numeradas)

    # 2) Llamada a Claude (mismo patron que analizador.py)
    client = Anthropic(api_key=_ANTHROPIC_KEY)
    msg = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-fable-5"),
        max_tokens=8000,
        messages=[{'role': 'user', 'content': prompt}],
    )
    raw = msg.content[0].text
    print(f"[estructura_ia] respuesta {len(raw)} chars", flush=True)

    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m:
        raise ValueError("estructura_ia: no se encontro JSON en la respuesta")
    data = json.loads(m.group())

    # 3) Mapa indice -> tipo (solo tipos validos)
    tipos = {}
    for it in data.get("lineas", []):
        n = it.get("n")
        tp = it.get("tipo", "parrafo")
        if isinstance(n, int) and 0 <= n < len(lineas):
            tipos[n] = tp if tp in _TIPOS else 'parrafo'
    if not tipos:
        raise ValueError("estructura_ia: JSON sin clasificaciones validas")

    # 4) Reconstruir Bloques desde el TEXTO ORIGINAL (no desde la IA)
    bloques = []
    primer = True
    for i, l in enumerate(lineas):
        tipo = tipos.get(i, 'parrafo')
        if tipo in ('parte', 'cap_titulo'):
            primer = True
            bloques.append(Bloque(tipo, l, l))
            continue
        if tipo in ('cap_subtitulo', 'epigrafe', 'separador'):
            bloques.append(Bloque(tipo, l, l))
            continue
        es_primer = (tipo == 'parrafo' and primer)
        if es_primer:
            primer = False
        bloques.append(Bloque(tipo, l, l, primer_parr=es_primer))

    print(f"[estructura_ia] {len(bloques)} bloques clasificados", flush=True)
    return bloques
