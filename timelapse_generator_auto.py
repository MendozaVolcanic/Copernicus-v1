"""
TIMELAPSE_GENERATOR_AUTO.PY
Genera timelapses AUTOMÁTICOS de últimos 30 días para dashboard
Se ejecuta después de cada descarga
"""

import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import glob
import requests
from io import BytesIO
import pytz

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
DIAS_TIMELAPSE = 30  # Últimos 30 días para dashboard
DURACION_FRAME = 1000  # ms

# =========================
# FUNCIONES (IGUAL QUE ANTES)
# =========================

def descargar_logo_copernicus():
    """Descarga logo de Copernicus"""
    try:
        logo_url = "https://identity.copernicus.eu/documents/20126/0/Copernicus_Logo_Full_Colour_RGB+%281%29.png"
        response = requests.get(logo_url, timeout=10)
        if response.status_code == 200:
            logo = Image.open(BytesIO(response.content))
            aspect = logo.height / logo.width
            new_width = 150
            new_height = int(new_width * aspect)
            logo = logo.resize((new_width, new_height), Image.Resampling.LANCZOS)
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            return logo
    except:
        pass
    return None

def crear_logo_copernicus_texto():
    """Logo de texto fallback"""
    logo_img = Image.new('RGBA', (150, 50), (0, 0, 0, 0))
    draw = ImageDraw.Draw(logo_img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        font = ImageFont.load_default()
    draw.rectangle([(0, 0), (150, 50)], fill=(0, 51, 153, 255))
    draw.text((10, 15), "COPERNICUS", fill=(255, 255, 255, 255), font=font)
    return logo_img

def agregar_escala_kilometros(img, escala_km=3, tipo='RGB'):
    """Agrega escala CORREGIDA"""
    draw = ImageDraw.Draw(img)
    
    img_width, img_height = img.size
    area_fisica_km = 6.0
    pixels_por_km = img_width / area_fisica_km
    ancho_barra_px = int(pixels_por_km * escala_km)
    
    x_start = img_width - ancho_barra_px - 30
    y_pos = img_height - 50
    
    padding = 10
    draw.rectangle(
        [(x_start - padding, y_pos - padding - 20), 
         (x_start + ancho_barra_px + padding, y_pos + padding + 10)],
        fill=(0, 0, 0, 180)
    )
    
    altura_barra = 6
    draw.rectangle(
        [(x_start - 2, y_pos - 2), 
         (x_start + ancho_barra_px + 2, y_pos + altura_barra + 2)],
        fill=(0, 0, 0, 255)
    )
    draw.rectangle(
        [(x_start, y_pos), 
         (x_start + ancho_barra_px, y_pos + altura_barra)],
        fill=(255, 255, 255, 255)
    )
    
    for i in range(int(escala_km) + 1):
        x_marca = x_start + int((ancho_barra_px / escala_km) * i)
        draw.line([(x_marca, y_pos), (x_marca, y_pos + altura_barra + 5)], fill=(255, 255, 255), width=2)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    texto_escala = f"{int(escala_km)} km"
    draw.text((x_start + ancho_barra_px//2 - 20, y_pos - 20), texto_escala, fill=(255, 255, 255), font=font)
    
    return img

def agregar_overlay_copernicus(img, fecha, tipo, logo_copernicus=None):
    """Agrega overlay completo"""
    img_copy = img.copy()
    
    if img_copy.mode != 'RGBA':
        img_copy = img_copy.convert('RGBA')
    
    overlay = Image.new('RGBA', img_copy.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    try:
        font_fecha = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_tipo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_fecha = ImageFont.load_default()
        font_tipo = ImageFont.load_default()
    
    if logo_copernicus:
        overlay.paste(logo_copernicus, (15, 15), logo_copernicus)
    
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
    
    img_final = Image.alpha_composite(img_copy, overlay)
    img_final = agregar_escala_kilometros(img_final, escala_km=3, tipo=tipo)
    
    if img_final.mode == 'RGBA':
        fondo = Image.new('RGB', img_final.size, (0, 0, 0))
        fondo.paste(img_final, (0, 0), img_final)
        img_final = fondo
    
    return img_final

def generar_gif_ultimos_30_dias(volcan_nombre, tipo='RGB', logo_copernicus=None):
    """
    Genera GIF con ÚLTIMOS 30 DÍAS para dashboard
    Automático - no requiere configuración manual
    """
    
    print(f"\n🎬 Generando GIF automático: {volcan_nombre} - {tipo}")
    
    carpeta_imagenes = f"data/sentinel2/{volcan_nombre}/{tipo}"
    
    if not os.path.exists(carpeta_imagenes):
        print(f"   ❌ Carpeta no existe")
        return None
    
    # Calcular fecha límite (hace 30 días)
    ahora = datetime.now(pytz.utc)
    hace_30_dias = ahora - timedelta(days=DIAS_TIMELAPSE)
    fecha_limite = hace_30_dias.strftime('%Y-%m-%d')
    
    print(f"   📅 Rango: {fecha_limite} → {ahora.strftime('%Y-%m-%d')}")
    
    # Filtrar imágenes de últimos 30 días
    imagenes_paths = []
    for img_path in sorted(glob.glob(f"{carpeta_imagenes}/*.png")):
        nombre = os.path.basename(img_path)
        fecha = nombre.split('_')[0]
        
        if fecha >= fecha_limite:
            imagenes_paths.append(img_path)
    
    if len(imagenes_paths) == 0:
        print(f"   ⚠️ No hay imágenes de últimos {DIAS_TIMELAPSE} días")
        return None
    
    print(f"   📷 Procesando {len(imagenes_paths)} imágenes")
    
    imagenes = []
    fechas = []
    
    for img_path in imagenes_paths:
        try:
            img = Image.open(img_path)
            nombre = os.path.basename(img_path)
            fecha = nombre.split('_')[0]
            fechas.append(fecha)
            
            img_con_overlay = agregar_overlay_copernicus(img, fecha, tipo, logo_copernicus)
            imagenes.append(img_con_overlay)
            
            print(f"   ✅ {fecha}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    if len(imagenes) == 0:
        print(f"   ❌ No se pudieron cargar imágenes")
        return None
    
    # Guardar en docs/ para GitHub Pages
    carpeta_gif = "docs/timelapses"
    os.makedirs(carpeta_gif, exist_ok=True)
    
    fecha_inicio = fechas[0]
    fecha_fin = fechas[-1]
    
    # Nombre fijo para dashboard: volcan_tipo.gif
    output_path = f"{carpeta_gif}/{volcan_nombre}_{tipo}.gif"
    
    try:
        # Comprimir GIF para <1.5 MB
        imagenes[0].save(
            output_path,
            save_all=True,
            append_images=imagenes[1:],
            duration=DURACION_FRAME,
            loop=0,
            optimize=True,
            quality=85
        )
        
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        
        # Si muy grande, reducir tamaño
        if size_mb > 1.5:
            print(f"   ⚠️ Reduciendo tamaño ({size_mb:.2f} MB)...")
            imagenes_reducidas = [img.resize((int(img.width * 0.85), int(img.height * 0.85)), Image.Resampling.LANCZOS) for img in imagenes]
            imagenes_reducidas[0].save(output_path, save_all=True, append_images=imagenes_reducidas[1:], duration=DURACION_FRAME, loop=0, optimize=True, quality=80)
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
        
        print(f"   ✅ GIF: {size_mb:.2f} MB")
        print(f"   📅 {fecha_inicio} → {fecha_fin}")
        
        return output_path
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def main():
    """Proceso automático para dashboard"""
    
    print("="*80)
    print("🎬 GENERADOR DE TIMELAPSES AUTOMÁTICO")
    print(f"   Últimos {DIAS_TIMELAPSE} días para dashboard")
    print("="*80)
    
    print("\n📥 Descargando logo...")
    logo = descargar_logo_copernicus()
    if logo is None:
        print("   ⚠️ Usando logo alternativo")
        logo = crear_logo_copernicus_texto()
    else:
        print("   ✅ Logo descargado")
    
    gifs_generados = []
    
    for volcan in VOLCANES_ACTIVOS:
        print(f"\n🌋 {volcan}")
        
        for tipo in ['RGB', 'ThermalFalseColor']:
            gif_path = generar_gif_ultimos_30_dias(volcan, tipo, logo)
            if gif_path:
                gifs_generados.append(gif_path)
    
    print("\n" + "="*80)
    print(f"✅ COMPLETADO - {len(gifs_generados)} GIFs")
    print("="*80)
    
    for gif in gifs_generados:
        size_mb = os.path.getsize(gif) / (1024 * 1024)
        print(f"   📁 {os.path.basename(gif)}: {size_mb:.2f} MB")

if __name__ == "__main__":
    main()
