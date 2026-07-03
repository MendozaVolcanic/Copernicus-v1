"""
SPECTRAL_DOWNLOADER.PY — Descarga índices espectrales para Change Detection
Descarga NDVI, NBR y SWIR_Anomaly para las mismas fechas que ya tienen RGB/Thermal.

Uso:
    python spectral_downloader.py --test              # 3 volcanes, última fecha
    python spectral_downloader.py --volcan Villarrica  # 1 volcán, todas las fechas
    python spectral_downloader.py                      # 43 volcanes, últimas 2 fechas
    python spectral_downloader.py --todas-fechas       # 43 volcanes, todas las fechas
"""

import os
import sys
import glob
import argparse
from datetime import datetime

# Fix encoding Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from config_sentinel2 import (
    VOLCANES, EVALSCRIPTS,
    IMAGE_WIDTH_THERMAL, IMAGE_HEIGHT_THERMAL,
    get_image_path
)
# FIX 2026-05-17: la clase real se llama SentinelHubDownloader (no Downloader).
# El alias mantiene el resto del código sin cambios. Este import roto
# explica por qué los NDVI/NBR/SWIR_Anomaly estaban vacíos en muchos volcanes.
# FIX 2026-06-07: SentinelHubDownloader requiere un objeto auth (SentinelHubAuth).
# El workflow fallaba con "missing 1 required positional argument: 'auth'".
from sentinel2_downloader import (
    SentinelHubDownloader as SentinelDownloader,
    SentinelHubAuth,
)

# Tipos de índices espectrales a descargar
TIPOS_ESPECTRALES = ['NDVI', 'NBR', 'SWIR_Anomaly']

SENTINEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "sentinel2")


def obtener_fechas_existentes(volcan):
    """Obtiene fechas que ya tienen RGB descargado (fuente de verdad)."""
    patron = os.path.join(SENTINEL_DIR, volcan, "*_RGB.png")
    archivos = sorted(glob.glob(patron))
    fechas = []
    for f in archivos:
        nombre = os.path.basename(f)
        fecha = nombre.split('_')[0]
        fechas.append(fecha)
    return fechas


def descargar_indices(volcanes=None, max_fechas=2):
    """Descarga índices espectrales para volcanes y fechas dadas."""

    if volcanes is None:
        volcanes = list(VOLCANES.keys())

    print(f"\n{'='*70}")
    print(f"SPECTRAL DOWNLOADER — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Volcanes: {len(volcanes)} | Max fechas/volcán: {max_fechas}")
    print(f"Tipos: {', '.join(TIPOS_ESPECTRALES)}")
    print(f"{'='*70}\n")

    downloader = SentinelDownloader(SentinelHubAuth())
    total_descargadas = 0
    total_existentes = 0
    total_errores = 0

    for i, volcan in enumerate(volcanes, 1):
        config = VOLCANES.get(volcan)
        if not config:
            print(f"[{i}/{len(volcanes)}] {volcan} — NO encontrado en config")
            continue

        lat = config['lat']
        lon = config['lon']
        buffer_km = config.get('buffer_km', 3)

        fechas = obtener_fechas_existentes(volcan)
        if not fechas:
            print(f"[{i}/{len(volcanes)}] {volcan} — Sin imágenes RGB existentes")
            continue

        # Tomar las últimas N fechas
        fechas_a_procesar = fechas[-max_fechas:]
        print(f"[{i}/{len(volcanes)}] {volcan} — {len(fechas_a_procesar)} fechas")

        for fecha in fechas_a_procesar:
            for tipo in TIPOS_ESPECTRALES:
                output_path = os.path.join(SENTINEL_DIR, volcan, f"{fecha}_{tipo}.png")

                if os.path.exists(output_path):
                    total_existentes += 1
                    continue

                print(f"    {fecha} {tipo}...", end=" ", flush=True)
                exito = downloader.download_image(lat, lon, fecha, tipo, output_path, buffer_km)

                if exito:
                    total_descargadas += 1
                    size_kb = os.path.getsize(output_path) / 1024
                    print(f"OK ({size_kb:.0f} KB)")
                else:
                    total_errores += 1
                    print("ERROR")

        # (Antes habia un reset manual de token cada 5 volcanes envuelto en
        # try/except Exception: pass. Era codigo muerto: SentinelHubAuth.get_token()
        # ya auto-renueva al vencer el token, y ese except tragaba fallas de auth.
        # Se elimino; el fail-fast/failover del downloader sigue intacto.)

    print(f"\n{'='*70}")
    print(f"RESUMEN:")
    print(f"  Descargadas: {total_descargadas}")
    print(f"  Ya existían: {total_existentes}")
    print(f"  Errores: {total_errores}")
    print(f"{'='*70}\n")

    return total_descargadas


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Descarga índices espectrales Sentinel-2')
    parser.add_argument('--test', action='store_true', help='Test con 3 volcanes')
    parser.add_argument('--volcan', type=str, help='Volcán específico')
    parser.add_argument('--todas-fechas', action='store_true', help='Todas las fechas disponibles')
    parser.add_argument('--fechas', type=int, default=2, help='Número de fechas recientes (default: 2)')
    args = parser.parse_args()

    if args.test:
        descargar_indices(["Villarrica", "Lascar", "Copahue"], max_fechas=1)
    elif args.volcan:
        max_f = 999 if args.todas_fechas else args.fechas
        descargar_indices([args.volcan], max_fechas=max_f)
    else:
        max_f = 999 if args.todas_fechas else args.fechas
        descargar_indices(max_fechas=max_f)
