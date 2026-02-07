"""
REPARAR_IMAGENES_NEGRAS.PY
Detecta imágenes negras y las marca para re-descarga
"""

import os
import glob
from PIL import Image
import numpy as np

VOLCANES = [
    'Taapaca', 'Parinacota', 'Guallatiri', 'Isluga', 'Irruputuncu', 'Ollague', 
    'San Pedro', 'Lascar', 'Tupungatito', 'San Jose', 'Tinguiririca', 
    'Planchon-Peteroa', 'Descabezado Grande', 'Tatara-San Pedro', 
    'Laguna del Maule', 'Nevado de Longavi', 'Nevados de Chillan',
    'Antuco', 'Copahue', 'Callaqui', 'Lonquimay', 'Llaima', 'Sollipulli', 
    'Villarrica', 'Quetrupillan', 'Lanin', 'Mocho-Choshuenco', 
    'Carran - Los Venados', 'Puyehue - Cordon Caulle', 
    'Antillanca - Casablanca', 'Osorno', 'Calbuco', 'Yate', 'Hornopiren', 
    'Huequi', 'Michinmahuida', 'Chaiten', 'Corcovado', 'Melimoyu', 
    'Mentolat', 'Cay', 'Maca', 'Hudson'
]

def is_black_image(image_path, threshold=5):
    """
    Detecta si una imagen es completamente negra
    
    Args:
        image_path: Path a la imagen
        threshold: Umbral de brillo promedio (0-255)
    
    Returns:
        True si es negra (mean < threshold)
    """
    try:
        img = Image.open(image_path)
        arr = np.array(img)
        mean_brightness = arr.mean()
        
        return mean_brightness < threshold
    except Exception as e:
        print(f"      Error: {e}")
        return False

def scan_volcano(volcan_nombre):
    """Escanea imágenes de un volcán y detecta las negras"""
    
    carpeta = f"docs/sentinel2/{volcan_nombre}"
    
    if not os.path.exists(carpeta):
        return []
    
    imagenes_negras = []
    
    # Buscar todas las imágenes PNG
    for img_path in glob.glob(f"{carpeta}/*.png"):
        if is_black_image(img_path):
            imagenes_negras.append(img_path)
    
    return imagenes_negras

def main():
    print("="*80)
    print("DETECTANDO IMÁGENES NEGRAS")
    print("="*80)
    
    todas_negras = []
    
    for volcan in VOLCANES:
        print(f"\n🌋 {volcan}")
        negras = scan_volcano(volcan)
        
        if negras:
            print(f"   ❌ {len(negras)} imágenes negras encontradas")
            for img in negras:
                nombre = os.path.basename(img)
                print(f"      - {nombre}")
                todas_negras.append(img)
        else:
            print(f"   ✅ Sin imágenes negras")
    
    print("\n" + "="*80)
    print(f"RESUMEN: {len(todas_negras)} imágenes negras en total")
    print("="*80)
    
    if todas_negras:
        print("\nPara re-descargar:")
        print("1. Ejecutar: python sentinel2_downloader.py (con MODO_SOBRESCRITURA=True)")
        print("2. O borrar manualmente las imágenes negras")
    
    # Guardar lista
    with open('imagenes_negras.txt', 'w') as f:
        for img in todas_negras:
            f.write(img + '\n')
    
    print(f"\n✅ Lista guardada en: imagenes_negras.txt")

if __name__ == "__main__":
    main()
