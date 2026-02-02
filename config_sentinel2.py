"""
Configuración Sentinel-2 - 44 VOLCANES ACTIVOS
Actualizado para descargar diariamente TODOS los volcanes de Chile
"""

import os
from datetime import datetime, timedelta

# Configuración Copernicus
SH_CLIENT_ID = os.getenv('SH_CLIENT_ID')
SH_CLIENT_SECRET = os.getenv('SH_CLIENT_SECRET')
SH_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
SH_PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"

# Configuración imágenes
BBOX_SIZE_KM = 15  # Buffer 15km alrededor del volcán
TARGET_WIDTH = 800
TARGET_HEIGHT = 800
MAX_CLOUD_COVER = 50  # Máximo 50% nubes

# Configuración temporal
DIAS_HISTORICO = 60  # Mantener últimos 60 días
FECHA_INICIO_DESCARGA = (datetime.now() - timedelta(days=DIAS_HISTORICO)).strftime('%Y-%m-%d')
FECHA_FIN_DESCARGA = datetime.now().strftime('%Y-%m-%d')

# ============================================
# VOLCANES - 44 VOLCANES ACTIVOS
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
    "Ollagüe": {
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
    "Láscar": {
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
    "San José": {
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
    "Planchón-Peteroa": {
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
    "Nevado de Longaví": {
        "lat": -36.19,
        "lon": -71.16,
        "id": "357065",
        "zona": "Centro",
        "activo": True
    },
    "Nevados de Chillán": {
        "lat": -36.86,
        "lon": -71.38,
        "id": "357070",
        "zona": "Centro",
        "activo": True
    },
    
    # ZONA SUR (14 volcanes)
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
    "Quetrupillán": {
        "lat": -39.50,
        "lon": -71.70,
        "id": "357125",
        "zona": "Sur",
        "activo": True
    },
    "Lanín": {
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
    "Carrán - Los Venados": {
        "lat": -40.35,
        "lon": -72.07,
        "id": "357143",
        "zona": "Sur",
        "activo": True
    },
    "Puyehue - Cordón Caulle": {
        "lat": -40.59,
        "lon": -72.12,
        "id": "357150",
        "zona": "Sur",
        "activo": True
    },
    "Antillanca – Casablanca": {
        "lat": -40.77,
        "lon": -72.15,
        "id": "357155",
        "zona": "Sur",
        "activo": True
    },
    
    # ZONA AUSTRAL (12 volcanes - FALTABA UNO)
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
    "Hornopirén": {
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
    "Chaitén": {
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
    "Macá": {
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

def get_active_volcanoes():
    """Retorna solo volcanes activos"""
    return {k: v for k, v in VOLCANES.items() if v.get('activo', False)}

def count_by_zone():
    """Cuenta volcanes por zona"""
    zones = {}
    for v_data in VOLCANES.values():
        zona = v_data.get('zona', 'Sin zona')
        zones[zona] = zones.get(zona, 0) + 1
    return zones
