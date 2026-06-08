"""
Job store asíncrono para el Pack Promoción y Marketing.
Replica el patrón de corrector_aplicado.py (dict en memoria + lock + thread).
Funciona porque gunicorn arranca con --workers 1. Si algún día escalas a
varios workers, esto habría que moverlo a Redis/DB.
"""
import os
import time
import uuid
import threading
import traceback
from typing import Optional

from pack_promocion_prompt import generar_pack_promocion

_PACK_JOBS = {}
_PACK_JOBS_LOCK = threading.Lock()


def _set_pack_job(job_id: str, datos: dict):
    with _PACK_JOBS_LOCK:
        if job_id not in _PACK_JOBS:
            _PACK_JOBS[job_id] = {}
        _PACK_JOBS[job_id].update(datos)


def _get_pack_job(job_id: str) -> Optional[dict]:
    with _PACK_JOBS_LOCK:
        if job_id not in _PACK_JOBS:
            return None
        return dict(_PACK_JOBS[job_id])


def crear_job_pack(texto_libro: str, titulo: str, autor: str,
                   genero: str, url_libreria: str,
                   asesora: str = "laura", presupuesto_id: str = "",
                   chars_libro: int = 0) -> str:
    """Crea el job y lo lanza en background. Devuelve job_id."""
    job_id = uuid.uuid4().hex[:12]
    _set_pack_job(job_id, {
        "estado": "pendiente",
        "progreso": 0,
        "mensaje": "En cola",
        "asesora": asesora,
        "presupuesto_id": presupuesto_id,
        "chars_libro": chars_libro,
        "ts_inicio": time.time(),
        "resultado": None,
        "error": None,
    })

    hilo = threading.Thread(
        target=_ejecutar_job_pack,
        args=(job_id, texto_libro, titulo, autor, genero, url_libreria,
              asesora, presupuesto_id, chars_libro),
        daemon=True,
    )
    hilo.start()
    return job_id


def _ejecutar_job_pack(job_id, texto_libro, titulo, autor, genero,
                       url_libreria, asesora, presupuesto_id, chars_libro):
    try:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY no configurada")

        _set_pack_job(job_id, {
            "estado": "procesando",
            "progreso": 10,
            "mensaje": "Generando pack con Claude API",
        })

        pack = generar_pack_promocion(
            texto_libro=texto_libro,
            titulo=titulo,
            autor=autor,
            genero=genero,
            url_libreria=url_libreria,
        )

        if "_meta" not in pack or not isinstance(pack.get("_meta"), dict):
            pack["_meta"] = {}
        pack["_meta"].update({
            "asesora": asesora,
            "presupuesto_id": presupuesto_id or None,
            "chars_libro": chars_libro,
            "chars_truncado": chars_libro > 80_000,
        })

        _set_pack_job(job_id, {
            "estado": "completado",
            "progreso": 100,
            "mensaje": "Pack completado",
            "resultado": pack,
            "ts_fin": time.time(),
        })
        print(f"[pack-async] job={job_id} COMPLETADO "
              f"tokens_in={pack['_meta'].get('tokens_input')} "
              f"tokens_out={pack['_meta'].get('tokens_output')} "
              f"coste_eur={pack['_meta'].get('coste_eur')}", flush=True)

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[pack-async] job={job_id} ERROR: {e}\n{tb}", flush=True)
        _set_pack_job(job_id, {
            "estado": "error",
            "mensaje": f"Error: {type(e).__name__}",
            "error": str(e),
            "ts_fin": time.time(),
        })


def get_pack_status(job_id: str) -> Optional[dict]:
    """Estado ligero para polling (incluye resultado solo si completado)."""
    j = _get_pack_job(job_id)
    if j is None:
        return None
    out = {
        "estado": j.get("estado"),
        "progreso": j.get("progreso", 0),
        "mensaje": j.get("mensaje", ""),
        "tiempo_seg": round(
            (j.get("ts_fin") or time.time()) - j.get("ts_inicio", time.time()), 1
        ),
    }
    if j.get("estado") == "completado":
        pack = j.get("resultado") or {}
        meta = pack.get("_meta", {}) if isinstance(pack, dict) else {}
        out["resultado"] = pack
        out["coste_eur"] = meta.get("coste_eur")
        out["tokens_input"] = meta.get("tokens_input")
        out["tokens_output"] = meta.get("tokens_output")
    elif j.get("estado") == "error":
        out["error"] = j.get("error")
    return out


def limpiar_pack_jobs_antiguos(horas: int = 24) -> int:
    """Borra jobs terminados con más de `horas` de antigüedad."""
    limite = time.time() - horas * 3600
    borrados = 0
    with _PACK_JOBS_LOCK:
        for jid in list(_PACK_JOBS.keys()):
            j = _PACK_JOBS[jid]
            if j.get("estado") in ("completado", "error") and \
               (j.get("ts_fin") or 0) < limite:
                del _PACK_JOBS[jid]
                borrados += 1
    return borrados
