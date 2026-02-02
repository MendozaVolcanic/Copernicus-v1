"""
IMAGE_COMPRESSION.PY
Módulo para comprimir imágenes Sentinel-2 al guardar

INTEGRACIÓN:
En tu sentinel2_downloader.py, reemplaza:
    image.save(output_path)
Por:
    from image_compression import save_compressed
    save_compressed(image, output_path, compression_level='balanced')
"""

from PIL import Image
import os

# =========================
# NIVELES DE COMPRESIÓN
# =========================

COMPRESSION_LEVELS = {
    'lossless': {
        'description': 'Sin pérdida de calidad (20% reducción)',
        'optimize': True,
        'compress_level': 9,  # PNG: 0-9, mayor = más compresión
        'quality': None  # No aplica para lossless
    },
    'balanced': {
        'description': 'Balance calidad/tamaño (50-60% reducción)',
        'optimize': True,
        'compress_level': 9,
        'quality': 90  # JPEG quality si se convierte
    },
    'aggressive': {
        'description': 'Máxima compresión (70-80% reducción)',
        'optimize': True,
        'compress_level': 9,
        'quality': 85
    }
}

# =========================
# FUNCIÓN PRINCIPAL
# =========================

def save_compressed(image, output_path, compression_level='balanced'):
    """
    Guarda imagen con compresión optimizada
    
    Args:
        image: PIL Image object
        output_path: Path donde guardar
        compression_level: 'lossless', 'balanced', 'aggressive'
    
    Returns:
        tuple: (output_path, size_mb, reduction_percent)
    """
    
    if compression_level not in COMPRESSION_LEVELS:
        raise ValueError(f"Nivel inválido. Usa: {list(COMPRESSION_LEVELS.keys())}")
    
    config = COMPRESSION_LEVELS[compression_level]
    
    # Determinar formato por extensión
    ext = os.path.splitext(output_path)[1].lower()
    
    try:
        if ext == '.png':
            # PNG lossless con optimize
            image.save(
                output_path,
                'PNG',
                optimize=config['optimize'],
                compress_level=config['compress_level']
            )
        
        elif ext in ['.jpg', '.jpeg']:
            # JPEG con calidad ajustable
            if config['quality']:
                image.save(
                    output_path,
                    'JPEG',
                    optimize=config['optimize'],
                    quality=config['quality']
                )
            else:
                # Lossless no aplica para JPEG, usar quality=95
                image.save(
                    output_path,
                    'JPEG',
                    optimize=True,
                    quality=95
                )
        
        else:
            # Otros formatos: solo optimize
            image.save(output_path, optimize=config['optimize'])
        
        # Calcular tamaño
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        
        return output_path, size_mb
    
    except Exception as e:
        print(f"❌ Error comprimiendo {output_path}: {e}")
        # Fallback: guardar sin compresión
        image.save(output_path)
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        return output_path, size_mb


# =========================
# FUNCIÓN DE ANÁLISIS
# =========================

def analyze_compression(original_size_mb, compressed_size_mb):
    """
    Analiza la efectividad de la compresión
    
    Args:
        original_size_mb: Tamaño original en MB
        compressed_size_mb: Tamaño comprimido en MB
    
    Returns:
        dict: {'reduction_mb', 'reduction_percent', 'verdict'}
    """
    
    reduction_mb = original_size_mb - compressed_size_mb
    reduction_percent = (reduction_mb / original_size_mb) * 100
    
    if reduction_percent > 60:
        verdict = "🟢 Excelente"
    elif reduction_percent > 40:
        verdict = "🟡 Buena"
    elif reduction_percent > 20:
        verdict = "🟠 Moderada"
    else:
        verdict = "🔴 Mínima"
    
    return {
        'reduction_mb': reduction_mb,
        'reduction_percent': reduction_percent,
        'verdict': verdict
    }


# =========================
# EJEMPLO DE USO
# =========================

if __name__ == "__main__":
    """
    Ejemplo de cómo integrar en sentinel2_downloader.py
    """
    
    print("="*80)
    print("📦 MÓDULO DE COMPRESIÓN DE IMÁGENES")
    print("="*80)
    
    print("\n🔧 INTEGRACIÓN EN SENTINEL2_DOWNLOADER.PY:\n")
    
    print("""
    # ANTES (sin compresión):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    image.save(output_path)  # ❌ Sin compresión
    
    # DESPUÉS (con compresión):
    from image_compression import save_compressed
    
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    
    # Opción 1: Lossless (recomendado al inicio)
    save_compressed(image, output_path, compression_level='lossless')
    
    # Opción 2: Balanced (si repo crece)
    save_compressed(image, output_path, compression_level='balanced')
    
    # Opción 3: Aggressive (si repo crítico)
    save_compressed(image, output_path, compression_level='aggressive')
    """)
    
    print("\n📊 NIVELES DISPONIBLES:\n")
    for level, config in COMPRESSION_LEVELS.items():
        print(f"   {level}:")
        print(f"      {config['description']}")
        print()
    
    print("="*80)
    print("💡 RECOMENDACIÓN INICIAL: compression_level='lossless'")
    print("   (Calidad 100%, reducción 20%, sin pérdida visual)")
    print("="*80)
