"""
Configuracin Sentinel-2 - 43 VOLCANES ACTIVOS
COMPATIBLE con sentinel2_downloader.py existente
"""

import os
from datetime import datetime, timedelta

# ============================================
# CREDENCIALES COPERNICUS (desde env vars) — con FAILOVER multi-cuenta
# ============================================
# Lee la cuenta primaria (SH_CLIENT_ID/SECRET) + backups numeradas
# (SH_CLIENT_ID_2/SECRET_2, _3, ...). El downloader rota a la siguiente cuando la
# activa devuelve 403 por PU/creditos agotados. Asi una cuenta seca no frena el
# monitoreo (y, sobre todo, no deja el run VERDE-vacio: si se agotan TODAS, aborta).
def _load_credential_sets():
    """Devuelve [(client_id, client_secret), ...] en orden de prioridad."""
    sets = []
    pid, psec = os.getenv('SH_CLIENT_ID'), os.getenv('SH_CLIENT_SECRET')
    if pid and psec:
        sets.append((pid, psec))
    i = 2
    while True:
        cid, csec = os.getenv(f'SH_CLIENT_ID_{i}'), os.getenv(f'SH_CLIENT_SECRET_{i}')
        if cid and csec:
            sets.append((cid, csec))
            i += 1
        else:
            break
    return sets

CREDENTIAL_SETS = _load_credential_sets()

# Backward-compat: primer set (o None si no hay). Codigo que importa CLIENT_ID/SECRET sigue andando.
CLIENT_ID = CREDENTIAL_SETS[0][0] if CREDENTIAL_SETS else os.getenv('SH_CLIENT_ID')
CLIENT_SECRET = CREDENTIAL_SETS[0][1] if CREDENTIAL_SETS else os.getenv('SH_CLIENT_SECRET')

# ============================================
# URLs API
# ============================================
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
PROCESS_API_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
CATALOG_API_URL = "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"

# ============================================
# CONFIGURACIN IMGENES
# ============================================
MAX_CLOUD_COVER = 100  # Descargar TODAS (incluso días nublados)
BUFFER_KM = 3  # Radio alrededor del volcan (antes 15)

# RGB
IMAGE_WIDTH_RGB = 800
IMAGE_HEIGHT_RGB = 800

# Thermal
IMAGE_WIDTH_THERMAL = 800
IMAGE_HEIGHT_THERMAL = 800

# ============================================
# EVALSCRIPTS
# ============================================
EVALSCRIPT_RGB = """
//VERSION=3
// TRUE COLOR que matchea Copernicus Browser: HighlightCompressVisualizer(0, 0.4).
//
// POR QUE: el gain lineal anterior (sRGB(2.5 * B0x)) clipeaba TODO pixel con
// reflectancia >= 0.40 a blanco puro (255). La nieve refleja 0.5-0.9 en el
// visible -> en dias nevados TODA la nieve se iba a 255 y se perdia la
// morfologia (verificado en Nevados de Chillan 2026-06-11/13). El gain lineal
// no puede a la vez aclarar la tierra oscura y preservar la nieve.
//
// HighlightCompressVisualizer(minVal=0, maxVal=0.4) mapea [0, 0.4] al rango
// brillante con la MISMA pendiente efectiva que el 2.5x (1/0.4 = 2.5), pero los
// valores por encima de 0.4 se COMPRIMEN con una curva suave (no se clipean) ->
// la nieve queda en grises distinguibles, igual que Copernicus Browser. Es el
// evalscript estandar "True color" de EO/Copernicus Browser. minVal/maxVal
// editables si se quiere mas/menos brillo.
let minVal = 0.0;
let maxVal = 0.4;
let viz = new HighlightCompressVisualizer(minVal, maxVal);

function setup() {
  return {
    input: ["B04", "B03", "B02"],
    output: { bands: 3, sampleType: "AUTO" }
  };
}

function evaluatePixel(sample) {
  return viz.processList([sample.B04, sample.B03, sample.B02]);
}
"""

EVALSCRIPT_THERMAL = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["B12", "B11", "B04", "dataMask"]
    }],
    output: {
      bands: 3,
      sampleType: "AUTO"
    }
  };
}

// IMPORTANTE: las composiciones SWIR/false-color se mantienen en espacio LINEAL
// (sin sRGB encoding). Aplicar gamma aplana el contraste termico y las anomalias
// dejan de resaltar. EO Browser usa la misma logica para "SWIR".
function evaluatePixel(sample) {
  return [2.5 * sample.B12, 2.5 * sample.B11, 2.5 * sample.B04];
}
"""

# SWIR_B8A: composite SWIR2 / SWIR1 / NIR-angosto = B12 / B11 / B8A.
# Diferencia con ThermalFalseColor (B12/B11/B04): el 3er canal usa B8A (865 nm,
# 20 m nativo) en vez del rojo visible B04 (665 nm, 10 m). Ventajas:
#   - Las TRES bandas son 20 m -> sin resampling (B04 obliga a remuestrear el SWIR).
#   - B8A separa mejor anomalia termica (rojo, SWIR alto) de vegetacion sana
#     (verde, NIR alto), nieve/hielo (oscuro en SWIR) y agua (oscuro).
# LINEAL como el thermal: aplicar sRGB/gamma aplana el contraste de los pixeles
# rojos de anomalia (lava/fumarola caliente). Misma ganancia 2.5x por consistencia.
EVALSCRIPT_SWIR_B8A = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["B12", "B11", "B8A", "dataMask"]
    }],
    output: {
      bands: 3,
      sampleType: "AUTO"
    }
  };
}

function evaluatePixel(sample) {
  return [2.5 * sample.B12, 2.5 * sample.B11, 2.5 * sample.B8A];
}
"""

# ============================================
# EVALSCRIPTS - ÍNDICES ESPECTRALES (Change Detection)
# ============================================

# NDVI: Normalized Difference Vegetation Index
# Fórmula: (NIR - Red) / (NIR + Red) = (B08 - B04) / (B08 + B04)
# Rango: -1 a 1. Verde = vegetación sana, Rojo/Marrón = suelo/roca/ceniza
# Resolución: 10m (B04 y B08 son 10m)
EVALSCRIPT_NDVI = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B04", "B08", "dataMask"] }],
    output: { bands: 3, sampleType: "AUTO" }
  };
}

function evaluatePixel(sample) {
  let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04 + 0.0001);
  // Paleta: rojo (-1) -> amarillo (0) -> verde (0.5) -> verde oscuro (1)
  if (ndvi < -0.2) return [0.5, 0.0, 0.0];     // Agua/sombra: rojo oscuro
  if (ndvi < 0.0)  return [0.8, 0.2, 0.1];      // Suelo desnudo: rojo
  if (ndvi < 0.1)  return [0.9, 0.5, 0.2];      // Roca/ceniza: naranja
  if (ndvi < 0.2)  return [0.95, 0.8, 0.3];     // Vegetación escasa: amarillo
  if (ndvi < 0.4)  return [0.5, 0.8, 0.2];      // Vegetación moderada: verde claro
  if (ndvi < 0.6)  return [0.2, 0.7, 0.1];      // Vegetación densa: verde
  return [0.0, 0.4, 0.0];                        // Vegetación muy densa: verde oscuro
}
"""

# NBR: Normalized Burn Ratio
# Fórmula: (NIR - SWIR2) / (NIR + SWIR2) = (B08 - B12) / (B08 + B12)
# Rango: -1 a 1. Valores bajos = suelo quemado/calcinado/lava
# Resolución: 20m (B12 es 20m)
EVALSCRIPT_NBR = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B08", "B12", "dataMask"] }],
    output: { bands: 3, sampleType: "AUTO" }
  };
}

function evaluatePixel(sample) {
  let nbr = (sample.B08 - sample.B12) / (sample.B08 + sample.B12 + 0.0001);
  // Paleta: rojo intenso (bajo NBR = quemado) -> amarillo -> verde (alto NBR = sano)
  if (nbr < -0.2) return [0.6, 0.0, 0.3];      // Quemado severo: púrpura
  if (nbr < 0.0)  return [0.9, 0.1, 0.1];       // Quemado/lava: rojo
  if (nbr < 0.1)  return [0.95, 0.4, 0.1];      // Suelo calcinado: naranja
  if (nbr < 0.2)  return [0.95, 0.7, 0.2];      // Suelo expuesto: amarillo
  if (nbr < 0.4)  return [0.7, 0.9, 0.3];       // Vegetación baja: verde amarillo
  if (nbr < 0.6)  return [0.3, 0.7, 0.2];       // Vegetación: verde
  return [0.0, 0.5, 0.0];                        // Vegetación densa: verde oscuro
}
"""

# SWIR Anomaly: Ratio SWIR2/SWIR1 normalizado
# Detecta anomalías térmicas de alta temperatura (fumarolas, flujos activos)
# Valores altos = píxel anormalmente caliente en SWIR2
EVALSCRIPT_SWIR_ANOMALY = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B11", "B12", "dataMask"] }],
    output: { bands: 3, sampleType: "AUTO" }
  };
}

function evaluatePixel(sample) {
  let ratio = (sample.B12 - sample.B11) / (sample.B12 + sample.B11 + 0.0001);
  // Este es esencialmente el NHISWIR de Marchese et al. 2019
  // Valores > 0 indican anomalía térmica (SWIR2 > SWIR1)
  // Paleta: azul (frío/normal) -> blanco (neutro) -> rojo (caliente)
  if (ratio < -0.3) return [0.0, 0.1, 0.5];     // Muy frío: azul oscuro
  if (ratio < -0.1) return [0.1, 0.3, 0.7];     // Frío: azul
  if (ratio < 0.0)  return [0.3, 0.5, 0.8];     // Normal frío: azul claro
  if (ratio < 0.05) return [0.7, 0.7, 0.7];     // Neutro: gris
  if (ratio < 0.1)  return [0.9, 0.7, 0.2];     // Tibio: amarillo
  if (ratio < 0.2)  return [0.95, 0.4, 0.1];    // Caliente: naranja
  return [0.9, 0.1, 0.1];                        // Muy caliente: rojo
}
"""

# SWIR_raw: B11 + B12 en REFLECTANCIA BOA cruda (sin escalado, sin sRGB).
# Salida TIFF float32 de 2 bandas. Imprescindible para calcular VRP REAL
# (Wooster 2003 / Coppola 2016) en Watts, no proxy del PNG ThermalFalseColor.
#
# units: "REFLECTANCE" → valores [0..1] BOA. Para hot pixels saturados (lava
# expuesta a >800 K) la reflectancia aparente puede exceder 1; el sampleType
# FLOAT32 preserva el rango sin clipping.
EVALSCRIPT_SWIR_RAW = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B11", "B12", "dataMask"], units: "REFLECTANCE" }],
    output: { bands: 3, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(s) {
  // B11 = SWIR1 (1.61 µm), B12 = SWIR2 (2.20 µm), banda 3 = dataMask
  return [s.B11, s.B12, s.dataMask];
}
"""

# Mapa de tipos de imagen -> evalscripts
EVALSCRIPTS = {
    'RGB': EVALSCRIPT_RGB,
    'ThermalFalseColor': EVALSCRIPT_THERMAL,
    'SWIR_B8A': EVALSCRIPT_SWIR_B8A,
    'NDVI': EVALSCRIPT_NDVI,
    'NBR': EVALSCRIPT_NBR,
    'SWIR_Anomaly': EVALSCRIPT_SWIR_ANOMALY,
    'SWIR_raw': EVALSCRIPT_SWIR_RAW,
}

# Tipos que se descargan como TIFF float32 (no PNG).
# Para estos se guarda como .npz comprimido por sentinel2_downloader.
TIPOS_RAW_FLOAT32 = {'SWIR_raw'}

# ============================================
# VOLCANES - 43 VOLCANES ACTIVOS
# ============================================

VOLCANES = {
    # ZONA NORTE (8 volcanes)
    "Taapaca": {
        "lat": -18.10922, "lon": -69.50584, "buffer_km": 5.0,
        "id": "354010", "zona": "Norte", "activo": True
    },
    "Parinacota": {
        "lat": -18.17126, "lon": -69.14534, "buffer_km": 2.5,
        "id": "354020", "zona": "Norte", "activo": True
    },
    "Guallatiri": {
        "lat": -18.42781, "lon": -69.08500, "buffer_km": 2.5,
        "id": "354030", "zona": "Norte", "activo": True
    },
    "Isluga": {
        # FIX 2026-06-04: coords y buffer actualizados por revision de colega
        "lat": -19.155746, "lon": -68.834406, "buffer_km": 1.0,
        "id": "355030", "zona": "Norte", "activo": True
    },
    "Irruputuncu": {
        "lat": -20.73329, "lon": -68.56041, "buffer_km": 1.4,
        "id": "355040", "zona": "Norte", "activo": True
    },
    "Ollague": {
        "lat": -21.30685, "lon": -68.17941, "buffer_km": 3.5,
        "id": "355050", "zona": "Norte", "activo": True
    },
    "San Pedro": {
        "lat": -21.88485, "lon": -68.40706, "buffer_km": 4.5,
        "id": "355080", "zona": "Norte", "activo": True
    },
    "Lascar": {
        # FIX 2026-06-04: buffer ajustado por revision de colega (2.8 -> 1.5)
        "lat": -23.36726, "lon": -67.73611, "buffer_km": 1.5,
        "id": "355100", "zona": "Norte", "activo": True
    },

    # ZONA CENTRO (9 volcanes)
    "Tupungatito": {
        "lat": -33.40849, "lon": -69.82181, "buffer_km": 3.5,
        "id": "357010", "zona": "Centro", "activo": True
    },
    "San Jose": {
        "lat": -33.78682, "lon": -69.89732, "buffer_km": 2.5,
        "id": "357020", "zona": "Centro", "activo": True
    },
    "Tinguiririca": {
        "lat": -34.80794, "lon": -70.34917, "buffer_km": 2.8,
        "id": "357030", "zona": "Centro", "activo": True
    },
    "Planchon-Peteroa": {
        "lat": -35.24212, "lon": -70.57189, "buffer_km": 1.3,
        "id": "357040", "zona": "Centro", "activo": True
    },
    "Descabezado Grande": {
        "lat": -35.60431, "lon": -70.74830, "buffer_km": 7.0,
        "id": "357050", "zona": "Centro", "activo": True
    },
    "Tatara-San Pedro": {
        "lat": -35.99755, "lon": -70.84533, "buffer_km": 3.5,
        "id": "357055", "zona": "Centro", "activo": True
    },
    "Laguna del Maule": {
        "lat": -36.07100, "lon": -70.49828, "buffer_km": 9.0,
        "id": "357058", "zona": "Centro", "activo": True
    },
    "Nevado de Longavi": {
        "lat": -36.20001, "lon": -71.17010, "buffer_km": 5.0,
        "id": "357065", "zona": "Centro", "activo": True
    },
    "Nevados de Chillan": {
        # FIX 2026-05-17: coords anteriores (-37.41/-71.35) apuntaban a Antuco.
        # Coord oficial SERNAGEOMIN: -36.870 / -71.380 (Volcán Chillán Nuevo)
        "lat": -36.870, "lon": -71.380, "buffer_km": 3.3,
        "id": "357070", "zona": "Centro", "activo": True
    },

    # ZONA SUR (13 volcanes)
    "Antuco": {
        "lat": -37.41093, "lon": -71.351307, "buffer_km": 3.0,
        "id": "357080", "zona": "Sur", "activo": True
    },
    "Copahue": {
        # FIX 2026-06-04: coords y buffer actualizados por revision de colega
        "lat": -37.858693, "lon": -71.16832, "buffer_km": 1.1,
        "id": "357090", "zona": "Sur", "activo": True
    },
    "Callaqui": {
        "lat": -37.92554, "lon": -71.46113, "buffer_km": 5.0,
        "id": "357095", "zona": "Sur", "activo": True
    },
    "Lonquimay": {
        "lat": -38.38216, "lon": -71.58530, "buffer_km": 3.0,
        "id": "357100", "zona": "Sur", "activo": True
    },
    "Llaima": {
        "lat": -38.71238, "lon": -71.73447, "buffer_km": 4.0,
        "id": "357110", "zona": "Sur", "activo": True
    },
    "Sollipulli": {
        "lat": -38.98103, "lon": -71.51557, "buffer_km": 5.0,
        "id": "357115", "zona": "Sur", "activo": True
    },
    "Villarrica": {
        "lat": -39.420210, "lon": -71.939870, "buffer_km": 1.0,
        "id": "357120", "zona": "Sur", "activo": True
    },
    "Quetrupillan": {
        "lat": -39.53150, "lon": -71.70337, "buffer_km": 8.5,
        "id": "357125", "zona": "Sur", "activo": True
    },
    "Lanin": {
        "lat": -39.637488, "lon": -71.502686, "buffer_km": 4.0,
        "id": "357130", "zona": "Sur", "activo": True
    },
    "Mocho-Choshuenco": {
        "lat": -39.933961, "lon": -72.030398, "buffer_km": 6.0,
        "id": "357135", "zona": "Sur", "activo": True
    },
    "Carran - Los Venados": {
        "lat": -40.37922, "lon": -72.10509, "buffer_km": 6.5,
        "id": "357143", "zona": "Sur", "activo": True
    },
    "Puyehue - Cordon Caulle": {
        "lat": -40.54783, "lon": -72.14826, "buffer_km": 10.0,
        "id": "357150", "zona": "Sur", "activo": True
    },
    "Antillanca - Casablanca": {
        "lat": -40.774523, "lon": -72.171543, "buffer_km": 5.5,
        "id": "357155", "zona": "Sur", "activo": True
    },

    # ZONA AUSTRAL (13 volcanes)
    "Osorno": {
        "lat": -41.10453, "lon": -72.49271, "buffer_km": 4.0,
        "id": "358060", "zona": "Austral", "activo": True
    },
    "Calbuco": {
        "lat": -41.33035, "lon": -72.60399, "buffer_km": 2.5,
        "id": "358070", "zona": "Austral", "activo": True
    },
    "Yate": {
        "lat": -41.78269, "lon": -72.387644, "buffer_km": 5.0,
        "id": "358080", "zona": "Austral", "activo": True
    },
    "Hornopiren": {
        "lat": -41.88132, "lon": -72.43178, "buffer_km": 2.5,
        "id": "358085", "zona": "Austral", "activo": True
    },
    "Huequi": {
        "lat": -42.381420, "lon": -72.582982, "buffer_km": 2.0,
        "id": "358090", "zona": "Austral", "activo": True
    },
    "Michinmahuida": {
        "lat": -42.83733, "lon": -72.43927, "buffer_km": 9.5,
        "id": "358095", "zona": "Austral", "activo": True
    },
    "Chaiten": {
        "lat": -42.83276, "lon": -72.65155, "buffer_km": 2.7,
        "id": "358041", "zona": "Austral", "activo": True
    },
    "Corcovado": {
        "lat": -43.19300, "lon": -72.78979, "buffer_km": 2.5,
        "id": "358100", "zona": "Austral", "activo": True
    },
    "Melimoyu": {
        "lat": -44.074015, "lon": -72.867431, "buffer_km": 7.0,
        "id": "358110", "zona": "Austral", "activo": True
    },
    "Mentolat": {
        "lat": -44.696206, "lon": -73.072694, "buffer_km": 3.0,
        "id": "358120", "zona": "Austral", "activo": True
    },
    "Cay": {
        "lat": -45.07068, "lon": -72.96318, "buffer_km": 3.5,
        "id": "358130", "zona": "Austral", "activo": True
    },
    "Maca": {
        "lat": -45.11210, "lon": -73.16908, "buffer_km": 3.5,
        "id": "358140", "zona": "Austral", "activo": True
    },
    "Hudson": {
        "lat": -45.90915, "lon": -72.96508, "buffer_km": 8.0,
        "id": "358150", "zona": "Austral", "activo": True
    },

    # =====================================================================
    # VISTAS ZOOM ADICIONALES (solicitadas por SERNAGEOMIN)
    # Sub-vistas centradas en zonas de interes especifico de cada volcan.
    # Cada una se procesa como un volcan independiente: descarga, GIFs, PPT.
    # =====================================================================
    "Melimoyu_Conos_Eruptivos": {
        "lat": -44.057878, "lon": -72.786587, "buffer_km": 4.0,
        "id": "358110_zoom1", "zona": "Austral", "activo": True,
        "vista_zoom_de": "Melimoyu",
        "motivo": "Seguimiento de centros eruptivos menores (Conos Suyai, Correntoso y El Sauce)"
    },
    "Mentolat_Sismicidad_VT": {
        "lat": -44.684081, "lon": -73.195247, "buffer_km": 3.5,
        "id": "358120_zoom1", "zona": "Austral", "activo": True,
        "vista_zoom_de": "Mentolat",
        "motivo": "Mayor cluster de sismicidad VT"
    },
    "Hudson_Ultima_Erupcion": {
        "lat": -45.950731, "lon": -72.989386, "buffer_km": 4.0,
        "id": "358150_zoom1", "zona": "Austral", "activo": True,
        "vista_zoom_de": "Hudson",
        "motivo": "Zona ultima erupcion"
    },

    # --- Vistas zoom agregadas 2026-06-04 (revision de colega) ---
    "Lascar_Crater": {
        "lat": -23.362885, "lon": -67.731225, "buffer_km": 0.5,
        "id": "355100_zoom1", "zona": "Norte", "activo": True,
        "vista_zoom_de": "Lascar",
        "motivo": "Crater"
    },
    "Isluga_Crater_Fumarola": {
        "lat": -19.158113, "lon": -68.834894, "buffer_km": 0.55,
        "id": "355030_zoom1", "zona": "Norte", "activo": True,
        "vista_zoom_de": "Isluga",
        "motivo": "Crater y fumarola flanco S"
    },
    "Copahue_Crater_Lake": {
        "lat": -37.855638, "lon": -71.160212, "buffer_km": 0.36,
        "id": "357090_zoom1", "zona": "Sur", "activo": True,
        "vista_zoom_de": "Copahue",
        "motivo": "Lago crater Copahue"
    },

    # --- Vistas zoom agregadas 2026-06-15 (export de revision_volcanes.html) ---
    "Nevados_de_Chillan_Crater_Nicanor": {
        "lat": -36.867211, "lon": -71.377411, "buffer_km": 1.2,
        "id": "357070_zoom1", "zona": "Centro", "activo": True,
        "vista_zoom_de": "Nevados de Chillan",
        "motivo": "Crater Nicanor (vent activo)"
    },
    "Nevado_de_Longavi_Crater": {
        "lat": -36.198067, "lon": -71.164861, "buffer_km": 2.0,
        "id": "357065_zoom1", "zona": "Centro", "activo": True,
        "vista_zoom_de": "Nevado de Longavi",
        "motivo": "Crater"
    },
}

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def get_active_volcanoes():
    """Retorna solo volcanes activos"""
    return {k: v for k, v in VOLCANES.items() if v.get('activo', False)}

def get_image_path(volcano_name, date_str, image_type):
    """Genera path para imagen.

    Para tipos RAW (SWIR_raw) devuelve .npz comprimido (numpy zip) en lugar
    de PNG: los valores son float32 de reflectancia BOA y un PNG 8-bit los
    perdería. .npz es ~50-80 KB por escena y no requiere GDAL/rasterio.
    """
    base_dir = "docs/sentinel2"
    volcano_dir = os.path.join(base_dir, volcano_name)
    os.makedirs(volcano_dir, exist_ok=True)

    if image_type in TIPOS_RAW_FLOAT32:
        filename = f"{date_str}_{image_type}.npz"
    else:
        filename = f"{date_str}_{image_type}.png"
    return os.path.join(volcano_dir, filename)

def get_metadata_path(volcano_name):
    """Genera path para metadata"""
    base_dir = "docs/sentinel2"
    volcano_dir = os.path.join(base_dir, volcano_name)
    os.makedirs(volcano_dir, exist_ok=True)
    return os.path.join(volcano_dir, "metadata.csv")

def validate_credentials():
    """Valida que las credenciales existan"""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError(" ERROR: SH_CLIENT_ID y SH_CLIENT_SECRET deben estar configurados en GitHub Secrets")
    return True

def count_by_zone():
    """Cuenta volcanes por zona"""
    zones = {}
    for v_data in VOLCANES.values():
        zona = v_data.get('zona', 'Sin zona')
        zones[zona] = zones.get(zona, 0) + 1
    return zones

