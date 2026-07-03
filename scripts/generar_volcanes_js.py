"""
Genera docs/volcanes.js desde config_sentinel2.py (single source of truth).

USO:
    python scripts/generar_volcanes_js.py

POR QUE:
    La lista de 46 entidades (43 volcanes + 3 vistas zoom) estaba duplicada en
    ~6 archivos HTML (index, sala_monitoreo, revision_volcanes, ppt_builder,
    experimental/cog_viewer, experimental/alta_resolucion). Eso causo bugs
    historicos (typo "Michinmahuidia", coords de Chillan apuntando a Antuco).

    Este script regenera docs/volcanes.js cada vez que se edita
    config_sentinel2.py. El HTML consume window.VOLCANES_CONFIG en vez de
    redeclarar la lista localmente.

INTEGRACION:
    Se corre automaticamente como primer step del cron .github/workflows/copernicus.yml.
    Tambien manualmente cuando se cambian coordenadas.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Permitir import desde la raiz del proyecto
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config_sentinel2 import VOLCANES  # noqa: E402


ZONA_ORDEN = ["Norte", "Centro", "Sur", "Austral"]

# 14 volcanes mas riesgosos segun ranking SERNAGEOMIN (replicado del index.html
# legacy). Si SERNAGEOMIN republica el ranking, actualizar aca.
VOLCANES_RIESGOSOS = [
    {"nombre": "Villarrica", "region": "La Araucania - Los Rios"},
    {"nombre": "Calbuco", "region": "Los Lagos"},
    {"nombre": "Llaima", "region": "La Araucania"},
    {"nombre": "Puyehue - Cordon Caulle", "region": "Los Rios - Los Lagos"},
    {"nombre": "Descabezado Grande", "region": "Maule"},
    {"nombre": "Carran - Los Venados", "region": "Los Rios"},
    {"nombre": "Chaiten", "region": "Los Lagos"},
    {"nombre": "Osorno", "region": "Los Lagos"},
    {"nombre": "Mocho-Choshuenco", "region": "Los Rios"},
    {"nombre": "Nevados de Chillan", "region": "Nuble"},
    {"nombre": "Lonquimay", "region": "La Araucania"},
    {"nombre": "Hudson", "region": "Aysen"},
    {"nombre": "Lascar", "region": "Antofagasta"},
    {"nombre": "Copahue", "region": "Bio Bio"},
]


def construir_estructuras() -> dict:
    """Arma los diccionarios que se serializan al JS."""
    config: dict[str, dict] = {}
    por_zona: dict[str, list[str]] = {z: [] for z in ZONA_ORDEN}
    vistas_zoom: list[str] = []

    for nombre, datos in VOLCANES.items():
        entry = {
            "lat": datos["lat"],
            "lon": datos["lon"],
            "buffer_km": datos["buffer_km"],
            "zona": datos.get("zona", ""),
            "id": datos.get("id", ""),
            "activo": datos.get("activo", True),
        }
        if "vista_zoom_de" in datos:
            entry["vista_zoom_de"] = datos["vista_zoom_de"]
            if "motivo" in datos:
                entry["motivo"] = datos["motivo"]
            vistas_zoom.append(nombre)
        else:
            por_zona.setdefault(datos.get("zona", "Sin zona"), []).append(nombre)
        config[nombre] = entry

    # Ordenar cada zona por latitud Norte->Sur (latitudes negativas: -18 > -23 > -45,
    # asi que descendente recorre Norte->Sur)
    for zona in por_zona:
        por_zona[zona].sort(key=lambda n: -config[n]["lat"])

    return {
        "config": config,
        "por_zona": por_zona,
        "vistas_zoom": vistas_zoom,
    }


def serializar_js(estructuras: dict) -> str:
    """Genera el texto del archivo docs/volcanes.js."""
    config = estructuras["config"]
    por_zona = estructuras["por_zona"]
    vistas_zoom = estructuras["vistas_zoom"]

    # Lista plana en orden Norte->Sur, vistas zoom al final (compatible con
    # sala_monitoreo.html TODOS_VOLCANES y ppt_builder VOLCANES)
    lista_plana: list[str] = []
    for zona in ZONA_ORDEN:
        lista_plana.extend(por_zona.get(zona, []))
    lista_plana.extend(vistas_zoom)

    dumps = lambda obj: json.dumps(obj, indent=2, ensure_ascii=False)  # noqa: E731
    timestamp = datetime.now(timezone.utc).isoformat()

    # Helpers que los HTMLs consumen sin reimplementar logica
    helpers = """
// ------------------------------------------------------------------
// Helpers (idempotentes, no mutan estado)
// ------------------------------------------------------------------
window.getVolcanesPorZona = function(zona) {
  return (window.VOLCANES_POR_ZONA[zona] || []).slice();
};
window.getVolcanInfo = function(nombre) {
  return window.VOLCANES_CONFIG[nombre] || null;
};
window.esVistaZoom = function(nombre) {
  return window.VISTAS_ZOOM.indexOf(nombre) !== -1;
};
""".lstrip()

    return f"""// =====================================================================
// docs/volcanes.js -- AUTO-GENERADO desde config_sentinel2.py
// NO EDITAR A MANO. Para modificar coordenadas, editar config_sentinel2.py
// y re-correr:
//     python scripts/generar_volcanes_js.py
//
// Single source of truth: config_sentinel2.VOLCANES
// Generado: {timestamp}
// Total entidades: {len(config)} ({len(config) - len(vistas_zoom)} volcanes + {len(vistas_zoom)} vistas zoom)
// =====================================================================

// Mapa nombre -> {{ lat, lon, buffer_km, zona, id, activo, [vista_zoom_de, motivo] }}
window.VOLCANES_CONFIG = {dumps(config)};

// Lista plana en orden Norte->Sur + vistas zoom al final
window.VOLCANES_LIST = {dumps(lista_plana)};

// Solo volcanes principales (sin vistas zoom), agrupados por zona y ordenados N->S
window.VOLCANES_POR_ZONA = {dumps(por_zona)};

// Nombres de las vistas zoom (sub-vistas de Melimoyu/Mentolat/Hudson)
window.VISTAS_ZOOM = {dumps(vistas_zoom)};

// Alias compatible: lista completa (volcanes + vistas zoom)
window.TODOS_VOLCANES = window.VOLCANES_LIST.slice();

// Ranking 14 mas riesgosos (SERNAGEOMIN). Estable, no derivado de config_sentinel2.
window.VOLCANES_RIESGOSOS = {dumps(VOLCANES_RIESGOSOS)};

{helpers}
"""


def main() -> int:
    estructuras = construir_estructuras()
    js = serializar_js(estructuras)

    out_path = ROOT / "docs" / "volcanes.js"
    out_path.write_text(js, encoding="utf-8")

    n_total = len(estructuras["config"])
    n_zoom = len(estructuras["vistas_zoom"])
    n_principales = n_total - n_zoom
    print(f"OK Generado {out_path.relative_to(ROOT)}")
    print(f"   {n_principales} volcanes principales + {n_zoom} vistas zoom = {n_total} entidades")
    for zona, lista in estructuras["por_zona"].items():
        print(f"   {zona}: {len(lista)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
