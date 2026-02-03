"""
SENTINEL-2 DOWNLOADER V3.0 COMPLETO
+ Compresión automática
+ Limpieza de imágenes >60 días
+ Generación de JSON para calendario
"""

import requests
import os
import pandas as pd
from datetime import datetime, timedelta
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

# Importar compresión
from image_compression import save_compressed

# =========================
# AUTENTICACIÓN OAUTH2
# =========================

class SentinelHubAuth:
    """Manejo de autenticación OAuth2 con Copernicus"""
    
    def __init__(self):
        validate_credentials()
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.token_url = TOKEN_URL
        self.access_token = None
    
    def get_token(self):
        """Obtiene access token OAuth2"""
        if self.access_token:
            return self.access_token
        
        print("🔐 Autenticando con Copernicus OAuth...")
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(self.token_url, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            print("✅ Autenticación exitosa")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en autenticación: {e}")
            raise
    
    def get_headers(self):
        """Retorna headers HTTP con Bearer token"""
        token = self.get_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

# =========================
# BÚSQUEDA DE IMÁGENES
# =========================

class SentinelHubSearcher:
    """Búsqueda de productos Sentinel-2 disponibles"""
    
    def __init__(self, auth):
        self.auth = auth
        self.catalog_url = CATALOG_API_URL
    
    def create_bbox(self, lat, lon, buffer_km=BUFFER_KM):
        """Crea bounding box alrededor del volcán"""
        delta = buffer_km / 111.0
        
        return {
            "bbox": [
                lon - delta, lat - delta,
                lon + delta, lat + delta
            ],
            "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
        }
    
    def search_images(self, lat, lon, start_date, end_date, max_cloud=MAX_CLOUD_COVER):
        """Busca imágenes Sentinel-2 en rango de fechas"""
        
        bbox_data = self.create_bbox(lat, lon)
        
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
        
        try:
            response = requests.get(
                self.catalog_url,
                params=params,
                headers=self.auth.get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            features = data.get('features', [])
            
            if not features:
                return []
            
            results = []
            for feature in features:
                props = feature['properties']
                
                # VALIDACIÓN: Asegurar que fecha no esté vacía
                fecha = props.get('startDate', props.get('published', props.get('datetime', '')))[:10]
                
                if not fecha or len(fecha) != 10:
                    print(f"   ⚠️ Imagen sin fecha válida, saltando...")
                    continue
                
                results.append({
                    'date': fecha,
                    'cloud_cover': props.get('cloudCover', props.get('eo:cloud_cover', 0)),
                    'sensor': 'Sentinel-2A' if props.get('platform', '').endswith('2A') else 'Sentinel-2B'
                })
            
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en búsqueda: {e}")
            if hasattr(e.response, 'text'):
                print(f"   Detalle: {e.response.text[:200]}")
            return []

# =========================
# DESCARGA DE IMÁGENES
# =========================

class SentinelHubDownloader:
    """Descarga de imágenes procesadas con compresión"""
    
    def __init__(self, auth):
        self.auth = auth
        self.process_url = PROCESS_API_URL
    
    def create_bbox(self, lat, lon, buffer_km=BUFFER_KM):
        """Crea bounding box en formato Process API"""
        delta = buffer_km / 111.0
        return [lon - delta, lat - delta, lon + delta, lat + delta]
    
    def download_image(self, lat, lon, fecha, tipo='RGB', output_path=None):
        """Descarga imagen procesada con compresión automática"""
        
        bbox = self.create_bbox(lat, lon)
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
        
        try:
            response = requests.post(
                self.process_url,
                headers=self.auth.get_headers(),
                json=request_payload,
                timeout=60
            )
            response.raise_for_status()
            
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Comprimir imagen
                image = Image.open(BytesIO(response.content))
                _, size_mb = save_compressed(image, output_path, compression_level='lossless')
                
                size_original_mb = len(response.content) / (1024 * 1024)
                reduccion = ((size_original_mb - size_mb) / size_original_mb) * 100
                
                print(f"   ✅ {tipo}: {size_mb:.2f} MB (↓{reduccion:.0f}%)")
                return True
            
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error descarga {tipo}: {e}")
            
            # Logging detallado del error
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"      🔍 Detalle JSON: {error_detail}")
                except:
                    print(f"      🔍 Detalle texto: {e.response.text[:500]}")
            
            return False

# =========================
# LIMPIEZA DE IMÁGENES ANTIGUAS
# =========================

def limpiar_imagenes_antiguas(volcan_nombre):
    """Borra imágenes >60 días"""
    import glob
    
    ahora = datetime.now(pytz.utc)
    cutoff = ahora - timedelta(days=60)
    cutoff_str = cutoff.strftime('%Y-%m-%d')
    
    print(f"\n🗑️ Limpiando imágenes anteriores a: {cutoff_str}")
    
    borrados = 0
    
    for tipo in ['RGB', 'ThermalFalseColor']:
        carpeta = f"data/sentinel2/{volcan_nombre}/{tipo}"
        
        if not os.path.exists(carpeta):
            continue
        
        for img_path in glob.glob(f"{carpeta}/*.png"):
            nombre = os.path.basename(img_path)
            fecha = nombre.split('_')[0]
            
            if fecha < cutoff_str:
                try:
                    os.remove(img_path)
                    borrados += 1
                except Exception as e:
                    print(f"   ⚠️ Error: {e}")
    
    if borrados > 0:
        print(f"   ✅ Borrados: {borrados} archivos")
    else:
        print(f"   ✅ No hay archivos antiguos")
    
    return borrados

# =========================
# GENERACIÓN DE JSON FECHAS
# =========================

def generar_json_fechas_disponibles():
    """Genera JSON para calendario del dashboard"""
    import glob
    
    volcanes_activos = get_active_volcanoes()
    fechas_por_volcan = {}
    
    for volcan_nombre in volcanes_activos.keys():
        carpeta_rgb = f"data/sentinel2/{volcan_nombre}/RGB"
        
        if not os.path.exists(carpeta_rgb):
            continue
        
        fechas = []
        for img_path in glob.glob(f"{carpeta_rgb}/*.png"):
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
    print(f"\n📅 JSON fechas generado: {output_path}")
    print(f"   Total fechas: {total}")
    
    return output_path

# =========================
# PROCESO PRINCIPAL
# =========================

def procesar_volcan(nombre_volcan, config, auth, searcher, downloader):
    """Procesa descarga de un volcán"""
    
    print(f"\n🌋 Procesando: {nombre_volcan}")
    
    lat = config['lat']
    lon = config['lon']
    
    # Buscar imágenes (últimos 60 días)
    hoy = datetime.now(pytz.utc)
    hace_60_dias = hoy - timedelta(days=60)
    
    resultados = searcher.search_images(
        lat, lon,
        start_date=hace_60_dias.strftime('%Y-%m-%d'),
        end_date=hoy.strftime('%Y-%m-%d')
    )
    
    if not resultados:
        print("   ⚠️ No hay imágenes disponibles")
        return None
    
    print(f"   📅 Encontradas {len(resultados)} imágenes")
    
    todos_resultados = []
    
    for resultado in resultados:
        fecha = resultado['date']
        cloud_cover = resultado['cloud_cover']
        sensor = resultado['sensor']
        
        # VALIDACIÓN: Saltar si fecha vacía o inválida
        if not fecha or len(fecha) != 10:
            print(f"\n   ⚠️ Saltando resultado con fecha inválida")
            continue
        
        print(f"\n   📅 {fecha} | ☁️ {cloud_cover:.1f}% | 🛰️ {sensor}")
        
        for tipo in ['RGB', 'ThermalFalseColor']:
            output_path = get_image_path(nombre_volcan, fecha, tipo)
            
            # Modo sobrescritura: False por defecto
            MODO_SOBRESCRITURA = False
            
            if os.path.exists(output_path) and not MODO_SOBRESCRITURA:
                print(f"   ⏭️ {tipo}: Ya existe")
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
            else:
                exito = downloader.download_image(lat, lon, fecha, tipo, output_path)
                if not exito:
                    continue
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            todos_resultados.append({
                'fecha': fecha,
                'tipo': tipo,
                'cobertura_nubosa': cloud_cover,
                'sensor': sensor,
                'ruta_archivo': f"{tipo}/{fecha}_{tipo}.png",
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
    
    print(f"   💾 Metadata: {len(df_final)} registros")

def main():
    """Proceso principal"""
    
    print("="*80)
    print("🛰️ SENTINEL-2 DOWNLOADER V3.0 AUTOMÁTICO")
    print("="*80)
    
    auth = SentinelHubAuth()
    searcher = SentinelHubSearcher(auth)
    downloader = SentinelHubDownloader(auth)
    
    volcanes_activos = get_active_volcanoes()
    
    if not volcanes_activos:
        print("⚠️ No hay volcanes activos")
        return
    
    print(f"\n📋 Volcanes activos: {len(volcanes_activos)}")
    print(f"📦 Compresión: lossless")
    print(f"🗑️ Retención: 60 días")
    
    for nombre, config in volcanes_activos.items():
        try:
            resultados = procesar_volcan(nombre, config, auth, searcher, downloader)
            
            if resultados:
                actualizar_metadata(nombre, resultados)
                
                # LIMPIEZA AUTOMÁTICA
                limpiar_imagenes_antiguas(nombre)
        
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    # GENERAR JSON PARA CALENDARIO
    generar_json_fechas_disponibles()
    
    print("\n" + "="*80)
    print("✅ PROCESO COMPLETADO")
    print("="*80)

if __name__ == "__main__":
    main()
