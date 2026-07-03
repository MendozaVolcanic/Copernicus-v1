"""
Fixtures comunes para la suite de tests Copernicus-v1.

Provee:
    - PNG sintéticos (lineal y sRGB) de 100x100
    - Config de volcán dummy
    - PROJECT_ROOT inyectado a sys.path
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

# ---------------------------------------------------------------
# Inyectar la raíz del repo en sys.path para que `import config_sentinel2`
# y `import change_analysis` funcionen sin instalar el proyecto.
# ---------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Credenciales dummy para que `config_sentinel2.validate_credentials()` no aborte
# si algún módulo lo invoca al importar.
os.environ.setdefault("SH_CLIENT_ID", "test-client-id")
os.environ.setdefault("SH_CLIENT_SECRET", "test-client-secret")


# ---------------------------------------------------------------
# PNGs sintéticos
# ---------------------------------------------------------------
def _save_png(arr: np.ndarray, path: Path) -> Path:
    Image.fromarray(arr.astype(np.uint8)).save(path)
    return path


@pytest.fixture
def tmp_png_lineal(tmp_path: Path) -> Path:
    """PNG 100x100 lineal gris medio (sin sRGB), 3 canales."""
    arr = np.full((100, 100, 3), 128, dtype=np.uint8)
    return _save_png(arr, tmp_path / "lineal.png")


@pytest.fixture
def tmp_png_srgb(tmp_path: Path) -> Path:
    """
    PNG 100x100 simulando RGB con sRGB encoding (verde-tierra).
    Útil como input visible en filtros NDSI.
    """
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    arr[:, :, 0] = 90    # R bajo
    arr[:, :, 1] = 140   # G medio (vegetación)
    arr[:, :, 2] = 70    # B bajo
    return _save_png(arr, tmp_path / "srgb.png")


@pytest.fixture
def tmp_png_thermal_uniforme(tmp_path: Path) -> Path:
    """Thermal lineal uniforme oscuro: sin anomalía térmica."""
    arr = np.full((100, 100, 3), 30, dtype=np.uint8)
    return _save_png(arr, tmp_path / "thermal_uniforme.png")


@pytest.fixture
def tmp_png_thermal_con_hot(tmp_path: Path) -> Path:
    """
    Thermal lineal con un cluster central de pixeles 'hot':
    R (B12) muy alto, G (B11) medio, B (B04) bajo → NHI_SWIR alto.
    """
    arr = np.full((100, 100, 3), 30, dtype=np.uint8)
    # Cluster 8x8 con SWIR2 saturado y SWIR1 medio
    arr[46:54, 46:54, 0] = 240  # R = B12 muy alto
    arr[46:54, 46:54, 1] = 90   # G = B11 medio
    arr[46:54, 46:54, 2] = 20   # B = B04 bajo
    return _save_png(arr, tmp_path / "thermal_hot.png")


@pytest.fixture
def tmp_png_rgb_con_nieve(tmp_path: Path) -> Path:
    """RGB con un parche blanco (nieve) sobre fondo verde."""
    arr = np.zeros((100, 100, 3), dtype=np.uint8)
    arr[:, :, 0] = 60    # R bajo (vegetación)
    arr[:, :, 1] = 130   # G medio
    arr[:, :, 2] = 50    # B bajo
    # Parche de nieve (alto en visibles)
    arr[20:60, 20:60, :] = 245
    return _save_png(arr, tmp_path / "rgb_nieve.png")


@pytest.fixture
def tmp_png_thermal_para_ndsi(tmp_path: Path) -> Path:
    """
    Thermal lineal: el parche que en el RGB es 'nieve' aquí tiene B11 bajo
    (la nieve es muy reflectiva en visible pero ABSORBE en SWIR1 → B11 bajo).
    Esto debería dar NDSI > 0.4 → píxel marcado como nieve.
    """
    arr = np.full((100, 100, 3), 60, dtype=np.uint8)
    # Sobre el parche, canal G (B11) muy bajo
    arr[20:60, 20:60, 1] = 10
    return _save_png(arr, tmp_path / "thermal_ndsi.png")


# ---------------------------------------------------------------
# Config volcán dummy
# ---------------------------------------------------------------
@pytest.fixture
def tmp_swir_raw_npz_frio(tmp_path: Path) -> Path:
    """
    .npz SWIR_raw (B11, B12, dataMask) 100x100 SIN anomalía térmica.
    Reflectancia BOA típica de roca volcánica fría: B11~0.20, B12~0.18.
    NHI = (B12-B11)/(B12+B11) ≈ -0.05 → ningún hot pixel.
    """
    out = tmp_path / "swir_raw_frio.npz"
    b11 = np.full((100, 100), 0.20, dtype=np.float32)
    b12 = np.full((100, 100), 0.18, dtype=np.float32)
    data_mask = np.ones((100, 100), dtype=np.uint8)
    np.savez_compressed(out, B11=b11, B12=b12, dataMask=data_mask)
    return out


@pytest.fixture
def tmp_swir_raw_npz_con_lava(tmp_path: Path) -> Path:
    """
    .npz SWIR_raw con cluster 5x5 caliente (B12 alto, B11 medio).
    Lava expuesta a >800K: B12 saturado a ~0.85, B11 ~0.35
    → NHI = (0.85-0.35)/(0.85+0.35) ≈ 0.42 > 0.30 → hot pixel.
    Fondo frío B11=B12=0.18.
    """
    out = tmp_path / "swir_raw_lava.npz"
    b11 = np.full((100, 100), 0.18, dtype=np.float32)
    b12 = np.full((100, 100), 0.18, dtype=np.float32)
    # Cluster 5x5 caliente
    b11[47:52, 47:52] = 0.35
    b12[47:52, 47:52] = 0.85
    data_mask = np.ones((100, 100), dtype=np.uint8)
    np.savez_compressed(out, B11=b11, B12=b12, dataMask=data_mask)
    return out


@pytest.fixture
def volcan_test() -> dict:
    return {
        "lat": -39.42,
        "lon": -71.93,
        "buffer_km": 3.0,
        "id": "999000",
        "zona": "Sur",
        "activo": True,
    }
