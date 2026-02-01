"""
SENTINEL-2 DOWNLOADER
Descarga automática de imágenes RGB y térmicas de volcanes chilenos
"""

import requests
import os
import pandas as pd
from datetime import datetime, timedelta
import pytz
import json
from pathlib import Path
from config_sentinel2 import (
    CLIENT_ID, CLIENT_SECRET, TOKEN_URL,
    PROCESS_API_URL, CATALOG_API_URL,
    MAX_CLOUD_COVER, BUFFER_KM, IMAGE_WIDTH, IMAGE_HEIGHT,
    EVALSCRIPT_RGB, EVALSCRIPT_THERMAL,
    get_active_volcanoes, get_image_path, get_metadata_path,
    validate_credentials
)

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
        # Aproximación: 1 grado ≈ 111 km
        delta = buffer_km / 111.0
        
        return {
            "bbox": [
                lon - delta,  # min_lon
                lat - delta,  # min_lat
                lon + delta,  # max_lon
                lat + delta   # max_lat
            ],
            "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
        }
    
    def search_images(self, lat, lon, start_date, end_date, max_cloud=MAX_CLOUD_COVER):
        """Busca TODAS las imágenes Sentinel-2 disponibles en el rango de fechas"""
        
        bbox_data = self.create_bbox(lat, lon)
        
        # Parámetros para Copernicus Catalog API
        params = {
            'box': ','.join(map(str, bbox_data["bbox"])),
            'startDate': f"{start_date}T00:00:00Z",
            'completionDate': f"{end_date}T23:59:59Z",
            'maxRecords': 50,  # Aumentado para obtener todas las del mes
            'cloudCover': f'[0,{max_cloud}]',
            'sortParam': 'startDate',
            'sortOrder': 'descending',
            'productType': 'S2MSI2A'  # Sentinel-2 L2A
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
            
            # Retornar TODAS las imágenes, no solo la más reciente
            results = []
            for feature in features:
                props = feature['properties']
                results.append({
                    'date': props.get('startDate', props.get('published', ''))[:10],
                    'cloud_cover': props.get('cloudCover', 0),
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
    """Descarga de imágenes procesadas"""
    
    def __init__(self, auth):
        self.auth = auth
        self.process_url = PROCESS_API_URL
    
    def create_bbox(self, lat, lon, buffer_km=BUFFER_KM):
        """Crea bounding box en formato Process API"""
        delta = buffer_km / 111.0
        
        return [
            lon - delta,  # min_lon
            lat - delta,  # min_lat
            lon + delta,  # max_lon
            lat + delta   # max_lat
        ]
    
    def download_image(self, lat, lon, fecha, tipo='RGB', output_path=None):
        """
        Descarga imagen procesada
        
        Args:
            lat, lon: Coordenadas del volcán
            fecha: Fecha en formato YYYY-MM-DD
            tipo: 'RGB' o 'ThermalFalseColor'
            output_path: Path de salida (opcional)
        
        Returns:
            bool: True si descarga exitosa
        """
        
        bbox = self.create_bbox(lat, lon)
        evalscript = EVALSCRIPT_RGB if tipo == 'RGB' else EVALSCRIPT_THERMAL
        
        # Payload para Process API
        request_payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                    }
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{fecha}T00:00:00Z",
                                "to": f"{fecha}T23:59:59Z"
                            },
                            "maxCloudCoverage": MAX_CLOUD_COVER
                        }
                    }
                ]
            },
            "output": {
                "width": IMAGE_WIDTH,
                "height": IMAGE_HEIGHT,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/png"
                        }
                    }
                ]
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
            
            # Guardar imagen
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                # Verificar tamaño
                size_mb = len(response.content) / (1024 * 1024)
                print(f"   ✅ {tipo}: {size_mb:.2f} MB")
                
                return True
            
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error descarga {tipo}: {e}")
            return False

# =========================
# PROCESO PRINCIPAL
# =========================

def procesar_volcan(nombre_volcan, config, auth, searcher, downloader):
    """Procesa descarga de un volcán"""
    
    print(f"\n🌋 Procesando: {nombre_volcan}")
    
    lat = config['lat']
    lon = config['lon']
    
    # Buscar imágenes disponibles (últimos 30 días)
    hoy = datetime.now(pytz.utc)
    hace_30_dias = hoy - timedelta(days=30)
    
    resultados = searcher.search_images(
        lat, lon,
        start_date=hace_30_dias.strftime('%Y-%m-%d'),
        end_date=hoy.strftime('%Y-%m-%d')
    )
    
    if not resultados:
        print("   ⚠️ No hay imágenes disponibles (nubes > 30%)")
        return None
    
    print(f"   📅 Encontradas {len(resultados)} imágenes disponibles")
    
    # Procesar cada fecha
    todos_resultados = []
    
    for resultado in resultados:
        fecha = resultado['date']
        cloud_cover = resultado['cloud_cover']
        sensor = resultado['sensor']
        
        print(f"\n   📅 Procesando: {fecha}")
        print(f"   ☁️ Nubes: {cloud_cover:.1f}%")
        print(f"   🛰️ Sensor: {sensor}")
        
        # Descargar imágenes
        for tipo in ['RGB', 'ThermalFalseColor']:
            output_path = get_image_path(nombre_volcan, tipo, fecha)
            
            # No descargar si ya existe
            if os.path.exists(output_path):
                print(f"   ⏭️ {tipo}: Ya existe")
                
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                todos_resultados.append({
                    'fecha': fecha,
                    'tipo': tipo,
                    'cobertura_nubosa': cloud_cover,
                    'sensor': sensor,
                    'ruta_archivo': f"{tipo}/{fecha}_{tipo}.png",
                    'tamano_mb': round(size_mb, 2)
                })
                continue
            
            # Descargar
            exito = downloader.download_image(lat, lon, fecha, tipo, output_path)
            
            if exito:
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
    
    # Cargar CSV existente
    if os.path.exists(metadata_path):
        df_existente = pd.read_csv(metadata_path)
    else:
        df_existente = pd.DataFrame()
    
    # Agregar nuevos datos
    df_nuevos = pd.DataFrame(nuevos_datos)
    df_final = pd.concat([df_existente, df_nuevos], ignore_index=True)
    
    # Eliminar duplicados (misma fecha + tipo)
    df_final = df_final.drop_duplicates(subset=['fecha', 'tipo'], keep='last')
    
    # Ordenar por fecha DESC
    df_final = df_final.sort_values('fecha', ascending=False)
    
    # Guardar
    Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(metadata_path, index=False)
    
    print(f"   💾 Metadata actualizado: {len(df_final)} registros")

def main():
    """Proceso principal"""
    
    print("="*80)
    print("🛰️ SENTINEL-2 DOWNLOADER - INICIO")
    print("="*80)
    
    # Autenticación
    auth = SentinelHubAuth()
    searcher = SentinelHubSearcher(auth)
    downloader = SentinelHubDownloader(auth)
    
    # Procesar solo volcanes activos
    volcanes_activos = get_active_volcanoes()
    
    if not volcanes_activos:
        print("⚠️ No hay volcanes activos configurados")
        return
    
    print(f"\n📋 Volcanes activos: {len(volcanes_activos)}")
    
    # Procesar cada volcán
    for nombre, config in volcanes_activos.items():
        try:
            resultados = procesar_volcan(nombre, config, auth, searcher, downloader)
            
            if resultados:
                actualizar_metadata(nombre, resultados)
        
        except Exception as e:
            print(f"❌ Error procesando {nombre}: {e}")
            continue
    
    print("\n" + "="*80)
    print("✅ PROCESO COMPLETADO")
    print("="*80)

if __name__ == "__main__":
    main()
