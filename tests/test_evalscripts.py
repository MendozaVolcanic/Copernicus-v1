"""
Tests de los evalscripts Sentinel-2.

Reglas críticas (CLAUDE.md):
  - EVALSCRIPT_RGB usa sRGB encoding (matchea Copernicus Browser)
  - EVALSCRIPT_THERMAL es LINEAL (sin sRGB; gamma rompe contraste térmico)
  - Ambos retornan 3 bandas
"""

import re

from config_sentinel2 import EVALSCRIPT_RGB, EVALSCRIPT_THERMAL, EVALSCRIPT_SWIR_B8A


def test_rgb_usa_highlight_compress():
    """RGB debe usar HighlightCompressVisualizer (matchea Copernicus Browser).

    El gain lineal anterior (sRGB(2.5*B0x)) clipeaba la nieve (refl>0.4) a blanco
    puro. HighlightCompress comprime los highlights sin clipear.
    """
    assert "HighlightCompressVisualizer" in EVALSCRIPT_RGB, (
        "EVALSCRIPT_RGB debe usar HighlightCompressVisualizer para no clipear la nieve"
    )


def test_rgb_no_usa_gain_lineal_que_clipea():
    """No debe quedar el patron viejo sRGB(2.5*...) que clipeaba los highlights."""
    assert "2.5 * sample.B04" not in EVALSCRIPT_RGB and "2.5*sample.B04" not in EVALSCRIPT_RGB, (
        "EVALSCRIPT_RGB no debe usar el gain lineal 2.5x que clipeaba la nieve a blanco"
    )


def test_rgb_highlight_maxval_04():
    """maxVal=0.4 es el punto donde empieza la compresion (estandar Copernicus)."""
    assert "0.4" in EVALSCRIPT_RGB


def test_thermal_NO_define_srgb():
    """Thermal debe ser LINEAL: sin función sRGB y sin llamadas a sRGB()."""
    assert "function sRGB" not in EVALSCRIPT_THERMAL, (
        "EVALSCRIPT_THERMAL no debe definir sRGB (rompe contraste térmico)"
    )
    cuerpo = EVALSCRIPT_THERMAL.split("evaluatePixel")[-1]
    assert "sRGB(" not in cuerpo, (
        "EVALSCRIPT_THERMAL no debe aplicar sRGB() en evaluatePixel"
    )


def test_rgb_output_3_bandas():
    assert "bands: 3" in EVALSCRIPT_RGB


def test_thermal_output_3_bandas():
    assert "bands: 3" in EVALSCRIPT_THERMAL


def test_rgb_input_bands_correctas():
    """RGB usa B04 (rojo), B03 (verde), B02 (azul)."""
    for banda in ("B04", "B03", "B02"):
        assert banda in EVALSCRIPT_RGB, f"RGB debe incluir banda {banda}"


def test_thermal_input_bands_correctas():
    """ThermalFalseColor usa B12 (SWIR2), B11 (SWIR1), B04 (Red)."""
    for banda in ("B12", "B11", "B04"):
        assert banda in EVALSCRIPT_THERMAL, f"Thermal debe incluir banda {banda}"


def test_thermal_orden_b12_b11_b04():
    """El return de thermal debe ser [B12, B11, B04] en ese orden (R, G, B)."""
    # Buscar el return en evaluatePixel
    m = re.search(r"return\s*\[([^\]]+)\]", EVALSCRIPT_THERMAL)
    assert m, "No se encontró return en evalscript thermal"
    expr = m.group(1)
    idx_b12 = expr.find("B12")
    idx_b11 = expr.find("B11")
    idx_b04 = expr.find("B04")
    assert -1 < idx_b12 < idx_b11 < idx_b04, (
        f"Orden incorrecto en thermal return: {expr.strip()}"
    )


# =====================================================================
# SWIR_B8A: 4o composite. SWIR2/SWIR1/NIR-angosto (B12/B11/B8A), todos a
# 20 m nativo (sin resampling). LINEAL como el thermal (gamma rompe el
# contraste de la anomalia termica roja).
# =====================================================================

def test_swir_b8a_NO_define_srgb():
    """SWIR_B8A debe ser LINEAL: sin función sRGB y sin llamadas a sRGB()."""
    assert "function sRGB" not in EVALSCRIPT_SWIR_B8A, (
        "EVALSCRIPT_SWIR_B8A no debe definir sRGB (rompe contraste térmico)"
    )
    cuerpo = EVALSCRIPT_SWIR_B8A.split("evaluatePixel")[-1]
    assert "sRGB(" not in cuerpo, (
        "EVALSCRIPT_SWIR_B8A no debe aplicar sRGB() en evaluatePixel"
    )


def test_swir_b8a_output_3_bandas():
    assert "bands: 3" in EVALSCRIPT_SWIR_B8A


def test_swir_b8a_input_bands_correctas():
    """SWIR_B8A usa B12 (SWIR2), B11 (SWIR1), B8A (NIR-angosto)."""
    for banda in ("B12", "B11", "B8A"):
        assert banda in EVALSCRIPT_SWIR_B8A, f"SWIR_B8A debe incluir banda {banda}"


def test_swir_b8a_NO_usa_b04():
    """SWIR_B8A reemplaza B04 por B8A: no debe quedar B04 residual del copy/paste."""
    assert "B04" not in EVALSCRIPT_SWIR_B8A, (
        "EVALSCRIPT_SWIR_B8A no debe usar B04 (la idea es B8A a 20m nativo)"
    )


def test_swir_b8a_orden_b12_b11_b8a():
    """El return de SWIR_B8A debe ser [B12, B11, B8A] en ese orden (R, G, B)."""
    m = re.search(r"return\s*\[([^\]]+)\]", EVALSCRIPT_SWIR_B8A)
    assert m, "No se encontró return en evalscript SWIR_B8A"
    expr = m.group(1)
    idx_b12 = expr.find("B12")
    idx_b11 = expr.find("B11")
    idx_b8a = expr.find("B8A")
    assert -1 < idx_b12 < idx_b11 < idx_b8a, (
        f"Orden incorrecto en SWIR_B8A return: {expr.strip()}"
    )


def test_swir_b8a_registrado_en_evalscripts():
    """SWIR_B8A debe estar en el dict EVALSCRIPTS con su key."""
    from config_sentinel2 import EVALSCRIPTS
    assert "SWIR_B8A" in EVALSCRIPTS, "Falta registrar 'SWIR_B8A' en EVALSCRIPTS"
    assert EVALSCRIPTS["SWIR_B8A"] is EVALSCRIPT_SWIR_B8A
