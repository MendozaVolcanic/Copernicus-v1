"""
Tests del downloader Sentinel-2 (sin tocar red).

Mockean requests/HTTP. Validan:
  - Fail-fast en 401/403 al obtener token (SystemExit)
  - Dedup de misma fecha: queda el de menor cloud_cover
  - `procesar_volcan` no re-descarga si el PNG ya existe
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from sentinel2_downloader import SentinelHubAuth, SentinelHubSearcher


# ----------------------------- Fail-fast 401 --------------------------------

def _fake_response(status_code: int, json_body: dict | None = None):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = json_body or {}
    r.text = str(json_body or {})
    return r


def test_fail_fast_en_401_levanta_systemexit():
    """Auth con 401 debe abortar el proceso, no devolver token vacío."""
    auth = SentinelHubAuth()
    fake = _fake_response(
        401,
        {"error": "invalid_client", "error_description": "Invalid credentials"},
    )
    with patch("sentinel2_downloader.requests.post", return_value=fake):
        with pytest.raises(SystemExit) as exc_info:
            auth._fetch_token()
        msg = str(exc_info.value)
        assert "401" in msg
        assert "Autenticacion" in msg or "autenticacion" in msg.lower()


def test_fail_fast_en_403_levanta_systemexit():
    auth = SentinelHubAuth()
    fake = _fake_response(403, {"error": "forbidden"})
    with patch("sentinel2_downloader.requests.post", return_value=fake):
        with pytest.raises(SystemExit):
            auth._fetch_token()


def test_auth_200_obtiene_token():
    """Caso feliz: 200 + json con access_token guarda el token."""
    auth = SentinelHubAuth()
    fake = _fake_response(200, {"access_token": "abc-123", "expires_in": 3600})
    with patch("sentinel2_downloader.requests.post", return_value=fake):
        auth._fetch_token()
    assert auth.access_token == "abc-123"


# ----------------------------- Errores transitorios (429/503) ---------------

def test_es_error_transitorio_detecta_429_y_503():
    """429/503 = rate-limit transitorio (reintentar con backoff), NO fatal.

    Distinto del 403-cuota (rota cuenta) y del 401 (renueva token). Antes un 429
    caia en el except y devolvia [] -> "No hay imagenes" -> volcan salteado.
    """
    from sentinel2_downloader import es_error_transitorio
    assert es_error_transitorio(_fake_response(429)) is True
    assert es_error_transitorio(_fake_response(503)) is True
    # NO transitorios:
    assert es_error_transitorio(_fake_response(200)) is False
    assert es_error_transitorio(_fake_response(403)) is False
    assert es_error_transitorio(_fake_response(401)) is False
    assert es_error_transitorio(None) is False


# ----------------------------- Failover multi-cuenta ------------------------

def _resp_cuota_403():
    """403 de PU/creditos agotados (debe gatillar rotacion, no abortar por creds)."""
    return _fake_response(
        403,
        {"code": 403, "description": "Insufficient processing units or requests available in your account."},
    )


def test_es_error_cuota_distingue_pu_de_creds_malas():
    """403 de cuota -> True; 403 de creds malas -> False; 200 -> False."""
    assert SentinelHubAuth.es_error_cuota(_resp_cuota_403()) is True
    assert SentinelHubAuth.es_error_cuota(_fake_response(403, {"error": "forbidden"})) is False
    assert SentinelHubAuth.es_error_cuota(_fake_response(200, {"access_token": "x"})) is False


def test_rotate_account_con_backup_avanza_y_se_detiene():
    auth = SentinelHubAuth(cred_sets=[("id1", "sec1"), ("id2", "sec2")])
    assert auth.active == 0 and auth.client_id == "id1"
    assert auth.rotate_account() is True
    assert auth.active == 1 and auth.client_id == "id2"
    assert auth.rotate_account() is False   # no hay tercera
    assert auth.active == 1                  # se queda en la ultima


def test_rotate_account_single_no_rotea():
    auth = SentinelHubAuth(cred_sets=[("solo", "una")])
    assert auth.rotate_account() is False


def test_fetch_token_rota_a_backup_cuando_la_primera_falla():
    """1a cuenta 403, 2a cuenta 200 -> termina autenticado con la 2a."""
    auth = SentinelHubAuth(cred_sets=[("malo", "malo"), ("bueno", "bueno")])
    respuestas = [
        _fake_response(403, {"error": "forbidden"}),                        # cuenta 1 falla
        _fake_response(200, {"access_token": "tok2", "expires_in": 3600}),  # cuenta 2 ok
    ]
    with patch("sentinel2_downloader.requests.post", side_effect=respuestas):
        auth._fetch_token()
    assert auth.access_token == "tok2"
    assert auth.active == 1


def test_search_403_cuota_sin_backup_levanta_systemexit():
    """Cuota agotada y SIN backup -> SystemExit (run ROJO), NO [] silencioso.

    Este es el fix de la falla silenciosa: antes el 403 caia en el except y
    devolvia [] -> "No hay imagenes" -> job VERDE con 0 descargas.
    """
    auth = SentinelHubAuth(cred_sets=[("id1", "sec1")])
    auth.access_token = "tok"
    auth.token_expiry = time.time() + 9999  # token valido -> no intenta fetch real
    searcher = SentinelHubSearcher(auth)
    with patch("sentinel2_downloader.requests.get", return_value=_resp_cuota_403()):
        with pytest.raises(SystemExit):
            searcher.search_images(-39.42, -71.93, "2026-05-01", "2026-06-01")


def test_search_403_cuota_con_backup_rota_y_no_aborta():
    """Con backup, la busqueda rota a la 2a cuenta y reintenta (no SystemExit)."""
    auth = SentinelHubAuth(cred_sets=[("id1", "sec1"), ("id2", "sec2")])
    auth.access_token = "tok"
    auth.token_expiry = time.time() + 9999
    searcher = SentinelHubSearcher(auth)
    # GET 1: 403 cuota -> rota (resetea token). GET 2: 200 con 0 features -> [].
    # rotate_account resetea el token -> el GET 2 re-pide token via POST (mockeado).
    get_respuestas = [_resp_cuota_403(), _fake_response(200, {"features": []})]
    token_ok = _fake_response(200, {"access_token": "tok2", "expires_in": 3600})
    with patch("sentinel2_downloader.requests.get", side_effect=get_respuestas), \
         patch("sentinel2_downloader.requests.post", return_value=token_ok):
        res = searcher.search_images(-39.42, -71.93, "2026-05-01", "2026-06-01")
    assert res == []
    assert auth.active == 1  # rotó a la cuenta backup


# ----------------------------- Dedup misma fecha ----------------------------

def test_dedup_misma_fecha_elige_menor_cloud_cover():
    """
    Replica la lógica de dedup de procesar_volcan(): si 2 satélites pasan el
    mismo día, se conserva el de menor cloud_cover.
    """
    resultados = [
        {"date": "2026-05-10", "cloud_cover": 80, "sensor": "S2A"},
        {"date": "2026-05-10", "cloud_cover": 15, "sensor": "S2B"},  # mejor
        {"date": "2026-05-08", "cloud_cover": 40, "sensor": "S2A"},
        {"date": "2026-05-08", "cloud_cover": 55, "sensor": "S2C"},
        {"date": "2026-05-05", "cloud_cover": 5,  "sensor": "S2B"},  # único
    ]

    # Misma lógica que procesar_volcan
    por_fecha = {}
    for r in resultados:
        f = r["date"]
        if f not in por_fecha or r["cloud_cover"] < por_fecha[f]["cloud_cover"]:
            por_fecha[f] = r

    assert len(por_fecha) == 3
    assert por_fecha["2026-05-10"]["cloud_cover"] == 15
    assert por_fecha["2026-05-10"]["sensor"] == "S2B"
    assert por_fecha["2026-05-08"]["cloud_cover"] == 40
    assert por_fecha["2026-05-05"]["cloud_cover"] == 5


# ----------------------------- Skip de archivos existentes ------------------

def test_procesar_volcan_skipa_si_archivo_existe(tmp_path, volcan_test, monkeypatch):
    """
    Si el PNG ya existe en disco, `procesar_volcan` no debe llamar
    a `downloader.download_image` para esa fecha+tipo.
    """
    import sentinel2_downloader as sd

    # Forzar que get_image_path devuelva una ruta dentro de tmp_path que YA exista
    fecha = "2026-05-10"

    def fake_get_path(volcan, fch, tipo):
        p = tmp_path / volcan / f"{fch}_{tipo}.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"FAKE_PNG_CONTENT_1234567890")
        return str(p)

    monkeypatch.setattr(sd, "get_image_path", fake_get_path)

    # Searcher devuelve 1 resultado, downloader registra calls
    searcher = MagicMock()
    searcher.search_images.return_value = [
        {"date": fecha, "cloud_cover": 10.0, "sensor": "Sentinel-2A L2A"},
    ]
    downloader = MagicMock()
    downloader.download_image.return_value = True  # nunca debería llamarse
    auth = MagicMock()

    res = sd.procesar_volcan("VolcanTest", volcan_test, auth, searcher, downloader)

    assert res is not None
    assert len(res) == 3  # RGB + ThermalFalseColor + SWIR_B8A (SWIR_raw removido: VRP vive en proyecto aparte)
    # NO debió descargar nada
    assert downloader.download_image.call_count == 0


def test_procesar_volcan_descarga_si_no_existe(tmp_path, volcan_test, monkeypatch):
    """Si no existe el archivo, sí debe invocar download_image."""
    import sentinel2_downloader as sd

    fecha = "2026-05-10"

    def fake_get_path(volcan, fch, tipo):
        p = tmp_path / volcan / f"{fch}_{tipo}.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        return str(p)

    monkeypatch.setattr(sd, "get_image_path", fake_get_path)

    searcher = MagicMock()
    searcher.search_images.return_value = [
        {"date": fecha, "cloud_cover": 10.0, "sensor": "Sentinel-2A L2A"},
    ]

    def fake_download(lat, lon, fch, tipo, output_path, buffer_km):
        # Simula que efectivamente escribe el archivo
        from pathlib import Path as _P
        _P(output_path).write_bytes(b"FAKE_BYTES_OK_12345")
        return True

    downloader = MagicMock()
    downloader.download_image.side_effect = fake_download
    auth = MagicMock()

    res = sd.procesar_volcan("VolcanTest", volcan_test, auth, searcher, downloader)

    assert res is not None
    # 3 tipos (RGB + ThermalFalseColor + SWIR_B8A)
    assert downloader.download_image.call_count == 3
