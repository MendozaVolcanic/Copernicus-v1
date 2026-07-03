"""
GIF_CACHE.PY
Sistema de caché para GIFs de timelapses
Evita re-procesar GIFs con el mismo rango de fechas
"""

import os
import hashlib
import json
from datetime import datetime, timedelta

CACHE_DIR = "docs/.cache"
CACHE_INDEX = "docs/.cache/index.json"

def generar_hash_config(volcan, tipo, fecha_inicio, fecha_fin):
    """
    Genera hash único para una configuración de GIF
    
    Args:
        volcan: Nombre del volcán
        tipo: 'RGB' o 'ThermalFalseColor'
        fecha_inicio: 'YYYY-MM-DD'
        fecha_fin: 'YYYY-MM-DD'
    
    Returns:
        str: Hash MD5 de la configuración
    
    Ejemplos:
        >>> generar_hash_config("Villarrica", "RGB", "2026-01-01", "2026-01-31")
        'a3f5c8d9e1b2...'
    """
    config_str = f"{volcan}_{tipo}_{fecha_inicio}_{fecha_fin}"
    return hashlib.md5(config_str.encode()).hexdigest()

def existe_en_cache(volcan, tipo, fecha_inicio, fecha_fin):
    """
    Verifica si existe un GIF en caché para esta configuración
    
    Returns:
        str|None: Path del GIF si existe, None si no
    """
    if not os.path.exists(CACHE_INDEX):
        return None
    
    try:
        with open(CACHE_INDEX, 'r') as f:
            cache_index = json.load(f)
    except:
        return None
    
    hash_config = generar_hash_config(volcan, tipo, fecha_inicio, fecha_fin)
    
    if hash_config in cache_index:
        cached_path = cache_index[hash_config]
        
        # Verificar que el archivo realmente exista
        if os.path.exists(cached_path):
            return cached_path
        else:
            # Entrada inválida, eliminar del índice
            del cache_index[hash_config]
            with open(CACHE_INDEX, 'w') as f:
                json.dump(cache_index, f, indent=2)
    
    return None

def guardar_en_cache(volcan, tipo, fecha_inicio, fecha_fin, gif_path):
    """
    Guarda referencia del GIF en el índice de caché
    
    Args:
        gif_path: Path donde se guardó el GIF
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Cargar índice existente
    if os.path.exists(CACHE_INDEX):
        try:
            with open(CACHE_INDEX, 'r') as f:
                cache_index = json.load(f)
        except:
            cache_index = {}
    else:
        cache_index = {}
    
    # Agregar entrada
    hash_config = generar_hash_config(volcan, tipo, fecha_inicio, fecha_fin)
    cache_index[hash_config] = gif_path
    
    # Guardar índice
    with open(CACHE_INDEX, 'w') as f:
        json.dump(cache_index, f, indent=2)
    
    print(f"    💾 Guardado en caché: {hash_config[:8]}...")

def limpiar_cache_antiguo(dias=90):
    """
    Elimina GIFs en caché más antiguos de X días
    
    Args:
        dias: Edad máxima en días para mantener GIFs
    
    Returns:
        int: Cantidad de GIFs eliminados
    """
    import glob
    
    if not os.path.exists("docs/sentinel2"):
        return 0
    
    ahora = datetime.now()
    cutoff = ahora - timedelta(days=dias)
    
    eliminados = 0
    
    # Limpiar GIFs antiguos en timelapses_ppt/
    for gif_path in glob.glob("docs/sentinel2/*/timelapses_ppt/*.gif"):
        # Extraer fecha del nombre
        nombre = os.path.basename(gif_path)
        # Formato: {Volcan}_{tipo}_{fecha_inicio}_{fecha_fin}.gif
        partes = nombre.replace('.gif', '').split('_')
        
        if len(partes) >= 4:
            fecha_fin_str = partes[-1]
            try:
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
                
                # Si es muy antiguo, eliminar
                if fecha_fin < cutoff:
                    os.remove(gif_path)
                    eliminados += 1
                    print(f"    🗑️  Eliminado GIF antiguo: {nombre}")
            except ValueError:
                # Fecha mal formateada, ignorar
                pass
    
    # Limpiar índice de caché de entradas inválidas
    if os.path.exists(CACHE_INDEX):
        try:
            with open(CACHE_INDEX, 'r') as f:
                cache_index = json.load(f)
            
            # Filtrar solo entradas con archivos existentes
            cache_index_limpio = {
                k: v for k, v in cache_index.items() 
                if os.path.exists(v)
            }
            
            if len(cache_index_limpio) < len(cache_index):
                with open(CACHE_INDEX, 'w') as f:
                    json.dump(cache_index_limpio, f, indent=2)
                
                print(f"    🧹 Índice de caché limpiado: {len(cache_index) - len(cache_index_limpio)} entradas inválidas")
        except:
            pass
    
    return eliminados

def estadisticas_cache():
    """
    Muestra estadísticas del caché
    
    Returns:
        dict: Estadísticas del caché
    """
    if not os.path.exists(CACHE_INDEX):
        return {
            'total_entradas': 0,
            'espacio_total_mb': 0
        }
    
    try:
        with open(CACHE_INDEX, 'r') as f:
            cache_index = json.load(f)
    except:
        return {'total_entradas': 0, 'espacio_total_mb': 0}
    
    # Calcular espacio total
    espacio_total = 0
    entradas_validas = 0
    
    for gif_path in cache_index.values():
        if os.path.exists(gif_path):
            espacio_total += os.path.getsize(gif_path)
            entradas_validas += 1
    
    return {
        'total_entradas': entradas_validas,
        'espacio_total_mb': round(espacio_total / (1024 * 1024), 2)
    }

if __name__ == "__main__":
    """Test del sistema de caché"""
    print("="*80)
    print("SISTEMA DE CACHÉ DE GIFs")
    print("="*80)
    
    stats = estadisticas_cache()
    print(f"\n📊 Estadísticas:")
    print(f"   Entradas en caché: {stats['total_entradas']}")
    print(f"   Espacio total: {stats['espacio_total_mb']} MB")
    
    print("\n🧹 Limpiando caché antiguo...")
    eliminados = limpiar_cache_antiguo(dias=90)
    print(f"   GIFs eliminados: {eliminados}")
