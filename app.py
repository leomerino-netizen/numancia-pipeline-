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
    Endpoint todo-en-uno para el flujo de Nuevo Análisis en Lovable.
    
    Acepta multipart/form-data:
      - docx     (file, requerido) — manuscrito Word
      - asesora  (string) — 'laura' | 'debora' | 'juan'
      - titulo   (string, opcional — sobreescribe el del docx)
      - autor    (string, opcional)
    
    Devuelve JSON:
    {
      "ok": true,
      "titulo": "...",
      "autor": "...",
      "genero": "...",
      "paginas_estimadas": 180,
      "palabras": 36000,
      "informe_pdf": "<base64>",
      "preview_pdf": "<base64>"
    }
    """
    _check_auth()
    try:
        if 'docx' not in request.files:
            return jsonify({'error': 'Campo "docx" requerido'}), 400

        docx_bytes = request.files['docx'].read()
        asesora    = request.form.get('asesora', 'laura')
        titulo_ovr = request.form.get('titulo', '')
        autor_ovr  = request.form.get('autor', '')

        # 1. Parsear el manuscrito
        from docx_parser import parsear_docx
        ms = parsear_docx(docx_bytes)

        titulo = titulo_ovr or ms.titulo or 'Sin título'
        autor  = autor_ovr  or ms.autor  or ''

        # 2. Estadísticas básicas
        palabras = sum(len(b.texto.split()) for b in ms.bloques)
        paginas_est = max(1, round(palabras / 250))  # ~250 palabras/página A5

        # 3. Generar preview PDF
        preview_bytes = generar_preview(
            texto='', titulo=titulo, autor=autor,
            docx_bytes=docx_bytes
        )

        # 4. Generar informe de viabilidad (datos automáticos del manuscrito)
        from datetime import date
        hoy = date.today()
        meses = ['enero','febrero','marzo','abril','mayo','junio',
                 'julio','agosto','septiembre','octubre','noviembre','diciembre']
        fecha_str = f"{hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

        # Mapear asesora a nombre completo
        asesoras_nombres = {
            'laura':  'Laura Vega Ugarte',
            'debora': 'Débora Tómas',
            'juan':   'Juan Muñoz',
            'nancy':  'Nancy',
        }

        # Calcular número de capítulos detectados
        num_caps = sum(1 for b in ms.bloques if b.tipo == 'cap_titulo')

        datos_informe = {
            'titulo':        titulo,
            'autor':         autor,
            'genero':        'Novela',
            'extension':     f'{palabras:,} palabras · {num_caps} capítulos · aprox. {paginas_est} págs. A5'.replace(',', '.'),
            'ambientacion':  'Pendiente de lectura completa',
            'fecha':         fecha_str,
            'evaluado_por':  asesoras_nombres.get(asesora, asesora),
            'sinopsis_i':    f'Manuscrito recibido. {palabras:,} palabras en {num_caps} capítulos detectados.'.replace(',', '.'),
            'sinopsis_ii':   'Sinopsis pendiente de elaboración tras lectura completa del manuscrito.',
            'sinopsis_iii':  '',
            'eval': [
                {'criterio': 'Originalidad',      'estrellas': '3/5', 'obs': 'Pendiente evaluación'},
                {'criterio': 'Calidad narrativa',  'estrellas': '3/5', 'obs': 'Pendiente evaluación'},
                {'criterio': 'Estructura',         'estrellas': '3/5', 'obs': 'Pendiente evaluación'},
                {'criterio': 'Estilo y voz',       'estrellas': '3/5', 'obs': 'Pendiente evaluación'},
                {'criterio': 'Viabilidad comercial','estrellas': '3/5', 'obs': 'Pendiente evaluación'},
            ],
            'veredicto':      'CON MEJORAS',
            'veredicto_texto': 'Informe preliminar generado automáticamente. Requiere lectura completa por la asesora para evaluación definitiva.',
            'lector_primario':   'Por determinar',
            'lector_secundario': 'Por determinar',
            'comparable':        'Por determinar',
            'precio':            'Por determinar',
            'notas':             [
                f'Manuscrito procesado automáticamente el {fecha_str}.',
                f'Capítulos detectados: {num_caps}.',
                'Este informe es preliminar. La asesora debe completar la evaluación.',
            ],
        }

        informe_bytes = generar_informe(datos_informe)

        # 5. Devolver JSON con ambos PDFs en base64
        return jsonify({
            'ok':                True,
            'titulo':            titulo,
            'autor':             autor,
            'genero':            'Novela',
            'palabras':          palabras,
            'capitulos':         num_caps,
            'paginas_estimadas': paginas_est,
            'asesora':           asesora,
            'fecha':             fecha_str,
            'informe_pdf':   base64.b64encode(informe_bytes).decode(),
            'preview_pdf':   base64.b64encode(preview_bytes).decode(),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
