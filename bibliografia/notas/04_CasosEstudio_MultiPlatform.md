# 04 — Casos de estudio multi-plataforma + calibración Landsat 9

Síntesis de 5 papers para diseñar mejoras al pipeline Copernicus-v1. Foco en transferibilidad a los 46 volcanes chilenos del proyecto.

---

## 1. Plank et al. 2023 — Cumbre Vieja, La Palma 2021 (multi-sensor TADR + DSM)

**Cita:** Plank, S., Shevchenko, A.V., d'Angelo, P., Gstaiger, V., González, P.J., Cesca, S., Martinis, S., Walter, T.R. (2023). Combining thermal, tri-stereo optical and bi-static InSAR satellite imagery for lava volume estimates: the 2021 Cumbre Vieja eruption, La Palma. *Scientific Reports* 13:2057. https://doi.org/10.1038/s41598-023-29061-6
**PDF:** `bibliografia/pdfs/Walter2023_CumbreVieja_TriStereo_InSAR.pdf`
**Páginas leídas:** 1-14 (íntegro)

### Caso de estudio
- **Volcán:** Cumbre Vieja, La Palma (Canarias) — erupción Tajogaite 2021
- **Período:** 19 sep – 13 dic 2021 (85 días 8 h, oficiales); observación hasta 25 dic 2021
- **Magnitud:** ~12.4 km² cubiertos por lava, 3000 casas destruidas, 7000 desplazados; volumen final subaéreo **212×10⁶ ± 13×10⁶ m³**, MOR **28.8 ± 1.4 m³/s**, pico de TADR **42.7 ± 21.3 m³/s** (28 sep)
- Cuatro a cinco bocas activas simultáneas alineadas NW-SE; tres deltas de lava

### Plataformas usadas

| Plataforma | Resolución | Banda/composite | Aporte específico |
|---|---|---|---|
| MODIS (Terra+Aqua) | 1 km | MIR 3.95 µm + TIR 11 µm | VRP de alta frecuencia (4/día) → TADR |
| VIIRS (Suomi-NPP, NOAA-20) | 375 m | I4 (3.74) / I5 (11.45) | VRP, hasta 8 obs/día combinado con MODIS |
| Pléiades tri-stereo | 0.5 m | pancromático | DSM 0.5 m post-erupción (31 dic 2021) |
| TanDEM-X bi-static | 5 m | SAR banda X | DSM co-eruptivo (3 fechas: 15-oct, 17-nov, 22-nov) |
| LiDAR pre-erupción | 2 m | — | DSM de referencia |
| Sentinel-1 / PAZ / CSK / TSX | 10–3 m | SAR | DInSAR co-eruptivo (>40 cm LOS) |

### Métodos de fusión / pipeline

```
PIPELINE TADR (Coppola 2013):
  1. Filtrar MODIS scan_zenith < 40°, VIIRS < 31.59° (1ª aggregation region)
  2. Solo daytime, cielo despejado sobre el campo de lava
  3. VRP por hotspot via Wooster MIR approach (lavas 600-1500 K)
  4. Sumar VRP por overflight, tomar máximo VRP/día
  5. TADR = VRP / c_rad,    c_rad = 6.45e25 * X_SiO2^(-10.4)
  6. Aplicar c_rad ± 50% como bandas de incertidumbre
  7. Volumen integrando TADR por trapezoidal: V_t = 0.5*(t_j-t_i)*(TADR_j+TADR_i)
  8. CALIBRACIÓN: cuando hay TanDEM-X DSM, reemplazar V_térmico por V_TanDEM-X.

PIPELINE DSM (volumen):
  Pléiades tri-stereo → SGM (CATENA o Agisoft Metashape) → DSM 0.5 m
  TanDEM-X CoSSC → SARscape (Goldstein filter, MCF unwrap) → DSM 5 m
  Para cada DSM:
    a) georeferenciar contra LiDAR usando GCPs en zona no afectada
    b) corregir offset vertical (RMSE 0.9-1.9 m)
    c) recortar al polígono Copernicus EMS de lava
    d) DSM_post − DSM_pre_LiDAR = mapa de espesor → volumen
```

### Hallazgos clave
- TADR puramente térmico **subestima 50%** el volumen final por aislamiento de tubos de lava bajo costra
- TanDEM-X solo (sin térmico) → buena precisión absoluta pero baja frecuencia
- **Combinación térmico calibrado por TanDEM-X reproduce los 212 Mm³ de Pléiades dentro de incertidumbres**
- Composición pasó de tefrita (44.93 wt% SiO₂) a basanita (43.61 wt% SiO₂) el 27 sep → bajada de viscosidad → aumento de TADR
- **Predicción de duración de erupción** con confianza 88% solo usando fases IIa+IIb del waning (modelo log-decay)

### Aplicabilidad a Copernicus-v1
- **REPLICABLE HOY (S2 + Landsat 8/9):** estimación de TADR/VRP usando Wooster MIR aplicada a SWIR Sentinel-2 (B11/B12) y TIRS Landsat (B10) — la metodología es agnóstica al sensor, solo cambia c_rad (silica-dependent). Para volcanes chilenos andesíticos (~58-62 wt% SiO₂) c_rad ≈ 1.6-2×10⁹ J/m³ vs 6×10⁹ usado en La Palma.
- **REPLICABLE SI integramos VIIRS/MODIS:** Copernicus-v1 hoy ya tiene MIROVA-style en `Automatizacion web/`. Falta cruzar VRP MIROVA con áreas de lava S2/Landsat para obtener espesor medio por iteración.
- **REQUIERE DATA ADICIONAL:** Pléiades/WorldView (comerciales, ~$15/km²) o TanDEM-X (DLR proposal) para DSMs. Sin DSM, lo que sí se puede hacer es **calibración mutua S2/L9** y comparación contra MIROVA.
- **Esfuerzo estimado:** 2 sprints. Sprint 1: integrar VRP MIROVA al dashboard como serie temporal por volcán. Sprint 2: implementar TADR via SWIR Sentinel-2 (Coppola formula, c_rad chileno).

### Para casos históricos chilenos
- **Calbuco 2015:** explosivo (VEI 4) más que efusivo, no aplica TADR pero sí DInSAR + tri-stereo post para volumen depósito piroclástico
- **Cordón Caulle 2011-2012:** efusión rhyolítica de 14 meses → CASO IDEAL para pipeline Coppola (c_rad para riolita ~10×10⁹). Reanalizable con MODIS+VIIRS archivo
- **Chaitén 2008:** dome growth → ASTER stereo + L8 TIRS time series
- **Hudson 1991:** archivo previo a S2/L9, requiere AVHRR+TM

---

## 2. Plank et al. 2025 — Home Reef, Tonga 2022-2024 (isla submarina + erosión)

**Cita:** Plank, S., Ciancia, E., Genzano, N., Falconieri, A., Martinis, S., Taubenböck, H., Pergola, N., Marchese, F. (2025). The evolution of the 2022–2024 eruption at Home Reef, Tonga, analyzed from space shows vent migration due to erosion. *Scientific Reports* 15:11508. https://doi.org/10.1038/s41598-025-95197-2
**PDF:** `bibliografia/pdfs/HomeReef_Tonga_2025_NatureSciRep.pdf`
**Páginas leídas:** 1-9 (cuerpo principal) + tabla 1 metodología

### Caso de estudio
- **Volcán:** Home Reef (Tonga Volcanic Arc), 18.992°S 174.775°W
- **Período:** 9 sep 2022 – sep 2024, **4 fases eruptivas** discretas (sep-oct 2022; sep-nov 2023; ene 2024; jun-sep 2024)
- **Magnitud:** isla creció de 0 → 122,000 m² en 2 años, con migración de la boca emergente

### Plataformas usadas

| Plataforma | Resolución | Banda/composite | Aporte específico |
|---|---|---|---|
| Sentinel-2 MSI | 10 / 20 m | NHI: NIR (B8) + SWIR (B11/B12) | Detección automática hotspots + área |
| Landsat-8/9 OLI | 30 m | NHI: NIR + SWIR | Refuerzo S2 cuando S2 nublado |
| MODIS Terra+Aqua | 1 km | bandas 21/22 + 31 (FIRMS) | VRP diaria (4/día) |
| VIIRS NPP+NOAA-20/21 | 375 m | I4 + I5 | VRP de mayor resolución |
| PlanetScope | 3 m | RGB+NIR | Detección plumas agua descolorida, contorno isla diario |
| TerraSAR-X HighResolution SpotLight | 1.2 m | SAR banda X | Área isla (todo tiempo) + coherencia interferométrica para detectar cambios sub-m |
| TerraSAR-X Staring SpotLight | 0.25 m | SAR banda X | Detalle morfológico vents |

### Métodos de fusión / pipeline

```
1. Detección onset: NHI (Normalized Hotspot Indices) sobre S2 y L8/9
   NHI_SWIR = (B12-B11)/(B12+B11) > umbral
   NHI_SWNIR = (B11-B8)/(B11+B8) > umbral
   → píxel hot si supera ambos
2. VRP diaria de NASA FIRMS (MODIS+VIIRS) → curva intensidad
3. Área de isla: segmentación de TSX-HS (umbral backscatter sobre mar)
   + verificación con S2/PS true-color cuando hay sol
4. Coherencia interferométrica TSX consecutivas: si γ > 0.5 → superficie estable
   (más sensible que backscatter para detectar cambios <1 m)
5. Vector de migración de bocas: centroide de hotspots S2 entre fases
```

### Hallazgos clave
- 4 fases identificadas con duración y VRP máxima (64 MW fase 1, ~10.7 MW fase 3)
- Tasas de crecimiento isla: 2,955 m²/día (fase 1) → 170 m²/día (waning) → 1,870 m²/día (fase 4)
- Tasas de erosión inter-eruptiva: 110 m²/día → 15 m²/día
- **Cada nueva boca apareció donde la erosión previa fue máxima** (modelo: descarga lateral cambia campo de esfuerzos → camino de menor resistencia)

### Aplicabilidad a Copernicus-v1
- **REPLICABLE HOY:** NHI (Normalized Hotspot Indices) es trivial implementar sobre las imágenes S2 y L8/9 que ya descargamos. Solo es aritmética de bandas. **Recomendación: añadir composite "NHI" a `change_detection.py` junto al SWIR clásico.**
- **REPLICABLE:** integrar VRP FIRMS (descarga libre desde NASA) como serie temporal en el dashboard, paralela a las imágenes
- **NO REPLICABLE sin SAR comercial:** TSX-HS y TSX-ST son comerciales (DLR, ~€2k/escena). Sentinel-1 (10 m, libre) es alternativa pero pierde la coherencia sub-métrica
- **Esfuerzo:** 1 sprint. NHI ya tiene paper de referencia (Marchese et al.) y es algoritmo cerrado de pocas líneas

### Para casos históricos chilenos
- Aplicabilidad **directa NO existe** (Chile no tiene vulcanismo submarino monitoreado), pero la estrategia es totalmente transferible a:
  - **Lascar** y **Villarrica** (lava lakes intermitentes): usar NHI S2 para detectar episodios térmicos sub-anuales
  - **Copahue** (cráter ácido con anomalías térmicas en lago): TSX coherence equivalent → usar S1 coherence para detectar cambios morfológicos
  - **Llaima 2008-2009:** crecimiento dome intracraterico → NHI + S1 coherence reanalizable

---

## 3. Ganci et al. 2025 — Etna feb-mar 2025 (multi-plataforma, primer Meteosat-FCI)

**Cita:** Ganci, G., Bilotta, G., Dozzo, M., Spina, F., Zuccarello, F., Cristofaro, R., Guardo, R., Spina, M., Cappello, A. (2025). Multi-platform satellite-derived products during the 2025 Etna eruption. *Scientific Data* 12:1353. https://doi.org/10.1038/s41597-025-05545-0
**PDF:** `bibliografia/pdfs/Etna2025_MultiPlatform_SciData.pdf`
**Páginas leídas:** 1-7 (íntegro)
**Dataset:** https://doi.org/10.6084/m9.figshare.28759586 (CC-BY 4.0)

### Caso de estudio
- **Volcán:** Mt. Etna (Sicilia), erupción 6 feb – 2 mar 2025 (efusiva-explosiva mixta)
- **Período:** ~25 días, 2 pulsos efusivos
- **Magnitud:** TADR pico, volumen total **5.05 ± 0.9 ×10⁶ m³** (DSM diff) vs **5.37 ± 0.8 ×10⁶ m³** (térmico) — convergencia 6%; lava cubrió 0.94 km², longitud 4.3 km

### Plataformas usadas

| Plataforma | Resolución | Banda/composite | Aporte específico |
|---|---|---|---|
| Meteosat MSG SEVIRI | 3 km nadir | Ch4 (3.9 µm) + Ch10 (10.8 µm) | TADR cada 5 min (RSS) — **temporal premium** |
| Meteosat MTG FCI | 1 km nadir | IR3.8 + IR10.5 HRFI | TADR cada 10 min — primera erupción cubierta |
| MODIS | 1 km | MIR + TIR | TADR 2/día por satélite |
| VIIRS | 375 / 750 m | I4 + I5 | TADR 2/día |
| SkySat | 0.5 m | RGB+NIR | Contorno lava on-demand |
| PlanetScope | 3 m | 8 bandas (incluye red-edge) | Contorno lava diario |
| Pléiades tri-stereo | 0.5 m | pan | DSM post-erupción 5 m, vertical RMSE 1.61 m |
| TROPOMI (S5P) | 5.5×3.5 km | UV-VIS | SO₂ flux DOAS, validador de TADR |

### Métodos de fusión / pipeline

```
CL-HOTSAT (Ganci et al. 2016, INGV):
  ├── Ingesta SEVIRI / FCI / MODIS / VIIRS
  ├── Hotspot algorithm contextual (MIR-TIR diff con threshold zonal)
  ├── Radiant heat flux por píxel via MIR radiance (Wooster 2003)
  └── Integración → TADR → Volumen

DSM differencing (MicMac open-source):
  ├── Pléiades pre-erupción (27 dic 2023, triplet)
  ├── Pléiades post (15 jul 2024 + 6 mar 2025)
  ├── Co-registro Nuth & Kääb 2011
  ├── Fusión datasets si hay nubes (Ganci et al. 2023)
  └── Diff → espesor → volumen + std residuales = incertidumbre

TROPOMI SO2 (Dozzo et al. 2025):
  ├── L3 product 15 km
  ├── SNIC segmentation + k-means
  ├── Threshold density > 0.00028 mol/m²
  └── Total mass diaria

Lava field via SkySat/PlanetScope:
  RGB compuesto RED-GREEN-NIR → thresholding semi-automático en GRASS/QGIS
  → polígono lava con fecha → área + perímetro
```

### Hallazgos clave
- **MTG-FCI** (Meteosat 3ª gen) provee primera vez 10-min IR cadence a 1 km — aplicable globalmente desde 2024
- DSM diff y TADR térmico convergen al **6%**, validación cruzada robusta
- SO₂ flux y TADR co-varían (2 picos coincidentes 20-26 feb) → confirma acoplamiento gas-lava
- Validación independiente con drones/cámaras térmicas INGV: error <40%

### Aplicabilidad a Copernicus-v1
- **REPLICABLE HOY (gratis):** S5P TROPOMI SO₂ disponible vía Google Earth Engine. Para volcanes chilenos con desgasificación crónica (Lascar, Villarrica, Copahue) → serie temporal SO₂ en el dashboard
- **REPLICABLE:** MicMac es open-source. Si conseguimos pares S2 con offsets temporales cortos, MicMac puede generar DSMs aproximados (resolución mucho peor que Pléiades pero gratis). Más realista: **descargar DSMs de Copernicus DEM 30 m como pre-erupción de referencia**.
- **REPLICABLE:** Meteosat SEVIRI cubre Sudamérica desde GOES, no SEVIRI; equivalente sería **GOES-16 ABI** (2 km, 5-15 min). GOES Level 2 fire products vía NOAA CLASS / GEE — propuesta concreta: integrar GOES-16 hotspots para los 14 más riesgosos
- **Esfuerzo:** 3 sprints. Sprint 1: TROPOMI SO₂ via GEE. Sprint 2: GOES-16 fire detection. Sprint 3: DSM diff con Copernicus DEM 30 m.

### Para casos históricos chilenos
- **Villarrica 2015 paroxismo:** combinación TADR (MIROVA archive) + Pléiades / WorldView post-evento → reconstruir volumen lava fountaining
- **Calbuco 2015:** SO₂ TROPOMI no disponible (S5P lanzado 2017), pero **OMI Aura** sí — re-análisis posible
- **Lascar erupciones recurrentes:** SEVIRI no cubre, pero **GOES-16/17 Geostationary** sí desde 2017

---

## 4. Civico et al. 2022 — Cumbre Vieja DSM UAS post-erupción

**Cita:** Civico, R., Ricci, T., Scarlato, P., Taddeucci, J., Andronico, D., Del Bello, E., D'Auria, L., Hernández, P.A., Pérez, N.M. (2022). High-resolution Digital Surface Model of the 2021 eruption deposit of Cumbre Vieja volcano, La Palma, Spain. *Scientific Data* 9:435. https://doi.org/10.1038/s41597-022-01551-8
**PDF:** `bibliografia/pdfs/CumbreVieja_DSM_SciData.pdf`
**Páginas leídas:** 1-7 (íntegro)
**Dataset:** OpenTopography https://doi.org/10.5069/G96971S8

### Caso de estudio
- **Volcán:** Cumbre Vieja (mismo evento 2021)
- **Período de levantamiento:** 24-28 ene 2022 (post-erupción)
- **Magnitud levantamiento:** **>12,000 fotos UAS** (DJI Phantom 4 RTK), 800 km de vuelo, 40 GCPs DGNSS, **DSM 0.2 m/pix**, ortofoto 0.1 m/pix, área 17 km²

### Plataformas usadas

| Plataforma | Resolución | Banda/composite | Aporte específico |
|---|---|---|---|
| DJI Phantom 4 RTK UAS | 0.054 m GSD | RGB | SfM photogrammetry |
| GNSS-RTK D-RTK 2 | cm | — | Posicionamiento cámara on-board |
| 40 GCPs DGNSS | 1-2 cm horiz, 2-4 cm vert | — | Validación + control |
| PNOA-LiDAR pre-erupción | 2 m | — | Diff topográfica |
| Agisoft Metashape v1.6.3 | — | — | SfM-MVS |

### Métodos / pipeline

```
SfM clásico:
  1. Misiones nadir 200 m AGL + oblicuas 50-200 m sobre el cono
  2. Forward+side overlap 80%
  3. 9970 fotos georeferenciadas (cull dark/blurry)
  4. Alignment HIGH + dense cloud HIGH + aggressive depth filter
  5. GCPs RMSE: 6.18 cm (33 GCPs) / 14.59 cm (7 checkpoints)
  6. DSM 0.2 m, RMSE vertical vs LiDAR 2015 = 0.26 m
  7. Threshold detección cambio: 0.5 m
```

### Hallazgos clave
- **Volumen total subaéreo:** 217.4 ± 6.6 Mm³ (depósito + fallout + cono)
- **Solo lava flows:** 177.6 ± 5.8 Mm³, área 11.8 km², espesor máx 65 m, medio 15.2 m
- **Cono volcánico:** 36.5 ± 0.3 Mm³, ejes 770 × 660 m, altura 187 m sobre topografía pre-existente
- **Tasa efusión final:** 24.1 m³/s
- Concordancia con Plank+Walter 2023 (212 Mm³ Pléiades) **dentro de 2-3%**

### Aplicabilidad a Copernicus-v1
- **NO ES REMOTE SENSING SATELITAL** — requiere acceso de campo y autorización de zona de exclusión
- Útil como **ground truth** de cualquier algoritmo de DSM diff que implementemos; el dataset es CC-BY 4.0 en OpenTopography
- **APLICACIÓN INMEDIATA:** descargar este DSM y usarlo para validar nuestro pipeline si reanalizamos S2/L9 sobre La Palma como caso prueba antes de aplicar a Chile
- **Esfuerzo:** medio sprint (descarga + integración como benchmark de tests)

### Para casos históricos chilenos
- SERNAGEOMIN ya tiene drones; este paper es **plantilla operacional** directa para Chile
- Casos relevantes: **Villarrica 2015**, **Calbuco 2015**, **Cordón Caulle 2011** — todos con volúmenes >100 Mm³ que justifican esfuerzo
- Combinable: SfM dron post-evento + S2/L9 co-evento → mejor reconstrucción TADR

---

## 5. Barsi et al. 2022 — Landsat-9 TIRS-2 radiometric performance

> **Nota:** el archivo se llama `Niclos_2021_L9TIRS2_validation.pdf` pero el contenido extraído corresponde a **Barsi, J.A., Montanaro, M., Thome, K.L., Raqueno, N.G., Hook, S., Anderson, C.H., Micijevic, E. (2022). Early Radiometric Performance of Landsat-9 Thermal Infrared Sensor**, SPIE proceedings. El paper de Niclós 2021 (sobre TIRS) puede ser una pre-publicación temática separada. Se reporta lo extraído.

**PDF:** `bibliografia/pdfs/Niclos_2021_L9TIRS2_validation.pdf`
**Páginas leídas:** 1-11 (íntegro)

### Comparación L8 vs L9 TIRS

| Parámetro | Landsat 8 TIRS-1 | Landsat 9 TIRS-2 |
|---|---|---|
| Lanzamiento | 11 feb 2013 | 27 sep 2021 (operacional feb 2022) |
| Diseño focal plane | 3 SCAs × 512×640 QWIP | Idéntico (close copy) |
| Bandas | B10 ~10.9 µm, B11 ~12.0 µm | B10 ~10.9 µm, B11 ~12.0 µm |
| **Stray light B10/B11 a 13° off-axis** | **0.4%** (peor caso) | **0.03% prelaunch / <0.01% on-orbit** |
| **Stray light a 22° off-axis** | 0.024% | **0.007%** (3× mejor) |
| Algoritmo stray-light correction | NECESARIO (USGS desde 2016, Coll-2) | **NO necesario** |
| Estabilidad responsividad/ciclo | ~0.2% | **<0.05% B10, <0.05% B11** post-CCE-reset |
| NEDT @ 300 K | ~0.2 K (B11 peor por stray) | **<0.05 K B10, <0.07 K B11** |
| Vicarious calibration residual | Mayor (impactado por stray) | **0.16 K B10, 0.61 K B11** |
| Vicarious uncertainty | mayor | **0.3 K B10, 0.5 K B11** |
| Cross-track baffles | No | Sí (3er lente) |
| CCE reset event | n/a | 12 mar 2022 → cambio responsividad 0.2%, parámetros actualizados (transparente al usuario L1/L2) |
| Quarterly relative-gain update | Desde Coll-2 (2020) | Sí (desde lanzamiento) |
| Jumpers/drifters detectados | varios | 10 jumpers + 12 drifters al 2022 |

### Coeficientes / fórmulas relevantes para Copernicus-v1

El paper **no transcribe coeficientes radiométricos numéricos K1/K2 ni gain/bias** (eso vive en los Calibration Parameter Files que USGS distribuye con cada escena, en `MTL.txt`). Lo que sí establece:

```
L_TOA = ε·t·L_T + L_u + L_d·(1-ε)        (Eq. 2 del paper)
  ε  = emisividad superficial
  t  = transmisión atmosférica en bandpass
  L_u, L_d = upwelling / downwelling radiance
```

Para nuestro pipeline esto significa: si estamos derivando temperatura de B10, debemos usar los coeficientes de cada escena (campo `RADIANCE_MULT_BAND_10`, `RADIANCE_ADD_BAND_10`, `K1_CONSTANT_BAND_10`, `K2_CONSTANT_BAND_10` del MTL). Los valores nominales prelaunch para L9 B10 son aproximadamente K1 = 799.0284, K2 = 1329.2405 (consultar MTL real).

### Qué cambia en Copernicus-v1

**Si nuestra metadata mezcla L8 y L9:**

1. **B10 es seguro de combinar** entre L8 y L9 (mismo bandpass, ambos bien calibrados desde Coll-2). Diferencia residual <0.16 K.
2. **B11 NO debe usarse en L8** sin la corrección stray-light (residual 0.61 K vs 0.16 K). Si usamos Collection-2 está corregido pero el ruido es peor que B10. **Recomendación: usar SOLO B10 monocanal de ambos** y reservar split-window (B10+B11) solo para L9.
3. **Considerar el evento CCE de marzo 2022:** escenas L9 entre 12-mar-2022 y la actualización de cal-params (~mayo 2022) tienen un offset 0.2%. USGS ya lo corrigió en Collection-2; verificar que descargamos siempre Collection-2 Tier-1.
4. **NEDT 0.05 K** significa que para detección de anomalías térmicas en cráteres chilenos (típicamente >5 K sobre fondo) tenemos margen 100×. La limitación real es la atmósfera (vapor, aerosoles), no el sensor.
5. **Verificación operacional:** añadir a `change_detection.py` una rama que separe L8 y L9 antes de cualquier estadística temporal cruzada, y aplicar bias correction si se mezclan en plots.

---

## Síntesis transversal y propuestas concretas para Copernicus-v1

### Tabla resumen — qué exporta cada paper al proyecto

| Paper | Algoritmo principal | ¿Implementable hoy? | Priority |
|---|---|---|---|
| Plank 2023 (Cumbre Vieja) | TADR via Coppola+VRP MIR | Sí (fórmula cerrada, S2/L9 OK) | **ALTA** — habilita "tasa efusión" en dashboard |
| Plank 2025 (Home Reef) | NHI sobre S2/L8/L9 | Sí (aritmética bandas) | **ALTA** — drop-in en `change_detection.py` |
| Ganci 2025 (Etna) | CL-HOTSAT + TROPOMI SO₂ + DSM diff | Parcial (TROPOMI vía GEE: sí; FCI/SEVIRI: no aplica Chile, usar GOES-16) | MEDIA |
| Civico 2022 (DSM UAS) | SfM photogrammetry post-evento | Sí (SERNAGEOMIN ya tiene drones) | BAJA (offline) |
| Barsi 2022 (L9 TIRS-2) | Calibración B10/B11 | Sí (separar L8/L9 en metadata) | **ALTA** — bug latente |

### Roadmap propuesto

1. **Sprint inmediato:** auditoría de `metadata.csv` por volcán para verificar separación L8/L9 y aplicar la regla "B10 monocanal, evitar B11 L8"
2. **Sprint corto:** añadir composite **NHI** (Normalized Hotspot Indices) al lado del SWIR clásico en el dashboard Landsat (modos Multi/Personal/Riesgosos). Dos líneas de aritmética por escena.
3. **Sprint medio:** integrar VRP MIROVA por volcán como **time-series chart** en dashboard, para los 14 más riesgosos. Reusa scrapers existentes en `Automatizacion web/`.
4. **Sprint medio:** TADR estimation via SWIR S2 + Coppola (c_rad chileno andesítico) → producto derivado por evento detectado
5. **Sprint largo:** SO₂ TROPOMI vía Google Earth Engine para Lascar, Villarrica, Copahue. Serie temporal cross-validable con MIROVA VRP
6. **Sprint largo:** GOES-16 ABI hotspots (5-15 min cadence) para los 14 más riesgosos como reemplazo regional de SEVIRI/FCI
7. **Reanalysis pipeline:** Cordón Caulle 2011-2012 como caso prueba completo (TADR Coppola + DSM diff Copernicus DEM vs post-evento + SO₂ OMI archivo)

### Datasets públicos a integrar
- OpenTopography Cumbre Vieja DSM (Civico 2022): https://doi.org/10.5069/G96971S8 — benchmark
- Etna 2025 figshare (Ganci 2025): https://doi.org/10.6084/m9.figshare.28759586 — benchmark TADR-DSM
- NASA FIRMS MODIS+VIIRS: https://firms.modaps.eosdis.nasa.gov — VRP por volcán
- Sentinel-5P TROPOMI vía GEE: `COPERNICUS/S5P/OFFL/L3_SO2`

### Referencias cruzadas con bibliografía existente del proyecto
- Coppola 2013 / 2019 / 2023 — `bibliografia/pdfs/Coppola*.pdf` (formula c_rad)
- Wright 2002/2004/2016 — algoritmos hotspot detection
- Pieri & Abrams 2004 — fundamento ASTER (precursor de la lógica multi-banda S2)

Estos 5 papers, leídos juntos, definen el **siguiente nivel del proyecto Copernicus-v1**: pasar de "visualización multi-temporal de imágenes" a "productos derivados cuantitativos" (TADR, volumen, SO₂, área activa) con calidad publicable para apoyar las decisiones de SERNAGEOMIN.
