# -*- coding: utf-8 -*-
"""Auditoria de calidad de las imagenes publicadas (Sentinel-2 y Landsat).

QUE PROBLEMA RESUELVE
=====================
Dos fallas reales, encontradas en agosto de 2026, que el pipeline no detectaba
porque nada miraba las imagenes YA GUARDADAS:

  1. ANOMALIA PERDIDA. Villarrica 2026-07-03 se publico con la anomalia termica
     borrada: el canal SWIR quedo topado en 79/255 en vez de 255. La escena si
     tenia la anomalia -- al re-descargarla aparecio con 176 pixeles rojos. El
     evalscript estaba bien; el archivo guardado estaba mal. Un mes en linea sin
     que nadie lo notara.

  2. IMAGEN QUEMADA. En volcanes con nieve permanente o sobre el desierto de
     Atacama, la ganancia lineal 2.5 satura las dos bandas SWIR a la vez.
     Lascar 2026-07-01 sale con los 640.000 pixeles saturados: la imagen
     completa. Villarrica 2026-06-26, con 64.228.

POR QUE LO SEGUNDO ES GRAVE, Y NO SOLO FEO
==========================================
Lo que separa una roca caliente de la nieve NO es el brillo -- las dos son
brillantes en SWIR -- sino CUAL de las dos bandas es mas fuerte:

    NHI = (B12 - B11) / (B12 + B11)        (Marchese et al. 2019)

    roca caliente -> B12 > B11 -> NHI > 0   (a mayor temperatura, el pico de
                                             emision se corre hacia 2.2 um)
    nieve         -> B12 < B11 -> NHI < 0   (el hielo absorbe mas en 2.2 um)

El falso color pinta B12 en rojo y B11 en verde. Cuando LAS DOS saturan en 255,
la diferencia entre ellas se destruye: rojo = verde = 255, o sea NHI = 0. Nieve
y lava quedan del mismo blanco, y ninguna inspeccion visual del PNG puede ya
distinguirlas. La saturacion no oscurece la imagen: borra justamente la magnitud
que discrimina el fenomeno.

De ahi la metrica central de esta auditoria: FRACCION CIEGA, el porcentaje de la
escena donde ya no se puede saber si hay calor o solo brillo.

COMO SE USA
===========
    python auditoria_imagenes.py                  # audita todo, resumen
    python auditoria_imagenes.py --detalle        # una linea por hallazgo
    python auditoria_imagenes.py --volcan Lascar  # filtra
    python auditoria_imagenes.py --json out.json  # para el dashboard o CI

No consume Processing Units: lee unicamente PNG ya presentes en disco.

LIMITE QUE HAY QUE TENER PRESENTE
=================================
Sobre un PNG se puede probar que una imagen esta CIEGA (saturada), pero NO se
puede probar que le falta una anomalia: para eso hay que comparar contra la
escena original. Los casos de anomalia sospechosa salen marcados como
REQUIERE_VERIFICACION, con el comando para contrastarlos. Confundir "sospechoso"
con "confirmado" fue un error cometido durante el diagnostico: de 4 fechas
sospechosas verificadas contra la fuente, solo 1 era bug real.
"""

import argparse
import glob
import json
import os
import sys

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Umbrales. Cada uno con el caso real que lo fijo, para que se pueda discutir.
# ---------------------------------------------------------------------------
SAT = 254            # a partir de aca un canal de 8 bits se considera saturado
CIEGA_ATENCION = 20.0    # % de escena ciega que merece mirarse
CIEGA_GRAVE = 60.0       # Lascar 2026-07-01 daba 100%
PLANA_STD = 3.0          # desvio tipico por debajo del cual no hay informacion
NODATA_MAX = 40.0        # % de escena sin dato tolerable
TRUNC_RATIO = 0.55       # tope < 55% de la referencia del propio volcan
TRUNC_MESETA = 50        # ...y con meseta: la firma de un clip, no de escena fria
NHI_MIN_SENAL = 40       # piso de senal para que el NHI signifique algo (8 bits)
NHI_CALOR = 0.15         # NHI que ya no se explica por ruido de cuantizacion


def cargar(path):
    try:
        im = np.array(Image.open(path).convert('RGB')).astype(np.int16)
    except Exception:
        return None
    return im


def analizar(im):
    """Metricas de una imagen en falso color SWIR (R=B12, G=B11, B=visible)."""
    R, G, B = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    total = R.size

    # negro perfecto en los tres canales = fuera de la pasada
    nodata = (R == 0) & (G == 0) & (B == 0)
    n_val = total - int(nodata.sum())
    if n_val == 0:
        return None

    val = ~nodata
    # CIEGA: las dos bandas SWIR saturadas -> NHI indistinguible
    ciega = val & (R >= SAT) & (G >= SAT)

    # NHI aproximado donde SI se puede medir: ni saturado ni tan oscuro que el
    # cociente sea ruido de cuantizacion. Con R=21 y G=19 -- diferencia de UN
    # nivel de 8 bits -- sale NHI=0.05 sin ningun significado fisico. Sin el
    # piso NHI_MIN_SENAL el detector reporta miles de falsos "calor": es el modo
    # de falla de un instrumento vivo que mide otra magnitud (ruido, no calor).
    medible = val & ~ciega & (R >= NHI_MIN_SENAL)
    if medible.sum() > 0:
        rr = R[medible].astype(np.float32)
        gg = G[medible].astype(np.float32)
        nhi = (rr - gg) / np.maximum(rr + gg, 1.0)
        nhi_p999 = float(np.percentile(nhi, 99.9))
        calor = int((nhi > NHI_CALOR).sum())
    else:
        nhi_p999, calor = float('nan'), 0

    rojo = val & (R > 150) & ((R - np.maximum(G, B)) > 40)
    mx = int(R[val].max())
    return {
        'nodata_pct': round(100.0 * float(nodata.mean()), 1),
        'ciega_pct': round(100.0 * int(ciega.sum()) / n_val, 1),
        'std': round(float(R[val].std()), 1),
        'r_max': mx,
        'meseta': int((R[val] == mx).sum()),
        'rojos': int(rojo.sum()),
        'nhi_p999': None if nhi_p999 != nhi_p999 else round(nhi_p999, 3),
        'px_calor': calor,
    }


def auditar(raiz, patron, filtro=None):
    """Recorre las imagenes y agrupa por volcan para comparar cada fecha
    contra el comportamiento habitual de SU volcan (no contra un valor fijo)."""
    grupos = {}
    for f in glob.glob(os.path.join(raiz, patron), recursive=True):
        volcan = os.path.basename(os.path.dirname(f))
        if filtro and filtro.lower() not in volcan.lower():
            continue
        base = os.path.basename(f)
        fecha = base[:10]
        if not (len(fecha) == 10 and fecha[4] == '-'):
            continue
        grupos.setdefault(volcan, []).append((fecha, f))

    hallazgos = []
    for volcan, items in sorted(grupos.items()):
        medidos = []
        for fecha, f in sorted(items):
            im = cargar(f)
            if im is None:
                continue
            m = analizar(im)
            if m:
                medidos.append((fecha, f, m))
        if not medidos:
            continue

        # referencia interna del volcan: mediana de sus topes
        ref = float(np.median([m['r_max'] for _, _, m in medidos]))

        for fecha, f, m in medidos:
            probs = []
            if m['nodata_pct'] > NODATA_MAX:
                probs.append(('NODATA', 'alta',
                              f"{m['nodata_pct']}% de la escena sin dato"))
            if m['ciega_pct'] >= CIEGA_GRAVE:
                probs.append(('QUEMADA', 'alta',
                              f"{m['ciega_pct']}% ciega: calor y nieve indistinguibles"))
            elif m['ciega_pct'] >= CIEGA_ATENCION:
                probs.append(('QUEMADA', 'media',
                              f"{m['ciega_pct']}% de la escena ciega por saturacion"))
            if m['std'] < PLANA_STD:
                probs.append(('PLANA', 'media',
                              f"desvio {m['std']}: imagen sin contraste util"))
            if (ref >= 200 and m['r_max'] < ref * TRUNC_RATIO
                    and m['meseta'] >= TRUNC_MESETA):
                probs.append(('REQUIERE_VERIFICACION', 'media',
                              f"tope {m['r_max']} vs {int(ref)} habitual del volcan, "
                              f"meseta de {m['meseta']} px"))
            # calor medible que el ojo no ve como rojo
            if m['px_calor'] > 200 and m['rojos'] == 0:
                probs.append(('CALOR_NO_VISIBLE', 'media',
                              f"{m['px_calor']} px con NHI>{NHI_CALOR} y ningun pixel rojo"))
            for tipo, sev, det in probs:
                hallazgos.append({'volcan': volcan, 'fecha': fecha, 'tipo': tipo,
                                  'severidad': sev, 'detalle': det,
                                  'archivo': os.path.relpath(f, raiz),
                                  'metricas': m})
    return hallazgos, sum(len(v) for v in grupos.values())


def control_positivo():
    """Regla dura 9: un negativo medido con el instrumento caido no es un
    negativo. Antes de creerle a esta auditoria, se le pasan casos construidos
    de respuesta conocida. Si falla alguno, el resto de los numeros no valen."""
    pruebas = []

    quemada = np.full((50, 50, 3), 255, np.uint8)
    pruebas.append(('imagen toda saturada -> QUEMADA', quemada,
                    lambda m: m['ciega_pct'] > 99))

    plana = np.zeros((50, 50, 3), np.uint8)
    plana[:, :, 2] = 100
    pruebas.append(('imagen sin contraste -> PLANA', plana,
                    lambda m: m['std'] < PLANA_STD))

    sana = np.zeros((50, 50, 3), np.uint8)
    sana[:, :, 2] = 90
    sana[20:24, 20:24, 0] = 255          # anomalia roja compacta
    rng = np.random.default_rng(0)
    sana[:, :, 0] = np.maximum(sana[:, :, 0], rng.integers(0, 60, (50, 50)))
    pruebas.append(('anomalia roja sobre fondo -> se detecta', sana,
                    lambda m: m['rojos'] > 0 and m['ciega_pct'] < 5))

    nodata = np.zeros((50, 50, 3), np.uint8)
    nodata[:10, :, 2] = 120
    pruebas.append(('escena mayormente vacia -> NODATA', nodata,
                    lambda m: m['nodata_pct'] > NODATA_MAX))

    # Las dos ramas que deben quedar SEPARABLES: si el detector de calor no
    # distingue ruido oscuro de una anomalia real, no es un detector.
    rng2 = np.random.default_rng(1)
    ruido = np.zeros((80, 80, 3), np.uint8)
    ruido[:, :, 0] = rng2.integers(5, 30, (80, 80))   # SWIR oscuro con ruido
    ruido[:, :, 1] = rng2.integers(5, 30, (80, 80))
    ruido[:, :, 2] = 80
    pruebas.append(('ruido oscuro -> NO debe reportar calor', ruido,
                    lambda m: m['px_calor'] == 0))

    caliente = np.zeros((80, 80, 3), np.uint8)
    caliente[:, :, 0] = rng2.integers(5, 30, (80, 80))
    caliente[:, :, 1] = rng2.integers(5, 30, (80, 80))
    caliente[:, :, 2] = 80
    caliente[38:46, 38:46, 0] = 220      # B12 alto
    caliente[38:46, 38:46, 1] = 90       # B11 bajo -> NHI claramente positivo
    pruebas.append(('anomalia con NHI real -> SI debe reportar calor', caliente,
                    lambda m: m['px_calor'] >= 60))

    ok = True
    print("CONTROL POSITIVO DEL INSTRUMENTO")
    for nombre, img, cond in pruebas:
        m = analizar(img.astype(np.int16))
        paso = bool(m) and cond(m)
        print(f"   [{'ok ' if paso else 'FALLA'}] {nombre}")
        ok = ok and paso
    if not ok:
        print("\n   El instrumento no distingue sus propios casos de prueba.")
        print("   No interpretes los resultados de abajo.")
    print()
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--volcan', help='filtra por nombre de volcan')
    ap.add_argument('--detalle', action='store_true', help='lista cada hallazgo')
    ap.add_argument('--json', help='guarda el resultado en un JSON')
    ap.add_argument('--landsat', help='ruta al repo Landsat-v1 para auditarlo tambien')
    args = ap.parse_args()

    raiz = os.path.dirname(os.path.abspath(__file__))

    if not control_positivo():
        return 2

    fuentes = [('SENTINEL-2', raiz, 'docs/sentinel2/**/*_ThermalFalseColor.png')]
    if args.landsat:
        fuentes.append(('LANDSAT 8/9', args.landsat, 'docs/landsat/**/*_SWIR.png'))

    todo = []
    for nombre, base, patron in fuentes:
        hall, n = auditar(base, patron, args.volcan)
        todo.extend({**h, 'fuente': nombre} for h in hall)
        print(f"{nombre}: {n} imagenes revisadas, {len(hall)} hallazgos")

        por_tipo = {}
        for h in hall:
            por_tipo.setdefault(h['tipo'], []).append(h)
        for tipo, hs in sorted(por_tipo.items(), key=lambda x: -len(x[1])):
            altas = sum(1 for h in hs if h['severidad'] == 'alta')
            print(f"   {tipo:<24}{len(hs):>5}   (severidad alta: {altas})")
            # volcanes mas afectados: donde conviene actuar
            pv = {}
            for h in hs:
                pv[h['volcan']] = pv.get(h['volcan'], 0) + 1
            top = sorted(pv.items(), key=lambda x: -x[1])[:4]
            print(f"      mas afectados: " +
                  ", ".join(f"{v} ({n})" for v, n in top))
        print()

    if args.detalle:
        print("-" * 78)
        for h in sorted(todo, key=lambda x: (x['tipo'], x['volcan'], x['fecha'])):
            print(f"  [{h['severidad']:<5}] {h['tipo']:<24}{h['volcan'][:22]:<24}"
                  f"{h['fecha']}  {h['detalle']}")

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as fh:
            json.dump({'hallazgos': todo, 'total': len(todo)}, fh,
                      indent=2, ensure_ascii=False)
        print(f"\nJSON escrito en {args.json}")

    graves = sum(1 for h in todo if h['severidad'] == 'alta')
    print(f"\nTOTAL: {len(todo)} hallazgos, {graves} de severidad alta")
    return 1 if graves else 0


if __name__ == '__main__':
    sys.exit(main())
