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
* **Timelapses Automáticos:** GIFs animados de últimos 30 días, regenerados **apenas Copernicus publica una imagen nueva** (cron 11×/día en los picos reales de publicación L2A 18-20 UTC y 01-02 UTC, no a horario fijo). Latencia típica desde el paso del satélite: ~4-6h.
* **Modo Multi-Volcán:** Vista comparativa de todos los volcanes por zona geográfica
* **Monitoreo Personal:** Selección personalizada de volcanes individuales de cualquier zona
* **14 más Riesgosos:** Vista fija con ranking SERNAGEOMIN de peligrosidad
* **🟠 Panel Landsat 8/9:** Integración con imágenes Landsat (RGB, SWIR, Thermal) de los 43 volcanes, cargadas en tiempo real desde el repositorio [Landsat-v1](https://github.com/MendozaVolcanic/Landsat-v1) — fuente **USGS EROS M2M API** (T+1 día de latencia, gratis, sin tarjeta)
* **Integración Copernicus Browser:** Acceso directo a explorador oficial para análisis avanzado
* **Pantalla Completa:** Modo fullscreen HTML5 disponible en todos los paneles
* **🔄 Sincronización UTC:** Todas las fechas en formato UTC para consistencia internacional

---

## 🌋 Red de Vigilancia

Sistema de monitoreo continuo de **49 entidades = 43 volcanes activos** (distribuidos en 4 zonas geográficas) **+ 6 vistas zoom** (recortes de detalle sobre cráteres/sectores específicos):

### **ZONA NORTE (8 volcanes)**
Taapacá, Parinacota, Guallatiri, Isluga, Irruputuncu, Ollagüe, San Pedro, Láscar

### **ZONA CENTRO (9 volcanes)**
Tupungatito, San José, Tinguiririca, Planchón-Peteroa, Descabezado Grande, Tatara-San Pedro, Laguna del Maule, Nevado de Longaví, Nevados de Chillán

### **ZONA SUR (13 volcanes)**
Antuco, Copahue, Callaqui, Lonquimay, Llaima, Sollipulli, Villarrica, Quetrupillán, Lanín, Mocho-Choshuenco, Carrán-Los Venados, Puyehue-Cordón Caulle, Antillanca-Casablanca

### **ZONA AUSTRAL (13 volcanes)**
Osorno, Calbuco, Yate, Hornopirén, Huequi, Michinmahuida, Chaitén, Corcovado, Melimoyu, Mentolat, Cay, Maca, Hudson

### **VISTAS ZOOM (6 recortes de detalle)**
Melimoyu_Conos_Eruptivos, Mentolat_Sismicidad_VT, Hudson_Ultima_Erupcion, Lascar_Crater, Isluga_Crater_Fumarola, Copahue_Crater_Lake
> Recortes de mayor detalle sobre un cráter/sector específico de su volcán padre. Suman **49 entidades en total** (43 + 6). Definidas en `config_sentinel2.py:VOLCANES` con el campo `vista_zoom_de`.

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

### **SWIR_B8A (composite alternativo del panel 2)**
* **Bandas:** B12 (SWIR2), B11 (SWIR1), B8A (NIR narrow)
* **Uso:** Realce de anomalías SWIR con fondo NIR; el dashboard alterna ThermalFalseColor ↔ SWIR_B8A con el toggle `composite2` de la card SWIR
* **Resolución:** 20m/píxel (B12, B11, B8A)

> **Se descargan 3 productos por escena:** RGB, ThermalFalseColor (B12/B11/B04) y SWIR_B8A (B12/B11/B8A).
> El antiguo composite **`SWIR_raw` (VRP en Watts) fue removido** — esa métrica radiativa se calcula ahora en el proyecto independiente **VRP Chile** (evalscript dormido en `config_sentinel2.py`).

**Escala geográfica:**
* Todas las imágenes incluyen **barra de escala de 3 km** con marcas cada kilómetro
* Cálculo: Área 6 km = 800 píxeles → 512 píxeles = 3 km
* Escala visible en: Dashboard, timelapses, reportes PPT

---

## 🚀 Arquitectura del Sistema

### **1. Descarga Automatizada (sentinel2_downloader.py)**

Motor principal de captura, ejecutado **11 veces al día** concentrado en los picos reales de publicación L2A:

* **Schedule:** `0,30 18-20 UTC` + `0 22 UTC` + `0,30 1-2 UTC` (cron afinado por análisis empírico)
* **Búsqueda temporal:** Últimos 60 días por volcán
* **Filtro de nubes:** MAX_CLOUD_COVER = 100% (acepta incluso días completamente nublados; el filtro estricto se aplica en timelapses con cobertura ≤30%)
* **Procesamiento on-demand:** Process API genera PNG directamente (no descarga .zip)
* **Compresión lossless:** ~20% reducción sin pérdida de calidad
* **Gestión automática:** Limpieza de imágenes >60 días en el working tree (NOTA: esto NO reduce el `.git`, que pesa ~25 GB por historia acumulada — ver `MIGRACION_REPO_LFS.md`)
* **Filtros CLI:** `--zona Norte|Centro|Sur|Austral`, `--volcan <nombre>`, `--skip-json`, `--only-json` (matrix-friendly)

**Evalscripts personalizados:**
```javascript
// RGB: B04, B03, B02 con factor 2.5x (encoding sRGB → matchea Copernicus Browser)
// ThermalFalseColor: B12, B11, B04 con factor 2.5x (LINEAL, sin gamma)
// SWIR_B8A: B12, B11, B8A con factor 2.5x (composite alternativo del panel 2)
// CRÍTICO: Sin filtro dataMask (mantiene nubes visibles)
// NOTA: SWIR_raw (VRP en Watts) removido → vive en el proyecto VRP Chile
```

### **2. Generación de Timelapses (timelapse_generator_auto.py)**

Sistema de generación automática de GIFs para dashboard:

* **Frecuencia:** 11×/día junto con cada cron (regenera apenas hay imagen nueva, no a horario fijo)
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

### **4. Búsqueda de Disponibilidad (buscar_fechas_workflow.yml — DESACTIVADO 2026-05-22)**

> ⚠️ Este workflow quedó solo en modo `workflow_dispatch` (manual).
> Su cron consumía PU adicionales y, cuando la API devolvía 403 por cuota, pisaba
> el JSON correcto con arrays vacíos. El JSON ahora se regenera escaneando el
> filesystem en el job consolidador de `copernicus.yml` (fuente de verdad: los PNGs en disco).

### **5. Constructor PPT client-side (`docs/ppt_builder.html`)**

Generador de presentaciones PowerPoint **en el browser, sin tocar el servidor**:

* **Tecnología:** JSZip + plantilla `docs/plantillas/Cambios_morfologicos.pptx` clonada slide por slide
* **Inputs:** período (default últimos 60 días, todas las imágenes disponibles), volcanes seleccionables
* **GIFs animados:** embebidos desde `docs/sentinel2/<volcan>/timelapses_ppt/` (filtrados a ≤30% nubes)
* **Secciones por volcán:** cada slide queda en su propia sección con el nombre del volcán — aparece como divisor en el panel lateral de PowerPoint, permite plegar/expandir grupos
* **Output:** `.pptx` descargado directamente — NUNCA toca el repo, cero impacto en almacenamiento

### **6. Limpieza automática de PPTs server-side**

PPTs generados por workflows server-side (`ppt_completo`, `ppt_via_issue`, mensual día 1):

* **Retención: 12 horas** (`-mmin +720`)
* Ejecuta en el job consolidador del cron (11×/día), borra cualquier `.pptx` con mtime >12h
* La plantilla `Cambios_morfologicos.pptx` está exenta (no matchea el patrón de fecha)

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
├── config_sentinel2.py                         # Configuración 49 entidades (43 volcanes + 6 vistas zoom)
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

### **Copernicus Processing Units (PU) — el free tier ALCANZA**

> ✅ **No se requiere plan de pago.** El free tier de CDSE/Sentinel Hub entrega **~30.000 PU/mes sin tarjeta de crédito**, y la arquitectura watcher (ver más abajo) mantiene el consumo estacionario en **~3-4k PU/mes** — un margen de ~8-10×. Hay además **failover multi-cuenta** (`SH_CLIENT_ID/_2/_3`) que rota a una cuenta backup si una se agota antes del reset mensual.

**Consumo por imagen (render real, Process API):**
* RGB (800×800px): ~50 PU
* Thermal/SWIR (800×800px): ~50 PU c/u
* Solo se renderiza cuando el watcher OData detecta un producto L2A nuevo (gate `has_new=true`), no en cada cron.

**Consumo mensual real (con watcher):**
* **~3-4k PU/mes** medido — muy por debajo del free tier de 30k.
* La detección de imágenes nuevas cuesta **$0 PU** (OData Catalogue, gratis, sin token). Detalle en la sección «Detección event-driven» más abajo.
* Reset de cuota: día 1 de cada mes. Si una cuenta se agota antes, el failover rota a la backup.

### **GitHub Repository**

> ⚠️ **El `.git` real pesa ~25 GB** (no ~800 MB) y crecía ~4.75 GB/mes porque los workflows hacían `git add -A` de cada PNG/GIF/PPTX generado antes de su limpieza, dejando blobs permanentes en la historia. Ver **`MIGRACION_REPO_LFS.md`** para el plan de mitigación (Paso 0: ignorar PPTX/GIFs por-volcán + adds explícitos; endgame: Git LFS o externalizar a R2). El working tree (PNGs vigentes en `docs/`) sí ronda los cientos de MB gracias a la retención de 60 días, pero la historia versionada es lo que infla los clones/push.

**Estrategia de retención (working tree):**
* Últimos 60 días de imágenes por entidad (auto-cleanup de PNG/NPZ viejos).
* La limpieza del filesystem NO reduce el `.git`: los blobs ya commiteados permanecen hasta una reescritura de historia (filter-repo, con backup previo).

**GitHub Actions:**
* Minutos usados: ~600 min/mes (cron afinado 11×/día + matrix paralelo)
* Límite free tier: 2,000 min/mes (holgado)

**Detección event-driven vía OData Catalogue (commit `watcher`, 2026-06-03):**

CDSE expone **dos catálogos distintos**, y la clave de eficiencia está en usar el correcto:

| Catálogo | Endpoint | Costo | Uso |
|----------|----------|-------|-----|
| Sentinel Hub Catalog API | `sh.dataspace.../api/v1/catalog` | **Consume PU** | Solo dentro del downloader (al renderizar) |
| **OData Catalogue** | `catalogue.dataspace.../odata/v1` | **GRATIS, sin token, sin PU** | **Detección de imágenes nuevas** |

* **Watcher (`scripts/watcher_odata.py`):** cada cron corre el job `detectar`, que hace **una sola query gratis** al OData Catalogue sobre el bbox de Chile (`PublicationDate gt <marcador>`). Si hay un producto L2A publicado que aún no tenemos → `has_new=true`.
* **Gate del pipeline:** las fases de descarga (Process API = PU) **solo corren si `has_new=true`**. Si no hay nada nuevo, el cron termina en ~30 s a **$0 PU**.
* **Marcador:** `docs/.s2_last_pub.json` guarda la última `PublicationDate` procesada (evita re-disparar el pipeline por el mismo producto).
* **Cron:** `*/15 17-21 * * *` + `*/15 0-3 * * *` (cada 15 min en las ventanas de publicación).

**Resultado:**
* Latencia de detección: **≤15 min** desde que ESA publica (antes: gap de 30 min – 2h entre crons)
* PU gastados en detección: **$0** (antes: ~15k PU/mes en búsquedas SH-Catalog)
* PU totales: **~3k/mes** (solo render real, antes ~18k/mes) → **6× menos**
* El piso físico sigue siendo ESA (mediana 4.7h paso → L2A); no se puede bajar de eso.

**Hora de paso / latencia (75 escenas analizadas):**
* Paso S2 sobre Chile: **14:26-14:37 UTC** (10:26-10:37 hora Chile, verificado)
* Latencia paso → L2A: mediana **4.7h**, P95 11.7h, bimodal (picos 18-20 UTC y 01-02 UTC)

**Cuota CDSE Sentinel Hub:**
* Free tier 30k PU/mes, sin tarjeta
* Consumo estacionario con watcher: **~3k PU/mes** (margen 10×)
* Resets el 1 de cada mes; switch a cuenta backup si se agota

**💡 Idea futura — CDSE Subscriptions API (push real, $0):**
* CDSE ofrece [Subscriptions](https://documentation.dataspace.copernicus.eu/APIs/Subscriptions.html) con notificación **push** al segundo que aparece un producto (filtro AOI + colección). **Es gratis** (límite: 2 suscripciones activas / 10 totales, sin tier de pago).
* Daría latencia de detección de **1-2 min** (vs ≤15 min del polling actual), pero requiere un **servidor siempre escuchando** (GitHub Actions es ejecución puntual, no sirve).
* **Cuándo implementarlo:** cuando el sistema corra en una máquina local/VM 24/7. Un mini-listener AMQP recibiría el push y dispararía el render. Por ahora el watcher OData cada 15 min es suficiente para monitoreo volcánico (el cuello real son las horas de ESA, no nuestros minutos).

**Arquitectura paralela (commit `417af5ed`):**
* Antes: 1 job secuencial procesaba las 49 entidades → timeout >2h
* Ahora: 4 jobs paralelos por zona (Norte/Centro/Sur/Austral) + 1 consolidador
* Wall-time: ~45 min vs ~2h del secuencial
* Cada zona sube su artifact, consolidador mergea + regenera JSON + commit + Pages deploy

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
- ✅ Descarga automatizada 49 entidades = 43 volcanes + 6 vistas zoom (Sentinel-2)
- ✅ Dashboard web interactivo
- ✅ Timelapses automáticos (30 días)
- ✅ Reportes PPT mensuales
- ✅ Calendarios con disponibilidad
- ✅ Modo multi-volcán por zonas
- ✅ Monitoreo Personal (selección individual)
- ✅ Vista 14 más Riesgosos (ranking SERNAGEOMIN)
- ✅ Sistema de detección de cambios morfológicos
- ✅ Alertas en 3 niveles (Crítica/Moderada/Menor)
- ✅ Integración NASA FIRMS VIIRS para doble confirmación térmica
- ✅ Pantalla completa (HTML5 Fullscreen API)
- ✅ Integración Copernicus Browser
- ✅ Panel Landsat 8/9 integrado (RGB, SWIR, Thermal) — datos desde [Landsat-v1](https://github.com/MendozaVolcanic/Landsat-v1)

### **V2.0 (En Desarrollo) 🔄**
- 🔄 PPT quincenal (días 1 y 16 de cada mes)
- 🔄 Comparación temporal con slider interactivo
- 🔄 Retry logic individual por volcán
- 🔄 Notificaciones email si workflow falla

### **V3.0 (Futuro) 📋**
- 📋 Machine Learning para clasificación de actividad
- 📋 Alertas automáticas vía email/Telegram
- 📋 Integración con datos sísmicos OVDAS
- 📋 API REST para datos históricos
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

**Última actualización:** Abril 2026
**Versión del sistema:** v1.1
**Estado:** Producción ✅

---

## 🔗 Repositorios relacionados

| Sistema | Fuente | Dashboard |
|---|---|---|
| [Copernicus-v1](https://github.com/MendozaVolcanic/Copernicus-v1) | Sentinel-2 (ESA) | [Ver dashboard](https://mendozavolcanic.github.io/Copernicus-v1/) |
| [Landsat-v1](https://github.com/MendozaVolcanic/Landsat-v1) | Landsat 8/9 (NASA/USGS) | Panel integrado en Copernicus-v1 |
| [Mirova-v1](https://github.com/MendozaVolcanic/Mirova-v1) | MIROVA (Universidad de Florencia) | [Ver dashboard](https://mendozavolcanic.github.io/Mirova-v1/) |
