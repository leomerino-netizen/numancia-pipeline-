"""
Pack Promoción y Marketing — Tier 1 "Lanzamiento Esencial"
Editorial Numancia · numancia-pipeline

Una sola llamada a Claude API genera, con structured JSON output, los 9
elementos del pack a partir del texto del libro, su título, autor, género
y URL de la Librería Numancia.

Uso típico desde el endpoint Flask /pack-phromocion:

    from pack_promocion_prompt import generar_pack_promocion
    pack = generar_pack_promocion(
        texto_libro=texto_extraido_del_pdf,
        titulo='París 1889',
        autor='Leo Merino',
        genero='Novela histórica',
        url_libreria='https://libreria.editorialnumancia.com/libros/paris-1889',
    )
    # pack es un dict con todos los campos + bloque _meta con tokens y coste

Coste estimado por llamada: ~2-3 € (Claude Sonnet 4.5, ~30k tokens entrada,
~10k tokens salida). Tiempo: 30-90 segundos.
"""

import os
import json
import anthropic


# ── Configuración del modelo ────────────────────────────────────────────────
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")   # Mismo modelo que el resto del pipeline
MAX_TOKENS = 8000             # Output generoso (28 publicaciones + 25 medios)
TEMPERATURE = 0.4              # Marketing creativo pero fiel al libro
MAX_CHARS_TEXTO_LIBRO = 25_000 # ~20k tokens, primeros 80k caracteres del libro

# Tarifas Claude Sonnet 4.5 (USD por millón de tokens, oficial Anthropic)
PRECIO_INPUT_USD_POR_MTOK  = 3.0
PRECIO_OUTPUT_USD_POR_MTOK = 15.0
# Conversión USD→EUR (aproximada, ajustable según tipo de cambio real)
USD_A_EUR = 0.92


# ── System prompt (estable, cacheable) ──────────────────────────────────────
SYSTEM_PROMPT = """Eres el responsable de marketing editorial de Editorial Numancia, sello de autopublicación profesional con sede en Barcelona (Grupo Printcolorweb.com). Tu trabajo es preparar el material de lanzamiento de un libro a partir de su manuscrito.

CONTEXTO DEL NEGOCIO
- Editorial Numancia publica autores noveles, mayoritariamente españoles, en español.
- Los autores tienen entre 45 y 65 años, no son nativos digitales y necesitan que les demos textos listos para copiar y pegar.
- La librería Numancia online (libreria.editorialnumancia.com) es el canal principal: el 100% de las ventas en esa librería van al autor.
- Otros canales: Amazon, Casa del Libro, librerías físicas locales del autor.

REGLAS DE FIDELIDAD (CRÍTICAS)
1. NO inventes tramas, personajes, capítulos, ubicaciones, escenas ni datos biográficos del autor que no aparezcan en el texto que te entregamos.
2. Las citas destacadas deben ser textuales del libro o claras adaptaciones de frases del libro. Cuando sea textual, marca `"tipo": "textual"`. Cuando reformules, marca `"tipo": "adaptada"`.
3. Para la bio del autor: úsate solo de las pistas que aparezcan en el texto (prólogo, dedicatorias, "sobre el autor", agradecimientos). Si no hay pistas suficientes, deja `bio_autor_sugerida` con una bio genérica honesta (3-4 líneas que el autor pueda completar) y rellena `bio_autor_advertencia` explicándolo.
4. Para los medios objetivo: prioriza nombres reales del mercado español que conozcas con seguridad (Lecturalia, Anika Entre Libros, Babelia, Zenda, Devaneos, podcast "Más libros y menos cuentos", premios Planeta/Nadal/Herralde/Tusquets, etc.). Si no estás seguro de un nombre concreto, describe el perfil del medio en `nombre` (p. ej. "Blog literario especializado en novela histórica") y pon `url_o_handle: null`. Mejor un perfil honesto que un nombre inventado.

TONO Y ESTILO
- Profesional editorial, no marketinero cutre. Nada de "imprescindible", "best-seller", "explosivo", "revolucionario".
- Cercano al lector español adulto. Evita el español neutro de Latam.
- Citas y textos: respeta la voz del libro. Si el libro es lírico, mantén el lirismo; si es directo, mantenlo directo.
- Hashtags: 3-5 por publicación, mezcla genéricos (#LibrosRecomendados) con específicos del género (#NovelaHistórica). Nada de hashtags raros tipo #BookishCommunity2024Reader.

FORMATO DE SALIDA (CRÍTICO)
Devuelve EXCLUSIVAMENTE un objeto JSON válido, sin texto antes ni después, sin bloques de código markdown (ni ```json ni ```). El JSON debe respetar exactamente el esquema indicado en el mensaje del usuario.

LONGITUDES (en caracteres, no palabras)
- sinopsis_corta: 150-200 caracteres (sirve para ficha, X/Twitter, descripción Amazon corta).
- sinopsis_larga: 800-1200 caracteres (para press kit, descripción Amazon larga).
- bio_autor_sugerida: 350-500 caracteres.
- cita_nuclear.texto: 80-200 caracteres (la cita más memorable, para reverso del libro y posts grandes).
- citas_destacadas[*].texto: 60-180 caracteres cada una.
- medios_objetivo: exactamente 25 elementos.
- calendario_editorial_4_semanas: exactamente 28 elementos (7 por semana × 4 semanas).
- descripcion_amazon_corta: 200-250 caracteres.
- descripcion_amazon_larga: 1500-3000 caracteres, con dobles saltos de línea entre párrafos.
- email_lanzamiento_autor.cuerpo: 400-700 caracteres.
- post_linkedin_autor: 300-500 caracteres."""


# ── Plantilla del user prompt ──────────────────────────────────────────────
USER_PROMPT_TEMPLATE = """Estos son los datos del libro que vamos a lanzar:

<libro_titulo>{titulo}</libro_titulo>
<libro_autor>{autor}</libro_autor>
<genero>{genero}</genero>
<url_libreria>{url_libreria}</url_libreria>

<texto_libro>
{texto_libro}
</texto_libro>

Genera el pack de marketing en formato JSON exactamente con esta estructura:

{{
  "metadatos_detectados": {{
    "genero_refinado": "subgénero detectado al leer el libro",
    "publico_objetivo": "descripción del lector ideal en una frase",
    "tono_voz": "ej. lírico contemplativo, ágil con humor, etc.",
    "comparables_mercado": ["libro 1 publicado en España últimos 5 años", "libro 2", "libro 3"]
  }},
  "sinopsis_corta": "...",
  "sinopsis_larga": "...",
  "bio_autor_sugerida": "...",
  "bio_autor_advertencia": "null si la bio está basada en pistas del texto, o una frase explicando que es una plantilla genérica si no hay datos suficientes",
  "cita_nuclear": {{
    "texto": "...",
    "tipo": "textual",
    "ubicacion": "indicación aproximada (ej. 'inicio del capítulo 3') o null si es adaptada"
  }},
  "citas_destacadas": [
    {{"texto": "...", "tipo": "textual"}},
    {{"texto": "...", "tipo": "textual"}},
    {{"texto": "...", "tipo": "adaptada"}},
    {{"texto": "...", "tipo": "textual"}},
    {{"texto": "...", "tipo": "adaptada"}}
  ],
  "medios_objetivo": [
    {{
      "nombre": "Lecturalia o 'Blog literario especializado en X'",
      "tipo": "blog_literario | podcast | instagram | premio | periodista | revista | newsletter",
      "url_o_handle": "https://... o @cuenta o null",
      "por_que_encaja": "razón breve (1 frase)",
      "ambito": "español | internacional"
    }}
  ],
  "calendario_editorial_4_semanas": [
    {{
      "dia": 1,
      "semana": 1,
      "tema_semana": "Lanzamiento",
      "canal": "instagram_feed | instagram_story | facebook | linkedin_autor | x_twitter",
      "tipo": "anuncio_lanzamiento | teaser | cita | datos_libro | tras_camaras | cta_compra | reseña | extracto",
      "texto_sugerido": "texto completo listo para copiar y pegar, incluido CTA si aplica",
      "hashtags": ["#...", "#..."]
    }}
  ],
  "descripcion_amazon_corta": "...",
  "descripcion_amazon_larga": "...",
  "email_lanzamiento_autor": {{
    "asunto": "...",
    "cuerpo": "..."
  }},
  "post_linkedin_autor": "..."
}}

ESTRUCTURA SUGERIDA DEL CALENDARIO (28 publicaciones, 7 por semana):
- Semana 1 — "Lanzamiento": anuncio oficial, teaser de portada, primera cita destacada, datos técnicos del libro, frase sobre el origen del libro, story con enlace a librería, llamada a la pre-compra/compra.
- Semana 2 — "El libro por dentro": 4 citas destacadas distribuidas, 1 extracto breve, 1 dato curioso/contexto histórico/temático, 1 CTA de compra suave.
- Semana 3 — "El autor y el proceso": bio breve del autor, motivación para escribir el libro, anécdota del proceso, foto de escritorio/manuscrito (texto sugerido para acompañar), agradecimientos, 1 cita, 1 CTA.
- Semana 4 — "Comunidad y eco": invitación a reseñas, recomendaciones del libro a perfiles concretos (mujeres que leen tal cosa, padres que..., aficionados a...), recordatorio del enlace, 1 cita final, 1 idea de regalo, 1 mensaje de gratitud, CTA cierre.

Distribución de canales sugerida por semana (puedes ajustar según el género):
- 4 instagram_feed + 2 instagram_story + 1 linkedin_autor

Si el género del libro es claramente no-ficción profesional (ensayo, divulgación, autoayuda), añade más peso a linkedin_autor (3 por semana) y reduce instagram_story.

Devuelve solo el JSON, sin texto antes ni después."""


# ── Función principal ──────────────────────────────────────────────────────
def generar_pack_promocion(
    texto_libro,
    titulo,
    autor,
    genero,
    url_libreria,
    *,
    client=None,
    model=MODEL,
    max_tokens=MAX_TOKENS,
    temperature=TEMPERATURE,
):
    """
    Llama a Claude API y devuelve el dict con los 9 elementos del pack
    + un bloque _meta con tokens utilizados y coste estimado en EUR.

    Args:
        texto_libro: texto plano del libro (se truncará a MAX_CHARS_TEXTO_LIBRO).
        titulo: título del libro.
        autor: nombre del autor.
        genero: género conocido del expediente (ej. 'Novela histórica').
        url_libreria: URL del libro en la Librería Numancia.
        client: cliente anthropic.Anthropic. Si es None, se crea uno con
                ANTHROPIC_API_KEY del entorno.
        model, max_tokens, temperature: ajustables si quieres experimentar.

    Returns:
        dict con los campos del pack + bloque _meta:
            {
              "metadatos_detectados": {...},
              "sinopsis_corta": "...",
              ...
              "_meta": {
                "tokens_input": int,
                "tokens_output": int,
                "coste_usd": float,
                "coste_eur": float,
                "model": str
              }
            }

    Raises:
        anthropic.APIError si la API falla.
        json.JSONDecodeError si el output no es JSON válido.
        ValueError si la respuesta carece de campos críticos.
    """
    if client is None:
        client = anthropic.Anthropic()  # usa ANTHROPIC_API_KEY del entorno

    # Truncar el libro si es muy largo (las novelas pueden tener 200k+ chars).
    # Los primeros 80k cubren la apertura + buena parte del desarrollo, que es
    # de donde mejor se extraen citas y tono.
    texto_recortado = texto_libro[:MAX_CHARS_TEXTO_LIBRO]
    truncado = len(texto_libro) > MAX_CHARS_TEXTO_LIBRO

    user_prompt = USER_PROMPT_TEMPLATE.format(
        titulo=titulo or '(sin título)',
        autor=autor or '(autor desconocido)',
        genero=genero or '(género no especificado)',
        url_libreria=url_libreria or '(URL no especificada)',
        texto_libro=texto_recortado,
    )

    print(
        f'[pack_promocion] llamada Claude API · modelo={model} '
        f'titulo={titulo!r} autor={autor!r} '
        f'chars_libro={len(texto_recortado)}/{len(texto_libro)} '
        f'truncado={truncado}',
        flush=True,
    )

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[
            {'role': 'user',      'content': user_prompt},
        ],
    )

    # Reconstruir el JSON (el prefill '{' se añade al inicio del output)
    raw = next((b.text for b in (response.content or []) if getattr(b, "type", None) == "text"), "")
    raw = raw.strip()
    # Por si el modelo añade ```json al inicio o ``` al final (raro con prefill)
    if raw.startswith('```'):
        raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
    if raw.endswith('```'):
        raw = raw.rsplit('```', 1)[0]
    raw = raw.strip()

    pack = json.loads(raw)

    # Validación mínima: campos críticos presentes
    criticos = [
        'sinopsis_corta', 'sinopsis_larga', 'bio_autor_sugerida',
        'cita_nuclear', 'citas_destacadas', 'medios_objetivo',
        'calendario_editorial_4_semanas',
        'descripcion_amazon_corta', 'descripcion_amazon_larga',
        'email_lanzamiento_autor', 'post_linkedin_autor',
    ]
    faltantes = [c for c in criticos if c not in pack]
    if faltantes:
        raise ValueError(
            f'[pack_promocion] respuesta incompleta, faltan campos: {faltantes}'
        )

    # ── Calcular coste a partir de tokens reportados por la API ────────────
    tokens_in  = response.usage.input_tokens
    tokens_out = response.usage.output_tokens
    coste_usd = (
        tokens_in  * PRECIO_INPUT_USD_POR_MTOK  / 1_000_000
        + tokens_out * PRECIO_OUTPUT_USD_POR_MTOK / 1_000_000
    )
    coste_eur = round(coste_usd * USD_A_EUR, 4)

    pack['_meta'] = {
        'model':         model,
        'tokens_input':  tokens_in,
        'tokens_output': tokens_out,
        'coste_usd':     round(coste_usd, 4),
        'coste_eur':     coste_eur,
    }

    print(
        f'[pack_promocion] OK · {len(pack.get("citas_destacadas",[]))} citas, '
        f'{len(pack.get("medios_objetivo",[]))} medios, '
        f'{len(pack.get("calendario_editorial_4_semanas",[]))} publicaciones, '
        f'tokens_in={tokens_in} tokens_out={tokens_out} '
        f'coste_eur={coste_eur}',
        flush=True,
    )

    return pack


# ── Ejemplo de uso local ────────────────────────────────────────────────────
if __name__ == '__main__':
    # Necesita ANTHROPIC_API_KEY en el entorno
    texto = """[Aquí iría el texto extraído del PDF del libro.
    En producción se llama a pdfplumber o pdf_a_texto desde el endpoint Flask
    y se le pasa el resultado a generar_pack_promocion()].

    Era una mañana de enero, y París se desperezaba bajo el peso de su propia
    expectativa. El Sena, todavía oscuro, reflejaba las primeras luces de gas
    que se resistían a apagarse... [continuaría el libro completo aquí]
    """

    pack = generar_pack_promocion(
        texto_libro=texto,
        titulo='París 1889',
        autor='Leo Merino',
        genero='Novela histórica',
        url_libreria='https://libreria.editorialnumancia.com/libros/paris-1889',
    )

    # Guardar el resultado a disco para inspeccionar
    with open('/tmp/pack_promocion_resultado.json', 'w', encoding='utf-8') as f:
        json.dump(pack, f, ensure_ascii=False, indent=2)

    print(f'\nPack generado. Métricas:')
    print(f'  Sinopsis corta: {len(pack["sinopsis_corta"])} chars')
    print(f'  Sinopsis larga: {len(pack["sinopsis_larga"])} chars')
    print(f'  Citas destacadas: {len(pack["citas_destacadas"])}')
    print(f'  Medios objetivo: {len(pack["medios_objetivo"])}')
    print(f'  Publicaciones: {len(pack["calendario_editorial_4_semanas"])}')
    print(f'  Tokens: {pack["_meta"]["tokens_input"]} in / '
          f'{pack["_meta"]["tokens_output"]} out')
    print(f'  Coste: {pack["_meta"]["coste_eur"]:.4f} €')
    print(f'\nGuardado en: /tmp/pack_promocion_resultado.json')
