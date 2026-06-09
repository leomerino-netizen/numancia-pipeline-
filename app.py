"""
Editorial Numancia — API de generación de documentos
Endpoints: /presupuesto  /informe  /preview  /maqueta  /pack-promocion
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
from corrector_aplicado import (
    crear_job_correccion,
    get_job_status,
    get_job_resultado,
    limpiar_jobs_antiguos,
)
from pack_promocion_prompt import generar_pack_promocion
from pack_promocion_jobs import (
    crear_job_pack,
    get_pack_status,
    limpiar_pack_jobs_antiguos,
)

app = Flask(__name__)
CORS(
        app,
        resources={r"/*": {"origins": [
                    r"https://([a-z0-9-]+\.)*lovableproject\.com$",
                    r"https://([a-z0-9-]+\.)*lovable\.app$",
                    "https://valoracion.editorialnumancia.com",
                    "https://numancia-scribe.lovable.app",
        ]}},
        supports_credentials=True,
        methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        max_age=86400,
)

# 64 MB: cubre PDF de manuscrito grande + portada en alta resolución
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024

API_KEY = os.environ.get('NUMANCIA_API_KEY', '')


def checkauth():
    if not API_KEY:
        return  # sin clave configurada → abierto (dev)
    key = request.headers.get('X-API-Key', '')
    if key != API_KEY:
        abort(401, 'API key inválida')


def pdfresponse(pdf_bytes: bytes, filename: str):
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


# ── Fallback de estrellas (compartido entre /procesar-manuscrito y /generar-informe-pdf)
def aplicarfallback_estrellas(eval_list, veredicto):
    """
    Si Claude (o Lovable) devolvió 'N/5', '0/5', placeholder o cadena vacía,
    aplica valores realistas según el veredicto. Devuelve la lista corregida.
    """
    import re as reest
    veredicto_real = (veredicto or 'CON MEJORAS').upper()
    if 'PUBLICABLE' in veredicto_real and 'CON' not in veredicto_real:
        puntos_default = ['4/5', '4/5', '4/5', '4/5', '4/5']
    elif 'CON MEJORAS' in veredicto_real or 'MEJORAS' in veredicto_real:
        puntos_default = ['3/5', '3/5', '3/5', '4/5', '3/5']
    else:  # REQUIERE REVISIÓN u otros
        puntos_default = ['2/5', '2/5', '2/5', '3/5', '2/5']

    eval_corregido = []
    fallback_activado = False
    for i, item in enumerate(eval_list or []):
        if not isinstance(item, dict):
            continue
        estrellas_raw = str(item.get('estrellas', '')).strip()
        m = reest.search(r'[1-5]', estrellas_raw)
        es_invalida = (
            not m
            or estrellas_raw in ('0/5', 'N/5', 'X/5', 'ENTRE_1_Y_5_ENTERO/5', '')
            or estrellas_raw.upper().startswith('N')
        )
        if es_invalida:
            estrellas_final = puntos_default[i] if i < len(puntos_default) else '3/5'
            fallback_activado = True
            print(f'[fallback] item {i} ({item.get("criterio","?")!r}): '
                  f'{estrellas_raw!r} → {estrellas_final!r}', flush=True)
        else:
            # Normalizar: si Claude devolvió "4" sin "/5", añadir
            if '/' not in estrellas_raw:
                estrellas_final = f'{m.group()}/5'
            else:
                estrellas_final = estrellas_raw
        eval_corregido.append({
            'criterio': item.get('criterio', ''),
            'estrellas': estrellas_final,
            'obs': item.get('obs', ''),
        })

    if fallback_activado:
        print(f'[fallback] ⚠️ Activado para veredicto={veredicto_real!r}', flush=True)
    return eval_corregido


# ── Health check ──────────────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def health():
    # Lista dinámica de todos los endpoints POST registrados en Flask
    rutas = sorted({str(r) for r in app.url_map.iter_rules()
                    if 'POST' in r.methods and 'static' not in str(r)})
    return jsonify({
        'status': 'ok',
        'service': 'Editorial Numancia — Document API',
        'version': '1.2.0',
        'endpoints': rutas,
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
      "asesora": "laura",
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
    checkauth()
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
        return pdfresponse(pdf, filename)
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
    checkauth()
    try:
        d = request.get_json(force=True)
        pdf = generar_informe(d)
        titulo_safe = d.get('titulo', 'informe').replace(' ', '_')[:30]
        return pdfresponse(pdf, f"informe_{titulo_safe}.pdf")
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
    checkauth()
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
        return pdfresponse(pdf, f"preview_{titulo_safe}.pdf")
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
    checkauth()
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
                    ms_pdf, info = parsear_pdf(contenido)
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
            return pdfresponse(pdf, f"Maqueta completa - {titulo_safe}.pdf")

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
        return pdfresponse(pdf, f"Maqueta completa - {titulo_safe}.pdf")

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
    checkauth()
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
    checkauth()
    try:
        if 'pdf' not in request.files:
            return jsonify({'error': 'Campo "pdf" requerido'}), 400
        pdf_bytes = request.files['pdf'].read()
        datos = extraer_presupuesto(pdf_bytes)

        if request.form.get('asesora'):
            datos['asesora'] = request.form['asesora']

        if request.form.get('overrides'):
            import json
            overrides = json.loads(request.form['overrides'])
            datos.update(overrides)

        pdf_out = generar_presupuesto(datos)
        cliente_safe = datos.get('cliente', 'cliente').split()[0]
        num = datos.get('num_presupuesto', '0')
        return pdfresponse(pdf_out, f"propuesta_{num}_{cliente_safe}.pdf")
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /generar-informe-pdf ─────────────────────────────────────────────────
@app.route('/generar-informe-pdf', methods=['POST'])
def generar_informe_pdf():
    """
    Recibe el JSON de datos del informe (potencialmente editado por el asesor)
    y devuelve solo el PDF del informe de lectura y valoración.
    """
    checkauth()
    try:
        d = request.get_json(force=True) or {}

        print(f'[generar_informe_pdf] payload keys: {list(d.keys())}', flush=True)
        eval_recibido = d.get('eval') or d.get('evaluacion') or []
        print(f'[generar_informe_pdf] eval recibido ({len(eval_recibido)} items): '
              f'{[(i.get("criterio"), i.get("estrellas")) for i in eval_recibido if isinstance(i, dict)]}',
              flush=True)
        print(f'[generar_informe_pdf] veredicto: {d.get("veredicto")!r}', flush=True)

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

        d['eval'] = aplicarfallback_estrellas(
            d.get('eval', []),
            d.get('veredicto', 'CON MEJORAS')
        )

        orto = d.get('ortotipo')
        if orto and 'incidencias' in orto and 'total' in orto and 'total_incidencias' not in orto:
            d['ortotipo'] = {
                'total_incidencias':    orto.get('total', 0),
                'categorias_afectadas': orto.get('categorias', 0),
                'resumen_corrector':    orto.get('resumen', ''),
                'incidencias':          orto.get('incidencias', []),
            }

        d['numero_presupuesto'] = (d.get('numero_presupuesto') or '').strip()
        if d['numero_presupuesto']:
            print(f'[generar_informe_pdf] numero_presupuesto={d["numero_presupuesto"]!r}', flush=True)

        pdf = generar_informe(d)
        titulo_safe = ''.join(c if c.isalnum() or c in ' -_' else '' for c in d.get('titulo','informe'))[:50].strip()
        return pdfresponse(pdf, f'Informe de lectura y valoracion - {titulo_safe}.pdf')
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── POST /generar-preview-pdf ─────────────────────────────────────────────────
@app.route('/generar-preview-pdf', methods=['POST'])
def generar_preview_pdf():
    """
    Recibe el JSON con titulo + autor + (bloques | docx_base64 | texto)
    y devuelve solo el PDF del preview con marca de agua.
    """
    checkauth()
    try:
        d = request.get_json(force=True) or {}

        titulo         = (d.get('titulo') or 'Sin titulo').strip()
        autor          = (d.get('autor') or '').strip()
        dedicatoria    = (d.get('dedicatoria') or '').strip()
        epigrafe       = (d.get('epigrafe') or '').strip()
        epigrafe_autor = (d.get('epigrafe_autor') or '').strip()
        asesora        = (d.get('asesora') or 'laura').strip().lower()
        tipo_papel     = (d.get('tipo_papel') or 'Papel novela ahuesado de 80 g/m²').strip()
        acabado        = (d.get('acabado') or 'Tapa blanda con solapas, encuadernación fresada').strip()

        bloques_raw = d.get('bloques')
        tiene_bloques = isinstance(bloques_raw, list) and len(bloques_raw) > 0
        tiene_docx    = bool(d.get('docx_base64'))
        tiene_texto   = bool(d.get('texto'))

        print(f'[preview] titulo={titulo!r} autor={autor!r} '
              f'bloques={len(bloques_raw) if tiene_bloques else 0} '
              f'docx={tiene_docx} texto={tiene_texto} '
              f'dedi={bool(dedicatoria)} epi={bool(epigrafe)}')

        if tiene_bloques:
            from docx_parser import Bloque
            bloques_lista = []
            for b in bloques_raw:
                if not isinstance(b, dict): continue
                if b.get('incluido') is False: continue
                tipo  = b.get('tipo','parrafo')
                texto = (b.get('texto') or '').strip()
                if not texto and tipo != 'pagina_blanca': continue
                html  = b.get('html') or texto
                primer_parr = bool(b.get('primer_parr', False))
                bloques_lista.append(Bloque(tipo, texto, html, primer_parr=primer_parr))

            siguiente_es_primero = False
            for bl in bloques_lista:
                if bl.tipo == 'cap_titulo':
                    siguiente_es_primero = True
                elif bl.tipo in ('parrafo','dialogo') and siguiente_es_primero:
                    bl.primer_parr = True
                    siguiente_es_primero = False

            print(f'[preview] generando con {len(bloques_lista)} bloques útiles')
            if not bloques_lista:
                bloques_lista = [Bloque('parrafo', '(sin contenido)', '(sin contenido)')]

            pdf = generar_preview('', titulo, autor, bloques=bloques_lista,
                                  dedicatoria=dedicatoria,
                                  epigrafe=epigrafe, epigrafe_autor=epigrafe_autor,
                                  asesora=asesora,
                                  tipo_papel=tipo_papel, acabado=acabado)
        elif tiene_docx:
            print(f'[preview] generando desde docx_base64')
            docx_b = base64.b64decode(d['docx_base64'])
            pdf = generar_preview('', titulo, autor, docx_bytes=docx_b,
                                  dedicatoria=dedicatoria,
                                  epigrafe=epigrafe, epigrafe_autor=epigrafe_autor,
                                  asesora=asesora,
                                  tipo_papel=tipo_papel, acabado=acabado)
        else:
            print(f'[preview] generando desde texto plano')
            pdf = generar_preview(d.get('texto',''), titulo, autor,
                                  dedicatoria=dedicatoria,
                                  epigrafe=epigrafe, epigrafe_autor=epigrafe_autor,
                                  asesora=asesora,
                                  tipo_papel=tipo_papel, acabado=acabado)

        if not pdf:
            print(f'[preview] ERROR: generar_preview devolvió bytes vacíos')
            return jsonify({'error': 'No se pudo generar el PDF (bytes vacíos)'}), 500

        print(f'[preview] PDF generado: {len(pdf)//1024} KB')
        titulo_safe = ''.join(c if c.isalnum() or c in ' -_' else '' for c in titulo)[:50].strip() or 'preview'

        formato = (d.get('format') or '').lower()
        accept  = (request.headers.get('Accept') or '').lower()
        quiere_json = formato == 'base64' or 'application/json' in accept

        if quiere_json:
            print(f'[preview] devolviendo JSON con base64')
            return jsonify({
                'ok': True,
                'preview_pdf': base64.b64encode(pdf).decode('ascii'),
                'filename': f'Maquetacion previa borrador - {titulo_safe}.pdf',
                'size_kb': len(pdf) // 1024,
            })

        return pdfresponse(pdf, f'Maquetacion previa borrador - {titulo_safe}.pdf')

    except Exception as e:
        print(f'[preview] EXCEPCIÓN: {type(e).__name__}: {e}')
        traceback.print_exc()
        return jsonify({'error': f'{type(e).__name__}: {str(e)}'}), 500


def bloquespara_preview(bloques, max_bloques=140):
    """
    Convierte la lista de Bloque del parser en un array JSON simple
    para que la asesora edite los párrafos antes de generar el preview.
    Limita a max_bloques (~20 páginas A5).
    """
    salida = []
    for b in bloques[:max_bloques]:
        salida.append({
            'tipo':        b.tipo,
            'texto':       b.texto,
            'html':        b.html or b.texto,
            'primer_parr': bool(getattr(b, 'primer_parr', False)),
            'incluido':    True,
        })
    return salida


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
    checkauth()
    try:
        archivo = None
        for nombre_campo in ('docx', 'pdf', 'manuscrito', 'file', 'archivo'):
            if nombre_campo in request.files:
                archivo = request.files[nombre_campo]
                break
        if archivo is None and request.files:
            archivo = next(iter(request.files.values()))
        if archivo is None:
            return jsonify({'error': 'No se ha enviado ningún archivo. Use el campo "docx", "pdf" o "manuscrito".'}), 400

        contenido_bytes = archivo.read()
        nombre_fichero  = archivo.filename or 'manuscrito'

        asesora    = request.form.get('asesora', 'laura')
        titulo_ovr = request.form.get('titulo', '')
      autor_ovr = None
# o
autor_ovr = request.form.get("autor_ovr", "")
