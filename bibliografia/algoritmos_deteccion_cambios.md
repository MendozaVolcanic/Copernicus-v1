# Detección de Cambios — Algoritmos y Métodos para Monitoreo Volcánico Satelital

Búsqueda exhaustiva orientada al sistema Copernicus-v1 (43–46 volcanes chilenos, Sentinel-2 + Landsat 8/9). Las referencias están organizadas por categoría algorítmica. Los PDFs descargados se guardan en `bibliografia/pdfs/`.

---

## A. Algoritmos térmicos específicos para volcanes

### 1. Volcanic Hot-Spot Detection Using SENTINEL-2 — vs MODIS-MIROVA
- **Autores:** Massimetti F., Coppola D., Laiolo M., Valade S., Cigolini C., Ripepe M.
- **Año:** 2020 · **Journal:** Remote Sensing 12(5), 820
- **DOI:** 10.3390/rs12050820 · OA: Sí · PDF: pendiente manual
- **Aplicabilidad:** Paper fundacional para detección térmica con S2 — adoptar sus umbrales α/β y clusters como benchmark.

### 2. Multi-Channel Algorithm for Volcanic Thermal Anomalies (NHI)
- **Autores:** Marchese F., Genzano N., Neri M., Falconieri A., Mazzeo G., Pergola N.
- **Año:** 2019 · **Journal:** Remote Sensing 11(23), 2876
- **DOI:** 10.3390/rs11232876 · OA: Sí
- **Aplicabilidad:** CRÍTICO. Define NHI_SWIR=(B12−B11)/(B12+B11) y NHI_SWNIR. Resuelve homogeneidad multi-sensor S2/L8/L9 con un solo umbral. Trivial de computar con bandas ya descargadas.

### 3. Global volcano monitoring through NHI system
- **Autores:** Marchese F., Genzano N. · **Año:** 2023
- **Journal:** Journal of the Geological Society 180(1)
- **DOI:** 10.1144/jgs2022-014 · OA: Parcial (preprint ResearchGate)
- **Aplicabilidad:** Sistema en Google Earth Engine, 15% falsos positivos. Modelo arquitectónico para series temporales de #hot_pixels.

### 4. NHI sobre infrared ASTER
- **Autores:** Genzano N., Marchese F., Plank S., Pergola N. · **Año:** 2021
- **Journal:** Sensors 21(4), 1538 · **DOI:** 10.3390/s21041538 · OA: Sí

### 5. MOUNTS Monitoring System (multi-sensor + AI)
- **Autores:** Valade S. et al. · **Año:** 2019
- **Journal:** Remote Sensing 11(13), 1528 · **DOI:** 10.3390/rs11131528 · OA: Sí
- **Aplicabilidad:** Modelo arquitectónico DIRECTO. Fusiona S1 (deformación) + S2 SWIR + S5P SO2 con CNN.

### 6. MODVOLC: Near-real-time thermal monitoring
- **Autores:** Wright R., Flynn L.P., Garbeil H., Harris A.J.L., Pilger E. · **Año:** 2004
- **Journal:** JVGR 135, 29–49 · **DOI:** 10.1016/j.jvolgeores.2003.12.008
- **PDF:** ✅ `pdfs/Wright_2004_MODVOLC.pdf` (2.6 MB)
- **Aplicabilidad:** Padre conceptual del NHI. NTI=(B22−B21)/(B22+B21).

### 7. MIROVA — Enhanced volcanic hot-spot detection
- **Autores:** Coppola D., Laiolo M., Cigolini C., Donne D.D., Ripepe M. · **Año:** 2016
- **Journal:** Geol Soc Special Pub 426 · **DOI:** 10.1144/SP426.5
- **PDF:** ✅ `pdfs/Coppola2019_MIROVA.pdf` (10 MB)
- **Aplicabilidad:** ESENCIAL. Define VRP = 18.9 × Apix × DLMIR. Implementar en Copernicus-v1 para tener métrica cuantitativa en Watts.

### 8. MODIS → VIIRS transition for global volcano thermal monitoring
- **Autores:** Coppola D. et al. · **Año:** 2022
- **Journal:** Sensors 22(5), 1713 · **DOI:** 10.3390/s22051713 · OA: Sí

### 9. TIRVolcH: Thermal IR Recognition of Volcanic Hotspots
- **Autores:** Silvestri M., Marotta E., Buongiorno M.F. et al. · **Año:** 2024
- **Journal:** Remote Sensing of Environment · **DOI:** 10.1016/j.rse.2024.114388
- **Aplicabilidad:** Complemento ideal a NHI para anomalías difusas (fumarolas, lagos calientes) en banda térmica Landsat B10.

---

## B. Métodos clásicos: differencing, ratioing, CVA, PCA

### 10. Singh A. — Digital change detection techniques (review fundacional)
- **Año:** 1989 · **IJRS** 10(6) · **DOI:** 10.1080/01431168908903939
- **Citas:** >5000

### 11. Fung & LeDrew — PCA Change Detection
- **Año:** 1987 · **PE&RS** 53(12), 1649–1658
- **Aplicabilidad:** PCA sobre stack histórico revela anomalías que Z-score por banda pierde.

### 12. Nackaerts et al. — TC-CVA categorise land cover change
- **Año:** 2005 · **IJRS**

### 13. Bovolo & Bruzzone — Algebraic vs ML benchmark
- **Año:** 2022 · **Electronics MDPI** 11(3), 431 · **DOI:** 10.3390/electronics11030431

---

## C. Time series analysis (BFAST, CCDC, LandTrendr)

### 14. LandTrendr
- **Autores:** Kennedy R.E., Yang Z., Cohen W.B. · **Año:** 2010
- **Journal:** RSE 114(12) · **DOI:** 10.1016/j.rse.2010.07.008
- **Aplicabilidad:** Series NDVI/NBR de cráteres → detectar destrucción vegetal por flujos.

### 15. BFAST
- **Autores:** Verbesselt J., Hyndman R., Newnham G., Culvenor D. · **Año:** 2010
- **Journal:** RSE 114(1) · **DOI:** 10.1016/j.rse.2009.08.014
- **Aplicabilidad:** Aplicar a series VRP o #hot_pixels para detectar transiciones de régimen.

### 16. CCDC — Continuous Change Detection
- **Autores:** Zhu Z., Woodcock C.E. · **Año:** 2014
- **Journal:** RSE 144 · **DOI:** 10.1016/j.rse.2014.01.011
- **Aplicabilidad:** ALINEADO con regla "consistencia temporal multi-frame" del proyecto. Modelo armónico + 3 obs consecutivas.

### 17. LandTrendr/CCDC/BFAST comparative assessment
- **Año:** 2025 · **Remote Sensing** 17(14), 2402

---

## D. Deep Learning aplicado a volcanes

### 18. ML para deformación volcánica en Sentinel-1
- **Autores:** Gaddes M.E., Hooper A., Albino F., Biggs J. · **Año:** 2022
- **Journal:** Bulletin of Volcanology 84(11), 100 · **DOI:** 10.1007/s00445-022-01608-x
- **PDF:** ✅ `pdfs/Gaddes_2022_ML_Sentinel1_Deformation.pdf` (4.4 MB)

### 19. Deep Learning para anomalías térmicas sutiles ASTER
- **Autores:** Murphy S.W., Wright R. et al. · **Año:** 2023
- **Journal:** IEEE TGRS · **DOI:** 10.1109/TGRS.2023.3236365

### 20. BIT — Bi-temporal Image Transformer
- **Autores:** Chen H., Qi Z., Shi Z. · **Año:** 2021
- **Journal:** IEEE TGRS · arXiv: 2103.00208
- **PDF:** ✅ `pdfs/Chen_2021_BIT_Transformer.pdf` (6.4 MB)
- **Aplicabilidad:** Estado del arte. Primera arquitectura a probar si Copernicus-v1 escala a deep learning.

### 21. Anomaly detection for volcanic unrest (autoencoders)
- **Autores:** Anantrasirichai N., Albino F. · **Año:** 2024
- **Repo:** ESS Open Archive · OA: Sí
- **PDF:** ✅ `pdfs/Anantrasirichai2022_ML_Sentinel1.pdf` (4.4 MB)

### 22. Siamese U-Net for Change Detection
- **Autores:** Kang J., Liu L. · **Año:** 2022
- **Journal:** IEEE JSTARS · **DOI:** 10.1109/JSTARS.2022.3162422

### 23. Land surface change after major volcanic eruptions in Indonesia (ML)
- **Año:** 2025 · **JAG** · **DOI:** 10.1016/j.jag.2025.06.012
- **Aplicabilidad:** Transferibilidad espacio-temporal entre volcanes — exactamente el problema de Copernicus-v1.

---

## E. Object-Based Image Analysis (OBIA)

### 24. Hossain & Chen — OBIA Segmentation review
- **Año:** 2019 · **ISPRS** 150 · **DOI:** 10.1016/j.isprsjprs.2019.02.009

### 25. OBIA for Lava Flow Morphology
- **Autores:** Aufaristama M. · **Año:** 2019 · **IJRS**
- **Aplicabilidad:** Llaima, Villarrica, Lonquimay — flujos recientes en lista del proyecto.

### 26. Lava Flow Mapping con S1 SAR + OBIA — Fagradalsfjall
- **Año:** 2023 · 79–93% accuracy

### 27. GEOBIA + CNN para landforms volcánicos/glaciares
- **Año:** 2022 · PMC9741658

---

## F. Anomaly detection estadístico (Mahalanobis)

### 28. LSMAD — Mahalanobis robusto para anomaly detection hyperspectral
- **Autores:** Zhang Y., Du B., Zhang L., Wang S. · **Año:** 2016
- **Journal:** IEEE TGRS 54(3) · **DOI:** 10.1109/TGRS.2015.2479299
- **Aplicabilidad:** Mejora directa al Z-score actual. `scipy.spatial.distance.mahalanobis`.

### 29. Hyperspectral anomaly detection benchmark
- **Año:** 2022 · **IJDE** · **DOI:** 10.1080/17538947.2022.2146770

### 30. Why Mahalanobis is Effective for Anomaly Detection
- **Año:** 2020 · arXiv: 2003.00402

---

## G. Cambios morfológicos (DEM differencing)

### 31. Shishaldin crater morphology (SAR amplitude)
- **Autores:** Wang T., Poland M.P. (USGS) · **Año:** 2023
- **Bulletin Volcanology** · **DOI:** 10.1007/s00445-023-01670-z

### 32. Telica Volcano crater morphology
- **Autores:** Hanagan C., Roman D.C. · **Año:** 2020
- **G3** · **DOI:** 10.1029/2019GC008889 · OA: Sí

### 33. Steep Slope Volcanoes Multi-Platform (Walter et al.)
- **Año:** 2020 · **Remote Sensing** 12(3), 438 · **DOI:** 10.3390/rs12030438

### 34. Oldoinyo Lengai SfM photogrammetry
- **Año:** 2023 · **JVGR** · **DOI:** 10.1016/j.jvolgeores.2023.107865

---

## H. Reviews y benchmarks generales

### 35. Remote Sensing of Volcanic Processes and Risk (special issue)
- **Editores:** Pyle D.M., Mather T.A., Biggs J. · **Año:** 2020
- **Remote Sensing** 12(16), 2567 · **DOI:** 10.3390/rs12162567

### 36. Indonesian volcanoes 2000–2020 ASTER
- **Autores:** Reath K., Pritchard M., Wright R. · **Año:** 2022
- **JVGR** · **DOI:** 10.1016/j.jvolgeores.2022.107627

### 37. Liu Y. — High-temperature anomalies S2 MSI
- **Año:** 2021 · **ISPRS** 177 · **DOI:** 10.1016/j.isprsjprs.2021.05.008

### 38. Wright R. (2016) — Algorithms Review for Hot Spot Detection
- **PDF:** ✅ `pdfs/Wright_2016_AlgorithmsReview_HotSpots.pdf` (377 KB)

### 39. Murphy et al. (2016) — Daytime detection algorithm S2
- **JVGR** · **DOI:** 10.1016/j.jvolgeores.2016.08.004

### 40. Coppola et al. (2023) — Global Radiant Flux MIROVA
- **PDF:** ✅ `pdfs/Coppola_2023_GlobalRadiantFlux_MIROVA.pdf` (5.1 MB)

---

## Recomendaciones priorizadas para Copernicus-v1

1. **Implementar NHI** (refs 2, 3) como detector primario homogéneo S2/L8/L9
2. **Calcular VRP** (ref 7) por anomalía → métrica cuantitativa en Watts comparable con MIROVA mundial
3. **Reemplazar Z-score → Mahalanobis** (refs 28, 30) sobre vector de bandas
4. **Adoptar CCDC harmonic baseline** (ref 16) que formaliza la "consistencia multi-frame"
5. **Para fase DL:** BIT (ref 20) o Siamese U-Net (ref 22) sobre par (mediana histórica, imagen actual)
6. **TIRVolcH** (ref 9) en composite THERMAL Landsat para anomalías difusas
