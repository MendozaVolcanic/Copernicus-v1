"""
TIMELAPSE_GENERATOR.PY V3.0 - ESCALAS CORREGIDAS
Genera GIF animado con escala CORRECTA y PROPORCIONAL
Buffer real: 3 km → Escala mostrada: 3 km
"""

import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import glob
import requests
from io import BytesIO
import json

# =========================
# CONFIGURACIÓN
# =========================

VOLCANES_ACTIVOS = [
    # ZONA NORTE
    "Taapaca", "Parinacota", "Guallatiri", "Isluga", "Irruputuncu", "Ollagüe", "San Pedro", "Láscar",
    # ZONA CENTRO
    "Tupungatito", "San José", "Tinguiririca", "Planchón-Peteroa", "Descabezado Grande", 
    "Tatara-San Pedro", "Laguna del Maule", "Nevado de Longaví", "Nevados de Chillán",
    # ZONA SUR
    "Antuco", "Copahue", "Callaqui", "Lonquimay", "Llaima", "Sollipulli", "Villarrica", 
    "Quetrupillán", "Lanín", "Mocho-Choshuenco", "Carrán - Los Venados", "Puyehue - Cordón Caulle", 
    "Antillanca – Casablanca",
    # ZONA AUSTRAL
    "Osorno", "Calbuco", "Yate", "Hornopirén", "Huequi", "Michinmahuida", "Chaitén", 
    "Corcovado", "Melimoyu", "Mentolat", "Cay", "Macá", "Hudson"
]

FPS = 1
DURACION_FRAME = 1000  # ms

# URL del logo de Copernicus
COPERNICUS_LOGO_URL = "https://www.copernicus.eu/themes/custom/copernicus/logo.svg"

# =========================
# FUNCIONES AUXILIARES
# =========================

def descargar_logo_copernicus():
    """
    Descarga y convierte el logo de Copernicus a PNG
    """
    try:
        # Usar logo alternativo (PNG directo)
        logo_url = "https://identity.copernicus.eu/documents/20126/0/Copernicus_Logo_Full_Colour_RGB+%281%29.png"
        
        response = requests.get(logo_url, timeout=10)
        if response.status_code == 200:
            logo = Image.open(BytesIO(response.content))
            # Redimensionar a tamaño apropiado (ancho 150px)
            aspect = logo.height / logo.width
            new_width = 150
            new_height = int(new_width * aspect)
            logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # Convertir a RGBA si no lo es
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            return logo
        else:
            print(f"   ⚠️ No se pudo descargar logo (status {response.status_code})")
            return None
    except Exception as e:
        print(f"   ⚠️ Error descargando logo: {e}")
        return None


def crear_logo_copernicus_texto():
    """
    Crea un logo de texto simple si no se puede descargar el real
    """
    logo_img = Image.new('RGBA', (150, 50), (0, 0, 0, 0))
    draw = ImageDraw.Draw(logo_img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Fondo azul Copernicus
    draw.rectangle([(0, 0), (150, 50)], fill=(0, 51, 153, 255))
    
    # Texto blanco
    draw.text((10, 15), "COPERNICUS", fill=(255, 255, 255, 255), font=font)
    
    return logo_img


def agregar_escala_kilometros(img, escala_km=3, tipo='RGB'):
    """
    Agrega escala de kilómetros CORRECTA y PROPORCIONAL
    
    FIX CRÍTICO:
    - Buffer usado en descarga: 3 km
    - Área total de imagen: 6 km × 6 km (2 × buffer)
    - Escala mostrada: 3 km (mitad del área)
    
    Args:
        img: PIL Image
        escala_km: Kilómetros a representar (3 km = buffer real)
        tipo: 'RGB' o 'ThermalFalseColor'
    """
    draw = ImageDraw.Draw(img)
    
    img_width, img_height = img.size
    
    # ========================================
    # FIX CRÍTICO: CÁLCULO CORRECTO DE ESCALA
    # ========================================
    # Área física total: 6 km × 6 km (buffer 3 km en config)
    # Ancho de imagen: 1024px (tanto RGB como Thermal)
    # Proporción: 1024px / 6 km = 170.67 px/km
    # Escala de 3 km: 3 km × 170.67 px/km = 512px
    
    area_fisica_km = 6.0  # Buffer 3km → área total 6km
    pixels_por_km = img_width / area_fisica_km
    ancho_barra_px = int(pixels_por_km * escala_km)
    
    print(f"   📏 Escala {tipo}: {escala_km} km = {ancho_barra_px} px (imagen {img_width}px = {area_fisica_km} km)")
    
    # Posición (abajo a la derecha)
    x_start = img_width - ancho_barra_px - 30
    y_pos = img_height - 50
    
    # Dibujar fondo negro semi-transparente
    padding = 10
    draw.rectangle(
        [(x_start - padding, y_pos - padding - 20), 
         (x_start + ancho_barra_px + padding, y_pos + padding + 10)],
        fill=(0, 0, 0, 180)
    )
    
    # Dibujar barra de escala (blanca con borde negro)
    altura_barra = 6
    
    # Borde negro
    draw.rectangle(
        [(x_start - 2, y_pos - 2), 
         (x_start + ancho_barra_px + 2, y_pos + altura_barra + 2)],
        fill=(0, 0, 0, 255)
    )
    
    # Barra blanca
    draw.rectangle(
        [(x_start, y_pos), 
         (x_start + ancho_barra_px, y_pos + altura_barra)],
        fill=(255, 255, 255, 255)
    )
    
    # Marcas cada kilómetro
    for i in range(int(escala_km) + 1):
        x_marca = x_start + int((ancho_barra_px / escala_km) * i)
        draw.line([(x_marca, y_pos), (x_marca, y_pos + altura_barra + 5)], fill=(255, 255, 255), width=2)
    
    # Texto de escala
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    texto_escala = f"{int(escala_km)} km"
    draw.text((x_start + ancho_barra_px//2 - 20, y_pos - 20), texto_escala, fill=(255, 255, 255), font=font)
    
    return img


def agregar_overlay_copernicus(img, fecha, tipo, logo_copernicus=None):
    """
    Agrega overlay completo estilo Copernicus
    """
    from PIL import ImageDraw, ImageFont
    
    img_copy = img.copy()
    
    # Convertir a RGBA para transparencias
    if img_copy.mode != 'RGBA':
        img_copy = img_copy.convert('RGBA')
    
    # Crear capa de overlay
    overlay = Image.new('RGBA', img_copy.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Fuentes
    try:
        font_fecha = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_tipo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_fecha = ImageFont.load_default()
        font_tipo = ImageFont.load_default()
    
    # 1. LOGO COPERNICUS (arriba izquierda)
    if logo_copernicus:
        overlay.paste(logo_copernicus, (15, 15), logo_copernicus)
    
    # 2. FECHA (arriba derecha con fondo)
    texto_fecha = fecha
    img_width = img_copy.size[0]
    
    bbox_fecha = draw.textbbox((0, 0), texto_fecha, font=font_fecha)
    ancho_texto = bbox_fecha[2] - bbox_fecha[0]
    x_fecha = img_width - ancho_texto - 20
    y_fecha = 15
    
    padding = 8
    draw.rectangle(
        [(x_fecha - padding, y_fecha - padding), 
         (x_fecha + ancho_texto + padding, y_fecha + 30 + padding)],
        fill=(0, 0, 0, 200)
    )
    draw.text((x_fecha, y_fecha), texto_fecha, fill=(255, 255, 255), font=font_fecha)
    
    # 3. TIPO DE IMAGEN (abajo izquierda con fondo)
    tipo_texto = "Sentinel-2 L2A RGB" if tipo == 'RGB' else "Sentinel-2 L2A SWIR (B12-B11-B04)"
    x_tipo = 15
    y_tipo = img_copy.size[1] - 40
    
    bbox_tipo = draw.textbbox((0, 0), tipo_texto, font=font_tipo)
    ancho_tipo = bbox_tipo[2] - bbox_tipo[0]
    
    draw.rectangle(
        [(x_tipo - 5, y_tipo - 5), 
         (x_tipo + ancho_tipo + 5, y_tipo + 25)],
        fill=(0, 0, 0, 200)
    )
    draw.text((x_tipo, y_tipo), tipo_texto, fill=(200, 200, 200), font=font_tipo)
    
    # Combinar overlay con imagen original
    img_final = Image.alpha_composite(img_copy, overlay)
    
    # 4. ESCALA (abajo derecha) - DESPUÉS del composite
    img_final = agregar_escala_kilometros(img_final, escala_km=3, tipo=tipo)
    
    # Convertir de vuelta a RGB
    if img_final.mode == 'RGBA':
        fondo = Image.new('RGB', img_final.size, (0, 0, 0))
        fondo.paste(img_final, (0, 0), img_final)
        img_final = fondo
    
    return img_final


def cargar_config_fechas(volcan_nombre):
    """
    Carga configuración de fechas desde JSON
    Si no existe, usa todas las fechas disponibles
    """
    config_path = f'data/sentinel2/configs/timelapse_{volcan_nombre}.json'
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            print(f"   📅 Usando rango: {config['fecha_inicio']} → {config['fecha_fin']}")
            return config['fecha_inicio'], config['fecha_fin']
    
    return None, None


def generar_gif(volcan_nombre, tipo='RGB', logo_copernicus=None, fecha_inicio=None, fecha_fin=None):
    """
    Genera GIF timelapse con rango de fechas configurable
    """
    
    print(f"\n🎬 Generando GIF: {volcan_nombre} - {tipo}")
    
    carpeta_imagenes = f"data/sentinel2/{volcan_nombre}/{tipo}"
    
    if not os.path.exists(carpeta_imagenes):
        print(f"   ❌ Carpeta no existe: {carpeta_imagenes}")
        return None
    
    imagenes_paths = sorted(glob.glob(f"{carpeta_imagenes}/*.png"))
    
    if len(imagenes_paths) == 0:
        print(f"   ⚠️ No hay imágenes en {carpeta_imagenes}")
        return None
    
    # Filtrar por rango de fechas si se especifica
    if fecha_inicio and fecha_fin:
        imagenes_filtradas = []
        for img_path in imagenes_paths:
            nombre = os.path.basename(img_path)
            fecha = nombre.split('_')[0]
            
            if fecha_inicio <= fecha <= fecha_fin:
                imagenes_filtradas.append(img_path)
        
        imagenes_paths = imagenes_filtradas
        print(f"   📅 Filtrado por fechas: {len(imagenes_paths)} imágenes")
    
    if len(imagenes_paths) == 0:
        print(f"   ⚠️ No hay imágenes en el rango {fecha_inicio} - {fecha_fin}")
        return None
    
    print(f"   📷 Procesando {len(imagenes_paths)} imágenes")
    
    imagenes = []
    fechas = []
    
    for img_path in imagenes_paths:
        try:
            img = Image.open(img_path)
            
            nombre_archivo = os.path.basename(img_path)
            fecha = nombre_archivo.split('_')[0]
            fechas.append(fecha)
            
            # Agregar overlay con escala CORREGIDA
            img_con_overlay = agregar_overlay_copernicus(img, fecha, tipo, logo_copernicus)
            imagenes.append(img_con_overlay)
            
            print(f"   ✅ {fecha}")
        except Exception as e:
            print(f"   ❌ Error cargando {img_path}: {e}")
            continue
    
    if len(imagenes) == 0:
        print(f"   ❌ No se pudieron cargar imágenes")
        return None
    
    carpeta_gif = f"data/sentinel2/{volcan_nombre}/timelapses"
    os.makedirs(carpeta_gif, exist_ok=True)
    
    fecha_inicio_real = fechas[0]
    fecha_fin_real = fechas[-1]
    
    # Nombre con rango de fechas
    output_path = f"{carpeta_gif}/{volcan_nombre}_{tipo}_{fecha_inicio_real}_{fecha_fin_real}.gif"
    
    try:
        # ========================================
        # COMPRIMIR GIF PARA <1.5 MB
        # ========================================
        imagenes[0].save(
            output_path,
            save_all=True,
            append_images=imagenes[1:],
            duration=DURACION_FRAME,
            loop=0,
            optimize=True,  # PIL optimiza automáticamente
            quality=85      # NUEVO: Reducir calidad para comprimir más
        )
        
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        
        # Si aún es muy grande, reducir más
        if size_mb > 1.5:
            print(f"   ⚠️ GIF muy grande ({size_mb:.2f} MB), recomprimiendo...")
            
            # Reducir tamaño de frames
            imagenes_reducidas = []
            for img in imagenes:
                # Reducir a 85% del tamaño
                new_size = (int(img.width * 0.85), int(img.height * 0.85))
                img_reducida = img.resize(new_size, Image.Resampling.LANCZOS)
                imagenes_reducidas.append(img_reducida)
            
            imagenes_reducidas[0].save(
                output_path,
                save_all=True,
                append_images=imagenes_reducidas[1:],
                duration=DURACION_FRAME,
                loop=0,
                optimize=True,
                quality=80
            )
            
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
        
        print(f"   ✅ GIF generado: {size_mb:.2f} MB")
        print(f"   📅 Período: {fecha_inicio_real} → {fecha_fin_real}")
        
        return output_path, fecha_inicio_real, fecha_fin_real
    except Exception as e:
        print(f"   ❌ Error generando GIF: {e}")
        return None


def main():
    print("="*80)
    print("🎬 GENERADOR DE TIMELAPSES V3.0")
    print("   Escalas CORREGIDAS - Buffer real: 3 km")
    print("="*80)
    
    # Descargar logo de Copernicus
    print("\n📥 Descargando logo de Copernicus...")
    logo_copernicus = descargar_logo_copernicus()
    
    if logo_copernicus is None:
        print("   ⚠️ Usando logo de texto alternativo")
        logo_copernicus = crear_logo_copernicus_texto()
    else:
        print("   ✅ Logo descargado")
    
    gifs_generados = []
    
    for volcan in VOLCANES_ACTIVOS:
        print(f"\n🌋 Procesando: {volcan}")
        
        # Cargar configuración de fechas (si existe)
        fecha_inicio, fecha_fin = cargar_config_fechas(volcan)
        
        for tipo in ['RGB', 'ThermalFalseColor']:
            resultado = generar_gif(volcan, tipo, logo_copernicus, fecha_inicio, fecha_fin)
            if resultado:
                gifs_generados.append(resultado)
    
    print("\n" + "="*80)
    print(f"✅ PROCESO COMPLETADO - {len(gifs_generados)} GIFs generados")
    print("="*80)
    
    for gif_info in gifs_generados:
        if len(gif_info) == 3:
            gif_path, fecha_i, fecha_f = gif_info
            size_mb = os.path.getsize(gif_path) / (1024 * 1024)
            print(f"   📁 {os.path.basename(gif_path)}: {size_mb:.2f} MB ({fecha_i} → {fecha_f})")


if __name__ == "__main__":
    main()
