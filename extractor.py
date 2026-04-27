"""
Extrae los campos de un presupuesto PDF generado por Editorial Numancia / Printcolor
y devuelve un dict listo para pasar a generar_presupuesto().
"""
import re
import pdfplumber


def _limpiar(txt: str) -> str:
    return txt.strip().replace('\u00a0', ' ')


def _eur(txt: str) -> float:
    """Convierte 'EUR 322,39' o '3,84' a float."""
    txt = re.sub(r'[^\d,\.]', '', txt.replace('.', '').replace(',', '.'))
    try:
        return float(txt)
    except Exception:
        return 0.0


def extraer_presupuesto(path_o_bytes) -> dict:
    """
    Acepta ruta de archivo o bytes del PDF.
    Devuelve dict con todos los campos del presupuesto.
    """
    if isinstance(path_o_bytes, (bytes, bytearray)):
        import io
        ctx = pdfplumber.open(io.BytesIO(path_o_bytes))
    else:
        ctx = pdfplumber.open(path_o_bytes)

    with ctx as pdf:
        texto = '\n'.join(
            page.extract_text() or '' for page in pdf.pages
        )

    resultado = {}

    # ── Número de presupuesto ─────────────────────────────────────────────────
    m = re.search(r'No\s+(\d+)', texto)
    resultado['num_presupuesto'] = m.group(1) if m else ''

    # ── Fecha ─────────────────────────────────────────────────────────────────
    m = re.search(r'No\s+\d+\s*\|\s*(.+?)\n', texto)
    resultado['fecha'] = _limpiar(m.group(1)) if m else ''

    # ── Asesora ───────────────────────────────────────────────────────────────
    asesora_key = 'laura'
    if re.search(r'debora|d[eé]bora', texto, re.IGNORECASE):
        asesora_key = 'debora'
    elif re.search(r'juan\s+mu[nñ]oz', texto, re.IGNORECASE):
        asesora_key = 'juan'
    elif re.search(r'nancy', texto, re.IGNORECASE):
        asesora_key = 'nancy'
    resultado['asesora'] = asesora_key

    # ── Cliente ───────────────────────────────────────────────────────────────
    # Línea después de "PARA  ASESORA EDITORIAL\n"
    m = re.search(r'PARA\s+ASESORA EDITORIAL\s*\n(.+?)(?:\n|Laura|D[eé]bora|Juan|Nancy)',
                  texto, re.IGNORECASE)
    if m:
        resultado['cliente'] = _limpiar(m.group(1))
    else:
        # fallback: primera línea que no sea cabecera
        for linea in texto.splitlines():
            l = linea.strip()
            if l and not any(x in l for x in ['PROPUESTA', 'No ', 'Validez', 'C/', 'Tel.', 'PARA', 'B839']):
                resultado['cliente'] = l
                break
        else:
            resultado['cliente'] = ''

    # ── Obra, género, páginas, formato ───────────────────────────────────────
    m = re.search(
        r'Obra:\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(\d+)\s*p[aá]ginas\s*\|\s*Formato\s*(\S+)',
        texto, re.IGNORECASE)
    if m:
        resultado['obra']    = _limpiar(m.group(1))
        resultado['genero']  = _limpiar(m.group(2))
        resultado['paginas'] = int(m.group(3))
        resultado['formato'] = _limpiar(m.group(4))
    else:
        resultado.setdefault('obra', '')
        resultado.setdefault('genero', 'Novela')
        resultado.setdefault('paginas', 0)
        resultado.setdefault('formato', 'A5')

    # ── Precio unitario y descuento ───────────────────────────────────────────
    # "4,52 EUR -15%"
    m = re.search(r'([\d,\.]+)\s*EUR\s*-(\d+)%', texto)
    if m:
        resultado['precio_unitario'] = _eur(m.group(1))
        resultado['descuento_pct']   = int(m.group(2))
    else:
        resultado['precio_unitario'] = 0.0
        resultado['descuento_pct']   = 0

    # Precio con descuento — primera línea con "EUR\n{precio}\npor ejemplar"
    m = re.search(r'([\d,\.]+)\s*EUR\s*\n+por ejemplar', texto)
    if m:
        resultado['precio_descuento'] = _eur(m.group(1))
    else:
        pu = resultado['precio_unitario']
        dto = resultado['descuento_pct']
        resultado['precio_descuento'] = round(pu * (1 - dto/100), 2)

    # ── Cantidad ──────────────────────────────────────────────────────────────
    m = re.search(r'(\d+)\s+ejemplares\s*=', texto)
    resultado['cantidad'] = int(m.group(1)) if m else 100

    # ── Especificaciones ──────────────────────────────────────────────────────
    # "Formato A5 (14.8 x 21 cm) | Interior en B/N | Cubierta a color"
    m = re.search(r'Interior en\s+([\w/]+)', texto, re.IGNORECASE)
    resultado['color_interior'] = _limpiar(m.group(1)) if m else 'B/N'

    m = re.search(r'(\d+)\s*p[aá]ginas\s*\|\s*([^|]+)\s*\|\s*Cubierta\s*(\S+)', texto, re.IGNORECASE)
    if m:
        resultado['papel']    = _limpiar(m.group(2))
        resultado['cubierta'] = _limpiar(m.group(3))
    else:
        resultado['papel']    = 'Papel novela 80 gr'
        resultado['cubierta'] = '300gr'

    m = re.search(r'Laminado\s+(\w+)', texto, re.IGNORECASE)
    resultado['laminado'] = _limpiar(m.group(1)) if m else 'brillante'

    m = re.search(r'Encuadernaci[oó]n\s+(\w+)', texto, re.IGNORECASE)
    resultado['encuadernacion'] = _limpiar(m.group(1)) if m else 'fresada'

    m = re.search(r'Lomo\s+([\w]+mm)', texto, re.IGNORECASE)
    resultado['lomo'] = _limpiar(m.group(1)) if m else '10mm'

    # ── Precios de servicios ──────────────────────────────────────────────────
    m = re.search(r'Maquetaci[oó]n y dise[nñ]o editorial.*?EUR\s*([\d,\.]+)', texto, re.IGNORECASE)
    resultado['precio_maquetacion'] = _eur(m.group(1)) if m else 322.39

    m = re.search(r'Servicios legales y distribuci[oó]n.*?EUR\s*([\d,\.]+)', texto, re.IGNORECASE)
    resultado['precio_legal'] = _eur(m.group(1)) if m else 114.40

    return resultado


# ── Test ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import json
    r = extraer_presupuesto('/mnt/user-data/uploads/Presupuesto_10212_Sara.pdf')
    print(json.dumps(r, ensure_ascii=False, indent=2))
