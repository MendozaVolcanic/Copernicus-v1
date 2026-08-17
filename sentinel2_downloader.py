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
    CLIENT_ID, CLIENT_SECRET, CREDENTIAL_SETS, TOKEN_URL,
    PROCESS_API_URL, CATALOG_API_URL,
    MAX_CLOUD_COVER, BUFFER_KM,
    IMAGE_WIDTH_RGB, IMAGE_HEIGHT_RGB,
    IMAGE_WIDTH_THERMAL, IMAGE_HEIGHT_THERMAL,
    EVALSCRIPT_RGB, EVALSCRIPT_THERMAL,
    get_active_volcanoes, get_image_path, get_metadata_path,
    validate_credentials, TIPOS_RAW_FLOAT32
)
import numpy as np

# Importar evalscripts de índices espectrales (change detection)
try:
    from config_sentinel2 import EVALSCRIPTS
except ImportError:
    EVALSCRIPTS = {
        'RGB': EVALSCRIPT_RGB,
        'ThermalFalseColor': EVALSCRIPT_THERMAL,
    }

# Importar compresin
from image_compression import save_compressed

# =========================
# VENTANAS DE TIEMPO (numeros magicos centralizados)
# =========================
# Tres ventanas relacionadas en el pipeline; mantenerlas coherentes:
#   1) DIAS_BUSQUEDA_DEFAULT (60) -> ventana de busqueda hacia atras (--dias).
#      El workflow normal la baja a 15 para limitar el costo de un backfill.
#   2) DIAS_RETENCION (60)        -> imagenes mas viejas que esto se borran
#      (limpiar_imagenes_antiguas). Debe ser >= a la ventana de busqueda para
#      no borrar lo que se acaba de bajar.
#   3) timelapse 30 dias          -> vive en timelapse_generator(_auto).py
#      (NO en este archivo); es la ventana del GIF del dashboard.
# Regla: DIAS_RETENCION >= DIAS_BUSQUEDA_DEFAULT >= ventana del timelapse.
#
# 2026-08-17: 60 -> 45. Nicolas confirma que mas alla de mes y medio no se usa.
# Las dos bajan juntas: dejar la busqueda en 60 con retencion 45 haria bajar
# imagenes para borrarlas en la misma corrida, gastando PU a cambio de nada.
# 45 respeta la regla (45 >= 45 >= 30). Efecto medido sobre el archivo actual:
# docs/sentinel2 pasa de 3.01 GB a 0.84 GB.
DIAS_BUSQUEDA_DEFAULT = 45
DIAS_RETENCION = 45

# Reintentos para errores transitorios (429/503). Distinto del 403-cuota
# (rota cuenta) y del 401 (renueva token).
MAX_REINTENTOS_TRANSITORIO = 3
BACKOFF_BASE_SEG = 2  # backoff exponencial: 2, 4, 8 s

# =========================
# AUTENTICACIN OAUTH2
# =========================

class SentinelHubAuth:
    """OAuth2 con Copernicus + auto-refresh del token + FAILOVER multi-cuenta.

    Mantiene una lista de credenciales (cuenta primaria + backups). Cuando la
    cuenta activa devuelve 403 por PU/creditos agotados, `rotate_account()` pasa
    a la siguiente. Si se agotan TODAS, el caller aborta con SystemExit -> el run
    queda en ROJO (antes el 403 de cuota en la busqueda se tragaba y el job salia
    VERDE con 0 descargas; ver lessons.md).
    """

    def __init__(self, cred_sets=None):
        # cred_sets inyectable para tests; por defecto lee config (env).
        self.cred_sets = list(cred_sets) if cred_sets is not None else list(CREDENTIAL_SETS)
        if not self.cred_sets:
            raise SystemExit(
                "\n[ERROR FATAL] No hay credenciales CDSE. Definir SH_CLIENT_ID y "
                "SH_CLIENT_SECRET (y opcional SH_CLIENT_ID_2/SECRET_2 para failover).\n"
            )
        self.active = 0
        self.client_id, self.client_secret = self.cred_sets[0]
        self.token_url = TOKEN_URL
        self.access_token = None
        self.token_expiry = 0  # timestamp UNIX de expiración

    @staticmethod
    def es_error_cuota(response):
        """True si un 403 es por PU/creditos agotados (no por credenciales malas).

        Distinguir importa: credenciales malas = fail-fast; cuota agotada = rotar
        a la cuenta backup. El cuerpo del 403 de cuota dice "Insufficient
        processing units or requests available...".
        """
        if response is None or getattr(response, 'status_code', None) != 403:
            return False
        try:
            txt = str(response.json()).lower()
        except Exception:
            txt = (getattr(response, 'text', '') or '').lower()
        return any(k in txt for k in ('processing unit', 'insufficient', 'credit', 'quota'))

    def rotate_account(self):
        """Pasa a la proxima cuenta. True si habia otra; False si se agotaron todas."""
        if self.active + 1 < len(self.cred_sets):
            self.active += 1
            self.client_id, self.client_secret = self.cred_sets[self.active]
            self.access_token = None
            self.token_expiry = 0
            print(f"    [FAILOVER] cuenta sin PU -> rotando a cuenta {self.active + 1}/{len(self.cred_sets)}")
            return True
        return False

    def _fetch_token(self):
        """Pide un token nuevo a la API y guarda su expiración"""
        print(f" Autenticando con Copernicus OAuth (cuenta {self.active + 1}/{len(self.cred_sets)})...")

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(self.token_url, data=data, timeout=30)

        # FAIL-FAST en 401/403: credenciales malas para ESTA cuenta. Si hay backup,
        # rotar y reintentar; si se agotaron todas, abortar con error explicito en
        # vez de continuar y "no encontrar imagenes" en silencio (eso hacia que los
        # workflows mostraran SUCCESS aun con auth rota).
        if response.status_code in (401, 403):
            if self.rotate_account():
                return self._fetch_token()
            try:
                err = response.json()
            except Exception:
                err = {}
            mensaje = err.get('error_description', err.get('error', response.text))
            raise SystemExit(
                f"\n[ERROR FATAL] Autenticacion Copernicus fallo ({response.status_code}) en TODAS las cuentas: {mensaje}\n"
                f"  Causa probable: SH_CLIENT_ID/SECRET (y _2, _3...) vencidos, incorrectos o sin PU.\n"
                f"  Accion: revisar GitHub Secrets en Settings -> Secrets and variables -> Actions.\n"
            )
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data['access_token']

        # expires_in suele ser 3600 s; renovamos 5 min antes para tener margen
        expires_in = token_data.get('expires_in', 3600)
        self.token_expiry = time.time() + expires_in - 300  # -5 min de margen

        print(f" Token obtenido (cuenta {self.active + 1}, expira en {expires_in//60} min)")

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
# REINTENTO ANTE ERRORES TRANSITORIOS (429/503)
# =========================

def es_error_transitorio(response):
    """True si la respuesta es un rate-limit/saturacion temporal (429 o 503).

    A diferencia del 403-cuota (rota cuenta) o el 401 (renueva token), un 429/503
    es esperable con varios jobs de matrix en paralelo y se debe REINTENTAR con
    backoff, no tratar como fatal. Antes caia en el `except RequestException` y
    devolvia []/False -> "No hay imagenes" -> volcan salteado sin senal.
    """
    return getattr(response, 'status_code', None) in (429, 503)


def esperar_backoff(response, intento):
    """Duerme respetando Retry-After si viene; si no, backoff exponencial 2/4/8s.

    intento es 0-based (primer reintento -> 2s, segundo -> 4s, tercero -> 8s).
    """
    retry_after = None
    try:
        ra = response.headers.get('Retry-After') if response is not None else None
        if ra is not None:
            retry_after = float(ra)
    except (ValueError, TypeError, AttributeError):
        retry_after = None

    espera = retry_after if retry_after is not None else BACKOFF_BASE_SEG * (2 ** intento)
    status = getattr(response, 'status_code', '?')
    print(f"    [TRANSITORIO {status}] reintento {intento + 1}/{MAX_REINTENTOS_TRANSITORIO} "
          f"tras {espera:.0f}s (rate-limit, no fatal)")
    time.sleep(espera)


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
        import math
        delta_lat = buffer_km / 111.0
        delta_lon = buffer_km / (111.0 * abs(math.cos(math.radians(lat))))

        return {
            "bbox": [
                lon - delta_lon, lat - delta_lat,
                lon + delta_lon, lat + delta_lat
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
        
        # Intentos: 1 normal + 1 por renovacion de token + 1 por cada cuenta backup.
        for intento in range(len(self.auth.cred_sets) + 2):
            try:
                # Reintentos por 429/503 (transitorios) van en un loop interno con
                # backoff: NO consumen el presupuesto de rotacion de cuenta. Solo si
                # se agotan se devuelve [] (vacio = "no encontre", caller lo maneja).
                reintentos_transitorio = 0
                while True:
                    response = requests.get(
                        self.catalog_url,
                        params=params,
                        headers=self.auth.get_headers(),
                        timeout=30
                    )
                    if es_error_transitorio(response) and reintentos_transitorio < MAX_REINTENTOS_TRANSITORIO:
                        esperar_backoff(response, reintentos_transitorio)
                        reintentos_transitorio += 1
                        continue
                    break

                if response.status_code == 401:
                    print(f"    Token expirado en búsqueda (401), renovando...")
                    self.auth.access_token = None
                    self.auth.token_expiry = 0
                    continue

                # 429/503 que sobrevivio a los reintentos: rate-limit/saturacion
                # persistente. Devolver [] (transitorio agotado, no fatal).
                if es_error_transitorio(response):
                    print(f"    [TRANSITORIO {response.status_code}] sin exito tras "
                          f"{MAX_REINTENTOS_TRANSITORIO} reintentos en busqueda")
                    return []

                # 403 por PU/creditos agotados: rotar a la cuenta backup. Si no hay
                # mas cuentas, ABORTAR (run en ROJO). Antes esto caia en el except de
                # abajo y devolvia [] -> "No hay imagenes" -> job VERDE con 0 descargas.
                if SentinelHubAuth.es_error_cuota(response):
                    if self.auth.rotate_account():
                        continue
                    raise SystemExit(
                        "\n[ERROR FATAL] Todas las cuentas CDSE sin PU/creditos (403 en busqueda del catalogo).\n"
                        "  El run queda en ROJO a proposito: una cuenta seca ya no se disfraza de exito.\n"
                        "  Accion: agregar PU/creditos, esperar el reset del dia 1, o cargar otra cuenta\n"
                        "  como secret SH_CLIENT_ID_2 / SH_CLIENT_SECRET_2 (failover automatico).\n"
                    )

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
        import math
        delta_lat = buffer_km / 111.0
        delta_lon = buffer_km / (111.0 * abs(math.cos(math.radians(lat))))
        return [lon - delta_lon, lat - delta_lat, lon + delta_lon, lat + delta_lat]
    
    def download_image(self, lat, lon, fecha, tipo='RGB', output_path=None, buffer_km=BUFFER_KM):
        """Descarga imagen procesada con compresin automtica"""

        bbox = self.create_bbox(lat, lon, buffer_km)
        evalscript = EVALSCRIPTS.get(tipo, EVALSCRIPT_RGB if tipo == 'RGB' else EVALSCRIPT_THERMAL)

        es_raw = tipo in TIPOS_RAW_FLOAT32

        if tipo == 'RGB':
            width = IMAGE_WIDTH_RGB
            height = IMAGE_HEIGHT_RGB
        else:
            # Thermal, NDVI, NBR, SWIR_Anomaly, SWIR_raw usan misma resolución
            width = IMAGE_WIDTH_THERMAL
            height = IMAGE_HEIGHT_THERMAL

        # SWIR_raw: TIFF float32 (reflectancia BOA cruda). El resto: PNG 8-bit.
        output_format = "image/tiff" if es_raw else "image/png"

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
                "responses": [{"identifier": "default", "format": {"type": output_format}}]
            },
            "evalscript": evalscript
        }
        
        # Intentos: 1 normal + 1 por renovacion de token + 1 por cada cuenta backup.
        for intento in range(len(self.auth.cred_sets) + 2):
            try:
                # Reintentos por 429/503 (transitorios) en loop interno con backoff:
                # NO consumen el presupuesto de rotacion de cuenta. Si se agotan, se
                # devuelve False (descarga fallida, caller saltea ese tipo).
                reintentos_transitorio = 0
                while True:
                    response = requests.post(
                        self.process_url,
                        headers=self.auth.get_headers(),
                        json=request_payload,
                        timeout=60
                    )
                    if es_error_transitorio(response) and reintentos_transitorio < MAX_REINTENTOS_TRANSITORIO:
                        esperar_backoff(response, reintentos_transitorio)
                        reintentos_transitorio += 1
                        continue
                    break

                # Si 401, forzar renovación del token y reintentar
                if response.status_code == 401:
                    print(f"    Token expirado (401), renovando...")
                    self.auth.access_token = None  # forzar re-fetch
                    self.auth.token_expiry = 0
                    continue

                # 429/503 que sobrevivio a los reintentos: rate-limit persistente.
                if es_error_transitorio(response):
                    print(f"    [TRANSITORIO {response.status_code}] {tipo}: sin exito tras "
                          f"{MAX_REINTENTOS_TRANSITORIO} reintentos")
                    return False

                # 403 por PU/creditos agotados: rotar a backup o abortar (run ROJO).
                if SentinelHubAuth.es_error_cuota(response):
                    if self.auth.rotate_account():
                        continue
                    raise SystemExit(
                        "\n[ERROR FATAL] Todas las cuentas CDSE sin PU/creditos (403 en descarga Process API).\n"
                        "  Run en ROJO a proposito. Agregar PU/creditos o cargar SH_CLIENT_ID_2/SECRET_2.\n"
                    )

                response.raise_for_status()

                if output_path:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                    if es_raw:
                        # SWIR_raw: TIFF float32 multibanda → npz comprimido (B11, B12, dataMask).
                        # PIL no maneja TIFF multibanda float32; usamos tifffile (dep liviana)
                        # con fallback a numpy + struct si no está disponible.
                        try:
                            import tifffile
                            arr = tifffile.imread(BytesIO(response.content))
                        except ImportError:
                            # Fallback: PIL puede leer TIFF de 1 banda; multibanda no garantizado.
                            # Si tifffile no está, abortamos con mensaje claro.
                            print(f"    [WARN] tifffile no instalado; SWIR_raw requiere `pip install tifffile`")
                            return False

                        # tifffile devuelve shape (H, W, C) o (C, H, W) según el TIFF.
                        # Sentinel Hub Process API entrega (H, W, C).
                        if arr.ndim == 3 and arr.shape[-1] >= 2:
                            b11 = arr[:, :, 0].astype(np.float32)
                            b12 = arr[:, :, 1].astype(np.float32)
                            data_mask = (arr[:, :, 2] > 0.5).astype(np.uint8) if arr.shape[-1] >= 3 else np.ones_like(b11, dtype=np.uint8)
                        elif arr.ndim == 3 and arr.shape[0] >= 2:
                            b11 = arr[0].astype(np.float32)
                            b12 = arr[1].astype(np.float32)
                            data_mask = (arr[2] > 0.5).astype(np.uint8) if arr.shape[0] >= 3 else np.ones_like(b11, dtype=np.uint8)
                        else:
                            print(f"    [WARN] SWIR_raw TIFF shape inesperado: {arr.shape}")
                            return False

                        # Guardar comprimido (.npz con compresión zlib)
                        np.savez_compressed(output_path, B11=b11, B12=b12, dataMask=data_mask)
                        size_mb = os.path.getsize(output_path) / (1024 * 1024)
                        size_original_mb = len(response.content) / (1024 * 1024)
                        print(f"    {tipo}: {size_mb:.2f} MB (TIFF {size_original_mb:.2f}MB -> npz)")
                        return True

                    # PNG normal: comprimir imagen
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
    """Borra imgenes mas viejas que DIAS_RETENCION (ver constantes arriba)"""
    import glob

    ahora = datetime.now(pytz.utc)
    cutoff = ahora - timedelta(days=DIAS_RETENCION)
    cutoff_str = cutoff.strftime('%Y-%m-%d')
    
    print(f"\n Limpiando imgenes anteriores a: {cutoff_str}")
    
    borrados = 0
    
    # FIX: Buscar en estructura correcta docs/sentinel2/{Volcan}/*.png
    carpeta = f"docs/sentinel2/{volcan_nombre}"
    
    if not os.path.exists(carpeta):
        print(f"    Carpeta no existe")
        return 0
    
    for patron in ("*.png", "*.npz"):
        for img_path in glob.glob(f"{carpeta}/{patron}"):
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

def procesar_volcan(nombre_volcan, config, auth, searcher, downloader, dias=DIAS_BUSQUEDA_DEFAULT,
                    sobrescribir=False, tipos=None):
    """Procesa descarga de un volcn.

    sobrescribir: si True, re-descarga aunque el archivo ya exista (--sobrescribir),
                  util tras cambiar un evalscript para re-renderizar lo ya bajado.
    tipos: lista de productos a bajar (ej. ['RGB']). None = los 3 por defecto.

    dias: ventana de busqueda hacia atras (default DIAS_BUSQUEDA_DEFAULT=60). El backfill grande solo
    pasa cuando hay productos faltantes en ese rango; en regimen normal baja la
    fecha del dia. Se baja a 15 via --dias para limitar el costo de un backfill.
    """

    print(f"\n Procesando: {nombre_volcan}")

    lat = config['lat']
    lon = config['lon']
    buffer_km = config.get('buffer_km', BUFFER_KM)

    # Buscar imgenes (ltimos N das)
    hoy = datetime.now(pytz.utc)
    desde = hoy - timedelta(days=dias)

    resultados = searcher.search_images(
        lat, lon,
        start_date=desde.strftime('%Y-%m-%d'),
        end_date=hoy.strftime('%Y-%m-%d'),
        buffer_km=buffer_km
    )
    
    if not resultados:
        print("    No hay imgenes disponibles")
        return None
    
    print(f"    Encontradas {len(resultados)} imgenes")

    # FIX duplicados misma fecha: cuando 2 satelites pasan el mismo dia,
    # nuestros archivos {fecha}_TIPO.png colisionan. Antes el segundo
    # se salteaba arbitrariamente. Ahora elegimos siempre el de MENOR
    # cobertura nubosa (mejor calidad para analisis).
    por_fecha = {}
    for r in resultados:
        f = r['date']
        if f not in por_fecha or r['cloud_cover'] < por_fecha[f]['cloud_cover']:
            por_fecha[f] = r
    if len(por_fecha) < len(resultados):
        descartados = len(resultados) - len(por_fecha)
        print(f"    Duplicados misma fecha (2 satelites): se descarta {descartados}, queda el menos nuboso")
    resultados = sorted(por_fecha.values(), key=lambda x: x['date'], reverse=True)

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
        
        # SWIR_B8A: composite visible B12/B11/B8A (20m nativo).
        # NOTA: SWIR_raw (B11+B12 float32 -> VRP en Watts) se removio a proposito.
        # El VRP calibrado lo hace el proyecto aparte "VRP Chile"; aca no se duplica
        # (ahorra ~1 POST/escena de PU). El evalscript queda en config por si se
        # quiere revivir, pero no se descarga.
        for tipo in (tipos or ['RGB', 'ThermalFalseColor', 'SWIR_B8A']):
            output_path = get_image_path(nombre_volcan, fecha, tipo)

            # Sobrescritura: re-descarga aunque exista (--sobrescribir). Util para
            # re-renderizar tras cambiar un evalscript (ej. nueva curva RGB).
            MODO_SOBRESCRITURA = sobrescribir

            if os.path.exists(output_path) and not MODO_SOBRESCRITURA:
                print(f"    {tipo}: Ya existe")
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
            else:
                exito = downloader.download_image(lat, lon, fecha, tipo, output_path, buffer_km)
                if not exito:
                    continue
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            ext = 'npz' if tipo in TIPOS_RAW_FLOAT32 else 'png'
            todos_resultados.append({
                'fecha': fecha,
                'tipo': tipo,
                'cobertura_nubosa': cloud_cover,
                'sensor': sensor,  # Guarda "Sentinel-2A L2A" en CSV
                'ruta_archivo': f"{fecha}_{tipo}.{ext}",
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
    """Proceso principal.

    Args CLI (opcionales):
      --zona Norte|Centro|Sur|Austral   Filtra a una sola zona (default: todas)
      --volcan <Nombre>                 Filtra a un solo volcan (default: todos)
      --skip-json                       No regenera el JSON de fechas al final
                                        (util cuando varios jobs paralelos
                                        descargan y el job consolidador regenera).
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--zona", choices=["Norte", "Centro", "Sur", "Austral"], default=None)
    parser.add_argument("--volcan", default=None)
    parser.add_argument("--dias", type=int, default=DIAS_BUSQUEDA_DEFAULT,
                        help="Ventana de busqueda hacia atras en dias (default 60). "
                             "Bajar (ej. 15) para limitar el costo de un backfill.")
    parser.add_argument("--sobrescribir", action="store_true",
                        help="Re-descargar aunque el archivo ya exista (tras cambiar un evalscript).")
    parser.add_argument("--tipos", default=None,
                        help="CSV de productos a re-bajar (ej. 'RGB'). Default: los 3 (RGB,ThermalFalseColor,SWIR_B8A).")
    parser.add_argument("--skip-json", action="store_true",
                        help="No regenerar fechas_disponibles_copernicus.json")
    parser.add_argument("--only-json", action="store_true",
                        help="SOLO regenerar JSON desde filesystem y salir (no descarga)")
    parser.add_argument("--only-purga", action="store_true",
                        help="SOLO aplicar la retencion (DIAS_RETENCION) y salir. Para el job "
                             "consolidador: es el unico workspace cuyos borrados se commitean.")
    args = parser.parse_args()
    tipos_lista = [t.strip() for t in args.tipos.split(',') if t.strip()] if args.tipos else None

    # Modo standalone para job consolidador
    if args.only_json:
        print("=== Solo regenerando fechas_disponibles_copernicus.json ===")
        generar_json_fechas_disponibles()
        return

    # Modo standalone de retencion.
    #
    # POR QUE EXISTE: los jobs de zona corren limpiar_imagenes_antiguas() en su
    # propio workspace efimero y lo suben como artifact. Pero download-artifact
    # SUPERPONE archivos --- agrega y sobrescribe, nunca borra --- y el job
    # consolidador parte de un checkout completo donde las imagenes viejas
    # siguen todas ahi. Resultado: los borrados de las zonas jamas llegaban al
    # `git add -A` y la retencion nunca se aplico (3.01 GB acumulados con la
    # politica diciendo 60 dias). Corriendo la purga ACA, en el unico workspace
    # que se commitea, los borrados si quedan staged.
    if args.only_purga:
        print(f"=== Solo aplicando retencion ({DIAS_RETENCION} dias) ===")
        total = 0
        for nombre in get_active_volcanoes().keys():
            total += limpiar_imagenes_antiguas(nombre)
        print(f"\nTotal borrado: {total} archivos")
        return

    print("="*80)
    print(" SENTINEL-2 DOWNLOADER V3.2 - matrix-friendly")
    if args.zona:    print(f" Filtro zona:   {args.zona}")
    if args.volcan:  print(f" Filtro volcan: {args.volcan}")
    if args.skip_json: print(f" Skip JSON regen: si (otro job consolida)")
    print("="*80)

    auth = SentinelHubAuth()
    searcher = SentinelHubSearcher(auth)
    downloader = SentinelHubDownloader(auth)

    volcanes_activos = get_active_volcanoes()

    if args.zona:
        volcanes_activos = {n: c for n, c in volcanes_activos.items()
                            if c.get("zona") == args.zona}
    if args.volcan:
        if args.volcan not in volcanes_activos:
            raise SystemExit(f"Volcan '{args.volcan}' no esta activo o no existe")
        volcanes_activos = {args.volcan: volcanes_activos[args.volcan]}

    if not volcanes_activos:
        print(" No hay volcanes que coincidan con los filtros")
        return

    print(f"\n Volcanes a procesar: {len(volcanes_activos)}")
    print(f" Compresion: lossless")
    print(f" Retencion: {DIAS_RETENCION} dias")
    print(f" Deteccion satelite: 2A/2B/2C L2A")

    import traceback

    total = len(volcanes_activos)
    fallidos = []  # [(nombre, mensaje_error), ...]

    for nombre, config in volcanes_activos.items():
        try:
            resultados = procesar_volcan(nombre, config, auth, searcher, downloader, dias=args.dias,
                                         sobrescribir=args.sobrescribir, tipos=tipos_lista)

            if resultados:
                actualizar_metadata(nombre, resultados)

            # LIMPIEZA AUTOMATICA — FUERA del `if resultados`.
            # Antes estaba dentro: un volcan sin imagenes nuevas ese dia (nublado,
            # sin pasada, o ya deduplicado) no se limpiaba nunca y acumulaba sin
            # techo. En invierno, que es cuando casi ninguna corrida trae nada,
            # la retencion quedaba practicamente apagada.
            limpiar_imagenes_antiguas(nombre)

        # NO atrapamos SystemExit aqui: el fail-fast de auth y el failover de cuota
        # (que abortan con SystemExit) DEBEN propagar para dejar el run en ROJO.
        # SystemExit hereda de BaseException, no de Exception, asi que este except
        # ya lo deja pasar; lo dejamos explicito para que nadie lo "arregle" a
        # `except BaseException` por error.
        except Exception as e:
            # Antes: print + continue silencioso -> un bug real (KeyError de config,
            # error pandas, permiso FS) dejaba el run VERDE con datos faltantes.
            # Ahora se registra el volcan y se sigue, pero queda contado y visible;
            # si fallan demasiados, el run termina en ROJO (ver abajo).
            print(f" [FALLO] {nombre}: {type(e).__name__}: {e}")
            traceback.print_exc()
            fallidos.append((nombre, f"{type(e).__name__}: {e}"))
            continue

    # GENERAR JSON PARA CALENDARIO (saltable si otro job consolida)
    if not args.skip_json:
        generar_json_fechas_disponibles()

    # RESUMEN DE FALLOS: visible siempre. Si fallaron demasiados, run en ROJO.
    if fallidos:
        print("\n" + "="*80)
        print(f" RESUMEN DE FALLOS: {len(fallidos)}/{total} volcanes fallaron")
        print("="*80)
        for nombre, err in fallidos:
            print(f"   - {nombre}: {err}")

        # Umbral: si TODOS fallaron o mas del 50%, el run debe quedar ROJO.
        # Un volcan suelto que falla puede seguir (continue arriba), pero un fallo
        # masivo casi siempre es un bug sistemico (config rota, FS, dependencia)
        # que no debe disfrazarse de exito.
        if len(fallidos) == total or len(fallidos) > total / 2:
            raise SystemExit(
                f"\n[ERROR FATAL] Fallaron {len(fallidos)}/{total} volcanes "
                f"(>50% o todos). El run queda en ROJO a proposito: un fallo masivo "
                f"casi siempre es un bug sistemico (config, FS, dependencia), no un "
                f"volcan suelto. Revisar el detalle de arriba.\n"
            )

    print("\n" + "="*80)
    print(" PROCESO COMPLETADO")
    print("="*80)

if __name__ == "__main__":
    main()
