"""
Tests del config principal (config_sentinel2.py).

Valida:
  - Cantidad y forma de la tabla VOLCANES
  - Rangos geográficos válidos para Chile continental
  - Atributos obligatorios
  - IDs SERNAGEOMIN únicos
  - Vistas zoom apuntan a volcán existente
  - Bug fix Nevados de Chillán (no debe tener coords de Antuco)
"""

import pytest

from config_sentinel2 import VOLCANES


ZONAS_VALIDAS = {"Norte", "Centro", "Sur", "Austral"}

# Rangos para Chile continental (incluye margen para zoom + Norte/Austral)
LAT_MIN, LAT_MAX = -56.0, -17.5
LON_MIN, LON_MAX = -76.0, -66.5


def _volcanes_principales() -> dict:
    """Volcanes sin contar las 3 vistas zoom."""
    return {k: v for k, v in VOLCANES.items() if "vista_zoom_de" not in v}


def _vistas_zoom() -> dict:
    return {k: v for k, v in VOLCANES.items() if "vista_zoom_de" in v}


# ----------------------------- Forma / cardinalidad --------------------------

def test_total_51_entidades():
    """51 entidades: 43 volcanes principales + 8 vistas zoom.
    FIX 2026-06-04: +3 zooms (Lascar/Isluga/Copahue).
    FIX 2026-06-15: +2 zooms (Chillan Crater Nicanor, Longavi Crater)."""
    assert len(VOLCANES) == 51, f"Esperaba 51 entidades, hay {len(VOLCANES)}"


def test_43_volcanes_principales():
    assert len(_volcanes_principales()) == 43


def test_8_vistas_zoom():
    zoom = _vistas_zoom()
    assert len(zoom) == 8
    assert set(zoom) == {
        "Melimoyu_Conos_Eruptivos",
        "Mentolat_Sismicidad_VT",
        "Hudson_Ultima_Erupcion",
        "Lascar_Crater",
        "Isluga_Crater_Fumarola",
        "Copahue_Crater_Lake",
        "Nevados_de_Chillan_Crater_Nicanor",
        "Nevado_de_Longavi_Crater",
    }


# ----------------------------- Campos obligatorios ---------------------------

CAMPOS_OBLIGATORIOS = {"lat", "lon", "buffer_km", "id", "zona", "activo"}


@pytest.mark.parametrize("nombre,cfg", list(VOLCANES.items()))
def test_campos_obligatorios_presentes(nombre, cfg):
    faltantes = CAMPOS_OBLIGATORIOS - set(cfg.keys())
    assert not faltantes, f"{nombre} faltan campos: {faltantes}"


# ----------------------------- Geografía -------------------------------------

@pytest.mark.parametrize("nombre,cfg", list(VOLCANES.items()))
def test_coords_en_rango_chile(nombre, cfg):
    assert LAT_MIN <= cfg["lat"] <= LAT_MAX, (
        f"{nombre}: lat={cfg['lat']} fuera de [{LAT_MIN},{LAT_MAX}]"
    )
    assert LON_MIN <= cfg["lon"] <= LON_MAX, (
        f"{nombre}: lon={cfg['lon']} fuera de [{LON_MIN},{LON_MAX}]"
    )


@pytest.mark.parametrize("nombre,cfg", list(VOLCANES.items()))
def test_zona_valida(nombre, cfg):
    assert cfg["zona"] in ZONAS_VALIDAS, (
        f"{nombre}: zona='{cfg['zona']}' no está en {ZONAS_VALIDAS}"
    )


@pytest.mark.parametrize("nombre,cfg", list(VOLCANES.items()))
def test_buffer_km_razonable(nombre, cfg):
    b = cfg["buffer_km"]
    assert 0 < b < 20, f"{nombre}: buffer_km={b} fuera de (0, 20)"


# ----------------------------- IDs SERNAGEOMIN -------------------------------

def test_ids_principales_son_unicos():
    """Los IDs SERNAGEOMIN entre volcanes principales deben ser únicos."""
    ids = [v["id"] for v in _volcanes_principales().values()]
    duplicados = {x for x in ids if ids.count(x) > 1}
    assert not duplicados, f"IDs duplicados entre volcanes principales: {duplicados}"


# ----------------------------- Vistas zoom -----------------------------------

def test_vistas_zoom_apuntan_a_volcan_existente():
    principales = set(_volcanes_principales().keys())
    for nombre, cfg in _vistas_zoom().items():
        padre = cfg["vista_zoom_de"]
        assert padre in principales, (
            f"Vista zoom {nombre} apunta a '{padre}' que no es un volcán principal"
        )


# ----------------------------- Bug fix Chillán -------------------------------

def test_nevados_chillan_no_es_antuco():
    """
    Regresión 2026-05-17: Nevados de Chillán antes tenía coords (-37.41, -71.35)
    que apuntaban a Antuco. Coord oficial SERNAGEOMIN: -36.870 / -71.380.
    """
    chillan = VOLCANES["Nevados de Chillan"]
    antuco = VOLCANES["Antuco"]

    # No deben compartir coordenadas (Antuco es claramente más al sur)
    assert chillan["lat"] != antuco["lat"], (
        "Nevados de Chillán y Antuco no pueden compartir latitud"
    )
    assert chillan["lon"] != antuco["lon"], (
        "Nevados de Chillán y Antuco no pueden compartir longitud"
    )

    # Chillán debe estar al norte de Antuco
    assert chillan["lat"] > antuco["lat"], (
        f"Chillán (lat={chillan['lat']}) debe estar al NORTE de Antuco (lat={antuco['lat']})"
    )

    # Chillán oficial está cerca de -36.87
    assert -37.1 < chillan["lat"] < -36.7, (
        f"Chillán lat={chillan['lat']} no coincide con coord oficial ~-36.870"
    )
