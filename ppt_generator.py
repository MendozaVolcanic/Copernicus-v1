"""
PPT_GENERATOR.PY V5.1
BASE: V5.0 + Integración sistema de caché

NUEVO V5.1:
- Import de gif_cache (los GIFs ya están cacheados por timelapse_generator.py)
- Mensaje informativo sobre GIFs encontrados
- NO genera GIFs (solo los usa)
"""

import os
import glob
import copy
from datetime import datetime
from pptx import Presentation
from PIL import Image

# =========================
# NUEVO V5.1: IMPORT SISTEMA DE CACHÉ
# =========================
# Nota: ppt_generator NO genera GIFs, solo los usa
# El caché ya fue implementado en timelapse_generator.py
from gif_cache import existe_en_cache

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
PLANTILLA_PATH = "docs/plantillas/Cambios_morfologicos.pptx"
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

def comprimir_gif(input_path, output_path, max_size_mb=1.0):
    try:
        size_mb = os.path.getsize(input_path) / (1024 * 1024)
        if size_mb <= max_size_mb:
            import shutil
            shutil.copy2(input_path, output_path)
            print(f"      ✅ GIF OK ({size_mb:.2f} MB)")
            return output_path
        
        print(f"      🔽 Comprimiendo ({size_mb:.2f} MB > {max_size_mb:.2f} MB)...")
        img = Image.open(input_path)
        frames = []
        try:
            while True:
                # Reducir colores a 64 (más agresivo)
                frame = img.copy().convert('P', palette=Image.ADAPTIVE, colors=64)
                frames.append(frame)
                img.seek(img.tell() + 1)
        except EOFError:
            pass
        
        # Reducir tamaño de frames si muy grande
        if size_mb > 2.0:
            new_size = (int(frames[0].width * 0.75), int(frames[0].height * 0.75))
            frames = [f.resize(new_size, Image.Resampling.LANCZOS) for f in frames]
        
        frames[0].save(output_path, save_all=True, append_images=frames[1:],
                      optimize=True, duration=img.info.get('duration', 100), loop=0)
        print(f"      ✅ {size_mb:.2f} MB → {os.path.getsize(output_path)/(1024*1024):.2f} MB")
        return output_path
    except Exception as e:
        print(f"      ❌ Error: {e}")
        import shutil
        shutil.copy2(input_path, output_path)
        return output_path

def generar_ppt(volcan_nombre):
    print(f"\n🌋 {volcan_nombre}")
    
    carpeta_timelapses = f"docs/sentinel2/{volcan_nombre}/timelapses_ppt"
    if not os.path.exists(carpeta_timelapses):
        print(f"    ❌ No existe: {carpeta_timelapses}")
        return None
    
    # =========================
    # NUEVO V5.1: BUSCAR GIFs (ya cacheados por timelapse_generator.py)
    # =========================
    gifs_rgb = sorted(glob.glob(f"{carpeta_timelapses}/{volcan_nombre}_RGB_*.gif"))
    gifs_thermal = sorted(glob.glob(f"{carpeta_timelapses}/{volcan_nombre}_ThermalFalseColor_*.gif"))
    
    print(f"    📂 GIFs encontrados: RGB={len(gifs_rgb)}, Thermal={len(gifs_thermal)}")
    
    if not gifs_rgb or not gifs_thermal:
        print(f"    ❌ GIFs incompletos")
        return None
    
    gif_rgb_path = gifs_rgb[-1]
    gif_thermal_path = gifs_thermal[-1]
    
    partes = os.path.basename(gif_rgb_path).replace('.gif', '').split('_')
    if len(partes) < 4:
        print(f"    ❌ No se pudieron extraer fechas")
        return None
    
    fecha_inicio, fecha_fin = partes[-2], partes[-1]
    print(f"    📅 {fecha_inicio} → {fecha_fin}")
    
    temp_rgb = f"/tmp/{volcan_nombre}_RGB.gif"
    temp_thermal = f"/tmp/{volcan_nombre}_Thermal.gif"
    
    print(f"    🔽 Comprimiendo GIFs para PPT...")
    gif_rgb_final = comprimir_gif(gif_rgb_path, temp_rgb)
    gif_thermal_final = comprimir_gif(gif_thermal_path, temp_thermal)
    
    if not os.path.exists(PLANTILLA_PATH):
        print(f"    ❌ Plantilla no encontrada")
        return None
    
    prs = Presentation(PLANTILLA_PATH)
    slide = prs.slides[0]
    
    fecha_inicio_es = formatear_fecha_espanol(fecha_inicio)
    fecha_fin_es = formatear_fecha_espanol(fecha_fin)
    ano = fecha_fin.split('-')[0]
    
    texto_rgb = f"Imagenes Sentinel 2 L2A color verdadero, Time Lapse {fecha_inicio_es} → {fecha_fin_es} {ano}"
    texto_thermal = f"Imagenes Sentinel 2 L2A Falso color, Time Lapse {fecha_inicio_es} → {fecha_fin_es} {ano}"
    
    print(f"    ✏️  Actualizando textos...")
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
            print(f"       ✅ RGB")
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
            print(f"       ✅ Thermal")
            textos_ok += 1
        
        # Reemplazar nombre del volcán en texto final
        elif ("volcán" in texto.lower() or "volcan" in texto.lower() or "volcano" in texto.lower()):
            import re
            # Reemplazar TODOS los nombres de volcanes en TODOS los párrafos
            cambio_realizado = False
            for volcan_antiguo in VOLCANES_ACTIVOS:
                if volcan_antiguo.lower() in texto.lower():
                    # Iterar sobre TODOS los párrafos (no solo el primero)
                    for p in shape.text_frame.paragraphs:
                        texto_parrafo = p.text
                        if volcan_antiguo.lower() in texto_parrafo.lower():
                            # Reemplazo case-insensitive
                            patron = re.compile(re.escape(volcan_antiguo), re.IGNORECASE)
                            texto_nuevo_p = patron.sub(volcan_nombre, texto_parrafo)
                            
                            # También reemplazar "mes de [mes] [año]"
                            # Extraer mes y año de fecha_fin
                            from datetime import datetime
                            try:
                                dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
                                mes_actual = MESES_ES[dt.month]
                                ano_actual = dt.year
                                
                                # Buscar patrón "mes de [cualquier mes] [año]"
                                patron_fecha = re.compile(
                                    r'(mes de )\w+(?: \d{4})?',
                                    re.IGNORECASE
                                )
                                texto_nuevo_p = patron_fecha.sub(
                                    f"mes de {mes_actual} {ano_actual}",
                                    texto_nuevo_p
                                )
                            except:
                                pass
                            
                            if texto_nuevo_p != texto_parrafo:
                                # Guardar formato
                                fmt = None
                                if p.runs:
                                    fmt = {'name': p.runs[0].font.name, 'size': p.runs[0].font.size,
                                          'bold': p.runs[0].font.bold, 'italic': p.runs[0].font.italic}
                                
                                # Reemplazar texto
                                p.clear()
                                run = p.add_run()
                                run.text = texto_nuevo_p
                                
                                # Restaurar formato
                                if fmt:
                                    if fmt['name']: run.font.name = fmt['name']
                                    if fmt['size']: run.font.size = fmt['size']
                                    if fmt['bold'] is not None: run.font.bold = fmt['bold']
                                    if fmt['italic'] is not None: run.font.italic = fmt['italic']
                                
                                cambio_realizado = True
            
            if cambio_realizado:
                print(f"       ✅ Nombre volcán actualizado")
                textos_ok += 1
    
    if textos_ok < 2:
        print(f"    ⚠️  Textos: {textos_ok} (esperados 2-3)")
    
    print(f"    🖼️  Reemplazando GIFs...")
    shapes_img = [{'shape': s, 'top': s.top, 'left': s.left, 
                   'width': s.width, 'height': s.height}
                  for s in slide.shapes if s.shape_type == 13]
    shapes_img.sort(key=lambda x: x['top'])
    
    if len(shapes_img) >= 2:
        # RGB (arriba)
        s = shapes_img[0]
        s['shape'].element.getparent().remove(s['shape'].element)
        slide.shapes.add_picture(gif_rgb_final, s['left'], s['top'], s['width'], s['height'])
        print(f"       ✅ RGB")
        
        # Thermal (abajo)
        s = shapes_img[1]
        s['shape'].element.getparent().remove(s['shape'].element)
        slide.shapes.add_picture(gif_thermal_final, s['left'], s['top'], s['width'], s['height'])
        print(f"       ✅ Thermal")
    
    carpeta_reportes = os.path.join(OUTPUT_DIR, volcan_nombre, "reportes")
    os.makedirs(carpeta_reportes, exist_ok=True)
    
    output_path = os.path.join(carpeta_reportes, 
                               f"{volcan_nombre}_Evaluacion_Mensual_{fecha_fin[:7]}.pptx")
    
    try:
        prs.save(output_path)
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        status = "✅" if size_mb < 3.0 else "⚠️"
        print(f"   {status} PPT: {size_mb:.2f} MB")
        
        try:
            os.remove(temp_rgb)
            os.remove(temp_thermal)
        except:
            pass
        
        return output_path
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return None

def _copiar_slide_a_prs(ppt_origen_path, prs_destino):
    """Copia el primer slide de un PPT (incluyendo imágenes) a otra presentación."""
    prs_origen = Presentation(ppt_origen_path)
    slide_origen = prs_origen.slides[0]

    blank_layout = prs_destino.slide_layouts[6]  # layout en blanco
    slide_nuevo = prs_destino.slides.add_slide(blank_layout)

    # Limpiar shapes del slide en blanco
    spTree = slide_nuevo.shapes._spTree
    for child in list(spTree):
        spTree.remove(child)

    # Copiar shapes del slide origen
    for child in slide_origen.shapes._spTree:
        spTree.append(copy.deepcopy(child))

    # Copiar relaciones de imágenes y actualizar rIds en el XML
    NS_A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    NS_R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

    for rel in slide_origen.part.rels.values():
        if 'image' in rel.reltype and not rel.is_external:
            old_rId = rel.rId
            new_rId = slide_nuevo.part.relate_to(rel.target_part, rel.reltype)
            if old_rId != new_rId:
                for blip in slide_nuevo._element.iter(f'{{{NS_A}}}blip'):
                    if blip.get(f'{{{NS_R}}}embed') == old_rId:
                        blip.set(f'{{{NS_R}}}embed', new_rId)


def generar_ppt_combinado(ppts_generados, fecha_inicio, fecha_fin):
    """Genera un PPT con todos los volcanes (1 slide por volcán)."""
    if not ppts_generados:
        print("⚠️  Sin PPTs individuales para combinar")
        return None

    print(f"\n{'='*80}")
    print(f"📚 GENERANDO PPT COMBINADO ({len(ppts_generados)} volcanes)...")

    # El primer PPT se usa como base
    prs = Presentation(ppts_generados[0])

    for ppt_path in ppts_generados[1:]:
        try:
            _copiar_slide_a_prs(ppt_path, prs)
            print(f"   ✅ {os.path.basename(ppt_path)}")
        except Exception as e:
            print(f"   ❌ Error copiando {os.path.basename(ppt_path)}: {e}")

    os.makedirs("docs/reportes", exist_ok=True)
    output_path = f"docs/reportes/Evaluacion_Completa_{fecha_inicio}_{fecha_fin}.pptx"
    prs.save(output_path)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅ PPT combinado: {output_path} ({size_mb:.1f} MB)")
    return output_path


def main():
    print("="*80)
    print("📊 PPT GENERATOR V5.2")
    print("   NUEVO: PPT combinado con todos los volcanes")
    print("="*80)

    if not os.path.exists(PLANTILLA_PATH):
        print(f"\n❌ Plantilla no encontrada: {PLANTILLA_PATH}")
        return

    volcan_env = os.getenv('VOLCAN')
    fecha_inicio_env = os.getenv('FECHA_INICIO')
    fecha_fin_env = os.getenv('FECHA_FIN')

    if volcan_env:
        print(f"\n📋 MODO MANUAL: Procesando {volcan_env}")
        volcanes_a_procesar = [volcan_env]
    else:
        print("\n🤖 MODO AUTOMÁTICO: Procesando todos los volcanes")
        volcanes_a_procesar = VOLCANES_ACTIVOS

    ppts = []
    for volcan in volcanes_a_procesar:
        try:
            ppt = generar_ppt(volcan)
            if ppt:
                ppts.append(ppt)
        except Exception as e:
            print(f"❌ Error en {volcan}: {e}")

    print("\n" + "="*80)
    print(f"✅ {len(ppts)} PPTs individuales generados")
    for ppt in ppts:
        size_mb = os.path.getsize(ppt) / (1024 * 1024)
        print(f"   📄 {os.path.basename(ppt)}: {size_mb:.2f} MB")

    # Generar PPT combinado (solo si hay más de 1 volcán)
    if len(ppts) > 1:
        # Usar fechas de env vars, o derivar del primer GIF disponible
        if not fecha_inicio_env or not fecha_fin_env:
            # Extraer del nombre del primer PPT generado
            partes = os.path.basename(ppts[0]).replace('.pptx', '').split('_')
            fecha_inicio_env = partes[-2] if len(partes) >= 2 else 'fecha'
            fecha_fin_env = partes[-1] if len(partes) >= 1 else 'fin'
        generar_ppt_combinado(ppts, fecha_inicio_env, fecha_fin_env)

    print("="*80)

if __name__ == "__main__":
    main()
