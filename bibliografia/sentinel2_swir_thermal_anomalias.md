# Sentinel-2 SWIR — Detección de Anomalías Térmicas Volcánicas

Bibliografía estructurada para fundamentar mejoras al sistema Copernicus-v1 (monitoreo de 46 volcanes chilenos con Sentinel-2, compuesto false-color B12-B11-B04).

> Carpeta de PDFs: `bibliografia/pdfs/` — descargas previas presentes para gran parte de las referencias core (MIROVA, MODVOLC, ASTER, MOUNTS, NHI, casos chilenos). MDPI bloquea descargas automatizadas vía CDN Akamai; varios PDFs MDPI quedan pendientes y deben bajarse manualmente desde navegador.

---

## A. Algoritmos Sentinel-2 SWIR específicos

### 1. Volcanic Hot-Spot Detection Using SENTINEL-2: A Comparison with MODIS-MIROVA Thermal Data Series
- **Autores:** Massimetti F., Coppola D., Laiolo M., Valade S., Cigolini C., Ripepe M.
- **Año:** 2020
- **Journal:** Remote Sensing (MDPI), 12(5), 820
- **DOI:** 10.3390/rs12050820
- **URL:** https://www.mdpi.com/2072-4292/12/5/820
- **Open Access:** Sí
- **PDF descargado:** sí (`Massimetti2020_S2_Hotspot.pdf` / `Coppola2020_MIROVA_Frontiers.pdf` ya presentes; nuevo intento bloqueado por Akamai)
- **Resumen relevante:** Algoritmo de detección de hot spots con S2 que combina índices espectrales sobre B8A-B11-B12 (20 m) con análisis estadístico contextual de clusters de píxeles. Validado contra VRP de MIROVA en >4 años. Omisión ~1 %, comisión ~6 %.
- **Aplicabilidad al proyecto:** Este es el paper de referencia para Copernicus-v1. La fórmula de "S2Pix" (clúster de píxeles alertados por umbrales sobre relaciones B12/B11 y B11/B8A) es directamente implementable en `change_detection.py`. Reemplaza el umbral estático actual del compuesto B12-B11-B04 por un sistema multi-índice más robusto.

### 2. A Multi-Channel Algorithm for Mapping Volcanic Thermal Anomalies by Means of Sentinel-2 MSI and Landsat-8 OLI Data (NHI)
- **Autores:** Marchese F., Genzano N., Neri M., Falconieri A., Mazzeo G., Pergola N.
- **Año:** 2019
- **Journal:** Remote Sensing (MDPI), 11(23), 2876
- **DOI:** 10.3390/rs11232876
- **URL:** https://www.mdpi.com/2072-4292/11/23/2876
- **Open Access:** Sí
- **PDF descargado:** parcial (`Marchese2019_S2_MultiChannel.pdf` ya presente)
- **Resumen relevante:** Define los Normalized Hotspot Indices: NHI_SWIR = (B12-B11)/(B12+B11) y NHI_SWNIR = (B11-B8)/(B11+B8). Un píxel se clasifica hot si NHI_SWIR > 0 y NHI_SWNIR > 0 con condiciones B12 > 1.0 y NDVI < umbral. Compatible S2 + Landsat-8.
- **Aplicabilidad al proyecto:** Implementación trivial en numpy: dos restas/sumas normalizadas. Es complementario a Massimetti — Marchese es más simple y rápido, mejor candidato como primer filtro antes de aplicar el clustering espacial.

### 3. Global volcano monitoring through the Normalized Hotspot Indices (NHI) system
- **Autores:** Marchese F., Genzano N.
- **Año:** 2023
- **Journal:** Journal of the Geological Society, 180, jgs2022-014
- **DOI:** 10.1144/jgs2022-014
- **URL:** https://www.lyellcollection.org/doi/abs/10.1144/jgs2022-014
- **Open Access:** No (paywalled GSL)
- **PDF descargado:** no
- **Resumen relevante:** Implementación operacional de NHI en Google Earth Engine con notificaciones automáticas globales en ventanas de 48 h. Tasa de falsos positivos ~15 % (incluyendo fuegos de vegetación).
- **Aplicabilidad al proyecto:** Documenta cómo manejar falsos positivos por fuego de vegetación — relevante para volcanes con cobertura forestal (Calbuco, Chaitén, Hornopirén). Sugiere usar NDVI y máscara de cráter.

### 4. Implementation of the NHI Algorithm on Infrared ASTER Data
- **Autores:** Genzano N., Marchese F., Plank S., Pergola N., Tramutoli V.
- **Año:** 2021
- **Journal:** Sensors (MDPI), 21(4), 1538
- **DOI:** 10.3390/s21041538
- **URL:** https://www.mdpi.com/1424-8220/21/4/1538
- **Open Access:** Sí
- **PDF descargado:** parcial (intento bloqueado; disponible vía PMC PMC7926431)
- **Resumen relevante:** Adapta NHI a las bandas SWIR de ASTER (B7, B8, B9). Útil como puente conceptual: las mismas relaciones espectrales sirven para distintos sensores SWIR.
- **Aplicabilidad al proyecto:** Marco conceptual para extender el sistema a Landsat OLI (ya parte del repo Landsat-v1) con consistencia metodológica.

### 5. A Google Earth Engine application for mapping volcanic thermal anomalies at a global scale by means of Sentinel-2 MSI and Landsat-8 OLI data
- **Autores:** Genzano N., Pergola N., Marchese F.
- **Año:** 2020 (EGU2020 / publicado posteriormente en JVGR)
- **Journal:** EGU General Assembly 2020, EGU2020-4683
- **DOI:** 10.5194/egusphere-egu2020-4683
- **URL:** https://meetingorganizer.copernicus.org/EGU2020/EGU2020-4683.html
- **Open Access:** Sí (abstract)
- **PDF descargado:** abstract solo
- **Resumen relevante:** Describe la implementación operacional GEE del sistema NHI: sitio web nhi-tool con time-series automáticas.
- **Aplicabilidad al proyecto:** Modelo de arquitectura para automatización (alternativa a descarga directa de Copernicus DataSpace).

### 6. Detecting high-temperature anomalies from Sentinel-2 MSI images
- **Autores:** Liu Y., Liu D., Liu Y., He J., Jiang L.
- **Año:** 2021
- **Journal:** ISPRS Journal of Photogrammetry and Remote Sensing, 177, 174-193
- **DOI:** 10.1016/j.isprsjprs.2021.05.008
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0924271621001337
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Algoritmo automático con umbrales adaptativos basados en estadística contextual del entorno. Reduce falsos positivos por superficies brillantes (nubes, nieve).
- **Aplicabilidad al proyecto:** Crítico para volcanes andinos con casquete glaciar (Villarrica, Hudson, Lonquimay). Aborda la confusión SWIR sobre nieve.

---

## B. Sistema MIROVA y MODIS

### 7. Enhanced volcanic hot-spot detection using MODIS IR data: results from the MIROVA system
- **Autores:** Coppola D., Laiolo M., Cigolini C., Delle Donne D., Ripepe M.
- **Año:** 2016
- **Journal:** Geological Society, London, Special Publications, 426, 181-205
- **DOI:** 10.1144/SP426.5
- **URL:** https://www.lyellcollection.org/doi/abs/10.1144/sp426.5
- **Open Access:** No (paywalled)
- **PDF descargado:** sí (`Coppola2019_MIROVA.pdf` — versión INGV preprint)
- **Resumen relevante:** Paper fundacional de MIROVA. Detalla el algoritmo dual de filtros espectrales (BTI - Background Thermal Index) y espaciales sobre MIR de MODIS (~3.9 µm). Detecta heat flux desde 1 MW.
- **Aplicabilidad al proyecto:** Define la métrica VRP (Volcanic Radiative Power) que es el estándar para cross-validation. Copernicus-v1 debería reportar VRP estimada desde S2 SWIR usando relaciones empíricas Massimetti vs MIROVA.

### 8. Thermal Remote Sensing for Global Volcano Monitoring: Experiences From the MIROVA System
- **Autores:** Coppola D., Laiolo M., Cigolini C., Massimetti F., Delle Donne D., Ripepe M., et al.
- **Año:** 2020
- **Journal:** Frontiers in Earth Science, 7, 362
- **DOI:** 10.3389/feart.2019.00362
- **URL:** https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2019.00362/full
- **Open Access:** Sí
- **PDF descargado:** sí (`Coppola2020_MIROVA_Frontiers.pdf`)
- **Resumen relevante:** Revisión de 15 años de MIROVA. Clasifica patrones térmicos pre-eruptivos: paroxismos vs efusiones, lava lakes, domos. Usa VRE (Energía Radiativa acumulada) como predictor.
- **Aplicabilidad al proyecto:** Proporciona la taxonomía de "firmas térmicas" tipo. Útil para `alert_generator.py` — define umbrales de alerta por VRP equivalente.

### 9. Global radiant flux from active volcanoes: the 2000-2019 MIROVA database
- **Autores:** Coppola D., Laiolo M., Massimetti F., et al.
- **Año:** 2023
- **Journal:** Frontiers in Earth Science, 11, 1240107
- **DOI:** 10.3389/feart.2023.1240107
- **URL:** https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2023.1240107/full
- **Open Access:** Sí
- **PDF descargado:** sí (`Coppola_2023_GlobalRadiantFlux_MIROVA.pdf`)
- **Resumen relevante:** Base de datos global con 20 años de mediciones VRP en >200 volcanes. Catálogo público.
- **Aplicabilidad al proyecto:** Fuente de baseline histórico de cada volcán chileno monitoreado. Cross-checking de eventos.

### 10. The 2008 "silent" eruption of Nevados de Chillán (Chile) detected from space: Effusive rates and trends from the MIROVA system
- **Autores:** Coppola D., Laiolo M., Cigolini C.
- **Año:** 2016
- **Journal:** Journal of Volcanology and Geothermal Research, 327, 322-335
- **DOI:** 10.1016/j.jvolgeores.2016.08.008
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S037702731630275X
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Detección retrospectiva de erupción efusiva no detectada en tiempo real (1.4 Mm³ dacita en 8 meses). Demuestra valor de monitoreo satelital persistente.
- **Aplicabilidad al proyecto:** Caso fundacional para Chile. Justifica la necesidad de cobertura satelital sistemática que ofrece Copernicus-v1.

---

## C. Sistema MODVOLC y precursores

### 11. Automated volcanic eruption detection using MODIS
- **Autores:** Wright R., Flynn L., Garbeil H., Harris A., Pilger E.
- **Año:** 2002
- **Journal:** Remote Sensing of Environment, 82(1), 135-155
- **DOI:** 10.1016/S0034-4257(02)00030-5
- **URL:** http://modis.higp.hawaii.edu/papers/wright.pdf
- **Open Access:** Sí (preprint HIGP)
- **PDF descargado:** sí (`Wright_2002_AutomatedVolcanicEruption_MODIS.pdf`)
- **Resumen relevante:** Algoritmo seminal de detección automática usando NTI (Normalized Thermal Index) sobre MIR/TIR de MODIS. NTI = (B22-B32)/(B22+B32). Threshold global -0.8.
- **Aplicabilidad al proyecto:** El concepto de índice normalizado ratio inspira directamente NHI. Define la lógica conceptual.

### 12. MODVOLC: near-real-time thermal monitoring of global volcanism
- **Autores:** Wright R., Flynn L.P., Garbeil H., Harris A.J.L., Pilger E.
- **Año:** 2004
- **Journal:** Journal of Volcanology and Geothermal Research, 135(1-2), 29-49
- **DOI:** 10.1016/j.jvolgeores.2003.12.008
- **URL:** http://modis.higp.hawaii.edu/doc/wright2004.pdf
- **Open Access:** Sí (preprint HIGP)
- **PDF descargado:** sí (`Wright_2004_MODVOLC.pdf`)
- **Resumen relevante:** Paper de implementación operacional de MODVOLC. Detalla pipeline NRT, distribución de datos via internet, geometría de observación.
- **Aplicabilidad al proyecto:** Modelo de pipeline NRT que Copernicus-v1 imita en su workflow de GitHub Actions.

### 13. MODVOLC: 14 years of autonomous observations of effusive volcanism from space
- **Autores:** Wright R.
- **Año:** 2016
- **Journal:** Geological Society, London, Special Publications, 426
- **DOI:** 10.1144/SP426.12
- **URL:** https://www.researchgate.net/publication/281564506
- **Open Access:** Parcial (preprint en RG)
- **PDF descargado:** sí (`Wright_2016_AlgorithmsReview_HotSpots.pdf`)
- **Resumen relevante:** Revisión de 14 años, lecciones aprendidas, comparativa con otros sistemas (incluyendo MIROVA).
- **Aplicabilidad al proyecto:** Buena referencia comparativa para justificar elecciones de diseño en publicación/reporte SERNAGEOMIN.

---

## D. ASTER y aproximaciones SWIR/TIR previas

### 14. ASTER watches the world's volcanoes: A new paradigm for volcanological observations from orbit
- **Autores:** Pieri D., Abrams M.
- **Año:** 2004
- **Journal:** Journal of Volcanology and Geothermal Research, 135(1-2), 13-28
- **DOI:** 10.1016/j.jvolgeores.2003.12.018
- **URL:** https://www.researchgate.net/publication/223867748
- **Open Access:** No
- **PDF descargado:** sí (`Pieri_Abrams_2004_ASTER_volcanoes.pdf`)
- **Resumen relevante:** Establece el paradigma de monitoreo volcánico multi-espectral desde órbita usando ASTER (NIR + SWIR + TIR). Umbrales de detección de temperatura.
- **Aplicabilidad al proyecto:** Precursor conceptual de la integración Sentinel-2 SWIR + Landsat TIRS que ya hace Copernicus-v1.

### 15. Exploring the limits of identifying sub-pixel thermal features using ASTER TIR data
- **Autores:** Murphy S.W., Wright R., Oppenheimer C., Filho C.R.S.
- **Año:** 2011
- **Journal:** Journal of Volcanology and Geothermal Research, 196(3-4), 248-258
- **DOI:** 10.1016/j.jvolgeores.2010.08.014
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0377027309004429
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Aplica el método dual-band para resolver mezclas térmicas sub-pixel. Ecuaciones de Planck inversas.
- **Aplicabilidad al proyecto:** Permitiría estimar temperatura efectiva del hot spot dentro de un píxel S2 (20 m) mezclando background frío + fracción caliente. Algoritmo dual-band documentado.

### 16. Monitoring volcanic thermal anomalies from space: Size matters
- **Autores:** Marchese F., Filizzola C., Genzano N., Mazzeo G., Pergola N., Tramutoli V.
- **Año:** 2011
- **Journal:** Journal of Volcanology and Geothermal Research, 203(1-2), 48-57
- **DOI:** 10.1016/j.jvolgeores.2011.04.008
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0377027311000904
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Introduce el método RST (Robust Satellite Technique) para detección. Importancia del tamaño del feature térmico vs resolución espacial.
- **Aplicabilidad al proyecto:** Justifica usar S2 (20 m) sobre MODIS (1 km) para fumarolas y domos pequeños típicos en Chile.

---

## E. Sistemas integrados: MOUNTS, VOLCANOMS

### 17. Towards Global Volcano Monitoring Using Multisensor Sentinel Missions and Artificial Intelligence: The MOUNTS Monitoring System
- **Autores:** Valade S., Ley A., Massimetti F., D'Hondt O., Laiolo M., Coppola D., Loibl D., Hellwich O., Walter T.R.
- **Año:** 2019
- **Journal:** Remote Sensing (MDPI), 11(13), 1528
- **DOI:** 10.3390/rs11131528
- **URL:** https://www.mdpi.com/2072-4292/11/13/1528
- **Open Access:** Sí
- **PDF descargado:** sí (`MOUNTS_Valade2019.pdf` ya presente)
- **Resumen relevante:** Sistema multi-sensor integrado: S1 SAR (deformación) + S2 SWIR (térmico, algoritmo Massimetti) + S5P (SO2). CNNs para despeckle y detección de deformación.
- **Aplicabilidad al proyecto:** Arquitectura de referencia. Copernicus-v1 cubre el pilar térmico — extensión natural sería integrar S5P SO2 y S1 InSAR.

### 18. Volcanic Anomalies Monitoring System (VOLCANOMS), a Low-Cost Volcanic Monitoring System Based on Landsat Images
- **Autores:** Reath K., Ramsey M.S., Dehn J., Webley P.W., et al. (variantes con Layana et al. para Andes)
- **Año:** 2019/2020
- **Journal:** Remote Sensing (MDPI), 12(10), 1589
- **DOI:** 10.3390/rs12101589
- **URL:** https://www.mdpi.com/2072-4292/12/10/1589
- **Open Access:** Sí
- **PDF descargado:** parcial (`VOLCANOMS_Layana2020.pdf` ya presente)
- **Resumen relevante:** Sistema de bajo costo basado en Landsat 8 OLI/TIRS. Específicamente desarrollado para volcanes andinos con cobertura nubosa.
- **Aplicabilidad al proyecto:** Paper de la zona — relevancia geográfica directa. Comparación válida con Copernicus-v1 para mostrar complementariedad S2 + Landsat.

---

## F. Machine Learning aplicado

### 19. Data-Driven Random Forest Models for Detecting Volcanic Hot Spots in Sentinel-2 MSI Images
- **Autores:** Amato L., Corradino C., Torrisi F., Del Negro C.
- **Año:** 2022
- **Journal:** Remote Sensing (MDPI), 14(17), 4370
- **DOI:** 10.3390/rs14174370
- **URL:** https://www.mdpi.com/2072-4292/14/17/4370
- **Open Access:** Sí
- **PDF descargado:** no (MDPI bloqueó descarga; abstract obtenido)
- **Resumen relevante:** Random Forest entrenado sobre S2 MSI elimina necesidad de umbrales fijos. Mejor detección de anomalías débiles que algoritmos basados en thresholds.
- **Aplicabilidad al proyecto:** Camino futuro post-Massimetti. Entrenable con etiquetas de la propia base histórica de Copernicus-v1 + cross-validation MIROVA.

### 20. Cascading Machine Learning to Monitor Volcanic Thermal Activity Using Orbital Infrared Data
- **Autores:** Corradino C., Amato L., Torrisi F., Del Negro C.
- **Año:** 2024
- **Journal:** Remote Sensing (MDPI), 16(1), 171
- **DOI:** 10.3390/rs16010171
- **URL:** https://www.mdpi.com/2072-4292/16/1/171
- **Open Access:** Sí
- **PDF descargado:** no (MDPI bloqueado)
- **Resumen relevante:** Pipeline ML en cascada: detección → clasificación → cuantificación. Usa varios algoritmos en serie.
- **Aplicabilidad al proyecto:** Arquitectura ideal para `alert_generator.py` v2.

---

## G. Casos de estudio relevantes

### 21. Mapping Recent Lava Flows at Mount Etna Using Multispectral Sentinel-2 Images and Machine Learning Techniques
- **Autores:** De Luca G., Silenzi A., Fortunato G., et al.
- **Año:** 2019
- **Journal:** Remote Sensing (MDPI), 11(16), 1916
- **DOI:** 10.3390/rs11161916
- **URL:** https://www.mdpi.com/2072-4292/11/16/1916
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** Mapeo de flujos lávicos recientes en Etna con clasificadores supervisados sobre S2.
- **Aplicabilidad al proyecto:** Receta para diferenciar lava reciente vs antigua — útil para distinguir colada activa de productos erosionados.

### 22. New Insights for Detecting and Deriving Thermal Properties of Lava Flow Using Infrared Satellite during 2014-2015 Effusive Eruption at Holuhraun, Iceland
- **Autores:** Aufaristama M., Hoskuldsson A., Jonsdottir I., Ulfarsson M.O., et al.
- **Año:** 2018
- **Journal:** Remote Sensing (MDPI), 10(1), 151
- **DOI:** 10.3390/rs10010151
- **URL:** https://www.mdpi.com/2072-4292/10/1/151
- **Open Access:** Sí
- **PDF descargado:** no (MDPI bloqueó)
- **Resumen relevante:** Define el TEI (Thermal Eruption Index) basado en SWIR + TIR de Landsat 8 para discriminar dominios térmicos en flujo de lava.
- **Aplicabilidad al proyecto:** Conceptualmente extensible a la sinergia S2 SWIR + L8 TIRS que ya tiene el repo (Landsat-v1).

### 23. Mapping and characterizing the Kīlauea (Hawaiʻi) lava lake through Sentinel-2 MSI and Landsat-8 OLI observations of December 2020-February 2021
- **Autores:** Marchese F., Genzano N., Pergola N., et al.
- **Año:** 2022
- **Journal:** Environmental Modelling & Software, 148, 105273
- **DOI:** 10.1016/j.envsoft.2021.105273
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1364815221003157
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Aplicación de NHI a lago de lava reactivado en Halema'uma'u. Cuantifica área y radiancia en time-series.
- **Aplicabilidad al proyecto:** Caso de uso directo aplicable a Villarrica (lago de lava intermitente).

### 24. Monitoring of the 2015 Villarrica Volcano Eruption by Means of DLR's Experimental TET-1 Satellite
- **Autores:** Plank S., Marchese F., Filizzola C., Pergola N., Neri M., Nolde M., Martinis S.
- **Año:** 2018
- **Journal:** Remote Sensing (MDPI), 10(9), 1379
- **DOI:** 10.3390/rs10091379
- **URL:** https://www.mdpi.com/2072-4292/10/9/1379
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** Monitoreo del paroxismo del Villarrica 2015 con micro-satélite TET-1 y comparación con MODIS/MIROVA. Específico para Chile.
- **Aplicabilidad al proyecto:** Caso de Villarrica directamente aplicable. Documenta firma térmica de paroxismo estromboliano.

### 25. The Transition from MODIS to VIIRS for Global Volcano Thermal Monitoring
- **Autores:** Ramsey M.S., Corradino C., Thompson J.O., Leggett T.N.
- **Año:** 2022
- **Journal:** Sensors (MDPI), 22(5), 1713
- **DOI:** 10.3390/s22051713
- **URL:** https://www.mdpi.com/1424-8220/22/5/1713
- **Open Access:** Sí
- **PDF descargado:** no (MDPI bloqueó)
- **Resumen relevante:** Documenta la transición operacional MODIS→VIIRS por descontinuación de MODIS. Implicancias para sistemas tipo MIROVA.
- **Aplicabilidad al proyecto:** Crítico para planificación a futuro: MIROVA está migrando a VIIRS. Si Copernicus-v1 cross-valida con MIROVA, hay que considerar el cambio de fuente.

---

## H. Atmosférico / procesamiento

### 26. Sen2Cor for Sentinel-2 (ATBD)
- **Autores:** Müller-Wilm U., Louis J., Richter R., Gascon F., Niezette M.
- **Año:** 2021 (versión 2.10)
- **Journal:** ESA Technical Document S2-PDGS-MPC-ATBD-L2A
- **URL:** https://step.esa.int/thirdparties/sen2cor/2.10.0/docs/S2-PDGS-MPC-L2A-ATBD-V2.10.0.pdf
- **Open Access:** Sí
- **PDF descargado:** no (no esencial; es documento técnico ESA)
- **Resumen relevante:** Algoritmo de corrección atmosférica oficial L1C→L2A. AOT y vapor de agua, BOA reflectance.
- **Aplicabilidad al proyecto:** Necesario para entender qué transformaciones aplica L2A a B11/B12. La saturación del SWIR sobre lava puede complicar la corrección — para hot spots intensos puede ser preferible usar L1C TOA reflectance directo.

---

## Pendientes de descarga manual

PDFs que deben bajarse desde navegador (MDPI bloquea curl/wget vía Akamai edge):

- Massimetti et al. 2020 (RS 12/5/820) — versión PDF actualizada
- Marchese et al. 2019 NHI multi-channel (RS 11/23/2876)
- Genzano et al. 2021 NHI ASTER (Sensors 21/4/1538)
- Amato et al. 2022 Random Forest (RS 14/17/4370)
- Aufaristama et al. 2018 Holuhraun (RS 10/1/151)
- Corradino et al. 2024 Cascading ML (RS 16/1/171)
- Ramsey et al. 2022 MODIS→VIIRS (Sensors 22/5/1713)
- Plank et al. 2018 Villarrica TET-1 (RS 10/9/1379)
- De Luca et al. 2019 Etna ML (RS 11/16/1916)

Paywalled (requieren institución/SciHub si lo permiten políticas):

- Marchese & Genzano 2023 JGS — global NHI
- Coppola et al. 2016 Nevados Chillán (JVGR) — disponible vía researchgate request
- Murphy et al. 2011 ASTER sub-pixel (JVGR)
- Marchese et al. 2011 Size matters (JVGR)
- Liu et al. 2021 ISPRS S2 high-temp anomalies
- Marchese et al. 2022 Kilauea lava lake (Env. Modelling)

---

## Síntesis de aplicabilidad inmediata para Copernicus-v1

1. **Reemplazar el threshold actual del compuesto B12-B11-B04** con el algoritmo NHI (Marchese 2019, ref. 2): dos índices normalizados, rápido, validado.
2. **Añadir clustering espacial estilo Massimetti** (ref. 1): umbral contextual + análisis de cluster reduce falsos positivos significativamente.
3. **Cross-validar VRP estimada vs MIROVA** (refs. 7, 9) para los 46 volcanes — Coppola 2023 da baseline 2000-2019.
4. **Manejar nieve/hielo** (ref. 6, Liu 2021) — relevante para Hudson, Villarrica, Lonquimay con casquete glaciar permanente.
5. **Caso Nevados de Chillán** (ref. 10) como narrativa de motivación en reportes SERNAGEOMIN.
6. **Roadmap futuro:** Random Forest entrenado con histórico propio (refs. 19, 20) para superar limitaciones de thresholds.
