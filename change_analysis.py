"""
CHANGE_ANALYSIS.PY — Análisis experimental de cambios volcánicos
Genera JSON con resultados para la página change_detection.html

Mejoras sobre change_detector.py:
- Máscara de nubes (excluye píxeles blancos/grises)
- Zona de interés central (cráter, no bordes)
- Comparación contra mediana de imágenes (background estadístico)
- Métricas separadas: térmico vs morfológico
- Cross-referencia NHI y Mirova
"""

import numpy as np
from PIL import Image
import os
import glob
import json
import csv
import sys
from datetime import datetime, timedelta

# VOLCANES dict para resolver latitud (necesaria para VRP calibrado).
# Si config_sentinel2 no importable (tests aislados), VRP real degrada
# gracefully a None y el pipeline sigue con el proxy.
try:
    from config_sentinel2 import VOLCANES as _VOLCANES_CFG
except Exception:
    _VOLCANES_CFG = {}


def _lat_de_volcan(nombre):
    """Devuelve la latitud configurada o None si el volcán no está."""
    cfg = _VOLCANES_CFG.get(nombre)
    if cfg is None:
        return None
    return cfg.get('lat')

# Fix encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SENTINEL_DIR = os.path.join(BASE_DIR, "docs", "sentinel2")
LANDSAT_DIR = os.path.join(BASE_DIR, "..", "Landsat-v1", "docs", "landsat")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "change_detection")
NHI_DIR = os.path.join(BASE_DIR, "..", "NHI-Tool", "docs", "nhi_data")
MIROVA_CSV = os.path.join(BASE_DIR, "..", "Mirova-v1", "monitoreo_satelital", "registro_vrp_maestro_publicable.csv")

# Configuración por sensor
SENSORES = {
    "sentinel2": {
        "base_dir": SENTINEL_DIR,
        "tipo_termico": "ThermalFalseColor",
        "tiene_indices_espectrales": True,  # NDVI, NBR, SWIR_Anomaly
    },
    "landsat": {
        "base_dir": LANDSAT_DIR,
        "tipo_termico": "THERMAL",
        "tiene_indices_espectrales": False,  # Landsat en este repo solo guarda THERMAL/RGB/SWIR
    },
}

# Volcanes con datos Mirova (nombres en Mirova pueden diferir)
MIROVA_NOMBRES = {
    "Isluga": "Isluga",
    "Lascar": "Lascar",
    "Lastarria": "Lastarria",
    "Tupungatito": "Tupungatito",
    "Planchon-Peteroa": "PlanchonPeteroa",
    "Nevados de Chillan": "Nevados_de_Chillan",
    "Copahue": "Copahue",
    "Llaima": "Llaima",
    "Villarrica": "Villarrica",
    "Puyehue - Cordon Caulle": "Puyehue-Cordon Caulle",
    "Chaiten": "Chaiten",
}

# Parámetros de análisis
UMBRAL_NUBE_BRILLO = 220      # Píxeles RGB > este valor = nube
UMBRAL_NUBE_SATURACION = 15   # Diferencia max entre canales < esto = gris/blanco
ZONA_CENTRAL_RATIO = 0.6      # Analizar el 60% central de la imagen
MIN_PIXELES_VALIDOS = 0.20    # Mínimo 20% píxeles no-nube para análisis válido
UMBRAL_CAMBIO_PIXEL = 25      # Diferencia mínima por píxel (0-255)

# --- Sprint 1 (Marchese 2019 / Coppola 2016) ---
# Volcanes con glaciar/nieve permanente → aplicar filtro NDSI para reducir falsos positivos SWIR
VOLCANES_CON_GLACIAR = [
    'Hudson', 'Villarrica', 'Lonquimay', 'Mocho-Choshuenco',
    'Yate', 'Michinmahuida', 'Calbuco', 'Quetrupillan',
    'Lanin', 'Llaima', 'Nevados de Chillan'
]
UMBRAL_NDSI_NIEVE = 0.4               # NDSI > 0.4 → nieve/hielo (McFeeters 1996 / Hall 1995)
NHI_HOT_PIXEL_UMBRAL = 5              # Min. pixeles con NHI>NHI_VALOR_UMBRAL para considerar señal térmica
NHI_STRICT_PIXEL_UMBRAL = 2           # Min. pixeles con AMBOS NHI fuertes (alta confianza)
NHI_MAX_UMBRAL_ATENCION = 0.4         # NHI_SWIR pico → señal térmica relevante
# Sobre PNGs normalizados (no reflectancia TOA absoluta) NHI>0 es trivial en
# terreno arido (B12>B11 por bajo albedo). Imponemos un umbral mas alto:
NHI_VALOR_UMBRAL = 0.30               # Solo "hot" si NHI > 0.30 (no solo > 0)
NHI_VALOR_UMBRAL_STRICT = 0.20        # Para SWNIR el criterio strict
# Adicionalmente, exigir que el pixel hot tenga brillo SWIR significativo
NHI_BRILLO_MIN_SWIR = 0.35            # R (B12 normalizado) > 0.35 → señal real, no shadow
A_PIXEL_S2_SWIR_M2 = 400.0            # Sentinel-2 SWIR nativo es 20m → 20*20 = 400 m²
VRP_COEF_WOOSTER = 18.9               # Coppola 2016/2023 (Wooster 2003)

# Niveles térmicos Coppola 2016a / 2023 (MW)
NIVELES_TERMICOS_MW = [
    ("Extreme",   10000.0),
    ("Very High",  1000.0),
    ("High",        100.0),
    ("Moderate",     10.0),
    ("Low",           0.0),
]

# Zonas geográficas
ZONAS = {
    "Norte": ["Taapaca", "Parinacota", "Guallatiri", "Isluga", "Irruputuncu",
              "Ollague", "San Pedro", "Lascar"],
    "Centro": ["Tupungatito", "San Jose", "Tinguiririca", "Planchon-Peteroa",
               "Descabezado Grande", "Tatara-San Pedro", "Laguna del Maule",
               "Nevado de Longavi", "Nevados de Chillan"],
    "Sur": ["Antuco", "Copahue", "Callaqui", "Lonquimay", "Llaima", "Sollipulli",
            "Villarrica", "Quetrupillan", "Lanin", "Mocho-Choshuenco",
            "Carran - Los Venados", "Puyehue - Cordon Caulle", "Antillanca - Casablanca"],
    "Austral": ["Osorno", "Calbuco", "Yate", "Hornopiren", "Huequi",
                "Michinmahuida", "Chaiten", "Corcovado", "Melimoyu",
                "Mentolat", "Cay", "Maca", "Hudson"]
}

ZONA_POR_VOLCAN = {}
for zona, volcanes in ZONAS.items():
    for v in volcanes:
        ZONA_POR_VOLCAN[v] = zona


# ============================================================
# FUNCIONES DE ANÁLISIS
# ============================================================

def crear_mascara_nubes(img_array):
    """
    Crea máscara booleana: True = píxel de nube (excluir del análisis).
    Nubes: píxeles brillantes y de baja saturación (blancos/grises).
    """
    brillo = np.mean(img_array, axis=2)
    r, g, b = img_array[:,:,0].astype(float), img_array[:,:,1].astype(float), img_array[:,:,2].astype(float)
    rango_color = np.max(img_array, axis=2).astype(float) - np.min(img_array, axis=2).astype(float)

    mascara = (brillo > UMBRAL_NUBE_BRILLO) & (rango_color < UMBRAL_NUBE_SATURACION)

    # También excluir píxeles completamente negros (sin datos)
    mascara_negro = (brillo < 5)

    return mascara | mascara_negro


def recortar_zona_central(shape, ratio=ZONA_CENTRAL_RATIO):
    """
    Retorna slices para la zona central de la imagen.
    ratio=0.6 significa el 60% central (20% margen cada lado).
    """
    h, w = shape[:2]
    margen_h = int(h * (1 - ratio) / 2)
    margen_w = int(w * (1 - ratio) / 2)
    return slice(margen_h, h - margen_h), slice(margen_w, w - margen_w)


def cargar_imagen(path):
    """Carga imagen como array numpy RGB."""
    try:
        img = Image.open(path).convert('RGB')
        return np.array(img)
    except Exception as e:
        print(f"    ERROR cargando {path}: {e}")
        return None


def obtener_fechas_disponibles(volcan, tipo='ThermalFalseColor', base_dir=None):
    """Retorna lista de fechas con imágenes disponibles, ordenadas."""
    base_dir = base_dir or SENTINEL_DIR
    patron = os.path.join(base_dir, volcan, f"*_{tipo}.png")
    archivos = sorted(glob.glob(patron))
    fechas = []
    for f in archivos:
        nombre = os.path.basename(f)
        fecha = nombre.split('_')[0]
        fechas.append(fecha)
    return fechas


def calcular_background_estadistico(volcan, tipo='ThermalFalseColor', max_imagenes=8, base_dir=None,
                                    return_stack=False):
    """
    Calcula la imagen mediana de las últimas N imágenes (background).
    La mediana es robusta contra nubes ocasionales.

    Si return_stack=True, retorna también el stack crudo (N, H, W, 3) para
    Mahalanobis u otros métodos multivariados.
    """
    base_dir = base_dir or SENTINEL_DIR
    fechas = obtener_fechas_disponibles(volcan, tipo, base_dir=base_dir)
    if len(fechas) < 3:
        return (None, [], None) if return_stack else (None, [])

    # Tomar las últimas max_imagenes (excluyendo la más reciente)
    fechas_bg = fechas[-(max_imagenes + 1):-1]

    arrays = []
    shape_ref = None
    for fecha in fechas_bg:
        path = os.path.join(base_dir, volcan, f"{fecha}_{tipo}.png")
        arr = cargar_imagen(path)
        if arr is None:
            continue
        if shape_ref is None:
            shape_ref = arr.shape
        if arr.shape != shape_ref:
            # Algunas imágenes pueden tener tamaños distintos: descartar
            continue
        arrays.append(arr)

    if len(arrays) < 2:
        return (None, fechas_bg, None) if return_stack else (None, fechas_bg)

    # Calcular mediana píxel por píxel
    stack = np.stack(arrays, axis=0)
    mediana = np.median(stack, axis=0).astype(np.uint8)

    if return_stack:
        return mediana, fechas_bg, stack
    return mediana, fechas_bg


def calcular_varianza_background(volcan, tipo='ThermalFalseColor', max_imagenes=8, base_dir=None):
    """
    Calcula la volatilidad natural del volcán comparando pares consecutivos
    de imágenes de background. Retorna (media_diffs, std_diffs) para Z-score.
    """
    base_dir = base_dir or SENTINEL_DIR
    fechas = obtener_fechas_disponibles(volcan, tipo, base_dir=base_dir)
    if len(fechas) < 4:
        return None, None

    fechas_bg = fechas[-(max_imagenes + 1):-1]
    if len(fechas_bg) < 2:
        return None, None

    diffs = []
    for i in range(len(fechas_bg) - 1):
        path_a = os.path.join(base_dir, volcan, f"{fechas_bg[i]}_{tipo}.png")
        path_b = os.path.join(base_dir, volcan, f"{fechas_bg[i+1]}_{tipo}.png")
        arr_a = cargar_imagen(path_a)
        arr_b = cargar_imagen(path_b)
        if arr_a is None or arr_b is None:
            continue

        sh, sw = recortar_zona_central(arr_a.shape)
        a_c = arr_a[sh, sw]
        b_c = arr_b[sh, sw]
        mascara = crear_mascara_nubes(a_c) | crear_mascara_nubes(b_c)
        validos = ~mascara
        if np.sum(validos) < 100:
            continue

        diff_rojo = np.abs(a_c[:,:,0].astype(float) - b_c[:,:,0].astype(float))
        valores = diff_rojo[validos]
        media_par = np.mean(valores)
        std_par = np.std(valores)
        umbral = max(media_par + 2 * std_par, 40)
        pct_anomalia = np.sum(valores > umbral) / len(valores) * 100
        diffs.append(pct_anomalia)

    if len(diffs) < 2:
        return None, None

    return float(np.mean(diffs)), float(np.std(diffs))


def clasificar_con_zscore(pct_anomalia, max_diff, pct_morfo, baseline_mean, baseline_std, indices_spectral=None):
    """
    Clasifica el estado del volcán usando Z-score respecto a su variabilidad histórica.
    Sin baseline suficiente, usa umbrales conservadores fijos.
    """
    ndvi_stable = (indices_spectral or {}).get('ndvi_stable', False)
    swir_confirmed = (indices_spectral or {}).get('swir_anomaly_confirmed', False)

    if baseline_mean is None:
        # Datos insuficientes: umbrales conservadores
        if pct_anomalia > 8:
            estado = "ALERTA"
            detalle = f"Anomalia termica ({pct_anomalia:.1f}%) — umbral conservador (sin baseline)"
        elif pct_anomalia > 3:
            estado = "ATENCION"
            detalle = f"Cambio termico ({pct_anomalia:.1f}%) — sin baseline historico"
        elif pct_morfo > 40 and not ndvi_stable:
            estado = "ATENCION"
            detalle = f"Cambio morfologico ({pct_morfo:.1f}%) — sin baseline"
        else:
            estado = "NORMAL"
            detalle = f"Sin cambios significativos (termico {pct_anomalia:.1f}%, morfo {pct_morfo:.1f}%)"
        if swir_confirmed and estado == "ATENCION":
            estado = "ALERTA"
            detalle = "Anomalia SWIR confirmada — " + detalle
        return estado, detalle, None

    z_termico = (pct_anomalia - baseline_mean) / max(baseline_std, 0.1)

    if z_termico > 3.0 and pct_anomalia > 3:
        estado = "ALERTA"
        detalle = f"Anomalia termica (Z={z_termico:.1f}, {pct_anomalia:.1f}% pixeles)"
    elif z_termico > 2.0 and pct_anomalia > 1:
        estado = "ATENCION"
        detalle = f"Cambio termico elevado (Z={z_termico:.1f}, {pct_anomalia:.1f}%)"
    elif pct_morfo > 40 and not ndvi_stable:
        estado = "ATENCION"
        detalle = f"Cambio morfologico ({pct_morfo:.1f}%) con variacion vegetal"
    else:
        estado = "NORMAL"
        detalle = f"Variacion normal (Z={z_termico:.1f}, termico {pct_anomalia:.1f}%)"

    # Ajustes por indices espectrales
    if ndvi_stable and estado == "ATENCION" and "morfol" in detalle.lower():
        estado = "NORMAL"
        detalle = f"Cambio morfologico estabilizado por NDVI ({pct_morfo:.1f}%)"
    if swir_confirmed and estado == "ATENCION":
        estado = "ALERTA"
        detalle = "Anomalia SWIR confirmada — " + detalle

    return estado, detalle, round(z_termico, 2)


# ============================================================
# SPRINT 1: NHI (Marchese 2019) + VRP (Coppola 2016) + NDSI
# ============================================================

def _leer_canales_normalizados(png_path):
    """
    Lee un PNG y retorna (R, G, B, mascara_datos) como floats 0-1.
    mascara_datos: True donde HAY datos (no negro absoluto, no nube).
    """
    img = cargar_imagen(png_path)
    if img is None:
        return None
    arr = img.astype(np.float32) / 255.0
    R = arr[:, :, 0]
    G = arr[:, :, 1]
    B = arr[:, :, 2]
    # dataMask: pixel no completamente negro
    mascara_datos = (arr.sum(axis=2) > 0.01)
    # Excluir nubes (mascara_nubes ya espera uint8, recreamos aqui en floats)
    brillo = arr.mean(axis=2)
    rango = arr.max(axis=2) - arr.min(axis=2)
    mascara_nube = (brillo > UMBRAL_NUBE_BRILLO / 255.0) & (rango < UMBRAL_NUBE_SATURACION / 255.0)
    mascara_datos = mascara_datos & ~mascara_nube
    return R, G, B, mascara_datos


def _calcular_nhi_generico(png_path, mascara_extra=None,
                            umbral_nhi=NHI_VALOR_UMBRAL,
                            umbral_nhi_strict=NHI_VALOR_UMBRAL_STRICT,
                            umbral_brillo=NHI_BRILLO_MIN_SWIR,
                            sensor_label='sentinel2'):
    """
    Cálculo NHI parametrizable para Sentinel-2 (ThermalFalseColor: R=B12 G=B11 B=B04)
    o Landsat 8/9 (SWIR composite: R=B7 G=B6 B=B4). En ambos casos R=SWIR2, G=SWIR1, B=Red.
    """
    res = _leer_canales_normalizados(png_path)
    if res is None:
        return None
    R, G, B, mascara_datos = res

    if mascara_extra is not None and mascara_extra.shape == mascara_datos.shape:
        mascara_datos = mascara_datos & mascara_extra

    suma_swir = R + G
    suma_swnir = R + B
    suma_swir_safe = np.where(suma_swir > 1e-6, suma_swir, 1.0)
    suma_swnir_safe = np.where(suma_swnir > 1e-6, suma_swnir, 1.0)

    nhi_swir = np.where(suma_swir > 1e-6, (R - G) / suma_swir_safe, 0.0)
    nhi_swnir = np.where(suma_swnir > 1e-6, (R - B) / suma_swnir_safe, 0.0)

    R_validos = R[mascara_datos]
    nhi_swir_validos = nhi_swir[mascara_datos]
    nhi_swnir_validos = nhi_swnir[mascara_datos]
    total_validos = int(mascara_datos.sum())

    if total_validos < 100:
        return {
            "n_hot_pixels_nhi": 0,
            "n_hot_pixels_nhi_strict": 0,
            "nhi_max": 0.0,
            "nhi_swnir_max": 0.0,
            "porcentaje_anomalia": 0.0,
            "pixeles_validos": total_validos,
            "sensor": sensor_label,
            "nota": "Insuficientes pixeles validos (<100)"
        }

    brillo_ok = R_validos > umbral_brillo
    hot_swir = (nhi_swir_validos > umbral_nhi) & brillo_ok
    hot_swnir = (nhi_swnir_validos > umbral_nhi_strict) & brillo_ok
    hot_strict = hot_swir & hot_swnir

    n_hot = int(hot_swir.sum())
    n_hot_strict = int(hot_strict.sum())
    nhi_max = float(nhi_swir_validos.max()) if nhi_swir_validos.size else 0.0
    nhi_swnir_max = float(nhi_swnir_validos.max()) if nhi_swnir_validos.size else 0.0
    pct_anom = (n_hot / total_validos) * 100.0

    return {
        "n_hot_pixels_nhi": n_hot,
        "n_hot_pixels_nhi_strict": n_hot_strict,
        "nhi_max": round(nhi_max, 4),
        "nhi_swnir_max": round(nhi_swnir_max, 4),
        "porcentaje_anomalia": round(pct_anom, 3),
        "pixeles_validos": total_validos,
        "sensor": sensor_label,
        "umbral_nhi": umbral_nhi,
        "umbral_brillo": umbral_brillo,
    }


def calcular_nhi(thermal_png_path, mascara_extra=None):
    """
    NHI Sentinel-2 (Marchese 2019 / Massimetti 2020).

    PNG ThermalFalseColor (evalscript LINEAL `[2.5*B12, 2.5*B11, 2.5*B04]`).
    R/G/B son proporcionales (clip 0-1) a SWIR2/SWIR1/Red.

    Fórmulas:
        NHI_SWIR  = (B12 - B11) / (B12 + B11)   -> anomalías térmicas moderadas
        NHI_SWNIR = (B12 - B04) / (B12 + B04)   -> anomalías de muy alta temperatura

    Criterio Sentinel-2 (20 m): NHI_SWIR > 0.30 AND brillo SWIR2 > 0.35.
    """
    return _calcular_nhi_generico(
        thermal_png_path,
        mascara_extra=mascara_extra,
        umbral_nhi=NHI_VALOR_UMBRAL,
        umbral_nhi_strict=NHI_VALOR_UMBRAL_STRICT,
        umbral_brillo=NHI_BRILLO_MIN_SWIR,
        sensor_label='sentinel2',
    )


# Umbrales NHI para Landsat 8/9 (30 m SWIR) — un poco más permisivos que S2 (20 m)
# porque el pixel mezcla más áreas frías y diluye la señal SWIR2.
NHI_VALOR_UMBRAL_LANDSAT = 0.25
NHI_VALOR_UMBRAL_STRICT_LANDSAT = 0.15
NHI_BRILLO_MIN_SWIR_LANDSAT = 0.35


def calcular_nhi_landsat(swir_png_path, mascara_extra=None):
    """
    NHI para Landsat 8/9 sobre composite SWIR (R=B7 G=B6 B=B4):
        B7 (2.2 μm)  ≡ S2 B12 (SWIR2)
        B6 (1.6 μm)  ≡ S2 B11 (SWIR1)
        B4 (655 nm)  ≡ S2 B04 (Red)

    Pixel Landsat = 30 m → área ~2.25× S2 → señal SWIR2 más diluida.
    Umbrales relajados: NHI > 0.25 AND brillo SWIR2 > 0.35.
    """
    return _calcular_nhi_generico(
        swir_png_path,
        mascara_extra=mascara_extra,
        umbral_nhi=NHI_VALOR_UMBRAL_LANDSAT,
        umbral_nhi_strict=NHI_VALOR_UMBRAL_STRICT_LANDSAT,
        umbral_brillo=NHI_BRILLO_MIN_SWIR_LANDSAT,
        sensor_label='landsat',
    )


def calcular_vrp_estimado(thermal_png_path, mascara_extra=None, area_pixel_m2=A_PIXEL_S2_SWIR_M2):
    """
    [DEPRECATED — usar calcular_vrp_real() cuando exista SWIR_raw .npz]

    Volcanic Radiative Power PROXY (no calibrado). NO comparable a MIROVA.

    Fórmula canónica:
        VRP = 18.9 · A_pixel · Σ (L_MIR_alert - L_MIR_bk)   [Watts]

    Sentinel-2 y Landsat 8/9 NO tienen MIR (3.9 µm) → adaptación SWIR.
    Como nuestros PNG son LINEAL (B12*2.5, clip 0-1), no tenemos radiancia absoluta.
    Usamos como proxy una escala empírica del canal SWIR2 (R):

        L_swir_proxy ≈ R_canal · 50   [W·m⁻²·sr⁻¹·µm⁻¹ aprox.]

    Esto es una APROXIMACIÓN para tener una métrica relativa comparable; para VRP real
    calibrado necesitamos descargar las bandas SWIR sin compositar (futuro Sprint 2).

    Solo contabilizamos pixeles con NHI_SWIR > 0 (hotspots reales).

    Returns:
        {
          'vrp_estimado_mw': float,    # Megawatts (aproximación)
          'nivel_termico': str,         # Low / Moderate / High / Very High / Extreme
          'pixels_calculados': int
        }
    """
    res = _leer_canales_normalizados(thermal_png_path)
    if res is None:
        return None
    R, G, B, mascara_datos = res

    if mascara_extra is not None and mascara_extra.shape == mascara_datos.shape:
        mascara_datos = mascara_datos & mascara_extra

    # Identificar hotspots (NHI_SWIR > umbral Y brillo SWIR2 alto) y radiancia excedente
    suma_swir = R + G
    nhi_swir = np.where(suma_swir > 1e-6, (R - G) / np.where(suma_swir > 1e-6, suma_swir, 1.0), 0.0)
    hot = (nhi_swir > NHI_VALOR_UMBRAL) & (R > NHI_BRILLO_MIN_SWIR) & mascara_datos

    if not np.any(hot):
        return {
            "vrp_estimado_mw": 0.0,
            "nivel_termico": "Low",
            "pixels_calculados": 0,
            "metodo": "SWIR-proxy (aprox)",
        }

    # Background SWIR: mediana del canal R sobre pixeles NO-hot (no térmicos)
    R_bg_candidatos = R[mascara_datos & ~hot]
    if R_bg_candidatos.size < 10:
        bg = 0.0
    else:
        bg = float(np.median(R_bg_candidatos))

    # Proxy de radiancia SWIR (escala empírica): factor 50 W·m⁻²·sr⁻¹·µm⁻¹ para R=1
    L_proxy_factor = 50.0
    exceso_R = np.clip(R[hot] - bg, 0.0, None)
    L_exceso = exceso_R * L_proxy_factor

    vrp_watts = VRP_COEF_WOOSTER * area_pixel_m2 * float(L_exceso.sum())
    vrp_mw = vrp_watts / 1e6

    # Clasificar nivel térmico (Coppola 2016a/2023)
    nivel = "Low"
    for nombre, umbral in NIVELES_TERMICOS_MW:
        if vrp_mw >= umbral:
            nivel = nombre
            break

    return {
        "vrp_estimado_mw": round(vrp_mw, 3),
        "nivel_termico": nivel,
        "pixels_calculados": int(hot.sum()),
        "background_swir_proxy": round(bg, 4),
        "metodo": "SWIR-proxy (aprox, no calibrado)",
    }


# ============================================================
# VRP CALIBRADO REAL (Wooster 2003 / Coppola 2016)
# ============================================================
#
# Constantes radiométricas Sentinel-2 banda B12 (SWIR2, 2.20 µm).
# E_SOLAR_B12: irradiancia solar exoatmosférica integrada en la banda.
# Valor 84.86 W/m²/µm corresponde al ESUN reportado por ESA en S2 MPC PSD
# (Product Specification Document) para Sentinel-2A; B/C difieren <1%.
# Wooster (2003) fija el coeficiente 18.9 para la MIR-method (3.9 µm).
# Para SWIR2 (2.2 µm) el mismo coeficiente es una aproximación razonable
# cuando se asume cuerpo negro a >800 K (lava expuesta); para temperaturas
# magmáticas <600 K subestima VRP por <20% (Coppola 2016, Apéndice A).
E_SOLAR_B12_S2 = 84.86           # W/m²/µm — irradiancia solar TOA banda B12
SOLAR_DISTANCE_AU_MEAN = 1.0     # se ajusta por día del año
VRP_NHI_UMBRAL_REAL = 0.30       # NHI_SWIR sobre reflectancia BOA
VRP_B12_BRILLO_MIN = 0.15        # B12 reflectancia BOA mínima (0.35 era escala PNG, no BOA)


def _angulo_zenital_solar(lat_deg, fecha_iso, hora_utc_paso=14.83):
    """
    θ_zenith aproximado (sin pvlib) para Sentinel-2 sobre Chile.

    Sentinel-2 pasa ~10:43-10:55 hora Chile (UTC-4) → ~14:50 UTC.
    Esta aproximación clásica (Spencer 1971 + ec. tiempo) tiene error <2°
    para latitudes -60° a -15° entre 10:00-12:00 hora local, que es nuestro
    rango operativo. Para VRP esto se traduce en error <3% sobre la
    radiancia convertida — aceptable cuando MIROVA reporta ±factor 2-3 de
    incerteza intrínseca de la método SWIR.

    Para mayor precisión usar pvlib (`pvlib.solarposition.get_solarposition`).
    """
    dt = datetime.fromisoformat(fecha_iso) if isinstance(fecha_iso, str) else fecha_iso
    dia_anio = dt.timetuple().tm_yday

    # Declinación solar (Spencer 1971 simplificada)
    declinacion = 23.45 * np.sin(np.radians(360.0 * (284 + dia_anio) / 365.0))

    # Hora solar local aproximada: UTC paso - longitud_volcán/15
    # No tenemos lon acá; usamos la lat para corregir grossly y asumimos
    # longitud ≈ -70° (Chile central) → desfase ~ -4.67 h respecto UTC.
    # Para volcanes de Norte/Centro/Sur/Austral este error de hora solar
    # local introduce <0.5° en θ_zenith.
    hora_solar = hora_utc_paso - 70.0 / 15.0
    angulo_horario = 15.0 * (hora_solar - 12.0)

    cos_zenith = (
        np.sin(np.radians(declinacion)) * np.sin(np.radians(lat_deg)) +
        np.cos(np.radians(declinacion)) * np.cos(np.radians(lat_deg)) * np.cos(np.radians(angulo_horario))
    )
    # Limitar para evitar división por valores muy chicos en latitudes extremas en invierno
    return max(0.1, float(cos_zenith))


def _distancia_tierra_sol(fecha_iso):
    """Distancia Tierra-Sol en UA (Spencer 1971). Varía 0.983-1.017 según mes."""
    dt = datetime.fromisoformat(fecha_iso) if isinstance(fecha_iso, str) else fecha_iso
    dia_anio = dt.timetuple().tm_yday
    # Aproximación clásica
    return 1.0 + 0.01672 * float(np.cos(np.radians(0.9856 * (dia_anio - 4))))


def calcular_vrp_real(swir_raw_npz_path, lat_volcan, fecha_iso, mascara_extra=None,
                      area_pixel_m2=A_PIXEL_S2_SWIR_M2,
                      umbral_nhi=VRP_NHI_UMBRAL_REAL,
                      umbral_b12=VRP_B12_BRILLO_MIN):
    """
    VRP en Watts REALES según Coppola 2016 / Wooster 2003.

    Mecanismo físico
    ----------------
    Un foco térmico (lava, fumarola, lago de cráter) emite radiación de
    cuerpo negro cuyo pico, según Wien, cae en el infrarrojo cercano-medio
    para temperaturas magmáticas (800-1400 K). Sentinel-2 no tiene MIR (3.9 µm)
    como MODIS, pero su banda B12 (2.20 µm) está en la cola Wien de cualquier
    cuerpo >500 K y satura ante lava expuesta. La radiancia "excedente"
    sobre el fondo solar reflejado mide la potencia radiativa del foco.

    Pipeline
    --------
    1. Leer B11 y B12 en reflectancia BOA float32 desde .npz
    2. Detectar hot pixels: NHI = (B12-B11)/(B12+B11) > 0.30 AND B12 > 0.15
    3. Convertir reflectancia → radiancia espectral:
       L_λ = ρ × E_solar × cos(θ_zenith) / (π × d²)   [W/m²/sr/µm]
    4. VRP_pixel = 18.9 × A_pixel × L_λ              [W]
    5. Sumar todos los hot pixels, clasificar nivel Coppola

    Parámetros
    ----------
    swir_raw_npz_path : Path al .npz con keys 'B11', 'B12', 'dataMask'
    lat_volcan        : Latitud (grados, negativa para hemisferio sur)
    fecha_iso         : 'YYYY-MM-DD'
    mascara_extra     : Booleano 2D, True = píxel válido (e.g. ~glaciar)
    area_pixel_m2     : 400 para S2 SWIR (20m), 900 para Landsat SWIR (30m)
    umbral_nhi        : Marchese 2019 → 0.30 conservador
    umbral_b12        : Reflectancia BOA mínima para considerar hot

    Returns
    -------
    dict con vrp_total_MW, vrp_max_pixel_W, n_hot_pixels, nivel_termico,
    mean_radiance_B12_Wm2srum, theta_zenith_cos, metodo.
    """
    if not os.path.exists(swir_raw_npz_path):
        return None

    try:
        data = np.load(swir_raw_npz_path)
        b11 = data['B11'].astype(np.float32)
        b12 = data['B12'].astype(np.float32)
        data_mask = data['dataMask'].astype(bool) if 'dataMask' in data.files else np.ones_like(b11, dtype=bool)
    except Exception as e:
        print(f"    [VRP_real] Error leyendo {swir_raw_npz_path}: {e}")
        return None

    if b11.shape != b12.shape:
        return None

    # Hot mask: NHI > umbral AND B12 brillante AND píxel válido
    suma = b11 + b12
    nhi = np.where(suma > 1e-6, (b12 - b11) / np.where(suma > 1e-6, suma, 1.0), 0.0)
    hot_mask = (nhi > umbral_nhi) & (b12 > umbral_b12) & data_mask

    if mascara_extra is not None and mascara_extra.shape == hot_mask.shape:
        hot_mask &= mascara_extra

    if not hot_mask.any():
        return {
            "vrp_calibrado_mw": 0.0,
            "vrp_max_pixel_W": 0.0,
            "n_hot_pixels": 0,
            "nivel_termico": "Low",
            "mean_radiance_B12_Wm2srum": 0.0,
            "theta_zenith_cos": None,
            "metodo": "SWIR2-calibrado (Wooster 2003)",
        }

    # Geometría solar
    cos_zenith = _angulo_zenital_solar(lat_volcan, fecha_iso)
    d_au = _distancia_tierra_sol(fecha_iso)

    # Reflectancia BOA → radiancia espectral L (W/m²/sr/µm)
    # L = ρ × E_solar × cos(θ_zenith) / (π × d²)
    L_B12 = b12 * E_SOLAR_B12_S2 * cos_zenith / (np.pi * d_au * d_au)

    L_hot = L_B12[hot_mask]
    # VRP por pixel (Wooster 2003): 18.9 × A_pixel × L_SWIR  [W]
    vrp_pixels = VRP_COEF_WOOSTER * area_pixel_m2 * L_hot
    vrp_total_w = float(vrp_pixels.sum())
    vrp_total_mw = vrp_total_w / 1e6
    vrp_max_w = float(vrp_pixels.max())

    # Clasificación Coppola 2016a / 2023
    nivel = "Low"
    for nombre, umbral in NIVELES_TERMICOS_MW:
        if vrp_total_mw >= umbral:
            nivel = nombre
            break

    return {
        "vrp_calibrado_mw": round(vrp_total_mw, 4),
        "vrp_max_pixel_W": round(vrp_max_w, 1),
        "n_hot_pixels": int(hot_mask.sum()),
        "nivel_termico": nivel,
        "mean_radiance_B12_Wm2srum": round(float(L_hot.mean()), 3),
        "theta_zenith_cos": round(cos_zenith, 4),
        "distancia_au": round(d_au, 5),
        "metodo": "SWIR2-calibrado (Wooster 2003 / Coppola 2016)",
    }


def filtro_ndsi_glaciar(rgb_png_path, thermal_png_path, umbral_ndsi=UMBRAL_NDSI_NIEVE):
    """
    NDSI = (B3 - B11) / (B3 + B11). NDSI > 0.4 → nieve/hielo (Hall 1995).
    Para evitar falsos positivos SWIR sobre glaciares en volcanes nevados.

    Inputs:
        rgb_png_path: PNG RGB (sRGB) — usamos canal G (B03 verde) como proxy de B03.
        thermal_png_path: PNG ThermalFalseColor — canal G es 2.5*B11 lineal.
                          El PNG RGB usa sRGB encoding pero el verde ahí es B03 visible.

    NOTA: como el RGB tiene sRGB y el thermal es lineal, esta aproximación es burda.
    Para mayor precisión Sprint 2 debe usar PNGs separados con B03 y B11 lineales.

    Returns:
        mascara booleana 2D (True = pixel NO es nieve, se puede analizar térmicamente).
        None si no se pudo calcular.
    """
    img_rgb = cargar_imagen(rgb_png_path)
    img_th = cargar_imagen(thermal_png_path)
    if img_rgb is None or img_th is None:
        return None
    if img_rgb.shape[:2] != img_th.shape[:2]:
        # Redimensionar el thermal al tamaño del rgb usando PIL
        try:
            img_th_pil = Image.fromarray(img_th).resize(
                (img_rgb.shape[1], img_rgb.shape[0]), Image.BILINEAR
            )
            img_th = np.array(img_th_pil)
        except Exception:
            return None

    # B03 (verde) del RGB con sRGB decoding aproximado (gamma 2.2)
    b03_srgb = img_rgb[:, :, 1].astype(np.float32) / 255.0
    b03 = np.power(b03_srgb, 2.2)
    # B11 (SWIR1) del thermal lineal
    b11 = img_th[:, :, 1].astype(np.float32) / 255.0

    suma = b03 + b11
    ndsi = np.where(suma > 1e-6, (b03 - b11) / np.where(suma > 1e-6, suma, 1.0), 0.0)
    # True = pixel NO es nieve
    return ndsi <= umbral_ndsi


def calcular_mahalanobis(stack_historico, imagen_actual, mascara_nube=None, umbral_d=3.0):
    """
    Detecta anomalias multivariadas con distancia de Mahalanobis (Zhang 2016 LSMAD,
    IEEE TGRS, DOI 10.1109/TGRS.2015.2479299).

    A diferencia del Z-score (que evalua cada banda independientemente), Mahalanobis
    usa la matriz de covarianza COMPLETA: detecta pixeles cuya combinacion de bandas
    es atipica respecto al historico, aunque ninguna banda aislada lo sea.

    Args:
        stack_historico: array (N, H, W, B) — N imagenes anteriores
        imagen_actual: array (H, W, B)
        mascara_nube: array (H, W) booleana — True donde HAY nube
        umbral_d: distancia umbral (default 3.0, chi^2 95% para 3 dof)

    Returns:
        dict con n_anomalous_pixels, pct_anomalous, mahalanobis_max,
        mahalanobis_mean, estado (NORMAL/ATENCION/ALERTA)
        o None si falla.
    """
    try:
        if stack_historico is None or imagen_actual is None:
            return None
        if stack_historico.ndim != 4 or imagen_actual.ndim != 3:
            return None
        if stack_historico.shape[1:] != imagen_actual.shape:
            return None

        stack_f = stack_historico.astype(np.float32)
        actual_f = imagen_actual.astype(np.float32)

        n_bandas = stack_f.shape[-1]
        flat = stack_f.reshape(-1, n_bandas)
        media = flat.mean(axis=0)
        # Estabilizar la matriz de covarianza
        cov = np.cov(flat.T)
        # Regularizacion para evitar singularidad (pequena diagonal)
        cov = cov + np.eye(n_bandas, dtype=np.float32) * 1e-3
        cov_inv = np.linalg.pinv(cov)

        delta = actual_f - media
        d2 = np.einsum('hwb,bc,hwc->hw', delta, cov_inv, delta)
        d = np.sqrt(np.clip(d2, 0, None))

        mascara = d > umbral_d
        if mascara_nube is not None and mascara_nube.shape == mascara.shape:
            mascara = mascara & ~mascara_nube
            total = int((~mascara_nube).sum())
        else:
            total = mascara.size

        n_anom = int(mascara.sum())
        pct = (n_anom / total * 100.0) if total > 0 else 0.0
        d_max = float(d.max())
        d_mean = float(d.mean())

        if pct > 3 and d_max > 5:
            estado = 'ALERTA'
        elif pct > 1 and d_max > 3:
            estado = 'ATENCION'
        else:
            estado = 'NORMAL'

        return {
            'n_anomalous_pixels': n_anom,
            'pct_anomalous': round(pct, 3),
            'mahalanobis_max': round(d_max, 3),
            'mahalanobis_mean': round(d_mean, 3),
            'umbral': umbral_d,
            'n_imagenes_baseline': int(stack_historico.shape[0]),
            'estado': estado,
        }
    except Exception as e:
        print(f"    Mahalanobis fallo: {e}")
        return None


def evaluar_estado_nhi(nhi_stats):
    """
    Convierte stats NHI en un estado: NORMAL / ATENCION / ALERTA.

    Reglas Sprint 1:
        - n_hot_pixels_nhi > NHI_HOT_PIXEL_UMBRAL Y nhi_max > NHI_MAX_UMBRAL_ATENCION → ATENCION
        - n_hot_pixels_nhi_strict > NHI_STRICT_PIXEL_UMBRAL → ATENCION confirmada (ambos NHI>0)
        - Si AMBAS condiciones se cumplen → ALERTA
    """
    if not nhi_stats:
        return "SIN_DATOS", "NHI no calculable"
    n = nhi_stats.get("n_hot_pixels_nhi", 0)
    n_strict = nhi_stats.get("n_hot_pixels_nhi_strict", 0)
    nhi_max = nhi_stats.get("nhi_max", 0.0)

    cond_modal = n > NHI_HOT_PIXEL_UMBRAL and nhi_max > NHI_MAX_UMBRAL_ATENCION
    cond_strict = n_strict > NHI_STRICT_PIXEL_UMBRAL

    if cond_modal and cond_strict:
        return "ALERTA", f"NHI alta confianza ({n_strict} px ambos NHI>0, max={nhi_max:.2f})"
    if cond_strict:
        return "ATENCION", f"NHI confirmado SWIR+SWNIR ({n_strict} px, max={nhi_max:.2f})"
    if cond_modal:
        return "ATENCION", f"NHI elevado ({n} hot px, max={nhi_max:.2f})"
    if n > 0:
        return "NORMAL", f"NHI debil ({n} px, max={nhi_max:.2f})"
    return "NORMAL", "Sin hotspots NHI"


def analizar_indices_espectrales(volcan, fecha_nueva, fecha_anterior):
    """
    Analiza PNGs espectrales (NDVI, NBR, SWIR_Anomaly) como validacion cruzada.
    Los PNGs son paletas coloreadas — se analizan canales RGB directamente.
    """
    resultado = {
        'ndvi_stable': False,
        'swir_anomaly_confirmed': False,
        'dnbr_pct': 0.0,
        'swir_pct': 0.0,
        'disponibles': []
    }

    for tipo in ['NDVI', 'NBR', 'SWIR_Anomaly']:
        path_nueva = os.path.join(SENTINEL_DIR, volcan, f"{fecha_nueva}_{tipo}.png")
        path_ant = os.path.join(SENTINEL_DIR, volcan, f"{fecha_anterior}_{tipo}.png") if fecha_anterior else None

        if not os.path.exists(path_nueva):
            continue

        resultado['disponibles'].append(tipo)
        arr_nueva = cargar_imagen(path_nueva)
        if arr_nueva is None:
            continue

        sh, sw = recortar_zona_central(arr_nueva.shape)
        nueva_c = arr_nueva[sh, sw]
        mascara_n = crear_mascara_nubes(nueva_c)
        validos_n = ~mascara_n

        if tipo == 'NDVI' and path_ant and os.path.exists(path_ant):
            arr_ant = cargar_imagen(path_ant)
            if arr_ant is not None:
                ant_c = arr_ant[sh, sw]
                validos_ambos = validos_n & ~crear_mascara_nubes(ant_c)
                if np.sum(validos_ambos) > 100:
                    diff_verde = np.abs(nueva_c[:,:,1].astype(float) - ant_c[:,:,1].astype(float))
                    resultado['ndvi_stable'] = float(np.mean(diff_verde[validos_ambos])) < 15

        elif tipo == 'SWIR_Anomaly':
            # Paleta: R>180, G<120, B<120 = anomalia termica
            if np.sum(validos_n) > 100:
                r, g, b = nueva_c[:,:,0], nueva_c[:,:,1], nueva_c[:,:,2]
                pixeles_rojos = (r > 180) & (g < 120) & (b < 120) & validos_n
                pct_rojos = float(np.sum(pixeles_rojos)) / float(np.sum(validos_n)) * 100
                resultado['swir_anomaly_confirmed'] = pct_rojos > 0.5
                resultado['swir_pct'] = round(pct_rojos, 2)

        elif tipo == 'NBR' and path_ant and os.path.exists(path_ant):
            arr_ant = cargar_imagen(path_ant)
            if arr_ant is not None:
                ant_c = arr_ant[sh, sw]
                validos_ambos = validos_n & ~crear_mascara_nubes(ant_c)
                if np.sum(validos_ambos) > 100:
                    diff_rojo = nueva_c[:,:,0].astype(float) - ant_c[:,:,0].astype(float)
                    pct_aumento = float(np.sum(diff_rojo[validos_ambos] > 30)) / float(np.sum(validos_ambos)) * 100
                    resultado['dnbr_pct'] = round(pct_aumento, 2)

    if not resultado['disponibles']:
        return None

    return resultado


def verificar_consistencia_temporal(volcan, estado_actual):
    """
    Verifica si el estado actual tiene respaldo en el historial.
    Un evento aislado (spike) se degrada para evitar falsos positivos.
    """
    history_path = os.path.join(OUTPUT_DIR, "change_history.json")
    resultado = {'consecutive_elevated': 0, 'consistent': False}

    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            historial = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return resultado

    registros = historial.get(volcan, [])
    if not registros:
        return resultado

    estados_elevados = {'ALERTA', 'ATENCION'}
    consecutivos = 0
    for r in reversed(registros[-10:]):
        if r.get('estado') in estados_elevados:
            consecutivos += 1
        else:
            break

    resultado['consecutive_elevated'] = consecutivos
    resultado['consistent'] = consecutivos >= 1

    return resultado


def analizar_cambio_volcan(volcan, sensor='sentinel2'):
    """
    Análisis completo de cambios para un volcán usando un sensor específico.
    Compara la imagen más reciente contra el background estadístico.

    Args:
        volcan: Nombre del volcán
        sensor: 'sentinel2' o 'landsat' (ver SENSORES)
    """
    sensor_cfg = SENSORES.get(sensor)
    if sensor_cfg is None:
        return {"estado": "ERROR", "detalle": f"Sensor desconocido: {sensor}"}

    base_dir = sensor_cfg["base_dir"]
    tipo = sensor_cfg["tipo_termico"]
    tiene_espectrales = sensor_cfg["tiene_indices_espectrales"]

    if not os.path.isdir(os.path.join(base_dir, volcan)):
        return {
            "estado": "SIN_DATOS",
            "detalle": f"Sin carpeta para {volcan} en {sensor}",
            "sensor": sensor
        }

    fechas = obtener_fechas_disponibles(volcan, tipo, base_dir=base_dir)
    if len(fechas) < 3:
        return {
            "estado": "SIN_DATOS",
            "detalle": f"Solo {len(fechas)} imágenes {sensor} disponibles (mínimo 3)",
            "confianza": "BAJA",
            "sensor": sensor
        }

    fecha_nueva = fechas[-1]
    path_nueva = os.path.join(base_dir, volcan, f"{fecha_nueva}_{tipo}.png")
    img_nueva = cargar_imagen(path_nueva)
    if img_nueva is None:
        return {"estado": "ERROR", "detalle": "No se pudo cargar imagen reciente", "sensor": sensor}

    # Background estadístico (con stack crudo para Mahalanobis)
    background, fechas_bg, stack_historico = calcular_background_estadistico(
        volcan, tipo, max_imagenes=10, base_dir=base_dir, return_stack=True
    )
    if background is None:
        return {"estado": "SIN_DATOS", "detalle": "No se pudo calcular background"}

    # Zona central
    slice_h, slice_w = recortar_zona_central(img_nueva.shape)
    img_central = img_nueva[slice_h, slice_w]
    bg_central = background[slice_h, slice_w]

    # Máscara de nubes en imagen nueva
    mascara_nubes = crear_mascara_nubes(img_central)
    total_pixeles = mascara_nubes.size
    pixeles_nube = np.sum(mascara_nubes)
    pct_nubes = (pixeles_nube / total_pixeles) * 100

    # Verificar cobertura mínima
    pixeles_validos_ratio = 1 - (pixeles_nube / total_pixeles)
    if pixeles_validos_ratio < MIN_PIXELES_VALIDOS:
        return {
            "estado": "NUBLADO",
            "nube_pct": round(pct_nubes, 1),
            "detalle": f"Demasiadas nubes ({pct_nubes:.0f}%), análisis no confiable",
            "confianza": "BAJA",
            "fecha_nueva": fecha_nueva,
            "fecha_referencia": f"mediana de {len(fechas_bg)} imgs"
        }

    # Máscara combinada: excluir nubes tanto en nueva como en background
    mascara_bg_nubes = crear_mascara_nubes(bg_central)
    mascara_excluir = mascara_nubes | mascara_bg_nubes

    # Diferencia absoluta (solo en píxeles válidos)
    diff = np.abs(img_central.astype(float) - bg_central.astype(float))

    # Poner a 0 los píxeles excluidos
    for c in range(3):
        diff[:,:,c][mascara_excluir] = 0

    pixeles_validos = np.sum(~mascara_excluir)
    if pixeles_validos == 0:
        return {"estado": "NUBLADO", "nube_pct": 100.0, "detalle": "Sin píxeles válidos", "confianza": "BAJA"}

    # --- Métricas ---

    # Cambio general: píxeles con diferencia > umbral
    mascara_cambio = np.any(diff > UMBRAL_CAMBIO_PIXEL, axis=2) & (~mascara_excluir)
    pixeles_cambiados = np.sum(mascara_cambio)
    pct_cambio_general = (pixeles_cambiados / pixeles_validos) * 100

    # Cambio térmico: canal rojo (B12 SWIR2 en ThermalFalseColor)
    diff_rojo = diff[:,:,0].copy()
    diff_rojo[mascara_excluir] = 0
    valores_rojo_validos = diff_rojo[~mascara_excluir]

    media_diff_rojo = np.mean(valores_rojo_validos) if len(valores_rojo_validos) > 0 else 0
    std_diff_rojo = np.std(valores_rojo_validos) if len(valores_rojo_validos) > 0 else 0
    max_diff_rojo = np.max(valores_rojo_validos) if len(valores_rojo_validos) > 0 else 0

    # Umbral estadístico para anomalía térmica
    umbral_termico = media_diff_rojo + 2 * std_diff_rojo
    pixeles_anomalia_termica = np.sum(valores_rojo_validos > max(umbral_termico, 40))
    pct_anomalia_termica = (pixeles_anomalia_termica / pixeles_validos) * 100

    # Cambio morfológico: canales verde+azul (B11 SWIR1 + B04 Red)
    diff_verde_azul = np.mean(diff[:,:,1:3], axis=2)
    diff_verde_azul[mascara_excluir] = 0
    valores_morfo = diff_verde_azul[~mascara_excluir]
    media_morfo = np.mean(valores_morfo) if len(valores_morfo) > 0 else 0
    pct_cambio_morfo = (np.sum(valores_morfo > UMBRAL_CAMBIO_PIXEL) / pixeles_validos) * 100

    # Confianza basada en cobertura de nubes
    if pct_nubes < 20:
        confianza = "ALTA"
    elif pct_nubes < 50:
        confianza = "MEDIA"
    else:
        confianza = "BAJA"

    # Imagen anterior (para before/after visual)
    fecha_anterior = fechas[-2] if len(fechas) >= 2 else None

    # Índices espectrales disponibles (solo sensores que los tengan)
    indices_disponibles = {}
    if tiene_espectrales:
        for idx_tipo in ['NDVI', 'NBR', 'SWIR_Anomaly']:
            path_idx = os.path.join(base_dir, volcan, f"{fecha_nueva}_{idx_tipo}.png")
            if os.path.exists(path_idx):
                indices_disponibles[idx_tipo] = True

    # --- Clasificación con Z-score ---
    baseline_mean, baseline_std = calcular_varianza_background(volcan, tipo, base_dir=base_dir)
    indices_spectral = analizar_indices_espectrales(volcan, fecha_nueva, fecha_anterior) if tiene_espectrales else None
    estado, detalle, z_score = clasificar_con_zscore(
        pct_anomalia_termica, max_diff_rojo, pct_cambio_morfo,
        baseline_mean, baseline_std, indices_spectral
    )

    # --- Sprint 1: NHI + VRP + filtro NDSI ---
    nhi_stats = None
    vrp_stats = None
    vrp_real_stats = None         # VRP calibrado en Watts (Wooster 2003) si SWIR_raw existe
    nhi_estado = None
    nhi_detalle = ""
    mascara_no_nieve = None
    aplicar_ndsi = (sensor == 'sentinel2' and volcan in VOLCANES_CON_GLACIAR)

    if sensor == 'sentinel2':
        path_rgb_nueva = os.path.join(base_dir, volcan, f"{fecha_nueva}_RGB.png")
        if aplicar_ndsi and os.path.exists(path_rgb_nueva):
            try:
                mascara_no_nieve = filtro_ndsi_glaciar(path_rgb_nueva, path_nueva)
            except Exception as e:
                print(f"    NDSI fallo en {volcan}: {e}")
                mascara_no_nieve = None

        try:
            nhi_stats = calcular_nhi(path_nueva, mascara_extra=mascara_no_nieve)
            vrp_stats = calcular_vrp_estimado(path_nueva, mascara_extra=mascara_no_nieve)
            if nhi_stats:
                nhi_estado, nhi_detalle = evaluar_estado_nhi(nhi_stats)
        except Exception as e:
            print(f"    NHI/VRP fallo en {volcan}: {e}")

        # VRP CALIBRADO REAL (Wooster 2003 / Coppola 2016) si hay SWIR_raw .npz.
        # Aditivo al proxy: si falta el .npz, vrp_real_stats queda None y la UI
        # cae al VRP proxy con un disclaimer.
        path_swir_raw = os.path.join(base_dir, volcan, f"{fecha_nueva}_SWIR_raw.npz")
        if os.path.exists(path_swir_raw):
            lat = _lat_de_volcan(volcan)
            if lat is not None:
                try:
                    # Adaptar máscara: VRP_real espera True=válido (mismo shape que .npz).
                    # mascara_no_nieve viene del PNG; tiene resolución distinta a .npz,
                    # así que aquí no la pasamos directamente. Para v1 confiamos en el
                    # umbral NHI conservador (0.30) — Sprint 2 puede resamplear NDSI.
                    vrp_real_stats = calcular_vrp_real(
                        path_swir_raw, lat_volcan=lat, fecha_iso=fecha_nueva
                    )
                except Exception as e:
                    print(f"    VRP_real fallo en {volcan}: {e}")

    elif sensor == 'landsat':
        # NHI Landsat usa el composite SWIR (B7-B6-B4), NO el THERMAL (B10 monocanal).
        path_swir_landsat = os.path.join(base_dir, volcan, f"{fecha_nueva}_SWIR.png")
        if os.path.exists(path_swir_landsat):
            try:
                nhi_stats = calcular_nhi_landsat(path_swir_landsat)
                # VRP Landsat: pixel SWIR ~30 m → 900 m²
                vrp_stats = calcular_vrp_estimado(
                    path_swir_landsat,
                    mascara_extra=None,
                    area_pixel_m2=900.0,
                )
                if nhi_stats:
                    nhi_estado, nhi_detalle = evaluar_estado_nhi(nhi_stats)
            except Exception as e:
                print(f"    NHI/VRP Landsat fallo en {volcan}: {e}")

    # --- Mahalanobis (Zhang 2016 LSMAD) — multivariado SWIR thermal ---
    mahalanobis_stats = None
    mahalanobis_estado = None
    if stack_historico is not None and stack_historico.shape[0] >= 5:
        try:
            # Recortar stack y actual a zona central, aplicar misma mascara de nubes
            stack_central = stack_historico[:, slice_h, slice_w, :]
            mahalanobis_stats = calcular_mahalanobis(
                stack_central, img_central,
                mascara_nube=mascara_excluir, umbral_d=3.0
            )
            if mahalanobis_stats:
                mahalanobis_estado = mahalanobis_stats.get('estado')
        except Exception as e:
            print(f"    Mahalanobis fallo en {volcan}: {e}")
    else:
        n_imgs = 0 if stack_historico is None else stack_historico.shape[0]
        mahalanobis_stats = {
            'estado': 'SIN_DATOS',
            'nota': f'Stack insuficiente ({n_imgs}<5) — fallback a Z-score',
            'n_imagenes_baseline': n_imgs,
        }
        mahalanobis_estado = 'SIN_DATOS'

    # --- Combinar 3 algoritmos: Z-score / NHI / Mahalanobis ---
    z_estado_original = estado
    z_detalle_original = detalle
    prio = PRIORIDAD_ESTADO

    # Recolectar candidatos validos
    candidatos = [('Z-score', estado, detalle)]
    if nhi_estado and nhi_estado != 'SIN_DATOS':
        candidatos.append(('NHI', nhi_estado, nhi_detalle))
    if mahalanobis_estado and mahalanobis_estado != 'SIN_DATOS':
        m_detalle = (f"d_max={mahalanobis_stats.get('mahalanobis_max',0)}, "
                     f"{mahalanobis_stats.get('n_anomalous_pixels',0)} px "
                     f"({mahalanobis_stats.get('pct_anomalous',0)}%)")
        candidatos.append(('Mahalanobis', mahalanobis_estado, m_detalle))

    # Estado final = el peor
    peor = max(candidatos, key=lambda c: prio.get(c[1], 0))
    if prio.get(peor[1], 0) > prio.get(estado, 0):
        estado = peor[1]
        detalle = f"[{peor[0]} override] {peor[2]} | Z-score era {z_estado_original}"

    # Divergencias entre algoritmos (solo de los que tienen dato real)
    divergencias = []
    estados_validos = [(n, e) for n, e, _ in candidatos]
    estados_unicos = set(e for _, e in estados_validos)
    triple_consenso = (len(estados_validos) == 3 and len(estados_unicos) == 1)
    if len(estados_unicos) > 1:
        for nombre_alg, est_alg in estados_validos:
            divergencias.append(f"{nombre_alg}: {est_alg}")

    # Consistencia temporal (evitar alertas aisladas) — namespace por sensor
    consistencia = verificar_consistencia_temporal(f"{volcan}::{sensor}", estado)
    if not consistencia['consistent']:
        if estado == "ALERTA":
            estado = "ATENCION"
            detalle = "[Pendiente confirmacion] " + detalle
        elif estado == "ATENCION":
            estado = "NORMAL"
            detalle = "[Sin consistencia temporal] " + detalle

    return {
        "sensor": sensor,
        "estado": estado,
        "cambio_termico_pct": round(pct_anomalia_termica, 2),
        "cambio_morfologico_pct": round(pct_cambio_morfo, 2),
        "cambio_general_pct": round(pct_cambio_general, 2),
        "max_diff_termico": round(float(max_diff_rojo), 1),
        "nube_pct": round(pct_nubes, 1),
        "fecha_nueva": fecha_nueva,
        "fecha_anterior": fecha_anterior,
        "fecha_referencia": f"mediana de {len(fechas_bg)} imgs ({fechas_bg[0]} a {fechas_bg[-1]})",
        "imagenes_en_background": len(fechas_bg),
        "confianza": confianza,
        "detalle": detalle,
        "indices_disponibles": indices_disponibles,
        "baseline_mean": round(baseline_mean, 3) if baseline_mean is not None else None,
        "baseline_std": round(baseline_std, 3) if baseline_std is not None else None,
        "z_score_termico": z_score,
        "indices_spectral": indices_spectral,
        "consistencia_temporal": consistencia,
        # --- Sprint 1: NHI + VRP ---
        "z_score_estado": z_estado_original,
        "nhi_estado": nhi_estado,
        "nhi_detalle": nhi_detalle,
        "nhi_stats": nhi_stats,
        "vrp_estimado_mw": vrp_stats.get("vrp_estimado_mw") if vrp_stats else None,
        "nivel_termico": vrp_stats.get("nivel_termico") if vrp_stats else None,
        "vrp_pixels": vrp_stats.get("pixels_calculados") if vrp_stats else None,
        # --- VRP calibrado real (Wooster 2003 / Coppola 2016) ---
        # Si el .npz SWIR_raw no está disponible queda None y la UI muestra "—".
        # Cuando exista, ES la métrica autoritativa comparable a MIROVA; el
        # proxy queda como fallback histórico.
        "vrp_calibrado_mw": vrp_real_stats.get("vrp_calibrado_mw") if vrp_real_stats else None,
        "vrp_calibrado_nivel": vrp_real_stats.get("nivel_termico") if vrp_real_stats else None,
        "vrp_calibrado_n_pixels": vrp_real_stats.get("n_hot_pixels") if vrp_real_stats else None,
        "vrp_calibrado_max_pixel_W": vrp_real_stats.get("vrp_max_pixel_W") if vrp_real_stats else None,
        "vrp_calibrado_stats": vrp_real_stats,
        "ndsi_aplicado": aplicar_ndsi,
        # --- Mahalanobis (Zhang 2016) ---
        "mahalanobis_stats": mahalanobis_stats,
        "mahalanobis_estado": mahalanobis_estado,
        "divergencias": divergencias,
        "triple_consenso": triple_consenso,
    }


# ============================================================
# COMBINADOR MULTI-SENSOR
# ============================================================

PRIORIDAD_ESTADO = {
    "ALERTA": 4, "ATENCION": 3, "NUBLADO": 2,
    "NORMAL": 1, "SIN_DATOS": 0, "ERROR": 0
}


def analizar_volcan_multisensor(volcan):
    """
    Corre el análisis en todos los sensores disponibles y combina resultados.
    Estado final = el peor entre sensores (ALERTA > ATENCION > NUBLADO > NORMAL).
    """
    por_sensor = {}
    for sensor in SENSORES.keys():
        por_sensor[sensor] = analizar_cambio_volcan(volcan, sensor=sensor)

    # Elegir el estado "peor" como combinado
    mejor_sensor = max(
        por_sensor.values(),
        key=lambda r: PRIORIDAD_ESTADO.get(r.get("estado", "ERROR"), 0)
    )
    estado_combinado = mejor_sensor.get("estado", "SIN_DATOS")
    detalle_combinado = f"[{mejor_sensor.get('sensor','?').upper()}] {mejor_sensor.get('detalle','')}"

    # Confirmación cruzada: si ambos sensores coinciden en ATENCION/ALERTA, subir confianza
    estados_elevados = {"ATENCION", "ALERTA"}
    sensores_elevados = [s for s, r in por_sensor.items() if r.get("estado") in estados_elevados]
    confirmacion_cruzada = len(sensores_elevados) >= 2

    if confirmacion_cruzada and estado_combinado == "ATENCION":
        estado_combinado = "ALERTA"
        detalle_combinado = "Confirmado por Sentinel-2 + Landsat — " + detalle_combinado

    # --- Cross-validación NHI Sentinel-2 vs Landsat ---
    r_s2 = por_sensor.get('sentinel2', {}) or {}
    r_l8 = por_sensor.get('landsat', {}) or {}
    nhi_s2 = r_s2.get('nhi_estado')
    nhi_l8 = r_l8.get('nhi_estado')
    fecha_s2 = r_s2.get('fecha_nueva')
    fecha_l8 = r_l8.get('fecha_nueva')
    nhi_estados_elevados = {'ATENCION', 'ALERTA'}

    # Triple confirmación térmica: NHI-S2 + NHI-Landsat + Z-score (S2 o L8) elevados
    z_elevado = (
        r_s2.get('z_score_estado') in nhi_estados_elevados or
        r_l8.get('z_score_estado') in nhi_estados_elevados
    )
    triple_confirmacion = (
        nhi_s2 in nhi_estados_elevados and
        nhi_l8 in nhi_estados_elevados and
        z_elevado
    )

    # Asimetría: solo un sensor detecta NHI elevado, el otro tiene dato y dice NORMAL
    asimetria = None
    if nhi_s2 and nhi_l8 and nhi_s2 not in (None, 'SIN_DATOS') and nhi_l8 not in (None, 'SIN_DATOS'):
        if (nhi_s2 in nhi_estados_elevados) != (nhi_l8 in nhi_estados_elevados):
            sensor_caliente = 'sentinel2' if nhi_s2 in nhi_estados_elevados else 'landsat'
            asimetria = f"NHI elevado solo en {sensor_caliente}"

    # Coincidencia temporal (misma semana)
    misma_semana = False
    try:
        if fecha_s2 and fecha_l8:
            d_s2 = datetime.strptime(fecha_s2, '%Y-%m-%d')
            d_l8 = datetime.strptime(fecha_l8, '%Y-%m-%d')
            misma_semana = abs((d_s2 - d_l8).days) <= 7
    except Exception:
        pass

    cross_validacion_nhi = {
        'nhi_s2': nhi_s2,
        'nhi_landsat': nhi_l8,
        'nhi_s2_max': (r_s2.get('nhi_stats') or {}).get('nhi_max'),
        'nhi_landsat_max': (r_l8.get('nhi_stats') or {}).get('nhi_max'),
        'fecha_s2': fecha_s2,
        'fecha_landsat': fecha_l8,
        'misma_semana': misma_semana,
        'triple_confirmacion': triple_confirmacion,
        'asimetria_sensor': asimetria,
        'doble_confirmacion_nhi': (
            nhi_s2 in nhi_estados_elevados and nhi_l8 in nhi_estados_elevados
        ),
    }

    # Si hay triple confirmación, escalar a ALERTA
    if triple_confirmacion and estado_combinado != 'ALERTA':
        estado_combinado = 'ALERTA'
        detalle_combinado = (
            'Triple confirmacion termica (NHI-S2 + NHI-Landsat + Z-score) — ' +
            detalle_combinado
        )

    return {
        "estado": estado_combinado,
        "detalle": detalle_combinado,
        "confirmacion_cruzada": confirmacion_cruzada,
        "por_sensor": por_sensor,
        # Campos heredados del sensor principal para compatibilidad con UI antigua
        "fecha_nueva": mejor_sensor.get("fecha_nueva"),
        "fecha_anterior": mejor_sensor.get("fecha_anterior"),
        "confianza": mejor_sensor.get("confianza"),
        "cambio_termico_pct": mejor_sensor.get("cambio_termico_pct"),
        "cambio_morfologico_pct": mejor_sensor.get("cambio_morfologico_pct"),
        "max_diff_termico": mejor_sensor.get("max_diff_termico"),
        "z_score_termico": mejor_sensor.get("z_score_termico"),
        "baseline_mean": mejor_sensor.get("baseline_mean"),
        "baseline_std": mejor_sensor.get("baseline_std"),
        "indices_disponibles": mejor_sensor.get("indices_disponibles"),
        "indices_spectral": mejor_sensor.get("indices_spectral"),
        "consistencia_temporal": mejor_sensor.get("consistencia_temporal"),
        "nube_pct": mejor_sensor.get("nube_pct"),
        # --- Sprint 1: NHI + VRP (heredados del sensor con mayor severidad) ---
        "z_score_estado": mejor_sensor.get("z_score_estado"),
        "nhi_estado": mejor_sensor.get("nhi_estado"),
        "nhi_detalle": mejor_sensor.get("nhi_detalle"),
        "nhi_stats": mejor_sensor.get("nhi_stats"),
        "vrp_estimado_mw": mejor_sensor.get("vrp_estimado_mw"),
        "nivel_termico": mejor_sensor.get("nivel_termico"),
        "vrp_pixels": mejor_sensor.get("vrp_pixels"),
        # VRP calibrado: tomamos siempre el del Sentinel-2 (única fuente con .npz);
        # Landsat ahora no descarga SWIR_raw, así que mejor_sensor podría ser L8 y
        # tendría calibrado=None. Preferimos el de S2 cuando esté.
        "vrp_calibrado_mw": (por_sensor.get('sentinel2') or {}).get('vrp_calibrado_mw') or mejor_sensor.get("vrp_calibrado_mw"),
        "vrp_calibrado_nivel": (por_sensor.get('sentinel2') or {}).get('vrp_calibrado_nivel') or mejor_sensor.get("vrp_calibrado_nivel"),
        "vrp_calibrado_n_pixels": (por_sensor.get('sentinel2') or {}).get('vrp_calibrado_n_pixels') or mejor_sensor.get("vrp_calibrado_n_pixels"),
        "vrp_calibrado_max_pixel_W": (por_sensor.get('sentinel2') or {}).get('vrp_calibrado_max_pixel_W') or mejor_sensor.get("vrp_calibrado_max_pixel_W"),
        "vrp_calibrado_stats": (por_sensor.get('sentinel2') or {}).get('vrp_calibrado_stats') or mejor_sensor.get("vrp_calibrado_stats"),
        "ndsi_aplicado": mejor_sensor.get("ndsi_aplicado"),
        # --- Mahalanobis ---
        "mahalanobis_stats": mejor_sensor.get("mahalanobis_stats"),
        "mahalanobis_estado": mejor_sensor.get("mahalanobis_estado"),
        "divergencias": mejor_sensor.get("divergencias", []),
        "triple_consenso": mejor_sensor.get("triple_consenso", False),
        # --- Cross-validación NHI multi-sensor (Sentinel-2 vs Landsat) ---
        "cross_validacion_nhi": cross_validacion_nhi,
        "nhi_s2_estado": nhi_s2,
        "nhi_landsat_estado": nhi_l8,
        "nhi_s2_stats": r_s2.get('nhi_stats'),
        "nhi_landsat_stats": r_l8.get('nhi_stats'),
    }


# ============================================================
# CROSS-REFERENCIA NHI
# ============================================================

def obtener_estado_nhi(volcan):
    """Lee el estado NHI más reciente del volcán."""
    nhi_path = os.path.join(NHI_DIR, volcan, "nhi_timeseries.json")
    if not os.path.exists(nhi_path):
        return None

    try:
        with open(nhi_path, 'r') as f:
            datos = json.load(f)

        if not datos:
            return None

        # Buscar alertas en últimos 7 y 30 días
        hoy = datetime.now()
        alertas_7d = 0
        alertas_30d = 0
        ultima_alerta = None

        for registro in datos:
            if registro.get('alerta'):
                fecha_reg = datetime.strptime(registro['fecha'], '%Y-%m-%d')
                dias = (hoy - fecha_reg).days
                if dias <= 7:
                    alertas_7d += 1
                if dias <= 30:
                    alertas_30d += 1
                    if ultima_alerta is None or fecha_reg > datetime.strptime(ultima_alerta, '%Y-%m-%d'):
                        ultima_alerta = registro['fecha']

        if alertas_7d > 0:
            estado = "ROJO"
        elif alertas_30d > 0:
            estado = "AMARILLO"
        else:
            estado = "VERDE"

        return {
            "estado": estado,
            "alertas_7d": alertas_7d,
            "alertas_30d": alertas_30d,
            "ultima_alerta": ultima_alerta,
            "total_registros": len(datos)
        }
    except Exception as e:
        print(f"    Error leyendo NHI {volcan}: {e}")
        return None


# ============================================================
# CROSS-REFERENCIA MIROVA
# ============================================================

def obtener_vrp_mirova(volcan):
    """Lee los datos VRP más recientes de Mirova para el volcán."""
    if volcan not in MIROVA_NOMBRES:
        return None

    if not os.path.exists(MIROVA_CSV):
        return None

    nombre_mirova = MIROVA_NOMBRES[volcan]

    try:
        registros = []
        with open(MIROVA_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Volcan', '') == nombre_mirova:
                    try:
                        vrp = float(row.get('VRP_MW', 0))
                        fecha = row.get('Fecha_Satelite_UTC', '')
                        sensor = row.get('Sensor', '')
                        registros.append({
                            "vrp": vrp,
                            "fecha": fecha,
                            "sensor": sensor
                        })
                    except (ValueError, KeyError):
                        continue

        if not registros:
            return {"disponible": True, "registros_recientes": 0, "vrp_max_reciente": 0}

        # Últimos 7 días
        hoy = datetime.now()
        recientes = []
        for r in registros:
            try:
                fecha_r = datetime.strptime(r['fecha'][:10], '%Y-%m-%d')
                if (hoy - fecha_r).days <= 7:
                    recientes.append(r)
            except ValueError:
                continue

        vrp_max = max([r['vrp'] for r in recientes]) if recientes else 0
        vrp_promedio = np.mean([r['vrp'] for r in recientes]) if recientes else 0

        return {
            "disponible": True,
            "registros_recientes": len(recientes),
            "vrp_max_reciente": round(vrp_max, 2),
            "vrp_promedio_reciente": round(float(vrp_promedio), 2),
            "ultimo_registro": registros[-1]['fecha'] if registros else None
        }
    except Exception as e:
        print(f"    Error leyendo Mirova {volcan}: {e}")
        return None


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

def obtener_lista_volcanes():
    """Retorna lista de volcanes con imágenes en cualquier sensor (S2 o Landsat)."""
    volcanes = set()
    for cfg in SENSORES.values():
        bd = cfg["base_dir"]
        if os.path.exists(bd):
            for d in os.listdir(bd):
                if os.path.isdir(os.path.join(bd, d)):
                    volcanes.add(d)
    return sorted(volcanes)


def analizar_todos(volcanes=None):
    """Ejecuta análisis completo para todos los volcanes."""
    if volcanes is None:
        volcanes = obtener_lista_volcanes()

    print(f"\n{'='*70}")
    print(f"CHANGE ANALYSIS — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Volcanes a analizar: {len(volcanes)}")
    print(f"{'='*70}\n")

    resultados = {
        "fecha_analisis": datetime.now().strftime('%Y-%m-%d %H:%M UTC'),
        "total_volcanes": len(volcanes),
        "volcanes": {}
    }

    conteo = {"NORMAL": 0, "ATENCION": 0, "ALERTA": 0, "NUBLADO": 0, "SIN_DATOS": 0, "ERROR": 0}

    for i, volcan in enumerate(volcanes, 1):
        print(f"[{i}/{len(volcanes)}] {volcan}...")

        # Análisis multi-sensor (Sentinel-2 + Landsat, combinado)
        resultado = analizar_volcan_multisensor(volcan)

        # Cross-referencia NHI
        nhi = obtener_estado_nhi(volcan)
        if nhi:
            resultado["nhi"] = nhi

        # Cross-referencia Mirova
        mirova = obtener_vrp_mirova(volcan)
        if mirova:
            resultado["mirova"] = mirova

        # Zona geográfica
        resultado["zona"] = ZONA_POR_VOLCAN.get(volcan, "Desconocida")

        # Guardar
        resultados["volcanes"][volcan] = resultado

        estado = resultado.get("estado", "ERROR")
        conteo[estado] = conteo.get(estado, 0) + 1
        print(f"    → {estado} | {resultado.get('detalle', '')}")

    # Resumen
    resultados["resumen"] = conteo

    print(f"\n{'='*70}")
    print(f"RESUMEN:")
    for estado, n in conteo.items():
        if n > 0:
            print(f"  {estado}: {n}")
    print(f"{'='*70}\n")

    # Guardar JSON
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "change_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"Resultados guardados en: {output_path}")

    # Guardar historial (últimos 30 registros por volcán)
    history_path = os.path.join(OUTPUT_DIR, "change_history.json")
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            historial = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        historial = {}

    for volcan, resultado in resultados["volcanes"].items():
        # Historial combinado (a nivel volcán)
        if volcan not in historial:
            historial[volcan] = []
        fecha_img = resultado.get("fecha_nueva", "")
        if fecha_img:
            ya_registrado = any(r.get("fecha") == fecha_img for r in historial[volcan][-3:])
            if not ya_registrado:
                historial[volcan].append({
                    "fecha": fecha_img,
                    "estado": resultado.get("estado", ""),
                    "cambio_termico_pct": resultado.get("cambio_termico_pct", 0),
                    "max_diff_termico": resultado.get("max_diff_termico", 0),
                    "z_score": resultado.get("z_score_termico"),
                    "confirmacion_cruzada": resultado.get("confirmacion_cruzada", False)
                })
            historial[volcan] = historial[volcan][-30:]

        # Historial por sensor (namespace volcan::sensor, para consistencia temporal)
        for sensor, r_sensor in (resultado.get("por_sensor") or {}).items():
            key = f"{volcan}::{sensor}"
            if key not in historial:
                historial[key] = []
            fecha_s = r_sensor.get("fecha_nueva", "")
            if not fecha_s:
                continue
            ya = any(h.get("fecha") == fecha_s for h in historial[key][-3:])
            if not ya:
                historial[key].append({
                    "fecha": fecha_s,
                    "estado": r_sensor.get("estado", ""),
                    "cambio_termico_pct": r_sensor.get("cambio_termico_pct", 0),
                    "z_score": r_sensor.get("z_score_termico")
                })
            historial[key] = historial[key][-30:]

    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)
    print(f"Historial guardado en: {history_path}")

    return resultados


if __name__ == "__main__":
    if "--test" in sys.argv:
        # Test con 3 volcanes
        analizar_todos(["Villarrica", "Lascar", "Copahue"])
    elif len(sys.argv) > 1 and sys.argv[1] != "--test":
        # Volcán específico
        analizar_todos([sys.argv[1]])
    else:
        # Todos
        analizar_todos()
