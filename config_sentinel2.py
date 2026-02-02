"""
CONFIG_SENTINEL2.PY - CONFIGURACIÓN ACTUALIZADA
+ Límite 2 meses para imágenes
+ Limpieza automática de imágenes antiguas
"""

import os
from datetime import datetime, timedelta
import pytz

# =========================
# CREDENCIALES COPERNICUS
# =========================

CLIENT_ID = os.getenv('SH_CLIENT_ID')
CLIENT_SECRET = os.getenv('SH_CLIENT_SECRET')

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
PROCESS_API_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
CATALOG_API_URL = "https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/search.json"

def validate_credentials():
    """Valida que las credenciales estén configuradas"""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError(
            "⚠️ Credenciales no configuradas.\n"
            "Configura SH_CLIENT_ID y SH_CLIENT_SECRET en GitHub Secrets"
        )

# =========================
# PARÁMETROS DE DESCARGA
# =========================

MAX_CLOUD_COVER = 30  # Máximo % de nubes
BUFFER_KM = 3  # Buffer alrededor del volcán (km)

# Tamaños de imagen
IMAGE_WIDTH_RGB = 1024
IMAGE_HEIGHT_RGB = 1024
IMAGE_WIDTH_THERMAL = 512
IMAGE_HEIGHT_THERMAL = 512

IMAGE_WIDTH = IMAGE_WIDTH_RGB
IMAGE_HEIGHT = IMAGE_HEIGHT_RGB

# ========================================
# NUEVO: LÍMITE DE RETENCIÓN
# ========================================
RETENTION_DAYS = 60  # Solo mantener últimos 60 días (2 meses)

def get_retention_cutoff_date():
    """Retorna fecha límite para borrar imágenes antiguas"""
    ahora = datetime.now(pytz.utc)
    cutoff = ahora - timedelta(days=RETENTION_DAYS)
    return cutoff.strftime('%Y-%m-%d')

# =========================
# VOLCANES MONITOREADOS
# =========================

VOLCANES = {
    "Villarrica": {
        "lat": -39.42,
        "lon": -71.93,
        "id": "357120",
        "activo": True
    },
    "Llaima": {
        "lat": -38.69,
        "lon": -71.73,
        "id": "357110",
        "activo": True
    },
    "Nevados de Chillán": {
        "lat": -36.86,
        "lon": -71.38,
        "id": "357070",
        "activo": False
    },
    "Copahue": {
        "lat": -37.85,
        "lon": -71.17,
        "id": "357090",
        "activo": False
    },
    # ... resto de volcanes
}

def get_active_volcanoes():
    """Retorna solo volcanes activos"""
    return {k: v for k, v in VOLCANES.items() if v.get('activo', False)}

# =========================
# EVALSCRIPTS
# =========================

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
# PATHS
# =========================

def get_image_path(volcan_nombre, tipo, fecha):
    """Retorna path para guardar imagen"""
    return f"data/sentinel2/{volcan_nombre}/{tipo}/{fecha}_{tipo}.png"

def get_metadata_path(volcan_nombre):
    """Retorna path del CSV de metadata"""
    return f"data/sentinel2/{volcan_nombre}/metadata.csv"

def get_timelapse_path(volcan_nombre, tipo, fecha_inicio, fecha_fin):
    """Retorna path para GIF timelapse"""
    return f"data/sentinel2/{volcan_nombre}/timelapses/{volcan_nombre}_{tipo}_{fecha_inicio}_{fecha_fin}.gif"

# =========================
# MODO SOBRESCRITURA
# =========================

MODO_SOBRESCRITURA = False  # False en producción, True para pruebas

# ========================================
# NUEVO: LIMPIEZA DE IMÁGENES ANTIGUAS
# ========================================

def limpiar_imagenes_antiguas(volcan_nombre):
    """
    Borra imágenes con fecha > RETENTION_DAYS días atrás
    Mantiene solo últimos 2 meses
    """
    import glob
    from pathlib import Path
    
    cutoff_date = get_retention_cutoff_date()
    print(f"\n🗑️ Limpiando imágenes anteriores a: {cutoff_date}")
    
    borrados = 0
    
    for tipo in ['RGB', 'ThermalFalseColor']:
        carpeta = f"data/sentinel2/{volcan_nombre}/{tipo}"
        
        if not os.path.exists(carpeta):
            continue
        
        imagenes = glob.glob(f"{carpeta}/*.png")
        
        for img_path in imagenes:
            # Extraer fecha del nombre: YYYY-MM-DD_tipo.png
            nombre = os.path.basename(img_path)
            fecha = nombre.split('_')[0]
            
            if fecha < cutoff_date:
                try:
                    os.remove(img_path)
                    borrados += 1
                    print(f"   🗑️ Borrado: {nombre}")
                except Exception as e:
                    print(f"   ⚠️ Error borrando {nombre}: {e}")
    
    if borrados > 0:
        print(f"   ✅ Total borrados: {borrados} archivos")
    else:
        print(f"   ✅ No hay archivos antiguos para borrar")
    
    return borrados


# ========================================
# NUEVO: GENERAR fechas_disponibles_copernicus.json
# ========================================

def generar_json_fechas_disponibles():
    """
    Genera JSON con fechas disponibles para el calendario
    Se ejecuta después de cada descarga
    """
    import json
    import glob
    
    fechas_por_volcan = {}
    
    volcanes_activos = get_active_volcanoes()
    
    for volcan_nombre in volcanes_activos.keys():
        carpeta_rgb = f"data/sentinel2/{volcan_nombre}/RGB"
        
        if not os.path.exists(carpeta_rgb):
            continue
        
        imagenes = glob.glob(f"{carpeta_rgb}/*.png")
        fechas = []
        
        for img_path in imagenes:
            nombre = os.path.basename(img_path)
            fecha = nombre.split('_')[0]  # YYYY-MM-DD
            fechas.append(fecha)
        
        fechas_por_volcan[volcan_nombre] = sorted(set(fechas))
    
    # Guardar JSON
    output_path = "docs/fechas_disponibles_copernicus.json"
    os.makedirs("docs", exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(fechas_por_volcan, f, indent=2)
    
    print(f"\n📅 JSON fechas generado: {output_path}")
    
    total_fechas = sum(len(f) for f in fechas_por_volcan.values())
    print(f"   Total fechas: {total_fechas}")
    
    return output_path
