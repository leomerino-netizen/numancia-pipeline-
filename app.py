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
        d = request.get_json(force=True)
        pdf = generar_preview(d['texto'], d['titulo'], d['autor'])
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
        d = request.get_json(force=True)
        pdf = generar_maqueta_completa(
            texto=d['texto'],
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
