"""
Watcher OData — detección GRATIS de imágenes Sentinel-2 nuevas sobre Chile.

CONTEXTO (por qué existe):
CDSE tiene DOS catálogos:
  1. Sentinel Hub Catalog API (sh.dataspace...)  -> CONSUME Process Units (PU)
  2. OData Catalogue        (catalogue.dataspace...) -> GRATIS, sin token, sin PU

El cron principal usaba (1) para preguntar "¿hay algo nuevo?" 11×/día × 46
volcanes = 506 búsquedas/día contra el endpoint que gasta cuota. Este watcher
usa (2): una sola query gratis sobre el bbox de Chile entero. Si detecta un
producto L2A publicado que aún no tenemos, marca has_new=true y el pipeline
de descarga (que sí cuesta PU) corre SOLO en ese caso.

Resultado:
  - Detección ≤15 min (el watcher corre cada 15 min en las ventanas)
  - Costo de detección: $0 PU
  - El Process API (PU) solo se invoca cuando hay imagen nueva real

Salida:
  - Escribe `has_new=true|false` en $GITHUB_OUTPUT (lo lee el job gate)
  - Actualiza docs/.s2_last_pub.json con la última PublicationDate vista
    (solo cuando has_new=true, para avanzar el marcador)

Uso:
  python scripts/watcher_odata.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# Polígono que envuelve Chile continental (lon/lat). Generoso pero acotado.
CHILE_WKT = "POLYGON((-76 -56,-66 -56,-66 -17,-76 -17,-76 -56))"
ODATA_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
MARKER_PATH = "docs/.s2_last_pub.json"

# Si no hay marcador previo, mirar las últimas N horas
DEFAULT_LOOKBACK_H = 6


def leer_marcador() -> str:
    """Devuelve la última PublicationDate procesada (ISO Z), o un default."""
    if os.path.isfile(MARKER_PATH):
        try:
            d = json.load(open(MARKER_PATH, encoding="utf-8"))
            v = d.get("last_publication")
            if v:
                return v
        except Exception:
            pass
    fallback = datetime.now(timezone.utc) - timedelta(hours=DEFAULT_LOOKBACK_H)
    return fallback.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def escribir_marcador(iso: str) -> None:
    os.makedirs(os.path.dirname(MARKER_PATH), exist_ok=True)
    json.dump(
        {"last_publication": iso, "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
        open(MARKER_PATH, "w", encoding="utf-8"),
        indent=2,
    )


def query_odata(since_iso: str) -> list[dict]:
    """Productos S2 L2A sobre Chile publicados después de `since_iso`."""
    filtro = (
        "Collection/Name eq 'SENTINEL-2' "
        "and contains(Name,'MSIL2A') "
        f"and PublicationDate gt {since_iso} "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;{CHILE_WKT}')"
    )
    params = {
        "$filter": filtro,
        "$orderby": "PublicationDate desc",
        "$top": "100",
        "$select": "Name,ContentDate,PublicationDate",
    }
    url = ODATA_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read()).get("value", [])


def set_output(key: str, value: str) -> None:
    """Escribe en $GITHUB_OUTPUT si existe; siempre imprime para logs."""
    print(f"[OUTPUT] {key}={value}")
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def main() -> None:
    marcador = leer_marcador()
    print(f"[watcher] Marcador previo (última publicación vista): {marcador}")

    try:
        productos = query_odata(marcador)
    except Exception as e:
        # Falla de red: NO disparar pipeline (evitamos gastar PU por un glitch),
        # pero tampoco rompemos el workflow. El próximo watcher reintenta.
        print(f"[watcher] ERROR consultando OData: {type(e).__name__}: {e}")
        set_output("has_new", "false")
        return

    if not productos:
        print("[watcher] Sin productos nuevos sobre Chile. has_new=false (0 PU gastados)")
        set_output("has_new", "false")
        return

    # Hay novedad: reportar y avanzar marcador a la publicación más reciente
    nueva_pub = productos[0]["PublicationDate"]
    print(f"[watcher] {len(productos)} productos nuevos publicados desde el marcador.")
    print("[watcher] Muestras (sensado -> publicado):")
    for p in productos[:5]:
        sensado = (p.get("ContentDate", {}) or {}).get("Start", "?")[:19]
        pub = p.get("PublicationDate", "?")[:19]
        print(f"           {sensado}  ->  {pub}  {p.get('Name','')[:35]}")

    # Escribimos el marcador local (para runs standalone), pero en el pipeline
    # el marcador NO se commitea acá: se avanza en el job 'consolidar' TRAS una
    # descarga exitosa. Motivo: si se commiteaba en 'detectar' (antes de bajar) y
    # la descarga fallaba, el marcador ya habia avanzado -> esas escenas nunca se
    # re-detectaban (perdida de datos). Por eso emitimos 'nueva_pub' como output
    # para que 'consolidar' lo persista solo si el pipeline llego hasta el final.
    escribir_marcador(nueva_pub)
    print(f"[watcher] Marcador local escrito: {nueva_pub} (se commitea en 'consolidar')")
    set_output("has_new", "true")
    set_output("nueva_pub", nueva_pub)


if __name__ == "__main__":
    main()
