# 📚 Bibliografía — Detección de Cambios en Monitoreo Volcánico Satelital

**Proyecto:** Copernicus-v1 — Sistema de monitoreo de 46 volcanes chilenos con Sentinel-2 + Landsat 8/9
**Generado:** 2026-05-10
**Total referencias:** ~149 (algunas duplicadas entre temas)

---

## 📑 Índice de archivos temáticos

> **Meta-documento:** [METODOLOGIA_BUSQUEDA_DESCARGA.md](METODOLOGIA_BUSQUEDA_DESCARGA.md) — manual operativo de cómo se buscó, descargó y fichó esta bibliografía (fuentes, comandos, lecciones aprendidas).

| # | Archivo | Foco | Refs |
|---|---|---|---|
| 1 | [algoritmos_deteccion_cambios.md](algoritmos_deteccion_cambios.md) | Algoritmos genéricos: differencing, CVA, PCA, time series (BFAST/CCDC/LandTrendr), deep learning (BIT, Siamese U-Net), Mahalanobis, OBIA | 40 |
| 2 | [sentinel2_swir_thermal_anomalias.md](sentinel2_swir_thermal_anomalias.md) | Sentinel-2 SWIR específico: MIROVA, MODVOLC, NHI, Massimetti, Marchese-Genzano, autores Coppola/Wright | 26 |
| 3 | [Landsat_Volcanic_Thermal_Bibliography.md](Landsat_Volcanic_Thermal_Bibliography.md) | Landsat 8/9 TIRS: LST algorithms (SCA, Mono-Window, Split-Window), AVTOD, USGS Collection 2, calibración B10/B11 | 30+ |
| 4 | [imagenes_comerciales_alta_resolucion.md](imagenes_comerciales_alta_resolucion.md) | Planet Labs, SkySat, Maxar/Vantor, SAR comercial (Capella, ICEYE), comparación resolución | 23 |
| 5 | [monitoreo_satelital_volcanes_chilenos_andinos.md](monitoreo_satelital_volcanes_chilenos_andinos.md) | Volcanes específicos Chile/Andes: Villarrica, Lascar, Cordón Caulle, Calbuco, Hudson, Chaitén, Copahue. Autores: Lara, Naranjo, Aguilera, Layana, Bertin | 30 |

---

## 🎯 Top 10 papers prioritarios para acción inmediata

| # | Paper | Por qué es crítico | PDF |
|---|---|---|---|
| 1 | **Massimetti 2020** — Hot-Spot Detection S2 vs MIROVA | Algoritmo benchmark, umbrales α/β, clusters | ❌ MDPI bloqueado |
| 2 | **Marchese 2019** — NHI Multi-Channel S2/L8 | NHI homogéneo S2/L8/L9 con un solo umbral | ❌ MDPI bloqueado |
| 3 | **Coppola 2016** — MIROVA enhanced detection | Define VRP en Watts (métrica universal) | ✅ `pdfs/Coppola2019_MIROVA.pdf` |
| 4 | **Valade 2019** — MOUNTS multi-sensor | Arquitectura modelo a replicar | ❌ MDPI bloqueado |
| 5 | **Wright 2004** — MODVOLC | Padre conceptual NHI | ✅ `pdfs/Wright_2004_MODVOLC.pdf` |
| 6 | **Reath 2019** — AVTOD Latam | Dataset cross-validación volcanes chilenos | ❌ Springer paywall |
| 7 | **Liu 2021** — High-temp S2 + nieve/hielo | Crítico para Hudson, Villarrica, Lonquimay (con glaciar) | ❌ Elsevier paywall |
| 8 | **Zhu 2014** — CCDC | Formaliza "consistencia multi-frame" del proyecto | ❌ Elsevier paywall |
| 9 | **Coppola 2023** — Global radiant flux MIROVA | Datos de referencia globales | ✅ `pdfs/Coppola_2023_GlobalRadiantFlux_MIROVA.pdf` |
| 10 | **Layana 2020** — VOLCANOMS Chile (UCN) | Antecedente nacional directo, coordinar con autores | ❌ Pendiente |

---

## 📥 PDFs descargados (15 archivos, ~74 MB)

Ubicación: `bibliografia/pdfs/`

| PDF | Tamaño | Tema |
|---|---|---|
| `Aguilera2022_Peteroa_Lakes.pdf` | 5.6 MB | Landsat 36 años Peteroa, autores chilenos UCN |
| `Anantrasirichai2022_ML_Sentinel1.pdf` | 4.4 MB | Autoencoders deformación InSAR |
| `Chen_2021_BIT_Transformer.pdf` | 6.4 MB | Transformer state-of-the-art change detection |
| `Coppola2019_MIROVA.pdf` | 10 MB | Sistema MIROVA, base teórica VRP |
| `Coppola_2023_GlobalRadiantFlux_MIROVA.pdf` | 5.1 MB | Datos globales VRP |
| `CumbreVieja_DSM_SciData.pdf` | 2.4 MB | DSM erupción 2021 multi-plataforma |
| `Etna2025_MultiPlatform_SciData.pdf` | 1.4 MB | Etna multi-plataforma reciente |
| `Gaddes_2022_ML_Sentinel1_Deformation.pdf` | 4.4 MB | CNN sobre 500K interferogramas |
| `HomeReef_Tonga_2025_NatureSciRep.pdf` | 3.8 MB | Tonga monitoring incluye PlanetScope |
| `Niclos_2021_L9TIRS2_validation.pdf` | 3.4 MB | Validación Landsat 9 TIRS-2 |
| `Pieri_Abrams_2004_ASTER_volcanoes.pdf` | 1.6 MB | URP — Underflight Radiance Product |
| `Romero2024_SVZ_Review.pdf` | 37 KB | South Volcanic Zone Chile review |
| `Walter2023_CumbreVieja_TriStereo_InSAR.pdf` | 2.7 MB | Tri-estéreo + InSAR |
| `Wright_2002_AutomatedVolcanicEruption_MODIS.pdf` | 1.5 MB | Detección automática MODIS pre-MODVOLC |
| `Wright_2004_MODVOLC.pdf` | 2.6 MB | MODVOLC algoritmo seminal |
| `Wright_2016_AlgorithmsReview_HotSpots.pdf` | 377 KB | Review algoritmos térmicos |

---

## 📝 Lista de pendientes — Para descargar manualmente

### MDPI (todos open access pero bloquean curl/wget — bajar desde navegador)

```
https://www.mdpi.com/2072-4292/12/5/820     — Massimetti 2020 S2 hot-spot
https://www.mdpi.com/2072-4292/11/23/2876   — Marchese 2019 NHI
https://www.mdpi.com/2072-4292/11/13/1528   — Valade 2019 MOUNTS
https://www.mdpi.com/1424-8220/21/4/1538    — Genzano 2021 NHI ASTER
https://www.mdpi.com/1424-8220/22/5/1713    — Coppola 2022 MODIS→VIIRS
https://www.mdpi.com/2072-4292/12/3/438     — Walter 2020 Steep Slope
https://www.mdpi.com/2072-4292/12/16/2567   — Pyle 2020 Special Issue
https://www.mdpi.com/2079-9292/11/3/431     — Bovolo 2022 Algebraic vs ML
https://www.mdpi.com/2072-4292/17/14/2402   — 2025 LandTrendr/CCDC/BFAST
```

### Elsevier / Wiley / Springer / IEEE (paywall — usar VPN institucional o ResearchGate)

```
DOI 10.1080/01431168908903939                — Singh 1989 review fundacional
DOI 10.1016/j.rse.2010.07.008                — LandTrendr Kennedy 2010
DOI 10.1016/j.rse.2009.08.014                — BFAST Verbesselt 2010
DOI 10.1016/j.rse.2014.01.011                — CCDC Zhu 2014
DOI 10.1016/j.rse.2024.114388                — TIRVolcH Silvestri 2024
DOI 10.1109/TGRS.2023.3236365                — Murphy 2023 ASTER DL
DOI 10.1016/j.isprsjprs.2019.02.009          — Hossain 2019 OBIA review
DOI 10.1016/j.isprsjprs.2021.05.008          — Liu 2021 S2 high-temp
DOI 10.1144/jgs2022-014                      — Marchese 2023 NHI Geological
DOI 10.1016/j.jvolgeores.2016.08.004         — Murphy 2016 daytime S2
DOI 10.1016/j.jvolgeores.2022.107627         — Reath 2022 ASTER Indonesia
DOI 10.1016/j.jvolgeores.2023.107865         — Kearney 2023 SfM
DOI 10.1016/j.jag.2025.06.012                — ML post-erupción Indonesia
DOI 10.1109/TGRS.2015.2479299                — LSMAD Mahalanobis
DOI 10.1109/JSTARS.2022.3162422              — Siamese U-Net Kang 2022
```

### Estrategias para bajarlos

1. **MDPI:** abrir URL en navegador con sesión activa → click en "Download PDF"
2. **Elsevier/Wiley/Springer:** usar VPN institucional SERNAGEOMIN/U.Chile → ResearchGate (autores suelen subir preprints)
3. **IEEE:** acceso institucional, o `arxiv.org` (muchos autores suben preprint)
4. **Sci-Hub:** opción de último recurso si no hay acceso institucional

---

## 🔬 Recomendaciones consolidadas para Copernicus-v1 (orden de prioridad)

### Cambios de bajo esfuerzo, alto impacto

1. **Implementar NHI (Marchese 2019)** — `(B12-B11)/(B12+B11)` y `(B12-B8A)/(B12+B8A)`. Trivial con bandas que ya descargamos. Reemplaza el Z-score actual con un detector que homogeniza S2 + Landsat 8/9 con un mismo umbral.

2. **Calcular VRP (Coppola 2016)** — Por cada hot pixel: `VRP_W = 18.9 × Apixel × DLMIR`. Permite reportar actividad en Watts → comparable con literatura mundial y con MIROVA scrapeado en el proyecto hermano.

3. **Mahalanobis sobre Z-score** — `scipy.spatial.distance.mahalanobis()` con la matriz de covarianza histórica del volcán. Captura correlaciones entre bandas que el Z-score por banda pierde.

4. **Filtro de glaciar (Liu 2021)** — Para Hudson, Villarrica, Lonquimay, Mocho-Choshuenco: máscara de nieve/hielo (NDSI > 0.4) excluida del análisis SWIR para reducir falsos positivos por reflexión brillante.

### Cambios de mediano esfuerzo

5. **CCDC harmonic baseline (Zhu 2014)** — Modela cada píxel como `c0 + c1·cos(2πt/T) + c2·sin(2πt/T)`. Detecta cambios solo cuando residuos exceden umbral por 3+ observaciones. Formaliza la regla "consistencia multi-frame" del proyecto.

6. **TIRVolcH (Silvestri 2024)** — Sobre composite THERMAL de Landsat (B10), detecta anomalías difusas (fumarolas, lagos calientes <300°C) que NHI no captura. Complementa el sistema actual.

7. **Time series VRP/hot_pixels** — Series de #hot_pixels y radiancia SWIR total como métricas resumen por volcán (Marchese 2023 las usa). Visor en dashboard.

### Cambios de alto esfuerzo (fase deep learning)

8. **BIT Transformer (Chen 2021)** o **Siamese U-Net (Kang 2022)** — Sobre par (mediana histórica, imagen actual). Pre-entrenar con LEVIR-CD / OSCD, fine-tune con casos chilenos (Calbuco 2015, Cordón Caulle 2011, Chillán 2008).

9. **Sentinel-1 InSAR (Gaddes 2022, Anantrasirichai 2024)** — Extender Copernicus-v1 con una segunda capa de datos: deformación pre-eruptiva. CNN sobre interferogramas. Hudson 2011 (Delgado) demostró detección 4 meses antes con InSAR + ASTER.

### Coordinación institucional

10. **Coordinar con VOLCANOMS UCN (Layana/Aguilera)** — Antecedente nacional directo. Posible colaboración / reusar dataset / cross-validar.

11. **AVTOD (Reath 2019)** — Dataset latinoamericano que incluye los volcanes del proyecto. Ideal para validación cuantitativa de detecciones.

---

## 🌟 Observaciones generales del estudio

- **Vantor = Maxar Intelligence rebranding** (oct-2025). Las URLs comerciales del dashboard apuntan a sucesor real.
- **PlanetScope no tiene SWIR** → solo BGR+NIR. No reemplaza Landsat/S2 thermal, sirve para morfología diaria (3 m).
- **MDPI Akamai** bloquea curl pero los papers son open access — todos descargables manualmente.
- **NICFI (Planet Education)** no cubre Chile (solo trópicos) → la única vía free para 3m es el Education & Research Program directo.
- **Massimetti 2020** y **Marchese 2019 NHI** son los 2 papers más críticos para implementar — ambos open access, ambos pendientes de bajar.

---

## 📞 Contactos institucionales sugeridos

- **VOLCANOMS UCN** (Antofagasta) — F. Aguilera, J. Layana
- **OVDAS-SERNAGEOMIN** — observatorios volcanes Andes Sur (Temuco)
- **INGV Italia** — Coppola, Massimetti, Marchese (autores principales NHI/MIROVA)
- **HIGP Hawaii** — Wright (MODVOLC autor)
- **University of Bristol** — Biggs, Anantrasirichai (DL volcanes)
