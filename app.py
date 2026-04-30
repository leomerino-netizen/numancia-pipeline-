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
    Genera la maqueta completa A5 lista para imprenta.
    
    Acepta multipart/form-data:
      - docx           (file, opcional pero recomendado)
      - pdf            (file, alternativa a docx)
      - titulo         (string, requerido)
      - autor          (string)
      - anyo           (string, default "2026")
      - dedicatoria    (string)
      - epigrafe       (string)
      - epigrafe_autor (string)
      - papel          (string, default "Papel offset 90 g/m²")
      - cubierta_tipo  (string, default "Cartulina 300 g/m²")
      - laminado       (string, default "Laminado brillante")
    
    También acepta JSON con los mismos campos + texto y docx_base64.
    
    Devuelve: PDF binario con Content-Type application/pdf
    """
    _check_auth()
    try:
        # ── Modo multipart ────────────────────────────────────────────────
        if request.content_type and 'multipart' in request.content_type:
            archivo = None
            for nc in ('docx', 'pdf', 'manuscrito', 'file', 'archivo'):
                if nc in request.files:
                    archivo = request.files[nc]; break
            if archivo is None and request.files:
                archivo = next(iter(request.files.values()))

            docx_bytes = None
            texto_pdf  = ''
            if archivo:
                contenido = archivo.read()
                nombre    = (archivo.filename or '').lower()
                es_pdf    = nombre.endswith('.pdf') or contenido[:4] == b'%PDF'
                if es_pdf:
                    from pdf_a_texto import parsear_pdf
                    ms_pdf, _info = parsear_pdf(contenido)
                    texto_pdf = '\n\n'.join(b.texto for b in ms_pdf.bloques)
                else:
                    docx_bytes = contenido

            titulo = request.form.get('titulo', '').strip() or 'Sin título'
            autor  = request.form.get('autor', '').strip()
            anyo   = request.form.get('anyo', '2026')

            pdf = generar_maqueta_completa(
                texto          = texto_pdf,
                titulo         = titulo,
                autor          = autor,
                anyo           = anyo,
                dedicatoria    = request.form.get('dedicatoria', ''),
                epigrafe       = request.form.get('epigrafe', ''),
                epigrafe_autor = request.form.get('epigrafe_autor', ''),
                docx_bytes     = docx_bytes,
                papel          = request.form.get('papel',         'Papel offset 90 g/m²'),
                cubierta_tipo  = request.form.get('cubierta_tipo', 'Cartulina 300 g/m²'),
                laminado       = request.form.get('laminado',      'Laminado brillante'),
                isbn           = request.form.get('isbn', ''),
                deposito_legal = request.form.get('deposito_legal', ''),
            )
            titulo_safe = ''.join(c if c.isalnum() or c in ' -_' else '' for c in titulo)[:60].strip()
            return _pdf_response(pdf, f"Maqueta completa - {titulo_safe}.pdf")

        # ── Modo JSON ─────────────────────────────────────────────────────
        d = request.get_json(force=True)
        docx_b = None
        if d.get('docx_base64'):
            import base64 as _b64
            docx_b = _b64.b64decode(d['docx_base64'])
        pdf = generar_maqueta_completa(
            texto          = d.get('texto', ''),
            titulo         = d.get('titulo', 'Sin título'),
            autor          = d.get('autor', ''),
            anyo           = d.get('anyo', '2026'),
            dedicatoria    = d.get('dedicatoria', ''),
            epigrafe       = d.get('epigrafe', ''),
            epigrafe_autor = d.get('epigrafe_autor', ''),
            docx_bytes     = docx_b,
            papel          = d.get('papel',         'Papel offset 90 g/m²'),
            cubierta_tipo  = d.get('cubierta_tipo', 'Cartulina 300 g/m²'),
            laminado       = d.get('laminado',      'Laminado brillante'),
            isbn           = d.get('isbn', ''),
            deposito_legal = d.get('deposito_legal', ''),
        )
        titulo_safe = ''.join(c if c.isalnum() or c in ' -_' else '' for c in d.get('titulo','maqueta'))[:60].strip()
        return _pdf_response(pdf, f"Maqueta completa - {titulo_safe}.pdf")

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



@app.route('/generar-informe-pdf', methods=['POST'])
def generar_informe_pdf():
    """
    Recibe el JSON de datos del informe (potencialmente editado por el asesor)
    y devuelve solo el PDF del informe de lectura y valoración.
    
    Body JSON con todos los campos del informe:
      titulo, autor, genero, ambientacion, extension,
      fecha, evaluado_por, sinopsis_i, sinopsis_ii, sinopsis_iii,
      eval (lista), veredicto, veredicto_texto,
      lector_primario, lector_secundario, comparable, precio,
      notas (lista), carta_autor, ortotipo (objeto opcional)
    """
    _check_auth()
    try:
        d = request.get_json(force=True)
        # Si viene anidado como en /procesar-manuscrito, normalizar
        if 'sinopsis' in d and isinstance(d['sinopsis'], dict):
            d['sinopsis_i']  = d['sinopsis'].get('i','')
            d['sinopsis_ii'] = d['sinopsis'].get('ii','')
            d['sinopsis_iii']= d['sinopsis'].get('iii','')
        if 'publico' in d and isinstance(d['publico'], dict):
            d['lector_primario']   = d['publico'].get('lector_primario','')
            d['lector_secundario'] = d['publico'].get('lector_secundario','')
            d['comparable']        = d['publico'].get('comparable','')
            d['precio']            = d['publico'].get('precio','')
        if 'evaluacion' in d:
            d['eval'] = d['evaluacion']
        if 'asesora_nombre' in d and not d.get('evaluado_por'):
            d['evaluado_por'] = d['asesora_nombre']

        # Reconstruir ortotipo si viene en formato simplificado
        orto = d.get('ortotipo')
        if orto and 'incidencias' in orto and 'total' in orto and 'total_incidencias' not in orto:
            d['ortotipo'] = {
                'total_incidencias':    orto.get('total', 0),
                'categorias_afectadas': orto.get('categorias', 0),
                'resumen_corrector':    orto.get('resumen', ''),
                'incidencias':          orto.get('incidencias', []),
            }

        pdf = generar_informe(d)
        titulo_safe = ''.join(c if c.isalnum() or c in ' -_' else '' for c in d.get('titulo','informe'))[:50].strip()
        return _pdf_response(pdf, f'Informe de lectura y valoracion - {titulo_safe}.pdf')
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/generar-preview-pdf', methods=['POST'])
def generar_preview_pdf():
    """
    Recibe el JSON con titulo + autor + (docx_base64 O texto)
    y devuelve solo el PDF del preview con marca de agua.
    """
    _check_auth()
    try:
        d = request.get_json(force=True)
        titulo = d.get('titulo','Sin titulo')
        autor  = d.get('autor','')
        docx_b = None
        if d.get('docx_base64'):
            docx_b = base64.b64decode(d['docx_base64'])
        if docx_b:
            pdf = generar_preview('', titulo, autor, docx_bytes=docx_b)
        else:
            pdf = generar_preview(d.get('texto',''), titulo, autor)
        titulo_safe = ''.join(c if c.isalnum() or c in ' -_' else '' for c in titulo)[:50].strip()
        return _pdf_response(pdf, f'Maquetacion previa borrador - {titulo_safe}.pdf')
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
        # Si incluir_pdfs=false, devolvemos solo los datos JSON (más rápido)
        # para que el asesor edite antes de generar los PDFs.
        incluir_pdfs = request.form.get('incluir_pdfs', 'true').lower() != 'false'

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

        informe_bytes = b''
        preview_bytes = b''
        if incluir_pdfs:
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
            'informe_pdf':   base64.b64encode(informe_bytes).decode() if informe_bytes else '',
            'preview_pdf':   base64.b64encode(preview_bytes).decode() if preview_bytes else '',
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
