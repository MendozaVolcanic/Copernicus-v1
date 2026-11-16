# -*- coding: utf-8 -*-
"""Decide si la calidad de las imagenes RECIENTES empeoro respecto de lo habitual.

POR QUE TASAS Y NO UNA LISTA DE CASOS
=====================================
La version anterior guardaba una linea base de casos conocidos por
(fuente, volcan, fecha, tipo) y fallaba con cualquier caso que no estuviera en
ella. No podia funcionar, por dos razones (revisadas el 2026-11-16):

  1. Los casos de severidad alta no son, en su mayoria, errores del codigo sino
     condiciones de la escena que se repiten: nieve que satura B12 y B11
     (QUEMADA), borde de pasada (NODATA), blanco puro en dia despejado
     (RGB_QUEMADA). Habia 262 en las ventanas de retencion: del orden de cinco
     por dia (estimado de esos conteos). Cada fecha nueva trae casos "nuevos" por construccion, asi que el
     job habria quedado rojo todos los dias.
  2. La clave llevaba la fecha y la retencion (45 dias S2, 60 Landsat) purga
     las fechas: a los dos meses la base ya no tenia ningun caso vigente.

Ademas miraba solo la severidad alta, y el defecto que motivo todo esto (B1:
Villarrica 2026-07-03 con el canal SWIR topado en 79/255) se manifiesta como
REQUIERE_VERIFICACION o CALOR_NO_VISIBLE, que son severidad media.

Lo que delata un defecto del pipeline no es que exista un caso, sino que la
FRECUENCIA de un tipo de caso cambie de golpe. Por eso este script compara,
para cada fuente y tipo (todas las severidades), la fraccion de imagenes
afectadas en los ultimos DIAS_RECIENTES dias contra la fraccion en el resto de
la ventana publicada. La referencia se recalcula sola cada dia y no vence.

CUANDO FALLA
============
  - Un tipo se dispara: la probabilidad binomial de ver tantos casos recientes
    con la tasa habitual es menor que ALFA, son al menos MIN_CASOS y la tasa
    reciente es al menos el doble de la habitual. Un tipo que nunca habia
    ocurrido entra por la misma via (su tasa habitual es casi cero).
  - Una fuente tiene menos de MIN_RECIENTES imagenes recientes: sin imagenes no
    hay nada que comparar, y un "no pude medir" que sale verde se lee como
    "todo bien".

LIMITES (para no leer de mas un verde)
======================================
  - Un defecto que dure mas que la ventana pasa a ser la referencia: este
    control avisa en la primera semana, no despues.
  - Una semana de nevadas puede disparar QUEMADA sin que el codigo cambie. El
    aviso lo dice; la decision es de quien lo revisa.

USO
===
    python scripts/comparar_auditoria.py --actual auditoria_actual.json
    python scripts/comparar_auditoria.py --actual out.json --hoy 2026-11-16
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys

DIAS_RECIENTES = 7
ALFA = 1e-4          # ~365 corridas x ~15 pares fuente/tipo al anio: pocas falsas alarmas
MIN_CASOS = 3
RAZON_MIN = 2.0
MIN_RECIENTES = 10


def cola_binomial(k, n, p):
    """P(X >= k) con X ~ Binomial(n, p), en logaritmos para no desbordar."""
    if k <= 0:
        return 1.0
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    total = 0.0
    for i in range(k, n + 1):
        total += math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                          + i * math.log(p) + (n - i) * math.log1p(-p))
    return min(total, 1.0)


def evaluar(datos, hoy, dias=DIAS_RECIENTES):
    corte = (hoy - dt.timedelta(days=dias)).isoformat()
    revisadas = datos.get("revisadas")
    if not revisadas:
        raise SystemExit("[ERROR] el JSON no trae 'revisadas' (imagenes por fecha); "
                         "hay que generarlo con la auditoria actual")

    # imagenes afectadas por (fuente, tipo), separadas en recientes y habituales
    casos = {}
    for h in datos.get("hallazgos", []):
        clave = (h.get("fuente", "?"), h.get("tipo", "?"))
        reciente = h.get("fecha", "") > corte
        c = casos.setdefault(clave, [set(), set()])
        c[0 if reciente else 1].add((h.get("volcan"), h.get("fecha")))

    filas, fallas, avisos = [], [], []
    for fuente, por_fecha in sorted(revisadas.items()):
        n_r = sum(n for f, n in por_fecha.items() if f > corte)
        n_h = sum(n for f, n in por_fecha.items() if f <= corte)
        if n_r < MIN_RECIENTES:
            fallas.append("%s: solo %d imagenes en los ultimos %d dias (minimo %d). "
                          "Sin imagenes no hay calidad que medir: revisar las descargas."
                          % (fuente, n_r, dias, MIN_RECIENTES))
            continue
        tipos = sorted(t for (f, t) in casos if f == fuente)
        for tipo in tipos:
            rec, hab = casos[(fuente, tipo)]
            k_r, k_h = len(rec), len(hab)
            p_h = (k_h + 0.5) / (n_h + 1)
            tasa_r = k_r / n_r
            pval = cola_binomial(k_r, n_r, p_h)
            disparo = pval < ALFA and k_r >= MIN_CASOS and tasa_r >= RAZON_MIN * p_h
            filas.append((fuente, tipo, k_r, n_r, k_h, n_h, tasa_r, p_h, pval, disparo))
            if disparo:
                ej = ", ".join("%s %s" % x for x in sorted(rec)[:5])
                fallas.append("%s %s: %d de %d imagenes recientes (%.1f%%) contra %.1f%% "
                              "habitual (p=%.1e). Ejemplos: %s"
                              % (fuente, tipo, k_r, n_r, 100 * tasa_r, 100 * p_h, pval, ej))
        if n_h < 50:
            avisos.append("%s: referencia corta (%d imagenes), la comparacion es debil"
                          % (fuente, n_h))
    return filas, fallas, avisos, corte


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--actual", required=True, help="JSON producido por auditoria_imagenes.py")
    ap.add_argument("--hoy", help="fecha de referencia AAAA-MM-DD (por defecto, hoy UTC)")
    ap.add_argument("--dias", type=int, default=DIAS_RECIENTES)
    args = ap.parse_args()

    hoy = (dt.date.fromisoformat(args.hoy) if args.hoy
           else dt.datetime.now(dt.timezone.utc).date())
    with open(args.actual, encoding="utf-8") as fh:
        datos = json.load(fh)
    filas, fallas, avisos, corte = evaluar(datos, hoy, args.dias)

    print("Recientes: fecha > %s (%d dias). Habitual: el resto de la ventana publicada."
          % (corte, args.dias))
    print("%-18s %-22s %12s %12s %8s %8s %9s" %
          ("fuente", "tipo", "recientes", "habitual", "%rec", "%hab", "p"))
    for f, t, k_r, n_r, k_h, n_h, tr, ph, pv, d in filas:
        print("%-18s %-22s %5d/%-6d %5d/%-6d %7.1f%% %7.1f%% %9.1e%s"
              % (f, t, k_r, n_r, k_h, n_h, 100 * tr, 100 * ph, pv, "  <== DISPARO" if d else ""))
    for a in avisos:
        print("[aviso] " + a)
    if fallas:
        print("\n[FALLA] la calidad reciente se aparta de la habitual:")
        for x in fallas:
            print("  - " + x)
        if any(fila[-1] for fila in filas):
            print("\nSi un disparo es una condicion real de la escena (nevadas, humo), anotalo en "
                  "el Issue y cierralo; el aviso se apaga solo cuando esas fechas salgan de los "
                  "ultimos %d dias." % args.dias)
        return 1
    print("\n[ok] ningun tipo de hallazgo se disparo respecto de lo habitual.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
