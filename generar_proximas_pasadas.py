"""
Genera docs/proximas_pasadas.json con la prediccion de proximas pasadas
de Sentinel-2 sobre cada volcan, basado en el historial de descargas.

LOGICA:
- Cada satelite (2A/2B/2C) tiene revisita exacta de 10 dias.
- Para cada par (volcan, satelite), la ultima fecha conocida + 10 dias
  da la siguiente pasada. Se proyectan 4 ciclos hacia adelante.
- La hora de paso se infiere del path (UTC ~14:43-14:55 segun longitud).

Uso (idealmente desde cron):
    python generar_proximas_pasadas.py

Output: docs/proximas_pasadas.json
"""
import os, sys, glob, json
import pandas as pd
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TZ_CHILE = ZoneInfo('America/Santiago')

from config_sentinel2 import VOLCANES

CICLO_DIAS = 10
PROYECCIONES = 4  # cuantos ciclos predecir hacia adelante

# Hora real de paso por longitud de path. Sentinel-2 pasa sobre Chile
# entre 14:26 y 14:37 UTC (10:26-10:37 hora Chile).
# FIX 2026-05-27: el rango previo (14:43-14:55 UTC) era estimacion vieja.
# Verificacion empirica con 75 escenas del catalogo CDSE muestra rango real
# 14:26-14:37 UTC. Sun-synchronous orbit, deltas <12 min entre paths E/W.
def estimar_hora_utc(lon):
    """Path occidental (-73) ~14:37 UTC, oriental (-67) ~14:26 UTC.
    Lineal interpolando entre limites observados."""
    lon_min, lon_max = -73.5, -67.0
    hora_min, hora_max = 14*60+37, 14*60+26  # minutos UTC (rango real)
    frac = (lon - lon_min) / (lon_max - lon_min)
    minutos = hora_min + frac * (hora_max - hora_min)
    minutos = max(14*60+24, min(14*60+40, minutos))
    h = int(minutos // 60)
    m = int(minutos % 60)
    return f"{h:02d}:{m:02d}"


def cargar_historial():
    """Carga todas las descargas registradas en metadata.csv"""
    todos = []
    for csv in glob.glob('docs/sentinel2/*/metadata.csv'):
        vol = os.path.basename(os.path.dirname(csv))
        try:
            df = pd.read_csv(csv)
            df = df[df['tipo'] == 'RGB'].copy()
            df['volcan'] = vol
            df['sat'] = df['sensor'].str.extract(r'(Sentinel-2[ABC])')
            df['fecha'] = pd.to_datetime(df['fecha'])
            todos.append(df[['volcan', 'fecha', 'sat']])
        except Exception:
            continue
    # DataFrame TIPADO si no hay historial: sin esto, un FS limpio / primer run deja
    # un DataFrame vacio sin columnas y predecir() crashea con KeyError 'volcan'
    # (el cron falla y el JSON de la Sala no se regenera). El gemelo Landsat ya lo guarda.
    return pd.concat(todos, ignore_index=True) if todos else pd.DataFrame(columns=['volcan', 'fecha', 'sat'])


def predecir(historial):
    """Para cada (volcan, sat), proyecta proximas pasadas por FASE ORBITAL.

    POR QUE FASE (no "ultima descarga + 10d"): la orbita de cada satelite repite
    EXACTO cada 10 dias, asi que el residuo `fecha.toordinal() % 10` de una pasada
    es estable. Ademas la mayoria de los puntos caen en el SOLAPE de 2 orbitas
    adyacentes -> cada satelite los fotografia ~2 veces por ciclo (2 fases). El
    modelo viejo (anclar a la unica ultima descarga + 10d) subcontaba pasadas
    (predecia la mitad -> huecos fantasma de 5d) y driftaba si faltaba una descarga.
    Proyectar por fase DESDE HOY captura las 2 orbitas y se auto-corrige.

    Combinada: intercala todas las fechas futuras (>= hoy) de los 3 satelites.
    Incluye HOY: la pasada de hoy se muestra hasta que realmente pase (el countdown
    del HTML distingue "en Xh" de "paso hace Xh"). El bug del usuario era que el
    `while <= hoy` + filtro `> hoy` tiraban la pasada de hoy a las 00:00 -> el
    countdown saltaba de "18h" a "5 dias" con la imagen sin cambiar.
    """
    hoy = datetime.now(timezone.utc).date()
    hoy_ord = hoy.toordinal()
    proxima = {}

    for vol, cfg in VOLCANES.items():
        df_vol = historial[historial['volcan'] == vol]
        sats_data = {}
        proximas_sat = []  # (fecha_iso, sat) de TODAS las fases de TODOS los sats

        hora_utc = estimar_hora_utc(cfg['lon'])

        for sat in ['Sentinel-2A', 'Sentinel-2B', 'Sentinel-2C']:
            df_s = df_vol[df_vol['sat'] == sat].sort_values('fecha')
            if df_s.empty:
                continue
            obs = [d.date() for d in df_s['fecha']]
            ultima = max(obs)

            # Fases (residuo mod 10) de las observaciones recientes (<=35d). El
            # solape de 2 orbitas da tipicamente 2 fases distintas por satelite.
            recientes = [d for d in obs if (ultima - d).days <= 35]
            fases = sorted(set(d.toordinal() % CICLO_DIAS for d in recientes)) \
                or [ultima.toordinal() % CICLO_DIAS]

            ciclos = []
            for fase in fases:
                off = (fase - hoy_ord) % CICLO_DIAS  # dias hasta la 1a fecha >= hoy con esa fase
                primera = hoy + timedelta(days=off)
                for k in range(PROYECCIONES):
                    ciclos.append((primera + timedelta(days=CICLO_DIAS * k)).isoformat())
            ciclos = sorted(set(ciclos))

            sats_data[sat] = {
                'ultima_observacion': ultima.isoformat(),
                'proximas': ciclos[:PROYECCIONES * 2],
            }
            for f in ciclos:
                proximas_sat.append((f, sat))

        # Combinada: fechas futuras (>= hoy), dedup por fecha, las 6 mas cercanas.
        hoy_iso = hoy.isoformat()
        proximas_sat.sort()
        vistos = set()
        combinada = []
        for f, s in proximas_sat:
            if f >= hoy_iso and f not in vistos:
                vistos.add(f)
                combinada.append({'fecha': f, 'sat': s,
                                  'hora_chile': calcular_hora_chile(hora_utc, f)})
            if len(combinada) >= 6:
                break

        # ultima_imagen: fecha de la imagen mas reciente YA descargada. El HTML la
        # usa para saber si la pasada de hoy ya produjo imagen (y mostrar countdown
        # de PUBLICACION L2A mientras se procesa, en vez de saltar a la siguiente).
        ultima_imagen = df_vol['fecha'].max().date().isoformat() if not df_vol.empty else None

        proxima[vol] = {
            'lat': cfg['lat'],
            'lon': cfg['lon'],
            'zona': cfg.get('zona', ''),
            'hora_utc_estimada': hora_utc,
            'hora_chile_estimada': calcular_hora_chile(hora_utc),
            'ultima_imagen': ultima_imagen,
            'satelites': sats_data,
            'proxima_combinada': combinada,
        }
    return proxima


def calcular_hora_chile(hora_utc_str, fecha_iso=None):
    """UTC -> hora local Chile continental, respetando DST (horario de verano).

    Chile continental alterna UTC-4 (invierno) / UTC-3 (verano austral, ~sep-abr).
    El offset NO es fijo: depende de la fecha. Por eso derivamos la hora local
    aplicando ZoneInfo('America/Santiago') al datetime UTC concreto de la pasada.

    Args:
        hora_utc_str: "HH:MM" UTC (fuente de verdad, hora_utc_estimada).
        fecha_iso: "YYYY-MM-DD" de la pasada. Si None, usa hoy (solo para el
                   campo informativo del header; cada pasada calcula la suya).
    Returns:
        "HH:MM" en hora local Chile para esa fecha concreta.
    """
    h, m = map(int, hora_utc_str.split(':'))
    if fecha_iso:
        y, mo, d = map(int, fecha_iso.split('-'))
    else:
        hoy = datetime.now(timezone.utc).date()
        y, mo, d = hoy.year, hoy.month, hoy.day
    dt_utc = datetime(y, mo, d, h, m, tzinfo=timezone.utc)
    dt_local = dt_utc.astimezone(TZ_CHILE)
    return dt_local.strftime('%H:%M')


def main():
    print("Cargando historial de descargas...")
    historial = cargar_historial()
    print(f"  {len(historial)} observaciones registradas")

    print("Prediciendo proximas pasadas...")
    pred = predecir(historial)

    output = {
        'generado_utc': datetime.now(timezone.utc).isoformat(),
        'ciclo_dias_por_satelite': CICLO_DIAS,
        'satelites': ['Sentinel-2A', 'Sentinel-2B', 'Sentinel-2C'],
        # Modelo de latencia de publicacion L2A (empirico, 75 escenas CDSE). El
        # HTML lo usa para el countdown de PUBLICACION cuando la pasada ya ocurrio
        # pero la imagen todavia no se publico. Bimodal: pico ppal 18-20 UTC,
        # pico tardio 01-02 UTC del dia siguiente, zona muerta 03-17 UTC.
        'latencia_l2a': {
            'mediana_h': 4.7,
            'p95_h': 11.7,
            'picos_utc': [[18, 20], [1, 2]],
            'zona_muerta_utc': [3, 17],
        },
        'volcanes': pred,
    }

    os.makedirs('docs', exist_ok=True)
    out_path = 'docs/proximas_pasadas.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nGenerado: {out_path}")

    # Resumen
    print(f"\n=== PROXIMAS PASADAS (5 mas cercanas) ===")
    todas = []
    for vol, info in pred.items():
        for p in info['proxima_combinada'][:1]:
            todas.append((p['fecha'], vol, p['sat'], info['hora_chile_estimada']))
    todas.sort()
    for fecha, vol, sat, hora in todas[:10]:
        print(f"  {fecha} {hora} Chile | {vol:30} | {sat}")


if __name__ == "__main__":
    main()
