# Editorial Numancia — Pipeline microservicio

Microservicio Python que gestiona el flujo editorial completo:
1. **Informe de viabilidad A4 PDF** (formato fijo Numancia)
2. **Preview 10 páginas A5 PDF** con marca de agua
3. **Maqueta completa A5 PDF** lista para Printcolor

---

## Endpoints

### `POST /procesar`
Recibe el `.docx` + asesora → devuelve informe + preview + análisis JSON.

**Form data:**
- `archivo` — archivo .docx
- `asesora` — nombre de la asesora

**Response JSON:**
```json
{
  "analisis": { ... },
  "informe_pdf": "<base64>",
  "preview_pdf": "<base64>"
}
```

---

### `POST /maqueta-completa`
Recibe el `.docx` + metadatos → devuelve el libro completo listo para imprenta.

**Form data:**
- `archivo` — archivo .docx
- `titulo` — título del libro
- `autor` — nombre del autor
- `anyo` — año de edición (default: 2025)
- `dedicatoria` — texto de dedicatoria (opcional)
- `epigrafe` — texto del epígrafe (opcional)
- `epigrafe_autor` — autor del epígrafe (opcional)

**Response JSON:**
```json
{
  "maqueta_pdf": "<base64>",
  "nombre_archivo": "INTERIOR_Apellido_Titulo.pdf"
}
```

---

## Despliegue en Railway (5 minutos)

1. Sube esta carpeta a un repo GitHub
2. Entra en [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. En Variables de entorno añade:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
4. Railway detecta el `Procfile` y arranca automáticamente
5. Copia la URL pública que te da Railway (ej: `https://numancia-pipeline.up.railway.app`)

---

## Variables de entorno requeridas

| Variable | Descripción |
|---|---|
| `ANTHROPIC_API_KEY` | Clave API de Anthropic (Claude) |

---

## Uso desde la app web

```javascript
// 1. PROCESAR (informe + preview)
const form = new FormData();
form.append('archivo', docxFile);
form.append('asesora', 'Laura Vega Ugarte');

const res = await fetch('https://TU-URL.up.railway.app/procesar', {
  method: 'POST', body: form
});
const data = await res.json();

// Descargar informe
const informe = atob(data.informe_pdf);
// Descargar preview
const preview = atob(data.preview_pdf);

// 2. MAQUETA COMPLETA (tras aprobación)
const form2 = new FormData();
form2.append('archivo', docxFile);
form2.append('titulo', 'Sara');
form2.append('autor', 'Nombre Autor');
form2.append('anyo', '2025');
form2.append('dedicatoria', 'A mi familia.');
form2.append('epigrafe', 'La vida es...');
form2.append('epigrafe_autor', 'Autor del epígrafe');

const res2 = await fetch('https://TU-URL.up.railway.app/maqueta-completa', {
  method: 'POST', body: form2
});
const data2 = await res2.json();
// data2.maqueta_pdf = base64 del PDF completo
```
