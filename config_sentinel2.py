"""
Configuracin Sentinel-2 - 43 VOLCANES ACTIVOS
COMPATIBLE con sentinel2_downloader.py existente
"""

import os
from datetime import datetime, timedelta

# ============================================
# CREDENCIALES COPERNICUS (desde env vars)
# ============================================
CLIENT_ID = os.getenv('SH_CLIENT_ID')
CLIENT_SECRET = os.getenv('SH_CLIENT_SECRET')

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
function setup() {
  return {
    input: [{
      bands: ["B04", "B03", "B02", "dataMask"]
    }],
    output: {
      bands: 3,
      sampleType: "AUTO"
    }
  };
}

function evaluatePixel(sample) {
  // IMPORTANTE: Retornar datos AUNQUE dataMask sea 0 (nube/sombra)
  // Esto permite ver las nubes en lugar de pÃ­xeles negros
  return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
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

function evaluatePixel(sample) {
  // IMPORTANTE: Retornar datos AUNQUE dataMask sea 0
  return [2.5 * sample.B12, 2.5 * sample.B11, 2.5 * sample.B04];
}
"""

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
        "lat": -18.17126, "lon": -69.14534, "buffer_km": 3.0,
        "id": "354020", "zona": "Norte", "activo": True
    },
    "Guallatiri": {
        "lat": -18.42781, "lon": -69.08500, "buffer_km": 3.0,
        "id": "354030", "zona": "Norte", "activo": True
    },
    "Isluga": {
        "lat": -19.16737, "lon": -68.82225, "buffer_km": 4.0,
        "id": "355030", "zona": "Norte", "activo": True
    },
    "Irruputuncu": {
        "lat": -20.73329, "lon": -68.56041, "buffer_km": 3.0,
        "id": "355040", "zona": "Norte", "activo": True
    },
    "Ollague": {
        "lat": -21.30685, "lon": -68.17941, "buffer_km": 4.0,
        "id": "355050", "zona": "Norte", "activo": True
    },
    "San Pedro": {
        "lat": -21.88485, "lon": -68.40706, "buffer_km": 5.5,
        "id": "355080", "zona": "Norte", "activo": True
    },
    "Lascar": {
        "lat": -23.36726, "lon": -67.73611, "buffer_km": 3.0,
        "id": "355100", "zona": "Norte", "activo": True
    },

    # ZONA CENTRO (9 volcanes)
    "Tupungatito": {
        "lat": -33.40849, "lon": -69.82181, "buffer_km": 4.0,
        "id": "357010", "zona": "Centro", "activo": True
    },
    "San Jose": {
        "lat": -33.78682, "lon": -69.89732, "buffer_km": 3.0,
        "id": "357020", "zona": "Centro", "activo": True
    },
    "Tinguiririca": {
        "lat": -34.80794, "lon": -70.34917, "buffer_km": 3.5,
        "id": "357030", "zona": "Centro", "activo": True
    },
    "Planchon-Peteroa": {
        "lat": -35.24212, "lon": -70.57189, "buffer_km": 3.0,
        "id": "357040", "zona": "Centro", "activo": True
    },
    "Descabezado Grande": {
        "lat": -35.60431, "lon": -70.74830, "buffer_km": 7.5,
        "id": "357050", "zona": "Centro", "activo": True
    },
    "Tatara-San Pedro": {
        "lat": -35.99755, "lon": -70.84533, "buffer_km": 4.5,
        "id": "357055", "zona": "Centro", "activo": True
    },
    "Laguna del Maule": {
        "lat": -36.07100, "lon": -70.49828, "buffer_km": 10.0,
        "id": "357058", "zona": "Centro", "activo": True
    },
    "Nevado de Longavi": {
        "lat": -36.20001, "lon": -71.17010, "buffer_km": 6.5,
        "id": "357065", "zona": "Centro", "activo": True
    },
    "Nevados de Chillan": {
        "lat": -36.89042, "lon": -71.37554, "buffer_km": 3.5,
        "id": "357070", "zona": "Centro", "activo": True
    },

    # ZONA SUR (13 volcanes)
    "Antuco": {
        "lat": -37.41859, "lon": -71.34097, "buffer_km": 4.5,
        "id": "357080", "zona": "Sur", "activo": True
    },
    "Copahue": {
        "lat": -37.85715, "lon": -71.16836, "buffer_km": 3.0,
        "id": "357090", "zona": "Sur", "activo": True
    },
    "Callaqui": {
        "lat": -37.92554, "lon": -71.46113, "buffer_km": 5.5,
        "id": "357095", "zona": "Sur", "activo": True
    },
    "Lonquimay": {
        "lat": -38.38216, "lon": -71.58530, "buffer_km": 3.5,
        "id": "357100", "zona": "Sur", "activo": True
    },
    "Llaima": {
        "lat": -38.71238, "lon": -71.73447, "buffer_km": 4.5,
        "id": "357110", "zona": "Sur", "activo": True
    },
    "Sollipulli": {
        "lat": -38.98103, "lon": -71.51557, "buffer_km": 5.5,
        "id": "357115", "zona": "Sur", "activo": True
    },
    "Villarrica": {
        "lat": -39.42052, "lon": -71.93939, "buffer_km": 3.0,
        "id": "357120", "zona": "Sur", "activo": True
    },
    "Quetrupillan": {
        "lat": -39.53150, "lon": -71.70337, "buffer_km": 7.0,
        "id": "357125", "zona": "Sur", "activo": True
    },
    "Lanin": {
        "lat": -39.62762, "lon": -71.47923, "buffer_km": 6.0,
        "id": "357130", "zona": "Sur", "activo": True
    },
    "Mocho-Choshuenco": {
        "lat": -39.93439, "lon": -72.00281, "buffer_km": 6.5,
        "id": "357135", "zona": "Sur", "activo": True
    },
    "Carran - Los Venados": {
        "lat": -40.37922, "lon": -72.10509, "buffer_km": 7.0,
        "id": "357143", "zona": "Sur", "activo": True
    },
    "Puyehue - Cordon Caulle": {
        "lat": -40.54783, "lon": -72.14826, "buffer_km": 11.5,
        "id": "357150", "zona": "Sur", "activo": True
    },
    "Antillanca - Casablanca": {
        "lat": -40.76716, "lon": -72.15114, "buffer_km": 6.5,
        "id": "357155", "zona": "Sur", "activo": True
    },

    # ZONA AUSTRAL (13 volcanes)
    "Osorno": {
        "lat": -41.10453, "lon": -72.49271, "buffer_km": 5.0,
        "id": "358060", "zona": "Austral", "activo": True
    },
    "Calbuco": {
        "lat": -41.33035, "lon": -72.60399, "buffer_km": 4.0,
        "id": "358070", "zona": "Austral", "activo": True
    },
    "Yate": {
        "lat": -41.77750, "lon": -72.38678, "buffer_km": 5.5,
        "id": "358080", "zona": "Austral", "activo": True
    },
    "Hornopiren": {
        "lat": -41.88132, "lon": -72.43178, "buffer_km": 3.0,
        "id": "358085", "zona": "Austral", "activo": True
    },
    "Huequi": {
        "lat": -42.38094, "lon": -72.58103, "buffer_km": 3.0,
        "id": "358090", "zona": "Austral", "activo": True
    },
    "Michinmahuida": {
        "lat": -42.83733, "lon": -72.43927, "buffer_km": 9.5,
        "id": "358095", "zona": "Austral", "activo": True
    },
    "Chaiten": {
        "lat": -42.83276, "lon": -72.65155, "buffer_km": 3.0,
        "id": "358041", "zona": "Austral", "activo": True
    },
    "Corcovado": {
        "lat": -43.19300, "lon": -72.78979, "buffer_km": 3.0,
        "id": "358100", "zona": "Austral", "activo": True
    },
    "Melimoyu": {
        "lat": -44.07612, "lon": -72.85073, "buffer_km": 8.5,
        "id": "358110", "zona": "Austral", "activo": True
    },
    "Mentolat": {
        "lat": -44.69272, "lon": -73.07507, "buffer_km": 4.0,
        "id": "358120", "zona": "Austral", "activo": True
    },
    "Cay": {
        "lat": -45.07068, "lon": -72.96318, "buffer_km": 4.5,
        "id": "358130", "zona": "Austral", "activo": True
    },
    "Maca": {
        "lat": -45.11210, "lon": -73.16908, "buffer_km": 4.5,
        "id": "358140", "zona": "Austral", "activo": True
    },
    "Hudson": {
        "lat": -45.90915, "lon": -72.96508, "buffer_km": 10.0,
        "id": "358150", "zona": "Austral", "activo": True
    }
}

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def get_active_volcanoes():
    """Retorna solo volcanes activos"""
    return {k: v for k, v in VOLCANES.items() if v.get('activo', False)}

def get_image_path(volcano_name, date_str, image_type):
    """Genera path para imagen"""
    base_dir = "docs/sentinel2"
    volcano_dir = os.path.join(base_dir, volcano_name)
    os.makedirs(volcano_dir, exist_ok=True)
    
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

