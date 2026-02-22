"""
ALERT_GENERATOR.PY
Genera alertas automáticas cuando se detectan cambios significativos
Crea archivos markdown para GitHub Issues
"""

import os
from datetime import datetime

def generar_alerta_markdown(volcan, nivel_alerta, cambio_sentinel, firms_resultado=None):
    """
    Genera archivo markdown con evidencia para alerta
    
    Args:
        volcan: Nombre del volcán
        nivel_alerta: 'ALERTA_CRITICA', 'ALERTA_MODERADA', 'ALERTA_MENOR'
        cambio_sentinel: dict con detección Sentinel
        firms_resultado: dict con detección FIRMS (opcional)
    
    Returns:
        dict: {
            'titulo': str,
            'cuerpo': str,
            'path': str,
            'nivel': str
        }
    """
    
    # Emojis por nivel
    emojis = {
        'ALERTA_CRITICA': '🔴',
        'ALERTA_MODERADA': '🟡',
        'ALERTA_MENOR': '🟢'
    }
    
    emoji = emojis.get(nivel_alerta, '⚪')
    
    # Construir título
    titulo = f"{emoji} {nivel_alerta.replace('_', ' ')}: {volcan}"
    
    # Construir cuerpo
    cuerpo = f"""# {titulo}

## 📊 Resumen

**Volcán:** {volcan}  
**Nivel:** {nivel_alerta}  
**Fecha detección:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}  
**Tipo de cambio:** {cambio_sentinel.get('tipo_cambio', 'N/A')}

---

## 🛰️ Detección Sentinel-2

- **Porcentaje de cambio:** {cambio_sentinel['porcentaje_cambio']}%
- **Fecha nueva:** {cambio_sentinel['fecha_nueva']}
- **Fecha comparación:** {cambio_sentinel['fecha_anterior']}
- **Tipo de imagen:** {cambio_sentinel.get('tipo_imagen', 'ThermalFalseColor')}

### 📸 Imágenes

**Antes ({cambio_sentinel['fecha_anterior']}):**

![Antes](../sentinel2/{volcan}/{cambio_sentinel['fecha_anterior']}_ThermalFalseColor.png)

**Después ({cambio_sentinel['fecha_nueva']}):**

![Después](../sentinel2/{volcan}/{cambio_sentinel['fecha_nueva']}_ThermalFalseColor.png)

---
"""
    
    # Agregar información de FIRMS si está disponible
    if firms_resultado and firms_resultado.get('tiene_anomalias'):
        cuerpo += f"""## 🔥 Confirmación NASA FIRMS (VIIRS)

✅ **Anomalías térmicas detectadas**

- **Cantidad de detecciones:** {firms_resultado['cantidad']}
- **Última detección:** {firms_resultado.get('ultima_fecha', 'N/A')}
- **FRP máximo:** {firms_resultado.get('max_frp', 0)} MW
- **Temperatura máxima:** {firms_resultado.get('max_brightness', 0)} K

> ⚠️ **Doble confirmación:** Cambio morfológico (Sentinel-2) + Anomalía térmica (VIIRS)

---
"""
    elif firms_resultado and firms_resultado.get('error'):
        cuerpo += f"""## 🌍 NASA FIRMS

⚠️ No se pudo consultar FIRMS: {firms_resultado.get('mensaje', firms_resultado.get('error'))}

> 💡 Tip: Verifica con tu sistema VIIRS/MODIS existente

---
"""
    else:
        cuerpo += f"""## 🌍 NASA FIRMS

⚪ Sin anomalías térmicas detectadas en últimos 7 días (FIRMS)

> 📝 Nota: El cambio detectado por Sentinel-2 podría ser morfológico (sin emisión térmica) o FIRMS podría no haber capturado el evento.

---
"""
    
    # Agregar recomendaciones
    if nivel_alerta == 'ALERTA_CRITICA':
        cuerpo += f"""## 🚨 Acciones Recomendadas

1. **Urgente:** Revisar imágenes en dashboard: https://MendozaVolcanic.github.io/Copernicus-v1/
2. Generar PPT comparativo:
   - Ejecutar workflow: `ppt_individual_workflow.yml`
   - Volcán: {volcan}
   - Fechas: {cambio_sentinel['fecha_anterior']} - {cambio_sentinel['fecha_nueva']}
3. Verificar reportes SERNAGEOMIN
4. Considerar análisis detallado de series temporales

"""
    elif nivel_alerta == 'ALERTA_MODERADA':
        cuerpo += f"""## ⚠️ Acciones Recomendadas

1. Revisar imágenes en dashboard: https://MendozaVolcanic.github.io/Copernicus-v1/
2. Monitorear en próximas adquisiciones
3. Considerar generar PPT comparativo si el cambio persiste

"""
    else:
        cuerpo += f"""## ℹ️ Acciones Recomendadas

1. Revisar en dashboard si es necesario
2. Monitoreo rutinario

"""
    
    cuerpo += f"""---

*Alerta generada automáticamente por Copernicus-v1 Sistema de Detección de Cambios*  
*Powered by Sentinel-2 L2A + NASA FIRMS VIIRS*
"""
    
    # Guardar archivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f"{volcan}_{nivel_alerta}_{timestamp}.md"
    
    alertas_dir = "docs/alertas"
    os.makedirs(alertas_dir, exist_ok=True)
    
    alert_path = os.path.join(alertas_dir, filename)
    
    with open(alert_path, 'w', encoding='utf-8') as f:
        f.write(cuerpo)
    
    print(f"    ✅ Alerta generada: {filename}")
    
    return {
        'titulo': titulo,
        'cuerpo': cuerpo,
        'path': alert_path,
        'nivel': nivel_alerta,
        'volcan': volcan
    }

def crear_resumen_alertas(alertas_generadas):
    """
    Crea un archivo resumen con todas las alertas del día
    
    Args:
        alertas_generadas: Lista de dicts de alertas
    
    Returns:
        str: Path del archivo resumen
    """
    if not alertas_generadas:
        return None
    
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    
    resumen = f"""# 📊 Resumen de Alertas - {fecha_hoy}

**Total de alertas:** {len(alertas_generadas)}

---

"""
    
    # Agrupar por nivel
    por_nivel = {
        'ALERTA_CRITICA': [],
        'ALERTA_MODERADA': [],
        'ALERTA_MENOR': []
    }
    
    for alerta in alertas_generadas:
        nivel = alerta['nivel']
        if nivel in por_nivel:
            por_nivel[nivel].append(alerta)
    
    # Sección críticas
    if por_nivel['ALERTA_CRITICA']:
        resumen += f"## 🔴 Alertas Críticas ({len(por_nivel['ALERTA_CRITICA'])})\n\n"
        for alerta in por_nivel['ALERTA_CRITICA']:
            resumen += f"- **{alerta['volcan']}** - [Ver detalle]({os.path.basename(alerta['path'])})\n"
        resumen += "\n"
    
    # Sección moderadas
    if por_nivel['ALERTA_MODERADA']:
        resumen += f"## 🟡 Alertas Moderadas ({len(por_nivel['ALERTA_MODERADA'])})\n\n"
        for alerta in por_nivel['ALERTA_MODERADA']:
            resumen += f"- **{alerta['volcan']}** - [Ver detalle]({os.path.basename(alerta['path'])})\n"
        resumen += "\n"
    
    # Sección menores
    if por_nivel['ALERTA_MENOR']:
        resumen += f"## 🟢 Alertas Menores ({len(por_nivel['ALERTA_MENOR'])})\n\n"
        for alerta in por_nivel['ALERTA_MENOR']:
            resumen += f"- **{alerta['volcan']}** - [Ver detalle]({os.path.basename(alerta['path'])})\n"
        resumen += "\n"
    
    resumen += "---\n\n*Generado automáticamente por Copernicus-v1*"
    
    # Guardar resumen
    resumen_path = f"docs/alertas/RESUMEN_{fecha_hoy}.md"
    
    with open(resumen_path, 'w', encoding='utf-8') as f:
        f.write(resumen)
    
    print(f"\n📋 Resumen creado: RESUMEN_{fecha_hoy}.md")
    
    return resumen_path

if __name__ == "__main__":
    """Test del generador de alertas"""
    
    print("="*80)
    print("TEST GENERADOR DE ALERTAS")
    print("="*80)
    
    # Datos de prueba
    cambio_test = {
        'cambio_detectado': True,
        'porcentaje_cambio': 28.5,
        'tipo_cambio': 'ANOMALÍA TÉRMICA MODERADA',
        'fecha_nueva': '2026-02-20',
        'fecha_anterior': '2026-02-10',
        'volcan': 'Villarrica',
        'tipo_imagen': 'ThermalFalseColor'
    }
    
    firms_test = {
        'tiene_anomalias': True,
        'cantidad': 3,
        'ultima_fecha': '2026-02-19',
        'max_frp': 12.5,
        'max_brightness': 345.2
    }
    
    # Generar alerta de prueba
    alerta = generar_alerta_markdown(
        'Villarrica',
        'ALERTA_CRITICA',
        cambio_test,
        firms_test
    )
    
    print(f"\n✅ Alerta creada: {os.path.basename(alerta['path'])}")
    print(f"   Nivel: {alerta['nivel']}")
