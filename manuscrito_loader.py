"""
manuscrito_loader.py
────────────────────
Carga el archivo de manuscrito subido por la asesora.
Acepta .docx (formato nativo) o .pdf (se convierte automáticamente).
Devuelve siempre bytes de un .docx válido para alimentar el pipeline
editorial (informe, preview, corrector_aplicado, maqueta).

ADVERTENCIA DE CALIDAD
──────────────────────
La conversión PDF→DOCX es aproximada. Puede:
  • Romper estilos, índice y notas al pie complejas
  • Unir párrafos en bloques densos
  • Fragmentar texto en cajas no editables semánticamente
  • Degradar la corrección ortotipográfica con Track Changes

Editorialmente, lo correcto es exigir al autor el .docx original.
Este módulo existe para no bloquear flujos urgentes cuando solo hay PDF.

DEPENDENCIAS
────────────
Añade al requirements.txt:
    pdf2docx>=0.5.8

(pdf2docx tira de PyMuPDF y python-docx, ambos con wheels para Linux
x86_64; Railway los instala sin compilación nativa adicional.)

USO
───
    from manuscrito_loader import cargar_manuscrito_docx

    raw = request.files['manuscrito'].read()
    nombre = request.files['manuscrito'].filename
    try:
        docx_bytes, info = cargar_manuscrito_docx(raw, nombre)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # docx_bytes siempre es un .docx válido a partir de aquí.
    # Si info['convertido']:
    #     mostrar info['aviso'] al frontend
"""

import io
import os
import tempfile
import zipfile
from typing import Tuple


def _detectar_tipo(blob: bytes) -> str:
    """
    Detecta el tipo real del archivo por su cabecera (magic bytes).
    Devuelve 'pdf', 'docx' o 'unknown'.
    No confía en la extensión del nombre: si el usuario renombra
    un .pdf a .docx, lo detectamos igual.
    """
    if not blob or len(blob) < 4:
        return 'unknown'

    # PDF: cabecera %PDF-
    if blob[:4] == b'%PDF':
        return 'pdf'

    # DOCX: es un ZIP que contiene word/document.xml
    if blob[:2] == b'PK':
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as zf:
                names = zf.namelist()
                if 'word/document.xml' in names:
                    return 'docx'
        except zipfile.BadZipFile:
            return 'unknown'

    return 'unknown'


def _convertir_pdf_a_docx(pdf_bytes: bytes) -> bytes:
    """
    Convierte PDF a DOCX usando pdf2docx.
    Trabaja con tempfiles porque la librería opera sobre rutas.
    Devuelve los bytes del .docx resultante.
    """
    try:
        from pdf2docx import Converter
    except ImportError as e:
        raise RuntimeError(
            'pdf2docx no está instalado. Añade `pdf2docx>=0.5.8` al '
            'requirements.txt y redeploya el backend.'
        ) from e

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, 'in.pdf')
        docx_path = os.path.join(tmpdir, 'out.docx')

        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)

        cv = Converter(pdf_path)
        try:
            # start=0, end=None convierte todas las páginas.
            cv.convert(docx_path, start=0, end=None)
        finally:
            cv.close()

        with open(docx_path, 'rb') as f:
            return f.read()


def cargar_manuscrito_docx(file_bytes: bytes,
                           nombre_original: str = '') -> Tuple[bytes, dict]:
    """
    Punto de entrada único: garantiza que el pipeline reciba siempre
    un .docx válido, convirtiendo desde PDF si hace falta.

    Parámetros
    ──────────
    file_bytes : bytes
        Contenido binario tal cual lo subió la asesora.
    nombre_original : str
        Nombre del archivo (para logging y mensajes de error).

    Devuelve
    ────────
    (docx_bytes, info)
        docx_bytes : bytes
            .docx válido para alimentar el pipeline editorial.
        info : dict
            {
              'tipo_original': 'pdf' | 'docx',
              'convertido': bool,
              'nombre': str,
              'aviso': str   # vacío si no se convirtió
            }

    Lanza
    ─────
    ValueError si el archivo no es PDF ni DOCX (incluye RTF, ODT,
    .doc antiguo, imágenes escaneadas sin OCR, etc.).
    """
    tipo = _detectar_tipo(file_bytes)

    if tipo == 'docx':
        return file_bytes, {
            'tipo_original': 'docx',
            'convertido': False,
            'nombre': nombre_original,
            'aviso': '',
        }

    if tipo == 'pdf':
        print(f'[manuscrito_loader] convirtiendo PDF→DOCX: {nombre_original}',
              flush=True)
        docx_bytes = _convertir_pdf_a_docx(file_bytes)
        return docx_bytes, {
            'tipo_original': 'pdf',
            'convertido': True,
            'nombre': nombre_original,
            'aviso': (
                'El manuscrito se entregó en PDF y se convirtió automáticamente '
                'a Word. La conversión puede haber alterado el formato (estilos, '
                'notas al pie, índice). Para máxima calidad editorial, pide al '
                'autor el archivo .docx original exportado desde Word.'
            ),
        }

    raise ValueError(
        f'El archivo «{nombre_original or "subido"}» no es un Word (.docx) '
        f'ni un PDF (.pdf). Tipo detectado: «{tipo}». '
        f'Si el archivo es un .doc antiguo de Word, ábrelo en Word y guárdalo '
        f'como «Documento de Word (.docx)». Si es otro formato (RTF, ODT, '
        f'imagen escaneada…), conviértelo previamente.'
    )


# Helper para uso CLI / testing
if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print('Uso: python manuscrito_loader.py <entrada> <salida.docx>')
        sys.exit(1)
    entrada, salida = sys.argv[1], sys.argv[2]
    with open(entrada, 'rb') as f:
        raw = f.read()
    try:
        docx_bytes, info = cargar_manuscrito_docx(raw, entrada)
    except ValueError as e:
        print(f'Error: {e}')
        sys.exit(2)
    with open(salida, 'wb') as f:
        f.write(docx_bytes)
    print(f'OK · tipo_original={info["tipo_original"]} '
          f'convertido={info["convertido"]}')
    if info['aviso']:
        print(f'Aviso: {info["aviso"]}')
