"""
PPT_GENERATOR.PY V2.0 - CORREGIDO
Genera presentación PowerPoint mensual con:
- GIFs de timelapses (no imágenes estáticas)
- Texto dinámico por volcán y mes
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from datetime import datetime
import os
import glob
from io import BytesIO

# =========================
# CONFIGURACIÓN
# =========================

VOLCANES_ACTIVOS = ["Villarrica", "Llaima"]
TEMPLATE_PPT = "data/Cambios_morfologicos.pptx"  # Plantilla en el repositorio

# Meses en español
MESES_ES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

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
        
        dia_inicio = int(fecha_inicio.split('-')[2])
        dia_fin = int(fecha_fin.split('-')[2])
        mes_nombre = MESES_ES[mes]
        
        rango_fechas_rgb = f"Imágenes Sentinel 2 L2A color verdadero\nTime Lapse {dia_inicio:02d} {mes_nombre} – {dia_fin:02d} {mes_nombre} {año}"
        rango_fechas_thermal = f"Imágenes Sentinel 2 L2A falso color térmico\nTime Lapse {dia_inicio:02d} {mes_nombre} – {dia_fin:02d} {mes_nombre} {año}"
    else:
        mes_nombre = MESES_ES[mes]
        rango_fechas_rgb = f"Imágenes Sentinel 2 L2A color verdadero\nTime Lapse {mes_str}"
        rango_fechas_thermal = f"Imágenes Sentinel 2 L2A falso color térmico\nTime Lapse {mes_str}"
    
    print(f"   📅 Rango: {rango_fechas_rgb.split('Time Lapse ')[1]}")
    
    # ========================================
    # FIX 3: Generar texto de conclusión dinámico
    # ========================================
    mes_nombre_conclusion = MESES_ES[mes]
    conclusion_text = (
        f"No se registran cambios morfológicos ni anomalías térmicas "
        f"desde imágenes Sentinel 2 L2A. No se registran datos asociados "
        f"a actividad superficial en volcán {volcan_nombre} durante el mes "
        f"de {mes_nombre_conclusion} {año}"
    )
    
    print(f"   📝 Conclusión: 'volcán {volcan_nombre} durante el mes de {mes_nombre_conclusion} {año}'")
    
    # Modificar slide
    slide = prs.slides[0]
    
    # SHAPE 1: Título - "Cambios Morfológicos"
    # SHAPE 2: Imagen RGB (izquierda) - posición x=0.49"
    # SHAPE 3: Imagen Thermal (derecha) - posición x=6.69"
    # SHAPE 4: Texto evaluación (abajo) - CONCLUSIÓN DINÁMICA
    # SHAPE 5: Texto RGB (título derecho) - posición x=5.15"
    # SHAPE 6: Texto Thermal (título izquierdo) - posición x=-1.42"
    
    shapes_to_remove = []
    
    for idx, shape in enumerate(slide.shapes):
        if hasattr(shape, "text"):
            # Título principal
            if "Cambios Morfológicos" in shape.text:
                shape.text = f"Cambios Morfológicos - {volcan_nombre}"
                print(f"   ✅ Actualizado título")
            
            # ========================================
            # FIX 3: Actualizar texto de conclusión
            # ========================================
            # Detectar por contenido (Tupungatito o texto característico)
            elif "No se registran cambios morfológicos" in shape.text or \
                 "Tupungatito" in shape.text or \
                 "diciembre 2025" in shape.text or \
                 "actividad superficial" in shape.text:
                shape.text = conclusion_text
                print(f"   ✅ Actualizado conclusión dinámica")
            
            # Identificar textos por posición
            elif hasattr(shape, 'left'):
                x_pos = shape.left.inches
                
                # Texto derecho (x > 5) = RGB
                if x_pos > 5:
                    shape.text = rango_fechas_rgb
                    print(f"   ✅ Actualizado texto RGB (x={x_pos:.2f}\")")
                
                # Texto izquierdo (x < 5) = Thermal
                elif "Time Lapse" in shape.text or "Imágenes Sentinel" in shape.text:
                    shape.text = rango_fechas_thermal
                    print(f"   ✅ Actualizado texto Thermal (x={x_pos:.2f}\")")
        
        # Marcar imágenes para reemplazo
        if shape.shape_type == 13:  # Picture
            shapes_to_remove.append((idx, shape))
    
    # ========================================
    # FIX 2: Reemplazar imágenes con GIFs (no PNGs estáticos)
    # ========================================
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
            print(f"   🖼️ Insertando GIF RGB en posición izquierda (x={x_pos:.2f}\")")
        else:
            gif_path = gif_thermal_path
            print(f"   🖼️ Insertando GIF Thermal en posición derecha (x={x_pos:.2f}\")")
        
        # Eliminar imagen antigua
        sp = shape.element
        sp.getparent().remove(sp)
        
        # ========================================
        # CRÍTICO: Agregar GIF (no PNG estático)
        # ========================================
        slide.shapes.add_picture(gif_path, left, top, width, height)
    
    # Guardar PPT
    carpeta_output = f"data/sentinel2/{volcan_nombre}/reportes"
    os.makedirs(carpeta_output, exist_ok=True)
    
    output_path = f"{carpeta_output}/{volcan_nombre}_Evaluacion_Mensual_{año}-{mes:02d}.pptx"
    prs.save(output_path)
    
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"   ✅ PPT generado: {output_path}")
    print(f"   📦 Tamaño: {size_mb:.2f} MB")
    
    return output_path


# =========================
# PROCESO PRINCIPAL
# =========================

def main():
    print("="*80)
    print("📊 GENERADOR PPT EVALUACIÓN MENSUAL V2.0")
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
        print(f"   📁 {ppt}")


if __name__ == "__main__":
    main()
