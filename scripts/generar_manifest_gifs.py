"""
Genera docs/timelapses_ppt_manifest.json mapeando:
  { "<Volcan>": { "rgb": "...", "thermal": "...", "desde": "YYYY-MM-DD", "hasta": "YYYY-MM-DD" } }

Reemplaza la lógica frágil del ppt_builder que adivinaba nombres de archivo.
Diseñado para correr al final del cron copernicus.yml.

Uso:
  python scripts/generar_manifest_gifs.py
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SENTINEL2 = DOCS / "sentinel2"
MANIFEST = DOCS / "timelapses_ppt_manifest.json"

# Patron: <Volcan>_<TIPO>_YYYY-MM-DD_YYYY-MM-DD.gif
PATRON = re.compile(r"^(.+)_(RGB|ThermalFalseColor)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.gif$")


def main() -> None:
    manifest: dict[str, dict] = {}
    if not SENTINEL2.exists():
        print(f"[WARN] {SENTINEL2} no existe")
        MANIFEST.write_text("{}", encoding="utf-8")
        return

    for volcan_dir in sorted(SENTINEL2.iterdir()):
        if not volcan_dir.is_dir() or volcan_dir.name.startswith("_LEGACY"):
            continue
        tlp = volcan_dir / "timelapses_ppt"
        if not tlp.is_dir():
            continue

        volcan = volcan_dir.name
        rgb_match = None
        therm_match = None
        for gif in tlp.glob("*.gif"):
            m = PATRON.match(gif.name)
            if not m:
                continue
            _name, tipo, desde, hasta = m.groups()
            entry = (desde, hasta, gif.name)
            if tipo == "RGB" and (rgb_match is None or hasta > rgb_match[1]):
                rgb_match = entry
            elif tipo == "ThermalFalseColor" and (therm_match is None or hasta > therm_match[1]):
                therm_match = entry

        if rgb_match and therm_match:
            manifest[volcan] = {
                "rgb": f"sentinel2/{volcan}/timelapses_ppt/{rgb_match[2]}",
                "thermal": f"sentinel2/{volcan}/timelapses_ppt/{therm_match[2]}",
                "desde": rgb_match[0],
                "hasta": rgb_match[1],
            }

    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Manifest con {len(manifest)} volcanes -> {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
