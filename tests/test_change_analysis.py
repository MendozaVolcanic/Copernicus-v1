"""
Tests de las funciones core de change_analysis.py.

Smoke tests sobre PNGs sintéticos generados con PIL (100x100).
No requieren imágenes reales del proyecto.
"""

import numpy as np
import pytest

try:
    import scipy  # noqa: F401
    HAS_SCIPY = True
except Exception:
    HAS_SCIPY = False

from change_analysis import (
    calcular_nhi,
    calcular_nhi_landsat,
    calcular_vrp_estimado,
    calcular_vrp_real,
    filtro_ndsi_glaciar,
    calcular_mahalanobis,
)


# ----------------------------- NHI Sentinel-2 -------------------------------

def test_nhi_imagen_gris_sin_anomalia(tmp_png_thermal_uniforme):
    """
    Imagen 100% gris (R=G=B=30) → NHI_SWIR=0, brillo bajo: no hay hot pixels.
    """
    stats = calcular_nhi(str(tmp_png_thermal_uniforme))
    assert stats is not None
    assert stats["n_hot_pixels_nhi"] == 0
    assert stats["n_hot_pixels_nhi_strict"] == 0
    assert stats["sensor"] == "sentinel2"


def test_nhi_detecta_cluster_hot(tmp_png_thermal_con_hot):
    """
    PNG con cluster central R=240, G=90 → NHI_SWIR = (240-90)/(240+90) ≈ 0.45 > 0.30
    y brillo R/255 ≈ 0.94 > 0.35. Debe detectar hot pixels.
    """
    stats = calcular_nhi(str(tmp_png_thermal_con_hot))
    assert stats is not None
    assert stats["n_hot_pixels_nhi"] > 0, "Debió detectar hot pixels en cluster sintético"
    assert stats["nhi_max"] > 0.30
    assert stats["porcentaje_anomalia"] > 0


def test_nhi_landsat_funciona_con_umbrales_relajados(tmp_png_thermal_con_hot):
    """
    Landsat usa umbral NHI 0.25 (más permisivo que S2 0.30). El mismo cluster
    sintético debe detectarse también en modo Landsat.
    """
    stats = calcular_nhi_landsat(str(tmp_png_thermal_con_hot))
    assert stats is not None
    assert stats["sensor"] == "landsat"
    assert stats["umbral_nhi"] == 0.25
    assert stats["n_hot_pixels_nhi"] > 0


def test_nhi_input_inexistente_no_explota(tmp_path):
    """Path inválido debe devolver None, no levantar excepción."""
    stats = calcular_nhi(str(tmp_path / "no_existe.png"))
    assert stats is None


# ----------------------------- VRP ------------------------------------------

def test_vrp_uniforme_devuelve_low(tmp_png_thermal_uniforme):
    """Sin hot pixels → VRP = 0 MW y nivel Low."""
    res = calcular_vrp_estimado(str(tmp_png_thermal_uniforme))
    assert res is not None
    assert res["vrp_estimado_mw"] == 0.0
    assert res["nivel_termico"] == "Low"
    assert res["pixels_calculados"] == 0


def test_vrp_con_hot_pixels_es_positivo(tmp_png_thermal_con_hot):
    """Con cluster térmico sintético, VRP > 0 MW y pixels_calculados > 0."""
    res = calcular_vrp_estimado(str(tmp_png_thermal_con_hot))
    assert res is not None
    assert res["vrp_estimado_mw"] > 0.0, (
        f"Esperaba VRP>0 con cluster térmico, dio {res['vrp_estimado_mw']}"
    )
    assert res["pixels_calculados"] > 0


# ----------------------------- VRP CALIBRADO (Wooster 2003) ------------------

def test_vrp_real_path_inexistente_devuelve_none(tmp_path):
    """Path inválido → None, sin excepción."""
    res = calcular_vrp_real(str(tmp_path / "no_existe.npz"),
                            lat_volcan=-23.37, fecha_iso="2026-01-15")
    assert res is None


def test_vrp_real_sin_anomalia_es_cero(tmp_swir_raw_npz_frio):
    """SWIR_raw uniforme frío → no hay hot pixels → VRP = 0 MW, nivel Low."""
    res = calcular_vrp_real(
        str(tmp_swir_raw_npz_frio),
        lat_volcan=-23.37,        # Lascar
        fecha_iso="2026-01-15",
    )
    assert res is not None
    assert res["vrp_calibrado_mw"] == 0.0
    assert res["n_hot_pixels"] == 0
    assert res["nivel_termico"] == "Low"


def test_vrp_real_con_lava_es_positivo(tmp_swir_raw_npz_con_lava):
    """
    Cluster sintético con B12=0.85 reflectancia BOA → VRP > 0 W.
    Para 25 pixels × 400 m² × L_B12 ~ 0.85×84.86×cos(θ)/(π×d²) ≈ 22 W/m²/sr/µm
    → VRP ~ 25 × 18.9 × 400 × 22 ~ 4.16 MW (orden de magnitud Lascar).
    """
    res = calcular_vrp_real(
        str(tmp_swir_raw_npz_con_lava),
        lat_volcan=-23.37,        # Lascar
        fecha_iso="2026-01-15",   # verano austral → cos(θ) alto
    )
    assert res is not None
    assert res["vrp_calibrado_mw"] > 0.0
    assert res["n_hot_pixels"] == 25, f"Esperaba 25 hot pixels (5x5), dio {res['n_hot_pixels']}"
    # Sanity: debería estar en el rango 1-50 MW para estos valores sintéticos
    assert 0.5 < res["vrp_calibrado_mw"] < 100.0, (
        f"VRP fuera de rango esperado: {res['vrp_calibrado_mw']} MW"
    )
    assert res["nivel_termico"] in ("Low", "Moderate")
    assert res["theta_zenith_cos"] is not None
    assert 0.1 <= res["theta_zenith_cos"] <= 1.0


def test_vrp_real_es_lineal_en_area_pixel(tmp_swir_raw_npz_con_lava):
    """VRP_total escala linealmente con A_pixel (Landsat 900 m² vs S2 400 m²)."""
    res_s2 = calcular_vrp_real(str(tmp_swir_raw_npz_con_lava),
                                lat_volcan=-23.37, fecha_iso="2026-01-15",
                                area_pixel_m2=400.0)
    res_l8 = calcular_vrp_real(str(tmp_swir_raw_npz_con_lava),
                                lat_volcan=-23.37, fecha_iso="2026-01-15",
                                area_pixel_m2=900.0)
    ratio = res_l8["vrp_calibrado_mw"] / max(res_s2["vrp_calibrado_mw"], 1e-9)
    assert abs(ratio - 900.0 / 400.0) < 0.01


# ----------------------------- NDSI (filtro glaciar) -------------------------

def test_ndsi_excluye_parche_nieve(tmp_png_rgb_con_nieve, tmp_png_thermal_para_ndsi):
    """
    Parche blanco en RGB (alto B03) + B11 bajo en thermal → NDSI alto → enmascarado.
    La máscara devuelta es True donde NO hay nieve. El parche debe ser False.
    """
    mascara = filtro_ndsi_glaciar(
        str(tmp_png_rgb_con_nieve),
        str(tmp_png_thermal_para_ndsi),
    )
    assert mascara is not None
    assert mascara.shape == (100, 100)
    # En el centro del parche (30, 30) debe ser False (es nieve)
    assert mascara[30, 30] == False, (  # noqa: E712
        "El píxel del parche de nieve debió ser marcado como nieve (False)"
    )
    # Fuera del parche debe ser True (no es nieve)
    assert mascara[80, 80] == True, (  # noqa: E712
        "Fondo verde no debió ser marcado como nieve"
    )


# ----------------------------- Mahalanobis ----------------------------------

@pytest.mark.skipif(not HAS_SCIPY, reason="scipy no disponible")
def test_mahalanobis_stack_uniforme_no_detecta_anomalia():
    """
    Stack histórico idéntico a la imagen actual → distancia ~0 → NORMAL.
    """
    rng = np.random.default_rng(seed=42)
    base = rng.integers(50, 60, size=(100, 100, 3), dtype=np.uint8).astype(np.float32)

    # 5 imágenes históricas con ruido pequeño
    stack = np.stack([
        base + rng.normal(0, 1.0, base.shape).astype(np.float32)
        for _ in range(5)
    ])
    actual = base + rng.normal(0, 1.0, base.shape).astype(np.float32)

    res = calcular_mahalanobis(stack, actual)
    assert res is not None
    assert res["estado"] == "NORMAL", (
        f"Stack uniforme no debió disparar alerta, dio {res['estado']}"
    )


@pytest.mark.skipif(not HAS_SCIPY, reason="scipy no disponible")
def test_mahalanobis_input_invalido_devuelve_none():
    """Shapes inconsistentes → devuelve None (no excepción)."""
    stack = np.zeros((5, 100, 100, 3), dtype=np.float32)
    actual_mal = np.zeros((50, 50, 3), dtype=np.float32)
    res = calcular_mahalanobis(stack, actual_mal)
    assert res is None
