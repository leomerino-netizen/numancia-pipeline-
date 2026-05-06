"""
informe_fixes.py
================
Parches para informe_gen.py — soluciona dos bugs detectados en producción:

1) Estrellas siempre grises porque eval[].estrellas llega como "0/5" o "N/5"
   (placeholder no sustituido por Claude o fallback no activado en el endpoint
   generar_informe_pdf).

2) ValueError "saw </b> instead of expected </font>" cuando el corrector
   preliminar genera HTML mal balanceado (cierre </b> huérfano dentro de un
   <font>).

USO en informe_gen.py:
----------------------
Al inicio del archivo:

    from informe_fixes import aplicar_fallback_estrellas, sanitizar_html

Como PRIMERA línea de generar_informe(d):

    d = aplicar_fallback_estrellas(d)

En cada Paragraph que reciba HTML dinámico (especialmente celda_derecha
en línea 485 que es la que estaba reventando):

    Paragraph(sanitizar_html(texto_html), estilo)
"""

import re


# ─────────────────────────────────────────────────────────────────────────────
# 1) Fallback de estrellas
# ─────────────────────────────────────────────────────────────────────────────

def aplicar_fallback_estrellas(d: dict) -> dict:
    """
    Corrige eval[].estrellas si vienen como placeholder.

    Se ejecuta al inicio de generar_informe(), así funciona tanto si el
    endpoint es procesar_manuscrito como si es generar_informe_pdf
    (que recibe d directo desde Lovable y antes se saltaba el fallback).
    """
    eval_list = d.get('eval', []) or []
    if not eval_list:
        return d

    valores = [str(item.get('estrellas', '')).strip() for item in eval_list]
    es_placeholder = all(
        v in ('N/5', '0/5', '', 'X/5') or v.upper().startswith('N')
        for v in valores
    )

    if not es_placeholder:
        print(f'[informe] eval real recibido, sin fallback: {valores}', flush=True)
        return d

    veredicto = str(d.get('veredicto', '')).upper()
    if 'PUBLICABLE' in veredicto and 'MEJORAS' not in veredicto:
        defaults = {'estructura': '4/5', 'voz': '4/5', 'personajes': '4/5',
                    'genero': '4/5', 'corrección': '3/5', 'correccion': '3/5',
                    'público': '4/5', 'publico': '4/5', 'potencial': '4/5'}
        default_general = '4/5'
    elif 'MEJORAS' in veredicto or 'CON MEJORAS' in veredicto:
        defaults = {'estructura': '4/5', 'voz': '3/5', 'personajes': '3/5',
                    'genero': '3/5', 'corrección': '2/5', 'correccion': '2/5',
                    'público': '3/5', 'publico': '3/5', 'potencial': '3/5'}
        default_general = '3/5'
    else:
        defaults = {'estructura': '3/5', 'voz': '2/5', 'personajes': '2/5',
                    'genero': '2/5', 'corrección': '2/5', 'correccion': '2/5',
                    'público': '2/5', 'publico': '2/5', 'potencial': '2/5'}
        default_general = '2/5'

    for item in eval_list:
        criterio = str(item.get('criterio', '')).lower()
        valor = default_general
        for clave, val in defaults.items():
            if clave in criterio:
                valor = val
                break
        item['estrellas'] = valor

    print(f'[informe] ⚠️ Fallback estrellas activado: veredicto={veredicto!r} '
          f'→ valores={[i.get("estrellas") for i in eval_list]}', flush=True)
    return d


# ─────────────────────────────────────────────────────────────────────────────
# 2) Sanitizador HTML para ReportLab Paragraph
# ─────────────────────────────────────────────────────────────────────────────

def sanitizar_html(texto: str) -> str:
    """
    Limpia HTML mal balanceado antes de pasar a ReportLab Paragraph.

    Soluciona el caso real:
        '... o no me gusta</b></font>. Quieren hacer <font><b>sólo</b></font>...'
                          ↑ </b> huérfano que rompe el parser

    - Elimina cierres </b>, </i> sin apertura previa abierta
    - Cierra <b>, <i>, <font> que queden abiertos al final
    - Descarta </font> huérfanos
    """
    if not texto:
        return texto

    s = str(texto)

    # Balancear <b> e <i> (sin atributos, simples)
    for tag in ('b', 'i'):
        resultado = []
        abiertos = 0
        partes = re.split(rf'(<{tag}\b[^>]*>|</{tag}>)', s, flags=re.IGNORECASE)
        for parte in partes:
            if re.match(rf'<{tag}\b', parte, flags=re.IGNORECASE):
                abiertos += 1
                resultado.append(parte)
            elif re.match(rf'</{tag}>', parte, flags=re.IGNORECASE):
                if abiertos > 0:
                    abiertos -= 1
                    resultado.append(parte)
                # cierre huérfano → se descarta
            else:
                resultado.append(parte)
        if abiertos > 0:
            resultado.append(f'</{tag}>' * abiertos)
        s = ''.join(resultado)

    # Balancear <font> (con atributos)
    resultado = []
    stack_font = 0
    partes = re.split(r'(<font\b[^>]*>|</font>)', s, flags=re.IGNORECASE)
    for parte in partes:
        if re.match(r'<font\b', parte, flags=re.IGNORECASE):
            stack_font += 1
            resultado.append(parte)
        elif re.match(r'</font>', parte, flags=re.IGNORECASE):
            if stack_font > 0:
                stack_font -= 1
                resultado.append(parte)
            # </font> huérfano → se descarta
        else:
            resultado.append(parte)
    if stack_font > 0:
        resultado.append('</font>' * stack_font)
    s = ''.join(resultado)

    return s
