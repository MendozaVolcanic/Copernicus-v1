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
        "lat": -18.10,
        "lon": -69.50,
        "id": "354010",
        "zona": "Norte",
        "activo": True
    },
    "Parinacota": {
        "lat": -18.17,
        "lon": -69.15,
        "id": "354020",
        "zona": "Norte",
        "activo": True
    },
    "Guallatiri": {
        "lat": -18.42,
        "lon": -69.09,
        "id": "354030",
        "zona": "Norte",
        "activo": True
    },
    "Isluga": {
        "lat": -19.15,
        "lon": -68.83,
        "id": "355030",
        "zona": "Norte",
        "activo": True
    },
    "Irruputuncu": {
        "lat": -20.73,
        "lon": -68.55,
        "id": "355040",
        "zona": "Norte",
        "activo": True
    },
    "Ollague": {
        "lat": -21.30,
        "lon": -68.18,
        "id": "355050",
        "zona": "Norte",
        "activo": True
    },
    "San Pedro": {
        "lat": -21.88,
        "lon": -68.40,
        "id": "355080",
        "zona": "Norte",
        "activo": True
    },
    "Lascar": {
        "lat": -23.37,
        "lon": -67.73,
        "id": "355100",
        "zona": "Norte",
        "activo": True
    },
    
    # ZONA CENTRO (9 volcanes)
    "Tupungatito": {
        "lat": -33.40,
        "lon": -69.80,
        "id": "357010",
        "zona": "Centro",
        "activo": True
    },
    "San Jose": {
        "lat": -33.78,
        "lon": -69.90,
        "id": "357020",
        "zona": "Centro",
        "activo": True
    },
    "Tinguiririca": {
        "lat": -34.81,
        "lon": -70.35,
        "id": "357030",
        "zona": "Centro",
        "activo": True
    },
    "Planchon-Peteroa": {
        "lat": -35.24,
        "lon": -70.57,
        "id": "357040",
        "zona": "Centro",
        "activo": True
    },
    "Descabezado Grande": {
        "lat": -35.58,
        "lon": -70.75,
        "id": "357050",
        "zona": "Centro",
        "activo": True
    },
    "Tatara-San Pedro": {
        "lat": -36.00,
        "lon": -70.80,
        "id": "357055",
        "zona": "Centro",
        "activo": True
    },
    "Laguna del Maule": {
        "lat": -36.02,
        "lon": -70.60,
        "id": "357058",
        "zona": "Centro",
        "activo": True
    },
    "Nevado de Longavi": {
        "lat": -36.19,
        "lon": -71.16,
        "id": "357065",
        "zona": "Centro",
        "activo": True
    },
    "Nevados de Chillan": {
        "lat": -36.86,
        "lon": -71.38,
        "id": "357070",
        "zona": "Centro",
        "activo": True
    },
    
    # ZONA SUR (13 volcanes)
    "Antuco": {
        "lat": -37.41,
        "lon": -71.35,
        "id": "357080",
        "zona": "Sur",
        "activo": True
    },
    "Copahue": {
        "lat": -37.85,
        "lon": -71.17,
        "id": "357090",
        "zona": "Sur",
        "activo": True
    },
    "Callaqui": {
        "lat": -37.92,
        "lon": -71.45,
        "id": "357095",
        "zona": "Sur",
        "activo": True
    },
    "Lonquimay": {
        "lat": -38.38,
        "lon": -71.58,
        "id": "357100",
        "zona": "Sur",
        "activo": True
    },
    "Llaima": {
        "lat": -38.69,
        "lon": -71.73,
        "id": "357110",
        "zona": "Sur",
        "activo": True
    },
    "Sollipulli": {
        "lat": -38.97,
        "lon": -71.52,
        "id": "357115",
        "zona": "Sur",
        "activo": True
    },
    "Villarrica": {
        "lat": -39.42,
        "lon": -71.93,
        "id": "357120",
        "zona": "Sur",
        "activo": True
    },
    "Quetrupillan": {
        "lat": -39.50,
        "lon": -71.70,
        "id": "357125",
        "zona": "Sur",
        "activo": True
    },
    "Lanin": {
        "lat": -39.64,
        "lon": -71.50,
        "id": "357130",
        "zona": "Sur",
        "activo": True
    },
    "Mocho-Choshuenco": {
        "lat": -39.93,
        "lon": -72.03,
        "id": "357135",
        "zona": "Sur",
        "activo": True
    },
    "Carran - Los Venados": {
        "lat": -40.35,
        "lon": -72.07,
        "id": "357143",
        "zona": "Sur",
        "activo": True
    },
    "Puyehue - Cordon Caulle": {
        "lat": -40.59,
        "lon": -72.12,
        "id": "357150",
        "zona": "Sur",
        "activo": True
    },
    "Antillanca - Casablanca": {
        "lat": -40.77,
        "lon": -72.15,
        "id": "357155",
        "zona": "Sur",
        "activo": True
    },
    
    # ZONA AUSTRAL (13 volcanes)
    "Osorno": {
        "lat": -41.10,
        "lon": -72.49,
        "id": "358060",
        "zona": "Austral",
        "activo": True
    },
    "Calbuco": {
        "lat": -41.33,
        "lon": -72.61,
        "id": "358070",
        "zona": "Austral",
        "activo": True
    },
    "Yate": {
        "lat": -41.76,
        "lon": -72.40,
        "id": "358080",
        "zona": "Austral",
        "activo": True
    },
    "Hornopiren": {
        "lat": -41.87,
        "lon": -72.43,
        "id": "358085",
        "zona": "Austral",
        "activo": True
    },
    "Huequi": {
        "lat": -42.38,
        "lon": -72.58,
        "id": "358090",
        "zona": "Austral",
        "activo": True
    },
    "Michinmahuida": {
        "lat": -42.79,
        "lon": -72.44,
        "id": "358095",
        "zona": "Austral",
        "activo": True
    },
    "Chaiten": {
        "lat": -42.83,
        "lon": -72.65,
        "id": "358041",
        "zona": "Austral",
        "activo": True
    },
    "Corcovado": {
        "lat": -43.18,
        "lon": -72.80,
        "id": "358100",
        "zona": "Austral",
        "activo": True
    },
    "Melimoyu": {
        "lat": -44.08,
        "lon": -72.88,
        "id": "358110",
        "zona": "Austral",
        "activo": True
    },
    "Mentolat": {
        "lat": -44.70,
        "lon": -73.08,
        "id": "358120",
        "zona": "Austral",
        "activo": True
    },
    "Cay": {
        "lat": -45.07,
        "lon": -73.00,
        "id": "358130",
        "zona": "Austral",
        "activo": True
    },
    "Maca": {
        "lat": -45.10,
        "lon": -73.17,
        "id": "358140",
        "zona": "Austral",
        "activo": True
    },
    "Hudson": {
        "lat": -45.90,
        "lon": -72.97,
        "id": "358150",
        "zona": "Austral",
        "activo": True
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

# Verificar al importar
if __name__ != "__main__":
    validate_credentials()
