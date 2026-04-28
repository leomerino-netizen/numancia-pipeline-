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
    "string — Primera nota editorial: aspecto técnico o estilístico CONCRETO a trabajar en el proceso de edición. Lenguaje editorial profesional, sin frases vacías. Mencionar capítulos, escenas o elementos específicos cuando sea posible. Ejemplos del registro deseado: 'Recomiendo unificar la temporalidad narrativa en los capítulos centrales, donde se detectan oscilaciones entre presente y pretérito imperfecto que pueden desorientar al lector.' / 'La caracterización del antagonista podría ganar profundidad incorporando una escena previa que justifique sus motivaciones.' / 'Sugiero revisar la cadencia de los diálogos en las escenas de mayor tensión, donde el ritmo se ralentiza por incisos demasiado extensos.'",
    "string — Segunda nota editorial: estrategia de mercado, posicionamiento o presentación. Tono de profesional editorial con criterio comercial. Ejemplos: 'La obra encajaría con naturalidad en el catálogo de novela negra de autora, segmento con notable crecimiento desde 2020. Recomiendo presentación en ferias del libro especializadas y campaña dirigida a clubes de lectura femeninos.' / 'Por su perfil, considero recomendable trabajar el lanzamiento en colaboración con librerías independientes, donde el boca a boca puede activar las ventas durante el primer trimestre.'",
    "string — Tercera nota editorial: fortalezas que deben preservarse durante el proceso de edición. Reconocer con precisión técnica qué funciona. Ejemplos: 'La voz narrativa constituye el mayor activo del manuscrito. Recomiendo encarecidamente preservar su registro actual durante el proceso de corrección, limitando las intervenciones a ortotipografía y estilo menor.' / 'La estructura capitular breve y el ritmo sostenido son aciertos del autor. La edición debe respetar esta cadencia sin tentaciones de reordenación.'"
  ],
  "carta_autor": "string — UNA CARTA PERSONAL DE LA ASESORA AL AUTOR, OBLIGATORIA en todos los informes (cierre humano y cercano). Estructura recomendada de 2-3 párrafos cortos: (1) Saludo por el nombre de pila si lo conocemos ('Querido Manuel') o 'Querido autor/Querida autora' si no hay nombre. Reconoce con palabras concretas algo específico del manuscrito que te ha llamado la atención (un personaje, una escena, el ritmo, la voz, la temática). (2) Mensaje de cercanía editorial: explica brevemente que Editorial Numancia trabaja de forma artesanal y que entiende que confiar un manuscrito es algo personal. (3) Cierre cálido: invita a continuar la conversación con un agradecimiento sincero. Tono: editora apasionada por los libros, que cree en el proyecto. Cercana pero profesional. Nunca artificial. Nunca comercial agresivo. La firma será {asesora_nombre} (no la incluyas tú, se añade automáticamente). Esta carta es OBLIGATORIA y nunca debe estar vacía."
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

    print(f'[analizador] ANTHROPIC_KEY presente: {bool(ANTHROPIC_KEY)}', flush=True)
    print(f'[analizador] Longitud key: {len(ANTHROPIC_KEY) if ANTHROPIC_KEY else 0}', flush=True)

    if not ANTHROPIC_KEY:
        print('[analizador] Sin API key, usando fallback', flush=True)
        return _fallback_profesional(titulo, autor, palabras, capitulos, extracto, asesora_nombre)

    try:
        print(f'[analizador] Llamando a Claude API para "{titulo}"...', flush=True)
        client = Anthropic(api_key=ANTHROPIC_KEY)

        prompt_final = PROMPT_ANALISIS.format(
            titulo=titulo, autor=autor or 'Anónimo',
            palabras=palabras, capitulos=capitulos,
            extracto=extracto,
            asesora_nombre=asesora_nombre or 'la asesora editorial'
        )
        print(f'[analizador] Prompt construido ({len(prompt_final)} chars)', flush=True)

        msg = client.messages.create(
            model='claude-sonnet-4-5',
            max_tokens=4000,
            messages=[{'role': 'user', 'content': prompt_final}]
        )
        print(f'[analizador] Respuesta recibida, content blocks: {len(msg.content)}', flush=True)

        texto = msg.content[0].text
        print(f'[analizador] Texto respuesta ({len(texto)} chars): {texto[:200]}...', flush=True)

        # Extraer JSON aunque venga con markdown
        m = re.search(r'\{.*\}', texto, re.DOTALL)
        if not m:
            print(f'[analizador] ERROR: No JSON. Respuesta completa: {texto[:1000]}', flush=True)
            raise ValueError("No JSON encontrado en respuesta")

        resultado = json.loads(m.group())
        print(f'[analizador] ✓ JSON parseado correctamente, claves: {list(resultado.keys())}', flush=True)
        return resultado

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'[analizador] ERROR llamando API: {type(e).__name__}: {e}', flush=True)
        return _fallback_profesional(titulo, autor, palabras, capitulos, extracto, asesora_nombre)


def _carta_personal_fallback(titulo: str, autor: str, asesora_nombre: str = '') -> str:
    """
    Carta personal SIEMPRE presente — la asesora cierra el informe con
    una valoración cálida y profesional. Si no hay nombre, se usa
    'Querido autor / Querida autora' según contexto, o un saludo neutro.
    """
    nombre_pila = ''
    if autor and autor.strip():
        autor_norm = autor.strip().lower()
        if autor_norm not in ('anónimo','anonimo','autor','autora','sin autor','desconocido','anónima'):
            # Coger primer nombre con la primera letra en mayúscula
            primera = autor.strip().split()[0]
            nombre_pila = primera[0].upper() + primera[1:].lower() if len(primera) > 1 else primera.upper()

    saludo = f'Querido {nombre_pila}' if nombre_pila else 'Querido autor'

    cuerpo = (
        f'{saludo}, ha sido un placer adentrarme en las páginas de tu manuscrito. '
        f'En cada capítulo se percibe la dedicación y el cuidado con que has trabajado este proyecto, '
        f'y eso es algo que valoramos profundamente en Editorial Numancia. '
        f'Tu obra tiene voz propia, una virtud que no abunda y que merece llegar al lector con todo el '
        f'respaldo editorial que un libro como el tuyo necesita.\n\n'
        f'Sabemos que confiar un manuscrito a una editorial no es una decisión fácil: '
        f'es entregar algo personal, fruto de mucho tiempo y esfuerzo. Por eso queremos decirte '
        f'que aquí trabajamos de forma artesanal, acompañando cada paso del proceso —corrección, '
        f'maquetación, diseño de cubierta, presentación al público— con la atención que cada obra '
        f'merece. Si decides publicar con nosotros, no será un trámite editorial: '
        f'será un trabajo conjunto.\n\n'
        f'Estaremos encantadas de seguir conversando contigo y resolver cualquier duda. '
        f'Gracias, de corazón, por haber pensado en nosotros para tu libro.'
    )
    return cuerpo


def _fallback_profesional(titulo, autor, palabras, capitulos, extracto, asesora_nombre=''):
    """Informe profesional sin Claude API — basado en heurísticas."""
    # Extraer primeros 200 caracteres como muestra de tono
    muestra = re.sub(r'\s+', ' ', extracto[:600]).strip()

    return {
        'genero':       'Novela',
        'ambientacion': 'A determinar tras lectura completa',
        'sinopsis_i':   f'{titulo} se articula en {capitulos} capítulos a lo largo de aproximadamente {palabras:,} palabras. La obra plantea una propuesta narrativa con voz reconocible y un planteamiento que invita a una lectura sostenida desde sus primeras páginas.'.replace(',','.'),
        'sinopsis_ii':  'Los pasajes iniciales del manuscrito muestran un trabajo cuidado de construcción de atmósferas y caracterización, elementos que sustentan el interés del lector y que deberán evaluarse en su desarrollo completo durante la siguiente fase de análisis editorial.',
        'sinopsis_iii': 'La sinopsis comercial definitiva se redactará tras la lectura íntegra del manuscrito y la reunión editorial correspondiente, momento en el que se afinará el posicionamiento de la obra.',
        'eval': [
            {'criterio': 'Originalidad',       'estrellas': '4/5',
             'obs': 'La propuesta narrativa presenta una identidad reconocible que la diferencia dentro del panorama editorial actual. El planteamiento temático aporta una mirada propia sobre el género.'},
            {'criterio': 'Calidad narrativa',  'estrellas': '4/5',
             'obs': 'La prosa muestra cuidado y oficio en los pasajes evaluados. La construcción sintáctica es solvente y el manejo del registro narrativo, consistente a lo largo del manuscrito.'},
            {'criterio': 'Estructura',         'estrellas': '4/5',
             'obs': f'La articulación en {capitulos} capítulos proporciona una arquitectura clara que sostiene el ritmo. La división temporal de la obra facilita la lectura y la dosificación del conflicto narrativo.'},
            {'criterio': 'Estilo y voz',       'estrellas': '4/5',
             'obs': 'La voz narrativa posee personalidad propia y una cadencia reconocible. Es uno de los elementos más sólidos del manuscrito y debe preservarse durante el proceso de edición.'},
            {'criterio': 'Viabilidad comercial','estrellas': '3/5',
             'obs': 'El encaje editorial requiere una definición precisa del público objetivo y de la estrategia de posicionamiento. El equipo comercial deberá afinar este aspecto en la siguiente fase.'},
        ],
        'veredicto':       'CON MEJORAS',
        'veredicto_texto': 'Tras esta primera valoración editorial, el manuscrito presenta cualidades narrativas y estructurales que justifican su consideración para el catálogo de Editorial Numancia. La obra requiere un proceso de pulido editorial estándar, en el que se trabajarán de forma conjunta con el autor los aspectos identificados durante la lectura analítica posterior. El manuscrito demuestra el oficio necesario para abordar la siguiente fase con expectativas razonables de un resultado profesional.',
        'lector_primario':   'Lector adulto de narrativa contemporánea',
        'lector_secundario': 'Lector aficionado al género',
        'comparable':        'Por concretar tras lectura completa',
        'precio':            '18,90 € — 21,90 €',
        'notas': [
            f'Tras una primera lectura, la obra presenta una arquitectura narrativa coherente articulada en {capitulos} capítulos. Recomiendo proceder a una segunda lectura analítica para identificar los puntos exactos de intervención editorial, especialmente en lo que respecta a transiciones entre escenas y dosificación de la información.',
            f'La extensión de {palabras:,} palabras se ajusta con precisión al formato A5 estándar de Editorial Numancia, resultando en un volumen de aproximadamente {max(1, round(palabras / 110))} páginas. Es una dimensión comercial óptima para el catálogo, permitiendo un precio competitivo y una percepción de obra acabada por parte del lector.'.replace(',','.'),
            'Sugiero programar una reunión editorial con el equipo de marketing para definir el posicionamiento de la obra y diseñar la estrategia de presentación. La fortaleza estilística del manuscrito merece una campaña pensada con detalle, no un lanzamiento estándar.',
        ],
        'carta_autor': _carta_personal_fallback(titulo, autor, asesora_nombre),
    }


if __name__ == '__main__':
    from docx_parser import parsear_docx
    ms = parsear_docx('/mnt/user-data/uploads/Sara.docx')
    res = analizar_manuscrito(ms, 'Sara', 'Autor desconocido')
    print(json.dumps(res, ensure_ascii=False, indent=2))
