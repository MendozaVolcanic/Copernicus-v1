"""
PPT_GENERATOR.PY V5.0 - CORREGIDO FINAL
NO modifica ttulo - Solo actualiza fechas timelapses - Comprime < 3MB
"""

import os
import glob
from datetime import datetime
from pptx import Presentation
from PIL import Image

VOLCANES_ACTIVOS = [
    # ZONA NORTE
    "Taapaca", "Parinacota", "Guallatiri", "Isluga", "Irruputuncu", "Ollague", "San Pedro", "Lascar",
    # ZONA CENTRO
    "Tupungatito", "San Jose", "Tinguiririca", "Planchon-Peteroa", "Descabezado Grande", 
    "Tatara-San Pedro", "Laguna del Maule", "Nevado de Longavi", "Nevados de Chillan",
    # ZONA SUR
    "Antuco", "Copahue", "Callaqui", "Lonquimay", "Llaima", "Sollipulli", "Villarrica", 
    "Quetrupillan", "Lanin", "Mocho-Choshuenco", "Carran - Los Venados", "Puyehue - Cordon Caulle", 
    "Antillanca - Casablanca",
    # ZONA AUSTRAL
    "Osorno", "Calbuco", "Yate", "Hornopiren", "Huequi", "Michinmahuida", "Chaiten", 
    "Corcovado", "Melimoyu", "Mentolat", "Cay", "Maca", "Hudson"
]
PLANTILLA_PATH = "data/Cambios_morfologicos.pptx"
OUTPUT_DIR = "docs/sentinel2"

MESES_ES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}

def formatear_fecha_espanol(fecha_str):
    try:
        dt = datetime.strptime(fecha_str, '%Y-%m-%d')
        return f"{dt.strftime('%d')} {MESES_ES[dt.month]}"
    except:
        return fecha_str

def comprimir_gif(input_path, output_path, max_size_mb=1.2):
    try:
        size_mb = os.path.getsize(input_path) / (1024 * 1024)
        if size_mb <= max_size_mb:
            import shutil
            shutil.copy2(input_path, output_path)
            print(f"      GIF OK ({size_mb:.2f} MB)")
            return output_path
        
        print(f"      Comprimiendo ({size_mb:.2f} MB  {max_size_mb:.2f} MB)...")
        img = Image.open(input_path)
        frames = []
        try:
            while True:
                frame = img.copy().convert('P', palette=Image.ADAPTIVE, colors=128)
                frames.append(frame)
                img.seek(img.tell() + 1)
        except EOFError:
            pass
        
        frames[0].save(output_path, save_all=True, append_images=frames[1:],
                      optimize=True, duration=img.info.get('duration', 100), loop=0)
        print(f"       {size_mb:.2f} MB  {os.path.getsize(output_path)/(1024*1024):.2f} MB")
        return output_path
    except Exception as e:
        print(f"       Error: {e}")
        import shutil
        shutil.copy2(input_path, output_path)
        return output_path

def generar_ppt(volcan_nombre):
    print(f"\n {volcan_nombre}")
    
    carpeta_timelapses = f"docs/sentinel2/{volcan_nombre}/timelapses"
    if not os.path.exists(carpeta_timelapses):
        print(f"    No existe: {carpeta_timelapses}")
        return None
    
    gifs_rgb = sorted(glob.glob(f"{carpeta_timelapses}/{volcan_nombre}_RGB_*.gif"))
    gifs_thermal = sorted(glob.glob(f"{carpeta_timelapses}/{volcan_nombre}_ThermalFalseColor_*.gif"))
    
    if not gifs_rgb or not gifs_thermal:
        print(f"    GIFs incompletos")
        return None
    
    gif_rgb_path = gifs_rgb[-1]
    gif_thermal_path = gifs_thermal[-1]
    
    partes = os.path.basename(gif_rgb_path).replace('.gif', '').split('_')
    if len(partes) < 4:
        print(f"    No se pudieron extraer fechas")
        return None
    
    fecha_inicio, fecha_fin = partes[-2], partes[-1]
    print(f"    {fecha_inicio}  {fecha_fin}")
    
    temp_rgb = f"/tmp/{volcan_nombre}_RGB.gif"
    temp_thermal = f"/tmp/{volcan_nombre}_Thermal.gif"
    
    print(f"    Comprimiendo...")
    gif_rgb_final = comprimir_gif(gif_rgb_path, temp_rgb)
    gif_thermal_final = comprimir_gif(gif_thermal_path, temp_thermal)
    
    if not os.path.exists(PLANTILLA_PATH):
        print(f"    Plantilla no encontrada")
        return None
    
    prs = Presentation(PLANTILLA_PATH)
    slide = prs.slides[0]
    
    fecha_inicio_es = formatear_fecha_espanol(fecha_inicio)
    fecha_fin_es = formatear_fecha_espanol(fecha_fin)
    ano = fecha_fin.split('-')[0]
    
    texto_rgb = f"Imagenes Sentinel 2 L2A color verdadero, Time Lapse {fecha_inicio_es}  {fecha_fin_es} {ano}"
    texto_thermal = f"Imagenes Sentinel 2 L2A Falso color, Time Lapse {fecha_inicio_es}  {fecha_fin_es} {ano}"
    
    print(f"    Actualizando textos...")
    textos_ok = 0
    
    for shape in slide.shapes:
        if not hasattr(shape, "text_frame") or not hasattr(shape, "text"):
            continue
        
        texto = shape.text.strip()
        
        # Reemplazar texto RGB timelapse
        if "color verdadero" in texto.lower() and "time lapse" in texto.lower():
            p = shape.text_frame.paragraphs[0]
            fmt = None
            if p.runs:
                fmt = {'name': p.runs[0].font.name, 'size': p.runs[0].font.size,
                      'bold': p.runs[0].font.bold, 'italic': p.runs[0].font.italic}
            p.clear()
            run = p.add_run()
            run.text = texto_rgb
            if fmt:
                if fmt['name']: run.font.name = fmt['name']
                if fmt['size']: run.font.size = fmt['size']
                if fmt['bold'] is not None: run.font.bold = fmt['bold']
                if fmt['italic'] is not None: run.font.italic = fmt['italic']
            print(f"       RGB")
            textos_ok += 1
        
        # Reemplazar texto Thermal timelapse
        elif "falso color" in texto.lower() and "time lapse" in texto.lower():
            p = shape.text_frame.paragraphs[0]
            fmt = None
            if p.runs:
                fmt = {'name': p.runs[0].font.name, 'size': p.runs[0].font.size,
                      'bold': p.runs[0].font.bold, 'italic': p.runs[0].font.italic}
            p.clear()
            run = p.add_run()
            run.text = texto_thermal
            if fmt:
                if fmt['name']: run.font.name = fmt['name']
                if fmt['size']: run.font.size = fmt['size']
                if fmt['bold'] is not None: run.font.bold = fmt['bold']
                if fmt['italic'] is not None: run.font.italic = fmt['italic']
            print(f"       Thermal")
            textos_ok += 1
        
        # NUEVO: Reemplazar nombre del volcan en texto final
        elif "volcan" in texto.lower() and "durante el mes" in texto.lower():
            # Buscar cualquier nombre de volcan en el texto
            for volcan_antiguo in VOLCANES_ACTIVOS:
                if volcan_antiguo in texto:
                    # Reemplazar con el volcan actual
                    texto_nuevo = texto.replace(volcan_antiguo, volcan_nombre)
                    
                    p = shape.text_frame.paragraphs[0]
                    fmt = None
                    if p.runs:
                        fmt = {'name': p.runs[0].font.name, 'size': p.runs[0].font.size,
                              'bold': p.runs[0].font.bold, 'italic': p.runs[0].font.italic}
                    p.clear()
                    run = p.add_run()
                    run.text = texto_nuevo
                    if fmt:
                        if fmt['name']: run.font.name = fmt['name']
                        if fmt['size']: run.font.size = fmt['size']
                        if fmt['bold'] is not None: run.font.bold = fmt['bold']
                        if fmt['italic'] is not None: run.font.italic = fmt['italic']
                    print(f"       Nombre volcan")
                    textos_ok += 1
                    break
    
    if textos_ok < 2:
        print(f"    Textos: {textos_ok} (esperados 2-3)")
    
    print(f"    Reemplazando GIFs...")
    shapes_img = [{'shape': s, 'top': s.top, 'left': s.left, 
                   'width': s.width, 'height': s.height}
                  for s in slide.shapes if s.shape_type == 13]
    shapes_img.sort(key=lambda x: x['top'])
    
    if len(shapes_img) >= 2:
        # RGB (arriba)
        s = shapes_img[0]
        s['shape'].element.getparent().remove(s['shape'].element)
        slide.shapes.add_picture(gif_rgb_final, s['left'], s['top'], s['width'], s['height'])
        print(f"       RGB")
        
        # Thermal (abajo)
        s = shapes_img[1]
        s['shape'].element.getparent().remove(s['shape'].element)
        slide.shapes.add_picture(gif_thermal_final, s['left'], s['top'], s['width'], s['height'])
        print(f"       Thermal")
    
    carpeta_reportes = os.path.join(OUTPUT_DIR, volcan_nombre, "reportes")
    os.makedirs(carpeta_reportes, exist_ok=True)
    
    output_path = os.path.join(carpeta_reportes, 
                               f"{volcan_nombre}_Evaluacion_Mensual_{fecha_fin[:7]}.pptx")
    
    try:
        prs.save(output_path)
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        status = "" if size_mb < 3.0 else ""
        print(f"   {status} PPT: {size_mb:.2f} MB")
        
        try:
            os.remove(temp_rgb)
            os.remove(temp_thermal)
        except:
            pass
        
        return output_path
    except Exception as e:
        print(f"    Error: {e}")
        return None

def main():
    print("="*80)
    print(" PPT GENERATOR V5.0 - NO modifica ttulo, solo fechas")
    print("="*80)
    
    if not os.path.exists(PLANTILLA_PATH):
        print(f"\n Plantilla no encontrada: {PLANTILLA_PATH}")
        return
    
    # Leer variables de entorno si existen (para workflow manual)
    volcan_env = os.getenv('VOLCAN')
    
    if volcan_env:
        print(f"\nMODO MANUAL: Procesando {volcan_env}")
        volcanes_a_procesar = [volcan_env]
    else:
        print("\nMODO AUTOMATICO: Procesando todos los volcanes")
        volcanes_a_procesar = VOLCANES_ACTIVOS
    
    ppts = []
    for volcan in volcanes_a_procesar:
        try:
            ppt = generar_ppt(volcan)
            if ppt:
                ppts.append(ppt)
        except Exception as e:
            print(f" Error en {volcan}: {e}")
    
    print("\n" + "="*80)
    print(f" {len(ppts)} PPTs generados")
    for ppt in ppts:
        size_mb = os.path.getsize(ppt) / (1024 * 1024)
        print(f"   {os.path.basename(ppt)}: {size_mb:.2f} MB")
    print("="*80)

if __name__ == "__main__":
    main()
