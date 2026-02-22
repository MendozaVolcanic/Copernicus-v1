"""
FIRMS_INTEGRATION.PY
Integración con sistema VIIRS/MODIS existente del usuario
Cross-referencia entre detección Sentinel-2 y anomalías térmicas
"""

import requests
from datetime import datetime, timedelta

# NOTA: Este código usa la API pública de NASA FIRMS
# El usuario ya tiene un sistema VIIRS/MODIS, así que esto es complementario

NASA_FIRMS_API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

def verificar_alertas_firms(volcan, lat, lon, dias_atras=7, api_key=None):
    """
    Consulta NASA FIRMS para anomalías térmicas
    
    Args:
        volcan: Nombre del volcán
        lat: Latitud
        lon: Longitud
        dias_atras: Días hacia atrás para buscar
        api_key: API key de FIRMS (gratis en https://firms.modaps.eosdis.nasa.gov/api/)
    
    Returns:
        dict: {
            'tiene_anomalias': bool,
            'cantidad': int,
            'ultima_fecha': str,
            'max_frp': float  # Fire Radiative Power en MW
        }
    """
    
    # Si no hay API key, retornar sin error
    if not api_key:
        return {
            'tiene_anomalias': False,
            'cantidad': 0,
            'error': 'API_KEY_NO_CONFIGURADA',
            'mensaje': 'Usa tu sistema VIIRS/MODIS existente para confirmación'
        }
    
    # Buffer de 0.1 grados (~10 km)
    bbox = f"{lat-0.1},{lon-0.1},{lat+0.1},{lon+0.1}"
    
    # URL API FIRMS (VIIRS + MODIS)
    url = f"{NASA_FIRMS_API}/{api_key}/VIIRS_SNPP_NRT/{bbox}/{dias_atras}"
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            return {
                'error': f'FIRMS API error: {response.status_code}',
                'tiene_anomalias': False
            }
        
        # Parsear CSV
        lineas = response.text.strip().split('\n')
        
        if len(lineas) <= 1:  # Solo header o vacío
            return {
                'tiene_anomalias': False,
                'cantidad': 0
            }
        
        # Analizar anomalías
        anomalias = []
        
        for linea in lineas[1:]:  # Skip header
            cols = linea.split(',')
            
            if len(cols) < 11:
                continue
            
            try:
                anomalia = {
                    'lat': float(cols[0]),
                    'lon': float(cols[1]),
                    'brightness': float(cols[2]),  # Temperatura de brillo (K)
                    'scan': float(cols[3]),
                    'track': float(cols[4]),
                    'acq_date': cols[5],
                    'acq_time': cols[6],
                    'satellite': cols[7],
                    'confidence': cols[8],
                    'version': cols[9],
                    'frp': float(cols[10])  # Fire Radiative Power (MW)
                }
                
                anomalias.append(anomalia)
            except (ValueError, IndexError):
                continue
        
        if not anomalias:
            return {
                'tiene_anomalias': False,
                'cantidad': 0
            }
        
        # Estadísticas
        max_frp = max(a['frp'] for a in anomalias)
        max_brightness = max(a['brightness'] for a in anomalias)
        ultima_fecha = max(a['acq_date'] for a in anomalias)
        
        return {
            'tiene_anomalias': True,
            'cantidad': len(anomalias),
            'ultima_fecha': ultima_fecha,
            'max_frp': round(max_frp, 2),
            'max_brightness': round(max_brightness, 1),
            'anomalias': anomalias[:5]  # Solo primeras 5
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'tiene_anomalias': False
        }

def cross_reference_sentinel_firms(volcan, lat, lon, cambio_sentinel, api_key=None):
    """
    Cruza detección Sentinel-2 con FIRMS/VIIRS
    
    Args:
        cambio_sentinel: dict resultado de detectar_cambios_significativos()
        api_key: API key opcional de FIRMS
    
    Returns:
        str: 'ALERTA_CRITICA', 'ALERTA_MODERADA', 'SIN_ALERTA'
    """
    
    # Si Sentinel NO detectó cambio, no alertar
    if not cambio_sentinel.get('cambio_detectado'):
        return 'SIN_ALERTA'
    
    porcentaje_cambio = cambio_sentinel['porcentaje_cambio']
    
    # Consultar FIRMS (si API key disponible)
    firms_resultado = verificar_alertas_firms(volcan, lat, lon, dias_atras=7, api_key=api_key)
    
    # Si FIRMS no está configurado o falló, decidir solo con Sentinel
    if firms_resultado.get('error') or not api_key:
        if porcentaje_cambio > 30:
            return 'ALERTA_MODERADA'
        elif porcentaje_cambio > 20:
            return 'ALERTA_MENOR'
        else:
            return 'SIN_ALERTA'
    
    # LÓGICA DE DECISIÓN: Cross-reference
    
    if firms_resultado['tiene_anomalias']:
        # AMBOS sistemas detectan → CRÍTICO
        if porcentaje_cambio > 20:
            return 'ALERTA_CRITICA'
        elif porcentaje_cambio > 15:
            return 'ALERTA_MODERADA'
        else:
            return 'ALERTA_MENOR'
    else:
        # SOLO Sentinel detecta
        if porcentaje_cambio > 35:
            # Cambio muy grande aunque FIRMS no detecte
            return 'ALERTA_MODERADA'
        elif porcentaje_cambio > 25:
            return 'ALERTA_MENOR'
        else:
            return 'SIN_ALERTA'

if __name__ == "__main__":
    """Test de FIRMS"""
    import os
    
    print("="*80)
    print("TEST INTEGRACIÓN NASA FIRMS")
    print("="*80)
    
    # Test con Villarrica
    volcan = "Villarrica"
    lat = -39.42
    lon = -71.93
    
    # Leer API key si existe
    api_key = os.getenv('NASA_FIRMS_API_KEY')
    
    if api_key:
        print(f"\n✅ API Key configurada")
    else:
        print(f"\n⚠️  API Key NO configurada (obténla gratis en https://firms.modaps.eosdis.nasa.gov/api/)")
    
    print(f"\n🔍 Buscando anomalías en {volcan}...")
    
    resultado = verificar_alertas_firms(volcan, lat, lon, dias_atras=7, api_key=api_key)
    
    if resultado.get('error'):
        print(f"   Error: {resultado['error']}")
        if resultado.get('mensaje'):
            print(f"   {resultado['mensaje']}")
    elif resultado['tiene_anomalias']:
        print(f"   ✅ {resultado['cantidad']} anomalías detectadas")
        print(f"   Última: {resultado['ultima_fecha']}")
        print(f"   FRP máximo: {resultado['max_frp']} MW")
    else:
        print(f"   ⚪ Sin anomalías en últimos 7 días")
