"""
Tests del predictor de proximas pasadas (generar_proximas_pasadas.py).

Foco: el fix de DST chileno (horario de verano). Antes el offset era UTC-4 fijo
y la hora/countdown quedaban 1h corridos ~7 meses al ano. Ahora se deriva con
zoneinfo America/Santiago aplicado a la fecha concreta de cada pasada.
"""

from generar_proximas_pasadas import calcular_hora_chile, estimar_hora_utc


# ----------------------------- DST chileno ----------------------------------

def test_hora_chile_invierno_es_utc4():
    """15-jun = invierno austral -> Chile continental UTC-4 (14:34Z -> 10:34)."""
    assert calcular_hora_chile("14:34", "2026-06-15") == "10:34"


def test_hora_chile_verano_es_utc3():
    """15-ene = verano austral (DST activo) -> UTC-3 (14:34Z -> 11:34)."""
    assert calcular_hora_chile("14:34", "2026-01-15") == "11:34"


def test_hora_chile_dst_corre_una_hora():
    """La misma hora UTC da distinto en verano vs invierno: el DST corre 1h."""
    invierno = calcular_hora_chile("14:00", "2026-07-01")
    verano = calcular_hora_chile("14:00", "2026-01-01")
    assert invierno != verano
    # Verano es 1h mas tarde que invierno (UTC-3 vs UTC-4)
    h_inv = int(invierno.split(":")[0])
    h_ver = int(verano.split(":")[0])
    assert h_ver == h_inv + 1


# ----------------------------- estimar_hora_utc -----------------------------

def test_estimar_hora_utc_en_rango_observado():
    """La hora UTC estimada cae en el rango empirico 14:24-14:40 para Chile."""
    for lon in (-73.5, -71.0, -67.0):
        hhmm = estimar_hora_utc(lon)
        h, m = map(int, hhmm.split(":"))
        minutos = h * 60 + m
        assert 14 * 60 + 24 <= minutos <= 14 * 60 + 40, f"{lon} -> {hhmm} fuera de rango"


# ----------------------------- Prediccion por fase orbital ------------------

def _hist(vol, *dias_atras_y_sat):
    """Helper: DataFrame de historial con (dias_atras, sat)."""
    import pandas as pd
    from datetime import datetime, timezone, timedelta
    hoy = datetime.now(timezone.utc).date()
    filas = [{"volcan": vol, "fecha": pd.Timestamp(hoy - timedelta(days=d)), "sat": s}
             for d, s in dias_atras_y_sat]
    return pd.DataFrame(filas)


def test_prediccion_incluye_pasada_de_hoy():
    """La pasada de HOY debe aparecer (no pre-rolarse +10d a las 00:00).

    Bug del usuario: el countdown saltaba de '18h' a '5 dias' al cambiar de dia
    porque `while <= hoy` + filtro `> hoy` descartaban la pasada de hoy a la
    medianoche, antes de que ocurriera (14:30 UTC) y de que llegara la imagen.
    """
    from datetime import datetime, timezone
    from generar_proximas_pasadas import predecir
    from config_sentinel2 import VOLCANES
    vol = next(iter(VOLCANES))
    hoy = datetime.now(timezone.utc).date()
    # Observacion hace exactamente 10 dias -> misma fase que hoy -> pasada HOY.
    pred = predecir(_hist(vol, (10, "Sentinel-2A")))
    fechas = [p["fecha"] for p in pred[vol]["proxima_combinada"]]
    assert hoy.isoformat() in fechas, f"La pasada de hoy ({hoy}) debe estar; hay {fechas[:3]}"


def test_prediccion_captura_doble_orbita():
    """2 fases (solape de 2 orbitas) -> ~2 pasadas por ciclo, no 1.

    El modelo viejo anclaba a la UNICA ultima descarga + 10d -> subcontaba la
    mitad de las pasadas (huecos fantasma de 5d). El nuevo proyecta por fase.
    """
    from datetime import datetime, timezone, date
    from generar_proximas_pasadas import predecir
    from config_sentinel2 import VOLCANES
    vol = next(iter(VOLCANES))
    hoy = datetime.now(timezone.utc).date()
    # Dos orbitas: una hace 10d (fase de hoy), otra hace 7d (otra fase).
    pred = predecir(_hist(vol, (10, "Sentinel-2A"), (7, "Sentinel-2A")))
    prox = pred[vol]["satelites"]["Sentinel-2A"]["proximas"]
    primer_ciclo = [f for f in prox if (date.fromisoformat(f) - hoy).days < 10]
    assert len(primer_ciclo) >= 2, f"2 fases deben dar >=2 pasadas en el 1er ciclo; hay {primer_ciclo}"


def test_prediccion_no_predice_pasado():
    """Ninguna fecha de proxima_combinada debe ser anterior a hoy."""
    from datetime import datetime, timezone
    from generar_proximas_pasadas import predecir
    from config_sentinel2 import VOLCANES
    vol = next(iter(VOLCANES))
    hoy_iso = datetime.now(timezone.utc).date().isoformat()
    pred = predecir(_hist(vol, (12, "Sentinel-2B"), (5, "Sentinel-2C")))
    for p in pred[vol]["proxima_combinada"]:
        assert p["fecha"] >= hoy_iso, f"{p['fecha']} es pasado"
