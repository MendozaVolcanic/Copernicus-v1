# Copernicus-v1 — Instrucciones del proyecto

Monitoreo satelital Sentinel-2 + Landsat 8/9 para **51 entidades** (43 volcanes chilenos + 8 vistas zoom).
Dashboard: https://mendozavolcanic.github.io/Copernicus-v1/

## Arquitectura general

```
Copernicus-v1/
├── docs/
│   ├── index.html                          Dashboard principal (modos individual/multi/zona/personal/riesgosos/Landsat)
│   ├── ayuda.html                          Manual con sensores, bandas, frecuencias
│   ├── proximas_pasadas.html               Visor predicción S2 (countdown vivo)
│   ├── proximas_pasadas.json               Regenerado 2×día por cron
│   ├── gif_builder.html                    Constructor GIF interactivo client-side
│   ├── change_detection.html               Estado actual + history
│   ├── fechas_disponibles_copernicus.json  Índice global de fechas
│   ├── experimental/cog_viewer.html        Leaflet + Microsoft Planetary Computer
│   ├── experimental/alta_resolucion.html   Links Planet/Vantor (Maxar rebranding)
│   ├── change_detection/*.json             Resultados V2 multi-sensor
│   ├── lib/gif.js + gif.worker.js          Generación GIF browser
│   ├── plantillas/Cambios_morfologicos.pptx  Plantilla activa "Trabajando para usted"
│   ├── sentinel2/<volcan>/                 Imágenes + metadata + reportes
│   └── timelapses/                         GIFs dashboard últimos 30 días
│
├── bibliografia/                            Estudio exhaustivo (~149 refs, 15 PDFs)
│   ├── BIBLIOGRAFIA.md                     Índice maestro
│   └── IMPLEMENTACION.md                   Roadmap accionable con pseudocódigo
│
├── sentinel2_downloader.py                 Descarga L2A + fail-fast 401 + dedup misma fecha
├── change_analysis.py                      Detección V2 multi-sensor
├── timelapse_generator.py / *_auto.py      GIFs PPT y dashboard
├── gif_optimizer.py                        MAXCOVERAGE para thermal (preserva anomalías)
├── ppt_generator.py                        PPT con orden RGB/Thermal correcto
├── generar_proximas_pasadas.py             Predicción JSON
├── spectral_downloader.py                  NDVI/NBR
├── config_sentinel2.py                     51 entidades (43 + 8 zoom)
└── .github/workflows/                      Cron 2×día + análisis cambios 22:30 UTC
```

## Modos del dashboard

1. **Vista Individual** — 1 volcán × 1 fecha, RGB + Thermal con selector calendario
2. **Multi-Volcán por Zona** — toda una zona en grid (Norte/Centro/Sur/Austral)
3. **Monitoreo Personal** — checkboxes multi-zona (violeta `#a371f7`)
4. **14 más Riesgosos** — ranking SERNAGEOMIN (naranja `#f97316`)
5. **Landsat 8/9** — modos Individual / Multi / Personal / Riesgosos con 3 composites (RGB, SWIR, THERMAL)
6. **Visores extra:** Change Detection, COG Viewer, Alta Resolución, Próximas Pasadas, Constructor GIF, Manual de Ayuda

## Reglas de edición (CRÍTICAS)

- **NO usar innerHTML con contenido dinámico** → hook de seguridad lo bloquea. Usar `createElement` + `textContent`.
- **Landsat data vive en repo externo** `Landsat-v1` (raw.githubusercontent.com). No duplicar imágenes acá.
- **Nombres con espacios/guiones** (ej. "Puyehue - Cordon Caulle") → siempre `encodeURIComponent` en URLs.
- **VOLCANES_LANDSAT_ZONAS vs PERSONAL_ZONAS** son listas distintas. No mezclar.
- **Vistas zoom** (8 en total: Melimoyu_Conos_Eruptivos, Mentolat_Sismicidad_VT, Hudson_Ultima_Erupcion, Lascar_Crater, Isluga_Crater_Fumarola, Copahue_Crater_Lake [2026-06-04], + Nevados_de_Chillan_Crater_Nicanor, Nevado_de_Longavi_Crater [2026-06-15]) viven en `config_sentinel2.py:VOLCANES` con campo extra `vista_zoom_de` que apunta al volcán padre. Se agregan exportando desde `revision_volcanes.html` y regenerando `docs/volcanes.js`.

## Tonalidad y processing

### Sentinel-2 evalscripts (`config_sentinel2.py`)

**RGB con sRGB encoding** — matchea Copernicus Browser:
```js
function sRGB(c) {
  return c <= 0.0031308 ? 12.92*c : 1.055*Math.pow(c, 1.0/2.4) - 0.055;
}
function evaluatePixel(s) {
  return [sRGB(2.5*s.B04), sRGB(2.5*s.B03), sRGB(2.5*s.B02)];
}
```

**ThermalFalseColor LINEAL** — gamma rompe contraste térmico, las anomalías rojas se aplanan:
```js
function evaluatePixel(s) {
  return [2.5*s.B12, 2.5*s.B11, 2.5*s.B04];  // sin sRGB
}
```

### GIF thermal con MAXCOVERAGE

**Crítico:** `Image.quantize(colors=256, method=Image.Quantize.MAXCOVERAGE)`.
ADAPTIVE/MEDIANCUT pierden 44/44 pixeles rojos (anomalías térmicas), MAXCOVERAGE preserva todos.
Aplicar SOLO a thermal — RGB usa ADAPTIVE normal.

## Composites Landsat

| Composite | Bandas | Uso | Rango |
|-----------|--------|-----|-------|
| RGB       | B4-B3-B2 | Color natural | — |
| SWIR      | B7-B6-B4 | Anomalías intensas (>300°C) | azul=nieve, rojo=calor |
| THERMAL   | B10 TIRS | Temperatura superficial difusa | -20°C → 80°C |

⚠️ **L8 TIRS-1 B11 tiene stray light** 0.61K residual (Barsi 2022) → usar B10 monocanal de L8 y L9.

## Cron automático

| Workflow | Cron | Qué hace |
|---|---|---|
| `copernicus.yml` | `0 10,20 * * *` UTC | Descarga S2 + GIFs dashboard + JSON próximas pasadas |
| `change_analysis.yml` | `0 22 30 * * *` (22:30 UTC) | Análisis V2 + change_results.json |
| `spectral_indices.yml` | configurar | NDVI/NBR |

**Auth:** `SH_CLIENT_ID` y `SH_CLIENT_SECRET` en GitHub Secrets. `sentinel2_downloader.py` aborta con `SystemExit` en 401/403 — fail-fast, sin fallas silenciosas.

## Hora de paso Sentinel-2 sobre Chile

Empírico (1.526 obs analizadas):
- **10:43–10:55 hora Chile** (UTC-4), todos los volcanes
- Ciclo por satélite: **exactamente 10 días**
- Combinada (3 sats 2A/2B/2C): **2.3 d** Villarrica/Melimoyu, **4.1 d** Hudson, **4.6 d** Lascar
- Disponibilidad L2A: 6-12h después del paso

## Estado de change detection (10 may 2026)

- 49 entidades analizadas, 6 ATENCION · 0 ALERTA (resto NORMAL)
- Z-score threshold: z>3.0 AND pct>3% → ALERTA; z>2.0 AND pct>1% → ATENCION
- En ATENCION: Cay, Hudson, Maca, Ollague, Parinacota, Tupungatito (todos por anomalía térmica)

## Bibliografía y roadmap

**Estudio exhaustivo completado** en `bibliografia/`:
- 5 archivos temáticos, ~149 referencias categorizadas
- 15 PDFs open access bajados (~74 MB)
- 4 notas técnicas (`notas/01..04_*.md`, ~25k palabras con fórmulas + pseudocódigo)
- **`IMPLEMENTACION.md`** = roadmap accionable de 10 mejoras priorizadas

**Quick wins recomendados (Sprint 1, 1 semana):**
1. NHI (Marchese 2019): `(B12-B11)/(B12+B11)` — homogeniza S2/L8/L9 con 1 umbral
2. VRP (Coppola 2016): `18.9 × Apixel × DLMIR` — métrica en Watts comparable MIROVA
3. Filtro NDSI para volcanes con glaciar (Hudson, Villarrica, Lonquimay, Mocho)

## Skills a usar proactivamente

- **`writing-plans`** + **`verification-before-completion`** — cualquier cambio en dashboard
- **`playwright-expert`** — testing E2E del dashboard tras cambios
- **`anthropic-skills:pptx`** — al tocar `ppt_generator.py` o plantillas
- **`anthropic-skills:docx`** — para revisión SERNAGEOMIN
- **`python-pro`** + **`pandas-pro`** — scripts de descarga y metadata
- **`data-visualization`** — timelapses, thermal plots
- **`github-actions-templates`** — workflows de auto-descarga
- **`systematic-debugging`** — cuando Copernicus Data Space falla o cambia API
- **`dispatching-parallel-agents`** — investigación bibliográfica, lectura múltiples PDFs

## Lecciones aprendidas críticas (no repetir errores)

1. **Cuantización thermal:** ADAPTIVE descarta outliers → usar MAXCOVERAGE para preservar anomalías rojas
2. **Evalscripts por preset:** RGB con sRGB, SWIR/thermal LINEAL (gamma rompe contraste térmico)
3. **Dedup misma fecha:** cuando 2 satélites pasan el mismo día, quedarse con el menos nuboso (no arbitrario)
4. **Fail-fast en auth:** 401/403 debe abortar el workflow, no continuar con 0 descargas y SUCCESS
5. **Push de archivos:** archivos críticos pueden quedar `untracked` por sesiones; auditar con `git status --short | grep "^??"` antes de cerrar
6. **PDFs descargados con curl** pueden ser HTML de paywall (5KB) — verificar tamaño y contenido real
7. **Workflows instalan `-r requirements.txt`, NO listas a mano.** Un `pip install requests pandas...` que se olvidó `tifffile` dejó `SWIR_raw` gastando ~33% de PU sin guardar `.npz` (0 en 2810 PNG). Si el script importa algo, requirements.txt debe tenerlo y el workflow debe instalarlo de ahí.
8. **Composites del panel 2:** hay 3 (RGB, ThermalFalseColor B12/B11/B04, **SWIR_B8A B12/B11/B8A**). El dashboard alterna ThermalFalseColor↔SWIR_B8A con `composite2` (toggle en la card SWIR). **SWIR_raw (VRP en Watts) se removio**: lo hace el proyecto aparte VRP Chile (evalscript dormido en config). Backfill limitado a 15 dias via `--dias`. Agregar un composite toca config+downloader+timelapse+index.html+tests (ver `tasks/lessons.md`).

Ver `../CLAUDE.md` para reglas globales del repositorio.
