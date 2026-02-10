# 🛰️ Copernicus-v1 - Sentinel-2 Volcanic Monitoring System

**Copernicus-v1** es una plataforma de **automatización y visualización científica** diseñada para el monitoreo satelital continuo de volcanes chilenos mediante imágenes **Sentinel-2**. El sistema captura, procesa y visualiza composiciones multiespectrales de alta resolución para el seguimiento de cambios morfológicos y actividad térmica.

⚠️ **Aclaración:** Este software es una herramienta independiente de análisis científico. No reemplaza los canales oficiales de alerta temprana de instituciones estatales como SERNAGEOMIN/OVDAS.

---

## 🌐 Dashboard Interactivo

El sistema cuenta con un **Dashboard Web** que permite visualizar imágenes satelitales, comparar composiciones y generar timelapses animados.

> [!IMPORTANT]
> **[👉 ACCEDER AL DASHBOARD EN VIVO](https://mendozavolcanic.github.io/Copernicus-v1/)**

### 🟢 Características del Dashboard

* **Visualización Dual:** Comparación lado a lado de composiciones RGB y Thermal False Color
* **Calendario Interactivo:** Navegación por fechas con indicadores de disponibilidad
  * 🟢 **Verde:** Imagen descargada y disponible
  * 🔵 **Azul:** Disponible en Copernicus (click para abrir browser)
  * ⚫ **Gris:** No disponible (nubes >100%)
* **Timelapses Automáticos:** GIFs animados de últimos 30 días actualizados diariamente
* **Modo Multi-Volcán:** Vista comparativa de todos los volcanes por zona geográfica
* **Integración Copernicus Browser:** Acceso directo a explorador oficial para análisis avanzado
* **🔄 Sincronización UTC:** Todas las fechas en formato UTC para consistencia internacional

---

## 🌋 Red de Vigilancia

Sistema de monitoreo continuo de **43 volcanes activos** distribuidos en 4 zonas geográficas:

### **ZONA NORTE (8 volcanes)**
Taapacá, Parinacota, Guallatiri, Isluga, Irruputuncu, Ollagüe, San Pedro, Láscar

### **ZONA CENTRO (9 volcanes)**
Tupungatito, San José, Tinguiririca, Planchón-Peteroa, Descabezado Grande, Tatara-San Pedro, Laguna del Maule, Nevado de Longaví, Nevados de Chillán

### **ZONA SUR (13 volcanes)**
Antuco, Copahue, Callaqui, Lonquimay, Llaima, Sollipulli, Villarrica, Quetrupillán, Lanín, Mocho-Choshuenco, Carrán-Los Venados, Puyehue-Cordón Caulle, Antillanca-Casablanca

### **ZONA AUSTRAL (13 volcanes)**
Osorno, Calbuco, Yate, Hornopirén, Huequi, Michinmahuida, Chaitén, Corcovado, Melimoyu, Mentolat, Cay, Maca, Hudson

**Configuración de monitoreo:**
* **Buffer espacial:** 3 km alrededor de coordenadas del cráter
* **Área de cobertura:** 6 km × 6 km por volcán
* **Filtro de nubes:** MAX_CLOUD_COVER = 100% (captura incluso días nublados)
* **Retención de datos:** Últimos 60 días en repositorio

---

## 📊 Composiciones Espectrales

### **RGB (Color Real)**
* **Bandas:** B04 (Red), B03 (Green), B02 (Blue)
* **Uso:** Visualización natural del terreno, identificación de cambios morfológicos
* **Resolución:** 10m/píxel
* **Aplicaciones:** Detección de flujos, colapsos de flanco, cambios en morfología cratérica

### **Thermal False Color (Falso Color Térmico)**
* **Bandas:** B12 (SWIR2), B11 (SWIR1), B04 (Red)
* **Uso:** Detección de anomalías térmicas, flujos de lava, actividad fumarólica
* **Resolución:** 20m/píxel (B12, B11) + 10m/píxel (B04)
* **Aplicaciones:** Monitoreo de puntos calientes, flujos activos, cambios en actividad fumarólica

**Escala geográfica:**
* Todas las imágenes incluyen **barra de escala de 3 km** con marcas cada kilómetro
* Cálculo: Área 6 km = 800 píxeles → 512 píxeles = 3 km
* Escala visible en: Dashboard, timelapses, reportes PPT

---

## 🚀 Arquitectura del Sistema

### **1. Descarga Automatizada (sentinel2_downloader.py)**

Motor principal de captura que ejecuta ciclos **diarios a las 06:00 UTC**:

* **Búsqueda temporal:** Últimos 60 días por volcán
* **Filtro de nubes:** MAX_CLOUD_COVER = 100% (acepta incluso días completamente nublados)
* **Procesamiento on-demand:** Process API genera PNG directamente (no descarga .zip)
* **Compresión lossless:** ~20% reducción sin pérdida de calidad
* **Gestión automática:** Limpieza de imágenes >60 días para mantener repositorio <1GB

**Evalscripts personalizados:**
```javascript
// RGB: B04, B03, B02 con factor 2.5x
// Thermal: B12, B11, B04 con factor 2.5x
// CRÍTICO: Sin filtro dataMask (mantiene nubes visibles)
```

### **2. Generación de Timelapses (timelapse_generator_auto.py)**

Sistema de generación automática de GIFs para dashboard:

* **Frecuencia:** Ejecución diaria junto con descarga
* **Rango temporal:** Últimos 30 días de imágenes disponibles
* **Overlays incluidos:**
  * Logo Copernicus (superior izquierdo)
  * Fecha de adquisición (superior derecho)
  * Tipo de composición (inferior izquierdo)
  * Barra de escala 3 km (inferior derecho)
* **Optimización:** GIFs <1.5 MB mediante compresión inteligente
* **Ubicación:** `docs/timelapses/{volcan}_{tipo}.gif`

### **3. Reportes PowerPoint (ppt_generator.py)**

Generador automático de presentaciones científicas:

* **Frecuencia:** Día 1 de cada mes (automático) o bajo demanda (manual)
* **Contenido:**
  * Timelapses RGB y Thermal del período seleccionado
  * Metadata de cobertura de nubes
  * Fechas de inicio y fin en español
  * Actualización dinámica de volcán y mes/año
* **Plantilla:** `docs/plantillas/Cambios_morfologicos.pptx`
* **Salida:** `docs/sentinel2/{volcan}/reportes/{volcan}_Evaluacion_Mensual_{YYYY-MM}.pptx`
* **Tamaño:** <3 MB por volcán mediante compresión de GIFs

### **4. Búsqueda de Disponibilidad (buscar_fechas_workflow.yml)**

Indexador que genera calendario de fechas disponibles:

* **Frecuencia:** Cada 6 horas
* **Función:** Consulta Catalog API para fechas con imágenes Sentinel-2
* **Filtro:** Últimos 2 meses por volcán
* **Salida:** `docs/fechas_disponibles_copernicus.json`
* **Uso:** Alimenta calendarios del dashboard con días azules (disponibles en Copernicus)

---

## 📂 Estructura del Repositorio

```
Copernicus-v1/
├── .github/
│   └── workflows/
│       ├── copernicus.yml                      # Workflow principal (diario)
│       ├── buscar_fechas_workflow.yml          # Indexador fechas (cada 6h)
│       ├── ppt_evaluacion_workflow.yml         # PPT individual (manual)
│       ├── redescargar_todos_volcanes.yml      # Re-descarga masiva (manual)
│       ├── limpiar_duplicados_workflow.yml     # Limpieza (manual)
│       └── deploy.yml                          # GitHub Pages (automático)
│
├── docs/                                       # Carpeta pública (GitHub Pages)
│   ├── index.html                              # Dashboard principal
│   ├── sentinel2/                              # Imágenes por volcán
│   │   └── {Volcan}/
│   │       ├── YYYY-MM-DD_RGB.png              # Imagen RGB
│   │       ├── YYYY-MM-DD_ThermalFalseColor.png # Imagen Thermal
│   │       ├── metadata.csv                     # Registro local
│   │       ├── reportes/                        # PPTs mensuales
│   │       └── timelapses_ppt/                  # GIFs para reportes
│   ├── timelapses/                             # GIFs para dashboard
│   │   ├── {Volcan}_RGB.gif                    # Últimos 30 días RGB
│   │   └── {Volcan}_ThermalFalseColor.gif      # Últimos 30 días Thermal
│   ├── plantillas/
│   │   └── Cambios_morfologicos.pptx           # Plantilla PPT
│   └── fechas_disponibles_copernicus.json      # Índice de fechas
│
├── config_sentinel2.py                         # Configuración 43 volcanes
├── sentinel2_downloader.py                     # Motor de descarga
├── timelapse_generator_auto.py                 # Generador timelapses dashboard
├── timelapse_generator.py                      # Generador timelapses PPT
├── ppt_generator.py                            # Generador reportes PPT
├── image_compression.py                        # Módulo compresión
├── selector_fechas_timelapse.py                # CLI selector de fechas
├── requirements.txt                            # Dependencias Python
└── README.md                                   # Este archivo
```

---

## ⚙️ Configuración Inicial

### **1. GitHub Secrets (CRÍTICO)**

El sistema requiere credenciales OAuth de Copernicus Data Space Ecosystem:

```
GitHub → Settings → Secrets and variables → Actions → New repository secret

Name: SH_CLIENT_ID
Value: [Tu Client ID de Copernicus]

Name: SH_CLIENT_SECRET
Value: [Tu Client Secret de Copernicus]
```

### **2. Obtener Credenciales OAuth**

**Requisitos:**
* Cuenta gratuita en Copernicus Data Space Ecosystem
* Tipo de cliente: **Client Credentials** (para automatización)
* Expiry recomendado: 365 días

**Pasos:**
1. Ir a: https://shapps.dataspace.copernicus.eu/dashboard/
2. Login con cuenta Copernicus (crear si es necesario)
3. "Create OAuth Client" → Type: **Client Credentials**
4. Copiar Client ID y Client Secret
5. Agregar a GitHub Secrets (paso 1)
6. ⚠️ **NUNCA** commitear credenciales en código

**Rotación de credenciales (cada 90-365 días):**
1. Crear nuevo cliente OAuth en Copernicus
2. Actualizar Secrets en GitHub
3. Ejecutar workflow manual para verificar
4. Eliminar cliente antiguo en Copernicus

---

## 🧪 Testing y Ejecución Manual

### **Workflow Principal (Descarga Diaria)**

```
Actions → Monitoreo Copernicus Automatico → Run workflow
```

**Incluye:**
1. Descarga de imágenes (últimos 60 días)
2. Generación de timelapses (últimos 30 días)
3. Generación de PPT mensual (solo día 1)
4. Deploy a GitHub Pages

**Tiempo estimado:** 5-10 minutos

### **Re-descargar Todos los Volcanes**

```
Actions → Re-descargar TODOS los Volcanes → Run workflow
Input: confirmar = YES
```

**Incluye:**
1. Borrado de TODAS las imágenes PNG
2. Borrado de metadata.csv
3. Re-descarga completa con MAX_CLOUD_COVER=100

**Tiempo estimado:** 30-45 minutos  
**Uso:** Corregir imágenes negras después de cambio de evalscript

### **PPT Individual**

```
Actions → Generar PPT Evaluacion → Run workflow
Seleccionar: Volcán, Fecha inicio, Fecha fin
```

**Genera:**
* Timelapses personalizados para rango de fechas
* PPT con overlays y metadata
* Salida en `docs/sentinel2/{volcan}/reportes/`

**Tiempo estimado:** 3-5 minutos por volcán

---

## 📋 Formato de Datos

### **metadata.csv (por volcán)**

```csv
fecha,tipo,cobertura_nubosa,sensor,ruta_archivo,tamano_mb
2026-02-09,RGB,45.2,Sentinel-2B,2026-02-09_RGB.png,1.8
2026-02-09,ThermalFalseColor,45.2,Sentinel-2B,2026-02-09_ThermalFalseColor.png,1.6
```

**Columnas:**
* `fecha`: YYYY-MM-DD (UTC)
* `tipo`: RGB o ThermalFalseColor
* `cobertura_nubosa`: Porcentaje 0-100 (del producto Sentinel-2)
* `sensor`: Sentinel-2A o Sentinel-2B
* `ruta_archivo`: Nombre de archivo PNG
* `tamano_mb`: Tamaño comprimido en MB

### **fechas_disponibles_copernicus.json**

```json
{
  "Villarrica": [
    "2026-01-10",
    "2026-01-15",
    "2026-01-20"
  ],
  "Llaima": [
    "2026-01-12",
    "2026-01-17"
  ]
}
```

**Uso:**
* Alimenta calendarios del dashboard (días azules)
* Se actualiza cada 6 horas automáticamente
* Últimos 2 meses por volcán

---

## 📊 Uso de Recursos

### **Copernicus Processing Units (PU)**

**Consumo por imagen:**
* RGB (800×800px): ~50 PU
* Thermal (800×800px): ~50 PU
* **Total por volcán/día:** ~100 PU

**Proyección mensual (43 volcanes):**
* Sentinel-2 pasa cada ~5 días → ~6 capturas/mes/volcán
* 43 volcanes × 6 capturas × 100 PU = **25,800 PU/mes**
* Límite free tier: **10,000 PU/mes** → Requiere plan de pago

**Plan recomendado:**
* **Sentinel Hub Professional:** €60/mes (100,000 PU)
* Suficiente para 43 volcanes con margen de seguridad

### **GitHub Repository**

**Estado actual:**
* Tamaño total: ~800 MB
* Límite recomendado: 1 GB
* Estrategia de retención: Últimos 60 días

**Cálculo de proyección:**
* 43 volcanes × 2 tipos × 1.8 MB/imagen × 12 capturas/60días ≈ **1,850 MB** sin limpieza
* Con limpieza automática: **~800 MB** estable

**GitHub Actions:**
* Minutos usados: ~300 min/mes
* Límite free tier: 2,000 min/mes (holgado)

---

## 🔐 Seguridad y Buenas Prácticas

### **NUNCA commitear:**
* ❌ Credenciales OAuth en código Python
* ❌ Archivos `.env` con secrets
* ❌ Tokens de acceso en comentarios
* ❌ Imágenes .zip completas (>100 MB)

### **SIEMPRE:**
* ✅ Usar GitHub Secrets para credenciales
* ✅ Variables de entorno con `os.getenv()`
* ✅ `.gitignore` actualizado (incluye .env, venv/, __pycache__)
* ✅ Compresión lossless en imágenes
* ✅ Limpieza automática de datos antiguos

### **Manejo de errores:**
* Retry logic con exponential backoff (workflows)
* Tokens OAuth con buffer de 5 minutos antes de expirar
* Refresh automático cada 10 iteraciones en loops largos
* Fallback a última imagen conocida si descarga falla

---

## 📚 Documentación Técnica

### **APIs Utilizadas**

* **Sentinel Hub Process API:** https://docs.sentinel-hub.com/api/latest/api/process/
  * Procesamiento on-demand de imágenes Sentinel-2
  * Evalscripts personalizados para composiciones
  * Salida: PNG con georeferencia embebida

* **Sentinel Hub Catalog API:** https://docs.sentinel-hub.com/api/latest/api/catalog/
  * Búsqueda de productos disponibles
  * Filtros: bounding box, rango temporal, cobertura de nubes
  * Salida: Lista de fechas con metadata

* **OAuth2 Token:** https://documentation.dataspace.copernicus.eu/APIs/Token.html
  * Autenticación tipo Client Credentials
  * Tokens válidos por 10 minutos
  * Refresh automático en scripts largos

### **Recursos Adicionales**

* **Copernicus Browser:** https://browser.dataspace.copernicus.eu/
* **Evalscripts Examples:** https://custom-scripts.sentinel-hub.com/
* **Sentinel-2 User Guide:** https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi
* **GitHub Actions Docs:** https://docs.github.com/en/actions

---

## 🎯 Roadmap

### **V1.0 (Actual) ✅**
- ✅ Descarga automatizada 43 volcanes
- ✅ Dashboard web interactivo
- ✅ Timelapses automáticos (30 días)
- ✅ Reportes PPT mensuales
- ✅ Calendarios con disponibilidad
- ✅ Modo multi-volcán por zonas
- ✅ Integración Copernicus Browser

### **V2.0 (En Desarrollo) 🔄**
- 🔄 PPT Completo (todos los volcanes en un archivo)
- 🔄 Detección automática de cambios morfológicos
- 🔄 Comparación temporal con slider interactivo
- 🔄 Exportación de datos en formato NetCDF
- 🔄 API REST para acceso a datos históricos

### **V3.0 (Futuro) 📋**
- 📋 Integración con MIROVA (cross-referencia térmica)
- 📋 Machine Learning para clasificación de actividad
- 📋 Alertas automáticas vía email/Telegram
- 📋 Integración con datos sísmicos OVDAS
- 📋 Modelado de flujos de lava mediante DEM

---

## 🛠️ Tecnologías y Autoría

### **Stack Tecnológico**

* **Lenguaje:** Python 3.10+
* **Procesamiento de imágenes:** Pillow (PIL), OpenCV
* **Datos:** Pandas, NumPy
* **Generación de reportes:** python-pptx
* **Web:** HTML5, CSS3, JavaScript (Vanilla)
* **Infraestructura:** GitHub Actions (CI/CD), GitHub Pages
* **APIs:** Sentinel Hub (Copernicus), OAuth2

### **Dependencias Python**

```
requests>=2.31.0
pandas>=2.2.0
pytz>=2024.1
Pillow>=10.3.0
python-pptx>=0.6.23
```

### **Autoría**

* **Desarrollo y Arquitectura:** Nicolás Mendoza
* **Asistencia Técnica:** Claude AI (Anthropic)
* **Fuente de datos:** Copernicus Sentinel-2 (ESA)
* **Infraestructura:** GitHub Actions + Pages

---

## 🙏 Agradecimientos

Este proyecto utiliza datos satelitales de acceso libre proporcionados por:

* **European Space Agency (ESA):** Programa Copernicus
* **Copernicus Data Space Ecosystem:** Infraestructura de distribución
* **Sentinel Hub:** APIs de procesamiento y acceso a datos

**Referencias científicas:**
* Drusch, M., et al. (2012). *Sentinel-2: ESA's Optical High-Resolution Mission for GMES Operational Services*. Remote Sensing of Environment, 120, 25-36.
* Gascon, F., et al. (2017). *Copernicus Sentinel-2A Calibration and Products Validation Status*. Remote Sensing, 9(6), 584.

> We gratefully acknowledge the European Space Agency (ESA) and the European Commission for free and open access to Sentinel-2 data through the Copernicus program.

---

## 📄 Licencia

Proyecto académico/científico de código abierto.

**Código:** MIT License  
**Datos Sentinel-2:** Free and open access (Copernicus terms of use)  
**Uso:** Libre para fines científicos, educativos y no comerciales

---

## 📞 Contacto

Para consultas técnicas, reportes de bugs o sugerencias:

* **GitHub Issues:** https://github.com/MendozaVolcanic/Copernicus-v1/issues
* **Email:** [Tu email institucional/profesional]

---

**Última actualización:** Febrero 2026  
**Versión del sistema:** v1.0  
**Estado:** Producción ✅
