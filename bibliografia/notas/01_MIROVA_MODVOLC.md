# 01 — MIROVA / MODVOLC: algoritmos fundacionales de detección de hot spots volcánicos

Notas técnicas accionables extraídas de 5 papers fundacionales. Pensadas como referencia de implementación para Copernicus-v1 (Sentinel-2 L2A + Landsat 8/9 sobre 46 volcanes chilenos).

**Resumen rápido del flujo**:
1. Wright 2002 → introduce **NTI** (Normalized Thermal Index) sobre MODIS bandas 21/22 (3.959 µm) vs 32 (12.02 µm). Threshold global empírico: **NTI > -0.80** = hot spot.
2. Wright 2004 → describe **MODVOLC**, sistema operacional global basado en NTI. Mismo umbral. Solo nocturno.
3. Steffke & Harris 2011 (etiquetado "Wright_2016") → review: clasifica algoritmos en **contextual / fixed-threshold / temporal**. Fundadores: VAST / MODVOLC / RST.
4. Coppola 2019 → **MIROVA**: NTI + ETI + filtro contextual espacial; introduce **VRP** (Volcanic Radiative Power) vía MIR-method de Wooster 2003: `VRP = 18.9 · A_pix · ΣΔL_MIR`.
5. Coppola 2023 → DB global 20 años, define `VRE = ∫VRP dt`, relación `VRE = Vol · c_rad` y niveles térmicos (Low/Med/High/Very High/Extreme).

**Adaptación clave para Sentinel-2 / Landsat 8/9**: estos sensores NO tienen banda MIR a 3.9 µm — los algoritmos NTI/VRP no son trasladables directos. Se usa SWIR (B11=1.6µm, B12=2.2µm para S2; B6=1.6µm, B7=2.2µm para L8/9) con índices análogos (NHI_SWIR, NHI_SWNIR) y banda térmica B10/B11 de Landsat para temperatura LST. Ver sección final "Mapeo a Copernicus-v1".

---

## Wright et al. 2002 — Automated volcanic eruption detection using MODIS

**Cita completa:** Wright R., Flynn L., Garbeil H., Harris A.J.L., Pilger E. (2002). *Automated volcanic eruption detection using MODIS*. Remote Sensing of Environment 82, 135–155. doi:10.1016/S0034-4257(02)00030-5
**PDF:** `bibliografia/pdfs/Wright_2002_AutomatedVolcanicEruption_MODIS.pdf`
**Páginas leídas:** 1–13 (sección 1–4, algoritmo y validación inicial)

### Resumen ejecutivo
Paper que introduce el **Normalized Thermal Index (NTI)** y el sistema MODVOLC. Demuestra que un umbral global **NTI > -0.80** discrimina hot spots volcánicos en MODIS nocturno con cero falsos positivos en el dataset de calibración (>100 escenas globales). Es la base teórica de todos los sistemas posteriores (MIROVA incluido).

### Fórmulas / Algoritmos (texto exacto)

```python
# Bandas MODIS usadas:
# B21 = MIR low-gain   (3.929–3.989 µm, saturación ~500 K, NEDT 2.0 K)
# B22 = MIR high-gain  (3.929–3.989 µm, saturación ~330 K, NEDT 0.07 K)
# B32 = TIR            (11.770–12.270 µm, saturación ~420 K, NEDT 0.05 K)

# NTI (Normalized Thermal Index)
# Si B22 NO saturado:
NTI = (L22 - L32) / (L22 + L32)            # Eq. (1)
# Si B22 saturado (SI=65533):
NTI = (L21 - L32) / (L21 + L32)            # Eq. (2)
# donde L21, L22, L32 son spectral radiance en W m-2 sr-1 µm-1

# Threshold global empírico (nocturno):
HOTSPOT = (NTI > -0.80)
```

Diagrama de flujo (Fig. 10 del paper) como pseudocódigo:

```python
def modvolc_pixel(pixel):
    if is_bad(pixel.SI):                     # SI > 32767 → reserve values
        return None
    if pixel.solar_zenith < 85:              # daytime → skip (versión nocturna)
        return None
    if pixel.B22_SI == 65533:                # B22 saturado
        nti = (pixel.L21 - pixel.L32) / (pixel.L21 + pixel.L32)
    else:
        nti = (pixel.L22 - pixel.L32) / (pixel.L22 + pixel.L32)
    if nti > -0.80:
        write_alert(pixel.lat, pixel.lon, pixel.time,
                    L21=pixel.L21, L22=pixel.L22, L28=pixel.L28,
                    L31=pixel.L31, L32=pixel.L32,
                    sat_zen=..., sat_az=..., sol_zen=...)
```

### Umbrales / parámetros

| Parámetro | Valor | Unidad | Comentario |
|---|---|---|---|
| NTI threshold (nocturno) | **-0.80** | adim | Empírico global, p.140-142 |
| NTI threshold (Erebus, lago lava polar) | -0.84 (no usado) | adim | Da 100k falsos en Erta Ale |
| Saturation B22 | ~330 | K | Igual que AVHRR/GOES |
| Saturation B21 | ~500 | K | Diseñado para fuegos |
| Saturation B32 | ~420 | K | Mejor que AVHRR/GOES |
| Resolución MODIS bandas térmicas | 1 | km | Nadir; degrada a 4.83 km cross-track en edge (scan ±55°) |
| Pixel size (across-track edge) | 4.83 × 2.08 | km | Distorsión "bow-tie" |
| Geolocation accuracy | ~200 | m | post-corrección bias roll/pitch/yaw |
| Cobertura global | 2 | días | Terra solo; con Aqua: 4 obs/día |
| Bits MODIS L1B | 12 → 16 SI | — | SI > 32767 = reserve values |
| SI saturado | 65533 | — | Trigger uso de B21 |
| SI dead detector | 65531 | — | Excluir pixel |

### Validación

- Calibración sobre 5 volcanes test: **Mt Erebus, Erta Ale, Etna, Soufrière Hills, Kilauea** (Fig. 8, p.142).
- Big Island 2 Feb 2001: 2,748,620 pixels → tail derecha del histograma NTI = 13 pixeles, todos con lava activa Kilauea (Fig. 7).
- Período 1 Oct 2000 – 31 May 2001: detectó hotspots en **33 volcanes** (Tabla 1) incluyendo Lascar (Chile, 4 alertas).
- Modelado lava lake Case A (Erta Ale, fondo 25°C) vs Case B (Erebus, fondo -35°C): NTI converge a -0.86 / -0.97 si lago < 10⁻⁵ del pixel; threshold -0.80 detecta lake desde ~10–100 m² hot fraction (Fig. 9).
- "While the NTI is reliable for **detection**, it should NOT be used for **quantitative analysis** of intensity" (p.144).

### Aplicabilidad concreta a Copernicus-v1

- **NO directo**: NTI requiere banda MIR a 3.9 µm que ni Sentinel-2 ni Landsat 8/9 OLI tienen. Sentinel-2 cubre VNIR+SWIR (hasta 2.2 µm). Landsat 8/9 TIRS sí tiene B10 (10.9 µm) y B11 (12 µm), pero no MIR.
- **Lo que sí trasladar**:
  1. Concepto de **threshold normalizado global** sobre un cociente espectral. El equivalente moderno para S2 es NHI_SWIR = (B12-B11)/(B12+B11) — agregarlo a `change_analysis.py` junto al filtro existente.
  2. Filtro de **datos válidos** análogo a "reserve values" → en S2 usar SCL (Scene Classification Layer) y descartar pixels SCL ∈ {0,1,8,9,10,11} (no_data/saturated/cloud).
  3. **Solo nocturno** no aplica a S2/L8 (sun-synchronous diurnal). Reemplazar con filtro de glint solar / sombras topográficas.
- **Esfuerzo: bajo** (definición de constantes + un nuevo cálculo de índice).

### Limitaciones / advertencias del autor

- "It is impossible to automatically detect all of the thermal anomalies all of the time while eliminating all false-positives" (p.146).
- Single threshold = compromiso entre sensibilidad polar/equatorial. Resulta en under-detection en latitudes frías (Erebus) y aún algunas FN en equatoriales con fondo cálido.
- NTI sensible a temperatura ambiente del fondo: variación 50% en NTI para mismo lago de lava entre fondos -35°C vs +25°C.
- NO discrimina lava de incendios forestales / fuentes industriales (ver lat/lon para asociar a volcán conocido).
- Plumes de ceniza atenúan radiancia 4 µm → falsa interpretación de "fin de erupción" (caso Etna 21 Jul 2001, dip espurio).

---

## Wright et al. 2004 — MODVOLC: near-real-time thermal monitoring of global volcanism

**Cita completa:** Wright R., Flynn L.P., Garbeil H., Harris A.J.L., Pilger E. (2004). *MODVOLC: near-real-time thermal monitoring of global volcanism*. J. Volcanol. Geotherm. Res. 135, 29–49. doi:10.1016/j.jvolgeores.2003.12.008
**PDF:** `bibliografia/pdfs/Wright_2004_MODVOLC.pdf`
**Páginas leídas:** 1–21 (completo, 21 páginas)

### Resumen ejecutivo
Descripción operacional de MODVOLC. Mismo algoritmo NTI > -0.80 de Wright 2002, pero ahora corriendo dentro del pipeline EOSDIS Core System (ECS) en GSFC DAAC. Resultados publicados en near-real-time en `http://modis.higp.hawaii.edu`. Validado contra 50+ volcanes (Tabla 1) entre Oct 2000 – Dic 2003.

### Fórmulas / Algoritmos

Idéntico a Wright 2002 (Eq. 1 y 2). Nuevas métricas operacionales:

```python
# Geolocation pipeline (MOD03)
# Pixel center geodetic coords + GTOPO30 DEM (30 arcsec, ±70 m vert.)
# para corregir parallax inducido por terreno

# Constraint: algoritmo es "point operation" con
#   - max 8 operaciones matemáticas por pixel
#   - max 5 bandas MODIS (usa: 21, 22, 28, 31, 32)
#   - sin estado entre pixels (no contextual, no spatial neighborhood)
```

### Umbrales / parámetros

| Parámetro | Valor | Unidad | Comentario |
|---|---|---|---|
| NTI threshold | -0.80 | adim | Mismo que 2002 |
| Geolocation accuracy (typical) | ~1 | km | Para volcanes listados Tabla 2 |
| Geolocation accuracy (sea-level fires UK) | <1 | km | Rothery et al. 2003 |
| Latencia (pre-mejoras) | hasta 24 | h | Después <24h |
| Pixel @ scan ±55° | 2.08 (along) × 4.83 (across) | km | "bow-tie distortion" |
| Min revisit con Terra+Aqua | ~6 | h | 4 obs/día en latitudes medias |

**Tabla 2 (p.39) — desviaciones medias hot-spot vs cumbre publicada (Simkin & Siebert 1994), año 2002:**

| Volcán | # alertas | Mean displ. (km) | σ (km) |
|---|---|---|---|
| Popocatépetl | 46 | 0.65 | 0.29 |
| Santa Maria | 97 | 3.25 | 0.42 (Caliente vent ≠ summit) |
| Colima | 126 | 0.64 | 0.92 |
| Karymsky | 215 | 0.81 | 0.42 |
| Erebus | 671 | 0.56 | 0.26 |
| Soufrière Hills | 164 | 1.38 | 0.72 |
| Fuego | 246 | 1.15 | 1.44 |
| Erta Ale | 461 | 1.05 | 0.60 |
| Kilauea | 2394 | 4.47 | 2.06 (lava far from summit) |
| Piton de la Fournaise | 184 | 6.11 | 2.15 |
| Shiveluch | 472 | 3.75 | 0.65 |
| Etna | 600 | 2.94 | 2.93 |

### Validación

- 50 volcanes detectados Oct 2000–Dic 2003. Para Chile: Lascar 21 alertas, Villarrica 6.
- Casos de éxito: detección activación de Mount Belinda (Montagu Is., sin Holocene record previo) y Kavachi submarino emergiendo.
- Casos de fallo:
  - **Stromboli**: solo 2 alertas en 19 meses pese a strombolianas ~10/h (energy per event insuficiente para subir NTI).
  - **Lascar (Chile)**: solo 5 hot spots en 573 días pese a presencia de domo activo — modo de emplazamiento (asísmico, endógeno) no produce SWIR suficiente.
- Recomendación del autor: usar trends largo plazo (mensuales+), no day-to-day (clouds/plumes confunden).

### Aplicabilidad concreta a Copernicus-v1

- **Tabla de displacement** (Tabla 2) sirve como **target de calidad de geolocalización** para nuestro sistema. Si nuestros hot spots Sentinel-2 caen >2 km de cumbre publicada en GVP → revisar pipeline.
- **Lección operacional**: para `change_analysis.py` agregar metadata: lat/lon hot pixel + distancia a cumbre + fecha → permite plot tipo "Distance from summit" de MIROVA (sección siguiente).
- **Lista de volcanes activos persistentes** sirve de validación cruzada: si el sistema NO detecta Lascar/Villarrica/Copahue cuando hay reportes SERNAGEOMIN, hay bug.
- **Esfuerzo: bajo** (sumar columna `dist_to_summit_km` al output).

### Limitaciones / advertencias del autor

- "MODVOLC is intended to facilitate **rapid detection**... should not be thought of as an all-encompassing thermal analysis tool" (p.46).
- "The fact that MODVOLC returns **no image data** can lead to ambiguity when interpreting radiance time-series" → siempre conservar la imagen original (S2 nuestro pipeline ya lo hace ✓).
- "**Short-term variations** may not be related to volcanic activity" → ash plumes / clouds / glint.
- Domos endógenos pueden NO disparar el algoritmo aunque crezcan activamente (caso Lascar, Colima pre-2002).

---

## Steffke & Harris 2011 — A review of algorithms for detecting volcanic hot spots in satellite infrared data

**Cita completa:** Steffke A.M., Harris A.J.L. (2011). *A review of algorithms for detecting volcanic hot spots in satellite infrared data*. Bull. Volcanol. 73, 1109–1137. doi:10.1007/s00445-011-0487-7
**PDF:** `bibliografia/pdfs/Wright_2016_AlgorithmsReview_HotSpots.pdf` (¡el filename del repo es engañoso!)
**Páginas leídas:** 1 (solo abstract Springer landing accesible — full text bloqueado por paywall en este PDF)

### Resumen ejecutivo
Review que **clasifica los algoritmos de hot spot detection en tres familias**:

1. **Contextual** — comparan pixel candidato contra estadística de su vecindario espacial. Algoritmo fundador: **VAST** (Higgins & Harris 1997, AVHRR).
2. **Fixed threshold** — un umbral global aplicado por pixel sin contexto. Fundador: **MODVOLC** (Wright et al. 2002, 2004).
3. **Temporal** — comparan pixel contra su propia historia (time-series). Fundador: **RST** (Robust Satellite Technique, Tramutoli 1998 / Pergola et al.).

Performance testeada contra detecciones manuales en Etna (lava sostenida), Stromboli (strombolianas), Augustine (domo+colapso), Vulcano (fumarolas).

### Fórmulas / Algoritmos

(No accesibles en este PDF — solo abstract). Cada familia conceptualmente:

```python
# 1. CONTEXTUAL (VAST family)
#    For each pixel p in scene:
#       window = neighborhood(p, NxN)  # típicamente 3x3 a 15x15
#       BG_mean, BG_std = stats(window minus suspicious pixels)
#       if T_pixel(p) > BG_mean + k * BG_std:  # k típicamente 2-4
#           flag as hotspot
#    Ventaja: adapta al fondo local. Desventaja: falla cerca de bordes/clouds.

# 2. FIXED THRESHOLD (MODVOLC family)
#    Single global rule (NTI > -0.80) — ver arriba.

# 3. TEMPORAL (RST family)
#    For each pixel p:
#       T_history = time-series(p, same_month, multi-year)
#       mu_t, sigma_t = robust_stats(T_history)
#       ALICE = (T_obs - mu_t) / sigma_t
#       if ALICE > threshold:  # típicamente 2-4 sigma
#           flag as hotspot
#    Ventaja: detecta cambios sutiles vs baseline propio. Desventaja: requiere archivo histórico.
```

### Conclusión clave del review (del abstract)

> "As the number of correctly identified anomalies increases, so too does the number of false positives. **No algorithm can be expected to perform perfectly under current data restraints.**"

### Aplicabilidad concreta a Copernicus-v1

- **DECISIÓN ARQUITECTÓNICA**: implementar las **3 familias en paralelo** sobre las imágenes Sentinel-2 ya descargadas:
  1. **Fixed**: NHI_SWIR > 0 (ver Massimetti et al. 2020 cuando esté en bibliografía).
  2. **Contextual**: ventana 7×7 pixels (≈140 m × 7 = 1 km, escala MIROVA), `BG_mean + 3·σ` sobre B12.
  3. **Temporal**: por pixel, comparar contra mediana móvil de las últimas N=12 fechas Sentinel-2 sobre ese mismo punto.
- **Hot pixel = consenso ≥2 de las 3 familias** → reduce falsos positivos sin perder sensibilidad. Esta lógica de "agreement vote" es la práctica moderna (MOUNTS, Valade et al. 2019).
- **Esfuerzo: medio** (agregar dos funciones nuevas a `change_analysis.py`, ya tenemos arquitectura para el fixed). Referencia para implementación: Coppola 2016a (no leído aún) describe el contextual de MIROVA.

### Limitaciones / advertencias

- Solo abstract disponible — recomendar conseguir full text (Sci-Hub o vía SERNAGEOMIN/biblioteca universidad).
- Conclusión del review aplica directo: **siempre habrá trade-off precision/recall**.

---

## Coppola et al. 2019 — Thermal Remote Sensing for Global Volcano Monitoring: Experiences From the MIROVA System

**Cita completa:** Coppola D., Laiolo M., Cigolini C., Massimetti F., Delle Donne D., Ripepe M., et al. (2020). *Thermal Remote Sensing for Global Volcano Monitoring: Experiences From the MIROVA System*. Front. Earth Sci. 7:362. doi:10.3389/feart.2019.00362
**PDF:** `bibliografia/pdfs/Coppola2019_MIROVA.pdf`
**Páginas leídas:** 1–15 (arquitectura, algoritmo, casos uso, thermal unrest, TADR)

### Resumen ejecutivo
Paper canónico del sistema MIROVA. Describe arquitectura (download LANCE → resample 50×50 km UTM → detección híbrida → cálculo VRP → web). Combina **NTI + ETI** (Enhanced Thermal Index, Coppola 2016a) más filtro espacial contextual. Sensibilidad ~1 MW VRP (lava @ 1000°C de 7 m² o fumarola @ 300°C de 143 m²). 216 volcanes operacionales, usado por 17 observatorios incluyendo SERNAGEOMIN.

### Fórmulas / Algoritmos

```python
# 1. RESAMPLE: granule MODIS L1B → grilla regular 50x50 km UTM, pixel 1x1 km
#    centrada en cumbre (coords de Global Volcanism Program).
#    Esto homogeneiza A_pix = 1 km² y elimina bow-tie cerca del nadir.

# 2. ÍNDICES ESPECTRALES (combinados):
NTI = (L_MIR - L_TIR) / (L_MIR + L_TIR)             # Wright 2004, banda 22 + 32
ETI = (L_MIR - L_TIR) * R_MIR                       # Coppola 2016a (R = reflectance/brightness factor)
# (forma exacta de ETI requiere leer Coppola 2016a — no en bibliografía aún)

# 3. FILTRO ESPACIAL CONTEXTUAL:
#    Para zona summit (5x5 km centrada en cumbre): umbrales más bajos
#       → permite detectar fumarolas / hot cracks pequeños
#    Para zonas distales (resto de los 50x50 km): umbrales más altos
#       → reduce falsos positivos (incendios)
#    Lógica: pixel candidato vs estadística de surroundings.

# 4. CÁLCULO VRP (MIR-method de Wooster et al. 2003):
VRP = 18.9 * A_pix * sum(L_MIR_alert_i - L_MIR_bk for i in range(npix))
# - 18.9: coef. proporcionalidad wavelength-dependent
# - A_pix = 1 km² (en MIROVA, post-resample)
# - L_MIR_alert: radiancia MIR del pixel alertado i
# - L_MIR_bk: radiancia MIR de background (promedio de pixeles surrounding)
# - npix: # de pixeles alertados
# Resultado en Watts (W)
# Error nominal: ±30%
# Válido para emisores integrados a 600–1500 K (Wooster 2003)

# 5. RELACIÓN CON STEPHAN-BOLTZMANN
#    VRP ≈ ε · σ · A_hot · T_hot⁴
#    Permite invertir A_hot si conoces T (o viceversa).

# 6. TADR (Time-Averaged Discharge Rate) — para lavas efusivas
TADR = VRP / c_rad
# c_rad (J m⁻³) depende composición:
#   basáltica:    1–4 × 10⁸
#   intermedia:   1.5–9 × 10⁷
#   ácida:        2–10 × 10⁶
# (Coppola et al. 2013, valores también reportados en Coppola 2023 abajo)

# 7. VOLUMEN ACUMULADO
Vol_erupted = integral(TADR dt)
```

### Umbrales / parámetros

| Parámetro | Valor | Unidad | Comentario |
|---|---|---|---|
| Sensibilidad mínima VRP | ~1 | MW | Coppola 2016a |
| Caso "hot" detectable | vent 7 m² @ 1000°C | — | Stephan-Boltzmann límite |
| Caso "cold" detectable | fumarola 143 m² @ 300°C | — | Idem |
| Rango operacional VRP | 1 MW – 50 GW | — | 5 órdenes de magnitud |
| Error VRP | ±30 | % | MIR-method, Wooster 2003 |
| Coef. MIR method | 18.9 | adim/wavelength | Wooster 2003 |
| Resampled pixel | 1 × 1 | km² | Grid UTM 50×50 km |
| Summit zone | 5 × 5 | km | Umbrales más sensibles |
| Distancia "proximal/distal" | 5 | km | Cutoff hotspots stems blue/black |
| Cloud false alert rate | 0–3 | % | "false alerts/MODIS overpasses" típico |
| Latency | 1–4 | h post-acquisition | Web update |

**Niveles térmicos VRP (escala log color, Coppola 2016a, replicada en 2023):**

| Nivel | VRP rango | Color | Uso |
|---|---|---|---|
| Low | < 10⁷ W (10 MW) | verde | fumarolas, dome estable |
| Medium | 10⁷ – 10⁸ W | amarillo | strombolianas leves, dome |
| High | 10⁸ – 10⁹ W | naranja | efusiva activa |
| Very High | 10⁹ – 10¹⁰ W | rojo | flank eruption sostenida |
| Extreme | > 10¹⁰ W (10 GW) | púrpura | mega-eruption (Bardarbunga, Kilauea 2018) |

**Threshold strombolian → effusive (Etna, Stromboli)** (Fig. 10 paper):

```
Magma flux crítico Q_c ≈ 0.1–0.3 m³/s
→ por encima: efusivo / fountains
→ por debajo: strombolian / open-vent
Determinado por análisis bimodal de log(TADR) histórico.
```

### Validación

- 216 volcanes operacionales 2014→presente, archivo desde 2000.
- 17 observatorios usuarios (Tabla S2): incluye **SERNAGEOMIN/Chile** (Bucarey Parra, Lara), IGP/Perú, IGEPN/Ecuador, SGC/Colombia, INSIVUMEH/Guatemala, etc.
- 5 casos arquetipos thermal unrest pre-VEI3 (Fig. 7):
  - **Sabancaya** (Perú): fumarole development, 860 días.
  - **Santa Ana** (El Salvador): hydrothermal rupture, 376 días.
  - **Llaima (Chile)**: rise of magmatic column.
  - **Bezymianny**: increase of dome extrusion rate (semanas).
  - **Tinakula**: sudden opening, solo 2 días pre-VEI3.
- Solo **6–8% de las VEI≥3** (entre 65 monitoreadas post-2002) muestra precursor térmico detectable en MODIS (Furtney et al. 2018). El % sube si se usa S2/L8 alta resolución.
- Casos sin precursor térmico: la mayoría de las VEI3+. Casos sin actividad superficial pese a sismicidad: Galeras, Chiles-Cerro Negro (Colombia).

### Aplicabilidad concreta a Copernicus-v1

- **CRÍTICO** — la VRP es el observable que reporta SERNAGEOMIN al consumir MIROVA. Nuestro sistema debe producir un **proxy de VRP usando bandas SWIR Sentinel-2/L8** ya que no tenemos MIR. Adaptaciones posibles:
  1. Wooster's MIR-method NO trasladable directo. Usar en su lugar **Marchese et al. 2014 / Massimetti 2020 NHI radiative power** vía Planck en SWIR (B11/B12 S2 ≈ 1.6/2.2 µm).
  2. Definir "VRP_SWIR" empírico y calibrar contra MIROVA-MODIS sobre fechas coincidentes (Lascar, Copahue, Villarrica, Nevados de Chillán, Lonquimay todos en MIROVA).
- **Implementar plot "Distance from summit"** (Fig. 4 del paper) en `change_analysis.py` o nuevo `vrp_plotter.py`:
  - Eje X: fecha
  - Eje Y: max(distancia_pixel_alertado_a_cumbre)
  - Stem azul si <5 km, negro si >5 km → distingue actividad cumbre vs flank lava / fires distantes.
- **Implementar niveles de color por VRP** en el dashboard `docs/index.html`:
  - Mapear VRP_proxy a 5 niveles Low/Med/High/Very High/Extreme con paleta de Coppola.
- **Implementar TADR** para erupciones efusivas (Hudson, Cordón Caulle, Lonquimay):
  - `TADR = VRP_proxy / c_rad` con `c_rad` por composición (lookup table volcán → composición SiO₂).
- **Bandas necesarias**: ya las descargamos (B02, B03, B04, B08, **B11**, **B12** Sentinel-2; B6, B7 SWIR + B10/B11 TIRS Landsat). ✓ No se requieren bandas adicionales.
- **Esfuerzo: medio-alto** (módulo nuevo `vrp_proxy.py` + calibración cruzada con MIROVA + UI dashboard).

### Limitaciones / advertencias del autor

- "VRP and color code provided by MIROVA are **not corrected automatically for cloud/geometry**" (p.4). Usuario debe inspeccionar Latest IR Images.
- Lava enfriada >6–24 h emite poco MIR → VRP **subestima** flujo radiante total de coladas viejas.
- VRP insensible a fenómenos difusos baja temperatura (lagos crater, degassing soil) — para Sabancaya pre-eruption se necesitó S2/L8 alta-res TIR (Reath 2019b).
- Topografía de cráteres profundos puede bloquear LOS al satélite con alto zenith → falso "fin actividad".
- "Lack of thermal data does not necessarily mean a volcano is cooling off" (clouds/ash plumes).
- Zenith angle alto + cráter profundo = pixel underestima VRP → reportar siempre `sat_zen` con cada alerta (MIROVA lo hace).

---

## Coppola et al. 2023 — Global radiant flux from active volcanoes: the 2000–2019 MIROVA database

**Cita completa:** Coppola D., Cardone D., Laiolo M., Aveni S., Campus A., Massimetti F. (2023). *Global radiant flux from active volcanoes: the 2000–2019 MIROVA database*. Front. Earth Sci. 11:1240107. doi:10.3389/feart.2023.1240107
**PDF:** `bibliografia/pdfs/Coppola_2023_GlobalRadiantFlux_MIROVA.pdf`
**Páginas leídas:** 1–11 (métodos, dataset, resultados globales, relación VRE↔Vol)

### Resumen ejecutivo
Publicación del **MIROVA Database v.1.0**, con time-series VRP de 111 volcanes (2000–2019). Define formalmente VRE (Volcanic Radiative Energy) y la relación empírica VRE = Vol × c_rad por composición. Ranking global de mayores emisores de calor.

### Fórmulas / Algoritmos (texto exacto)

```python
# 1. EXCESS MIR RADIANCE (Eq. 1, p.3)
L_MIR = sum(L_MIR_hot_i - L_MIR_bk for i in range(N_pix))
# donde:
# - N_pix: # pixeles detectados
# - L_MIR_hot: pixel-integrated radiance del pixel i
# - L_MIR_bk: background radiance (calculada de pixels surrounding la anomalía)

# 2. VOLCANIC RADIATIVE POWER (Eq. 2, p.3)
VRP = A_pix * 18.9 * L_MIR
# A_pix = 10⁶ m² (1 km² post-resample)
# 18.9 = best-fit wavelength-dependent regression coefficient (Wooster 2003)
# Válido para emisor integrado 600–1500 K, error ±30%

# 3. VOLCANIC RADIATIVE ENERGY (sec. 2.4)
# Dos métodos:

# Method-1 (sub-estima por nubes):
VRE_weekly = average(VRP_week) * 7days  # promedio semanal × 7d

# Method-2 (mejor representación):
VRP_filtered = local_minima_filter(VRP_week)  # remueve mínimos locales (clouds)
VRE_weekly = average(VRP_filtered) * 7days

VRE_annual = sum(VRE_weekly for week in year)
VRE_total = sum(VRE_annual for year in 2000..2019)

# 4. RELACIÓN VRE ↔ VOLUMEN ERUPTADO (Eq. 3, Coppola 2013)
VRE = Vol * c_rad
# Vol en m³ (densidad ρ = 2600 kg/m³ para conversión masa↔volumen)
# c_rad (J/m³) por composición:
#   basáltica:    1×10⁸  – 4×10⁸
#   intermedia:   1.5×10⁷ – 9×10⁷
#   ácida:        2×10⁶  – 1×10⁷
```

### Umbrales / parámetros

| Parámetro | Valor | Unidad | Comentario |
|---|---|---|---|
| MIR method coef | 18.9 | — | Wooster 2003 |
| MIR method error | ±30 | % | Para 600–1500 K |
| MODIS pixel resampled | 1×1 = 10⁶ | m² | UTM grid 51×51 |
| Detection threshold VRP | ~1 | MW | Equivale a VTF radio 1.5 m @ 1000°C, o radio 6.9 m @ 330°C |
| Composiciones (SiO₂) | basic <55%, intermediate 55–65%, acid >65% | wt% | Clasificación db |
| **c_rad basáltica** | **1–4 × 10⁸** | J/m³ | Coppola 2013 |
| **c_rad intermedia** | **1.5–9 × 10⁷** | J/m³ | Coppola 2013 |
| **c_rad ácida** | **2–10 × 10⁶** | J/m³ | Coppola 2013 |
| Densidad lava (default) | 2600 | kg/m³ | Galetto 2023 |
| Global VRP avg (2000-2019) | 1.9 × 10⁹ | W | 1.9 GW steady state |
| Volcanes activos (anual) | 60–80 | — | Promedio 67.3 ± 6.1 |
| Volcanes activos (semanal) | 25–40 | — | Promedio 32.5 ± 4.6 |
| VRE total 20 años | ~2.0 × 10¹⁸ | J | 91% basic, 8% inter, 1% acid |

**Tabla 1 (p.5) — campos del CSV por volcán** (cada hot detection):

| Campo | Unidad | Descripción |
|---|---|---|
| UTC | dd/mm/yyyy hh:mm:ss | Fecha y hora de la adquisición |
| Dayflag | 0/1 | 0=nighttime, 1=daytime |
| Sensor | 1/2 | 1=MODIS/Terra, 2=MODIS/Aqua |
| Resolution | m | Pixel size nominal |
| SatZen | deg | Satellite zenith (0=nadir) |
| SatAzi | deg | Satellite azimuth (N clockwise 0–360) |
| Npix | adim | # pixels alertados |
| Tot_Lmir_hot | W m⁻² sr⁻¹ µm⁻¹ | Σ MIR radiance pixels alerted |
| Tot_Lmir_bk | W m⁻² sr⁻¹ µm⁻¹ | Σ MIR background radiance |
| **VRP** | **W** | **Volcanic Radiative Power** |
| Lat | deg | Lat del pixel más caliente |
| Lon | deg | Lon del pixel más caliente |
| max Dist | m | Distancia del pixel alertado más lejano a cumbre |

**Top emisores 20 años (Fig. 6C):**
1. Kilauea ~4.2×10¹⁷ J
2. Nyiragongo ~3.4×10¹⁷ J
3. Bardarbunga ~1.7×10¹⁷ J
4. Nyamuragira ~1.3×10¹⁷ J
5. Etna ~1.2×10¹⁷ J
6. Piton de la Fournaise ~1.1×10¹⁷ J

**Volcanes chilenos en MIROVA Database v.1 (mencionados):**
- Llaima (Fig. 7c, intermediate) — thermal unrest archetype "rise of magmatic column"
- Lascar — degassing plug, intermediate, persistencia >70%
- Puyehue–Cordón Caulle — acid, VRE ~5.8×10¹⁵ J (segundo ácido más energético)
- Chaitén — acid, VRE ~6.2×10¹⁵ J (primer ácido más energético del DB)

### Validación

- Subset 74 volcanes con volúmenes Galetto 2023 → R² = 0.75 entre VRE y Vol (Fig. 7A).
- R² mejora >0.9 cuando se separa por composición (Fig. 7B–D).
- 19 cases basálticos efusivos: c_rad consistente.
- Anomalías "exceso radiación": volcanes open-vent (Stromboli, Erta Ale, Yasur) emiten MÁS calor del que predice su volumen erupted → atribuido a magma column convectivo / outgassing permeable.

### Aplicabilidad concreta a Copernicus-v1

- **DESCARGAR LA BASE DE DATOS**: https://osf.io/zm62w/ — contiene CSVs por volcán (todos los volcanes chilenos en MIROVA). Útil para:
  1. **Calibrar** nuestro VRP_SWIR proxy contra VRP_MODIS para fechas coincidentes (Llaima, Lascar, Villarrica, Copahue, Nevados de Chillán, Hudson, Cordón Caulle, Chaitén, Puyehue).
  2. **Backfill histórico**: integrar serie MIROVA pre-Sentinel-2 (2000–2015) en el dashboard como referencia.
- **Implementar `vre_calculator.py`**:
  ```python
  def vre_from_vrp_series(vrp_ts, dates):
      """Method-2: weekly local-minima filter + integral."""
      ...
  def estimate_volume(vre, composition):
      c_rad = {'basic': 2.5e8, 'intermediate': 5e7, 'acid': 6e6}[composition]
      return vre / c_rad  # m³
  ```
- **Tabla composición por volcán chileno** — agregar a `config/volcano_metadata.json`:
  - Basic: Villarrica, Llaima(?), Hudson, Lonquimay, Calbuco
  - Intermediate: Lascar, Nevados de Chillán, Copahue, Lascar, Planchón-Peteroa, Tupungatito
  - Acid: Chaitén, Puyehue–Cordón Caulle, Quizapu/Descabezado
- **Esfuerzo: medio** (módulo VRE + calibración + metadata composición).

### Limitaciones / advertencias del autor

- VRP NO incluye corrección atmosférica ni cloud fraction (decisión por latency).
- Method-1 (mean weekly) sub-estima; Method-2 (local-min filter) sobre-estima durante cambios abruptos. Promediar ambos = ground truth aproximado.
- VRP solo captura componentes >600 K. Crater lakes, fumarolas difusas, cripto-domos → sub-estimados.
- 1 km² resolución MODIS no resuelve VTF puntuales bien — recomendado integrar S2/L8 alta-resolución (esto es exactamente lo que Copernicus-v1 hace).
- Errores potenciales: alertas "no volcánicas" (incendios, industrial) supervisadas manualmente en v.1.0 pero algunas pueden persistir.

---

## ANEXO: Mapeo MIROVA/MODVOLC → Copernicus-v1 (Sentinel-2 + Landsat 8/9)

### Equivalencias de bandas

| MODIS (MIROVA/MODVOLC) | Sentinel-2 L2A | Landsat 8/9 |
|---|---|---|
| B22 (3.959 µm MIR high-gain) | **NO existe** (S2 corta en B12=2.2 µm) | **NO existe** (OLI corta en B7=2.29 µm) |
| B21 (3.959 µm MIR low-gain) | NO existe | NO existe |
| B32 (12.02 µm TIR) | NO existe | **B11 TIRS** (12.0 µm) ✓ |
| B31 (11.03 µm TIR) | NO existe | **B10 TIRS** (10.9 µm) ✓ |
| (proxy SWIR) | **B11 (1.6 µm), B12 (2.2 µm)** ✓ | **B6 (1.6 µm), B7 (2.2 µm)** ✓ |

### Índices recomendados (sustitutos de NTI para S2/L8)

```python
# Sentinel-2 (resolución 20 m B11/B12, mejor que MODIS 1 km)
NHI_SWIR = (B12 - B11) / (B12 + B11)    # Massimetti et al. 2020
NHI_SWNIR = (B12 - B8A) / (B12 + B8A)
HOTSPOT_S2 = (NHI_SWIR > 0.0) AND (NHI_SWNIR > 0.0)
# B12 saturation > 1.0 reflectancia → saturation hot lava

# Landsat 8/9
NHI_L8_SWIR = (B7 - B6) / (B7 + B6)
LST_L8 = brightness_temperature(B10)    # SWIR + TIRS combinable
```

### Pipeline propuesto unificado para `change_analysis.py`

```
Para cada par (volcán, fecha):
  1. Cargar S2 L2A + Landsat 8/9 (si existe) → rescale a misma grilla UTM 50×50 km
  2. Aplicar SCL filter (descartar nubes/sombras/saturated)
  3. Calcular índices:
       a) Fixed:        NHI_SWIR > 0 (per pixel)
       b) Contextual:   B12 > mean(BG_window_7x7) + 3*sigma
       c) Temporal:     B12 > median(BG_history_12fechas) + 3*MAD
  4. HOT_PIXEL = vote >= 2 de las 3 familias
  5. Agrupar pixels conexos → "anomaly clusters"
  6. Para cada cluster:
       - lat/lon centroide
       - dist_to_summit_km
       - n_pixels
       - VRP_proxy = empirical_swir_to_W(B11, B12, n_pixels, A_pix)
       - LST_max = brightness_T(B10) si Landsat disponible
  7. Output JSON + actualizar plots:
       - Time-series VRP_proxy (escala log, niveles color Coppola)
       - Distance-from-summit plot (proximal blue, distal black)
       - Mapa de hotspots con overlay
  8. Calibración periódica vs MIROVA database (osf.io/zm62w)
```

### Volcanes chilenos en MIROVA — calibración cruzada disponible

(Ver Coppola 2023 Tabla / Coppola 2019 Supplementary Table S2)

Persistencia >70% en 2000–2019:
- Lascar (intermediate, persistente)

Mencionados con eventos importantes:
- Llaima (intermediate) — case Fig. 7c
- Chaitén (acid) — VRE 6.2×10¹⁵ J
- Puyehue–Cordón Caulle (acid) — VRE 5.8×10¹⁵ J
- Villarrica (basic, lava lake intermitente)

Cobertura SERNAGEOMIN MIROVA confirmada (paper 2019, autores Bucarey Parra, Lara) — **podemos pedir directo a SERNAGEOMIN los time-series VRP de los 46 volcanes chilenos** para calibración.

### Esfuerzo total estimado

| Tarea | Esfuerzo | Prioridad |
|---|---|---|
| Agregar NHI_SWIR / NHI_SWNIR a `change_analysis.py` | bajo | alta |
| Agregar familia contextual (BG_window 7x7) | medio | alta |
| Agregar familia temporal (mediana móvil) | medio | media |
| Voting >=2 ensemble | bajo | alta |
| `dist_to_summit_km` por hotspot | bajo | alta |
| Plot "Distance from summit" estilo MIROVA | bajo | media |
| 5 niveles color VRP en dashboard | bajo | media |
| `vrp_proxy.py` (Wooster-adaptado SWIR) | alto | alta |
| `vre_calculator.py` (Method-1 + Method-2) | medio | media |
| Tabla composición SiO₂ por volcán | bajo | alta (necesaria para TADR) |
| `tadr_calculator.py` con c_rad por composición | bajo | media |
| Calibración VRP_proxy vs MIROVA DB (osf.io) | medio | alta |
| Backfill histórico MIROVA 2000–2015 en dashboard | medio | baja |

**Próximo paper a leer prioritario** (no en este lote): **Massimetti et al. 2020** "Volcanic Hot-Spot Detection Using SENTINEL-2: A Comparison With MODIS–MIROVA Thermal Data Series" — adapta directamente NHI a S2 con thresholds calibrados, falta en `bibliografia/pdfs/`.
