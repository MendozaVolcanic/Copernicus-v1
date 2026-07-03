# 🔧 Roadmap de Implementación — Copernicus-v1 mejorado

**Basado en:** ~149 referencias bibliográficas + lectura técnica de 13 PDFs
**Generado:** 2026-05-10
**Notas técnicas detalladas:** `bibliografia/notas/01..04_*.md`

---

## 📚 Documentos de referencia generados

| Archivo | Contenido |
|---|---|
| [`notas/01_MIROVA_MODVOLC.md`](notas/01_MIROVA_MODVOLC.md) | ~9.000 palabras. Wright 2002/2004 (NTI/MODVOLC), Coppola 2019/2023 (MIROVA, VRP, c_rad). Pseudocódigo completo. |
| [`notas/02_DeepLearning_ChangeDetection.md`](notas/02_DeepLearning_ChangeDetection.md) | Chen 2021 (BIT Transformer) + Gaddes 2022 (CNN deformación). Repos GitHub para fork. |
| [`notas/03_Chile_Andes.md`](notas/03_Chile_Andes.md) | Aguilera 2021 (Peteroa, pipeline VOLCANOMS UCN), Murphy 2013 (Lascar). Validado contra in-situ. |
| [`notas/04_CasosEstudio_MultiPlatform.md`](notas/04_CasosEstudio_MultiPlatform.md) | Cumbre Vieja, Home Reef, Etna, Civico DSM, Barsi 2022 (L9 TIRS-2). Pipelines multi-sensor. |

---

## 🎯 Quick wins — Cambios concretos al proyecto (orden de prioridad)

### #1 Implementar NHI (Normalized Hotspot Indices) — **EFFORT: 1 día**

**Por qué:** Reemplaza el Z-score actual con un detector validado científicamente, **homogéneo entre Sentinel-2 y Landsat 8/9** (un solo umbral). No requiere re-descarga de imágenes (las bandas ya están).

**Bandas necesarias** (todas ya descargadas):
- Sentinel-2: B12 (SWIR2), B11 (SWIR1), B8A (NIR narrow). Resolución 20 m.
- Landsat 8/9: B7 (SWIR2), B6 (SWIR1), B5 (NIR). Resolución 30 m.

**Algoritmo (Marchese et al. 2019):**

```python
# En change_analysis.py — agregar antes del cálculo de Z-score
def nhi_swir(b12, b11):
    """Normalized Hotspot Index SWIR. b12, b11 = reflectancias TOA o BOA."""
    return (b12 - b11) / (b12 + b11 + 1e-10)

def nhi_swnir(b12, b8a):
    """NHI SWIR-NIR — para hot spots de muy alta T (lava expuesta)."""
    return (b12 - b8a) / (b12 + b8a + 1e-10)

def detectar_hot_pixels_nhi(b12, b11, b8a):
    """
    Retorna máscara booleana de hot pixels.
    Umbrales según Marchese 2019 + Massimetti 2020:
    - NHI_SWIR > 0   → píxel térmicamente anómalo
    - NHI_SWNIR > 0  AND b8a > 0.15 → confirmación alta-T
    """
    h_swir = nhi_swir(b12, b11) > 0
    h_swnir_strict = (nhi_swnir(b12, b8a) > 0) & (b8a > 0.15)
    return h_swir | h_swnir_strict
```

**Validación esperada:** ~6% comisión / 1% omisión globalmente (Massimetti 2020 paper).

**Dónde insertarlo:** `change_analysis.py` — agregar después del cargado de bandas, antes del Z-score actual. Comparar resultados.

---

### #2 Calcular VRP en Watts (Volcanic Radiative Power) — **EFFORT: 1 día** — STATUS: IMPLEMENTADO (Sprint 2, 2026-05-17)

**ESTADO:** `calcular_vrp_real()` en `change_analysis.py` (Sprint 2).
Descarga aditiva de `SWIR_raw.npz` (B11+B12 reflectancia BOA float32) por escena S2.
Fallback al proxy legacy si el `.npz` no está disponible (compatibilidad histórica).

- **Constante solar B12 Sentinel-2:** `E_SOLAR_B12 = 84.86 W/m²/µm` (ESA S2 PSD).
- **Ángulo solar zenital:** aproximación Spencer 1971 (error <2° para -60°<lat<-15° en hora de paso S2 ~14:50 UTC). Suficiente para precisión MIROVA (±factor 2-3). Para mayor exactitud → `pvlib.solarposition.get_solarposition()` (no agregado para evitar dependencia pesada).
- **Validación sintética Lascar:** 6 hot pixels con B12=0.70 → **0.749 MW** (rango MIROVA 0.5-5 MW confirmado).
- **Tests:** 4 nuevos en `tests/test_change_analysis.py` (path inexistente, escena fría, escena con lava, escalado por área de pixel).
- **PU adicional estimado:** 1 evalscript extra por escena S2 → ~33% más Process Units (escalable, ya teníamos RGB+ThermalFalseColor). Para 46 entidades × 2 pasadas/día ≈ 92 PU/día adicionales.

**ROADMAP residual:**
- TADR (m³/s) = VRP / c_rad con `c_rad` 1.5-9×10⁷ J/m³ (Coppola 2023). Pendiente.
- Series temporales VRP en dashboard (#? en sección 6.4).
- Re-descargar histórico de 60 días con SWIR_raw — decisión de PU.

---

### #2 (original) Calcular VRP en Watts — referencia histórica

**Por qué:** Métrica universal en Watts comparable con MIROVA mundial y con literatura. Permite reportar actividad cuantitativamente, no solo "ATENCIÓN/ALERTA". SERNAGEOMIN ya es usuario MIROVA → calibración cruzada directa con sus DB.

**Fórmula simplificada (Coppola 2016, ec. simplificada Wooster 2003):**

```python
# Para CADA hot pixel detectado:
SIGMA = 5.67e-8   # Stefan-Boltzmann (W/m²/K⁴)
T_BG = 273.15     # Temperatura fondo asumida (0°C)

def vrp_pixel(L_swir, A_pixel_m2):
    """
    L_swir: radiancia espectral en banda SWIR (W/m²/sr/μm)
    A_pixel: 400 m² (S2 a 20 m) o 900 m² (Landsat a 30 m)
    
    Devuelve: VRP en Watts del píxel.
    Constante 18.9 calibrada por Wooster para SWIR (1.6 μm).
    """
    return 18.9 * A_pixel_m2 * L_swir

# Total volcán = suma sobre hot pixels
def vrp_total(hot_pixels_mask, l_swir_array, a_pixel):
    return (l_swir_array[hot_pixels_mask] * 18.9 * a_pixel).sum()
```

**Niveles térmicos referencia (Coppola 2019):**

| Nivel | VRP (MW) | Interpretación |
|---|---|---|
| Low | < 10 | Fumarolas, lago de agua caliente |
| Moderate | 10–100 | Lago de lava pequeño, dome |
| High | 100–1.000 | Lava effusive activa |
| Very High | 1.000–10.000 | Erupción importante |
| Extreme | > 10.000 | Erupción mayor (Holuhraun, Cumbre Vieja) |

**Para volcanes chilenos (composición intermedia):** usar `c_rad = 1.5 a 9 × 10⁷ J/m³` (Coppola 2023). TADR (m³/s) = VRP / c_rad.

---

### #3 Filtro de glaciar (NDSI) para volcanes con nieve — **EFFORT: medio día**

**Por qué:** Liu 2021 documenta que nieve/hielo pueden generar falsos positivos SWIR. **Crítico para Hudson, Villarrica, Lonquimay, Mocho-Choshuenco** (todos con glaciar significativo).

```python
def ndsi(b3_green, b11_swir):
    """Normalized Difference Snow Index. >0.4 = nieve/hielo."""
    return (b3_green - b11_swir) / (b3_green + b11_swir + 1e-10)

def excluir_glaciar(hot_pixels_mask, b3, b11, umbral_ndsi=0.4):
    """Quita del mask cualquier hot pixel sobre nieve."""
    snow_mask = ndsi(b3, b11) > umbral_ndsi
    return hot_pixels_mask & ~snow_mask
```

**Aplicar selectivamente:** solo a volcanes con glaciar (lista en config). Para volcanes áridos (Lascar, Taapaca, Parinacota) no hace falta.

---

### #4 Z-score → Distancia Mahalanobis — **EFFORT: 1 día**

**Por qué:** Z-score por banda **pierde correlaciones** entre bandas. Mahalanobis las captura, detectando anomalías que el sistema actual omite.

```python
import numpy as np
from scipy.spatial.distance import mahalanobis

def calcular_baseline_mahalanobis(stack_historico):
    """
    stack_historico: array (N, H, W, B) — N imágenes históricas, B bandas.
    Calcula media y covarianza por píxel sobre el eje temporal.
    """
    media = stack_historico.mean(axis=0)  # (H, W, B)
    # Por simplicidad, covarianza global no por píxel:
    flat = stack_historico.reshape(-1, stack_historico.shape[-1])
    cov = np.cov(flat.T)
    cov_inv = np.linalg.pinv(cov)
    return media, cov_inv

def detectar_anomalias_mahalanobis(imagen_nueva, media, cov_inv, umbral=3.0):
    """imagen_nueva: (H, W, B). Retorna mask booleana."""
    h, w, b = imagen_nueva.shape
    delta = imagen_nueva - media
    # Distancia por píxel
    d2 = np.einsum('hwb,bc,hwc->hw', delta, cov_inv, delta)
    return d2 > umbral**2  # umbral en unidades de SD
```

**Recomendación:** mantener Z-score como métrica auxiliar para retro-compatibilidad, pero usar Mahalanobis como detector principal.

---

### #5 Adoptar consistencia temporal estilo CCDC — **EFFORT: 1-2 días**

**Por qué:** El proyecto ya tiene "consistencia temporal por sensor" (mencionado en STATUS.md). CCDC (Zhu 2014) la formaliza con modelo armónico:

```python
import numpy as np
from scipy.optimize import curve_fit

def modelo_armonico(t, c0, c1, c2, c3, c4):
    """Periodo anual T=365.25 días."""
    omega = 2 * np.pi / 365.25
    return c0 + c1*t + c2*np.cos(omega*t) + c3*np.sin(omega*t) + c4*np.cos(2*omega*t)

def fit_baseline_pixel(serie_temporal, fechas_dias):
    """Ajusta modelo armónico a la serie histórica de un píxel."""
    popt, _ = curve_fit(modelo_armonico, fechas_dias, serie_temporal)
    return popt

def declarar_cambio(serie, fechas, popt, umbral_sigma=3, n_consec=3):
    """
    Declara cambio cuando 3 observaciones consecutivas exceden N sigma.
    Reduce falsos positivos por nubes/sombras puntuales.
    """
    pred = modelo_armonico(fechas, *popt)
    residuos = serie - pred
    sigma = residuos.std()
    excede = np.abs(residuos) > umbral_sigma * sigma
    # Buscar n_consec consecutivos
    for i in range(len(excede) - n_consec + 1):
        if excede[i:i+n_consec].all():
            return True, fechas[i]
    return False, None
```

---

## 📐 Cambios estructurales (medio plazo)

### #6 Vistas zoom triple (cráter / annulus / regional)

Murphy 2013 valida que para volcanes con cráter pequeño (Lascar, Villarrica, Copahue) **3 niveles de buffer mejoran detección**:

| Vista | Buffer_km | Uso |
|---|---|---|
| **Cráter** | 0.3–0.6 | Detección hot pixels |
| **Annulus** | radio_crater × 2 a 3 | Background contextual (μ, σ) |
| **Regional** | actual del proyecto | Contexto geomorfológico |

Para los volcanes activos (Villarrica, Lascar, Copahue, Chillán, Planchón-Peteroa) **agregar la vista cráter** además de la regional ya existente. Las zoom views Hudson_Ultima_Erupcion, Mentolat_Sismicidad_VT, Melimoyu_Conos_Eruptivos son ejemplos correctos de esta arquitectura.

---

### #7 Enriquecer metadata.csv con métricas térmicas

Agregar columnas a `docs/sentinel2/<volcan>/metadata.csv`:

```csv
fecha, tipo, cobertura_nubosa, sensor, ruta_archivo, tamano_mb,
n_hot_pixels_nhi,            # cantidad NHI > 0
vrp_total_mw,                # VRP en megawatts
nhi_max,                     # valor pico NHI_SWIR
nhi_swnir_max,               # valor pico NHI_SWNIR
n_pixels_glaciar,            # excluidos por NDSI
estado_termico,              # Low/Moderate/High/Very High/Extreme
```

Esto permite:
- **Series temporales VRP** en el dashboard (gráfico nuevo)
- **Validación cuantitativa** contra MIROVA scrapeado
- **Alertas más informativas** (no solo NORMAL/ATENCIÓN/ALERTA)

---

### #8 Integrar AVTOD (Reath 2019) para validación

**AVTOD** (Andes Volcanic Thermal Observation Dataset) cubre los **mismos volcanes chilenos** del proyecto. Es ideal para validación cruzada:

1. Bajar dataset (ESS Open Archive)
2. Comparar nuestras detecciones NHI vs AVTOD para 2015–2020
3. Calibrar umbrales si hay discrepancia sistemática

**Esfuerzo:** 2 días (1 día en bajar/parsear + 1 día comparación).

---

## 🤖 Fase Deep Learning (largo plazo, opcional)

### #9 BIT Transformer para change detection (Chen 2021)

**Repo:** https://github.com/justchenhao/BIT_CD (PyTorch oficial)

**Aplicación al proyecto:**
1. Pre-entrenar con datasets públicos: LEVIR-CD, WHU, DSIFN
2. Fine-tune con casos chilenos: Calbuco 2015, Cordón Caulle 2011, Chillán 2008, Villarrica 2015
3. Reemplazar gradualmente change_analysis.py para casos donde hay buena baseline

**Hardware:** 1 GPU 16GB (RTX 3090 / Tesla T4) para entrenar. Inferencia OK en CPU.

### #10 Autoencoder para anomaly detection térmico

Concepto: entrenar autoencoder convolucional con stacks históricos de imágenes "normales" del volcán. Cuando el reconstruction error supera umbral → anomalía.

**Ventaja:** no necesita labels (unsupervised), solo data histórica que ya tenemos.

**Repo de inspiración:** Anantrasirichai 2024 (autoencoders para Sentinel-1) — similar approach aplicable a S2 SWIR.

---

## 📊 Mapa Bandas MODIS ↔ Sentinel-2 ↔ Landsat (importante)

Limitación clave detectada: **MODIS MIR 3.9μm (B22) NO existe en S2/L8**. Las fórmulas originales de Wright/Coppola usan MIR — debemos sustituir por NHI SWIR.

| Función | MODIS | Sentinel-2 | Landsat 8/9 |
|---|---|---|---|
| Hot spot strong | B22 (3.9 μm MIR) | **B12 (2.19 μm SWIR2)** ← sustituto | B7 (2.2 μm SWIR2) |
| Background | B32 (12 μm TIR) | — (no TIR) | B10 (10.9 μm TIR) |
| Cloud / vegetation | varias | B8A (865 nm NIR) | B5 (865 nm NIR) |
| Hot spot extreme | B21 (4 μm MIR) | B11 (1.61 μm SWIR1) | B6 (1.61 μm SWIR1) |

**Implicancia:** los algoritmos como NTI no son directamente aplicables — usar NHI (Marchese 2019) que ya está adaptado a SWIR de S2/L8.

---

## 🚨 Bugs encontrados durante el estudio

1. **PDFs mal etiquetados (renombrados ya):**
   - `Pieri_Abrams_2004_*.pdf` era en realidad Murphy et al. 2013 → renombrado a `Murphy2013_MODIS_ASTER_synergy.pdf`
   - `Niclos_2021_*.pdf` era Barsi 2022 SPIE → renombrado a `Barsi2022_L9_TIRS2_commissioning.pdf`
   - `Wright_2016_*.pdf` era solo landing page paywall de Steffke & Harris 2011 → renombrado a `Steffke_Harris_2011_landingpage_paywall.pdf`
   - `Romero2024_SVZ_Review.pdf` (37 KB) **es solo HTML del journal**, no PDF. Re-bajar desde DOI 10.5027/andgeoV51n2-3681

2. **Anantrasirichai paper:** el PDF en repo era duplicado de Gaddes (mismo MD5). Bajar correcto desde ESS Open Archive 2024.

3. **Bug latente en proyecto:** si `metadata.csv` mezcla L8 y L9 sin distinguir, plots térmicos tienen bias por **0.61 K residual stray light en B11 de L8** (Barsi 2022). **Recomendación: usar B10 monocanal de ambos**, reservar split-window solo para L9.

---

## 📞 Contactos académicos sugeridos

| Institución | Personas | Para qué |
|---|---|---|
| **VOLCANOMS UCN** Antofagasta | Aguilera, Layana | Pipeline norte de Chile, calibración Lascar |
| **OVDAS-SERNAGEOMIN** | Bucarey Parra, Lara (autores Coppola 2019 — ya son usuarios MIROVA) | Validación cruzada con MIROVA DB |
| **U. de O'Higgins** | Romero | South Volcanic Zone Chile review |
| **OAVV (Argentina)** | Forte | Volcanes binacionales (Lanín, Copahue, Peteroa) |
| **HIGP Hawaii** | Wright | Validación contra MODVOLC histórica |
| **U. Bristol** | Biggs, Anantrasirichai | Deep Learning + InSAR |

---

## 📋 Roadmap consolidado por sprints

### Sprint 1 (1 semana) — Quick wins implementables ya
- [ ] Implementar NHI en `change_analysis.py` (#1)
- [x] Calcular VRP en Watts por volcán (#2) — calibrado real Wooster 2003 / Coppola 2016 vía SWIR_raw .npz
- [ ] Filtro NDSI para volcanes con glaciar (#3)
- [ ] Push + comparar con sistema actual

### Sprint 2 (1 semana) — Métricas + validación
- [ ] Migrar Z-score → Mahalanobis (#4)
- [ ] Enriquecer metadata.csv con métricas térmicas (#7)
- [ ] Bug fix L8 vs L9 stray light (#bugs latentes)
- [ ] Bajar AVTOD dataset y comparar (#8)

### Sprint 3 (1-2 semanas) — Estructura + arquitectura
- [ ] Vistas zoom triple para 6 volcanes activos (#6)
- [ ] CCDC harmonic baseline (#5)
- [ ] Series temporales VRP en dashboard (gráfico nuevo)

### Sprint 4 (3-4 semanas, opcional) — Deep Learning
- [ ] Setup BIT Transformer + datasets públicos (#9)
- [ ] Fine-tune con casos chilenos
- [ ] A/B testing contra change_analysis.py actual

### Sprint 5 (continuo) — Coordinación institucional
- [ ] Contactar VOLCANOMS UCN (#contactos)
- [ ] Validación cruzada con MIROVA DB (vía Bucarey/Lara SERNAGEOMIN)
- [ ] Publicación conjunta resultados

---

## 📈 Métricas de éxito esperadas

Con #1+#2+#3 implementados, comparar contra sistema actual:
- **Tasa de detección:** debería aumentar para hot spots débiles (NHI captura outliers que Z-score pierde)
- **Falsos positivos por glaciar:** reducir a ~0% en Hudson/Villarrica/Lonquimay
- **VRP reportado:** comparable contra MIROVA en ±1 orden de magnitud (validación)

Con #5+#6 estructurales:
- **Falsos positivos por nubes/sombras:** reducir 50%+ con consistencia temporal
- **Sensibilidad a anomalías subpixel:** mejorar 2-3× con vistas cráter

Con #9 deep learning (si se llega):
- **F1 vs sistema clásico:** estado del arte reporta +5-15% mejora con BIT/Siamese U-Net.

---

## 🎓 Recursos para implementación

**Repos GitHub útiles:**
- BIT Change Detection: https://github.com/justchenhao/BIT_CD
- LEVIR-CD dataset: https://justchenhao.github.io/LEVIR/
- COMET-LiCSAR (Gaddes deformación): https://comet.nerc.ac.uk/COMET-LiCS-portal/
- Sentinel Hub Custom Scripts (NHI ready-to-use): https://custom-scripts.sentinel-hub.com/

**Datasets públicos:**
- AVTOD Latam: https://essopenarchive.org/users/.../1...
- MIROVA OSF database: https://osf.io/zm62w/
- LEVIR-CD: 637 imágenes change pairs, free
- OSCD: 24 ciudades, free, change detection

**Manuales algoritmos:**
- USGS Landsat Algorithm Theoretical Basis Documents (ATBDs): https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products
- Sentinel Hub Process API documentation
- Coppola 2019 MIROVA — full pipeline schematic en Figure 2

---

**Estado del documento:** v1.0, generado a partir de búsqueda bibliográfica exhaustiva + lectura técnica de 13 PDFs por 4 agentes paralelos.
