"""
SELECTOR_FECHAS_TIMELAPSE.PY
Permite seleccionar rango de fechas para generar timelapses
Dentro de los Ãºltimos 2 meses disponibles
"""

import os
import glob
from datetime import datetime
import json

def listar_fechas_disponibles(volcan_nombre, tipo='RGB'):
    """Lista todas las fechas disponibles para un volcÃ¡n"""
    carpeta = f"docs/sentinel2/{volcan_nombre}/{tipo}"
    
    if not os.path.exists(carpeta):
        return []
    
    imagenes = sorted(glob.glob(f"{carpeta}/*.png"))
    fechas = []
    
    for img_path in imagenes:
        nombre = os.path.basename(img_path)
        fecha = nombre.split('_')[0]  # YYYY-MM-DD
        fechas.append(fecha)
    
    return sorted(set(fechas))

def seleccionar_rango_fechas(volcan_nombre):
    """
    Permite seleccionar rango de fechas para timelapse
    
    Returns:
        tuple: (fecha_inicio, fecha_fin) o None si no hay fechas
    """
    
    print(f"\nðŸ“… Fechas disponibles para {volcan_nombre}:")
    print("="*60)
    
    # Listar fechas RGB (asumiendo que RGB y Thermal tienen las mismas)
    fechas = listar_fechas_disponibles(volcan_nombre, 'RGB')
    
    if not fechas:
        print("   âš ï¸ No hay fechas disponibles")
        return None
    
    # Mostrar fechas con Ã­ndices
    for i, fecha in enumerate(fechas, 1):
        print(f"   {i:2d}. {fecha}")
    
    print("\n" + "="*60)
    print(f"Total de fechas: {len(fechas)}")
    
    # OpciÃ³n 1: Usar todas las fechas
    print("\nðŸŽ¯ OPCIONES:")
    print("   1. Usar TODAS las fechas disponibles")
    print("   2. Seleccionar rango personalizado")
    print("   3. Ãšltimos 30 dÃ­as")
    print("   4. Este mes (del 1 al Ãºltimo dÃ­a disponible)")
    
    try:
        opcion = input("\nSelecciona opciÃ³n (1-4): ").strip()
        
        if opcion == '1':
            # Todas las fechas
            return fechas[0], fechas[-1]
        
        elif opcion == '2':
            # Rango personalizado
            print(f"\nFecha mÃ¡s antigua: {fechas[0]}")
            print(f"Fecha mÃ¡s reciente: {fechas[-1]}")
            
            fecha_inicio = input("\nFecha inicio (YYYY-MM-DD): ").strip()
            fecha_fin = input("Fecha fin (YYYY-MM-DD): ").strip()
            
            # Validar que existan
            if fecha_inicio not in fechas or fecha_fin not in fechas:
                print("âš ï¸ Fechas no vÃ¡lidas")
                return None
            
            if fecha_inicio > fecha_fin:
                print("âš ï¸ Fecha inicio debe ser anterior a fecha fin")
                return None
            
            return fecha_inicio, fecha_fin
        
        elif opcion == '3':
            # Ãšltimos 30 dÃ­as
            from datetime import datetime, timedelta
            ahora = datetime.now()
            hace_30 = (ahora - timedelta(days=30)).strftime('%Y-%m-%d')
            
            fechas_filtradas = [f for f in fechas if f >= hace_30]
            
            if not fechas_filtradas:
                print("âš ï¸ No hay fechas en los Ãºltimos 30 dÃ­as")
                return None
            
            return fechas_filtradas[0], fechas_filtradas[-1]
        
        elif opcion == '4':
            # Este mes
            mes_actual = datetime.now().strftime('%Y-%m')
            fechas_este_mes = [f for f in fechas if f.startswith(mes_actual)]
            
            if not fechas_este_mes:
                print("âš ï¸ No hay fechas en este mes")
                return None
            
            return fechas_este_mes[0], fechas_este_mes[-1]
        
        else:
            print("âš ï¸ OpciÃ³n no vÃ¡lida")
            return None
    
    except KeyboardInterrupt:
        print("\nâš ï¸ Cancelado")
        return None

def guardar_config_timelapse(volcan_nombre, fecha_inicio, fecha_fin):
    """Guarda configuraciÃ³n de timelapse en JSON"""
    config = {
        'volcan': volcan_nombre,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'generado': datetime.now().isoformat()
    }
    
    os.makedirs('docs/sentinel2/configs', exist_ok=True)
    config_path = f'docs/sentinel2/configs/timelapse_{volcan_nombre}.json'
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nâœ… ConfiguraciÃ³n guardada: {config_path}")
    return config_path

def main():
    """Script interactivo para configurar timelapses"""
    
    print("="*80)
    print("ðŸ“… SELECTOR DE FECHAS PARA TIMELAPSES")
    print("="*80)
    
    # Listar volcanes con imÃ¡genes
    volcanes_disponibles = []
    for volcan in ['Villarrica', 'Llaima']:
        if os.path.exists(f"docs/sentinel2/{volcan}/RGB"):
            volcanes_disponibles.append(volcan)
    
    if not volcanes_disponibles:
        print("\nâš ï¸ No hay volcanes con imÃ¡genes disponibles")
        return
    
    print("\nðŸŒ‹ Volcanes disponibles:")
    for i, volcan in enumerate(volcanes_disponibles, 1):
        print(f"   {i}. {volcan}")
    
    try:
        seleccion = int(input("\nSelecciona volcÃ¡n (nÃºmero): ").strip())
        
        if seleccion < 1 or seleccion > len(volcanes_disponibles):
            print("âš ï¸ SelecciÃ³n no vÃ¡lida")
            return
        
        volcan_nombre = volcanes_disponibles[seleccion - 1]
        
        # Seleccionar rango de fechas
        rango = seleccionar_rango_fechas(volcan_nombre)
        
        if rango:
            fecha_inicio, fecha_fin = rango
            
            print("\n" + "="*80)
            print("âœ… CONFIGURACIÃ“N CONFIRMADA")
            print("="*80)
            print(f"VolcÃ¡n: {volcan_nombre}")
            print(f"Fecha inicio: {fecha_inicio}")
            print(f"Fecha fin: {fecha_fin}")
            
            # Guardar configuraciÃ³n
            guardar_config_timelapse(volcan_nombre, fecha_inicio, fecha_fin)
            
            print("\nðŸŽ¬ Siguiente paso:")
            print("   python timelapse_generator.py")
    
    except (ValueError, KeyboardInterrupt):
        print("\nâš ï¸ Cancelado")

if __name__ == "__main__":
    main()
