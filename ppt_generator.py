"""
PPT_GENERATOR.PY
Genera presentación PowerPoint mensual con GIFs de timelapses
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from datetime import datetime
import os
import glob
from io import BytesIO
from PIL import Image

# =========================
# CONFIGURACIÓN
# =========================

VOLCANES_ACTIVOS = ["Villarrica", "Llaima"]
TEMPLATE_PPT = "data/Cambios_morfologicos.pptx"  # Plantilla en el repositorio
CALIDAD_COMPRESION = 85  # Calidad JPEG (1-100, 85 = buen balance)

# =========================
# FUNCIÓN DE COMPRESIÓN
# =========================

def comprimir_gif_para_ppt(gif_path, calidad=CALIDAD_COMPRESION):
    """
    Comprime GIF para reducir tamaño en PPT
    
    Args:
        gif_path: Path al GIF original
        calidad: Calidad JPEG (1-100)
    
    Returns:
        str: Path al GIF comprimido temporal
    """
    try:
        # Abrir GIF
        img = Image.open(gif_path)
        
        # Crear path temporal
        temp_path = gif_path.replace('.gif', '_compressed.jpg')
        
        # Para GIF animado, tomar primer frame
        if hasattr(img, 'n_frames') and img.n_frames > 1:
            img.seek(0)  # Primer frame
        
        # Convertir a RGB si necesario
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Guardar como JPEG comprimido
        img.save(temp_path, 'JPEG', quality=calidad, optimize=True)
        
        # Reportar reducción
        size_original = os.path.getsize(gif_path) / 1024
        size_comprimida = os.path.getsize(temp_path) / 1024
        reduccion = ((size_original - size_comprimida) / size_original) * 100
        
        print(f"      📦 Comprimido: {size_original:.0f} KB → {size_comprimida:.0f} KB ({reduccion:.0f}% menos)")
        
        return temp_path
    
    except Exception as e:
        print(f"      ⚠️ Error comprimiendo: {e}")
        return gif_path  # Retornar original si falla

# =========================
# GENERADOR PPT
# =========================

def generar_ppt_mensual(volcan_nombre, mes=None, año=None):
    """
    Genera PPT mensual para un volcán
    
    Args:
        volcan_nombre: Nombre del volcán
        mes: Mes (1-12), si None usa mes anterior
        año: Año, si None usa año actual
    
    Returns:
        str: Path al PPT generado
    """
    
    # Si no se especifica mes/año, usar mes anterior
    if mes is None or año is None:
        ahora = datetime.now()
        if ahora.month == 1:
            mes = 12
            año = ahora.year - 1
        else:
            mes = ahora.month - 1
            año = ahora.year
    
    print(f"\n📊 Generando PPT: {volcan_nombre} - {año}-{mes:02d}")
    
    # Cargar plantilla
    if not os.path.exists(TEMPLATE_PPT):
        print(f"   ❌ Plantilla no encontrada: {TEMPLATE_PPT}")
        return None
    
    prs = Presentation(TEMPLATE_PPT)
    
    # Buscar GIFs del mes
    carpeta_timelapses = f"data/sentinel2/{volcan_nombre}/timelapses"
    mes_str = f"{año}-{mes:02d}"
    
    gif_rgb_path = f"{carpeta_timelapses}/{volcan_nombre}_RGB_{mes_str}.gif"
    gif_thermal_path = f"{carpeta_timelapses}/{volcan_nombre}_ThermalFalseColor_{mes_str}.gif"
    
    if not os.path.exists(gif_rgb_path) or not os.path.exists(gif_thermal_path):
        print(f"   ⚠️ No se encontraron GIFs para {mes_str}")
        print(f"      Buscado: {gif_rgb_path}")
        return None
    
    print(f"   ✅ GIF RGB: {gif_rgb_path}")
    print(f"   ✅ GIF Thermal: {gif_thermal_path}")
    
    # Obtener rango de fechas de los GIFs
    carpeta_rgb = f"data/sentinel2/{volcan_nombre}/RGB"
    imagenes_mes = sorted(glob.glob(f"{carpeta_rgb}/{año}-{mes:02d}-*.png"))
    
    if imagenes_mes:
        fecha_inicio = os.path.basename(imagenes_mes[0]).split('_')[0]
        fecha_fin = os.path.basename(imagenes_mes[-1]).split('_')[0]
        
        # Formato: "02 diciembre – 30 diciembre 2025"
        meses_es = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        
        dia_inicio = int(fecha_inicio.split('-')[2])
        dia_fin = int(fecha_fin.split('-')[2])
        mes_nombre = meses_es[mes]
        
        rango_fechas_rgb = f"Imágenes Sentinel 2 L2A color verdadero\nTime Lapse {dia_inicio:02d} {mes_nombre} – {dia_fin:02d} {mes_nombre} {año}"
        rango_fechas_thermal = f"Imágenes Sentinel 2 L2A falso color térmico\nTime Lapse {dia_inicio:02d} {mes_nombre} – {dia_fin:02d} {mes_nombre} {año}"
    else:
        rango_fechas_rgb = f"Imágenes Sentinel 2 L2A color verdadero\nTime Lapse {mes_str}"
        rango_fechas_thermal = f"Imágenes Sentinel 2 L2A falso color térmico\nTime Lapse {mes_str}"
    
    print(f"   📅 Rango: {rango_fechas_rgb.split('Time Lapse ')[1]}")
    
    # Modificar slide
    slide = prs.slides[0]
    
    # SHAPE 1: Título - "Cambios Morfológicos"
    # SHAPE 2: Imagen RGB (izquierda) - posición x=0.49"
    # SHAPE 3: Imagen Thermal (derecha) - posición x=6.69"
    # SHAPE 4: Texto evaluación (abajo)
    # SHAPE 5: Texto IZQUIERDA (RGB) - posición x < 5
    # SHAPE 6: Texto DERECHA (Thermal) - posición x > 5
    
    shapes_to_remove = []
    
    for idx, shape in enumerate(slide.shapes):
        if hasattr(shape, "text"):
            # Título principal
            if "Cambios Morfológicos" in shape.text:
                # Preservar formato modificando runs en vez de reemplazar texto
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        if "Cambios Morfológicos" in run.text:
                            run.text = f"Cambios Morfológicos - {volcan_nombre}"
                print(f"   ✅ Actualizado título")
            
            # Identificar textos por posición
            elif hasattr(shape, 'left'):
                x_pos = shape.left.inches
                
                # FIX CRÍTICO: Invertir lógica (estaba al revés)
                # Texto DERECHO (x > 5) = THERMAL (derecha)
                if x_pos > 5 and ("Time Lapse" in shape.text or "Imágenes Sentinel" in shape.text):
                    # Preservar formato
                    for paragraph in shape.text_frame.paragraphs:
                        paragraph.clear()  # Limpiar párrafo
                    # Agregar texto nuevo con formato original
                    p = shape.text_frame.paragraphs[0]
                    p.text = rango_fechas_thermal
                    print(f"   ✅ Actualizado texto THERMAL derecho (x={x_pos:.2f}\")")
                
                # Texto IZQUIERDO (x < 5) = RGB (izquierda)
                elif x_pos < 5 and ("Time Lapse" in shape.text or "Imágenes Sentinel" in shape.text):
                    # Preservar formato
                    for paragraph in shape.text_frame.paragraphs:
                        paragraph.clear()
                    p = shape.text_frame.paragraphs[0]
                    p.text = rango_fechas_rgb
                    print(f"   ✅ Actualizado texto RGB izquierdo (x={x_pos:.2f}\")")
        
        # Marcar imágenes para reemplazo
        if shape.shape_type == 13:  # Picture
            shapes_to_remove.append((idx, shape))
    
    # Reemplazar imágenes (de atrás hacia adelante para no afectar índices)
    imagenes_temporales = []  # Para limpiar después
    
    for idx, shape in reversed(shapes_to_remove):
        left = shape.left
        top = shape.top
        width = shape.width
        height = shape.height
        x_pos = left.inches
        
        # Imagen izquierda (x < 4) = RGB
        # Imagen derecha (x > 4) = Thermal
        if x_pos < 4:
            gif_path = gif_rgb_path
            print(f"   🖼️ Reemplazando imagen izquierda (x={x_pos:.2f}\") con RGB")
        else:
            gif_path = gif_thermal_path
            print(f"   🖼️ Reemplazando imagen derecha (x={x_pos:.2f}\") con Thermal")
        
        # Comprimir GIF antes de insertar
        gif_comprimido = comprimir_gif_para_ppt(gif_path)
        imagenes_temporales.append(gif_comprimido)
        
        # Eliminar imagen antigua
        sp = shape.element
        sp.getparent().remove(sp)
        
        # Agregar imagen comprimida en la misma posición
        slide.shapes.add_picture(gif_comprimido, left, top, width, height)
    
    # Guardar PPT
    carpeta_output = f"data/sentinel2/{volcan_nombre}/reportes"
    os.makedirs(carpeta_output, exist_ok=True)
    
    output_path = f"{carpeta_output}/{volcan_nombre}_Evaluacion_Mensual_{año}-{mes:02d}.pptx"
    prs.save(output_path)
    
    # Limpiar imágenes temporales
    for temp_img in imagenes_temporales:
        if temp_img.endswith('_compressed.jpg') and os.path.exists(temp_img):
            try:
                os.remove(temp_img)
            except:
                pass
    
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"   ✅ PPT generado: {output_path}")
    print(f"   📦 Tamaño: {size_mb:.2f} MB")
    
    return output_path


# =========================
# PROCESO PRINCIPAL
# =========================

def main():
    print("="*80)
    print("📊 GENERADOR PPT EVALUACIÓN MENSUAL")
    print("="*80)
    
    ppts_generados = []
    
    for volcan in VOLCANES_ACTIVOS:
        ppt_path = generar_ppt_mensual(volcan)
        if ppt_path:
            ppts_generados.append(ppt_path)
    
    print("\n" + "="*80)
    print(f"✅ PROCESO COMPLETADO - {len(ppts_generados)} PPTs generados")
    print("="*80)
    
    for ppt in ppts_generados:
        print(f"   📄 {ppt}")


if __name__ == "__main__":
    main()
