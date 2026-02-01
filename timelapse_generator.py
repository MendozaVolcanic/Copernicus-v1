"""
TIMELAPSE_GENERATOR.PY
Genera GIF animado con todas las imágenes del último mes
"""

import os
from PIL import Image
from datetime import datetime
import glob

# =========================
# CONFIGURACIÓN
# =========================

VOLCANES_ACTIVOS = ["Villarrica", "Llaima"]  # Expandir cuando se activen más

FPS = 1  # Frame por segundo
DURACION_FRAME = 1000  # Milisegundos por frame (1000ms = 1s)

# =========================
# GENERADOR DE GIF
# =========================

def generar_gif(volcan_nombre, tipo='RGB'):
    """
    Genera GIF timelapse para un volcán y tipo de imagen
    
    Args:
        volcan_nombre: Nombre del volcán
        tipo: 'RGB' o 'ThermalFalseColor'
    
    Returns:
        str: Path al GIF generado
    """
    
    print(f"\n🎬 Generando GIF: {volcan_nombre} - {tipo}")
    
    # Carpeta de imágenes
    carpeta_imagenes = f"data/sentinel2/{volcan_nombre}/{tipo}"
    
    if not os.path.exists(carpeta_imagenes):
        print(f"   ❌ Carpeta no existe: {carpeta_imagenes}")
        return None
    
    # Obtener todas las imágenes PNG
    imagenes_paths = sorted(glob.glob(f"{carpeta_imagenes}/*.png"))
    
    if len(imagenes_paths) == 0:
        print(f"   ⚠️ No hay imágenes en {carpeta_imagenes}")
        return None
    
    print(f"   📷 Encontradas {len(imagenes_paths)} imágenes")
    
    # Cargar imágenes
    imagenes = []
    fechas = []
    
    for img_path in imagenes_paths:
        try:
            img = Image.open(img_path)
            
            # Extraer fecha del nombre del archivo
            # Formato: YYYY-MM-DD_RGB.png
            nombre_archivo = os.path.basename(img_path)
            fecha = nombre_archivo.split('_')[0]
            fechas.append(fecha)
            
            # Agregar texto de fecha a la imagen
            img_con_texto = agregar_fecha_a_imagen(img, fecha, tipo)
            imagenes.append(img_con_texto)
            
            print(f"   ✅ {fecha}")
        except Exception as e:
            print(f"   ❌ Error cargando {img_path}: {e}")
            continue
    
    if len(imagenes) == 0:
        print(f"   ❌ No se pudieron cargar imágenes")
        return None
    
    # Crear carpeta de salida
    carpeta_gif = f"data/sentinel2/{volcan_nombre}/timelapses"
    os.makedirs(carpeta_gif, exist_ok=True)
    
    # Generar GIF
    fecha_inicio = fechas[0]
    fecha_fin = fechas[-1]
    
    # Usar mes del período más reciente para nombre consistente
    mes_actual = fecha_fin[:7]  # YYYY-MM
    output_path = f"{carpeta_gif}/{volcan_nombre}_{tipo}_{mes_actual}.gif"
    
    try:
        imagenes[0].save(
            output_path,
            save_all=True,
            append_images=imagenes[1:],
            duration=DURACION_FRAME,
            loop=0,  # Loop infinito
            optimize=True
        )
        
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"   ✅ GIF generado: {output_path}")
        print(f"   📦 Tamaño: {size_mb:.2f} MB")
        print(f"   🎞️ Frames: {len(imagenes)}")
        
        return output_path
    
    except Exception as e:
        print(f"   ❌ Error generando GIF: {e}")
        return None


def agregar_fecha_a_imagen(img, fecha, tipo):
    """
    Agrega texto de fecha y tipo a la imagen
    
    Args:
        img: PIL Image
        fecha: String de fecha (YYYY-MM-DD)
        tipo: 'RGB' o 'ThermalFalseColor'
    
    Returns:
        PIL Image con texto
    """
    from PIL import ImageDraw, ImageFont
    
    # Crear copia
    img_copy = img.copy()
    draw = ImageDraw.Draw(img_copy)
    
    # Intentar usar fuente del sistema, si no, usar default
    try:
        font_fecha = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_tipo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_fecha = ImageFont.load_default()
        font_tipo = ImageFont.load_default()
    
    # Texto de fecha
    texto_fecha = f"📅 {fecha}"
    
    # Texto de tipo
    tipo_texto = "RGB (Color Real)" if tipo == 'RGB' else "Falso Color Térmico (SWIR)"
    
    # Posición del texto (esquina superior izquierda)
    x = 20
    y = 20
    
    # Dibujar fondo semi-transparente para el texto
    # (PIL no soporta transparencia directamente, usamos un rectángulo negro)
    bbox_fecha = draw.textbbox((x, y), texto_fecha, font=font_fecha)
    draw.rectangle(bbox_fecha, fill=(0, 0, 0))
    
    bbox_tipo = draw.textbbox((x, y + 35), tipo_texto, font=font_tipo)
    draw.rectangle(bbox_tipo, fill=(0, 0, 0))
    
    # Dibujar texto
    draw.text((x, y), texto_fecha, fill=(255, 255, 255), font=font_fecha)
    draw.text((x, y + 35), tipo_texto, fill=(200, 200, 200), font=font_tipo)
    
    return img_copy


# =========================
# PROCESO PRINCIPAL
# =========================

def main():
    print("="*80)
    print("🎬 GENERADOR DE TIMELAPSE GIF")
    print("="*80)
    
    gifs_generados = []
    
    for volcan in VOLCANES_ACTIVOS:
        print(f"\n🌋 Procesando: {volcan}")
        
        # Generar GIF RGB
        gif_rgb = generar_gif(volcan, 'RGB')
        if gif_rgb:
            gifs_generados.append(gif_rgb)
        
        # Generar GIF Thermal
        gif_thermal = generar_gif(volcan, 'ThermalFalseColor')
        if gif_thermal:
            gifs_generados.append(gif_thermal)
    
    print("\n" + "="*80)
    print(f"✅ PROCESO COMPLETADO - {len(gifs_generados)} GIFs generados")
    print("="*80)
    
    for gif in gifs_generados:
        print(f"   📁 {gif}")


if __name__ == "__main__":
    main()
