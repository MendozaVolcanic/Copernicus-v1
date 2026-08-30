# -*- coding: utf-8 -*-
"""Compara la auditoria de imagenes contra una linea base y falla solo con lo NUEVO.

POR QUE ASI Y NO "FALLAR SI HAY HALLAZGOS"
==========================================
Al 2026-08-30 la auditoria encuentra 325 hallazgos de severidad alta entre los
dos repos. Un job que falle con eso arranca en rojo el primer dia y a la semana
nadie lo mira: el atajo se vuelve la norma y el control deja de existir aunque
siga corriendo. Lo que importa vigilar no es el stock heredado -- que ya esta
medido y documentado -- sino que no APAREZCAN casos nuevos.

La linea base es la lista de casos altos conocidos, por (fuente, volcan, fecha,
tipo). Un caso que desaparece porque la retencion purgo el PNG simplemente ya no
esta; uno nuevo hace fallar el job con nombre y apellido.

USO
===
    python scripts/comparar_auditoria.py --actual out.json --base tasks/auditoria_baseline.json
    python scripts/comparar_auditoria.py --actual out.json --escribir-base tasks/auditoria_baseline.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def claves_altas(datos):
    out = set()
    for h in datos.get("hallazgos", []):
        if h.get("severidad") != "alta":
            continue
        out.add("|".join([h.get("fuente", "?"), h.get("volcan", "?"),
                          h.get("fecha", "?"), h.get("tipo", "?")]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--actual", required=True, help="JSON producido por auditoria_imagenes.py")
    ap.add_argument("--base", help="linea base contra la que comparar")
    ap.add_argument("--escribir-base", help="regenera la linea base y sale 0")
    ap.add_argument("--max-nuevos", type=int, default=0,
                    help="cuantos casos nuevos se toleran antes de fallar")
    args = ap.parse_args()

    with open(args.actual, encoding="utf-8") as fh:
        actual = json.load(fh)
    hoy = claves_altas(actual)

    if args.escribir_base:
        os.makedirs(os.path.dirname(args.escribir_base) or ".", exist_ok=True)
        with open(args.escribir_base, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"generado_desde": os.path.basename(args.actual),
                       "n": len(hoy),
                       "casos": sorted(hoy)}, fh, indent=1, ensure_ascii=False)
        print("[ok] linea base con %d casos altos -> %s" % (len(hoy), args.escribir_base))
        return 0

    if not args.base:
        print("[ERROR] falta --base o --escribir-base")
        return 2
    try:
        with open(args.base, encoding="utf-8") as fh:
            base = set(json.load(fh).get("casos", []))
    except FileNotFoundError:
        print("[ERROR] no existe la linea base %s. Generala con --escribir-base"
              % args.base)
        return 2

    nuevos = sorted(hoy - base)
    idos = len(base - hoy)

    print("Casos de severidad alta: %d hoy, %d en la linea base" % (len(hoy), len(base)))
    print("  desaparecidos (purgados por retencion o corregidos): %d" % idos)
    print("  NUEVOS: %d" % len(nuevos))
    for k in nuevos[:40]:
        f, v, fe, t = k.split("|")
        print("    %-18s %-26s %s  %s" % (f, v, fe, t))
    if len(nuevos) > 40:
        print("    ... y %d mas" % (len(nuevos) - 40))

    if len(nuevos) > args.max_nuevos:
        print("\n[FALLA] aparecieron %d casos altos nuevos (tolerancia %d)."
              % (len(nuevos), args.max_nuevos))
        print("Si son legitimos y ya los revisaste, actualiza la linea base con:")
        print("  python scripts/comparar_auditoria.py --actual <json> "
              "--escribir-base tasks/auditoria_baseline.json")
        return 1

    print("\n[ok] sin casos altos nuevos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
