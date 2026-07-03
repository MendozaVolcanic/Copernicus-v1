# Monitoreo Satelital — Volcanes Chilenos y Andinos

Búsqueda bibliográfica enfocada en monitoreo satelital de volcanes chilenos y andinos, fusión multi-sensor (Sentinel-2 + Landsat + Sentinel-1 SAR), sistemas de alerta temprana, y trabajos paralelos en Latinoamérica.

Fecha de compilación: 2026-05-10. Compilado para el sistema Copernicus-v1 (43 volcanes chilenos, SERNAGEOMIN/OVDAS).

---

## 1. Villarrica (lago de lava persistente)

### 1.1 Volcanic Hot-Spot Detection Using SENTINEL-2: A Comparison with MODIS–MIROVA Thermal Data Series
- **Autores:** Massimetti, F.; Coppola, D.; Laiolo, M.; Valade, S.; Cigolini, C.; Ripepe, M.
- **Año:** 2020
- **DOI:** 10.3390/rs12050820
- **Link:** https://www.mdpi.com/2072-4292/12/5/820
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** parcial (stub MDPI, descarga directa bloqueada)
- **Resumen relevante:** Algoritmo de detección de hotspots en S2 MSI usando bandas SWIR 8a-11-12 (20 m), validado contra MIROVA/MODIS en cinco volcanes incluyendo Villarrica y Lascar. En Villarrica reproduce VRP entre 1e7 y 1e8 W con conteo S2Pix variable.
- **Aplicabilidad al proyecto:** Algoritmo directamente reimplementable en `change_detector.py` y `spectral_downloader.py`. Define umbrales NHI/NHIswir que pueden integrarse a la detección automatizada actual.

### 1.2 Thermal Remote Sensing for Global Volcano Monitoring: Experiences From the MIROVA System
- **Autores:** Coppola, D.; Laiolo, M.; Cigolini, C.; Massimetti, F.; Delle Donne, D.; Ripepe, M.; et al.
- **Año:** 2019
- **DOI:** 10.3389/feart.2019.00362
- **Link:** https://www.frontiersin.org/articles/10.3389/feart.2019.00362/full
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** sí (`Coppola2019_MIROVA.pdf`, 10 MB)
- **Resumen relevante:** Descripción operativa del sistema MIROVA (MODIS/MIR), métricas de VRP, casos de uso incluyendo Villarrica. Define la lógica de alerta térmica que el proyecto Copernicus-v1 emula con S2/Landsat.
- **Aplicabilidad al proyecto:** Referencia base para toda la lógica de `alert_generator.py`. La métrica de Volcanic Radiative Power debería incorporarse al pipeline para hacer cross-validación con MIROVA scrapeada en `Automatizacion web/`.

---

## 2. Lascar (anomalía térmica persistente)

### 2.1 Quantitative analysis of thermal anomaly from Lascar volcano (northern Chile) using Landsat TM and ETM+ imagery during period 2000-2004
- **Autores:** González-Ferrán, O.; Aguilera, F.; Layana, S.
- **Año:** 2014
- **Link:** https://www.researchgate.net/publication/265552273
- **Idioma:** EN
- **Open Access:** parcial (ResearchGate)
- **PDF descargado:** no
- **Resumen relevante:** Cuantificación pixel-a-pixel de la anomalía térmica del cráter activo de Lascar (300 m de diámetro) en TM/ETM+, con temperaturas >380°C en ventanas SWIR. Predicen reducción térmica previa a erupciones de 1986 y 1993.
- **Aplicabilidad al proyecto:** Lascar es uno de los 43 volcanes monitoreados; este estudio define el régimen térmico esperado y la firma pre-eruptiva (decaimiento térmico) que la detección automatizada debería capturar.

### 2.2 Thermal monitoring of Lascar Volcano, Chile, using infrared data from the along-track scanning radiometer: a 1992–1995 time series
- **Autores:** Wooster, M. J.; Rothery, D. A.
- **Año:** 1997
- **DOI:** 10.1007/s004450050163
- **Link:** https://link.springer.com/article/10.1007/s004450050163
- **Idioma:** EN
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Serie temporal ATSR de 3 años; identifica caída de radiación térmica como precursor eruptivo. Trabajo seminal para Lascar.
- **Aplicabilidad al proyecto:** Soporte teórico para el módulo de alertas: el patrón "decaimiento previo a erupción" debe estar codificado como criterio.

### 2.3 The 16 September 1986 eruption of Lascar volcano, north Chile: Satellite investigations
- **Autores:** Glaze, L. S.; Francis, P. W.; Self, S.; Rothery, D. A.
- **Año:** 1989
- **DOI:** 10.1007/BF01067952
- **Link:** https://link.springer.com/article/10.1007/BF01067952
- **Idioma:** EN
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Trabajo pionero TM en Lascar; demuestra capacidad de detectar anomalías <100 m a >150°C. Caso de estudio histórico para algoritmos de detección.
- **Aplicabilidad al proyecto:** Estableció el límite de detección que sigue vigente para Sentinel-2 (resolución equivalente).

---

## 3. Puyehue – Cordón Caulle (erupción 2011, deformación)

### 3.1 Rhyolitic volcano dynamics in the Southern Andes: Contributions from 17 years of InSAR observations at Cordón Caulle volcano from 2003 to 2020
- **Autores:** Delgado, F.; Pritchard, M. E.; Ebmeier, S.; González, P. J.; Lara, L.
- **Año:** 2021
- **DOI:** 10.1016/j.jvolgeores.2020.107011
- **Link:** https://www.sciencedirect.com/science/article/abs/pii/S0895981120303849
- **Idioma:** EN
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** 17 años de InSAR (ALOS, ENVISAT, Sentinel-1) cubriendo ciclo completo pre/co/post-erupción. Uplift pre-eruptivo de ~0.5 m en 2003-2011 a 3-30 cm/yr; deflación co-eruptiva de 1.5 m por dos fuentes a 4-6 km. Co-autor Luis Lara (SERNAGEOMIN).
- **Aplicabilidad al proyecto:** Fundamental para integrar Sentinel-1 al pipeline. Define magnitudes y escalas temporales esperadas en deformación pre-eruptiva en SVZ.

### 3.2 Rapid reinflation following the 2011–2012 rhyodacite eruption at Cordón Caulle volcano (Southern Andes) imaged by InSAR: Evidence for magma reservoir refill
- **Autores:** Delgado, F.; Pritchard, M. E.; Lohman, R.; Naranjo, J. A.
- **Año:** 2016
- **DOI:** 10.1002/2016GL070066
- **Link:** https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2016GL070066
- **Idioma:** EN
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Reinflación post-eruptiva de Cordón Caulle imaged con InSAR. Co-autor José Naranjo (SERNAGEOMIN).
- **Aplicabilidad al proyecto:** Demuestra que post-eruption monitoring con InSAR es esencial; aplicable a Calbuco y Chaitén actualmente en el sistema.

### 3.3 The 2011 Cordón Caulle eruption triggered by slip on the Liquiñe-Ofqui fault system
- **Autores:** Wendt, A.; Tassara, A.; Báez, J. C.; Basualto, D.; Lara, L. E.; et al.
- **Año:** 2022
- **DOI:** 10.1016/j.epsl.2022.117365
- **Link:** https://www.sciencedirect.com/science/article/abs/pii/S0012821X2200022X
- **Idioma:** EN
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Análisis tectono-volcánico vinculando la falla Liquiñe-Ofqui con el disparo de la erupción. Autores chilenos.
- **Aplicabilidad al proyecto:** Justifica priorizar volcanes alineados con LOFZ (Villarrica, Llaima, Cordón Caulle, Chaitén, Hudson) en el sistema de alertas.

### 3.4 Possible structural control on the 2011 eruption of Puyehue-Cordón Caulle determined by InSAR, GPS and seismicity
- **Autores:** Jay, J. A.; Costa, F.; Pritchard, M.; Lara, L.; Singer, B.; Herrin, J.
- **Año:** 2014
- **DOI:** 10.1093/gji/ggw355
- **Link:** https://doi.org/10.1093/gji/ggw355
- **Idioma:** EN
- **Open Access:** parcial
- **PDF descargado:** no
- **Resumen relevante:** Fusión multi-sensor (InSAR + GPS + sismicidad) para Cordón Caulle 2011. Co-autor Luis Lara.
- **Aplicabilidad al proyecto:** Plantilla metodológica para fusionar Sentinel-1 con datos terrestres SERNAGEOMIN.

---

## 4. Calbuco (erupción 2015)

### 4.1 Multisatellite Multisensor Observations of a Sub-Plinian Volcanic Eruption: The 2015 Calbuco Explosive Event in Chile
- **Autores:** Marzano, F. S.; Mereu, L.; Scollo, S.; Donnadieu, F.; Bonadonna, C.
- **Año:** 2018
- **DOI:** 10.1109/TGRS.2017.2783220
- **Link:** https://ui.adsabs.harvard.edu/abs/2018ITGRS..56.2597M/abstract
- **Idioma:** EN
- **Open Access:** No (preprint Earth-prints)
- **PDF descargado:** no (descarga falló)
- **Resumen relevante:** Combinación A-train (microondas + IR + visible) sobre Calbuco; altura de pluma 21 km, masa de ceniza 3.65e10 kg. Demuestra que IR no funciona cerca del vento.
- **Aplicabilidad al proyecto:** Calbuco es uno de los 43 volcanes; este es el benchmark para la detección de columnas eruptivas grandes.

### 4.2 Volcanic lightning and plume behavior reveal evolving hazards during the April 2015 eruption of Calbuco volcano, Chile
- **Autores:** Van Eaton, A. R.; Amigo, A.; Bertin, D.; Mastin, L. G.; Giacosa, R. E.; et al.
- **Año:** 2016
- **DOI:** 10.1002/2015GL067245
- **Link:** https://pubs.usgs.gov/publication/70182739
- **Idioma:** EN
- **Open Access:** Sí (USGS)
- **PDF descargado:** no
- **Resumen relevante:** Análisis de pluma con datos satelitales + relámpago volcánico. Co-autores Bertin (SERNAGEOMIN) y Amigo.
- **Aplicabilidad al proyecto:** Trabajo SERNAGEOMIN directamente relacionado; cita patrones de pluma reproducibles en Sentinel-2.

### 4.3 Synergetic Aerosol Layer Observation After the 2015 Calbuco Volcanic Eruption Event
- **Autores:** Bègue, N.; Vignelles, D.; Berthet, G.; Portafaix, T.; et al.
- **Año:** 2019
- **DOI:** 10.3390/rs11020195
- **Link:** https://www.mdpi.com/2072-4292/11/2/195
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** Observación sinérgica multi-sensor (CALIPSO + lidar terrestre) de aerosoles tras Calbuco 2015.
- **Aplicabilidad al proyecto:** Modelo de fusión de fuentes para pluma estratosférica.

---

## 5. Hudson

### 5.1 The 2011 Hudson volcano eruption (Southern Andes, Chile): Pre-eruptive inflation and hotspots observed with InSAR and thermal imagery
- **Autores:** Delgado, F.; Pritchard, M.; Lohman, R.; Naranjo, J. A.
- **Año:** 2014
- **DOI:** 10.1007/s00445-014-0815-9
- **Link:** https://link.springer.com/article/10.1007/s00445-014-0815-9
- **Idioma:** EN
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Hudson infló 2-3 cm/yr entre 2004-2010; ASTER detectó hotspots 7-8 K sobre fondo cuatro meses antes de la erupción 2011. Co-autor Naranjo (SERNAGEOMIN).
- **Aplicabilidad al proyecto:** Caso ejemplar de detección pre-eruptiva combinando InSAR + térmico, exactamente lo que Copernicus-v1 + Sentinel-1 podría replicar para Hudson hoy.

---

## 6. Chaitén (erupción riolítica 2008)

### 6.1 Overview of Chaitén Volcano, Chile, and its 2008-2009 eruption
- **Autores:** Lara, L. E. (coord.); Major, J. J.; Pierson, T. C.; et al.
- **Año:** 2013
- **Link:** https://pubs.usgs.gov/publication/70046211 ; versión Andean Geology: https://www.redalyc.org/pdf/1739/173927491001.pdf
- **Idioma:** EN/ES
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** Volumen Andean Geology editado por Luis Lara compilando observaciones de la erupción riolítica más grande desde Katmai 1912. Incluye SAR comercial near-real-time documentando crecimiento de domo >25 m³/s.
- **Aplicabilidad al proyecto:** Lectura obligatoria para entender el régimen eruptivo de Chaitén, que sigue activo en el catálogo Copernicus-v1.

### 6.2 Satellite remote sensing of the 2008 Chaitén eruption
- **Autores:** Stohl, A.; Prata, A. J.; Eckhardt, S.; et al. (NILU)
- **Año:** 2010
- **Link:** https://nilu.com/publication/25613/
- **Idioma:** EN
- **Open Access:** parcial
- **PDF descargado:** no
- **Resumen relevante:** Análisis de pluma de ceniza Chaitén con MODIS y AIRS, transporte transcontinental.
- **Aplicabilidad al proyecto:** Validación histórica del sistema de detección de plumas.

---

## 7. Copahue (binacional Chile-Argentina)

### 7.1 An analysis of volcanic SO2 and ash emissions from Copahue volcano
- **Autores:** Aguilera, F.; Gutiérrez, F.; Layana, S.; Inostroza, M.; et al.
- **Año:** 2022
- **DOI:** 10.1016/j.jvolgeores.2021.107405
- **Link:** https://www.sciencedirect.com/science/article/abs/pii/S0895981121002121
- **Idioma:** EN
- **Open Access:** parcial (Academia.edu)
- **PDF descargado:** no
- **Resumen relevante:** OMI/OMPS sobre Copahue 2016, tasa promedio 985 t/d SO2. Autores chilenos (UCN), incluyendo F. Aguilera y S. Layana.
- **Aplicabilidad al proyecto:** Plantilla para integrar TROPOMI/Sentinel-5P en el pipeline para flujo de SO2.

### 7.2 Analysis of thermal anomalies at Copahue Volcano between October 2011 and the December 2012 eruption with MODIS
- **Autores:** Reckziegel, F.; Bustos, E.; Mingari, L.; et al.
- **Año:** 2022
- **DOI:** 10.1016/j.jvolgeores.2021.107361
- **Link:** https://www.sciencedirect.com/science/article/abs/pii/S0895981121001577
- **Idioma:** EN
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Detección térmica MODIS pre-eruptiva en Copahue 2012.
- **Aplicabilidad al proyecto:** Modelo de monitoreo binacional aplicable al volcán compartido.

### 7.3 The Copahue Volcanic-Hydrothermal System and Applications for Volcanic Surveillance
- **Autores:** Caselli, A. T.; Agusto, M.; Velez, M. L.; Forte, P.; et al.
- **Año:** 2016
- **DOI:** 10.1007/978-3-662-48005-2_9
- **Link:** https://link.springer.com/chapter/10.1007/978-3-662-48005-2_9
- **Idioma:** EN
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Capítulo de libro sobre vigilancia integral en Copahue (lago crater, hidrotermal). Caselli es referente argentino.
- **Aplicabilidad al proyecto:** Marco conceptual para fusionar firma térmica con química del lago.

### 7.4 Seasonal control on phreatic activity of the crater lake of Copahue volcano during the 2018–2022 eruptive cycle
- **Autores:** Tassi, F.; Agusto, M.; et al.
- **Año:** 2025
- **DOI:** 10.1007/s00445-025-01826-z
- **Link:** https://link.springer.com/article/10.1007/s00445-025-01826-z
- **Idioma:** EN
- **Open Access:** parcial
- **PDF descargado:** no
- **Resumen relevante:** Ciclo eruptivo reciente de Copahue con control estacional sobre actividad freática.
- **Aplicabilidad al proyecto:** Justifica considerar estacionalidad en alertas — el sistema actual no la modela.

---

## 8. Planchón-Peteroa, Tupungatito, Lanín (lagos crateriarios)

### 8.1 The Evolution of Peteroa Volcano (Chile–Argentina) Crater Lakes Between 1984 and 2020 Based on Landsat and Planet Labs Imagery Analysis
- **Autores:** Aguilera, F.; Benavente, O.; Gutiérrez, F.; Romero, J.; Saltori, O.; et al.
- **Año:** 2021
- **DOI:** 10.3389/feart.2021.722056
- **Link:** https://www.frontiersin.org/articles/10.3389/feart.2021.722056/full
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** sí (`Aguilera2022_Peteroa_Lakes.pdf`, 5.6 MB)
- **Resumen relevante:** 36 años de Landsat TM/ETM+/OLI sobre lagos crater de Peteroa. Cuantifica radiancia térmica, temperatura de brillo, flujos de calor. Autores chilenos clave (Aguilera UCN, Benavente).
- **Aplicabilidad al proyecto:** Metodología de serie temporal Landsat directamente aplicable a Peteroa, Copahue, Tupungatito en Copernicus-v1. Demuestra que el archivo histórico Landsat 1984+ es explotable.

### 8.2 Eruptive activity of Planchón-Peteroa volcano for period 2010-2011, Southern Andean Volcanic Zone, Chile
- **Autores:** Aguilera, F.; Benavente, O.; Gutiérrez, F.; et al.
- **Año:** 2016
- **Link:** https://www.redalyc.org/journal/1739/173945728002/html/
- **Idioma:** EN
- **Open Access:** Sí (Andean Geology)
- **PDF descargado:** no
- **Resumen relevante:** Caracterización de actividad 2010-2011 con observación satelital + terrestre.
- **Aplicabilidad al proyecto:** Caso de estudio chileno publicado en Andean Geology, referencia local.

### 8.3 Lanín volcano (39.5°S), Southern Andes: geology and morphostructural evolution
- **Autores:** Lara, L. E.
- **Año:** 2004
- **Link:** https://www.andeangeology.cl/index.php/revista1/article/view/V31n2-a04/html
- **Idioma:** EN/ES
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** Trabajo geológico fundamental de Luis Lara (SERNAGEOMIN) sobre Lanín, esencial para contexto eruptivo de un volcán argentino-chileno.
- **Aplicabilidad al proyecto:** Lanín está en el catálogo Copernicus-v1; este es el background geológico requerido.

---

## 9. Nevados de Chillán

### 9.1 Volcanic unrest at Nevados de Chillán (Southern Andean Volcanic Zone) from January 2019 to November 2020, imaged by DInSAR
- **Autores:** Astort, A.; Walter, T. R.; Ruch, J.; Zimmer, M.; et al.
- **Año:** 2022
- **DOI:** 10.1016/j.jvolgeores.2022.107551
- **Link:** https://www.sciencedirect.com/science/article/pii/S0377027322000993
- **Idioma:** EN
- **Open Access:** parcial
- **PDF descargado:** no
- **Resumen relevante:** DInSAR Sentinel-1 cubriendo el unrest 2019-2020 en Chillán; identifica fuente de presión.
- **Aplicabilidad al proyecto:** Chillán es Top-3 más peligroso (SERNAGEOMIN); este trabajo define la línea base InSAR a integrar.

### 9.2 Use of SBAS to monitor activity of the Nevados de Chillán volcano (UN-SPIDER case study)
- **Autores:** UN-SPIDER / SERNAGEOMIN
- **Año:** 2020
- **Link:** https://www.un-spider.org/use-sbas-monitor-activity-nevados-de-chillan-volcano
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** Caso institucional ONU usando Small BAseline Subset InSAR sobre Chillán.
- **Aplicabilidad al proyecto:** Workflow SBAS reproducible con Sentinel-1 SLC.

---

## 10. Sistemas multi-sensor / fusión Sentinel-1 + Sentinel-2 + Landsat

### 10.1 Towards Global Volcano Monitoring Using Multisensor Sentinel Missions and Artificial Intelligence: The MOUNTS Monitoring System
- **Autores:** Valade, S.; Ley, A.; Massimetti, F.; D'Hondt, O.; Laiolo, M.; Coppola, D.; et al.
- **Año:** 2019
- **DOI:** 10.3390/rs11131528
- **Link:** https://www.mdpi.com/2072-4292/11/13/1528
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** parcial (stub)
- **Resumen relevante:** Sistema MOUNTS combina Sentinel-1 SAR (deformación), Sentinel-2 SWIR (térmico), Sentinel-5P TROPOMI (SO2), datos sísmicos y CNN para detección de unrest.
- **Aplicabilidad al proyecto:** Arquitectura de referencia. Copernicus-v1 ya cubre S2/Landsat; MOUNTS es la hoja de ruta para añadir S1 + S5P.

### 10.2 Large-scale demonstration of machine learning for the detection of volcanic deformation in Sentinel-1 satellite imagery
- **Autores:** Gaddes, M. E.; Hooper, A.; Anantrasirichai, N.; Bull, D.; Ebmeier, S. K.
- **Año:** 2022
- **DOI:** 10.1007/s00445-022-01608-x
- **Link:** https://link.springer.com/article/10.1007/s00445-022-01608-x
- **Idioma:** EN
- **Open Access:** Sí (PMC)
- **PDF descargado:** sí (`Anantrasirichai2022_ML_Sentinel1.pdf` y `Gaddes_2022_ML_Sentinel1_Deformation.pdf`, ~4.4 MB)
- **Resumen relevante:** CNN sobre 600.000 interferogramas Sentinel-1 cubriendo >900 volcanes; reduce inspección manual de 30k a ~100 imágenes.
- **Aplicabilidad al proyecto:** Modelo ML reusable para integrar al pipeline. Reduciría falsos positivos en alertas.

### 10.3 A Multi-Channel Algorithm for Mapping Volcanic Thermal Anomalies by Means of Sentinel-2 MSI and Landsat-8 OLI Data
- **Autores:** Marchese, F.; Genzano, N.; Neri, M.; Falconieri, A.; Mazzeo, G.; Pergola, N.
- **Año:** 2019
- **DOI:** 10.3390/rs11232876
- **Link:** https://www.mdpi.com/2072-4292/11/23/2876
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** parcial
- **Resumen relevante:** Algoritmo NHI (Normalized Hot Spot Index) que combina S2 + L8 OLI usando bandas SWIR y NIR. Aprovecha compatibilidad espectral S2/L8.
- **Aplicabilidad al proyecto:** Implementación directa para combinar las dos series del proyecto (`docs/sentinel2/` + `docs/landsat/`).

### 10.4 Synergic Use of Multi-Sensor Satellite Data for Volcanic Hazards Monitoring: The Fogo (Cape Verde) 2014–2015 Effusive Eruption
- **Autores:** Cappello, A.; Ganci, G.; Bilotta, G.; Corradino, C.; Hérault, A.; Del Negro, C.
- **Año:** 2020
- **DOI:** 10.3389/feart.2020.00022
- **Link:** https://www.frontiersin.org/articles/10.3389/feart.2020.00022/full
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** Fusión multi-sensor (radar, térmico, óptico) en Fogo. Demuestra valor cuando un sensor falla por nubes o pluma densa.
- **Aplicabilidad al proyecto:** Justifica diseñar el pipeline con fallback automático S2 → Landsat → S1 según condiciones.

### 10.5 Application of Machine Learning to Classification of Volcanic Deformation in Routinely Generated InSAR Data
- **Autores:** Anantrasirichai, N.; Biggs, J.; Albino, F.; Hill, P.; Bull, D.
- **Año:** 2018
- **DOI:** 10.1029/2018JB015911
- **Link:** https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2018JB015911
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** Trabajo seminal de CNN sobre InSAR volcánico. Define la metodología que Gaddes 2022 escala.
- **Aplicabilidad al proyecto:** Background metodológico del módulo ML.

---

## 11. Plataforma chilena: VOLCANOMS

### 11.1 Volcanic Anomalies Monitoring System (VOLCANOMS), a Low-Cost Volcanic Monitoring System Based on Landsat Images
- **Autores:** Layana, S.; Aguilera, F.; Rojas, F.; Inostroza, M.; et al. (Universidad Católica del Norte)
- **Año:** 2020
- **DOI:** 10.3390/rs12101589
- **Link:** https://www.mdpi.com/2072-4292/12/10/1589 ; sistema en línea: http://volcano.ucn.cl/
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** parcial (stub)
- **Resumen relevante:** Primera plataforma chilena de monitoreo volcánico satelital, basada en Landsat NIR/SWIR/TIR; calcula radiancia térmica, temperatura efectiva, áreas de anomalía, flujos de calor convectivo/radiativo. Implementada en Python.
- **Aplicabilidad al proyecto:** El proyecto Copernicus-v1 es complementario directo a VOLCANOMS. Alinear formatos de salida y citar como antecedente nacional. Equipo UCN (F. Aguilera, S. Layana) son interlocutores naturales.

---

## 12. Latinoamérica — referencias paralelas

### 12.1 Continuous monitoring of the 2015–2018 Nevado del Ruiz activity, Colombia, using satellite infrared images and local infrasound records
- **Autores:** Laiolo, M.; Ripepe, M.; Cigolini, C.; Coppola, D.; Genco, R.; et al.
- **Año:** 2020
- **DOI:** 10.1186/s40623-020-01197-z
- **Link:** https://earth-planets-space.springeropen.com/articles/10.1186/s40623-020-01197-z
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** Monitoreo continuo Nevado del Ruiz con MODIS + infrasonido. Modelo extrapolable al SVZ chileno.
- **Aplicabilidad al proyecto:** Demuestra integración satelital + ground-based para volcán similar a Chillán.

### 12.2 Magma extrusion during the Ubinas 2013–2014 eruptive crisis based on satellite thermal imaging (MIROVA) and ground-based monitoring
- **Autores:** Coppola, D.; Macedo, O.; Ramos, D.; Finizola, A.; Delle Donne, D.; et al. (con OVI/INGEMMET)
- **Año:** 2015
- **DOI:** 10.1016/j.jvolgeores.2015.06.013
- **Link:** https://www.sciencedirect.com/science/article/abs/pii/S0377027315002139
- **Idioma:** EN
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** MIROVA + monitoreo terrestre INGEMMET en Ubinas. Cuantifica extrusión magmática.
- **Aplicabilidad al proyecto:** Modelo cooperativo INGEMMET-Italia replicable con SERNAGEOMIN.

### 12.3 Hazard assessment studies and multiparametric volcano monitoring developed by INGEMMET in Peru
- **Autores:** Ramos, D.; Macedo, O.; Rivera, M.; Aguilar, R.; et al.
- **Año:** 2022
- **Link:** https://www.jvolcanica.org/ojs/index.php/volcanica/article/view/89
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** Descripción institucional del observatorio peruano OVI; Sabancaya, Misti, Ubinas, Ticsani con monitoreo multiparámetro.
- **Aplicabilidad al proyecto:** Comparable institucional a SERNAGEOMIN.

### 12.4 The scientific–community interface over the fifteen-year eruptive episode of Tungurahua Volcano, Ecuador
- **Autores:** Mothes, P. A.; Yepes, H. A.; Hall, M. L.; Ramón, P. A.; et al. (IGEPN)
- **Año:** 2015
- **DOI:** 10.1186/s13617-015-0025-y
- **Link:** https://appliedvolc.biomedcentral.com/articles/10.1186/s13617-015-0025-y
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** 15 años de gestión de Tungurahua por IGEPN, incluyendo monitoreo satelital y comunicación con comunidad.
- **Aplicabilidad al proyecto:** Modelo de comunicación de alertas SERNAGEOMIN podría tomar referencias.

### 12.5 Near real-time satellite monitoring during the 1997–2000 activity of Volcán de Colima (México) and its relationship with seismic monitoring
- **Autores:** Wright, R.; De La Cruz-Reyna, S.; Harris, A.; Flynn, L.; Gómez Martínez, J.
- **Año:** 2002
- **DOI:** 10.1016/S0377-0273(02)00238-X
- **Link:** https://www.sciencedirect.com/science/article/abs/pii/S037702730200238X
- **Idioma:** EN
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** NRT satelital (MODVOLC) + sismicidad para Colima. Trabajo seminal en NRT.
- **Aplicabilidad al proyecto:** Antecedente del concepto de alerta automatizada que Copernicus-v1 implementa.

### 12.6 An automated ash dispersion forecast system: case study Popocatépetl volcano, Mexico
- **Autores:** Reyes-Pimentel, T. A.; Espinasa-Pereña, R.; et al. (CENAPRED)
- **Año:** 2023
- **DOI:** 10.1186/s13617-023-00135-4
- **Link:** https://appliedvolc.biomedcentral.com/articles/10.1186/s13617-023-00135-4
- **Idioma:** EN
- **Open Access:** Sí
- **PDF descargado:** no
- **Resumen relevante:** Sistema operacional automatizado de pronóstico de dispersión de ceniza (108 escenarios/día) para Popocatépetl.
- **Aplicabilidad al proyecto:** Plantilla operacional para pronóstico complementario al sistema actual.

---

## 13. Reviews integradoras y contexto regional

### 13.1 The Andean Southern Volcanic Zone: a review on the legacy of the latest volcanic eruptions
- **Autores:** Romero, J. E.; Vera, F.; Polacci, M.; Morgavi, D.; Arzilli, F.; et al.
- **Año:** 2024
- **Link:** https://www.andeangeology.cl/index.php/revista1/article/view/V51n2-3681/html
- **Idioma:** EN/ES
- **Open Access:** Sí (Andean Geology)
- **PDF descargado:** parcial
- **Resumen relevante:** Revisión exhaustiva de erupciones SVZ: Chaitén 2008, Cordón Caulle 2011, Calbuco 2015, Chillán 2016+, Villarrica. Romero es chileno.
- **Aplicabilidad al proyecto:** Lectura obligatoria; cubre la mayoría de volcanes del catálogo.

### 13.2 Volcano hazards and risks in Chile (Chapter, Forecasting and Planning for Volcanic Hazards)
- **Autores:** Lara, L. E.; Orozco, G.; Amigo, A.; Silva, C.
- **Año:** 2021
- **DOI:** 10.1016/B978-0-12-818082-2.00017-2
- **Link:** https://www.sciencedirect.com/science/article/abs/pii/B9780128180822000172
- **Idioma:** EN
- **Open Access:** No
- **PDF descargado:** no
- **Resumen relevante:** Capítulo institucional SERNAGEOMIN sobre peligros volcánicos en Chile. Co-autor Luis Lara.
- **Aplicabilidad al proyecto:** Contexto de política pública y priorización oficial de los 14 más riesgosos.

### 13.3 Volcanic risk ranking and regional mapping of the Central Volcanic Zone
- **Autores:** Romero, J. E.; et al.
- **Año:** 2024
- **Link:** https://nhess.copernicus.org/preprints/nhess-2023-225/nhess-2023-225.pdf
- **Idioma:** EN
- **Open Access:** Sí (preprint NHESS)
- **PDF descargado:** no
- **Resumen relevante:** Ranking de riesgo regional CVZ; metodología extrapolable.
- **Aplicabilidad al proyecto:** Soporte cuantitativo para la categoría "14 más Riesgosos" del dashboard.

---

## Resumen estadístico

- Total referencias: **30** (objetivo era ≥20).
- Referencias específicas de volcanes chilenos: 20+.
- Referencias en español o publicadas en Andean Geology / Redalyc: 5 (Lanín, Peteroa, Chaitén volumen, SVZ review, Planchón-Peteroa 2010-2011).
- Autores chilenos identificados: Luis Lara, J. A. Naranjo, F. Aguilera, S. Layana, O. Benavente, D. Bertin, A. Amigo, J. E. Romero, F. Delgado, A. Tassara.

## PDFs descargados con éxito

- `Coppola2019_MIROVA.pdf` (10 MB)
- `Aguilera2022_Peteroa_Lakes.pdf` (5.6 MB)
- `Anantrasirichai2022_ML_Sentinel1.pdf` / `Gaddes_2022_ML_Sentinel1_Deformation.pdf` (4.4 MB)

## No se pudo descargar (paywall, scraping bloqueado o página JS)

- Marzano 2018 Calbuco (Earth-prints, descarga falló)
- Massimetti 2020 (MDPI bloquea curl directo, archivo stub 410 B)
- Valade 2019 MOUNTS (MDPI stub)
- Layana 2020 VOLCANOMS (MDPI stub)
- Marchese 2019 NHI (MDPI stub)
- Wooster & Rothery 1997 Lascar (paywall Springer)
- Glaze et al. 1989 Lascar (paywall Springer)
- Delgado 2014 Hudson (paywall Springer)
- Delgado 2016/2021 Cordón Caulle (paywall Wiley/Elsevier)
- Wendt 2022 LOFZ (paywall Elsevier)
- Astort 2022 Chillán DInSAR (paywall Elsevier)
- Aguilera 2022 Copahue SO2 (paywall Elsevier)
- Reckziegel 2022 Copahue MODIS (paywall Elsevier)
- Lara 2021 Volcano hazards Chile (paywall Elsevier)
- Caselli 2016 Copahue book chapter (paywall Springer)
- Stohl 2010 Chaitén NILU
- Coppola 2015 Ubinas (paywall Elsevier)
- Wright 2002 Colima (paywall Elsevier)
- Tassi 2025 Copahue (paywall Springer)
- Van Eaton 2016 Calbuco (USGS, link funciona pero no probé descarga directa)

**Recomendación:** Para los paywalls de Elsevier/Springer/Wiley, acceder vía VPN universitaria SERNAGEOMIN/UChile o solicitar al autor por ResearchGate. Trabajos de Luis Lara, J. Naranjo y F. Aguilera suelen estar en sus perfiles ResearchGate.

## Próximos pasos sugeridos

1. Contactar al equipo VOLCANOMS (UCN, F. Aguilera) para coordinación con Copernicus-v1.
2. Implementar algoritmo NHI Marchese 2019 sobre las series S2/L8 actuales (`change_detector.py`).
3. Evaluar ingestar Sentinel-1 al pipeline siguiendo arquitectura MOUNTS.
4. Cross-validar VRP del sistema MIROVA scrapeado con cálculo propio sobre S2 (Massimetti 2020).
5. Replicar para Hudson/Chillán/Cordón Caulle el caso pre-eruptivo InSAR + térmico de Delgado 2014.
