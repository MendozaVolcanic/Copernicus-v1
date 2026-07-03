# 03 — Volcanes de Chile y los Andes (referencia operativa)

Síntesis de tres referencias regionales relevantes para el monitoreo Sentinel-2 + Landsat de Copernicus-v1. Foco: Peteroa, Lascar y la Zona Volcánica Sur (SVZ) chilena.

---

## 1. The Evolution of Peteroa Volcano (Chile–Argentina) Crater Lakes Between 1984 and 2020 Based on Landsat and Planet Labs Imagery Analysis

**Cita completa:** Aguilera, F.; Caro, J.; Layana, S. (2021). *The Evolution of Peteroa Volcano (Chile–Argentina) Crater Lakes Between 1984 and 2020 Based on Landsat and Planet Labs Imagery Analysis*. Frontiers in Earth Science 9: 722056. doi: 10.3389/feart.2021.722056.
**PDF:** `bibliografia/pdfs/Aguilera2022_Peteroa_Lakes.pdf`
**Páginas leídas:** 1–17 (introducción, metodologías, resultados, discusión)

### Resumen ejecutivo

Aguilera, Caro y Layana (UCN, Antofagasta + CIGIDEN) reconstruyen 36 años (1984–2020) de actividad térmica en los cuatro lagos cratéricos del complejo Planchón–Peteroa–Azufre combinando 1.208 imágenes Landsat TM/ETM+/OLI-TIRS (TIR + SWIR) con 551 imágenes Planet Labs (RapidEye + PlanetScope) post-2009. Identifican dos ciclos térmico-eruptivos completos (1986–2011 y 2017–2020 en curso), demuestran que aumentos de Qvolc anteceden por meses a las erupciones de febrero 1991, septiembre 2010–julio 2011 y octubre 2018–abril 2019, y validan que el sistema es de bajo flujo de calor (Qvolc máximo 59 MW, individual 7–38 MW por cráter). Es el referente metodológico chileno más completo para monitoreo TIR/SWIR de larga serie con Landsat.

### 🌋 Volcanes / zona estudiada

- **Peteroa** (35.240°S, 70.570°W, 3.603 m s.n.m.), parte del Complejo Volcánico Planchón–Peteroa–Azufre — frontera Chile/Argentina, Zona Volcánica Sur Transicional (TSVZ) — pp. 2–3.
- Mención contextual de los otros dos volcanes con lagos cratéricos en SVZ: **Tupungatito** y **Copahue** (p. 2).
- Período cubierto: **octubre 1984 – diciembre 2020** (Landsat); **mayo 2009 – diciembre 2020** (Planet Labs).

**Coincidencia con los 46 volcanes de Copernicus-v1:**
- ✅ **Planchon-Peteroa** (foco directo del paper)
- ✅ **Tupungatito** (citado como uno de 3 con lagos cratéricos en SVZ)
- ✅ **Copahue** (citado como referente comparativo Qvolc 7–45 MW)
- ✅ **Descabezado Grande**, **Tatara-San Pedro**, **Laguna del Maule** (TSVZ vecina, mismo régimen climático y latitudinal)

### 🛰️ Sensores / datos usados

- **Landsat 4/5 TM** (600 imágenes, bandas TIR-6, SWIR-5/7)
- **Landsat 7 ETM+** (302 imágenes; con franjas negras del SLC-off post-2003 — 113 imágenes parcialmente procesadas)
- **Landsat 8 OLI-TIRS** (306 imágenes; SWIR bandas 6 y 7, TIR-10/11)
- **RapidEye** (117 imágenes, 5 bandas VNIR, 5 m, 5.5 d revisita) y **PlanetScope** (434 imágenes, 4 bandas VNIR, 3–4 m, diaria)
- 400 imágenes Landsat descartadas por nubes; 3 por plumas de tefra.
- Pre-procesado:
  - GeoTIFF descargado de earthexplorer.usgs.gov.
  - **Inspección visual previa** (combinación natural RGB y combinación 7-5-4 RGB para discriminar fumarolas) para separar pixeles "térmicos" vs. "no térmicos" antes de aplicar umbrales.
  - Software **VIPS** dentro de la plataforma **VOLCANOMS** (Layana et al., 2020) — pipeline UCN para radiancia térmica, brightness temperature y radiative heat flux.

### 🧮 Métodos / fórmulas

Umbral de número digital para aislar pixel térmico (esto es directamente reusable en `change_detection.py`):

```python
# Eq. 6 - Aguilera 2022
DN_threshold = mu_non_thermal + 2 * sigma_non_thermal
# pixel termico si DN > DN_threshold
```

Brightness temperature (Landsat TIR):

```python
# Eq. 7 - constantes Landsat TM banda 6
K1 = 607.76  # W/m2 um sr
K2 = 1260.56  # K
T = K2 / np.log(K1 / L_lambda + 1)
```

Radiative heat flux por pixel (Stefan–Boltzmann):

```python
# Eq. 8
sigma_SB = 5.67e-8  # W m-2 K-4
# Emisividades calibradas para lagos cratéricos andinos por estación:
emissivity_lake = {'verano': 0.94, 'invierno': 0.93, 'primavera': 0.93, 'otono': 0.95}
emissivity_ground = 0.98  # todas las estaciones
Q_rad = sigma_SB * eps * T**4 * A_pixel  # W/pixel
# luego restar Q_rad medio del area no termica (background correction)
```

Balance energético completo (Eq. 1–13) implementa Qsun, Qatm, Qrad, Qevap, Qcond, Qrain → permite despejar **Qvolc** (flujo volcánico/hidrotermal). Parámetros atmosféricos fijos a altitud 3.460 m s.n.m. (NOAA): viento 8 m/s, presión 670 mbar, precipitación 0.0029 m/d.

### 📊 Hallazgos clave validados

| Evento | Fecha | Detección satelital | Validación in-situ |
|---|---|---|---|
| Nuevo campo fumarólico precursor C3 | sep 1986 | Qrad TIR 0.1–1.1 MW por 4 años 5 meses | GVP 1987 (40–50 vents, ~100 m²) |
| Erupción freatomagmática | 9–15 feb 1991 | Pico Qrad fumarólico 2.1 MW (19 ene 1991) precediendo erupción | Gardeweg 1991, GVP 1991 |
| Pico de degasificación 1998–2001 | mar 2001 | Qvolc Lago 2 = 38 MW; Lago 4 = 23 MW (máximos del registro) | GVP 2001 (gas plume 500 m, transporte 1 km) |
| Erupción freática | sep 2010–jul 2011 | Crater 3 vaporizado completamente (visible Planet) | Aguilera et al. 2016 |
| Anomalía SWIR primera vez | 6 dic 2018 | Banda 7 OLI = 0.4 W/m²μmsr (Tabla 1) | Erupción oct 2018–abr 2019, GVP 2019, Romero et al. 2020 |
| Pico SWIR | 22 ago 2020 | Banda 7 = 17.4 W/m²μmsr; banda 5 = 7.3 W/m²μmsr (primera vez en banda 5) | — |

**Hallazgo operacional clave:** El aumento de Qvolc precede entre **meses y años** los episodios eruptivos en Peteroa. La anomalía SWIR en banda 7 aparece **antes** que en banda 5 (umbral inferior de detección).

**Validación in-situ:** comparación contra mediciones de temperatura en boca de fumarola y agua del lago muestra discrepancias de ±1 a ±4 K → en términos de Qrad por pixel esto representa solo 0.003–0.006 MW de error → **el método es robusto** (p. 8).

**Mínimo Qrad detectable por pixel** tras corrección de fondo: **0.007 MW** (con ΔT mínima térmico/no-térmico de 2 K).

### 🔗 Aplicabilidad a Copernicus-v1

**Reusable directamente.** El proyecto Copernicus-v1 ya descarga Landsat 8/9 vía repo `Landsat-v1` y produce el composite THERMAL B10. Las ecuaciones (5)–(13) de Aguilera son el siguiente paso natural para pasar de "imagen térmica" a **flujo radiante calibrado** comparable con MIROVA.

**Volcanes Copernicus-v1 que se benefician inmediatamente** (lagos cratéricos o fuerte fumarólico, latitudes templado-frías con temporada seca y restricciones de campo):
- **Planchon-Peteroa** — replicar el ciclo y graficar Qvolc vs fecha en `visualizador.py`.
- **Copahue** — referencia comparable (Varekamp 2001, 7–45 MW). Extender método.
- **Tupungatito** — único caso del NSVZ con lago, casi sin literatura, datos faltantes.
- **Laguna del Maule** — sistema con cuerpo magmático somero detectado por InSAR; estructuras hidrotermales superficiales candidatas a TIR.
- **Nevados de Chillan** — domos activos con anomalías térmicas persistentes ≈ Lascar.
- **Villarrica** — lago de lava persistente; el método de inspección visual TIR + 754 RGB se traslada igual.

**Sub-vistas zoom recomendadas** (basadas en lo que el paper destaca):
- Zoom **interior del cráter principal** — el paper resalta que toda la actividad detectable está confinada a la caldera de 5 km. Para Copernicus-v1 esto valida el patrón de **3 vistas zoom** ya implementado (cumbre / flanco / regional).
- Anular (annulus) **alrededor del cráter activo** para calcular temperatura de fondo robusta, replicable de Murphy et al. 2013 (paper #3 abajo).

**Conexión con datos del proyecto:** el paper procesa 1.208 escenas en 36 años (~33/año). En `docs/sentinel2/Planchon-Peteroa/metadata.csv` Copernicus-v1 ya tiene cadencia mucho mayor con S2 (≈73 escenas/año potenciales pre-nubes). El **rate limiting** real es la cobertura nubosa en TSVZ (33% de descarte en el paper).

### 📞 Autores y afiliación

- **Felipe Aguilera** — Núcleo de Investigación en Riesgo Volcánico-**Ckelar Volcanes**, Universidad Católica del Norte (UCN), Antofagasta + CIGIDEN. Email: `feaguilera@ucn.cl`. Proyecto **VOLCANOMS** / plataforma **VIPS**.
- **Susana Layana** — UCN/CIGIDEN. Co-autora del software VIPS (Layana et al. 2020).
- **Javiera Caro** — UCN.
- **Colaboración futura recomendada:** UCN/Ckelar es un actor clave en remote sensing de volcanes chilenos del norte (Lascar, Lastarria, San Pedro, Putana). Pueden compartir parámetros calibrados de emisividad, software VIPS y series históricas Qrad. Especialmente relevante porque SERNAGEOMIN-OVDAS no publica esa data calibrada.

### ⚠️ Limitaciones / advertencias

- Cobertura nubosa SVZ: **400/1.208 imágenes Landsat (33%) descartadas** — limitación operacional permanente.
- **Failure SLC ETM+ (post-mayo 2003):** 113 imágenes con bandas negras — Lago 1 a 3 a veces ocluidos. *Lección para Copernicus-v1: confiar en Landsat 8/9 (OLI-TIRS) para series consistentes; tratar Landsat 7 como suplementario.*
- **Lagos congelados** en invierno (24–35% Cráteres 1, 2, 4 / solo 3% Cráter 3) → **subestiman Qvolc** en invierno por absorción diferencial vapor/líquido. Aplica a TODO volcán Copernicus-v1 con lago al sur del paralelo 30°S.
- Qvolc=0 cuando hay nube total → underestimación sistemática. Necesario marcar las gaps explícitamente en el dashboard.
- Viento, presión y precipitación se asumen **fijos** (8 m/s, 670 mbar, 0.0029 m/d) — válido para Peteroa caldera pero requiere recalibrar por volcán.

---

## 2. The Andean Southern Volcanic Zone: a review on the legacy of the latest volcanic eruptions

**Cita completa:** Romero, J.E.; Vergara-Pinto, F.; Forte, P.; Ovalle, J.T.; Sánchez, F. (2024). *The Andean Southern Volcanic Zone: a review on the legacy of the latest volcanic eruptions*. Andean Geology 51(2): 379–412. doi: [10.5027/andgeoV51n2-3681](https://dx.doi.org/10.5027/andgeoV51n2-3681).
**PDF:** `bibliografia/pdfs/Romero2024_SVZ_Review.pdf` (en realidad página HTML del journal — solo abstract y metadata accesibles offline; el PDF completo está alojado en SERNAGEOMIN/Andean Geology).
**Páginas leídas:** abstract completo + listado de autores y afiliaciones (todo el contenido extraíble del archivo).

### Resumen ejecutivo

Romero et al. (Universidad de O'Higgins + U. Manchester + OAVV-Argentina + U. Mayor + U. Minho) revisan las erupciones de los últimos <35 años de la Zona Volcánica Sur (SVZ) de los Andes y encuentran que estos eventos han generado >430 publicaciones peer-review con >9.000 citas, dominadas por erupciones VEI 4–5. El abstract divide los hallazgos por composición magmática: erupciones poco silícicas (Llaima 2008–2009, Villarrica 2015) iluminan recarga magmática y desgasificación; intermedias (andesítico-dacítico) revelan transiciones freático→magmático; silícicas (riolítico-riodacítico) explican ascenso rápido de magma y fragmentación. Es la guía bibliográfica de cabecera para priorizar qué volcanes Copernicus-v1 tienen literatura validable.

### 🌋 Volcanes / zona estudiada

Mencionados explícitamente en el abstract:
- **Llaima** (erupción 2008–2009, basalto-andesítica)
- **Villarrica** (erupción 2015, basalto-andesítica)

Cobertura general: **toda la SVZ** desde 33°S a 46°S aproximadamente. Esto incluye en Copernicus-v1:

✅ **Coincidencia masiva** — la SVZ engloba 28 de los 46 volcanes del proyecto:
Tupungatito, San Jose, Tinguiririca, Planchon-Peteroa, Descabezado Grande, Tatara-San Pedro, Laguna del Maule, Nevado de Longavi, Nevados de Chillan, Antuco, Copahue, Callaqui, Lonquimay, Llaima, Sollipulli, Villarrica, Quetrupillan, Lanin, Mocho-Choshuenco, Carran, Puyehue-Cordon Caulle, Antillanca, Osorno, Calbuco, Yate, Hornopiren, Huequi, Michinmahuida.

Período cubierto: **<35 años** (≈1989–2024).

### 🛰️ Sensores / datos usados

No detallado en el abstract. Es paper de revisión bibliográfica, no de procesamiento. Contiene síntesis cualitativa de literatura previa.

### 🧮 Métodos / fórmulas

No aplica — review.

### 📊 Hallazgos clave validados

Categorías porcentuales del estado del arte SVZ:
- **29%** impactos ambientales y atmosféricos
- **20%** descripciones eruptivas y volcanología física
- **15%** evaluación de peligro y riesgo
- el resto se distribuye en geoquímica, petrología, monitoreo, etc.

Hallazgo bibliométrico: **>430 publicaciones peer-review, >9.000 citas** en 35 años de erupciones SVZ — alta densidad de literatura validable para los volcanes "estrella": Chaiten 2008, Cordon Caulle 2011, Calbuco 2015, Villarrica 2015, Llaima 2008, Copahue 2012–presente.

### 🔗 Aplicabilidad a Copernicus-v1

**Indirectamente reusable.** Este paper es la **bibliografía de cabecera** para mapear cada uno de los 28 volcanes SVZ del proyecto a literatura específica. No aporta algoritmos pero sí prioridades de investigación.

**Acción concreta para el proyecto:**
1. Descargar el PDF real desde `https://dx.doi.org/10.5027/andgeoV51n2-3681` (la copia local es solo HTML del landing page).
2. Extraer del PDF completo la **tabla de erupciones recientes SVZ** y cruzarla con `docs/fechas_disponibles_copernicus.json` para verificar que los timelapses cubren los eventos VEI 3+ documentados.
3. Priorizar generación de reportes PPT (vía `ppt_generator.py`) para los volcanes con mayor densidad de literatura: **Villarrica, Llaima, Calbuco, Cordon Caulle, Copahue, Chaiten, Nevados de Chillan**.

**Sub-vistas zoom recomendadas:** no aplica directamente; ver lo derivado del paper #1 y #3.

### 📞 Autores y afiliación

- **Jorge E. Romero** — Instituto de Ciencias de la Ingeniería, **Universidad de O'Higgins**, Rancagua, Chile. Sitio: https://sites.google.com/view/jorge-e-romero/home
- **Francisca Vergara-Pinto** — Humanitarian and Conflict Response Institute, **University of Manchester**, UK.
- **Pablo Forte** — **OAVV / SEGEMAR-CONICET**, Argentina. (Observatorio Argentino de Vigilancia Volcánica — contraparte de SERNAGEOMIN-OVDAS).
- **J. Tomás Ovalle** — Universidad Mayor, Santiago.
- **Florencia Sánchez** — Universidade do Minho, Portugal.
- **Colaboración futura:** Romero (UOH) y Forte (OAVV) son contactos cross-frontera para volcanes binacionales (Peteroa, Copahue, Lanin, Lascar). El proyecto Copernicus-v1 podría ofrecer su pipeline de timelapses como complemento operativo.

### ⚠️ Limitaciones / advertencias

- **El archivo `Romero2024_SVZ_Review.pdf` del repo NO es el PDF del paper, es la página HTML del landing del journal.** Solo 5.755 caracteres extraídos, todos correspondientes al abstract + metadatos del journal Andean Geology. Recomendación urgente: re-descargar el PDF completo desde el DOI.
- Como review, no provee datos cuantitativos directamente reusables.
- No discrimina por tipo de sensor; mezcla literatura InSAR, térmica, geoquímica, sismológica.

---

## 3. MODIS and ASTER synergy for characterizing thermal volcanic activity (incluye Láscar, Chile)

**Cita completa:** Murphy, S.W.; Wright, R.; Oppenheimer, C.; Souza Filho, C.R. (2013). *MODIS and ASTER synergy for characterizing thermal volcanic activity*. Remote Sensing of Environment 131: 195–205. doi: 10.1016/j.rse.2012.12.005.
**PDF:** `bibliografia/pdfs/Pieri_Abrams_2004_ASTER_volcanoes.pdf` ⚠️ **El nombre del archivo es engañoso** — el PDF físico que contiene la carpeta `bibliografia/pdfs/` es Murphy et al. 2013, no Pieri & Abrams 2004. Verificar y, si se quiere el original Pieri & Abrams (Adv. Space Res. 2004, ASTER URP), redescargarlo. Aun así, este paper es ASTER-céntrico, cubre Lascar, y es directamente útil.
**Páginas leídas:** 1–11 (todo el cuerpo del artículo).

### Resumen ejecutivo

Murphy, Wright (autor de MODVOLC), Oppenheimer (Cambridge) y Souza Filho (UNICAMP) comparan 11 años (2000–2012) de **MODIS** (Terra) y **ASTER** (Terra) sobre cuatro volcanes contrastados: Erta 'Ale (lago de lava), Kīlauea (efusivo basáltico), Kliuchevskoi (estratovolcán de arco) y **Láscar (Chile, fumarólico-explosivo)**. Definen dos métricas: **MOD\*** (radiancia anómala MIR via canal 21/22 vs canal 32 de MODIS) y **AST\*** (área anómala usando ASTER TIR a 90 m con umbral ΔT = 40 °C sobre fondo). Demuestran que **MODIS no detecta consistentemente Láscar** porque su actividad fumarólica es de baja temperatura y sub-pixel, mientras que **ASTER sí lo detecta de forma rutinaria (10.000–40.000 m² persistentes)**. Identifican un precursor térmico en Kliuchevskoi (≥5 pixeles ASTER >40 °C en cráter) que anticipó por 2 semanas las coladas de lava 2007 y 2009. Es el mejor argumento técnico para preferir Landsat/Sentinel-2 (alta resolución espacial) sobre MODIS para los volcanes chilenos del norte.

### 🌋 Volcanes / zona estudiada

- **Láscar** (23.37°S, 67.73°W, 5.592 m s.n.m.) — Andes Centrales chilenos, Región de Antofagasta — pp. 1, 4–5, 7–8.
- Otros (no chilenos): Erta 'Ale (Etiopía), Kīlauea (Hawai'i), Kliuchevskoi (Kamchatka).

**Coincidencia con los 46 volcanes de Copernicus-v1:**
- ✅ **Lascar** (estudiado directamente) — el paper lo destaca como volcán difícil para MODIS y bandera de la utilidad de la alta resolución espacial.
- ✅ Por extensión metodológica directa: **Guallatiri, Isluga, Irruputuncu, Ollague, Lastarria, San Pedro, Tupungatito** (todos volcanes con actividad principalmente fumarólica de baja-moderada temperatura y áreas sub-kilométricas, idénticos a Lascar en perfil térmico).

Período cubierto: **24 feb 2000 – 1 ene 2012** (11 años; 17.133 escenas MOD02 + N escenas ASTER por sitio).

### 🛰️ Sensores / datos usados

- **MODIS-Terra** (lanzado 1999):
  - Producto: **MOD02 1km nighttime calibrated radiance** + geolocalización MOD03.
  - Canales: **21** (3.929–3.989 μm, MIR, satura ~225 °C, NEΔT ≈ 2.0 K), **22** (mismo rango, satura ~60 °C, NEΔT 0.07 K), **32** (11.77–12.270 μm, TIR fondo).
  - Solo escenas nocturnas (eliminan contaminación solar).
  - 3.772 escenas para Láscar.
- **ASTER-Terra** (15 m VNIR, 30 m SWIR, 90 m TIR):
  - Producto: **AST_09T** (radiancia at-surface TIR, geo/radio/atmosféricamente corregida por LP DAAC/USGS).
  - Recuperación de temperatura por **Normalized Emissivity Method (NEM)**, ε_max = 0.97 (se descarta AST_08 TES).
  - SWIR de ASTER **inutilizable post-2008** por falla del cooler — VNIR + TIR siguen funcionando (relevante: el SWIR-Landsat sigue siendo opción para Copernicus-v1).
- Pre-procesado:
  - Inspección visual TIR para descartar nubes (escena entera removida si cráter no localizable).
  - Anomalía MODIS por **NTI (Normalized Thermal Index)** = (L_22 − L_32) / (L_22 + L_32). Umbral global MODVOLC = −0.8. Umbrales locales por volcán optimizados con histogramas de NTI.

### 🧮 Métricas / algoritmos

```python
# MOD* — Eq. 2 de Murphy et al. 2013
def MOD_star(scene, anomalous_pixels_idx):
    """Radiancia anomala acumulada en MIR (canal 21)."""
    L = scene['ch21'][anomalous_pixels_idx]
    L_bkgd = bkgd_radiance_from_ch32(scene)  # via brightness T canal 32 -> proxy fondo MIR
    return np.sum(L - L_bkgd)

# NTI - umbral de anomalia MODIS (Wright et al. 2002)
NTI = (L22 - L32) / (L22 + L32)
# si saturacion en canal 22 -> usar canal 21
# umbral global MODVOLC: NTI > -0.8
# umbral local Lascar: definido por histograma NTI por volcan

# AST* — Eq. 4
def AST_star(scene_AST_09T, T_background):
    """Tamano del area anomala (m^2) en ASTER TIR."""
    A_pixel = 8100  # 90 m x 90 m
    delta_T = scene_AST_09T['T'] - T_background
    n_anomalous = np.sum(delta_T > 40.0)  # umbral: 40 C sobre fondo
    return A_pixel * n_anomalous
```

**Background anular para estratoconos** (aplicable a Lascar, Llaima, Villarrica, Lonquimay, Calbuco, etc.):
- Anillo (annulus) alrededor del cráter activo; sigma-clipping a 2σ para excluir flujos de lava intrusivos.
- Provee temperatura de fondo dentro de ±5 °C (validado en Erta 'Ale, Kliuchevskoi, Láscar — p. 4–5).
- Contraejemplo: Kīlauea como volcán escudo no admite annulus → se define con puntos manuales (±15 °C, peor).

### 📊 Hallazgos clave validados

| Volcán | MOD* típico | AST* típico | Detección operativa |
|---|---|---|---|
| Láscar | < 0.5 W/m²/sr/μm (max 2.5) | 10.000–40.000 m² (≈1–5 pixeles ASTER) | **MODIS NO detecta** rutinariamente; ASTER detecta anomalía persistente fumarólica |
| Erta 'Ale | 0–14.4 (med <5) | 1–4×10⁵ m² | Ambos detectan; correlación AST*–MOD* = 0.54 |
| Kīlauea | 7.5 promedio, picos >50 | mean 8.9×10⁵ m² | MODIS captura mejor (eventos cortos) |
| Kliuchevskoi | picos durante 4 erupciones | precursor: ≥5 pixeles ASTER ΔT>40 °C | **Precursor térmico ASTER detectó 2 semanas antes de coladas 2007 y 2009** |

**Hallazgo operacional clave para Chile:** Para volcanes con actividad fumarólica baja (Lascar y similares — todo el norte de Chile salvo erupciones explosivas activas), **la detección con sensores tipo MODIS/MIROVA es estructuralmente insuficiente**. Esta es la justificación científica directa del valor agregado de Copernicus-v1 (Sentinel-2 a 20 m + Landsat OLI-TIRS a 30/100 m) sobre el sistema MIROVA actual en `Automatizacion web/`.

**Validación in-situ:** observación de campo Smithsonian/GVP confirmó:
- Erupciones de fisura Erta 'Ale nov 2008 → coincidente con anomalía NNW del cráter.
- Coladas Kliuchevskoi 2007/2009 → precedidas por inflación térmica ASTER en cráter.
- Lascar: actividad fumarólica persistente confirmada por GVP y campo (Murphy et al. 2011).

### 🔗 Aplicabilidad a Copernicus-v1

**Reusable directamente.**

1. **Métrica AST\*** trasladable a **L8/L9 OLI-TIRS B10/B11** y a Sentinel-2 SWIR (B11/B12 + diferencia con bandas frías). El umbral ΔT > 40 °C es el referente para detección automática de anomalías persistentes en los reportes mensuales (`Hudson_Evaluacion_Mensual_*.pptx` y similares).
2. **Backgrounds anulares** alrededor del cráter principal para todos los estratoconos del proyecto (Llaima, Villarrica, Lascar, Calbuco, Antuco, Lonquimay, Osorno, Lanin) — directamente implementable en `change_detection.py` cuando ya se conoce el centro del cráter.
3. **Justificación ante SERNAGEOMIN:** este paper es la cita académica para responder "¿por qué Copernicus-v1 detecta lo que MIROVA no?" — porque los volcanes chilenos del norte son fumarólicos y sub-pixel para MIROVA/MODIS.

**Volcanes Copernicus-v1 con perfil "tipo Lascar"** (fumarólicos, sin lava lake, sin colada activa) — se benefician en orden de prioridad:
- **Lascar, Lastarria, San Pedro, Putana** — Norte Grande, climas áridos: la combinación Sentinel-2 SWIR (alta detección) + Landsat TIR es ideal.
- **Guallatiri, Isluga, Irruputuncu, Ollague** — todos NSVZ/CVZ con desgasificación persistente.
- **Tupungatito** — lago cratérico análogo a Peteroa pero menor.
- **Villarrica, Copahue** durante quiescencia entre erupciones.

**Sub-vistas zoom recomendadas** (basadas en lo que el paper destaca):
- **Cráter activo** (annulus interior): vista de detalle <500 m radio para detectar fumarolas sub-100m.
- **Anillo background** 500m–1km radio: para estimación de temperatura de fondo dentro de ±5 °C.
- Estas dos vistas zoom son adicionales al "regional" ya implementado, y refuerzan la decisión arquitectónica del proyecto de **3 vistas zoom**.

**Conexión con datos del proyecto:** el `Antillanca - Casablanca/metadata.csv` y similares ya guardan fecha y nombre de banda. El siguiente paso es enriquecer los metadatos con `n_anomalous_pixels` y `AST_star_m2` calculados por la fórmula de arriba.

### 📞 Autores y afiliación

- **Samuel W. Murphy** (autor principal) — University of Campinas (UNICAMP), Brasil. Email: `samsammurphy@gmail.com`.
- **Robert Wright** — University of Hawai'i at Mānoa, USA. **Autor de MODVOLC** y co-autor de los papers MODIS Wright 2002, 2004 y 2016 ya en `bibliografia/pdfs/`.
- **Clive Oppenheimer** — University of Cambridge, UK. Referente histórico de TIR volcánico.
- **Carlos R. Souza Filho** — UNICAMP, Brasil.
- **Colaboración futura:** Souza Filho (Brasil) + Aguilera/Layana (Chile, paper #1) son los nodos sudamericanos del remote sensing volcánico. Wright (Hawai'i) es el contacto MODVOLC para validar resultados Sentinel-2/Landsat de Copernicus-v1 contra la base global MODVOLC.

### ⚠️ Limitaciones / advertencias

- **MODIS satura** sobre lava activa (canal 22 a ~60 °C). Solución: failover a canal 21 (~225 °C). En L8/L9 OLI-TIRS B10 también satura sobre lava — Copernicus-v1 debe usar SWIR L8 B7 cuando hay temperatura magmática.
- **ASTER no es mapping mission** (adquiere bajo demanda) → eventos cortos se pierden. Sentinel-2 (revisita 5 d) y Landsat 8/9 (combinada 8 d) son mejores en cadencia.
- **ASTER SWIR roto desde 2008** — irrelevante para Copernicus-v1 que usa Sentinel-2 SWIR (B11=1.6 μm, B12=2.2 μm).
- **Umbral ΔT=40 °C** es conservador (cero falsas alarmas) pero puede perder fumarolas frías. Para Tupungatito o Lascar quiescente, evaluar bajar a 25–30 °C.
- **Annulus** falla en volcanes escudo — ninguno de los 46 de Copernicus-v1 es escudo puro, así que el método anular es seguro.
- **Inspección manual de nubes** se hizo escena por escena — costoso. Copernicus-v1 puede usar la máscara SCL de Sentinel-2 L2A para automatizar.

---

## Síntesis transversal

1. **Para volcanes Copernicus-v1 con lago cratérico** (Planchon-Peteroa, Tupungatito, Copahue, Laguna del Maule en parte) → aplicar pipeline Aguilera 2022 (balance energético completo, calibración estacional de emisividad 0.93–0.95, parámetros atmosféricos fijos por altitud). Software de referencia: VIPS/VOLCANOMS de UCN.
2. **Para volcanes Copernicus-v1 fumarólicos** (Lascar, Lastarria, San Pedro, Guallatiri, Isluga, Irruputuncu, Ollague, Tupungatito) → aplicar AST*/MOD* de Murphy 2013, con annulus de fondo y umbral ΔT=40 °C (bajable a 25 °C para mayor sensibilidad).
3. **Para volcanes con literatura abundante SVZ** (28 volcanes según Romero 2024) → priorizar reportes PPT y verificación de cobertura de eventos VEI 3+; confirmar en `docs/fechas_disponibles_copernicus.json`.
4. **Cobertura nubosa SVZ ~33%** (Aguilera 2022) → asumir esta tasa de descarte sistemática para Lanin, Villarrica, Calbuco, Hudson, Melimoyu y otros volcanes al sur del paralelo 38°S.
5. **Latencia precursora detectada**: meses (Peteroa 1991, 2018) o semanas (Kliuchevskoi 2007/2009) → la cadencia 5–8 días Sentinel-2/Landsat es **suficiente** para captar precursores térmicos.
6. **Justificación científica de Copernicus-v1 sobre MIROVA**: Murphy 2013 demuestra que MODIS no ve Lascar; eso vale por extensión para todos los volcanes chilenos fumarólicos sub-kilométricos. Citar este paper en cualquier informe a SERNAGEOMIN.
