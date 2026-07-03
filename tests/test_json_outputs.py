"""
Tests de los JSON públicos del sistema (docs/).

  - docs/fechas_disponibles_copernicus.json
  - docs/change_detection/change_results.json
"""

import json
import re
from datetime import datetime
from pathlib import Path

import pytest

from config_sentinel2 import VOLCANES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FECHAS_JSON = PROJECT_ROOT / "docs" / "fechas_disponibles_copernicus.json"
CHANGE_JSON = PROJECT_ROOT / "docs" / "change_detection" / "change_results.json"

FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ----------------------------- fechas_disponibles ---------------------------

@pytest.mark.skipif(not FECHAS_JSON.exists(), reason=f"{FECHAS_JSON.name} no presente")
def test_fechas_disponibles_es_json_valido():
    with open(FECHAS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)
    assert len(data) > 0


@pytest.mark.skipif(not FECHAS_JSON.exists(), reason="JSON no presente")
def test_fechas_disponibles_claves_son_volcanes_conocidos():
    """Toda clave debe corresponder a un volcán de VOLCANES."""
    with open(FECHAS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    desconocidos = [k for k in data.keys() if k not in VOLCANES]
    assert not desconocidos, (
        f"Claves no presentes en VOLCANES: {desconocidos[:5]}"
    )


@pytest.mark.skipif(not FECHAS_JSON.exists(), reason="JSON no presente")
def test_fechas_disponibles_orden_y_formato():
    """Cada lista debe estar ordenada ASC y con formato YYYY-MM-DD válido."""
    with open(FECHAS_JSON, encoding="utf-8") as f:
        data = json.load(f)

    for volcan, fechas in data.items():
        assert isinstance(fechas, list), f"{volcan} no es lista"
        # Formato
        for fecha in fechas:
            assert FECHA_RE.match(fecha), (
                f"{volcan}: fecha '{fecha}' no es YYYY-MM-DD"
            )
            # Parseable
            datetime.strptime(fecha, "%Y-%m-%d")
        # Orden ASC
        assert fechas == sorted(fechas), (
            f"{volcan}: lista de fechas no está ordenada ASC"
        )


# ----------------------------- change_results -------------------------------

CAMPOS_ESPERADOS_VOLCAN = {
    "estado",
    "z_score_estado",
    "nhi_estado",
    "mahalanobis_estado",
}


@pytest.mark.skipif(not CHANGE_JSON.exists(), reason=f"{CHANGE_JSON.name} no presente")
def test_change_results_es_json_valido():
    with open(CHANGE_JSON, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)
    # Estructura top-level esperada
    assert "volcanes" in data, "Falta clave 'volcanes' en change_results.json"
    assert "fecha_analisis" in data


@pytest.mark.skipif(not CHANGE_JSON.exists(), reason="JSON no presente")
def test_change_results_estructura_por_volcan():
    """Cada entrada de 'volcanes' debe tener los campos clave de estado."""
    with open(CHANGE_JSON, encoding="utf-8") as f:
        data = json.load(f)

    volcanes = data["volcanes"]
    assert isinstance(volcanes, dict)
    assert len(volcanes) > 0

    # Muestreamos los primeros 5 para mantener test rápido
    for nombre, entry in list(volcanes.items())[:5]:
        faltantes = CAMPOS_ESPERADOS_VOLCAN - set(entry.keys())
        assert not faltantes, f"{nombre}: faltan campos {faltantes}"
