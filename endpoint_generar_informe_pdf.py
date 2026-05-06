# =============================================================================
# SUSTITUIR el endpoint /generar-informe-pdf en app.py
# =============================================================================
# Localiza en app.py el bloque que empieza por:
#     @app.route('/generar-informe-pdf', methods=['POST'])
# (o @app.post('/generar-informe-pdf'))
#
# Sustituye TODO el cuerpo de esa función por este:
# =============================================================================

@app.route('/generar-informe-pdf', methods=['POST'])
def generar_informe_pdf():
    try:
        d = request.get_json(force=True) or {}

        # ── DEBUG: log de lo que llega de Lovable ──────────────────────
        eval_recibido = d.get('eval', []) or []
        print(
            f'[generar_informe_pdf] payload keys: {list(d.keys())}',
            flush=True
        )
        print(
            f'[generar_informe_pdf] eval recibido ({len(eval_recibido)} items): '
            f'{[(i.get("criterio"), i.get("estrellas")) for i in eval_recibido]}',
            flush=True
        )
        print(
            f'[generar_informe_pdf] veredicto: {d.get("veredicto")!r}',
            flush=True
        )

        # ── FALLBACK: corrige estrellas placeholder antes de renderizar ──
        try:
            from informe_fixes import aplicar_fallback_estrellas
            d = aplicar_fallback_estrellas(d)
        except ImportError as e:
            print(f'[generar_informe_pdf] ⚠️ informe_fixes no disponible: {e}', flush=True)

        # ── Generar PDF ────────────────────────────────────────────────
        pdf = generar_informe(d)

        return send_file(
            io.BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'informe_{d.get("titulo", "manuscrito")}.pdf'
        )

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f'[generar_informe_pdf] ❌ ERROR: {e}\n{tb}', flush=True)
        return jsonify({'error': str(e), 'trace': tb}), 500
