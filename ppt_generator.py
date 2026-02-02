"""
PPT_GENERATOR.PY V4.0 - CORREGIDO
Genera PPT manteniendo formato exacto de plantilla
- Preserva título original
- Preserva textos originales con solo fechas actualizadas
- Mantiene tamaño fuente original
- Comprime GIFs para < 3MB
"""

import os
import glob
from datetime import datetime
from pptx import Presentation
from pptx.util import Pt
from PIL import Image
import io

# =========================
# CONFIGURACIÓN
# =========================

VOLCANES_ACTIVOS = ["Villarrica", "Llaima"]

PLANTILLA_PATH = "data/Cambios_morfologicos.pptx"
OUTPUT_DIR = "data/sentinel2"

# Meses en español
MESES_ES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

# =========================
# FUNCIÓN PRINCIPAL
# =========================

def formatear_fecha_espanol(fecha_str):
    """
    Convierte YYYY-MM-DD a "DD mes" en español
    Ejemplo: "2025-12-02" → "02 diciembre"
    """
    try:
        dt = datetime.strptime(fecha_str, '%Y-%m-%d')
        dia = dt.strftime('%d')
        mes = MESES_ES[dt.month]
        return f"{dia} {mes}"
    except:
        return fecha_str


def comprimir_gif(input_path, output_path, max_size_mb=1.2):
    """
    Comprime GIF para mantener PPT < 3MB
    Reduce colores y calidad si es necesario
    """
    try:
        size_mb = os.path.getsize(input_path) / (1024 * 1024)
        
        if size_mb <= max_size_mb:
            # Ya es suficientemente pequeño, copiar directo
            import shutil
            shutil.copy2(input_path, output_path)
            print(f"      GIF OK ({size_mb:.2f} MB), sin comprimir")
            return output_path
        
        # Necesita compresión
        print(f"      Comprimiendo GIF ({size_mb:.2f} MB → ~{max_size_mb:.2f} MB)...")
        
        img = Image.open(input_path)
        
        frames = []
        try:
            while True:
                # Copiar frame
                frame = img.copy()
                
                # Reducir colores a 128 (de 256)
                frame = frame.convert('P', palette=Image.ADAPTIVE, colors=128)
                
                frames.append(frame)
                img.seek(img.tell() + 1)
        except EOFError:
            pass
        
        # Guardar con compresión
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            optimize=True,
            duration=img.info.get('duration', 100),
            loop=0
        )
        
        new_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"      ✅ Comprimido: {size_mb:.2f} MB → {new_size_mb:.2f} MB")
        
        return output_path
    
    except Exception as e:
        print(f"      ⚠️ Error comprimiendo, usando original: {e}")
        import shutil
        shutil.copy2(input_path, output_path)
        return output_path


def generar_ppt(volcan_nombre):
    """
    Genera PPT para un volcán manteniendo textos originales
    """
    
    print(f"\n📊 Generando PPT: {volcan_nombre}")
    
    # Buscar GIFs más recientes
    carpeta_timelapses = f"data/sentinel2/{volcan_nombre}/timelapses"
    
    if not os.path.exists(carpeta_timelapses):
        print(f"   ❌ No existe carpeta: {carpeta_timelapses}")
        return None
    
    # Buscar GIFs (patrón: Volcan_tipo_fechaInicio_fechaFin.gif)
    gifs_rgb = sorted(glob.glob(f"{carpeta_timelapses}/{volcan_nombre}_RGB_*.gif"))
    gifs_thermal = sorted(glob.glob(f"{carpeta_timelapses}/{volcan_nombre}_ThermalFalseColor_*.gif"))
    
    if not gifs_rgb or not gifs_thermal:
        print(f"   ⚠️ No se encontraron GIFs completos")
        return None
    
    # Tomar los más recientes
    gif_rgb_path = gifs_rgb[-1]
    gif_thermal_path = gifs_thermal[-1]
    
    # Extraer fechas del nombre del archivo
    # Formato: Volcan_RGB_2025-12-02_2025-12-30.gif
    nombre_rgb = os.path.basename(gif_rgb_path)
    partes_rgb = nombre_rgb.replace('.gif', '').split('_')
    
    if len(partes_rgb) >= 4:
        fecha_inicio = partes_rgb[-2]  # YYYY-MM-DD
        fecha_fin = partes_rgb[-1]      # YYYY-MM-DD
    else:
        print(f"   ⚠️ No se pudieron extraer fechas del nombre: {nombre_rgb}")
        return None
    
    print(f"   📅 Período: {fecha_inicio} → {fecha_fin}")
    print(f"   🖼️ RGB: {os.path.basename(gif_rgb_path)}")
    print(f"   🖼️ Thermal: {os.path.basename(gif_thermal_path)}")
    
    # Verificar tamaños
    size_rgb_mb = os.path.getsize(gif_rgb_path) / (1024 * 1024)
    size_thermal_mb = os.path.getsize(gif_thermal_path) / (1024 * 1024)
    
    print(f"   📦 Tamaño RGB: {size_rgb_mb:.2f} MB")
    print(f"   📦 Tamaño Thermal: {size_thermal_mb:.2f} MB")
    
    # COMPRIMIR GIFs SI ES NECESARIO
    temp_rgb = f"/tmp/{volcan_nombre}_RGB_compressed.gif"
    temp_thermal = f"/tmp/{volcan_nombre}_Thermal_compressed.gif"
    
    print(f"   🗜️ Comprimiendo GIFs...")
    gif_rgb_final = comprimir_gif(gif_rgb_path, temp_rgb, max_size_mb=1.2)
    gif_thermal_final = comprimir_gif(gif_thermal_path, temp_thermal, max_size_mb=1.2)
    
    # ========================================
    # CARGAR PLANTILLA
    # ========================================
    if not os.path.exists(PLANTILLA_PATH):
        print(f"   ❌ No existe plantilla: {PLANTILLA_PATH}")
        return None
    
    prs = Presentation(PLANTILLA_PATH)
    
    print(f"   ✅ Plantilla cargada: {len(prs.slides)} slides")
    
    # ========================================
    # SLIDE 1: NO TOCAR TÍTULO
    # ========================================
    # El título "Sentinel - Cambios Morfológicos y anomalías térmicas"
    # NO se modifica, se mantiene de la plantilla
    
    # ========================================
    # MODIFICAR SLIDE 2 (índice 1)
    # ========================================
    if len(prs.slides) < 2:
        print(f"   ❌ Plantilla debe tener al menos 2 slides")
        return None
    
    slide = prs.slides[1]  # Slide 2 (índice 1)
    
    # Formatear fechas en español
    fecha_inicio_es = formatear_fecha_espanol(fecha_inicio)
    fecha_fin_es = formatear_fecha_espanol(fecha_fin)
    
    # Extraer año de fecha_fin
    año = fecha_fin.split('-')[0]
    
    # ========================================
    # TEXTOS QUE DEBEN MANTENERSE (FORMATO EXACTO PLANTILLA)
    # ========================================
    # ETIQUETA RGB (debe estar arriba en la plantilla):
    texto_rgb_correcto = f"Imágenes Sentinel 2 L2A color verdadero, Time Lapse {fecha_inicio_es} – {fecha_fin_es} {año}"
    
    # ETIQUETA THERMAL (debe estar abajo en la plantilla):
    texto_thermal_correcto = f"Imágenes Sentinel 2 L2A falso color (SWIR), Time Lapse {fecha_inicio_es} – {fecha_fin_es} {año}"
    
    # ========================================
    # REEMPLAZAR TEXTOS EN SLIDE (PRESERVANDO FORMATO)
    # ========================================
    textos_encontrados = 0
    
    for shape in slide.shapes:
        if hasattr(shape, "text") and hasattr(shape, "text_frame"):
            texto_actual = shape.text
            
            # Detectar si es el texto RGB (contiene "color verdadero")
            if "color verdadero" in texto_actual.lower():
                # PRESERVAR FORMATO ORIGINAL
                if shape.text_frame.paragraphs:
                    p = shape.text_frame.paragraphs[0]
                    
                    # Guardar formato original del primer run
                    formato_original = None
                    if p.runs:
                        formato_original = {
                            'font_name': p.runs[0].font.name,
                            'font_size': p.runs[0].font.size,
                            'bold': p.runs[0].font.bold,
                            'italic': p.runs[0].font.italic
                        }
                    
                    # Limpiar y reescribir
                    p.clear()
                    run = p.add_run()
                    run.text = texto_rgb_correcto
                    
                    # Aplicar formato original
                    if formato_original:
                        run.font.name = formato_original['font_name']
                        run.font.size = formato_original['font_size']
                        run.font.bold = formato_original['bold']
                        run.font.italic = formato_original['italic']
                    
                    print(f"   ✅ Actualizado texto RGB (formato preservado)")
                    textos_encontrados += 1
            
            # Detectar si es el texto Thermal (contiene "falso color" o "SWIR")
            elif "falso color" in texto_actual.lower() or "swir" in texto_actual.lower():
                if shape.text_frame.paragraphs:
                    p = shape.text_frame.paragraphs[0]
                    
                    # Guardar formato original
                    formato_original = None
                    if p.runs:
                        formato_original = {
                            'font_name': p.runs[0].font.name,
                            'font_size': p.runs[0].font.size,
                            'bold': p.runs[0].font.bold,
                            'italic': p.runs[0].font.italic
                        }
                    
                    # Limpiar y reescribir
                    p.clear()
                    run = p.add_run()
                    run.text = texto_thermal_correcto
                    
                    # Aplicar formato original
                    if formato_original:
                        run.font.name = formato_original['font_name']
                        run.font.size = formato_original['font_size']
                        run.font.bold = formato_original['bold']
                        run.font.italic = formato_original['italic']
                    
                    print(f"   ✅ Actualizado texto Thermal (formato preservado)")
                    textos_encontrados += 1
    
    if textos_encontrados < 2:
        print(f"   ⚠️ Solo se encontraron {textos_encontrados} textos para actualizar")
    
    # ========================================
    # REEMPLAZAR GIFS (MANTENER POSICIÓN EXACTA)
    # ========================================
    imagenes_reemplazadas = 0
    
    # Identificar imágenes existentes por posición Y
    shapes_imagenes = []
    for shape in slide.shapes:
        if shape.shape_type == 13:  # 13 = Picture
            shapes_imagenes.append({
                'shape': shape,
                'top': shape.top,
                'left': shape.left,
                'width': shape.width,
                'height': shape.height
            })
    
    # Ordenar por posición Y (arriba primero)
    shapes_imagenes.sort(key=lambda x: x['top'])
    
    if len(shapes_imagenes) >= 2:
        # Primera imagen (arriba) = RGB
        shape_rgb = shapes_imagenes[0]
        
        # Eliminar imagen original
        sp = shape_rgb['shape'].element
        sp.getparent().remove(sp)
        
        # Insertar GIF RGB en misma posición
        slide.shapes.add_picture(
            gif_rgb_final,
            shape_rgb['left'],
            shape_rgb['top'],
            shape_rgb['width'],
            shape_rgb['height']
        )
        
        print(f"   🖼️ GIF RGB insertado (arriba)")
        imagenes_reemplazadas += 1
        
        # Segunda imagen (abajo) = Thermal
        shape_thermal = shapes_imagenes[1]
        
        # Eliminar imagen original
        sp = shape_thermal['shape'].element
        sp.getparent().remove(sp)
        
        # Insertar GIF Thermal en misma posición
        slide.shapes.add_picture(
            gif_thermal_final,
            shape_thermal['left'],
            shape_thermal['top'],
            shape_thermal['width'],
            shape_thermal['height']
        )
        
        print(f"   🖼️ GIF Thermal insertado (abajo)")
        imagenes_reemplazadas += 1
    else:
        print(f"   ⚠️ Solo se encontraron {len(shapes_imagenes)} imágenes en slide")
    
    # ========================================
    # GUARDAR PPT
    # ========================================
    carpeta_reportes = os.path.join(OUTPUT_DIR, volcan_nombre, "reportes")
    os.makedirs(carpeta_reportes, exist_ok=True)
    
    # Nombre: Volcan_YYYY-MM.pptx
    mes_año = fecha_fin[:7]  # YYYY-MM
    output_filename = f"{volcan_nombre}_{mes_año}.pptx"
    output_path = os.path.join(carpeta_reportes, output_filename)
    
    try:
        prs.save(output_path)
        
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        
        print(f"   ✅ PPT generado: {output_path}")
        print(f"   📦 Tamaño final: {size_mb:.2f} MB")
        
        if size_mb > 3.0:
            print(f"   ⚠️ PPT pesa más de 3 MB ({size_mb:.2f} MB)")
        else:
            print(f"   ✅ Tamaño OK (< 3 MB)")
        
        # Limpiar archivos temporales
        try:
            os.remove(temp_rgb)
            os.remove(temp_thermal)
        except:
            pass
        
        return output_path
    
    except Exception as e:
        print(f"   ❌ Error guardando PPT: {e}")
        return None


def main():
    """Proceso principal"""
    
    print("="*80)
    print("📊 GENERADOR DE PPT V4.0 - CORREGIDO")
    print("   - Preserva título original de plantilla")
    print("   - Preserva formato de fuentes")
    print("   - Comprime GIFs para < 3MB")
    print("="*80)
    
    if not os.path.exists(PLANTILLA_PATH):
        print(f"\n❌ No se encuentra plantilla: {PLANTILLA_PATH}")
        print(f"   Coloca el archivo 'Cambios_morfologicos.pptx' en data/")
        return
    
    ppts_generados = []
    
    for volcan in VOLCANES_ACTIVOS:
        try:
            ppt_path = generar_ppt(volcan)
            if ppt_path:
                ppts_generados.append(ppt_path)
        except Exception as e:
            print(f"❌ Error procesando {volcan}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "="*80)
    print(f"✅ PROCESO COMPLETADO - {len(ppts_generados)} PPTs generados")
    print("="*80)
    
    for ppt in ppts_generados:
        size_mb = os.path.getsize(ppt) / (1024 * 1024)
        status = "✅" if size_mb < 3.0 else "⚠️"
        print(f"   {status} {os.path.basename(ppt)}: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
