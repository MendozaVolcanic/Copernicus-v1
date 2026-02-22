"""
GIF_OPTIMIZER.PY
Compresión inteligente de GIFs basada en análisis de complejidad visual
Optimiza tamaño manteniendo calidad según contenido de la imagen
"""

from PIL import Image
import numpy as np
import os

def analizar_complejidad_visual(imagenes):
    """
    Analiza la variación de colores en las imágenes
    
    Args:
        imagenes: Lista de PIL Images
    
    Returns:
        float: Índice de complejidad 0.0-1.0
               0.0 = Muy uniforme (nubes blancas)
               1.0 = Muy detallado (terreno variado)
    
    Método:
        Calcula la desviación estándar de los valores RGB
        Alta desviación = muchos colores diferentes = alta complejidad
        Baja desviación = colores uniformes = baja complejidad
    """
    if not imagenes or len(imagenes) == 0:
        return 0.5  # Valor por defecto
    
    # Analizar primeros 3 frames (representativo del GIF)
    muestras = imagenes[:min(3, len(imagenes))]
    
    variaciones = []
    
    for img in muestras:
        # Convertir a RGB si es necesario
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Convertir a array numpy
        arr = np.array(img)
        
        # Calcular desviación estándar de cada canal
        std_r = np.std(arr[:,:,0])
        std_g = np.std(arr[:,:,1])
        std_b = np.std(arr[:,:,2])
        
        # Promedio de variación
        variacion = (std_r + std_g + std_b) / 3.0
        variaciones.append(variacion)
    
    # Promedio de todas las muestras
    variacion_promedio = np.mean(variaciones)
    
    # Normalizar a rango 0-1
    # Típicamente std está en rango 0-100
    complejidad = min(variacion_promedio / 100.0, 1.0)
    
    return complejidad

def calcular_parametros_compresion(imagenes, target_mb=1.2):
    """
    Calcula parámetros óptimos de compresión según complejidad
    
    Args:
        imagenes: Lista de PIL Images
        target_mb: Tamaño objetivo en MB
    
    Returns:
        dict: {
            'colors': int,      # Número de colores en paleta
            'quality': int,     # Calidad JPEG/GIF
            'scale': float,     # Factor de escala (1.0 = sin cambio)
            'modo': str         # Descripción del modo
        }
    """
    complejidad = analizar_complejidad_visual(imagenes)
    
    print(f"    📊 Complejidad visual: {complejidad:.2f}")
    
    # ESTRATEGIA DE COMPRESIÓN POR COMPLEJIDAD
    
    if complejidad > 0.8:
        # ALTA COMPLEJIDAD: Terreno muy detallado, lava, flujos
        params = {
            'colors': 256,      # Paleta completa
            'quality': 90,      # Alta calidad
            'scale': 1.0,       # Sin reducción
            'modo': 'Alta detalle'
        }
    
    elif complejidad > 0.6:
        # COMPLEJIDAD MEDIA-ALTA: Terreno con detalles moderados
        params = {
            'colors': 192,
            'quality': 85,
            'scale': 1.0,
            'modo': 'Detalle medio-alto'
        }
    
    elif complejidad > 0.4:
        # COMPLEJIDAD MEDIA: Mix de terreno y nubes
        params = {
            'colors': 128,
            'quality': 80,
            'scale': 1.0,
            'modo': 'Detalle medio'
        }
    
    elif complejidad > 0.25:
        # COMPLEJIDAD BAJA: Mayormente nubes con algo de terreno
        params = {
            'colors': 96,
            'quality': 75,
            'scale': 1.0,
            'modo': 'Nubes parciales'
        }
    
    else:
        # MUY BAJA COMPLEJIDAD: Nubes uniformes, blanco/gris
        params = {
            'colors': 64,       # Paleta muy reducida
            'quality': 70,
            'scale': 0.95,      # Reducir ligeramente tamaño
            'modo': 'Nubes uniformes'
        }
    
    print(f"    🎨 Modo seleccionado: {params['modo']} ({params['colors']} colores)")
    
    return params

def comprimir_gif_inteligente(imagenes, output_path, duracion=1000, target_mb=1.2):
    """
    Comprime GIF con parámetros adaptativos según contenido
    
    Args:
        imagenes: Lista de PIL Images (con overlays ya aplicados)
        output_path: Path donde guardar el GIF
        duracion: Duración por frame en ms
        target_mb: Tamaño objetivo máximo en MB
    
    Returns:
        float: Tamaño final en MB
    
    Proceso:
        1. Analizar complejidad visual
        2. Seleccionar parámetros óptimos
        3. Aplicar reducción de escala si es necesario
        4. Reducir paleta de colores
        5. Guardar con optimize=True
        6. Si excede target, comprimir más agresivamente
    """
    if not imagenes or len(imagenes) == 0:
        raise ValueError("Lista de imágenes vacía")
    
    # PASO 1: Calcular parámetros óptimos
    params = calcular_parametros_compresion(imagenes, target_mb)
    
    # PASO 2: Aplicar escala si es necesario
    imagenes_procesadas = imagenes
    
    if params['scale'] < 1.0:
        print(f"    🔽 Reduciendo escala: {params['scale']:.0%}")
        imagenes_procesadas = []
        
        for img in imagenes:
            new_size = (
                int(img.width * params['scale']),
                int(img.height * params['scale'])
            )
            img_scaled = img.resize(new_size, Image.Resampling.LANCZOS)
            imagenes_procesadas.append(img_scaled)
    
    # PASO 3: Reducir paleta de colores
    print(f"    🎨 Reduciendo paleta a {params['colors']} colores...")
    imagenes_optimizadas = []
    
    for img in imagenes_procesadas:
        # Convertir a modo RGB si es necesario
        if img.mode == 'RGBA':
            # Crear fondo blanco
            fondo = Image.new('RGB', img.size, (255, 255, 255))
            fondo.paste(img, (0, 0), img)
            img = fondo
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Reducir a paleta con N colores
        img_p = img.convert('P', palette=Image.ADAPTIVE, colors=params['colors'])
        imagenes_optimizadas.append(img_p)
    
    # PASO 4: Guardar GIF
    print(f"    💾 Guardando GIF (quality={params['quality']})...")
    
    imagenes_optimizadas[0].save(
        output_path,
        save_all=True,
        append_images=imagenes_optimizadas[1:],
        duration=duracion,
        loop=0,
        optimize=True,
        quality=params['quality']
    )
    
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"    📦 Tamaño inicial: {size_mb:.2f} MB")
    
    # PASO 5: Si excede target, comprimir más agresivamente
    if size_mb > target_mb:
        print(f"    ⚠️  Excede target ({target_mb} MB), comprimiendo más...")
        
        # Reducir tamaño un 15%
        imagenes_reducidas = []
        for img in imagenes_optimizadas:
            new_size = (int(img.width * 0.85), int(img.height * 0.85))
            img_reducido = img.resize(new_size, Image.Resampling.LANCZOS)
            imagenes_reducidas.append(img_reducido)
        
        # Re-guardar con menor calidad
        imagenes_reducidas[0].save(
            output_path,
            save_all=True,
            append_images=imagenes_reducidas[1:],
            duration=duracion,
            loop=0,
            optimize=True,
            quality=max(params['quality'] - 10, 60)
        )
        
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"    ✅ Tamaño final: {size_mb:.2f} MB")
    
    return size_mb

def estimar_tamano_sin_comprimir(imagenes):
    """
    Estima el tamaño aproximado del GIF sin compresión avanzada
    
    Returns:
        float: Tamaño estimado en MB
    """
    if not imagenes:
        return 0.0
    
    # Tamaño aproximado por frame (sin compresión)
    bytes_por_frame = imagenes[0].width * imagenes[0].height * 3
    
    # Total para todos los frames
    total_bytes = bytes_por_frame * len(imagenes)
    
    # GIF tiene algo de compresión natural
    estimado_mb = (total_bytes * 0.7) / (1024 * 1024)
    
    return estimado_mb

if __name__ == "__main__":
    """Test del optimizador"""
    import glob
    
    print("="*80)
    print("OPTIMIZADOR INTELIGENTE DE GIFs")
    print("="*80)
    
    # Buscar un GIF de ejemplo
    ejemplos = glob.glob("docs/sentinel2/*/timelapses_ppt/*.gif")
    
    if ejemplos:
        ejemplo = ejemplos[0]
        print(f"\n📂 Analizando: {os.path.basename(ejemplo)}")
        
        # Cargar frames
        gif = Image.open(ejemplo)
        frames = []
        
        try:
            while True:
                frames.append(gif.copy())
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass
        
        print(f"   Frames: {len(frames)}")
        
        # Analizar complejidad
        comp = analizar_complejidad_visual(frames)
        print(f"   Complejidad: {comp:.2f}")
        
        # Calcular parámetros
        params = calcular_parametros_compresion(frames)
        print(f"   Modo: {params['modo']}")
        print(f"   Colores: {params['colors']}")
    else:
        print("\n⚠️  No se encontraron GIFs de ejemplo")
