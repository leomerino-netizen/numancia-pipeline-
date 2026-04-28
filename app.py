"""
Editorial Numancia — API de generación de documentos
Endpoints: /presupuesto  /informe  /preview  /maqueta
"""
import os, io, json, base64, traceback
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from datetime import datetime

from presupuesto_gen import generar_presupuesto
from informe_gen import generar_informe
from preview_gen import generar_preview
from maqueta_gen import generar_maqueta_completa
from extractor import extraer_presupuesto

app = Flask(__name__)
CORS(app)  # Permite llamadas desde Lovable y cualquier dominio
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

API_KEY = os.environ.get('NUMANCIA_API_KEY', '')


def _check_auth():
    if not API_KEY:
        return  # sin clave configurada → abierto (dev)
    key = request.headers.get('X-API-Key', '')
    if key != API_KEY:
        abort(401, 'API key inválida')


def _pdf_response(pdf_bytes: bytes, filename: str):
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


# ── Health check ──────────────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'Editorial Numancia — Document API',
        'version': '1.0.0',
        'endpoints': ['/presupuesto', '/informe', '/preview', '/maqueta'],
        'timestamp': datetime.utcnow().isoformat()
    })


# ── POST /presupuesto ─────────────────────────────────────────────────────────
@app.route('/presupuesto', methods=['POST'])
def presupuesto():
    """
    Body JSON:
    {
      "num_presupuesto": "10212",
      "fecha": "25 de abril de 2026",
      "asesora": "laura",           // laura | debora | juan | nancy
      "cliente": "Sara Libro Test",
      "obra": "Sara",
      "genero": "Novela",
      "paginas": 200,
      "formato": "A5",
      "precio_unitario": 4.52,
      "precio_descuento": 3.84,
      "cantidad": 100,
      "descuento_pct": 15,
      "precio_maquetacion": 322.39,
      "precio_legal": 114.40
    }
    Devuelve: PDF binario
    """
    _check_auth()
    try:
        d = request.get_json(force=True)
        if not d:
            return jsonify({'error': 'JSON vacío'}), 400

        required = ['num_presupuesto', 'fecha', 'asesora', 'cliente', 'obra',
                    'genero', 'paginas', 'formato', 'precio_unitario',
                    'precio_descuento', 'cantidad', 'precio_maquetacion', 'precio_legal']
        missing = [k for k in required if k not in d]
        if missing:
            return jsonify({'error': f'Campos requeridos: {missing}'}), 400

        pdf = generar_presupuesto(d)
        filename = f"presupuesto_{d['num_presupuesto']}_{d['cliente'].split()[0]}.pdf"
        return _pdf_response(pdf, filename)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /informe ─────────────────────────────────────────────────────────────
@app.route('/informe', methods=['POST'])
def informe():
    """
    Body JSON: mismo dict que acepta informe_gen.generar_informe()
    Devuelve: PDF binario
    """
    _check_auth()
    try:
        d = request.get_json(force=True)
        pdf = generar_informe(d)
        titulo_safe = d.get('titulo', 'informe').replace(' ', '_')[:30]
        return _pdf_response(pdf, f"informe_{titulo_safe}.pdf")
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /preview ─────────────────────────────────────────────────────────────
@app.route('/preview', methods=['POST'])
def preview():
    """
    Body JSON:
    {
      "texto": "...",
      "titulo": "...",
      "autor": "..."
    }
    """
    _check_auth()
    try:
        if request.content_type and 'multipart' in request.content_type:
            f = request.files.get('docx')
            titulo = request.form.get('titulo','')
            autor  = request.form.get('autor','')
            pdf = generar_preview('', titulo, autor, docx_bytes=f.read() if f else None)
        else:
            d = request.get_json(force=True)
            docx_b = None
            if d.get('docx_base64'):
                import base64
                docx_b = base64.b64decode(d['docx_base64'])
            pdf = generar_preview(d.get('texto',''), d['titulo'], d['autor'], docx_bytes=docx_b)
        titulo_safe = d.get('titulo', 'preview').replace(' ', '_')[:30]
        return _pdf_response(pdf, f"preview_{titulo_safe}.pdf")
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /maqueta ─────────────────────────────────────────────────────────────
@app.route('/maqueta', methods=['POST'])
def maqueta():
    """
    Body JSON:
    {
      "texto": "...",
      "titulo": "...",
      "autor": "...",
      "anyo": "2025",
      "dedicatoria": "...",
      "epigrafe": "...",
      "epigrafe_autor": "..."
    }
    """
    _check_auth()
    try:
        if request.content_type and 'multipart' in request.content_type:
            f = request.files.get('docx')
            titulo = request.form.get('titulo','')
            autor  = request.form.get('autor','')
            anyo   = request.form.get('anyo','2025')
            pdf = generar_maqueta_completa('', titulo, autor, anyo=anyo,
                      docx_bytes=f.read() if f else None)
        else:
            d = request.get_json(force=True)
            docx_b = None
            if d.get('docx_base64'):
                import base64
                docx_b = base64.b64decode(d['docx_base64'])
            pdf = generar_maqueta_completa(
                texto=d.get('texto',''),
            titulo=d['titulo'],
            autor=d['autor'],
            anyo=d.get('anyo', '2025'),
            dedicatoria=d.get('dedicatoria', ''),
            epigrafe=d.get('epigrafe', ''),
            epigrafe_autor=d.get('epigrafe_autor', ''),
        )
        titulo_safe = d.get('titulo', 'maqueta').replace(' ', '_')[:30]
        return _pdf_response(pdf, f"maqueta_{titulo_safe}.pdf")
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /extraer-presupuesto ─────────────────────────────────────────────────
@app.route('/extraer-presupuesto', methods=['POST'])
def extraer():
    """
    Recibe un PDF (multipart field 'pdf') generado por Printcolor/Numancia.
    Devuelve JSON con todos los campos extraídos listos para el formulario.
    """
    _check_auth()
    try:
        if 'pdf' not in request.files:
            return jsonify({'error': 'Campo "pdf" requerido'}), 400
        archivo = request.files['pdf']
        pdf_bytes = archivo.read()
        if not pdf_bytes:
            return jsonify({'error': 'Archivo vacío'}), 400

        datos = extraer_presupuesto(pdf_bytes)
        return jsonify({'ok': True, 'datos': datos})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /transformar-presupuesto ─────────────────────────────────────────────
@app.route('/transformar-presupuesto', methods=['POST'])
def transformar():
    """
    Todo en uno: sube el PDF de Printcolor + overrides opcionales en form-data,
    extrae los datos, aplica los overrides y devuelve el PDF personalizado.

    Form fields:
      - pdf (file, requerido)
      - asesora (string, opcional — sobreescribe la detectada)
      - overrides (JSON string, opcional — cualquier campo a sobreescribir)
    """
    _check_auth()
    try:
        if 'pdf' not in request.files:
            return jsonify({'error': 'Campo "pdf" requerido'}), 400

        pdf_bytes = request.files['pdf'].read()
        datos = extraer_presupuesto(pdf_bytes)

        # Asesora override (campo directo por comodidad)
        if request.form.get('asesora'):
            datos['asesora'] = request.form['asesora']

        # Override genérico en JSON
        if request.form.get('overrides'):
            import json
            overrides = json.loads(request.form['overrides'])
            datos.update(overrides)

        pdf_out = generar_presupuesto(datos)
        cliente_safe = datos.get('cliente', 'cliente').split()[0]
        num = datos.get('num_presupuesto', '0')
        return _pdf_response(pdf_out, f"propuesta_{num}_{cliente_safe}.pdf")

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)


# ── POST /procesar-manuscrito ─────────────────────────────────────────────────
@app.route('/procesar-manuscrito', methods=['POST'])
def procesar_manuscrito():
    """
    Procesa un manuscrito .docx y genera:
      - Informe de lectura y valoración (PDF + datos JSON)
      - Maquetación previa borrador (PDF)
    
    Multipart form-data:
      - docx     (file, requerido)
      - asesora  (string: 'laura'|'debora'|'juan')
      - titulo   (opcional)
      - autor    (opcional)
    """
    _check_auth()
    try:
        # Aceptar varios nombres de campo: docx, pdf, manuscrito, file
        archivo = None
        for nombre_campo in ('docx', 'pdf', 'manuscrito', 'file', 'archivo'):
            if nombre_campo in request.files:
                archivo = request.files[nombre_campo]
                break
        if archivo is None and request.files:
            # Tomar el primer archivo subido
            archivo = next(iter(request.files.values()))
        if archivo is None:
            return jsonify({'error': 'No se ha enviado ningún archivo. Use el campo "docx", "pdf" o "manuscrito".'}), 400

        contenido_bytes = archivo.read()
        nombre_fichero  = archivo.filename or 'manuscrito'
        asesora    = request.form.get('asesora', 'laura')
        titulo_ovr = request.form.get('titulo', '')
        autor_ovr  = request.form.get('autor', '')

        # Detectar formato
        nombre_lower = nombre_fichero.lower()
        es_pdf  = nombre_lower.endswith('.pdf')  or contenido_bytes[:4] == b'%PDF'
        es_docx = nombre_lower.endswith('.docx') or contenido_bytes[:4] == b'PK\x03\x04'

        # Título del nombre de archivo (sin extensión, normalizado)
        import re as _re
        titulo_archivo = _re.sub(r'\.(docx?|pdf|txt)$', '', nombre_fichero, flags=_re.IGNORECASE)
        titulo_archivo = _re.sub(r'[_-]+', ' ', titulo_archivo).strip()
        titulo_archivo = ' '.join(w.capitalize() if len(w) > 3 or i == 0 else w.lower()
                                   for i, w in enumerate(titulo_archivo.split()))

        # 1. Parsear manuscrito según formato
        from analizador import analizar_manuscrito
        aviso_pdf = ''
        if es_pdf:
            from pdf_a_texto import parsear_pdf
            ms, info_pdf = parsear_pdf(contenido_bytes)
            aviso_pdf = info_pdf.get('aviso', '')
            if not info_pdf.get('tiene_texto'):
                return jsonify({
                    'error': 'PDF sin texto extraíble (probablemente escaneado).',
                    'aviso': aviso_pdf,
                    'sugerencia': 'Solicita al autor el manuscrito en formato .docx (Word).',
                }), 422
            # Para PDFs hay que generar el .docx temporal para preview/maqueta
            # — alternativa: pasar bytes vacíos y que use el texto
            docx_bytes_para_maqueta = None
        elif es_docx:
            from docx_parser import parsear_docx
            ms = parsear_docx(contenido_bytes)
            docx_bytes_para_maqueta = contenido_bytes
        else:
            return jsonify({
                'error': f'Formato no soportado: {nombre_fichero}',
                'sugerencia': 'Use .docx (Word) o .pdf (PDF con texto)',
            }), 415
        # Prioridad: override > parser > nombre archivo
        titulo = titulo_ovr or ms.titulo or titulo_archivo or 'Sin título'
        autor  = autor_ovr  or ms.autor  or ''

        # 2. Estadísticas
        palabras    = sum(len(b.texto.split()) for b in ms.bloques)
        num_caps    = sum(1 for b in ms.bloques if b.tipo == 'cap_titulo')
        # Páginas estimadas: A5 fresada con interlineado profesional
        # Media empírica = ~110 palabras netas por página de cuerpo
        # (incluye páginas con diálogo, inicios de capítulo, blancos, etc.)
        paginas_est = max(1, round(palabras / 110))

        # 3. Mapear asesora a nombre
        asesoras_n = {
            'laura':  'Laura Vega Ugarte',
            'debora': 'Débora Tómas',
            'juan':   'Juan Muñoz',
            'nancy':  'Nancy',
        }

        # 4. Análisis editorial completo (Claude API o fallback)
        analisis = analizar_manuscrito(ms, titulo, autor,
                                       asesora_nombre=asesoras_n.get(asesora, asesora))

        # 4-bis. Análisis ortotipográfico preliminar (RAE / Martínez de Sousa)
        from corrector_preliminar import analizar_desde_bloques
        ortotipo = analizar_desde_bloques(ms.bloques)

        # 4. Fecha en español
        from datetime import date
        hoy = date.today()
        meses = ['enero','febrero','marzo','abril','mayo','junio',
                 'julio','agosto','septiembre','octubre','noviembre','diciembre']
        fecha_str = f"{hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

        # 5. Construir dict completo del informe
        datos_informe = {
            'titulo':        titulo,
            'autor':         autor,
            'genero':        analisis.get('genero', 'Novela'),
            'extension':     f'{palabras:,} palabras · {num_caps} capítulos · aprox. {paginas_est} págs. A5'.replace(',', '.'),
            'ambientacion':  analisis.get('ambientacion', ''),
            'fecha':         fecha_str,
            'evaluado_por':  asesoras_n.get(asesora, asesora),
            'sinopsis_i':    analisis.get('sinopsis_i', ''),
            'sinopsis_ii':   analisis.get('sinopsis_ii', ''),
            'sinopsis_iii':  analisis.get('sinopsis_iii', ''),
            'eval':          analisis.get('eval', []),
            'veredicto':       analisis.get('veredicto', 'CON MEJORAS'),
            'veredicto_texto': analisis.get('veredicto_texto', ''),
            'lector_primario':   analisis.get('lector_primario', ''),
            'lector_secundario': analisis.get('lector_secundario', ''),
            'comparable':        analisis.get('comparable', ''),
            'precio':            analisis.get('precio', ''),
            'notas':             analisis.get('notas', []),
            'carta_autor':       analisis.get('carta_autor', ''),
            'ortotipo':          ortotipo,
        }

        informe_bytes = generar_informe(datos_informe)

        # 6. Generar preview PDF
        if docx_bytes_para_maqueta:
            preview_bytes = generar_preview('', titulo, autor, docx_bytes=docx_bytes_para_maqueta)
        else:
            # Para PDF: pasar los bloques ya parseados para conservar estructura
            preview_bytes = generar_preview('', titulo, autor, bloques=ms.bloques)

        # 7. Nombres de archivo profesionales
        titulo_safe = ''.join(c if c.isalnum() or c in ' -_' else '' for c in titulo)[:50].strip()
        nombre_informe = f'Informe de lectura y valoracion - {titulo_safe}.pdf'
        nombre_preview = f'Maquetacion previa borrador - {titulo_safe}.pdf'

        # 8. Devolver JSON con todos los datos para Lovable
        return jsonify({
            'ok':                True,
            'titulo':            titulo,
            'autor':             autor,
            'genero':            datos_informe['genero'],
            'ambientacion':      datos_informe['ambientacion'],
            'palabras':          palabras,
            'capitulos':         num_caps,
            'paginas_estimadas': paginas_est,
            'asesora':           asesora,
            'asesora_nombre':    asesoras_n.get(asesora, asesora),
            'fecha':             fecha_str,
            'sinopsis': {
                'i':   datos_informe['sinopsis_i'],
                'ii':  datos_informe['sinopsis_ii'],
                'iii': datos_informe['sinopsis_iii'],
            },
            'evaluacion':        datos_informe['eval'],
            'veredicto':         datos_informe['veredicto'],
            'veredicto_texto':   datos_informe['veredicto_texto'],
            'publico': {
                'lector_primario':   datos_informe['lector_primario'],
                'lector_secundario': datos_informe['lector_secundario'],
                'comparable':        datos_informe['comparable'],
                'precio':            datos_informe['precio'],
            },
            'notas':             datos_informe['notas'],
            'carta_autor':       datos_informe['carta_autor'],
            'ortotipo': {
                'total':       ortotipo['total_incidencias'],
                'categorias':  ortotipo['categorias_afectadas'],
                'resumen':     ortotipo['resumen_corrector'],
                'incidencias': ortotipo['incidencias'],
            },
            'nombre_informe':    nombre_informe,
            'nombre_preview':    nombre_preview,
            'informe_pdf':   base64.b64encode(informe_bytes).decode(),
            'preview_pdf':   base64.b64encode(preview_bytes).decode(),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
