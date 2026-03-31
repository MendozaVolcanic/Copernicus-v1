"""
SENTINEL-2 DOWNLOADER V3.1 - FIX DETECCIÓN SATÉLITE
+ Compresin automtica
+ Limpieza de imgenes >60 das
+ Generacin de JSON para calendario
+ NUEVO: Detección correcta Sentinel-2A/2B/2C con nivel L2A
"""

import requests
import os
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz
import json
from pathlib import Path
from PIL import Image
from io import BytesIO

from config_sentinel2 import (
    CLIENT_ID, CLIENT_SECRET, TOKEN_URL,
    PROCESS_API_URL, CATALOG_API_URL,
    MAX_CLOUD_COVER, BUFFER_KM, 
    IMAGE_WIDTH_RGB, IMAGE_HEIGHT_RGB,
    IMAGE_WIDTH_THERMAL, IMAGE_HEIGHT_THERMAL,
    EVALSCRIPT_RGB, EVALSCRIPT_THERMAL,
    get_active_volcanoes, get_image_path, get_metadata_path,
    validate_credentials
)

# Importar compresin
from image_compression import save_compressed

# =========================
# AUTENTICACIN OAUTH2
# =========================

class SentinelHubAuth:
    """Manejo de autenticacin OAuth2 con Copernicus - con auto-refresh del token"""

    def __init__(self):
        validate_credentials()
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.token_url = TOKEN_URL
        self.access_token = None
        self.token_expiry = 0  # timestamp UNIX de expiración

    def _fetch_token(self):
        """Pide un token nuevo a la API y guarda su expiración"""
        print(" Autenticando con Copernicus OAuth...")

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(self.token_url, data=data, timeout=30)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data['access_token']

        # expires_in suele ser 3600 s; renovamos 5 min antes para tener margen
        expires_in = token_data.get('expires_in', 3600)
        self.token_expiry = time.time() + expires_in - 300  # -5 min de margen

        print(f" Token obtenido (expira en {expires_in//60} min, renovará en {(expires_in-300)//60} min)")

    def get_token(self):
        """Retorna token válido, renovándolo automáticamente si está por vencer"""
        if not self.access_token or time.time() >= self.token_expiry:
            self._fetch_token()
        return self.access_token

    def get_headers(self):
        """Retorna headers HTTP con Bearer token (siempre válido)"""
        token = self.get_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

# =========================
# FUNCIN AUXILIAR DETECCIN SATLITE
# =========================

def detectar_satelite(platform_str):
    """
    Detecta satélite Sentinel-2 desde platform string de la API
    
    FIX V3.1: Ahora detecta correctamente 2A, 2B y 2C
    Incluye nivel de procesamiento L2A en el nombre
    
    Args:
        platform_str: String como "Sentinel-2A", "Sentinel-2B", "Sentinel-2C" 
                     o "sentinel-2a", "SENTINEL-2B", etc.
    
    Returns:
        str: "Sentinel-2A L2A", "Sentinel-2B L2A" o "Sentinel-2C L2A"
    
    Ejemplos:
        >>> detectar_satelite("Sentinel-2A")
        'Sentinel-2A L2A'
        >>> detectar_satelite("sentinel-2c")
        'Sentinel-2C L2A'
    """
    if not platform_str:
        return 'Sentinel-2 L2A (desconocido)'
    
    platform_lower = platform_str.lower()
    
    if 'sentinel-2a' in platform_lower or platform_str.endswith('2A'):
        return 'Sentinel-2A L2A'
    elif 'sentinel-2b' in platform_lower or platform_str.endswith('2B'):
        return 'Sentinel-2B L2A'
    elif 'sentinel-2c' in platform_lower or platform_str.endswith('2C'):
        return 'Sentinel-2C L2A'
    else:
        return 'Sentinel-2 L2A (desconocido)'

# =========================
# BSQUEDA DE IMGENES
# =========================

class SentinelHubSearcher:
    """Bsqueda de productos Sentinel-2 disponibles"""
    
    def __init__(self, auth):
        self.auth = auth
        self.catalog_url = CATALOG_API_URL
    
    def create_bbox(self, lat, lon, buffer_km=BUFFER_KM):
        """Crea bounding box alrededor del volcn"""
        delta = buffer_km / 111.0
        
        return {
            "bbox": [
                lon - delta, lat - delta,
                lon + delta, lat + delta
            ],
            "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
        }
    
    def search_images(self, lat, lon, start_date, end_date, max_cloud=MAX_CLOUD_COVER, buffer_km=BUFFER_KM):
        """Busca imgenes Sentinel-2 en rango de fechas"""

        bbox_data = self.create_bbox(lat, lon, buffer_km)
        
        params = {
            'collections': ['sentinel-2-l2a'],
            'bbox': ','.join(map(str, bbox_data["bbox"])),
            'datetime': f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
            'limit': 50
        }
        
        # Filtro de nubes
        if max_cloud < 100:
            params['query'] = {
                'eo:cloud_cover': {
                    'lte': max_cloud
                }
            }
        
        for intento in range(2):  # 2 intentos: normal + retry si 401
            try:
                response = requests.get(
                    self.catalog_url,
                    params=params,
                    headers=self.auth.get_headers(),
                    timeout=30
                )

                if response.status_code == 401 and intento == 0:
                    print(f"    Token expirado en búsqueda (401), renovando...")
                    self.auth.access_token = None
                    self.auth.token_expiry = 0
                    continue

                response.raise_for_status()

                data = response.json()
                features = data.get('features', [])

                if not features:
                    return []

                results = []
                for feature in features:
                    props = feature['properties']

                    # VALIDACIN: Asegurar que fecha no est vaca
                    fecha = props.get('startDate', props.get('published', props.get('datetime', '')))[:10]

                    if not fecha or len(fecha) != 10:
                        print(f"    Imagen sin fecha vlida, saltando...")
                        continue

                    # FIX V3.1: Usar función detectar_satelite() para 2A/2B/2C
                    results.append({
                        'date': fecha,
                        'cloud_cover': props.get('cloudCover', props.get('eo:cloud_cover', 0)),
                        'sensor': detectar_satelite(props.get('platform', ''))
                    })

                return results

            except requests.exceptions.RequestException as e:
                print(f" Error en bsqueda: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"   Detalle: {e.response.text[:200]}")
                return []

        return []

# =========================
# DESCARGA DE IMGENES
# =========================

class SentinelHubDownloader:
    """Descarga de imgenes procesadas con compresin"""
    
    def __init__(self, auth):
        self.auth = auth
        self.process_url = PROCESS_API_URL
    
    def create_bbox(self, lat, lon, buffer_km=BUFFER_KM):
        """Crea bounding box en formato Process API"""
        delta = buffer_km / 111.0
        return [lon - delta, lat - delta, lon + delta, lat + delta]
    
    def download_image(self, lat, lon, fecha, tipo='RGB', output_path=None, buffer_km=BUFFER_KM):
        """Descarga imagen procesada con compresin automtica"""

        bbox = self.create_bbox(lat, lon, buffer_km)
        evalscript = EVALSCRIPT_RGB if tipo == 'RGB' else EVALSCRIPT_THERMAL
        
        if tipo == 'RGB':
            width = IMAGE_WIDTH_RGB
            height = IMAGE_HEIGHT_RGB
        else:
            width = IMAGE_WIDTH_THERMAL
            height = IMAGE_HEIGHT_THERMAL
        
        request_payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": f"{fecha}T00:00:00Z",
                            "to": f"{fecha}T23:59:59Z"
                        },
                        "maxCloudCoverage": MAX_CLOUD_COVER
                    }
                }]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [{"identifier": "default", "format": {"type": "image/png"}}]
            },
            "evalscript": evalscript
        }
        
        for intento in range(2):  # 2 intentos: normal + retry si 401
            try:
                response = requests.post(
                    self.process_url,
                    headers=self.auth.get_headers(),
                    json=request_payload,
                    timeout=60
                )

                # Si 401, forzar renovación del token y reintentar una vez
                if response.status_code == 401 and intento == 0:
                    print(f"    Token expirado (401), renovando...")
                    self.auth.access_token = None  # forzar re-fetch
                    self.auth.token_expiry = 0
                    continue

                response.raise_for_status()

                if output_path:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                    # Comprimir imagen
                    image = Image.open(BytesIO(response.content))
                    _, size_mb = save_compressed(image, output_path, compression_level='lossless')

                    size_original_mb = len(response.content) / (1024 * 1024)
                    reduccion = ((size_original_mb - size_mb) / size_original_mb) * 100

                    print(f"    {tipo}: {size_mb:.2f} MB ({reduccion:.0f}%)")
                    return True

                return False

            except requests.exceptions.RequestException as e:
                print(f"    Error descarga {tipo}: {e}")

                # Logging detallado del error
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_detail = e.response.json()
                        print(f"       Detalle JSON: {error_detail}")
                    except:
                        print(f"       Detalle texto: {e.response.text[:500]}")

                return False

        return False

# =========================
# LIMPIEZA DE IMGENES ANTIGUAS
# =========================

def limpiar_imagenes_antiguas(volcan_nombre):
    """Borra imgenes >60 das"""
    import glob
    
    ahora = datetime.now(pytz.utc)
    cutoff = ahora - timedelta(days=60)
    cutoff_str = cutoff.strftime('%Y-%m-%d')
    
    print(f"\n Limpiando imgenes anteriores a: {cutoff_str}")
    
    borrados = 0
    
    # FIX: Buscar en estructura correcta docs/sentinel2/{Volcan}/*.png
    carpeta = f"docs/sentinel2/{volcan_nombre}"
    
    if not os.path.exists(carpeta):
        print(f"    Carpeta no existe")
        return 0
    
    for img_path in glob.glob(f"{carpeta}/*.png"):
        nombre = os.path.basename(img_path)
        fecha = nombre.split('_')[0]
        
        if fecha < cutoff_str:
            try:
                os.remove(img_path)
                borrados += 1
            except Exception as e:
                print(f"    Error: {e}")
    
    if borrados > 0:
        print(f"    Borrados: {borrados} archivos")
    else:
        print(f"    No hay archivos antiguos")
    
    return borrados

# =========================
# GENERACIN DE JSON FECHAS
# =========================

def generar_json_fechas_disponibles():
    """Genera JSON para calendario del dashboard"""
    import glob
    
    volcanes_activos = get_active_volcanoes()
    fechas_por_volcan = {}
    
    for volcan_nombre in volcanes_activos.keys():
        # FIX: Buscar directamente en docs/sentinel2/{Volcan}/*.png
        carpeta = f"docs/sentinel2/{volcan_nombre}"
        
        if not os.path.exists(carpeta):
            continue
        
        fechas = []
        # Buscar solo archivos RGB (para no duplicar fechas)
        for img_path in glob.glob(f"{carpeta}/*_RGB.png"):
            nombre = os.path.basename(img_path)
            fecha = nombre.split('_')[0]
            fechas.append(fecha)
        
        fechas_por_volcan[volcan_nombre] = sorted(set(fechas))
    
    # Guardar JSON
    os.makedirs("docs", exist_ok=True)
    output_path = "docs/fechas_disponibles_copernicus.json"
    
    with open(output_path, 'w') as f:
        json.dump(fechas_por_volcan, f, indent=2)
    
    total = sum(len(f) for f in fechas_por_volcan.values())
    print(f"\n JSON fechas generado: {output_path}")
    print(f"   Total fechas: {total}")
    
    return output_path

# =========================
# PROCESO PRINCIPAL
# =========================

def procesar_volcan(nombre_volcan, config, auth, searcher, downloader):
    """Procesa descarga de un volcn"""
    
    print(f"\n Procesando: {nombre_volcan}")
    
    lat = config['lat']
    lon = config['lon']
    buffer_km = config.get('buffer_km', BUFFER_KM)

    # Buscar imgenes (ltimos 60 das)
    hoy = datetime.now(pytz.utc)
    hace_60_dias = hoy - timedelta(days=60)

    resultados = searcher.search_images(
        lat, lon,
        start_date=hace_60_dias.strftime('%Y-%m-%d'),
        end_date=hoy.strftime('%Y-%m-%d'),
        buffer_km=buffer_km
    )
    
    if not resultados:
        print("    No hay imgenes disponibles")
        return None
    
    print(f"    Encontradas {len(resultados)} imgenes")
    
    todos_resultados = []
    
    for resultado in resultados:
        fecha = resultado['date']
        cloud_cover = resultado['cloud_cover']
        sensor = resultado['sensor']  # Ahora incluye "L2A" al final
        
        # VALIDACIN: Saltar si fecha vaca o invlida
        if not fecha or len(fecha) != 10:
            print(f"\n    Saltando resultado con fecha invlida")
            continue
        
        print(f"\n    {fecha} |  {cloud_cover:.1f}% |  {sensor}")
        
        for tipo in ['RGB', 'ThermalFalseColor']:
            output_path = get_image_path(nombre_volcan, fecha, tipo)
            
            # Modo sobrescritura: False por defecto
            MODO_SOBRESCRITURA = False
            
            if os.path.exists(output_path) and not MODO_SOBRESCRITURA:
                print(f"    {tipo}: Ya existe")
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
            else:
                exito = downloader.download_image(lat, lon, fecha, tipo, output_path, buffer_km)
                if not exito:
                    continue
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            todos_resultados.append({
                'fecha': fecha,
                'tipo': tipo,
                'cobertura_nubosa': cloud_cover,
                'sensor': sensor,  # Guarda "Sentinel-2A L2A" en CSV
                'ruta_archivo': f"{fecha}_{tipo}.png",  # FIX: Ruta correcta
                'tamano_mb': round(size_mb, 2)
            })
    
    return todos_resultados

def actualizar_metadata(nombre_volcan, nuevos_datos):
    """Actualiza CSV de metadata"""
    
    metadata_path = get_metadata_path(nombre_volcan)
    
    if os.path.exists(metadata_path):
        df_existente = pd.read_csv(metadata_path)
    else:
        df_existente = pd.DataFrame()
    
    df_nuevos = pd.DataFrame(nuevos_datos)
    df_final = pd.concat([df_existente, df_nuevos], ignore_index=True)
    df_final = df_final.drop_duplicates(subset=['fecha', 'tipo'], keep='last')
    df_final = df_final.sort_values('fecha', ascending=False)
    
    Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(metadata_path, index=False)
    
    print(f"    Metadata: {len(df_final)} registros")

def main():
    """Proceso principal"""
    
    print("="*80)
    print(" SENTINEL-2 DOWNLOADER V3.1 - FIX DETECCIN SATLITE")
    print("="*80)
    
    auth = SentinelHubAuth()
    searcher = SentinelHubSearcher(auth)
    downloader = SentinelHubDownloader(auth)
    
    volcanes_activos = get_active_volcanoes()
    
    if not volcanes_activos:
        print(" No hay volcanes activos")
        return
    
    print(f"\n Volcanes activos: {len(volcanes_activos)}")
    print(f" Compresin: lossless")
    print(f" Retencin: 60 das")
    print(f" Deteccin satlite: 2A/2B/2C L2A")  # ← NUEVO
    
    for nombre, config in volcanes_activos.items():
        try:
            resultados = procesar_volcan(nombre, config, auth, searcher, downloader)
            
            if resultados:
                actualizar_metadata(nombre, resultados)
                
                # LIMPIEZA AUTOMTICA
                limpiar_imagenes_antiguas(nombre)
        
        except Exception as e:
            print(f" Error: {e}")
            continue
    
    # GENERAR JSON PARA CALENDARIO
    generar_json_fechas_disponibles()
    
    print("\n" + "="*80)
    print(" PROCESO COMPLETADO")
    print("="*80)

if __name__ == "__main__":
    main()
