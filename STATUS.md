# STATUS — Copernicus-v1

## Estado actual (2026-05-10)
Dashboard operativo en GitHub Pages con cron automático funcionando 2× día.
Change Detection V2 multi-sensor activo, 49 entidades monitoreadas (43 volcanes + 6 vistas zoom).
Bibliografía exhaustiva consolidada con roadmap de implementación.

## Objetivo
Dashboard principal de monitoreo volcánico: 43 volcanes chilenos + 6 vistas zoom adicionales (49 entidades),
Sentinel-2 + Landsat 8/9, con change detection automático diario y predicción de pasadas satelitales.

## Completado (orden cronológico)

### Detección de cambios (V2 multi-sensor)
- `change_analysis.py` — analiza Sentinel-2 + Landsat independientemente, combina estados
- Confirmación cruzada: ambos sensores en ATENCION → sube a ALERTA
- Z-score por volcán y por sensor (calibrado contra variabilidad propia)
- Consistencia temporal por sensor (namespace `volcan::sensor`)
- Índices espectrales (NDVI/NBR/SWIR) solo para Sentinel-2
- `.github/workflows/change_analysis.yml` — cron 22:30 UTC + workflow_dispatch
- `change_history.json` — combinado a nivel volcán + desglose por sensor

### Visores nuevos del dashboard
- `docs/change_detection.html` — zona-stats cards, history bar chart, badges consistencia
- `docs/experimental/cog_viewer.html` — Leaflet + Microsoft Planetary Computer STAC (tiles en vivo)
- `docs/experimental/alta_resolucion.html` — links Planet Explorer + Vantor (Maxar rebranding)
- `docs/ayuda.html` — manual de uso con explicación sensores, bandas, frecuencias
- `docs/proximas_pasadas.html` — predicción próximas pasadas con countdown en vivo
- `docs/gif_builder.html` — constructor GIF interactivo client-side (gif.js)

### Tonalidad y fixes visualización (V5.2)
- RGB con encoding sRGB en evalscript → matchea Copernicus Browser
- Thermal SWIR sigue lineal (gamma rompe contraste térmico)
- GIFs thermal con MAXCOVERAGE 256 colores → preserva anomalías rojas
  (ADAPTIVE descartaba outliers que son los hot pixels críticos)
- Resolución 800×800 uniforme dashboard + PPT
- Escala km sin redondeo: `f"{escala_km:g} km"` (1.5, 3.3 exactos)
- Comparador con `agregarEscalaAImagen` (canvas) en lugar de CSS hardcoded

### PPT mensual
- Plantilla nueva "Trabajando para usted" en `docs/plantillas/Cambios_morfologicos.pptx`
- Backup en `Cambios_morfologicos_backup_pre_FORMATO.pptx`
- Fix orden RGB/Thermal: la plantilla nueva tenía tops casi iguales (diferencia 0.01cm)
  → reescrito `ppt_generator.py` para emparejar imágenes con subtítulos por proximidad horizontal
- VOLCANES_ACTIVOS extendido con las vistas zoom (6 en total al 2026-06-04)

### Descarga y cron
- 49 entidades (43 volcanes + 6 zoom views), abril 1-30 + extensión mayo Melimoyu
- Workflow `copernicus.yml` corre 2× día (10 UTC + 20 UTC = 6h y 16h Chile)
- Workflow ahora regenera también `proximas_pasadas.json` automáticamente
- Auth Copernicus actualizado en GitHub Secrets (creds nuevos `sh-e103ec7b-...`)
- Fail-fast en `sentinel2_downloader.py`: si 401/403 aborta con `SystemExit`
  (antes el workflow daba SUCCESS aunque no bajara nada)
- Dedup misma fecha (2 satélites mismo día) → queda siempre el menos nuboso
- 228 imágenes nuevas mayo 1-5 + JSON regenerado: 1.329 fechas totales

### Modificación de coordenadas (revisión SERNAGEOMIN)
Cambios aplicados a 10 volcanes según `GIF_VOLCANES_REVISION_v1.docx`:
- Antuco, Villarrica (radio 1.5→1 km), Quetrupillan (5.5→8.5 km)
- Lanin, Mocho-Choshuenco (radio 5→6 km), Antillanca-Casablanca
- Yate (radio 4.5→5 km), Huequi (radio 1.5→2 km)
- Melimoyu, Mentolat (lat/lon ajustados)

3 vistas zoom adicionales agregadas (las primeras 3 del total de 6):
- `Melimoyu_Conos_Eruptivos` (lat -44.057878, lon -72.786587, 4 km)
- `Mentolat_Sismicidad_VT` (lat -44.684081, lon -73.195247, 3.5 km)
- `Hudson_Ultima_Erupcion` (lat -45.950731, lon -72.989386, 4 km)

Posteriormente (2026-06-04) se agregaron otras 3 vistas zoom → 6 en total:
`Lascar_Crater`, `Isluga_Crater_Fumarola`, `Copahue_Crater_Lake`.

### Badge "NUEVA HOY" en multi-volcán
- Helper `esNuevaHoy(fecha)` compara con día actual UTC-4 (Chile)
- Panel del volcán con borde rojo pulsante + pill 🆕 cuando ultima fecha === hoy
- Aplicado a los 4 modos multi (zona, personal, riesgosos, individual)

### Bibliografía consolidada (`bibliografia/`)
- 5 archivos temáticos con ~149 referencias categorizadas
- 15 PDFs open access descargados (~74 MB)
- 4 archivos `notas/0X_*.md` con extractos técnicos densos (~25.000 palabras)
- `IMPLEMENTACION.md` — roadmap accionable de 10 mejoras priorizadas con pseudocódigo
- Hallazgos clave: implementar NHI (Marchese 2019), calcular VRP (Coppola 2016),
  filtro NDSI para glaciares, Mahalanobis sobre Z-score, CCDC harmonic baseline

### Documento revisión SERNAGEOMIN
- `GIF_VOLCANES_REVISION_v1.docx` — devuelto editado con cambios + 3 zoom views

## Pendiente
- Integrar link NHI-v1 en dashboard principal
- Vantor URL exacta confirmar (Vantor = Maxar Intelligence rebranding oct 2025)
- Sprint 1 IMPLEMENTACION: NHI + VRP + NDSI glaciar (1 semana)
- Sprint 2: Mahalanobis + enriquecer metadata.csv (1 semana)
- Sprint 3: vistas zoom triple + CCDC harmonic (1-2 semanas)
- Sprint 4 opcional: BIT Transformer DL (3-4 semanas)
- Bajar manualmente ~24 papers MDPI/Elsevier (DOIs en `bibliografia/BIBLIOGRAFIA.md`)
- Re-bajar `Romero2024_SVZ_Review.pdf` (es HTML 37KB, no PDF real)

## Arquitectura

```
Copernicus-v1/
├── docs/
│   ├── index.html                          Dashboard principal
│   ├── ayuda.html                          Manual de uso
│   ├── proximas_pasadas.html               Visor predicción S2
│   ├── proximas_pasadas.json               JSON regenerado 2×día
│   ├── gif_builder.html                    Constructor GIF interactivo
│   ├── change_detection.html               Visor change detection
│   ├── fechas_disponibles_copernicus.json  Índice global fechas (1.329)
│   ├── experimental/
│   │   ├── cog_viewer.html                 Leaflet + Planetary Computer
│   │   └── alta_resolucion.html            Links Planet/Vantor
│   ├── change_detection/
│   │   ├── change_results.json             Estado actual 49 entidades
│   │   └── change_history.json             Histórico V2
│   ├── lib/
│   │   ├── gif.js                          Constructor GIF (33 KB)
│   │   └── gif.worker.js
│   ├── plantillas/
│   │   ├── Cambios_morfologicos.pptx       Plantilla nueva activa
│   │   └── ..._backup_pre_FORMATO.pptx     Plantilla anterior
│   ├── sentinel2/<volcan>/                 Imágenes + metadata + reportes
│   ├── timelapses/                         GIFs dashboard últimos 30 días
│   └── reportes/                           PPT combinado (gitignored >100MB)
│
├── bibliografia/
│   ├── BIBLIOGRAFIA.md                     Índice maestro 149 refs
│   ├── IMPLEMENTACION.md                   Roadmap accionable 10 mejoras
│   ├── algoritmos_deteccion_cambios.md     (40 refs)
│   ├── sentinel2_swir_thermal_anomalias.md (26 refs)
│   ├── Landsat_Volcanic_Thermal_Bibliography.md (30+ refs)
│   ├── imagenes_comerciales_alta_resolucion.md  (23 refs)
│   ├── monitoreo_satelital_volcanes_chilenos_andinos.md (30 refs)
│   ├── notas/
│   │   ├── 01_MIROVA_MODVOLC.md            ~9000 palabras técnicas
│   │   ├── 02_DeepLearning_ChangeDetection.md
│   │   ├── 03_Chile_Andes.md
│   │   └── 04_CasosEstudio_MultiPlatform.md
│   └── pdfs/                                15 PDFs (~74 MB)
│
├── scripts Python
│   ├── sentinel2_downloader.py             Descarga + fail-fast 401
│   ├── change_analysis.py                  Detección V2 multi-sensor
│   ├── timelapse_generator.py              GIFs PPT
│   ├── timelapse_generator_auto.py         GIFs dashboard 30d
│   ├── gif_optimizer.py                    MAXCOVERAGE para thermal
│   ├── ppt_generator.py                    PPT con orden RGB/Thermal correcto
│   ├── generar_proximas_pasadas.py         Predicción JSON
│   ├── spectral_downloader.py              NDVI/NBR
│   └── config_sentinel2.py                 49 entidades (43 volcanes + 6 zoom views)
│
├── .github/workflows/
│   ├── copernicus.yml                      Cron 2×día (10 + 20 UTC)
│   ├── change_analysis.yml                 Cron 22:30 UTC
│   ├── spectral_indices.yml                NDVI/NBR cron
│   ├── deteccion_cambios.yml               V1 legacy deshabilitado
│   └── (workflows PPT individuales/completos)
│
├── GIF_VOLCANES_REVISION_v1.docx           Editado por SERNAGEOMIN
├── CLAUDE.md                                Instrucciones proyecto
└── STATUS.md                                Este archivo
```

## Notas técnicas

### Tonalidad
- **RGB con sRGB encoding** en evalscript: `function sRGB(c) { return c <= 0.0031308 ? 12.92*c : 1.055*Math.pow(c, 1/2.4) - 0.055; }`
- **Thermal SWIR lineal** (sin gamma): preserva contraste rojo/oscuro de anomalías
- **GIFs thermal MAXCOVERAGE**: `Image.quantize(colors=256, method=Image.Quantize.MAXCOVERAGE)` — ADAPTIVE pierde 44/44 pixeles rojos en Lascar, MAXCOVERAGE preserva 44/44

### Detección de cambios
- Z-score threshold: z>3.0 AND pct>3% → ALERTA; z>2.0 AND pct>1% → ATENCION
- 6 volcanes actualmente en ATENCION (10 mayo 2026): Cay, Hudson, Maca, Ollague, Parinacota, Tupungatito

### Cron y autenticación
- Workflow `copernicus.yml` corre `0 10,20 * * *` UTC
- `sentinel2_downloader.py` ahora aborta explícito en 401/403 → notificación email
- 10 UTC (6h Chile) = antes del paso satélite
- 20 UTC (16h Chile) = después del paso (S2 pasa 14:43-14:55 UTC sobre Chile)

### Predicción de pasadas
- Empírica: 1.526 obs analizadas, ciclo 10 días exacto por satélite
- Combinada: Villarrica 2.3d / Lascar 4.6d / Hudson 4.1d / Melimoyu 2.3d
- Hora paso UTC-4: 10:43–10:55 (norte→sur, longitud W más oeste pasa después)
- 3 satélites activos: 2A (240 obs), 2B (639), 2C (647) — 2A subutilizado

### Bug latente Landsat 8 vs 9
- L8 TIRS-1 B11 tiene stray light residual 0.61 K (Barsi 2022)
- Recomendación: usar B10 monocanal de ambos, no mezclar L8+L9 sin distinguir sensor

### Sensores Sentinel-2 limitations
- NO tiene MIR 3.9 μm (que MODIS sí tiene) → algoritmos NTI no aplicables directamente
- Usar NHI Marchese 2019 como sustituto (SWIR-only): `(B12-B11)/(B12+B11)`

### Configuración descarga
- Buffer_km por volcán (no global): config_sentinel2.py:VOLCANES
- MAX_CLOUD_COVER=100 (todas las imágenes disponibles del catalog)
- Período retención: 60 días (auto-cleanup viejas)

### Documentos clave para próximos pasos
- `bibliografia/IMPLEMENTACION.md` — roadmap accionable con pseudocódigo
- `bibliografia/notas/01_MIROVA_MODVOLC.md` — fórmulas NHI/VRP listas
- `bibliografia/notas/03_Chile_Andes.md` — pipeline VOLCANOMS UCN reusable
