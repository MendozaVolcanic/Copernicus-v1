# -*- coding: utf-8 -*-
"""Falla si Copernicus-v1 y Landsat-v1 se separaron en lo que debe ser identico.

POR QUE EXISTE
==============
Los dos repos comparten datos pero no comparten instrumento. change_analysis.py
lee Landsat, auditoria_imagenes.py sabe leer Landsat, gif_optimizer.py es casi el
mismo archivo en los dos lados. **El flujo de datos es bidireccional; el de
correcciones es unidireccional y manual**: alguien tiene que acordarse de copiar.

La auditoria del 2026-08-30 encontro cuatro instancias del mismo hecho, todas
descubiertas por accidente meses despues: la curva RGB con gamma sRGB, el
MAXCOVERAGE del composite SWIR, las coordenadas de Nevados de Chillan en el KML,
y seis centroides refinados solo de un lado. Y antes de eso, el caso que origino
todo: Landsat publico Antuco bajo el nombre de "Nevados de Chillan" durante
cuatro meses, con las dos entradas a 1.31 km entre si -- los dos paneles mostraban
el mismo cerro con nombres distintos y se veian plausibles.

Nada falla cuando dos copias divergen. Los dos archivos siguen siendo validos, los
dos dashboards siguen renderizando, todos los runs siguen en verde. La divergencia
solo se ve comparando los dos a la vez, y nadie lo hace por rutina. Esto lo hace
por rutina.

QUE VERIFICA
============
1. Que el catalogo de volcanes sea el mismo conjunto (excluyendo las vistas zoom,
   que existen solo en Copernicus por diseno).
2. Que las coordenadas sean IDENTICAS, no "parecidas". Un umbral de tolerancia
   invita a discutir cuanto es mucho; la igualdad exacta se verifica sin discutir
   y cualquier deriva falla el mismo dia. Los buffer_km SI pueden diferir: el
   centroide es un hecho del volcan, el buffer es una decision de encuadre que
   cambia legitimamente entre 20 m/px y 30 m/px.
3. Que dentro de CADA config no haya dos volcanes DISTINTOS a menos de 5 km. Es el
   detector del caso Antuco/Chillan, generalizado: dos nombres distintos apuntando
   casi al mismo punto es casi siempre un centroide copiado de la fila de al lado.

USO
===
    python scripts/verificar_divergencia_repos.py --landsat ../Landsat-v1
    python scripts/verificar_divergencia_repos.py --landsat _landsat_data  # en CI

Sale 0 si todo coincide, 1 si hay divergencia, 2 si no pudo comparar (que NO se
reporta como exito: una verificacion que no corrio no es una verificacion que paso).
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UMBRAL_VECINOS_KM = 5.0


def cargar_modulo(ruta, nombre):
    """Importa un config por ruta, sin depender del sys.path ni del cwd."""
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001
        print("[ERROR] no se pudo importar %s: %s" % (ruta, e))
        return None
    return mod


def haversine_km(a, b):
    R = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = p2 - p1
    dl = math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def vecinos_sospechosos(volcanes, etiqueta):
    """Pares de volcanes DISTINTOS a menos de UMBRAL_VECINOS_KM dentro del mismo
    catalogo. Asi se veia el bug de Antuco: 1.31 km entre dos nombres distintos."""
    problemas = []
    nombres = sorted(volcanes)
    for i in range(len(nombres)):
        for j in range(i + 1, len(nombres)):
            a, b = nombres[i], nombres[j]
            d = haversine_km(volcanes[a], volcanes[b])
            if d < UMBRAL_VECINOS_KM:
                problemas.append("%s: '%s' y '%s' estan a %.2f km entre si"
                                 % (etiqueta, a, b, d))
    return problemas


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--landsat", required=True,
                    help="ruta a la raiz del repo Landsat-v1 (o al checkout en CI)")
    args = ap.parse_args()

    ruta_cop = os.path.join(RAIZ, "config_sentinel2.py")
    ruta_land = os.path.join(args.landsat, "config_landsat.py")

    if not os.path.isfile(ruta_land):
        # Un "no pude comparar" que sale 0 es un negativo medido con el
        # instrumento caido: se leeria como "no divergen". Sale 2.
        print("[ERROR] no encuentro %s." % ruta_land)
        print("        En CI, el sparse-checkout de Landsat-v1 tiene que incluir")
        print("        config_landsat.py ademas de docs/landsat.")
        return 2

    mod_cop = cargar_modulo(ruta_cop, "cfg_cop")
    mod_land = cargar_modulo(ruta_land, "cfg_land")
    if mod_cop is None or mod_land is None:
        return 2

    # Las vistas zoom existen solo en Copernicus: son recortes mas cerrados de un
    # volcan que ya esta en la lista, no entidades propias.
    cop = {n: c for n, c in mod_cop.VOLCANES.items() if not c.get("vista_zoom_de")}
    land = dict(mod_land.VOLCANES)

    print("Copernicus-v1: %d volcanes (mas %d vistas zoom, excluidas)"
          % (len(cop), len(mod_cop.VOLCANES) - len(cop)))
    print("Landsat-v1:    %d volcanes" % len(land))

    fallos = []

    solo_cop = sorted(set(cop) - set(land))
    solo_land = sorted(set(land) - set(cop))
    if solo_cop:
        fallos.append("solo en Copernicus-v1: %s" % ", ".join(solo_cop))
    if solo_land:
        fallos.append("solo en Landsat-v1: %s" % ", ".join(solo_land))

    comunes = sorted(set(cop) & set(land))
    difs = []
    for n in comunes:
        a = (cop[n]["lat"], cop[n]["lon"])
        b = (land[n]["lat"], land[n]["lon"])
        if a != b:
            difs.append((haversine_km(a, b), n, a, b))
    difs.sort(reverse=True)
    for d, n, a, b in difs:
        fallos.append("'%s' difiere %.3f km: Copernicus %s vs Landsat %s"
                      % (n, d, a, b))

    fallos.extend(vecinos_sospechosos({n: (c["lat"], c["lon"]) for n, c in cop.items()},
                                      "Copernicus-v1"))
    fallos.extend(vecinos_sospechosos({n: (c["lat"], c["lon"]) for n, c in land.items()},
                                      "Landsat-v1"))

    print("Volcanes en ambos: %d | coordenadas identicas: %d"
          % (len(comunes), len(comunes) - len(difs)))

    if fallos:
        print("\n[FALLA] los dos repos divergieron:")
        for f in fallos:
            print("  - " + f)
        print("\nEl dueno de las coordenadas es Copernicus-v1/config_sentinel2.py.")
        print("Si el cambio es legitimo, propagalo al otro repo en el mismo dia.")
        return 1

    print("\n[ok] catalogos alineados y sin vecinos sospechosos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
