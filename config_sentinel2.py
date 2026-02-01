"""
CONFIGURACIÓN SENTINEL-2 - VOLCANES CHILE
Credenciales OAuth y configuración de volcanes
"""

import os

# =========================
# CREDENCIALES COPERNICUS
# =========================

# Estas credenciales se cargan desde GitHub Secrets
CLIENT_ID = os.getenv('SH_CLIENT_ID')
CLIENT_SECRET = os.getenv('SH_CLIENT_SECRET')

# OAuth endpoint
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

# =========================
# CONFIGURACIÓN SENTINEL HUB
# =========================

# Endpoints API
SENTINEL_HUB_BASE = "https://sh.dataspace.copernicus.eu"
PROCESS_API_URL = f"{SENTINEL_HUB_BASE}/api/v1/process"

# Catalog API (endpoint diferente)
CATALOG_API_URL = "https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/search.json"

# Parámetros de búsqueda
MAX_CLOUD_COVER = 30  # Máximo 30% de nubes
BUFFER_KM = 3         # Buffer de 3 km alrededor del volcán
RESOLUTION_M = 60     # Resolución 60m por píxel

# MODO SOBRESCRITURA (para pruebas)
MODO_SOBRESCRITURA = True  # True = Sobrescribe imágenes existentes

# Tamaño de imagen
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024

# =========================
# VOLCANES MONITOREADOS
# =========================

VOLCANES = {
    "Villarrica": {
        "lat": -39.42,
        "lon": -71.93,
        "id_mirova": "357120",
        "limite_km": 5.0,
        "region": "Araucanía",
        "activo": True  # Volcán piloto
    },
    "Llaima": {
        "lat": -38.69,
        "lon": -71.73,
        "id_mirova": "357110",
        "limite_km": 5.0,
        "region": "Araucanía",
        "activo": True  # ACTIVADO para pruebas
    },
    "Nevados de Chillan": {
        "lat": -36.86,
        "lon": -71.38,
        "id_mirova": "357070",
        "limite_km": 5.0,
        "region": "Ñuble",
        "activo": False
    },
    "Copahue": {
        "lat": -37.85,
        "lon": -71.17,
        "id_mirova": "357090",
        "limite_km": 4.0,
        "region": "Biobío",
        "activo": False
    },
    "Puyehue-Cordon Caulle": {
        "lat": -40.59,
        "lon": -72.12,
        "id_mirova": "357150",
        "limite_km": 20.0,
        "region": "Los Lagos",
        "activo": False
    },
    "PlanchonPeteroa": {
        "lat": -35.24,
        "lon": -70.57,
        "id_mirova": "357040",
        "limite_km": 3.0,
        "region": "Maule",
        "activo": False
    },
    "Lascar": {
        "lat": -23.37,
        "lon": -67.73,
        "id_mirova": "355100",
        "limite_km": 5.0,
        "region": "Antofagasta",
        "activo": False
    },
    "Lastarria": {
        "lat": -25.17,
        "lon": -68.50,
        "id_mirova": "355120",
        "limite_km": 3.0,
        "region": "Antofagasta",
        "activo": False
    },
    "Isluga": {
        "lat": -19.15,
        "lon": -68.83,
        "id_mirova": "355030",
        "limite_km": 5.0,
        "region": "Tarapacá",
        "activo": False
    },
    "Chaiten": {
        "lat": -42.83,
        "lon": -72.65,
        "id_mirova": "358041",
        "limite_km": 5.0,
        "region": "Los Lagos",
        "activo": False
    }
}

# =========================
# EVALSCRIPTS
# =========================

# Evalscript para composición RGB (color real)
EVALSCRIPT_RGB = """
//VERSION=3
function setup() {
  return {
    input: ["B04", "B03", "B02"],
    output: { bands: 3 }
  };
}

function evaluatePixel(sample) {
  return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
}
"""

# Evalscript para falso color térmico (SWIR)
EVALSCRIPT_THERMAL = """
//VERSION=3
function setup() {
  return {
    input: ["B12", "B11", "B04"],
    output: { bands: 3 }
  };
}

function evaluatePixel(sample) {
  return [2.5 * sample.B12, 2.5 * sample.B11, 2.5 * sample.B04];
}
"""

# =========================
# FUNCIONES AUXILIARES
# =========================

def get_active_volcanoes():
    """Retorna solo volcanes activos"""
    return {k: v for k, v in VOLCANES.items() if v.get('activo', False)}

def get_volcano_config(nombre):
    """Obtiene configuración de un volcán específico"""
    return VOLCANES.get(nombre)

def validate_credentials():
    """Valida que las credenciales estén configuradas"""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError(
            "Credenciales no configuradas. "
            "Debes configurar SH_CLIENT_ID y SH_CLIENT_SECRET en GitHub Secrets."
        )
    return True

# =========================
# PATHS DE ALMACENAMIENTO
# =========================

def get_volcano_path(nombre_volcan):
    """Retorna path base para un volcán"""
    return f"data/sentinel2/{nombre_volcan}"

def get_image_path(nombre_volcan, tipo, fecha):
    """Retorna path completo para una imagen"""
    return f"{get_volcano_path(nombre_volcan)}/{tipo}/{fecha}_{tipo}.png"

def get_metadata_path(nombre_volcan):
    """Retorna path del CSV de metadata"""
    return f"{get_volcano_path(nombre_volcan)}/metadata.csv"
