"""
SELECTOR_FECHAS_TIMELAPSE.PY
Permite seleccionar rango de fechas para generar timelapses
Dentro de los últimos 2 meses disponibles
"""

import os
import glob
from datetime import datetime
import json

def listar_fechas_disponibles(volcan_nombre, tipo='RGB'):
    """Lista todas las fechas disponibles para un volcán"""
    carpeta = f"data/sentinel2/{volcan_nombre}/{tipo}"
    
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
    
    print(f"\n📅 Fechas disponibles para {volcan_nombre}:")
    print("="*60)
    
    # Listar fechas RGB (asumiendo que RGB y Thermal tienen las mismas)
    fechas = listar_fechas_disponibles(volcan_nombre, 'RGB')
    
    if not fechas:
        print("   ⚠️ No hay fechas disponibles")
        return None
    
    # Mostrar fechas con índices
    for i, fecha in enumerate(fechas, 1):
        print(f"   {i:2d}. {fecha}")
    
    print("\n" + "="*60)
    print(f"Total de fechas: {len(fechas)}")
    
    # Opción 1: Usar todas las fechas
    print("\n🎯 OPCIONES:")
    print("   1. Usar TODAS las fechas disponibles")
    print("   2. Seleccionar rango personalizado")
    print("   3. Últimos 30 días")
    print("   4. Este mes (del 1 al último día disponible)")
    
    try:
        opcion = input("\nSelecciona opción (1-4): ").strip()
        
        if opcion == '1':
            # Todas las fechas
            return fechas[0], fechas[-1]
        
        elif opcion == '2':
            # Rango personalizado
            print(f"\nFecha más antigua: {fechas[0]}")
            print(f"Fecha más reciente: {fechas[-1]}")
            
            fecha_inicio = input("\nFecha inicio (YYYY-MM-DD): ").strip()
            fecha_fin = input("Fecha fin (YYYY-MM-DD): ").strip()
            
            # Validar que existan
            if fecha_inicio not in fechas or fecha_fin not in fechas:
                print("⚠️ Fechas no válidas")
                return None
            
            if fecha_inicio > fecha_fin:
                print("⚠️ Fecha inicio debe ser anterior a fecha fin")
                return None
            
            return fecha_inicio, fecha_fin
        
        elif opcion == '3':
            # Últimos 30 días
            from datetime import datetime, timedelta
            ahora = datetime.now()
            hace_30 = (ahora - timedelta(days=30)).strftime('%Y-%m-%d')
            
            fechas_filtradas = [f for f in fechas if f >= hace_30]
            
            if not fechas_filtradas:
                print("⚠️ No hay fechas en los últimos 30 días")
                return None
            
            return fechas_filtradas[0], fechas_filtradas[-1]
        
        elif opcion == '4':
            # Este mes
            mes_actual = datetime.now().strftime('%Y-%m')
            fechas_este_mes = [f for f in fechas if f.startswith(mes_actual)]
            
            if not fechas_este_mes:
                print("⚠️ No hay fechas en este mes")
                return None
            
            return fechas_este_mes[0], fechas_este_mes[-1]
        
        else:
            print("⚠️ Opción no válida")
            return None
    
    except KeyboardInterrupt:
        print("\n⚠️ Cancelado")
        return None

def guardar_config_timelapse(volcan_nombre, fecha_inicio, fecha_fin):
    """Guarda configuración de timelapse en JSON"""
    config = {
        'volcan': volcan_nombre,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'generado': datetime.now().isoformat()
    }
    
    os.makedirs('data/sentinel2/configs', exist_ok=True)
    config_path = f'data/sentinel2/configs/timelapse_{volcan_nombre}.json'
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuración guardada: {config_path}")
    return config_path

def main():
    """Script interactivo para configurar timelapses"""
    
    print("="*80)
    print("📅 SELECTOR DE FECHAS PARA TIMELAPSES")
    print("="*80)
    
    # Listar volcanes con imágenes
    volcanes_disponibles = []
    for volcan in ['Villarrica', 'Llaima']:
        if os.path.exists(f"data/sentinel2/{volcan}/RGB"):
            volcanes_disponibles.append(volcan)
    
    if not volcanes_disponibles:
        print("\n⚠️ No hay volcanes con imágenes disponibles")
        return
    
    print("\n🌋 Volcanes disponibles:")
    for i, volcan in enumerate(volcanes_disponibles, 1):
        print(f"   {i}. {volcan}")
    
    try:
        seleccion = int(input("\nSelecciona volcán (número): ").strip())
        
        if seleccion < 1 or seleccion > len(volcanes_disponibles):
            print("⚠️ Selección no válida")
            return
        
        volcan_nombre = volcanes_disponibles[seleccion - 1]
        
        # Seleccionar rango de fechas
        rango = seleccionar_rango_fechas(volcan_nombre)
        
        if rango:
            fecha_inicio, fecha_fin = rango
            
            print("\n" + "="*80)
            print("✅ CONFIGURACIÓN CONFIRMADA")
            print("="*80)
            print(f"Volcán: {volcan_nombre}")
            print(f"Fecha inicio: {fecha_inicio}")
            print(f"Fecha fin: {fecha_fin}")
            
            # Guardar configuración
            guardar_config_timelapse(volcan_nombre, fecha_inicio, fecha_fin)
            
            print("\n🎬 Siguiente paso:")
            print("   python timelapse_generator.py")
    
    except (ValueError, KeyboardInterrupt):
        print("\n⚠️ Cancelado")

if __name__ == "__main__":
    main()
