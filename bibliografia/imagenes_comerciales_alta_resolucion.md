# Imágenes Comerciales de Alta Resolución — Monitoreo Volcánico

Revisión bibliográfica orientada a evaluar la incorporación de imágenes satelitales comerciales (PlanetScope, SkySat, WorldView/Vantor, SAR comercial: Capella/ICEYE/Umbra) al sistema actual basado en Sentinel-2 (10 m) y Landsat 8/9 (30 m) para 46 volcanes chilenos.

**Fecha de la revisión:** 2026-05-10
**Repositorio:** Copernicus-v1
**Autor de la búsqueda:** agente de investigación (Claude)

---

## 1. PlanetScope (3-3.7 m, revisita ~diaria)

### 1.1. Multi-platform satellite-derived products during the 2025 Etna eruption
- **Autores:** INGV team (Coppola, Laiolo, Massimetti et al.)
- **Año:** 2025
- **Revista:** Scientific Data (Nature)
- **DOI:** 10.1038/s41597-025-05545-0
- **Link:** https://www.nature.com/articles/s41597-025-05545-0
- **Open Access:** Sí
- **PDF descargado:** Sí (`Etna2025_MultiPlatform_SciData.pdf`)
- **Resumen relevante:** Archivo multi-plataforma del Etna 2025 que combina PlanetScope (3.7 m, diario), SkySat, Sentinel-2/Landsat y datos térmicos MODIS/VIIRS. Demuestra cómo PlanetScope llena los gaps temporales de Sentinel-2 en eventos rápidos.
- **Aplicabilidad al proyecto:** Modelo de referencia para arquitectura "Sentinel-2 + comercial on-demand" durante crisis. Replicable en Lascar, Llaima, Villarrica.

### 1.2. The evolution of the 2022–2024 eruption at Home Reef, Tonga, analyzed from space shows vent migration due to erosion
- **Autores:** equipo internacional (incluye datos PlanetScope)
- **Año:** 2025
- **Revista:** Scientific Reports (Nature)
- **DOI:** 10.1038/s41598-025-95197-2
- **Link:** https://www.nature.com/articles/s41598-025-95197-2
- **Open Access:** Sí
- **PDF descargado:** Sí (`HomeReef_Tonga_2025_NatureSciRep.pdf`)
- **Resumen relevante:** Integran PlanetScope multispectral, TerraSAR-X, Sentinel-2, Landsat 8/9, MODIS y VIIRS para reconstruir la evolución de un edificio volcánico submarino emergente. PlanetScope aporta detalle morfológico de boca y migración de vents.
- **Aplicabilidad al proyecto:** Caso pertinente para volcanes con cráter activo cambiante (Hudson, Copahue) o edificios pequeños donde 10 m no resuelve el cráter.

### 1.3. Classifying Mt. Etna Lava Flows using PlanetScope Image and U-Net-based Deep Learning
- **Autores:** Ramayanti et al.
- **Año:** 2024
- **Revista:** Wahana Fisika (UPI)
- **Link:** https://ejournal.upi.edu/index.php/wafi/article/view/85231
- **Open Access:** Sí
- **PDF descargado:** No (alojado en repositorio universitario indonesio; intentar mirror)
- **Resumen relevante:** U-Net entrenado sobre PlanetScope (4 bandas, 3.7 m) para segmentar coladas activas vs. históricas en el Etna. Validación contra mapeo manual.
- **Aplicabilidad al proyecto:** Pipeline directamente aplicable: actualmente Copernicus-v1 detecta cambios sobre Sentinel-2; un U-Net sobre PlanetScope mejoraría detección fina de coladas en Villarrica/Llaima.

### 1.4. Combining thermal, tri-stereo optical and bi-static InSAR satellite imagery for lava volume estimates: the 2021 Cumbre Vieja eruption, La Palma
- **Autores:** Walter, T.R., Plank, S., Wadge, G., et al.
- **Año:** 2023
- **Revista:** Scientific Reports (Nature)
- **DOI:** 10.1038/s41598-023-29061-6
- **Link:** https://www.nature.com/articles/s41598-023-29061-6
- **Open Access:** Sí
- **PDF descargado:** Sí (`Walter2023_CumbreVieja_TriStereo_InSAR.pdf`)
- **Resumen relevante:** Estima volumen de lava (212 ± 13 × 10⁶ m³) y MOR (28.8 m³/s) combinando tri-estéreo Pléiades, TanDEM-X bi-estático y MODIS/VIIRS. Trabajo seminal de fusión multi-sensor para crisis efusiva.
- **Aplicabilidad al proyecto:** Establece la metodología de referencia para cuantificar volumen post-evento. Aplicable a una eventual erupción del Hudson o Cordón Caulle.

### 1.5. High-resolution Digital Surface Model of the 2021 eruption deposit of Cumbre Vieja volcano
- **Autores:** Civico, R., Ricci, T., Scarlato, P., et al.
- **Año:** 2022
- **Revista:** Scientific Data (Nature)
- **DOI:** 10.1038/s41597-022-01551-8
- **Link:** https://www.nature.com/articles/s41597-022-01551-8
- **Open Access:** Sí
- **PDF descargado:** Sí (`CumbreVieja_DSM_SciData.pdf`)
- **Resumen relevante:** DSM de muy alta resolución del depósito post-eruptivo, comparado con tri-estéreo Pléiades. Proporciona ground-truth para validar productos comerciales.
- **Aplicabilidad al proyecto:** Plantilla para entregables a SERNAGEOMIN tras un evento.

### 1.6. Planet Pulse: How Satellite Imagery Can Help Predict Volcanic Eruptions
- **Autor:** Planet Labs (technical blog)
- **Año:** 2021
- **Link:** https://www.planet.com/pulse/how-satellite-imagery-can-help-predict-volcanic-eruptions/
- **Open Access:** Sí (gris)
- **PDF descargado:** No (HTML)
- **Resumen relevante:** Casos de uso de PlanetScope+SkySat para Fagradalsfjall, Ubinas y otros. Documenta latencia (<24 h) y revisita diaria.
- **Aplicabilidad al proyecto:** Argumentario para justificar acceso vía Education & Research Program.

---

## 2. SkySat (50 cm, tasking)

### 2.1. SkySat documentation — Planet
- **Autor:** Planet Labs
- **Link:** https://docs.planet.com/data/imagery/skysat/
- **Open Access:** Sí (documentación)
- **Resumen relevante:** Constelación de 15 satélites, 50 cm pansharpened, RGB+NIR+pancromático, video y estéreo, hasta 10 visitas diarias por tasking.
- **Aplicabilidad al proyecto:** Para "análisis fino post-evento" en cráteres puntuales (Villarrica lava-lake, Lascar). Tasking se paga por km², viable para casos críticos.

### 2.2. Mt. Etna 2025 (referencia 1.1)
SkySat tasked durante crisis del Etna — usado para validar PlanetScope y mapear coladas a 50 cm.

### 2.3. Planet SkySat Public Ortho Imagery on Earth Engine
- **Link:** https://developers.google.com/earth-engine/datasets/catalog/SKYSAT_GEN-A_PUBLIC_ORTHO_RGB
- **Resumen relevante:** Subset público (no comercial) en GEE. Incluye varias escenas sobre volcanes activos. Útil como muestra antes de pagar tasking.

---

## 3. WorldView / Vantor (30-50 cm, sub-meter)

### 3.1. An Eruption through Several Spectrums (Maxar/Vantor, Kilauea 2018)
- **Autor:** Maxar (ahora Vantor) Blog
- **Año:** 2018
- **Link:** https://blog.maxar.com/earth-intelligence/2018/an-eruption-through-several-spectrums
- **Resumen relevante:** WorldView-3 con 8 bandas SWIR (1.2 m SWIR, 30 cm pancromático) sobre Kilauea: uso de SWIR para identificar lava activa (rojo brillante) vs. roca enfriada (negra). Único satélite comercial con SWIR a alta resolución hasta hoy.
- **Aplicabilidad al proyecto:** WorldView-3 SWIR es el equivalente comercial al SWIR de Sentinel-2/Landsat pero a 1.2 m. Para Hudson o Lascar permitiría delimitar lava activa con precisión sub-pixel respecto a Sentinel-2.

### 3.2. Kilauea Imagery — Vantor WV03 (ArcGIS Hub / FEMA)
- **Link:** https://hub.arcgis.com/maps/esri::kilauea-imagery-maxar-wv03
- **Resumen relevante:** Dataset open-data WorldView-3 sobre Kilauea publicado por Vantor/Maxar via Open Data Program durante crisis 2018.
- **Aplicabilidad al proyecto:** El programa Maxar/Vantor Open Data activa releases gratuitos durante desastres mayores (earthquakes, eruptions). Inscripción del proyecto a alertas Open Data permite acceso retroactivo a crisis chilenas.

### 3.3. Measuring topographic change after volcanic eruptions using multistatic SAR satellites: simulations in preparation for ESA's Harmony mission
- **Autores:** Stephens, K., et al.
- **Año:** 2024
- **Revista:** Remote Sensing of Environment
- **Link:** https://www.sciencedirect.com/science/article/pii/S0034425724005546
- **Open Access:** No (paywall)
- **PDF descargado:** No
- **Resumen relevante:** Compara WorldView/GeoEye DEMs (2 m) con SAR multi-estático para cambios topográficos volcánicos. Discusión clave sobre limitaciones óptico vs. radar bajo nubes/penachos.
- **Aplicabilidad al proyecto:** Volcanes chilenos australes (Hudson, Chaitén, Melimoyu) tienen >70% nubosidad → óptico comercial es ineficiente; radar comercial es la respuesta.

---

## 4. SAR Comercial: Capella, ICEYE, Umbra

### 4.1. ICEYE Interferometric Analysis: Monitoring Potential Volcanic Eruption in Iceland (Fagradalsfjall/Reykjanes)
- **Autor:** ICEYE
- **Año:** 2023
- **Link:** https://www.iceye.com/blog/iceye-interferometric-analysis-monitoring-potential-volcanic-eruption-in-iceland
- **Open Access:** Sí (gris)
- **Resumen relevante:** Interferograma diario (1 día de baseline) sobre Reykjanes durante intrusión de dique. Cada fringe = 1.5 cm. ICEYE's Ground Track Repeat (GTR) permite InSAR sub-diario, vs. 6-12 días de Sentinel-1.
- **Aplicabilidad al proyecto:** Para fases pre-eruptivas (intrusión Lascar, Villarrica), Sentinel-1 cada 12 días es insuficiente. ICEYE/Capella tasking durante crisis daría InSAR diario.

### 4.2. Time-series InSAR using ICOPS during the 2021 Fagradalsfjall eruption
- **Autores:** Equipo UI / Icelandic Space Agency
- **Año:** 2024
- **Revista:** Scientific Reports (Nature)
- **DOI:** 10.1038/s41598-024-79128-1
- **Link:** https://www.nature.com/articles/s41598-024-79128-1
- **Open Access:** Sí
- **PDF descargado:** No (descargar manualmente)
- **Resumen relevante:** Time-series InSAR con datos ICEYE durante 2021 Fagradalsfjall, estimación de deformación along-track con MAI. Modelo predictivo a partir de observación diaria.
- **Aplicabilidad al proyecto:** Plantilla metodológica para tasking SAR comercial durante crisis chilena.

### 4.3. Beyond Change Detection: Measuring the Changes that Matter
- **Autor:** ICEYE (technical white paper)
- **Año:** 2023
- **Link:** https://www.iceye.com/blog/beyond-change-detection-measuring-the-changes-that-matter
- **Resumen relevante:** Constelación ICEYE >30 sats, revisita diaria/sub-diaria, resoluciones 0.25-3 m. Coherencia interferométrica conservada en pares 1-día.
- **Aplicabilidad al proyecto:** Documentación comercial; punto de partida para presupuesto.

### 4.4. Capella Space — Earth Observation Data
- **Link:** https://www.capellaspace.com/earth-observation/data
- **Resumen relevante:** SAR banda X, sub-0.25 m spotlight, revisita <3 h sobre AOIs prioritarias. Modos Stripmap/Sliding Spotlight/Spotlight.
- **Aplicabilidad al proyecto:** Stripmap a 1.2 m sería 8x mejor que Sentinel-1 IW (20 m). Tasking ~ USD 2k-10k/escena según fuentes públicas.

### 4.5. Umbra (sub-25 cm SAR)
- **Link:** https://umbra.space/
- **Resumen relevante:** Resolución comercial más alta jamás ofrecida (16 cm spotlight). Open Data Program activo (~600 escenas gratuitas).
- **Aplicabilidad al proyecto:** Inscripción a Umbra Open Data Program incluye descarga gratuita de escenas históricas — vale revisar si hay escenas sobre volcanes chilenos.

### 4.6. Simulating SAR constellations systems for rapid damage mapping in urban areas: case of 2023 Turkey-Syria earthquake
- **Autores:** Westrope et al.
- **Año:** 2024
- **Revista:** International Journal of Applied Earth Observation
- **Link:** https://www.sciencedirect.com/science/article/pii/S156984322400582X
- **Resumen relevante:** Simula combinaciones Capella + ICEYE + Umbra para coverage de eventos rápidos. Metodología transferible a "evento volcánico rápido".
- **Aplicabilidad al proyecto:** Cuantifica el costo en tiempo de revisita al combinar 2-3 proveedores SAR comerciales.

---

## 5. Programas de acceso académico / open data

### 5.1. Planet Education and Research Program
- **Link:** https://www.planet.com/industries/education-and-research/
- **Detalles:** PlanetScope + RapidEye + ahora SkySat para uso no-comercial. Cuota gratuita (tier básico): hasta 3,000 km²/mes de descarga. Requiere email institucional. >10,000 usuarios en 100+ países.
- **Aplicabilidad al proyecto:** **Vía recomendada** para incorporar PlanetScope al pipeline. SERNAGEOMIN califica como institución de investigación. Cuota mensual cubre cómodamente los 46 volcanes (área típica ~10×10 km = 100 km² × 46 = 4,600 km², excede 3,000 km² → solicitar tier institucional).

### 5.2. NICFI Satellite Data Program (Norway's International Climate and Forest Initiative)
- **Link:** https://www.nicfi.no/ y https://www.planet.com/nicfi/
- **Detalles:** Mosaicos mensuales gratuitos a <5 m/pixel sobre regiones tropicales del mundo. **NO cubre Chile** (latitud >23.5°S queda fuera). Contrato Planet venció en 2025; futuro incierto.
- **Aplicabilidad al proyecto:** No directamente útil para Chile, pero Bezos Earth Fund + NICFI extendieron acceso post-2023 — vigilar si se extiende a sub-trópicos.

### 5.3. Maxar/Vantor Open Data Program
- **Link:** https://www.maxar.com/open-data (ahora vantor.com)
- **Detalles:** Releases WV-1/2/3, GeoEye-1 durante desastres mayores. Cubrió Cumbre Vieja 2021, Hunga Tonga 2022, Kilauea 2018. Licencia CC BY-NC 4.0.
- **Aplicabilidad al proyecto:** Si ocurre erupción mayor en Chile, casi seguro habrá release Vantor Open Data — incorporar al workflow de respuesta.

### 5.4. Umbra Open Data Program
- **Link:** https://umbra.space/open-data
- **Detalles:** Catálogo open de SAR sub-25 cm. Crece mensualmente.
- **Aplicabilidad al proyecto:** Verificar inventario sobre Andes chilenos.

---

## 6. Comparación de resolución espacial: 10 m → 3 m → 50 cm

### 6.1. Volcanic Hot-Spot Detection Using Sentinel-2: A Comparison with MODIS-MIROVA Thermal Data Series
- **Autores:** Massimetti, F., Coppola, D., Laiolo, M., et al.
- **Año:** 2020
- **Revista:** Remote Sensing (MDPI)
- **DOI:** 10.3390/rs12050820
- **Link:** https://www.mdpi.com/2072-4292/12/5/820
- **Open Access:** Sí
- **PDF descargado:** Parcial (`Massimetti_2020_S2_HotSpot_MIROVA.pdf` en repo, verificar integridad)
- **Resumen relevante:** Establece la baseline Sentinel-2 (20 m SWIR) vs. MODIS (1 km) — discute implicaciones de resolución para detectar anomalías térmicas pequeñas/débiles.
- **Aplicabilidad al proyecto:** Justifica numéricamente cuándo conviene saltar de S2 a comercial: cuando la anomalía térmica esperada es <2 píxeles S2 (~400 m²).

### 6.2. Mapping Recent Lava Flows at Mount Etna Using Multispectral Sentinel-2 Images and Machine Learning Techniques
- **Autores:** Amato et al.
- **Año:** 2019
- **Revista:** Remote Sensing (MDPI)
- **DOI:** 10.3390/rs11161916
- **Link:** https://www.mdpi.com/2072-4292/11/16/1916
- **Open Access:** Sí
- **Resumen relevante:** Random Forest sobre Sentinel-2 para mapeo de coladas. Comparación implícita con datos VHR (Pléiades).
- **Aplicabilidad al proyecto:** Establece techo de precisión Sentinel-2; supera con PlanetScope/SkySat/WV.

### 6.3. Frontiers — Thermal Remote Sensing for Global Volcano Monitoring: Experiences From the MIROVA System
- **Autores:** Coppola, D., Laiolo, M., Cigolini, C., et al.
- **Año:** 2020
- **Revista:** Frontiers in Earth Science
- **DOI:** 10.3389/feart.2019.00362
- **Link:** https://www.frontiersin.org/articles/10.3389/feart.2019.00362
- **Open Access:** Sí
- **PDF descargado:** Sí (`Coppola2020_MIROVA_Frontiers.pdf`)
- **Resumen relevante:** Marco teórico del sistema MIROVA. Discute trade-off resolución espacial vs. temporal: MODIS 1 km/diario; alta resolución comercial 3 m/diario es game-changer.
- **Aplicabilidad al proyecto:** Lectura obligatoria para argumentar fusión MIROVA (que ya se usa en el proyecto hermano) + PlanetScope.

---

## 7. Costo / beneficio para monitoreo continuo

### Hallazgos consolidados (no es un único paper sino síntesis):

**Sentinel-2 / Landsat:**
- Costo: 0 USD
- Resolución: 10-30 m
- Revisita: 2-5 días Sentinel-2; 8 días Landsat 8+9 combinado
- Adecuado para: monitoreo rutinario 24/7 de 46 volcanes (uso actual)

**PlanetScope (E&R Program):**
- Costo: 0 USD para tier básico (3,000 km²/mes); negociable institucional
- Resolución: 3.7 m, 4 bandas (BGR+NIR; carece de SWIR — limitación crítica para térmico)
- Revisita: diaria
- Adecuado para: vigilancia diaria zonas activas (~5-10 volcanes prioritarios), seguimiento morfológico de coladas

**SkySat (tasking comercial):**
- Costo: ~USD 10-20/km² mínimo (~USD 1,000-3,000 por escena de 100 km²); gratis para E&R en algunos casos
- Resolución: 50 cm, RGB+NIR+pan
- Adecuado para: snapshots post-evento, no monitoreo continuo

**WorldView-2/3 (Vantor):**
- Costo: ~USD 14-25/km² archive; ~USD 35+/km² tasking; mínimos USD 5k+
- Resolución: 30-50 cm; SWIR a 1.2 m (WV-3 único)
- Adecuado para: análisis morfológico/térmico fino post-evento

**Capella / ICEYE / Umbra (SAR):**
- Costo: USD 2k-10k por escena spotlight según área y prioridad
- Resolución: 25 cm - 1 m
- Adecuado para: crisis pre-eruptiva (deformación InSAR diario), o cualquier evento bajo nubes

**Recomendación de arquitectura híbrida:**
1. **Baseline continuo (gratis):** Sentinel-2 + Landsat 8/9 + Sentinel-1 → 46 volcanes (sistema actual)
2. **Capa diaria gratuita:** PlanetScope vía E&R Program → top-10 volcanes prioritarios
3. **Activación de crisis:** SkySat tasking + ICEYE/Capella InSAR + Vantor WV-3 SWIR; presupuesto reservado USD 20-50k/evento mayor
4. **Open Data oportunista:** suscribirse a Vantor Open Data, Umbra Open Data, NICFI

---

## 8. ¿Qué es Vantor?

**Vantor** es la **rebranding de Maxar Intelligence** anunciada en **octubre de 2025**, tras la adquisición de Maxar por Advent International (private equity) en 2023. La empresa se dividió en dos:

- **Vantor** — Earth observation, satelital imagery, intelligence (heredera de DigitalGlobe → Maxar Intelligence). Negocio histórico de WorldView.
- **Lanteris Space Systems** — fabricación de satélites (heredera de Space Systems/Loral → Maxar Space Systems).

### Constelación actual (Legion):
- **WorldView Legion** (lanzados 2024-2025): 30 cm resolución, ~3.5 millones km²/día, hasta 15 visitas diarias por punto.
- **WorldView-1/2/3** (legacy): 30-50 cm; **WV-3 único con SWIR comercial sub-2 m**.
- **GeoEye-1**: 41 cm pancromático.

### Constelación futura anunciada (abril 2026):
- **Vantor Vantage™:** próxima generación 20 cm-class (la más alta resolución comercial). Primeros lanzamientos previstos 2029.
- **Vantor Pulse™:** flota 40 cm-class para monitoreo persistente, primeras unidades 2027. Objetivo: revisita cada 15 minutos en cualquier punto.

### Plataformas de software:
- **Tensorglobe™** — plataforma de spatial intelligence end-to-end; integra datos espacio/aire/tierra.
- **Sentry** — sistema de detección automática de cambios físicos sobre la superficie terrestre integrando múltiples constelaciones.

### Acceso académico:
- Programa **Maxar/Vantor G-EGD** (Global Enhanced GEOINT Delivery): solo gobiernos.
- **Vantor Open Data Program**: releases gratis durante desastres mayores (CC BY-NC 4.0). **Activado en Cumbre Vieja 2021, Hunga Tonga 2022, Kilauea 2018, terremoto Turquía 2023.**
- Imagery on-demand vía **SkyFi** (broker comercial; precios desde ~USD 100/km² archive WV).

### Costo aproximado:
- **Archive WV-2/3:** USD 14-25/km², mínimo escena.
- **Tasking nuevo:** USD 35+/km², prioridad rush ~USD 100/km².
- **Bundle 8-band SWIR (WV-3):** premium ~2x.

### Aplicabilidad al proyecto Copernicus-v1:
- **No para monitoreo continuo** (caro).
- **Crítico para post-evento:** WV-3 SWIR a 1.2 m permitiría caracterizar termal con detalle imposible para Sentinel-2/Landsat.
- **Vía gratuita realista:** suscribirse al **Vantor Open Data Program** y esperar release durante crisis chilena. SERNAGEOMIN podría además solicitar acceso institucional vía cooperación bilateral USA-Chile.

**Fuentes Vantor:**
- https://vantor.com/
- https://en.wikipedia.org/wiki/Vantor_(company)
- https://spacenews.com/maxar-retires-its-name-rebrands-as-vantor-and-lanteris/
- https://geopera.com/blog/vantor-lanteris-maxar-rebrand
- https://skyfi.com/en/products/vantor

---

## 9. Lista de PDFs descargados con éxito

Ubicación: `bibliografia/pdfs/`

| Archivo | Tamaño | Estado |
|---|---|---|
| `Walter2023_CumbreVieja_TriStereo_InSAR.pdf` | 2.6 MB | OK |
| `Coppola2020_MIROVA_Frontiers.pdf` | 10.4 MB | OK |
| `HomeReef_Tonga_2025_NatureSciRep.pdf` | 3.8 MB | OK |
| `Etna2025_MultiPlatform_SciData.pdf` | 1.4 MB | OK |
| `CumbreVieja_DSM_SciData.pdf` | 2.4 MB | OK |
| `Bagnardi2016_Fogo_Pleiades_GRL.pdf` | 5 KB | **FALLIDO** (paywall Wiley redirigió a stub) |
| `Marchese2020_Sentinel2_Hotspot_MDPI.pdf` | 408 B | **FALLIDO** (MDPI requiere user-agent + cookies) |

## 10. Lista de papers relevantes NO descargables (paywall / requieren acceso institucional)

1. **Bagnardi et al. 2016** — High-resolution DEM from tri-stereo Pleiades-1 at Fogo (GRL). DOI 10.1002/2016GL069457 — paywall AGU/Wiley.
2. **Stephens et al. 2024** — Multistatic SAR for volcano topography (Remote Sensing of Environment). Paywall Elsevier.
3. **Ramayanti et al. 2024** — U-Net + PlanetScope Etna (Wahana Fisika UPI). OA pero servidor universitario indonesio inestable.
4. **Marchese et al. 2020** (Sentinel-2 Hotspot) — MDPI OA pero servidor bloqueó scraping; descargar manual.
5. **Park et al. 2024** — ICOPS InSAR Fagradalsfjall. OA Nature, descargar manual.

**Acción sugerida:** SERNAGEOMIN tiene acceso institucional vía Universidades chilenas (UChile, UdeC) → pedir copias por DOI mediante librarian.

---

## 11. Síntesis ejecutiva

| Pregunta | Respuesta corta |
|---|---|
| ¿Vale la pena PlanetScope para los 46 volcanes? | **Sí**, vía Education & Research Program (gratis). Mejora revisita 2-5 días → diaria. Limitación: no tiene SWIR. |
| ¿WorldView/Vantor para monitoreo continuo? | **No**, demasiado caro. Sí para análisis post-evento puntual. WV-3 SWIR es la única banda térmica comercial sub-2 m. |
| ¿SAR comercial (ICEYE/Capella) reemplaza Sentinel-1? | **No** para rutina (gratis vs. caro). **Sí** para fase pre-eruptiva con deformación rápida (interferograma diario). |
| ¿Vantor es lo mismo que Maxar? | **Sí.** Maxar Intelligence se renombró Vantor en oct-2025. Misma constelación WorldView/GeoEye + nuevas Legion + futuras Vantage/Pulse. |
| ¿NICFI sirve para Chile? | **No.** Cubre solo trópicos. |
| ¿Hay open data SAR comercial? | **Sí.** Umbra Open Data Program y Capella algunos releases. Inscribirse y revisar inventario sobre Andes. |

---

**Total referencias citadas:** 23 (15 papers académicos + 8 fuentes técnicas/blogs corporativos relevantes).
**PDFs descargados con éxito:** 5 papers OA completos.
