"""
Extrae campos de presupuestos PDF:
  - Formato Printcolorweb.com  (web pública)
  - Formato Editorial Numancia (PDF corporativo)
"""
import re, io
import pdfplumber

MESES = {
    '01':'enero','02':'febrero','03':'marzo','04':'abril',
    '05':'mayo','06':'junio','07':'julio','08':'agosto',
    '09':'septiembre','10':'octubre','11':'noviembre','12':'diciembre'
}

def _eur(txt):
    txt = re.sub(r'[€$\s]','', str(txt))
    txt = txt.replace('.','').replace(',','.')
    try: return round(float(txt), 2)
    except: return 0.0

def _fecha_es(txt):
    m = re.search(r'(\d{1,2})/(\d{2})/(\d{4})', txt)
    if m:
        d, mo, y = m.group(1), m.group(2), m.group(3)
        return f"{int(d)} de {MESES.get(mo,mo)} de {y}"
    return txt.strip()

def _leer(src):
    ctx = pdfplumber.open(io.BytesIO(src) if isinstance(src,(bytes,bytearray)) else src)
    with ctx as pdf:
        return '\n'.join(p.extract_text() or '' for p in pdf.pages)

def _es_printcolorweb(t):
    return bool(re.search(r'Nº de Presupuesto|Titulo del libro|printcolorweb\.com', t, re.I))

def _printcolorweb(t):
    d = {}
    m = re.search(r'Nº de Presupuesto:\s*#?(\d+)', t, re.I)
    d['num_presupuesto'] = m.group(1) if m else ''

    m = re.search(r'Nº de Presupuesto:.*?(\d{1,2}/\d{2}/\d{4})', t, re.I)
    d['fecha'] = _fecha_es(m.group(1)) if m else ''

    m = re.search(r'Nombre:\s*(.+)', t)
    d['cliente'] = m.group(1).strip() if m else ''

    m = re.search(r'Titulo del libro:\s*([^\n\d€]+?)(?:\s+\d|\s*\n)', t, re.I)
    d['obra'] = m.group(1).strip() if m else d.get('cliente','')

    d['genero'] = 'Novela'

    m = re.search(r'P[aá]ginas:\s*(\d+)', t, re.I)
    d['paginas'] = int(m.group(1)) if m else 0

    m = re.search(r'Formato:\s*(A\d)', t, re.I)
    d['formato'] = m.group(1) if m else 'A5'

    m = re.search(r'Tinta:\s*(B/N|Color|Blanco)', t, re.I)
    d['color_interior'] = 'B/N' if (m and 'B' in m.group(1).upper()) else 'Color'

    m = re.search(r'Tipo papel y gramaje:\s*(.+?)(?:\n|Tipo)', t, re.I)
    d['papel'] = m.group(1).strip() if m else 'Papel novela 80 gr'

    m = re.search(r'Tipo papel de la cubierta:\s*(\d+\s*gr)', t, re.I)
    d['cubierta'] = m.group(1).replace(' ','') if m else '300gr'

    m = re.search(r'Laminado\s+(brillante|mate)', t, re.I)
    d['laminado'] = m.group(1).lower() if m else 'brillante'

    m = re.search(r'Tipo de Encuadernaci[oó]n:\s*(\w+)', t, re.I)
    d['encuadernacion'] = m.group(1).lower() if m else 'fresada'

    m = re.search(r'Lomo:\s*(\d+\s*mm)', t, re.I)
    d['lomo'] = m.group(1).replace(' ','') if m else '10mm'

    # Cantidad + total impresión
    m = re.search(r'Titulo del libro:.+?(\d+)\s*€\s*[\d\.,]+\s*€\s*[\d\.,]+\s*€\s*([\d\.,]+)', t, re.I)
    if m:
        d['cantidad'] = int(m.group(1))
        total_imp = _eur(m.group(2))
        d['precio_unitario'] = round(total_imp / d['cantidad'], 2) if d['cantidad'] else 0.0
    else:
        d['cantidad'] = 100
        d['precio_unitario'] = 0.0

    m = re.search(r'-(\d+)%\s+Imprime', t, re.I)
    d['descuento_pct'] = int(m.group(1)) if m else 0
    dto = d['descuento_pct']
    d['precio_descuento'] = round(d['precio_unitario']*(1-dto/100), 2) if dto else d['precio_unitario']

    # Maquetación total (último número de la línea)
    m = re.search(r'Maquetaci[oó]n profesional.+?€\s*[\d\.,]+\s*€\s*[\d\.,]+\s*€\s*([\d\.,]+)', t, re.I|re.DOTALL)
    d['precio_maquetacion'] = _eur(m.group(1)) if m else 322.39

    m = re.search(r'Servicios extras.+?€\s*[\d\.,]+\s*€\s*[\d\.,]+\s*€\s*([\d\.,]+)', t, re.I|re.DOTALL)
    d['precio_legal'] = _eur(m.group(1)) if m else 114.40

    d['asesora'] = 'laura'
    return d

def _numancia(t):
    d = {}
    m = re.search(r'No\s+(\d+)', t)
    d['num_presupuesto'] = m.group(1) if m else ''

    m = re.search(r'No\s+\d+\s*\|\s*(.+?)\n', t)
    d['fecha'] = m.group(1).strip() if m else ''

    d['asesora'] = 'debora' if re.search(r'debora|d[eé]bora',t,re.I) else \
                   'juan'   if re.search(r'juan\s+mu[nñ]oz',t,re.I) else 'laura'

    m = re.search(r'PARA\s+ASESORA EDITORIAL\s*\n(.+?)(?:\n|Laura|D[eé]bora|Juan)',t,re.I)
    d['cliente'] = m.group(1).strip() if m else ''

    m = re.search(r'Obra:\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(\d+)\s*p[aá]ginas\s*\|\s*Formato\s*(\S+)',t,re.I)
    if m:
        d['obra']=m.group(1).strip(); d['genero']=m.group(2).strip()
        d['paginas']=int(m.group(3)); d['formato']=m.group(4).strip()
    else:
        d.update({'obra':'','genero':'Novela','paginas':0,'formato':'A5'})

    m = re.search(r'([\d,\.]+)\s*EUR\s*-(\d+)%', t)
    d['precio_unitario'] = _eur(m.group(1)) if m else 0.0
    d['descuento_pct']   = int(m.group(2)) if m else 0

    m = re.search(r'([\d,\.]+)\s*EUR\s*\n+por ejemplar', t)
    d['precio_descuento'] = _eur(m.group(1)) if m else round(d['precio_unitario']*(1-d['descuento_pct']/100),2)

    m = re.search(r'(\d+)\s+ejemplares\s*=', t)
    d['cantidad'] = int(m.group(1)) if m else 100

    m = re.search(r'Interior en\s+([\w/]+)', t, re.I)
    d['color_interior'] = m.group(1).strip() if m else 'B/N'

    m = re.search(r'(\d+)\s*p[aá]ginas\s*\|\s*([^|]+)\s*\|\s*Cubierta\s*(\S+)',t,re.I)
    d['papel']    = m.group(2).strip() if m else 'Papel novela 80 gr'
    d['cubierta'] = m.group(3).strip() if m else '300gr'

    m = re.search(r'Laminado\s+(\w+)', t, re.I)
    d['laminado'] = m.group(1).strip() if m else 'brillante'

    m = re.search(r'Encuadernaci[oó]n\s+(\w+)', t, re.I)
    d['encuadernacion'] = m.group(1).strip() if m else 'fresada'

    m = re.search(r'Lomo\s+([\w]+mm)', t, re.I)
    d['lomo'] = m.group(1).strip() if m else '10mm'

    m = re.search(r'Maquetaci[oó]n y dise[nñ]o editorial.*?EUR\s*([\d,\.]+)',t,re.I)
    d['precio_maquetacion'] = _eur(m.group(1)) if m else 322.39

    m = re.search(r'Servicios legales y distribuci[oó]n.*?EUR\s*([\d,\.]+)',t,re.I)
    d['precio_legal'] = _eur(m.group(1)) if m else 114.40

    return d

def extraer_presupuesto(src):
    t = _leer(src)
    return _printcolorweb(t) if _es_printcolorweb(t) else _numancia(t)

if __name__ == '__main__':
    import json, sys
    f = sys.argv[1] if len(sys.argv)>1 else '/mnt/user-data/uploads/Presupuesto_010212.pdf'
    print(json.dumps(extraer_presupuesto(f), ensure_ascii=False, indent=2))
