"""
Borra del working tree:
  - PNGs y GIFs cuyo nombre empiece con YYYY-MM-DD < cutoff
  - TODOS los .pptx (sin distinción)
  - .npz (raw SWIR) viejos también

Uso (cutoff por defecto = hoy - 60 dias):
  python scripts/limpiar_imagenes_antiguas.py

Variable de entorno opcional:
  CUTOFF_DATE=2026-03-17 python scripts/limpiar_imagenes_antiguas.py

Diseñado para correr DENTRO del workflow purgar_historico_completo.yml
antes del orphan commit. No depende de git; solo toca filesystem.
"""
from __future__ import annotations
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Patron: archivos que empiezan con YYYY-MM-DD
PAT_FECHA = re.compile(r"^(\d{4}-\d{2}-\d{2})[_.]")


def main() -> None:
    cutoff_env = os.environ.get("CUTOFF_DATE")
    if cutoff_env:
        cutoff = cutoff_env
    else:
        cutoff = (date.today() - timedelta(days=60)).isoformat()
    print(f"[INFO] Cutoff: archivos con fecha < {cutoff} seran borrados")

    borrados = {"png_viejo": 0, "gif_viejo": 0, "npz_viejo": 0, "pptx": 0, "mb": 0.0}

    if not DOCS.exists():
        print(f"[WARN] {DOCS} no existe, nada que hacer")
        return

    for path in DOCS.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        suf = path.suffix.lower()

        # NUNCA borrar plantillas: son codigo del proyecto (el ppt_builder las
        # necesita), no reportes regenerables. Bug 2026-07: la purga borro
        # Cambios_morfologicos.pptx y rompio el generador de PPT.
        if "plantillas" in path.parts:
            continue

        # 1) PPTX: borrar TODOS (decision usuario)
        if suf == ".pptx":
            size_mb = path.stat().st_size / 1024 / 1024
            path.unlink()
            borrados["pptx"] += 1
            borrados["mb"] += size_mb
            continue

        # 2) PNG / GIF / NPZ con fecha en nombre y fecha < cutoff
        if suf in {".png", ".gif", ".npz"}:
            m = PAT_FECHA.match(path.name)
            if m and m.group(1) < cutoff:
                size_mb = path.stat().st_size / 1024 / 1024
                path.unlink()
                key = {"png": "png_viejo", "gif": "gif_viejo", "npz": "npz_viejo"}[suf[1:]]
                borrados[key] += 1
                borrados["mb"] += size_mb

    print(f"[OK] PNG  viejos borrados: {borrados['png_viejo']}")
    print(f"[OK] GIF  viejos borrados: {borrados['gif_viejo']}")
    print(f"[OK] NPZ  viejos borrados: {borrados['npz_viejo']}")
    print(f"[OK] PPTX (todos) borrados: {borrados['pptx']}")
    print(f"[OK] Espacio liberado:     {borrados['mb']:.1f} MB")


if __name__ == "__main__":
    main()
