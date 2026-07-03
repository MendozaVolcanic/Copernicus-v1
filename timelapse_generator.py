"""
TIMELAPSE_GENERATOR.PY V3.1
BASE: V3.0 + Sistema de caché + Compresión inteligente

NUEVO V3.1:
- Integración con gif_cache.py (evita re-procesar GIFs existentes)
- Integración con gif_optimizer.py (compresión adaptativa)
- Limpieza automática de caché >90 días
- Estadísticas de caché al finalizar
"""

import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import glob
import requests
from io import BytesIO
import json
from config_sentinel2 import VOLCANES, BUFFER_KM

# =========================
# NUEVO V3.1: IMPORTS CACHÉ Y OPTIMIZADOR
# =========================
from gif_cache import existe_en_cache, guardar_en_cache, limpiar_cache_antiguo, estadisticas_cache
from gif_optimizer import comprimir_gif_inteligente

# =========================
# CONFIGURACIÓN
# =========================

# FIX 2026-06-02: lista hardcoded de 43 volcanes NO incluia las 3 vistas
# zoom (Melimoyu_Conos_Eruptivos, Mentolat_Sismicidad_VT, Hudson_Ultima_
# Erupcion). Esas vistas si estan activas en VOLCANES (config_sentinel2.py)
# y tienen PNGs descargados, pero el generador las saltaba => ppt_builder
# las mostraba en gris.
# Ahora derivamos la lista del config (single source of truth).
VOLCANES_ACTIVOS = [n for n, c in VOLCANES.items() if c.get('activo', False)]

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
            print(f"    ⚠️  No se pudo descargar logo (status {response.status_code})")
            return None
    except Exception as e:
        print(f"    ⚠️  Error descargando logo: {e}")
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


def agregar_escala_kilometros(img, buffer_km=3, tipo='RGB'):
    """
    Agrega escala de kilómetros correcta según el buffer real del volcán.

    Args:
        img: PIL Image
        buffer_km: Radio real del volcán (del config). La barra muestra este valor.
        tipo: 'RGB' o 'ThermalFalseColor'
    """
    draw = ImageDraw.Draw(img)

    img_width, img_height = img.size

    area_fisica_km = buffer_km * 2  # área total = 2 × radio
    escala_km = buffer_km           # la barra muestra el radio (mitad del área)
    pixels_por_km = img_width / area_fisica_km
    ancho_barra_px = int(pixels_por_km * escala_km)
    
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
    
    texto_escala = f"{escala_km:g} km"
    draw.text((x_start + ancho_barra_px//2 - 20, y_pos - 20), texto_escala, fill=(255, 255, 255), font=font)

    return img


def agregar_overlay_copernicus(img, fecha, tipo, logo_copernicus=None, buffer_km=3):
    """
    Agrega overlay completo estilo Copernicus
    """
    
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
    tipo_texto = "Sentinel-2 L2A Color Verdadero" if tipo == 'RGB' else "Sentinel-2 L2A SWIR (B12-B11-B04)"
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
    img_final = agregar_escala_kilometros(img_final, buffer_km=buffer_km, tipo=tipo)
    
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
    config_path = f'docs/sentinel2/configs/timelapse_{volcan_nombre}.json'
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            print(f"    ℹ️  Usando rango: {config['fecha_inicio']} → {config['fecha_fin']}")
            return config['fecha_inicio'], config['fecha_fin']
    
    return None, None


def generar_gif(volcan_nombre, tipo='RGB', logo_copernicus=None, fecha_inicio=None, fecha_fin=None, buffer_km=None, max_cloud_cover=30):
    """
    Genera GIF timelapse con rango de fechas configurable
    FILTRA imágenes con cobertura de nubes <= max_cloud_cover (default 30%)

    NUEVO V3.1: Sistema de caché integrado
    """
    
    print(f"\n🎬 Generando GIF: {volcan_nombre} - {tipo}")
    
    # =========================
    # NUEVO V3.1: VERIFICAR CACHÉ PRIMERO
    # =========================
    if fecha_inicio and fecha_fin:
        cached_gif = existe_en_cache(volcan_nombre, tipo, fecha_inicio, fecha_fin)
        
        if cached_gif:
            print(f"    ✅ Usando GIF en caché: {os.path.basename(cached_gif)}")
            size_mb = os.path.getsize(cached_gif) / (1024 * 1024)
            print(f"    📦 Tamaño: {size_mb:.2f} MB")
            
            # Extraer fechas del nombre para retornar
            return cached_gif, fecha_inicio, fecha_fin
    
    print(f"    🔨 Generando nuevo GIF...")
    
    # CORRECCIÓN: Las imágenes están directamente en docs/sentinel2/{volcan}/
    carpeta_imagenes = f"docs/sentinel2/{volcan_nombre}"
    
    if not os.path.exists(carpeta_imagenes):
        print(f"    ❌ Carpeta no existe: {carpeta_imagenes}")
        return None
    
    # Cargar metadata para filtrar por cobertura de nubes
    metadata_path = f"{carpeta_imagenes}/metadata.csv"
    fechas_validas = set()
    
    if os.path.exists(metadata_path):
        try:
            import pandas as pd
            df = pd.read_csv(metadata_path)
            
            # Filtrar solo fechas con cobertura <= max_cloud_cover
            df_filtrado = df[df['cobertura_nubosa'] <= max_cloud_cover]
            fechas_validas = set(df_filtrado['fecha'].unique())

            print(f"    🌥️  Filtro nubes: {len(fechas_validas)} fechas con ≤{max_cloud_cover}% nubes")
        except Exception as e:
            print(f"    ⚠️  No se pudo cargar metadata: {e}")
            print(f"    ℹ️  Continuando sin filtro de nubes...")
    else:
        print(f"    ⚠️  metadata.csv no encontrado, sin filtro de nubes")
    
    # Buscar imágenes del tipo específico
    imagenes_paths = sorted(glob.glob(f"{carpeta_imagenes}/*_{tipo}.png"))
    
    if len(imagenes_paths) == 0:
        print(f"    ❌ No hay imágenes {tipo} en {carpeta_imagenes}")
        return None
    
    # Filtrar por rango de fechas si se especifica
    if fecha_inicio and fecha_fin:
        imagenes_filtradas = []
        for img_path in imagenes_paths:
            nombre = os.path.basename(img_path)
            fecha = nombre.split('_')[0]
            
            if fecha_inicio <= fecha <= fecha_fin:
                # FILTRO ADICIONAL: Solo imágenes con nubes <= 30%
                if not fechas_validas or fecha in fechas_validas:
                    imagenes_filtradas.append(img_path)
        
        imagenes_paths = imagenes_filtradas
        print(f"    📅 Filtrado por fechas + nubes: {len(imagenes_paths)} imágenes")
    
    if len(imagenes_paths) == 0:
        print(f"    ❌ No hay imágenes en el rango {fecha_inicio} → {fecha_fin}")
        return None
    
    print(f"    🔍 Procesando {len(imagenes_paths)} imágenes")
    
    imagenes = []
    fechas = []
    
    for img_path in imagenes_paths:
        try:
            img = Image.open(img_path)
            
            nombre_archivo = os.path.basename(img_path)
            fecha = nombre_archivo.split('_')[0]
            fechas.append(fecha)
            
            # Agregar overlay con escala correcta según buffer del volcán
            img_con_overlay = agregar_overlay_copernicus(img, fecha, tipo, logo_copernicus, buffer_km=buffer_km or 3)
            imagenes.append(img_con_overlay)
            
            print(f"       {fecha}")
        except Exception as e:
            print(f"    ❌ Error cargando {img_path}: {e}")
            continue
    
    if len(imagenes) == 0:
        print(f"    ❌ No se pudieron cargar imágenes")
        return None
    
    carpeta_gif = f"docs/sentinel2/{volcan_nombre}/timelapses_ppt"
    os.makedirs(carpeta_gif, exist_ok=True)
    
    fecha_inicio_real = fechas[0]
    fecha_fin_real = fechas[-1]
    
    # Nombre con rango de fechas
    output_path = f"{carpeta_gif}/{volcan_nombre}_{tipo}_{fecha_inicio_real}_{fecha_fin_real}.gif"
    
    try:
        # =========================
        # NUEVO V3.1: USAR COMPRESOR INTELIGENTE
        # =========================
        print(f"    🎨 Aplicando compresión inteligente...")
        size_mb = comprimir_gif_inteligente(
            imagenes,
            output_path,
            duracion=DURACION_FRAME,
            target_mb=1.2,
            tipo=tipo
        )
        
        # =========================
        # NUEVO V3.1: GUARDAR EN CACHÉ
        # =========================
        if fecha_inicio and fecha_fin:
            guardar_en_cache(volcan_nombre, tipo, fecha_inicio_real, fecha_fin_real, output_path)
        
        print(f"    ✅ GIF generado: {size_mb:.2f} MB")
        print(f"    📅 Período: {fecha_inicio_real} → {fecha_fin_real}")
        
        return output_path, fecha_inicio_real, fecha_fin_real
    
    except Exception as e:
        print(f"    ❌ Error generando GIF: {e}")
        return None


def main():
    print("="*80)
    print("🎬 GENERADOR DE TIMELAPSES V3.1")
    print("   NUEVO: Caché + Compresión inteligente")
    print("="*80)
    
    # =========================
    # NUEVO V3.1: LIMPIAR CACHÉ ANTIGUO AL INICIO
    # =========================
    print("\n🧹 Limpiando caché antiguo (>90 días)...")
    eliminados = limpiar_cache_antiguo(dias=90)
    if eliminados > 0:
        print(f"   🗑️  Eliminados: {eliminados} GIFs antiguos")
    else:
        print(f"   ✅ No hay GIFs antiguos para eliminar")
    
    # Leer variables de entorno si existen (para workflow manual)
    volcan_env = os.getenv('VOLCAN')
    fecha_inicio_env = os.getenv('FECHA_INICIO')
    fecha_fin_env = os.getenv('FECHA_FIN')
    
    if volcan_env and fecha_inicio_env and fecha_fin_env:
        print(f"\n📋 MODO MANUAL:")
        print(f"   Volcán: {volcan_env}")
        print(f"   Rango: {fecha_inicio_env} → {fecha_fin_env}")
        volcanes_a_procesar = [volcan_env]
    else:
        print("\n🤖 MODO AUTOMÁTICO: Procesando todos los volcanes")
        volcanes_a_procesar = VOLCANES_ACTIVOS
    
    # Descargar logo de Copernicus
    print("\n📥 Descargando logo de Copernicus...")
    logo_copernicus = descargar_logo_copernicus()
    
    if logo_copernicus is None:
        print("    ℹ️  Usando logo de texto alternativo")
        logo_copernicus = crear_logo_copernicus_texto()
    else:
        print("    ✅ Logo descargado")
    
    gifs_generados = []
    
    for volcan in volcanes_a_procesar:
        print(f"\n🌋 Procesando: {volcan}")
        
        # Si hay variables de entorno, usarlas; sino, cargar config
        if fecha_inicio_env and fecha_fin_env:
            fecha_inicio = fecha_inicio_env
            fecha_fin = fecha_fin_env
        else:
            fecha_inicio, fecha_fin = cargar_config_fechas(volcan)
        
        buf_km = VOLCANES.get(volcan, {}).get('buffer_km', BUFFER_KM)
        for tipo in ['RGB', 'ThermalFalseColor']:
            resultado = generar_gif(volcan, tipo, logo_copernicus, fecha_inicio, fecha_fin, buffer_km=buf_km)
            if resultado:
                gifs_generados.append(resultado)
    
    print("\n" + "="*80)
    print(f"✅ PROCESO COMPLETADO - {len(gifs_generados)} GIFs generados")
    print("="*80)
    
    # =========================
    # NUEVO V3.1: MOSTRAR ESTADÍSTICAS DE CACHÉ
    # =========================
    stats = estadisticas_cache()
    print(f"\n💾 Estadísticas de caché:")
    print(f"   Entradas: {stats['total_entradas']}")
    print(f"   Espacio: {stats['espacio_total_mb']} MB")
    
    print(f"\n📦 GIFs generados:")
    for gif_info in gifs_generados:
        if isinstance(gif_info, tuple) and len(gif_info) == 3:
            gif_path, fecha_i, fecha_f = gif_info
            size_mb = os.path.getsize(gif_path) / (1024 * 1024)
            print(f"   {os.path.basename(gif_path)}: {size_mb:.2f} MB ({fecha_i} → {fecha_f})")
    
    print("="*80)


if __name__ == "__main__":
    main()
