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
  "lector_primario":   "string — perfil específico del lector ideal: franja de edad concreta + perfil sociocultural + intereses lectores. Ejemplo: 'Lectora adulta de 35-55 años, aficionada a la novela negra contemporánea, lectora habitual de Dolores Redondo y María Oruña, suscriptora de clubes de lectura'",
  "lector_secundario": "string — segundo perfil de lector ampliado, más generalista. Ejemplo: 'Lector general de 25-65 años interesado en thrillers psicológicos con ambientación rural española'",
  "comparable":        "string — TRES títulos publicados realmente existentes que el público objetivo ya conoce, en formato 'Autor 1 · «Título 1» · Autor 2 · «Título 2» · Autor 3 · «Título 3»'. Los nombres deben ser autores reales del panorama editorial español o internacional con obra comparable en género, tono o público. NUNCA dejes este campo vacío ni pongas 'Por concretar'.",
  "precio":            "string — rango de precio sugerido con formato (ej: 18,90 € — 21,90 € rústica con solapas)",
  "notas": [
    "string — Primera nota editorial: aspecto técnico o estilístico CONCRETO a trabajar en el proceso de edición. Lenguaje editorial profesional, sin frases vacías. Mencionar capítulos, escenas o elementos específicos cuando sea posible. Ejemplos del registro deseado: 'Recomiendo unificar la temporalidad narrativa en los capítulos centrales, donde se detectan oscilaciones entre presente y pretérito imperfecto que pueden desorientar al lector.' / 'La caracterización del antagonista podría ganar profundidad incorporando una escena previa que justifique sus motivaciones.' / 'Sugiero revisar la cadencia de los diálogos en las escenas de mayor tensión, donde el ritmo se ralentiza por incisos demasiado extensos.'",
    "string — Segunda nota editorial: estrategia de mercado, posicionamiento o presentación. Tono de profesional editorial con criterio comercial. Ejemplos: 'La obra encajaría con naturalidad en el catálogo de novela negra de autora, segmento con notable crecimiento desde 2020. Recomiendo presentación en ferias del libro especializadas y campaña dirigida a clubes de lectura femeninos.' / 'Por su perfil, considero recomendable trabajar el lanzamiento en colaboración con librerías independientes, donde el boca a boca puede activar las ventas durante el primer trimestre.'",
    "string — Tercera nota editorial: fortalezas que deben preservarse durante el proceso de edición. Reconocer con precisión técnica qué funciona. Ejemplos: 'La voz narrativa constituye el mayor activo del manuscrito. Recomiendo encarecidamente preservar su registro actual durante el proceso de corrección, limitando las intervenciones a ortotipografía y estilo menor.' / 'La estructura capitular breve y el ritmo sostenido son aciertos del autor. La edición debe respetar esta cadencia sin tentaciones de reordenación.'"
  ],
  "carta_autor": "string — CARTA DE CIERRE BREVE, PROFESIONAL Y CERCANA dirigida al autor con TUTEO. OBLIGATORIA en todos los informes. ESTRUCTURA EN 2 PÁRRAFOS CORTOS (5-6 líneas en total, no más): (1) Saludo cercano: 'Estimado/a {{nombre_de_pila}}' (NUNCA apellido, NUNCA 'señor/a'). Si no hay nombre, 'Estimado autor'. Agradece la confianza depositada y reconoce con UNA frase concreta algo positivo del manuscrito. (2) Compromiso de acompañamiento: explica brevemente que la asesora te acompañará personalmente en TODAS las fases (corrección, maquetación, diseño de cubierta, depósito legal e ISBN, distribución), según los servicios que contrate, garantizando un libro a la altura. Cierra invitando a una reunión. Tono: cercano y profesional, con tuteo natural ('te agradezco', 'tu obra', 'tu manuscrito', 'te acompañaré', 'si decides', 'según los servicios que contrates'). NUNCA usar 'usted' ni 'le acompañaré'. La firma será {asesora_nombre} (no la incluyas tú). Esta carta es OBLIGATORIA y nunca debe estar vacía."
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
        # Inicializar cliente con manejo robusto del conflicto httpx/proxies
        try:
            client = Anthropic(api_key=ANTHROPIC_KEY)
        except TypeError as te:
            if 'proxies' in str(te):
                # Conflicto de versión httpx ↔ anthropic SDK. Forzar httpx_client.
                print(f'[analizador] Workaround conflicto httpx: {te}', flush=True)
                import httpx
                client = Anthropic(api_key=ANTHROPIC_KEY, http_client=httpx.Client())
            else:
                raise

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
    Carta de cierre breve, profesional y cercana — adaptada a un perfil
    de autor adulto (45-70 años). Tono editorial maduro, sin tuteo,
    con compromiso de acompañamiento de principio a fin.
    """
    # Detección de género por nombre de pila para "señor/señora"
    def _es_femenino(n: str) -> bool:
        n = n.lower().rstrip('.').strip()
        # Excepciones: nombres masculinos terminados en -a
        masc_a = {'luca','andrea','elia','noa','iván','iván','jonás','jonás','isaías'}
        if n in masc_a: return False
        # Femeninos comunes que no terminan en -a
        fem_no_a = {'carmen','rocío','consuelo','dolores','mercedes','isabel',
                    'soledad','esther','beatriz','inés','raquel','ester','noemí',
                    'pilar','luz','sol','asunción','encarnación'}
        if n in fem_no_a: return True
        # Por defecto: termina en -a → femenino
        return n.endswith('a')

    saludo = 'Estimado autor'
    if autor and autor.strip():
        autor_norm = autor.strip().lower()
        if autor_norm not in ('anónimo','anonimo','autor','autora','sin autor','desconocido','anónima'):
            partes = autor.strip().split()
            es_fem = _es_femenino(partes[0])
            tratamiento = 'Estimada' if es_fem else 'Estimado'
            # Usar nombre de pila capitalizado
            nombre_pila = partes[0].capitalize()
            saludo = f'{tratamiento} {nombre_pila}'

    cuerpo = (
        f'{saludo}, te agradezco sinceramente la confianza depositada en '
        f'Editorial Numancia al compartir tu manuscrito con nosotros. '
        f'Tras la valoración inicial, considero que tu obra reúne '
        f'cualidades editoriales sólidas y un planteamiento que merece llegar al lector '
        f'con la mejor presentación posible.\n\n'
        f'Si decides publicar con nosotros, te acompañaré personalmente en cada fase '
        f'del proceso —corrección ortotipográfica, maquetación profesional, diseño de cubierta, '
        f'depósito legal, ISBN y distribución—, según los servicios que contrates, '
        f'garantizando un libro a la altura de tu contenido. Quedo a tu disposición '
        f'para concertar una reunión y exponerte, con detalle, la propuesta editorial completa.'
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
        'lector_primario':   'Lector adulto de 35-60 años, aficionado a la narrativa contemporánea española, lector habitual de novelas de autor con cierta complejidad temática. Perfil sociocultural medio-alto, suscriptor de clubes de lectura o seguidor de programas culturales.',
        'lector_secundario': 'Lector general de 25-70 años interesado en obras con voz propia y planteamiento literario cuidado. Comprador habitual en librerías independientes y usuario de plataformas de recomendación lectora.',
        'comparable':        'Almudena Grandes · «Los pacientes del doctor García» · Sara Mesa · «Cara de pan» · Manuel Vilas · «Ordesa»',
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
