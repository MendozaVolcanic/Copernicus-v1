"""
CHANGE_DETECTOR.PY
Detecta cambios significativos entre imágenes Sentinel-2
Análisis diferencial de píxeles para identificar cambios morfológicos
"""

import numpy as np
from PIL import Image
import os
import glob

def detectar_cambios_significativos(volcan, fecha_nueva, fecha_anterior, tipo='ThermalFalseColor'):
    """
    Compara 2 imágenes y detecta cambios significativos
    
    Args:
        volcan: Nombre del volcán
        fecha_nueva: 'YYYY-MM-DD' (más reciente)
        fecha_anterior: 'YYYY-MM-DD' (referencia)
        tipo: 'RGB' o 'ThermalFalseColor'
    
    Returns:
        dict: {
            'cambio_detectado': bool,
            'porcentaje_cambio': float,
            'tipo_cambio': str,
            'fecha_nueva': str,
            'fecha_anterior': str,
            'volcan': str
        }
    """
    
    # Construir paths
    img_nueva_path = f"docs/sentinel2/{volcan}/{fecha_nueva}_{tipo}.png"
    img_anterior_path = f"docs/sentinel2/{volcan}/{fecha_anterior}_{tipo}.png"
    
    # Verificar que existan
    if not os.path.exists(img_nueva_path):
        return {'cambio_detectado': False, 'error': f'Imagen nueva no encontrada: {fecha_nueva}'}
    
    if not os.path.exists(img_anterior_path):
        return {'cambio_detectado': False, 'error': f'Imagen anterior no encontrada: {fecha_anterior}'}
    
    # Cargar imágenes
    try:
        img_nueva = Image.open(img_nueva_path).convert('RGB')
        img_anterior = Image.open(img_anterior_path).convert('RGB')
    except Exception as e:
        return {'cambio_detectado': False, 'error': f'Error cargando imágenes: {e}'}
    
    # Convertir a arrays numpy
    arr_nueva = np.array(img_nueva)
    arr_anterior = np.array(img_anterior)
    
    # Verificar que tengan mismo tamaño
    if arr_nueva.shape != arr_anterior.shape:
        return {'cambio_detectado': False, 'error': 'Imágenes con diferentes dimensiones'}
    
    # ANÁLISIS 1: Diferencia absoluta
    diferencia = np.abs(arr_nueva.astype(float) - arr_anterior.astype(float))
    
    # ANÁLISIS 2: Cambio porcentual
    # Considerar solo píxeles con cambio > umbral (evitar ruido atmosférico)
    UMBRAL_PIXEL = 30  # Diferencia mínima por píxel (0-255)
    
    # Máscara de píxeles cambiados
    mascara_cambio = diferencia > UMBRAL_PIXEL
    
    # Contar píxeles cambiados (en cualquier canal)
    pixeles_cambiados = np.sum(np.any(mascara_cambio, axis=2))
    total_pixeles = arr_nueva.shape[0] * arr_nueva.shape[1]
    
    porcentaje_cambio = (pixeles_cambiados / total_pixeles) * 100
    
    # ANÁLISIS 3: Clasificación del cambio según tipo de imagen
    if tipo == 'ThermalFalseColor':
        # Para thermal: analizar canal rojo (B12 - SWIR2 - sensible a calor)
        diff_rojo = diferencia[:,:,0]
        cambio_calor_medio = np.mean(diff_rojo)
        cambio_calor_max = np.max(diff_rojo)
        
        if cambio_calor_max > 100:
            tipo_cambio = "ANOMALÍA TÉRMICA FUERTE"
        elif cambio_calor_medio > 40:
            tipo_cambio = "ANOMALÍA TÉRMICA MODERADA"
        elif porcentaje_cambio > 20:
            tipo_cambio = "CAMBIO MORFOLÓGICO MAYOR"
        elif porcentaje_cambio > 10:
            tipo_cambio = "CAMBIO MORFOLÓGICO MENOR"
        else:
            tipo_cambio = "CAMBIO NORMAL"
    else:
        # Para RGB: analizar cambios morfológicos generales
        if porcentaje_cambio > 25:
            tipo_cambio = "CAMBIO MORFOLÓGICO MAYOR"
        elif porcentaje_cambio > 15:
            tipo_cambio = "CAMBIO MODERADO"
        elif porcentaje_cambio > 8:
            tipo_cambio = "CAMBIO MENOR"
        else:
            tipo_cambio = "CAMBIO NORMAL"
    
    # DECISIÓN: ¿Es significativo?
    UMBRAL_SIGNIFICATIVO = 15  # % de cambio
    
    cambio_detectado = porcentaje_cambio > UMBRAL_SIGNIFICATIVO
    
    return {
        'cambio_detectado': cambio_detectado,
        'porcentaje_cambio': round(porcentaje_cambio, 2),
        'tipo_cambio': tipo_cambio,
        'fecha_nueva': fecha_nueva,
        'fecha_anterior': fecha_anterior,
        'volcan': volcan,
        'tipo_imagen': tipo
    }

def analizar_serie_temporal(volcan, dias_atras=30, tipo='ThermalFalseColor'):
    """
    Analiza serie temporal completa para detectar tendencias
    
    Args:
        volcan: Nombre del volcán
        dias_atras: Cuántas imágenes atrás analizar
        tipo: 'RGB' o 'ThermalFalseColor'
    
    Returns:
        list: Lista de cambios detectados ordenados por severidad
    """
    
    # Obtener todas las imágenes del tipo especificado
    patron = f"docs/sentinel2/{volcan}/*_{tipo}.png"
    imagenes = sorted(glob.glob(patron))
    
    if len(imagenes) < 2:
        print(f"    ⚠️  Menos de 2 imágenes {tipo} disponibles")
        return []
    
    # Tomar la más reciente
    fecha_mas_reciente = os.path.basename(imagenes[-1]).split('_')[0]
    
    print(f"    📅 Fecha más reciente: {fecha_mas_reciente}")
    
    cambios_detectados = []
    
    # Comparar con imágenes anteriores (últimas N)
    imagenes_a_comparar = imagenes[-min(10, len(imagenes)):-1]  # Últimas 9 imágenes
    
    for img_path in imagenes_a_comparar:
        fecha_anterior = os.path.basename(img_path).split('_')[0]
        
        resultado = detectar_cambios_significativos(
            volcan,
            fecha_mas_reciente,
            fecha_anterior,
            tipo=tipo
        )
        
        if resultado.get('error'):
            continue
        
        if resultado['cambio_detectado']:
            cambios_detectados.append(resultado)
            print(f"       🔍 vs {fecha_anterior}: {resultado['porcentaje_cambio']:.1f}% - {resultado['tipo_cambio']}")
    
    # Ordenar por porcentaje de cambio (mayor primero)
    cambios_detectados.sort(key=lambda x: x['porcentaje_cambio'], reverse=True)
    
    return cambios_detectados

def obtener_cambio_maximo(volcan):
    """
    Encuentra el cambio más significativo para un volcán
    
    Returns:
        dict|None: Cambio más significativo o None
    """
    # Analizar con Thermal (más sensible a anomalías)
    cambios = analizar_serie_temporal(volcan, dias_atras=30, tipo='ThermalFalseColor')
    
    if cambios:
        return cambios[0]  # El más significativo
    
    return None

if __name__ == "__main__":
    """Test del detector de cambios"""
    import sys
    
    if len(sys.argv) > 1:
        volcan_test = sys.argv[1]
    else:
        volcan_test = "Villarrica"
    
    print("="*80)
    print(f"TEST DETECTOR DE CAMBIOS: {volcan_test}")
    print("="*80)
    
    cambios = analizar_serie_temporal(volcan_test, dias_atras=30)
    
    if cambios:
        print(f"\n✅ {len(cambios)} cambios significativos detectados")
        print("\nTop 3:")
        for i, cambio in enumerate(cambios[:3], 1):
            print(f"  {i}. {cambio['fecha_anterior']} → {cambio['fecha_nueva']}")
            print(f"     Cambio: {cambio['porcentaje_cambio']}%")
            print(f"     Tipo: {cambio['tipo_cambio']}")
    else:
        print("\n⚠️  No se detectaron cambios significativos")
