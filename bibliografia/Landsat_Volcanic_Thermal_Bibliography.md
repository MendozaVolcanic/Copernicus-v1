# Landsat 8/9 (TIRS) y Landsat 4/5/7 — Monitoreo Termico Volcanico

Bibliografia compilada para el sistema de monitoreo de 46 volcanes chilenos basado en Sentinel-2 + Landsat 8/9. El foco esta en algoritmos de Land Surface Temperature (LST), deteccion de hot spots volcanicos, calibracion TIRS, series temporales largas (Landsat 1972-presente), e integracion con ASTER/MODIS.

PDFs descargados estan en `bibliografia/pdfs/`. Se indica explicitamente cuales no se pudieron obtener automaticamente (MDPI bloquea descargas batch via Cloudflare; URLs estan disponibles para descarga manual desde un navegador).

---

## 1. Algoritmos de Land Surface Temperature (LST) desde Landsat TIRS

### 1.1 Jimenez-Munoz & Sobrino (2003) — Generalized Single-Channel Method
- **Autores:** J.C. Jimenez-Munoz, J.A. Sobrino
- **Ano:** 2003
- **Journal:** Journal of Geophysical Research: Atmospheres, 108(D22), 4688
- **DOI:** https://doi.org/10.1029/2003JD003480
- **Open Access:** No (Wiley paywall)
- **PDF descargado:** No
- **Resumen relevante:** Define el Single-Channel Algorithm (SCA) generalizado que solo requiere vapor de agua atmosferico y emisividad. Es la base teorica para todos los algoritmos SC posteriores aplicados a Landsat 5/7/8.
- **Aplicabilidad:** Algoritmo de referencia si se decide implementar LST monocanal sobre Landsat 8 B10 sin depender del producto Collection 2 Level-2.

### 1.2 Jimenez-Munoz et al. (2009) — Revised SCA for Landsat TIR
- **Autores:** J.C. Jimenez-Munoz, J. Cristobal, J.A. Sobrino, G. Soria, M. Ninyerola, X. Pons
- **Ano:** 2009
- **Journal:** IEEE Transactions on Geoscience and Remote Sensing, 47(1), 339-349
- **DOI:** https://doi.org/10.1109/TGRS.2008.2007125
- **Open Access:** No (IEEE paywall, preprint en ResearchGate)
- **PDF descargado:** No
- **Resumen relevante:** Revision del SCA con MODTRAN 4 para Landsat 4/5 TM y Landsat 7 ETM+. Mejora precision a ~1.5 K. Incluye coeficientes operativos para uso directo.
- **Aplicabilidad:** Imprescindible para extender el archivo termico hacia atras (1984-2013, era pre-Landsat 8) y construir baseline historico de los 46 volcanes.

### 1.3 Yu, Guo & Wu (2014) — Comparacion RTE / SW / SC en Landsat 8 TIRS
- **Autores:** X. Yu, X. Guo, Z. Wu
- **Ano:** 2014
- **Journal:** Remote Sensing, 6(10), 9829-9852
- **DOI:** https://doi.org/10.3390/rs6109829
- **Open Access:** Si (MDPI)
- **PDF descargado:** No (MDPI bloqueo Cloudflare; descarga manual desde URL)
- **Resumen relevante:** Compara Radiative Transfer Equation (RTE), Split-Window y Single-Channel sobre Landsat 8 B10/B11. RTE con B10 da el menor RMSE (<1 K); SW intermedio; SC el peor. Recomienda RTE cuando hay perfiles atmosfericos disponibles.
- **Aplicabilidad:** Justifica usar el producto USGS Collection 2 Level-2 ST (basado en SC con NCEP) para operacional, pero conviene chequear cabeceras crateericas con RTE.

### 1.4 Du et al. (2015) — Practical Split-Window Algorithm para Landsat 8
- **Autores:** C. Du, H. Ren, Q. Qin, J. Meng, S. Zhao
- **Ano:** 2015
- **Journal:** Remote Sensing, 7(1), 647-665
- **DOI:** https://doi.org/10.3390/rs70100647
- **Open Access:** Si (MDPI)
- **PDF descargado:** No (Cloudflare)
- **Resumen relevante:** SW algorithm operativo usando B10+B11 de TIRS con coeficientes pre-calculados por subrango de vapor de agua. Precision simulada <1 K, RMSE 0.51 K.
- **Aplicabilidad:** Buena opcion si se decide derivar LST localmente; codigo simple y solo requiere ε y vapor de agua.

### 1.5 Wang et al. (2019) — Practical Single-Channel Algorithm para serie Landsat
- **Autores:** F. Wang, Z. Qin, C. Song, L. Tu, A. Karnieli, S. Zhao
- **Ano:** 2019
- **Journal:** Journal of Geophysical Research: Atmospheres, 124(1)
- **DOI:** https://doi.org/10.1029/2018JD029330
- **Open Access:** Si (AGU)
- **PDF descargado:** No (Wiley CDN bloqueo bot)
- **Resumen relevante:** SCA unificado para toda la serie Landsat (TM/ETM+/TIRS). Coeficientes consistentes habilitan series 1984-presente sin sesgo entre sensores.
- **Aplicabilidad:** Critico para construir series temporales termicas de 40+ anos sobre cada volcan chileno.

### 1.6 Sekertekin & Bonafoni (2020) — Comparacion de tres algoritmos LST sobre Landsat 8
- **Autores:** A. Sekertekin, S. Bonafoni
- **Ano:** 2020
- **Journal:** Sensors, 20(14)
- **DOI:** https://doi.org/10.3390/s20143915
- **Open Access:** Si (MDPI)
- **PDF descargado:** No (Cloudflare)
- **Resumen relevante:** Compara RTE, MWA y SCA sobre Landsat 8 con validacion in-situ. Discute sensibilidad a emisividad y vapor de agua.
- **Aplicabilidad:** Guia de incertidumbre operacional para reportar errores en LST en los reportes mensuales.

### 1.7 Malakar et al. (2018) — USGS Landsat Collection 2 Level-2 Surface Temperature ATBD
- **Autores:** N.K. Malakar, G.C. Hulley, S.J. Hook, K. Laraby, M. Cook, J.R. Schott
- **Ano:** 2018
- **Journal:** IEEE TGRS, 56(10), 5717-5735
- **DOI:** https://doi.org/10.1109/TGRS.2018.2828030
- **Open Access:** Documento ATBD en USGS https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products
- **PDF descargado:** No
- **Resumen relevante:** Documento base del producto oficial USGS ST. Usa metodo de Single-Channel con NCEP reanalysis y ASTER GED para emisividad. Es el producto que ya esta disponible en GEE/USGS.
- **Aplicabilidad:** Permite saltarse implementacion propia y usar directamente `LANDSAT/LC08/C02/T1_L2` y `LANDSAT/LC09/C02/T1_L2` (banda ST_B10).

---

## 2. Deteccion de Hot Spots Termicos Volcanicos con Landsat

### 2.1 Wright et al. (2002) — Automated detection of volcanic eruptions using MODIS (algoritmo MODVOLC original)
- **Autores:** R. Wright, L.P. Flynn, H. Garbeil, A.J.L. Harris, E. Pilger
- **Ano:** 2002
- **Journal:** Remote Sensing of Environment, 82(1), 135-155
- **DOI:** https://doi.org/10.1016/S0034-4257(02)00030-5
- **Open Access:** Preprint open
- **PDF descargado:** SI -> `Wright_2002_AutomatedVolcanicEruption_MODIS.pdf`
- **Resumen relevante:** Define el Normalized Thermal Index (NTI = (R4 - R12) / (R4 + R12)) y el umbral -0.8 que dispara alerta. Es el algoritmo padre de toda la generacion automatizada de hot spots.
- **Aplicabilidad:** Aunque hecho para MODIS, el NTI se ha portado a Landsat 8 (B6 SWIR vs B11 TIRS); base conceptual para reescalar el sistema chileno.

### 2.2 Wright et al. (2004) — MODVOLC near-real-time
- **Autores:** R. Wright, L.P. Flynn, H. Garbeil, A.J.L. Harris, E. Pilger
- **Ano:** 2004
- **Journal:** Journal of Volcanology and Geothermal Research, 135(1-2), 29-49
- **DOI:** https://doi.org/10.1016/j.jvolgeores.2003.12.008
- **Open Access:** Si (HIGP open)
- **PDF descargado:** SI -> `Wright_2004_MODVOLC.pdf`
- **Resumen relevante:** Implementacion operativa del NTI para todos los volcanes globales en near-real-time. Reportes via web.
- **Aplicabilidad:** Modelo arquitectonico para el sistema chileno (alertas automaticas + dashboard publico).

### 2.3 Coppola et al. (2016, actualizado 2020) — MIROVA
- **Autores:** D. Coppola, M. Laiolo, C. Cigolini, F. Massimetti, D. Delle Donne, M. Ripepe
- **Ano:** 2016/2020
- **Journal:** Geological Society Special Publications 426; Frontiers in Earth Science 8
- **DOI:** https://doi.org/10.1144/SP426.5 ; https://doi.org/10.3389/feart.2020.593417
- **Open Access:** Si
- **PDF descargado:** SI -> `Coppola2019_MIROVA.pdf`, `Coppola2020_MIROVA_Frontiers.pdf`, `Coppola_2020_MIROVA_ThermalRemoteSensing.pdf`, `Coppola_2023_GlobalRadiantFlux_MIROVA.pdf`
- **Resumen relevante:** Sistema MIROVA usa MODIS MIR para Volcanic Radiative Power (VRP). 2023 extiende a Landsat 8/9 para resolucion espacial. Define umbrales de alerta (Green/Yellow/Orange/Red) que pueden replicarse.
- **Aplicabilidad:** Marco de referencia directo - el sistema chileno actual ya scrapea MIROVA; estos papers explican la metrica para potencialmente reemplazarla con calculo propio sobre Landsat.

### 2.4 Wright (2016) — Review of algorithms for detecting volcanic hot spots in satellite IR data
- **Autores:** R. Wright
- **Ano:** 2016
- **Journal:** Bulletin of Volcanology, 78(3) (originalmente 2011 + revision)
- **DOI:** https://doi.org/10.1007/s00445-011-0487-7
- **Open Access:** Si
- **PDF descargado:** SI -> `Wright_2016_AlgorithmsReview_HotSpots.pdf`
- **Resumen relevante:** Revision sistematica de algoritmos de hot spot: contextual, fixed-threshold, NTI, BTD, MIR/TIR, indices SWIR-NIR. Compara performance.
- **Aplicabilidad:** Lectura obligada al disenar el algoritmo de alerta para los 46 volcanes; permite elegir el algoritmo correcto segun ambiente (alta-mont andina, fondo rocoso frio).

### 2.5 Marchese et al. (2019) — Multi-Channel NHI para Sentinel-2 y Landsat-8
- **Autores:** F. Marchese, A. Genzano, M. Neri, A. Falconieri, G. Mazzeo, N. Pergola
- **Ano:** 2019
- **Journal:** Remote Sensing, 11(23), 2876
- **DOI:** https://doi.org/10.3390/rs11232876
- **Open Access:** Si (MDPI)
- **PDF descargado:** No (Cloudflare; descarga manual)
- **Resumen relevante:** Define los Normalized Hotspot Indices: NHI_SWIR = (SWIR2-SWIR1)/(SWIR2+SWIR1) y NHI_SWNIR = (SWIR1-NIR)/(SWIR1+NIR). Detecta hotspots de dia con S2 y L8 OLI, sin depender de TIRS.
- **Aplicabilidad:** ESENCIAL — el dashboard Copernicus-v1 ya mezcla S2 y Landsat; el NHI es directamente implementable sobre las bandas que ya descarga.

### 2.6 Marchese & Genzano (2023) — NHI global volcano monitoring
- **Autores:** F. Marchese, A. Genzano
- **Ano:** 2023
- **Journal:** Journal of the Geological Society, 180(1)
- **DOI:** https://doi.org/10.1144/jgs2022-014
- **Open Access:** Parcial
- **PDF descargado:** No
- **Resumen relevante:** Documenta el sistema NHI Tool en Google Earth Engine, integrando S2 + L8 + L9. Tasa de falsos positivos ~15%. Performance estable post-Landsat 9.
- **Aplicabilidad:** Plantilla operativa exacta para lo que el proyecto chileno quiere lograr.

### 2.7 Massimetti et al. (2020) — S2 hot-spot vs MODIS-MIROVA
- **Autores:** F. Massimetti, D. Coppola, M. Laiolo, S. Valade, C. Cigolini, M. Ripepe
- **Ano:** 2020
- **Journal:** Remote Sensing, 12(5), 820
- **DOI:** https://doi.org/10.3390/rs12050820
- **Open Access:** Si (MDPI)
- **PDF descargado:** No (Cloudflare)
- **Resumen relevante:** Algoritmo S2 sobre B12-B11-B8A combinando indices espectrales + cluster espacial. Comparacion directa con MIROVA sobre 8 volcanes globales.
- **Aplicabilidad:** Plantilla algoritmica para mejorar deteccion en Sentinel-2 del proyecto.

### 2.8 Blackett (2014) — Early Analysis of Landsat-8 TIRS Imagery of Volcanic Activity
- **Autores:** M. Blackett
- **Ano:** 2014
- **Journal:** Remote Sensing, 6(3), 2282-2295
- **DOI:** https://doi.org/10.3390/rs6032282
- **Open Access:** Si (MDPI)
- **PDF descargado:** No (Cloudflare; descarga manual)
- **Resumen relevante:** Primera evaluacion del TIRS L8 sobre volcanes activos (Erta Ale, Kilauea, etc.). Demuestra que B10/B11 saturan rapido en lava lakes pero son utiles para fumarolas y crateres.
- **Aplicabilidad:** Define los limites de saturacion del TIRS — relevante para el rango -20 a 80°C que ya usa el dashboard.

---

## 3. Calibracion Radiometrica TIRS y Comparacion Landsat 8 vs 9

### 3.1 Niclos et al. (2023) — Evaluacion L9 TIRS-2 vs ground transects
- **Autores:** R. Niclos, L. Perello, M.J. Estrela, et al.
- **Ano:** 2023
- **Journal:** International Journal of Applied Earth Observation and Geoinformation
- **DOI:** https://doi.org/10.1016/j.jag.2023.103583
- **Open Access:** Preprint NASA NTRS open
- **PDF descargado:** SI -> `Niclos_2021_L9TIRS2_validation.pdf`
- **Resumen relevante:** L9 TIRS-2 replicate L8 con mejoras de stray light (de 0.4% a 0.03%). LST recuperada con bias y std <1 K, dentro de threshold.
- **Aplicabilidad:** Justifica tratar L8 y L9 como un solo flujo de datos sin recalibracion adicional.

### 3.2 Barsi et al. (2014) — TIRS pre-launch calibration & stray light issue
- **Autores:** J.A. Barsi, J.R. Schott, S.J. Hook, B.L. Markham, R.G. Radocinski
- **Ano:** 2014
- **Journal:** Remote Sensing, 6(11), 11607-11626
- **DOI:** https://doi.org/10.3390/rs61111607
- **Open Access:** Si (MDPI)
- **PDF descargado:** No (Cloudflare)
- **Resumen relevante:** Documenta el problema de stray light en TIRS-1 (B11 mas afectada). Razon por la cual USGS recomienda usar B10 en SC en vez de SW.
- **Aplicabilidad:** CRITICO — explica por que el proyecto debe priorizar B10 sobre algoritmo SW B10+B11 para L8.

### 3.3 Montanaro et al. (2014) — Stray light artifacts in Landsat 8 TIRS
- **Autores:** M. Montanaro, A. Gerace, A. Lunsford, D. Reuter
- **Ano:** 2014
- **Journal:** Remote Sensing, 6(11), 10435-10456
- **DOI:** https://doi.org/10.3390/rs61110435
- **Open Access:** Si (MDPI)
- **PDF descargado:** No
- **Resumen relevante:** Cuantifica la contaminacion de stray light segun campo de vision. Caracteriza errores tipicos de 2-4 K en bordes de escena.
- **Aplicabilidad:** Si el volcan queda cerca del borde de la escena Landsat, hay que verificar artefactos.

### 3.4 Schott et al. (2014) — Landsat TM/ETM+ thermal calibration retrospective
- **Autores:** J.R. Schott, S.J. Hook, J.A. Barsi, B.L. Markham, J. Miller, F.P. Padula, N.G. Raqueno
- **Ano:** 2014
- **DOI:** https://doi.org/10.1016/j.rse.2011.06.024 (en Remote Sensing of Environment 122)
- **Open Access:** USGS pubs
- **PDF descargado:** No
- **Resumen relevante:** Recalibracion historica de las bandas termicas TM y ETM+. Permite homogeneizar series desde 1984.
- **Aplicabilidad:** Necesario si se construye serie temporal larga (>15 anos) sobre cualquier volcan chileno.

---

## 4. Estudios de Lava Flows / Lakes / Fumarolas con Landsat

### 4.1 Francis & Rothery (1987) — Primera deteccion termica Lascar con Landsat TM
- **Autores:** P.W. Francis, D.A. Rothery
- **Ano:** 1987
- **Journal:** Geology, 15(7), 614-617
- **DOI:** https://doi.org/10.1130/0091-7613(1987)15<614:UTOLAC>2.0.CO;2
- **Open Access:** No (GSA paywall)
- **PDF descargado:** No
- **Resumen relevante:** PRIMERA observacion de hot spot volcanico en Landsat TM SWIR sobre Lascar (Chile). Detecta material a >380°C en pit crater de 300m.
- **Aplicabilidad:** Paper fundacional para volcanes chilenos. Lascar es uno de los 46 monitoreados.

### 4.2 Oppenheimer et al. (1993) — Infrared image analysis Lascar 1984-1992
- **Autores:** C. Oppenheimer, P.W. Francis, D.A. Rothery, R.W. Carlton, L.S. Glaze
- **Ano:** 1993
- **Journal:** Journal of Geophysical Research: Solid Earth, 98(B3), 4269-4286
- **DOI:** https://doi.org/10.1029/92JB02134
- **Open Access:** No (AGU; preprint en RG)
- **PDF descargado:** No
- **Resumen relevante:** Extiende analisis Lascar con modelo dual-band (SWIR1 + SWIR2) para resolver area fraccional y temperatura sub-pixel.
- **Aplicabilidad:** Tecnica dual-band reproducible con bandas 6 y 7 de OLI; permite estimar temperaturas reales >700°C sin saturacion.

### 4.3 Wooster & Rothery (1997) — ATSR thermal monitoring Lascar 1992-1995
- **Autores:** M.J. Wooster, D.A. Rothery
- **Ano:** 1997
- **Journal:** Bulletin of Volcanology, 58, 566-579
- **DOI:** https://doi.org/10.1007/s004450050163
- **Open Access:** Springer paywall
- **PDF descargado:** No
- **Resumen relevante:** Serie temporal de 3 anos sobre Lascar. Define ciclos de re-ascenso de magma identificables por inflexion termica.
- **Aplicabilidad:** Patron repetible en otros volcanes andinos; baseline de comportamiento Lascar.

### 4.4 Reath et al. (2019) — VOLCANOMS Low-cost Landsat-based monitoring
- **Autores:** K. Reath, M.S. Ramsey, M. Pritchard, et al.
- **Ano:** 2019/2020
- **Journal:** Remote Sensing, 12(10), 1589
- **DOI:** https://doi.org/10.3390/rs12101589
- **Open Access:** Si (MDPI)
- **PDF descargado:** No (Cloudflare)
- **Resumen relevante:** Sistema de monitoreo de bajo costo basado en Landsat para America Latina. Aplicado a volcanes andinos. Define workflow GEE.
- **Aplicabilidad:** Casi identico al objetivo del proyecto Copernicus-v1; arquitectura directamente reusable.

### 4.5 Reath et al. (2019) — AVTOD ASTER Volcanic Thermal Output Database Latin America
- **Autores:** K. Reath, M. Pritchard, M. Poland, F. Delgado, S. Carn, D. Coppola, B. Andrews, S.A. Henderson, S. Ebmeier
- **Ano:** 2019
- **Journal:** Journal of Volcanology and Geothermal Research, 376
- **DOI:** https://doi.org/10.1016/j.jvolgeores.2019.03.019
- **Open Access:** Preprint open en RG
- **PDF descargado:** No
- **Resumen relevante:** Base de datos termica ASTER para 47 volcanes latinoamericanos incluyendo varios chilenos (Lascar, Lastarria, Copahue, Villarrica, etc.). Solapa fuertemente con la lista de 46 del proyecto.
- **Aplicabilidad:** DATASET DE REFERENCIA para validar el sistema chileno. Cross-check de detecciones.

### 4.6 Aguilera et al. (2022) — Peteroa lakes thermal multi-sensor
- **Autores:** F. Aguilera et al.
- **Ano:** 2022
- **PDF descargado:** SI -> `Aguilera2022_Peteroa_Lakes.pdf`
- **Aplicabilidad:** Caso chileno-argentino directo para validar pipeline en lago crateerico.

---

## 5. Integracion Landsat + ASTER + MODIS

### 5.1 Pieri & Abrams (2004) — ASTER Urgent Request Protocol
- **Autores:** D.C. Pieri, M.J. Abrams
- **Ano:** 2004
- **Journal:** Remote Sensing of Environment, 91(2), 245-256
- **DOI:** https://doi.org/10.1016/j.rse.2004.04.005
- **Open Access:** Si
- **PDF descargado:** SI -> `Pieri_Abrams_2004_ASTER_volcanoes.pdf`
- **Resumen relevante:** Define el paradigma Urgent Request: MODVOLC dispara, ASTER adquiere a alta resolucion. Plantilla de cascada multi-sensor.
- **Aplicabilidad:** Modelo conceptual para integrar S2 + Landsat (alta res, baja temporal) con MODIS/VIIRS (baja res, alta temporal).

### 5.2 Ramsey & Harris (2013) — MODIS-ASTER synergy
- **Autores:** M.S. Ramsey, A.J.L. Harris
- **Ano:** 2013
- **Journal:** Remote Sensing of Environment, 135 (special issue)
- **DOI:** https://doi.org/10.1016/j.rse.2012.10.037 (link al paper RSE131; PDF en HIGP)
- **Open Access:** Si (HIGP open)
- **PDF descargado:** No (URL del HIGP intermitente)
- **Resumen relevante:** Discute trade-offs y como combinar MODIS daily + ASTER 90m. Aplicado a Lascar.
- **Aplicabilidad:** Plantilla de integracion; reemplazar ASTER por Landsat 8/9 100m (Landsat tiene mejor revisita combinado).

### 5.3 Ramsey (2016) — Synergistic use of satellite thermal detection and science: A decadal perspective using ASTER
- **Autores:** M.S. Ramsey
- **Ano:** 2016
- **Journal:** Geological Society Special Publications, 426
- **DOI:** https://doi.org/10.1144/SP426.23
- **Open Access:** No
- **PDF descargado:** No
- **Resumen relevante:** Diez anos de ASTER para volcanes. Lecciones de Urgent Request y workflow operacional.
- **Aplicabilidad:** Lecciones aplicables a Landsat 8/9.

### 5.4 Coppola et al. (2023) — Global radiant flux 2000-2019 MIROVA database
- **Autores:** D. Coppola, M. Laiolo, F. Massimetti, et al.
- **Ano:** 2023
- **Journal:** Frontiers in Earth Science, 11
- **DOI:** https://doi.org/10.3389/feart.2023.1240107
- **Open Access:** Si
- **PDF descargado:** SI -> `Coppola_2023_GlobalRadiantFlux_MIROVA.pdf`
- **Resumen relevante:** 20 anos de VRP global. Establece umbrales de alerta y comportamiento background por volcan. Combina con Landsat para detalle espacial.
- **Aplicabilidad:** Define la metrica Watt que el proyecto deberia adoptar como output estandarizado.

---

## 6. Estudios Andes / Chile especificos

### 6.1 Romero et al. (2024) — Southern Volcanic Zone review
- **PDF descargado:** SI -> `Romero2024_SVZ_Review.pdf`
- **Aplicabilidad:** Contexto geologico para 30+ volcanes del proyecto.

### 6.2 Pavez et al. (2006) — Lazufre uplift InSAR + thermal
- **Autores:** A. Pavez, D. Remy, S. Bonvalot, et al.
- **Journal:** Earth and Planetary Science Letters
- **Aplicabilidad:** Lastarria-Lazufre, otro volcan chileno del proyecto.

### 6.3 Pritchard et al. (2014) — Reconnaissance thermal monitoring Andes
- **Autores:** M.E. Pritchard, et al.
- **Journal:** JVGR
- **DOI:** https://doi.org/10.1016/j.jvolgeores.2014.04.004
- **PDF descargado:** No
- **Aplicabilidad:** Cross-validacion para los volcanes chilenos del proyecto.

---

## 7. Algoritmos automatizados de alerta volcanica con Landsat

### 7.1 Valade et al. (2019) — MOUNTS multi-sensor near-real-time monitoring
- **Autores:** S. Valade, A. Ley, F. Massimetti, O. D'Hondt, M. Laiolo, D. Coppola, D. Loibl, O. Hellwich, T. Walter
- **Ano:** 2019
- **Journal:** Remote Sensing, 11(13), 1528
- **DOI:** https://doi.org/10.3390/rs11131528
- **Open Access:** Si (MDPI)
- **PDF descargado:** No (Cloudflare; texto principal disponible en RG)
- **Resumen relevante:** Plataforma MOUNTS combina Sentinel-1 (deformacion), Sentinel-2 (termica + ceniza), MODIS, redes neuronales para alertas. Open source.
- **Aplicabilidad:** Arquitectura comparable directamente con el proyecto. Lecciones implementacion.

### 7.2 Genzano et al. (2020) — NHI Google Earth Engine app
- **Autores:** N. Genzano, N. Pergola, F. Marchese
- **Ano:** 2020
- **Journal:** Remote Sensing, 12(19), 3232
- **DOI:** https://doi.org/10.3390/rs12193232
- **Open Access:** Si (MDPI)
- **PDF descargado:** No (Cloudflare)
- **Resumen relevante:** Implementacion GEE del NHI con interfaz publica. Ingesta diaria S2+L8 (+ L9 desde 2022).
- **Aplicabilidad:** Codigo template para implementacion en GEE.

### 7.3 Massimetti, Marchese et al. (2024) — Real-time multi-sensor radiative power
- **PDF descargado:** No
- **DOI:** https://doi.org/10.3390/rs16162879 (Remote Sensing 2024, 16, 2879)
- **Aplicabilidad:** Estado-del-arte 2024 para data fusion termica.

---

## 8. PDFs adicionales relevantes ya en el repositorio

- `Anantrasirichai2022_ML_Sentinel1.pdf` — ML para deformacion (complemento)
- `Gaddes_2022_ML_Sentinel1_Deformation.pdf` — ML deformacion
- `Walter2023_CumbreVieja_TriStereo_InSAR.pdf` — Caso de erupcion 2021
- `HomeReef_Tonga_2025_NatureSciRep.pdf` — Erupcion submarina
- `Etna2025_MultiPlatform_SciData.pdf` — Etna multi-plataforma
- `Chen_2021_BIT_Transformer.pdf` — Arquitectura ML para change detection

---

## 9. PDFs que NO se pudieron descargar automaticamente

MDPI bloquea descargas batch via Cloudflare. Todas las URLs estan listadas en cada entry; descarga manual desde un navegador con sesion activa funciona.

Lista de no descargados:
- Yu et al. 2014 (RS 6/10/9829)
- Du et al. 2015 (RS 7/1/647)
- Wang et al. 2015 (RS 7/4/4371)
- Marchese et al. 2019 NHI (RS 11/23/2876)
- Marchese et al. 2020 S2-MIROVA (RS 12/5/820)
- Marchese et al. 2021 NHI ASTER (Sensors 21/4/1538)
- Reath et al. 2020 VOLCANOMS (RS 12/10/1589)
- Sekertekin & Bonafoni 2020 (Sensors 20/14/3915)
- Blackett 2014 L8 TIRS (RS 6/3/2282)
- Genzano et al. 2020 GEE (RS 12/19/3232)
- Massimetti et al. 2020 (RS 12/5/820)
- Valade et al. 2019 MOUNTS (RS 11/13/1528)
- Barsi et al. 2014 TIRS calibration (RS 6/11/11607)
- Montanaro et al. 2014 stray light (RS 6/11/10435)

Paywalled (Wiley/Springer/Elsevier/IEEE):
- Jimenez-Munoz & Sobrino 2003 (JGR)
- Jimenez-Munoz et al. 2009 (IEEE TGRS)
- Wang et al. 2019 SC algorithm (JGR Atmospheres)
- Francis & Rothery 1987 (Geology)
- Oppenheimer et al. 1993 (JGR)
- Wooster & Rothery 1997 (Bull Volcanol)
- Reath et al. 2019 AVTOD (JVGR)
- Pritchard et al. 2014 (JVGR)
- Schott et al. 2014 (RSE)
- Ramsey 2016 (GSL SP426)
- Malakar et al. 2018 ATBD (IEEE TGRS)

---

## 10. Recomendaciones operativas para el proyecto

1. **Adoptar producto USGS Landsat C2 Level-2 ST_B10** como fuente primaria de LST (ya validado, sin re-implementar SC). Disponible en GEE: `LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LC09/C02/T1_L2`.
2. **Implementar NHI (Marchese 2019)** sobre bandas SWIR1+SWIR2+NIR de OLI para deteccion de hot spots; complementa el TIRS cuando hay saturacion termica.
3. **Usar SOLO B10 para LST** (no SW con B10+B11) en Landsat 8 por el problema de stray light en B11 (Barsi 2014, Montanaro 2014). Landsat 9 ya no tiene este problema.
4. **Construir baseline historico** con Wang et al. 2019 SCA unificado para extender series 1984-presente sobre los 46 volcanes.
5. **Cross-validar** con AVTOD (Reath et al. 2019) y MIROVA (Coppola 2023) para los volcanes chilenos comunes.
6. **Cascada multi-sensor** estilo Pieri-Abrams: VIIRS/MODIS dispara -> Landsat/S2 confirma con detalle espacial -> alerta SERNAGEOMIN.
