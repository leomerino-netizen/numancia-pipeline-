"""
Editorial Numancia — Pipeline microservicio
POST /procesar         → informe A4 + preview A5 (10 págs con marca de agua)
POST /maqueta-completa → libro completo A5 listo para Printcolor
"""

import os, io, json, base64, anthropic
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import docx2txt

from informe_gen import generar_informe
from preview_gen import generar_preview
from maqueta_gen import generar_maqueta_completa

app = FastAPI(title="Editorial Numancia Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CLAUDE_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


# ─── ANÁLISIS EDITORIAL vía Claude ───────────────────────────────────────────
def analizar_manuscrito(texto: str, asesora: str, palabras: int) -> dict:
    from datetime import date
    today = date.today().strftime("%d/%m/%Y")
    snippet = texto[:14000]

    client = anthropic.Anthropic(api_key=CLAUDE_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": f"""Eres el sistema de análisis editorial de Editorial Numancia.
Analiza el manuscrito y devuelve ÚNICAMENTE un objeto JSON válido, sin texto adicional ni backticks.

Asesora: {asesora}
Fecha: {today}
Palabras totales: {palabras}
Primeras 14.000 caracteres del manuscrito:
---
{snippet}
---

JSON requerido (todos los campos obligatorios):
{{
  "titulo": "título exacto",
  "autor": "nombre o 'Pendiente de confirmar'",
  "genero": "género literario específico",
  "extension": "{palabras} palabras · estimación capítulos · aprox. X págs. A5",
  "ambientacion": "lugar y época",
  "fecha": "{today}",
  "evaluado_por": "{asesora} · Editorial Numancia",
  "sinopsis_i": "párrafo acto I, 2-3 frases literarias",
  "sinopsis_ii": "párrafo acto II, 2-3 frases",
  "sinopsis_iii": "párrafo acto III, 2-3 frases",
  "eval": [
    {{"criterio":"Voz narrativa","estrellas":"★★★★☆","obs":"observación concisa"}},
    {{"criterio":"Estructura","estrellas":"★★★☆☆","obs":"observación concisa"}},
    {{"criterio":"Personajes","estrellas":"★★★★☆","obs":"observación concisa"}},
    {{"criterio":"Género","estrellas":"★★★★☆","obs":"observación concisa"}},
    {{"criterio":"Corrección lingüística","estrellas":"★★★☆☆","obs":"observación concisa"}},
    {{"criterio":"Público y mercado","estrellas":"★★★★☆","obs":"observación concisa"}},
    {{"criterio":"Potencial comercial","estrellas":"★★★☆☆","obs":"observación concisa"}}
  ],
  "veredicto": "PUBLICABLE" o "CON MEJORAS" o "REQUIERE REVISIÓN",
  "veredicto_texto": "2 frases directas justificando el veredicto",
  "lector_primario": "descripción",
  "lector_secundario": "descripción",
  "comparable": "títulos comparables",
  "precio": "rango €",
  "notas": ["nota 1", "nota 2"]
}}"""
        }]
    )
    raw = msg.content[0].text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    return json.loads(raw)


# ─── ENDPOINT 1: PROCESAR (informe + preview) ─────────────────────────────────
@app.post("/procesar")
async def procesar(
    archivo: UploadFile = File(...),
    asesora: str = Form(...)
):
    if not archivo.filename.endswith(".docx"):
        raise HTTPException(400, "Solo se aceptan archivos .docx")
    if not CLAUDE_KEY:
        raise HTTPException(500, "ANTHROPIC_API_KEY no configurada")

    contenido = await archivo.read()

    # Extraer texto
    texto = docx2txt.process(io.BytesIO(contenido))
    palabras = len(texto.split())

    # Análisis Claude
    try:
        analisis = analizar_manuscrito(texto, asesora, palabras)
    except Exception as e:
        raise HTTPException(500, f"Error en análisis Claude: {e}")

    # Generar informe A4
    informe_bytes = generar_informe(analisis)

    # Generar preview A5 (10 páginas)
    preview_bytes = generar_preview(
        texto=texto,
        titulo=analisis.get("titulo", "Sin título"),
        autor=analisis.get("autor", "Anónimo")
    )

    return JSONResponse({
        "analisis": analisis,
        "informe_pdf": base64.b64encode(informe_bytes).decode(),
        "preview_pdf": base64.b64encode(preview_bytes).decode(),
    })


# ─── ENDPOINT 2: MAQUETA COMPLETA ─────────────────────────────────────────────
@app.post("/maqueta-completa")
async def maqueta_completa(
    archivo: UploadFile = File(...),
    titulo: str = Form(...),
    autor: str = Form(...),
    anyo: str = Form("2025"),
    dedicatoria: str = Form(""),
    epigrafe: str = Form(""),
    epigrafe_autor: str = Form(""),
):
    if not archivo.filename.endswith(".docx"):
        raise HTTPException(400, "Solo se aceptan archivos .docx")

    contenido = await archivo.read()
    texto = docx2txt.process(io.BytesIO(contenido))

    pdf_bytes = generar_maqueta_completa(
        texto=texto,
        titulo=titulo,
        autor=autor,
        anyo=anyo,
        dedicatoria=dedicatoria,
        epigrafe=epigrafe,
        epigrafe_autor=epigrafe_autor,
    )

    return JSONResponse({
        "maqueta_pdf": base64.b64encode(pdf_bytes).decode(),
        "nombre_archivo": f"INTERIOR_{autor.split()[0]}_{titulo[:20].replace(' ','_')}.pdf"
    })


@app.get("/")
def root():
    return {"status": "ok", "servicio": "Editorial Numancia Pipeline"}
