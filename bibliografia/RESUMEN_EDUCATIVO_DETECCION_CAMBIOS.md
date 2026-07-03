# 🌋 Detección de Cambios Volcánicos con Satélites — Guía para el Equipo

> Documento educativo. Síntesis de ~149 referencias bibliográficas + 15 PDFs analizados durante el proyecto Copernicus-v1.
>
> **Audiencia:** Volcanólogos y geólogos del equipo SERNAGEOMIN. No requiere background previo en teledetección ni programación.
>
> **Objetivo:** Que después de leer esto entiendas **QUÉ** hace nuestro sistema, **POR QUÉ** funciona físicamente, y **CÓMO** se compara con los grandes sistemas operacionales del mundo (MIROVA, MOUNTS, MODVOLC).
>
> **Tiempo estimado de lectura:** 45–60 minutos.

---

## Índice

1. [¿Qué es detección de cambios y para qué sirve?](#1)
2. [Físicamente, ¿qué estamos midiendo?](#2)
3. [Bandas espectrales y qué detecta cada una](#3)
4. [Algoritmos clásicos vs modernos](#4)
5. [Sistemas operacionales en el mundo](#5)
6. [El caso de Chile: nuestro sistema vs MIROVA](#6)
7. [Limitaciones reales del enfoque óptico](#7)
8. [Glosario de términos clave](#8)
9. [Lecturas recomendadas](#9)

---

<a id="1"></a>
## 1. ¿Qué es detección de cambios y para qué sirve?

### El concepto, en una frase

**Detección de cambios** = comparar dos imágenes satelitales del mismo lugar tomadas en fechas distintas, e identificar **qué píxeles cambiaron de manera significativa** entre las dos fechas.

Suena trivial — y conceptualmente lo es — pero "significativo" hace todo el trabajo pesado. Una nube nueva, una sombra que se movió, un cambio estacional de la vegetación, todos generan diferencias entre dos imágenes. La pregunta clave es: **¿este cambio es ruido natural, o es algo nuevo que vale la pena investigar?**

### Tipos de cambio en un volcán

| Tipo de cambio | Qué detectamos | Banda satelital que mejor lo ve | Ejemplo chileno |
|---|---|---|---|
| **Térmico** | Lava, fumarolas, lago de lava, domos calientes | SWIR (1.6 y 2.2 µm) y TIR (10–12 µm) | Villarrica (lago de lava 2014–presente), Lascar (fumarolas persistentes) |
| **Morfológico** | Cráter nuevo, colada de lava, depósito piroclástico, lahar | Color natural RGB (alta resolución) | Calbuco 2015 (cráter ampliado), Cordón Caulle 2011 (depósitos riolíticos) |
| **Vegetación** | Quema/destrucción por flujos piroclásticos o lahares | NDVI (rojo + NIR) | Chaitén 2008 (bosque arrasado), Hudson 1991 (zonas defoliadas por ceniza) |
| **Volátiles atmosféricos** | SO₂, ceniza en suspensión | UV (Sentinel-5P TROPOMI) | Calbuco 2015 (pluma SO₂ visible 7000 km) |
| **Hidrológico/glaciar** | Avance/retroceso glaciar, lagunas nuevas, deshielo abrupto | NDSI (verde + SWIR1) | Hudson (manto glaciar), Mocho-Choshuenco |
| **Deformación** | Inflación/deflación del edificio volcánico | Sentinel-1 SAR interferometría (InSAR) | Laguna del Maule (~25 cm/año desde 2007) |

Copernicus-v1 se enfoca actualmente en los **tres primeros** (térmico, morfológico, vegetación). El cuarto (SO₂) y el sexto (deformación) son extensiones futuras planeadas.

### ¿Para qué sirve en la práctica?

**Pre-erupción** — Detectar anomalías incipientes que precedan una erupción.
- Caso paradigmático: **Peteroa 2018**. Aguilera et al. 2021 mostraron que la radiancia SWIR en banda 7 de Landsat 8 apareció **el 6 de diciembre 2018**, casi 4 semanas antes del inicio de la erupción freática del 14 de enero 2019. Una señal subpixel, indetectable a ojo, pero medible si comparás contra el historial del píxel.
- Caso Kliuchevskoi (Kamchatka, Murphy 2013): inflación térmica medida con ASTER **2 semanas antes** de las coladas de 2007 y 2009.

**Durante la erupción** — Cuantificar lo que está pasando.
- Coppola 2019 (MIROVA): convierte la radiancia infrarroja en VRP (Volcanic Radiative Power) en Watts. Eso permite estimar la tasa efusiva (TADR, m³/s) y, integrando en el tiempo, el volumen total erupciónado.
- Ejemplo Cordón Caulle 2011: la integración del VRP da una VRE (Volcanic Radiative Energy) de ~5.8 × 10¹⁵ J → traducible a ~10⁹ m³ de magma ácido (Coppola 2023).

**Post-erupción** — Mapear daños y cambios morfológicos.
- Calbuco abril 2015: comparación Sentinel-2 antes/después permitió mapear el alcance de flujos piroclásticos hacia el norte y la zona de pérdida glaciar.
- Chaitén mayo 2008: Landsat documentó la destrucción del bosque norte y el crecimiento del domo riolítico mes a mes.

### ¿Por qué no basta con mirar las imágenes?

Una respuesta corta: porque son demasiadas, vienen demasiado seguido, y los cambios sutiles son **subpixel** (más chicos que el píxel mismo).

- Copernicus-v1 monitorea 46 entidades con Sentinel-2 (5 días) + Landsat 8/9 (8 días combinados). Eso son ~13 escenas/semana procesables, ~700/año.
- Una fumarola nueva de 50 m² ocupa **1/4 de un pixel S2** (10 m × 10 m = 100 m²) y **0.05% de un pixel Landsat TIR** (100 m × 100 m). A ojo no se ve. El algoritmo sí la detecta porque mide la **mezcla espectral** dentro del píxel.

---

<a id="2"></a>
## 2. Físicamente, ¿qué estamos midiendo?

### Radiación reflejada vs radiación emitida

Todo cuerpo a temperatura > 0 K emite radiación electromagnética. La **longitud de onda dominante** depende de la temperatura, según la **Ley de desplazamiento de Wien**:

```
λ_max (µm) ≈ 2898 / T (K)
```

Aplicado a fenómenos volcánicos:

| Fenómeno | T típica | λ_max | Banda que mejor lo ve |
|---|---|---|---|
| Suelo a temperatura ambiente | 290 K (~17 °C) | ~10 µm | **TIR** (10–12 µm) |
| Fumarola tibia | 370 K (~100 °C) | ~7.8 µm | TIR |
| Fumarola caliente | 570 K (~300 °C) | ~5.1 µm | MIR (4 µm) |
| Domo en enfriamiento | 770 K (~500 °C) | ~3.8 µm | **MIR** (3.9 µm, MODIS) |
| Lago de lava | 1273 K (~1000 °C) | ~2.3 µm | **SWIR2** (2.2 µm) |
| Lava recién emitida | 1473 K (~1200 °C) | ~2.0 µm | **SWIR2** |

**Conclusión física fundamental**:
- Para cuerpos fríos (suelo, agua) → la mejor banda es TIR.
- Para cuerpos calientes (lava activa) → la mejor banda es SWIR (1.6–2.2 µm) o MIR (3.9 µm).
- Por eso MODVOLC/MIROVA usa MODIS-MIR: barre el rango de temperaturas eruptivas.

Pero **MODIS tiene resolución de 1 km**. Para volcanes con anomalías subpixel (Lascar, Lastarria, Tupungatito) eso es demasiado grueso. Ahí entra Sentinel-2.

### Por qué Sentinel-2 NO tiene TIR pero igual sirve

Sentinel-2 corta su rango espectral en B12 = 2.2 µm. No tiene banda térmica. Sin embargo, **el SWIR es un proxy excelente para detección de lava activa**, por dos razones físicas:

1. **La curva de Planck de un cuerpo a 1000 °C tiene un hombro pronunciado en 2 µm**. Mientras una piedra a 20 °C apenas emite a 2 µm, una lava a 1000 °C emite ahí ~10⁵ veces más. Esa diferencia hace que el SWIR sea **muy contrastado** para hot spots: pasás de "negro casi total" a "saturación total" en pocos píxeles.

2. **Resolución espacial**: B11 y B12 de Sentinel-2 son de **20 m**. Vs MODIS 1 km, ganás un factor 50× en cada eje, o **2500× en área**. Eso compensa con creces la falta de TIR para fenómenos calientes.

**Limitación**: el SWIR **NO** sirve para fumarolas tibias (<300 °C). Para eso necesitás TIR.

### Por qué Landsat 8/9 SÍ tiene TIR (B10) y para qué lo usamos

Landsat 8 y 9 llevan el sensor TIRS (Thermal Infrared Sensor) con dos bandas térmicas:

- **B10**: 10.6–11.2 µm, resolución nativa 100 m, remuestreada a 30 m.
- **B11**: 11.5–12.5 µm, resolución 100 m. **No la usamos** porque tiene "stray light" residual de 0.61 K (Barsi 2022) que contamina su calibración.

Usamos B10 de Landsat para:
- Detectar fumarolas tibias que el SWIR no ve.
- Calcular **brightness temperature** (Aguilera 2021, Eq. 7) para mapas de temperatura superficial absoluta.
- Estimar **flujo radiativo** vía Stefan-Boltzmann: `Q = ε · σ · T⁴ · A_pixel`.

Esto le da a Copernicus-v1 una capacidad que ni Sentinel-2 puro ni MODIS pueden ofrecer: **resolución intermedia (30 m) con calibración térmica absoluta**, ideal para los volcanes fumarólicos del norte de Chile (Lascar, Lastarria, San Pedro, Putana).

---

<a id="3"></a>
## 3. Bandas espectrales y qué detecta cada una

### Tabla maestra de bandas

| Banda | λ (µm) | Sentinel-2 | Landsat 8/9 | Resolución | Qué detecta | Caso típico volcán |
|---|---|---|---|---|---|---|
| Aerosoles | 0.44 | B01 (60 m) | B1 (30 m) | baja | Aerosoles, calidad atmosférica | Plumas SO₂/aerosol post-erupción |
| **Azul** | 0.49 | B02 (10 m) | B2 (30 m) | alta | Cuerpos de agua claros, atmósfera | Lagos cratéricos (Peteroa) |
| **Verde** | 0.56 | B03 (10 m) | B3 (30 m) | alta | Vegetación sana, nieve fresca | Glaciares (Hudson, Villarrica) |
| **Rojo** | 0.66 | B04 (10 m) | B4 (30 m) | alta | Vegetación estresada, suelos oxidados | Zonas de ceniza reciente |
| Red Edge | 0.70–0.78 | B05–B07 | — | media | Estrés vegetacional fino | Bosque envenenado por gases |
| **NIR** | 0.83 | B08 (10 m) | B5 (30 m) | alta | Vegetación viva (con B04 → **NDVI**) | Mapeo de zonas defoliadas |
| Vapor de agua | 0.945 | B09 (60 m) | — | baja | Contenido columnar de H₂O | — |
| Cirros | 1.375 | B10 (60 m) | B9 (30 m) | baja | Nubes cirros | Filtro de nubes finas |
| **SWIR1** | 1.6 | B11 (20 m) | B6 (30 m) | media | Humedad, nieve vs hielo, hot spots | Discriminar nieve/hielo en Hudson |
| **SWIR2** | 2.2 | B12 (20 m) | B7 (30 m) | media | Minerales arcillosos, **lava activa** | Lava lake Villarrica, anomalías Lascar |
| **TIR1** | 10.9 | ❌ | **B10** (100→30 m) | media | **Temperatura superficial** | Fumarolas tibias, calor difuso |
| TIR2 | 12.0 | ❌ | B11 (100→30 m) | media | T superficial (stray light) | **No usar sola** (Barsi 2022) |

### El composite RGB-multitemporal SWIR (B12-B11-B04)

Este es el "color thermal" que el equipo ya conoce del dashboard. Se construye así:

- Canal **rojo** ← B12 (SWIR2, 2.2 µm) — saturado donde hay lava o cuerpo muy caliente.
- Canal **verde** ← B11 (SWIR1, 1.6 µm) — sensible a calor moderado y humedad.
- Canal **azul** ← B04 (rojo visible) — contexto morfológico.

**Cómo leer la imagen**:

| Color en la imagen | Significado físico |
|---|---|
| **Rojo brillante saturado** | Lava activa / cuerpo a >700 °C / SWIR2 saturado |
| **Rojo-naranja** | Cuerpo caliente moderado (200–600 °C), fumarola intensa, anomalía térmica clara |
| **Amarillo-verde** | Vegetación viva (poca emisión SWIR, alta reflectancia visible) |
| **Azul-cian** | Cuerpos de agua, hielo, glaciar |
| **Blanco** | Nieve fresca (refleja en todo el espectro) |
| **Negro** | Sombra, agua profunda, lava enfriada |
| **Gris/marrón** | Suelo desnudo, roca expuesta |

**Punto crítico técnico** (lección aprendida del proyecto): el evalscript del thermal NO debe aplicar corrección gamma sRGB. La función sRGB es no-lineal y **aplana** los contrastes en las anomalías rojas — exactamente lo que querés preservar. Por eso usamos `[2.5*B12, 2.5*B11, 2.5*B04]` lineal (ver `config_sentinel2.py`).

### Índices derivados (NDVI, NBR, NDSI, NHI)

Los **índices normalizados** son cocientes diseñados para ser robustos a iluminación y atmósfera. Tienen la forma genérica `(A - B) / (A + B)`, lo que los acota en [-1, +1].

#### NDVI — Normalized Difference Vegetation Index

```
NDVI = (NIR - Red) / (NIR + Red) = (B08 - B04) / (B08 + B04)
```

- Rango típico: -1 (agua/nieve) hasta +1 (vegetación densa sana).
- Umbrales prácticos: <0.2 = sin vegetación, 0.2–0.5 = vegetación dispersa, >0.5 = bosque sano.
- **Uso volcanológico**: detectar **defoliación por ceniza** o **destrucción por flujo piroclástico**. Caída brusca de NDVI en píxeles antes vegetados = daño.

#### NBR — Normalized Burn Ratio

```
NBR = (NIR - SWIR2) / (NIR + SWIR2) = (B08 - B12) / (B08 + B12)
```

- Originalmente diseñado para incendios.
- **Uso volcanológico**: cuantificar severidad de daño por flujo piroclástico (dNBR = NBR_pre - NBR_post). Aplicable a Calbuco 2015, Chaitén 2008.

#### NDSI — Normalized Difference Snow Index

```
NDSI = (Green - SWIR1) / (Green + SWIR1) = (B03 - B11) / (B03 + B11)
```

- Umbral estándar: NDSI > 0.4 = píxel con nieve/hielo.
- **Uso crítico para Copernicus-v1**: enmascarar **falsos positivos térmicos** en volcanes con glaciar (Hudson, Villarrica, Lonquimay, Mocho-Choshuenco). La nieve fresca reflectiva puede dar señales SWIR altas que el algoritmo confunde con calor (Liu 2021). Aplicar máscara NDSI > 0.4 antes del análisis SWIR resuelve esto.

#### NHI — Normalized Hotspot Indices (Marchese 2019)

**Este es el índice más importante para nuestro proyecto** y el roadmap lo prioriza como "quick win" en Sprint 1.

```
NHI_SWIR  = (B12 - B11) / (B12 + B11)   ← detecta lava (>700°C)
NHI_SWNIR = (B12 - B8A) / (B12 + B8A)   ← detecta calor moderado
```

Hot spot = NHI_SWIR > 0 **AND** NHI_SWNIR > 0.

**¿Por qué es tan poderoso?**

1. Sentinel-2 y Landsat 8/9 tienen ambos bandas SWIR equivalentes (B11/B12 vs B6/B7). NHI funciona idénticamente en ambos → un mismo umbral homogeneiza la detección entre sensores.
2. La normalización lo hace robusto a variaciones de iluminación, ángulo solar y atmósfera.
3. Es **una operación matemática trivial** — no requiere matriz de covarianza ni serie temporal.
4. Marchese 2019 validó el umbral cero contra MODVOLC sobre 50+ volcanes globales con ~15% de falsos positivos (bajísimo para detección automática).

### El composite Landsat (RGB, SWIR, THERMAL)

Para Landsat 8/9 el dashboard tiene 3 composites con propósitos distintos:

| Composite | Bandas | Para qué | Rango interpretativo |
|---|---|---|---|
| **RGB** | B4-B3-B2 | Color natural, contexto morfológico | — |
| **SWIR** | B7-B6-B4 | Anomalías intensas (>300 °C) | Azul = nieve/hielo · Rojo = calor |
| **THERMAL** | B10 monocanal | Temperatura superficial difusa | -20 °C → 80 °C |

El THERMAL es lo único que ningún otro sensor del proyecto provee, y es **insustituible** para fumarolas tibias del norte de Chile.

---

<a id="4"></a>
## 4. Algoritmos clásicos vs modernos

Esta sección es la columna vertebral del documento. Hay decenas de algoritmos publicados desde los años 80; los agrupamos en tres familias conceptuales y una cuarta moderna (deep learning).

### 4.1 Algoritmos clásicos (1980s–2010s)

Estos son los métodos básicos. Son rápidos, interpretables, y siguen siendo la base de todo sistema operacional.

#### Image differencing — la idea más simple

```
Δ = A - B   (píxel a píxel, banda por banda)
```

- Si |Δ| > umbral → cambio.
- **Ventaja**: trivial, calculable en milisegundos.
- **Desventaja**: ruidoso. Cualquier cambio de iluminación, nube fina, sombra topográfica, dispara falsos positivos.
- Howarth & Wickware 1981 es la referencia original.

#### Image ratioing — normaliza iluminación

```
ρ = A / B
```

- Si ρ ≠ 1 → cambio.
- **Ventaja**: insensible a multiplicaciones globales de brillo (cambio de iluminación).
- **Desventaja**: indeterminado cerca de B=0 (sombras, agua oscura).

#### Change Vector Analysis (CVA) — magnitud y dirección

Cada píxel se representa como un **vector en el espacio multibanda** (R, G, B, NIR, SWIR...). La diferencia entre fechas también es un vector:

```
v_cambio = (R_B - R_A, G_B - G_A, ..., SWIR_B - SWIR_A)
|v_cambio| = magnitud del cambio
θ(v_cambio) = dirección (qué bandas dominan)
```

- **Ventaja**: distingue **qué tipo de cambio** ocurrió (vegetación cayó vs apareció calor) por la dirección del vector.
- Bovolo & Bruzzone 2007 formalizó la versión polar del CVA.

#### PCA multitemporal — encuentra los patrones dominantes

Aplica análisis de componentes principales al **stack temporal** de imágenes. Los primeros componentes capturan la variabilidad estacional "normal"; los últimos componentes capturan los **cambios anómalos**.

- **Ventaja**: separa señal real de ruido cíclico.
- **Desventaja**: requiere serie temporal larga (>20 fechas) y los componentes son difíciles de interpretar.

### 4.2 Algoritmos estadísticos

#### Z-score por banda — lo que usamos hoy

Para cada píxel y cada banda, mantener un histórico (mediana móvil + desviación estándar) y preguntar:

```
z = (valor_actual - mediana_historica) / sigma_historica
si z > 2.0 AND porcentaje_pixeles_anomalos > 1% → ATENCION
si z > 3.0 AND porcentaje_pixeles_anomalos > 3% → ALERTA
```

- **Esto es exactamente la lógica de `change_analysis.py`** y produce el JSON de estado actual (40 NORMAL · 6 ATENCION · 0 ALERTA, mayo 2026).
- **Ventaja**: cada píxel es su propia referencia → adapta a la baseline natural del volcán.
- **Desventaja**: ignora correlaciones entre bandas. Un cambio coherente en B11 + B12 (firma de calor) y un cambio incoherente (nube fina afectando una banda más que otra) reciben el mismo z-score.

#### Distancia de Mahalanobis — mejora propuesta

Igual concepto que z-score, pero usa la **matriz de covarianza** entre bandas. Penaliza más fuerte cambios que son anómalos en una combinación de bandas, no solo en una.

```
d_M = sqrt( (x - μ)ᵀ · Σ⁻¹ · (x - μ) )
```

- **Ventaja**: detecta firmas multibanda coherentes, reduce falsos positivos por nube/sombra.
- **Implementación**: trivial con `scipy.spatial.distance.mahalanobis()`. Próximo Sprint.

### 4.3 Análisis de series temporales

#### BFAST — Breakpoint detection

Modela la serie temporal como tendencia + estacionalidad + ruido, y busca **breakpoints** donde la tendencia o estacionalidad cambian abruptamente.

- Verbesselt et al. 2010.
- Usado en silvicultura, transferible a volcanes con baseline estable.

#### CCDC — Continuous Change Detection and Classification

Modela cada píxel como una **función armónica continua**:

```
y(t) = c0 + c1·cos(2πt/T) + c2·sin(2πt/T) + ruido
```

Detecta cambios solo cuando los residuos exceden el umbral **por 3+ observaciones consecutivas**.

- Zhu 2014.
- **Aplicabilidad directa a Copernicus-v1**: formaliza la "regla de consistencia multi-frame" que ya intuimos. Hoy decimos "necesito ver la anomalía en 2 fechas seguidas para creer"; CCDC lo hace cuantitativamente.

#### LandTrendr — segmentación de tendencias

Encuentra los **vértices** (puntos de quiebre) que mejor describen la serie como una secuencia de segmentos lineales.

- Kennedy 2010.
- Excelente para visualizar trayectorias largas (>10 años).

### 4.4 Algoritmos específicos de volcanología

Estos están diseñados desde cero para detección de hot spots volcánicos. Son los que producen los sistemas operacionales mundiales.

#### MODVOLC (Wright 2004) — el padre fundador

Sistema operacional global de la Universidad de Hawaii. Algoritmo:

```python
# Bandas MODIS: B22 (MIR 3.9 µm), B32 (TIR 12 µm)
NTI = (L_22 - L_32) / (L_22 + L_32)   # Normalized Thermal Index
hot_spot = (NTI > -0.80) AND (solo_nocturno)
```

- Umbral global empírico **-0.80** validado contra >100 escenas.
- Operacional 24/7 desde 2002 sobre todos los volcanes del mundo.
- **Limitación crítica**: no funciona con Sentinel-2 (S2 no tiene MIR a 3.9 µm). Solo MODIS/VIIRS.

**Para Lascar (Chile)**: en 573 días Wright 2004 reportó solo 5 hot spots. La actividad fumarólica de Lascar es **subpixel para MODIS** (resolución 1 km).

#### MIROVA (Coppola 2019) — el referente actual

Es el sistema que SERNAGEOMIN consume hoy. Extensión sofisticada de MODVOLC:

1. Resample MODIS a grilla UTM 50×50 km, píxel 1×1 km (elimina distorsión bow-tie).
2. Combina NTI + ETI (Enhanced Thermal Index).
3. Aplica **filtro contextual espacial**: umbrales más bajos cerca del summit, más altos lejos.
4. Calcula **VRP** (Volcanic Radiative Power) en Watts vía Wooster 2003:

```
VRP = 18.9 · A_pix · Σ(L_MIR_hot - L_MIR_background)
```

5. Reporta en escala log con 5 niveles de color: Low / Medium / High / Very High / Extreme.

**Sensibilidad mínima**: 1 MW (equivalente a un vent de 7 m² a 1000 °C, o una fumarola de 143 m² a 300 °C).

**Rango operacional**: 5 órdenes de magnitud, desde 1 MW hasta 50 GW.

**Volcanes chilenos en MIROVA** (Coppola 2023, base de datos 2000–2019):
- **Lascar**: intermediate, persistencia >70%, VRE histórica moderada.
- **Llaima**: intermediate, caso "rise of magmatic column" pre-2008.
- **Chaitén**: acid, VRE = 6.2 × 10¹⁵ J (primer ácido más energético del catálogo global).
- **Puyehue-Cordón Caulle**: acid, VRE = 5.8 × 10¹⁵ J.
- **Villarrica**: basic, lago de lava intermitente.

Toda la base de datos MIROVA está **disponible públicamente** en https://osf.io/zm62w/ — incluye los time-series VRP por volcán que SERNAGEOMIN puede descargar directo.

#### NHI (Marchese 2019) — el más práctico para nosotros

Ya descrito en sección 3.5. Recapitulando lo crítico:

```
NHI_SWIR  = (B12 - B11) / (B12 + B11)
NHI_SWNIR = (B12 - B8A) / (B12 + B8A)
hot_spot = NHI_SWIR > 0 AND NHI_SWNIR > 0
```

**Por qué es la prioridad #1 de implementación** (ver `IMPLEMENTACION.md`):
- Homogeniza Sentinel-2 + Landsat 8/9 con un mismo umbral cero.
- ~15% falsos positivos sobre 50+ volcanes globales (Marchese 2019, validación).
- Trivial de calcular con las bandas que ya descargamos.
- Output directamente comparable con la literatura mundial.

### 4.5 Algoritmos modernos (Deep Learning, 2018+)

Esta familia es la "frontera" actual. Requiere datasets etiquetados, GPU y mucha experiencia técnica, pero los resultados son superiores en escenarios complejos.

#### Siamese Networks

Dos ramas idénticas de red neuronal, una procesa la imagen T1 y la otra T2. Una capa final compara las dos representaciones latentes.

- Kang 2022 (Siamese U-Net) para change detection genérico.

#### BIT Transformer (Chen 2021)

State-of-the-art actual en change detection genérico. Aplica self-attention al par de imágenes para identificar regiones de cambio relevantes.

- F1-score >0.90 en LEVIR-CD (dataset benchmark).

#### Aplicaciones específicas a volcanología

- **Anantrasirichai 2022, 2024**: autoencoders sobre interferogramas Sentinel-1 para detectar deformación volcánica anómala. CNN entrenada con 500.000 interferogramas globales (Gaddes 2022).
- **Murphy 2023** (ASTER Deep Learning): detección de hot spots ASTER con CNN — mejora vs umbrales clásicos.

**Estado en Copernicus-v1**: el roadmap prevé fase deep learning como **Sprint 3** (alto esfuerzo). El pre-requisito es haber acumulado un dataset etiquetado de casos chilenos (Calbuco 2015, Cordón Caulle 2011, Chillán 2008+, Villarrica 2015) que sirva como fine-tuning sobre modelos pre-entrenados.

### 4.6 Lección crítica: el voto por consenso

Steffke & Harris 2011 (review fundacional) clasificaron los algoritmos en **tres familias**:

1. **Fixed-threshold** (MODVOLC, NHI)
2. **Contextual** (VAST: pixel vs vecindario espacial)
3. **Temporal** (RST: pixel vs su propia historia)

**Conclusión del review**: ningún algoritmo solo es óptimo. La práctica moderna (MIROVA, MOUNTS) es **correr los tres en paralelo** y declarar hot spot solo si **≥2 familias coinciden**.

Esta es la arquitectura propuesta para Copernicus-v1 Sprint 2:

```
Para cada (volcán, fecha):
  1. Fixed:      NHI_SWIR > 0
  2. Contextual: B12 > mean(ventana_7x7) + 3·sigma
  3. Temporal:   B12 > mediana(historico_12_fechas) + 3·MAD
  4. HOT_PIXEL = vote >= 2 of 3
```

Reduce falsos positivos sin sacrificar sensibilidad.

---

<a id="5"></a>
## 5. Sistemas operacionales en el mundo

Estos son los grandes sistemas que producen alertas térmicas en tiempo real. Conocerlos te permite saber **con qué nos estamos comparando** y dónde Copernicus-v1 aporta valor diferencial.

### MIROVA — Università di Torino + INGV (Italia)

- **Sensor**: MODIS Terra + Aqua + VIIRS (en algunas versiones).
- **Banda primaria**: MIR (3.9 µm), método NTI + ETI.
- **Resolución**: 1 km (limitación intrínseca de MODIS).
- **Cobertura**: 216 volcanes globales, archivo desde 2000.
- **Latencia**: 1–4 horas post-adquisición.
- **Output**: VRP en Watts, mapa de hot spots, time-series web.
- **17 observatorios usuarios**, incluyendo **SERNAGEOMIN/Chile** (Bucarey Parra, Lara, Coppola 2019 Tabla S2).
- **URL**: https://www.mirovaweb.it

**Limitación clave para Chile**: la resolución de 1 km **no detecta los volcanes fumarólicos del norte chileno**. Murphy 2013 lo demostró cuantitativamente con Lascar: en 11 años, MODIS prácticamente no lo registra, mientras ASTER (90 m TIR) lo detecta rutinariamente con áreas anómalas de 10.000–40.000 m².

### MOUNTS — DLR (Alemania)

- **Acrónimo**: Monitoring Unrest from Space.
- **Multi-sensor**: Sentinel-1 SAR + Sentinel-2 óptico + Sentinel-5P TROPOMI (SO₂) + MODIS térmico.
- **Innovación**: fusión multi-sensor automática + alertas semanales en panel web.
- **Cobertura**: ~30 volcanes prioritarios.
- **Validación**: Valade et al. 2019 lo aplica a Erta Ale, Anak Krakatau, Stromboli.

Es **el modelo arquitectónico a replicar** para Copernicus-v1 Fase 2 (cuando incorporemos SAR).

### MODVOLC — University of Hawaii

- **Sensor**: MODIS (igual que MIROVA pero algoritmo más simple).
- **Cobertura**: global, todos los volcanes.
- **Latencia**: <24h.
- **URL**: http://modis.higp.hawaii.edu
- **Wright et al. 2002, 2004** — referencia fundacional.

Más antiguo y menos sofisticado que MIROVA, pero aún operacional. Su valor está en el **archivo histórico continuo desde 2000**, útil para validación retrospectiva.

### AVTOD — Cornell University

- **Acrónimo**: Andean Volcano Thermal Output Database.
- **Foco**: catálogo retrospectivo de **volcanes latinoamericanos** con MODIS + ASTER.
- **Cobertura**: incluye prácticamente todos los volcanes activos de Copernicus-v1.
- **Reath 2019** — referencia.
- **Valor para nosotros**: **dataset de validación cruzada**. Si Copernicus-v1 detecta algo, podemos confirmar contra AVTOD; si AVTOD reportó algo histórico, podemos buscar firmas en nuestras imágenes.

### VOLCANOMS — Universidad Católica del Norte (Chile)

- **Acrónimo**: VOLCAN Observation and Monitoring System.
- **Plataforma**: VIPS (Volcanic Imagery Processing Software), software desarrollado en UCN.
- **Foco**: balance energético completo (Qsun + Qatm + Qrad + Qevap + Qcond + Qrain → despeja Qvolc).
- **Volcanes**: Lascar, Lastarria, San Pedro, Putana, Peteroa, Tupungatito.
- **Layana 2020, Aguilera 2021** — papers fundacionales.
- **Contactos**: Felipe Aguilera (`feaguilera@ucn.cl`), Susana Layana.

Es el **único antecedente nacional chileno** del proyecto Copernicus-v1. Recomendación del roadmap: **coordinar con UCN** para reusar dataset, intercambiar metodología y validar cruzadamente.

### NHI Tool — Università della Basilicata (Italia)

- Implementación de NHI (Marchese 2019) en **Google Earth Engine**.
- Procesa Sentinel-2 + Landsat 8/9 con un mismo umbral.
- ~15% falsos positivos validados globalmente.
- **Reproducible**: el código GEE está publicado. Podemos replicar idéntico en Copernicus-v1 sin dependencias propietarias.

### Comparación resumida

| Sistema | Sensor | Resolución | Latencia | Cobertura | Output |
|---|---|---|---|---|---|
| MIROVA | MODIS MIR | 1 km | 1–4 h | 216 volcanes globales | VRP en W |
| MOUNTS | S1+S2+S5P+MODIS | 10 m – 1 km | semanal | ~30 volcanes | Multi-señal |
| MODVOLC | MODIS MIR | 1 km | <24 h | global todos | NTI hot spots |
| AVTOD | MODIS+ASTER | 90 m – 1 km | histórico | Latam | Catálogo |
| VOLCANOMS | Landsat TIR | 30/100 m | manual | ~6 volcanes Chile N | Qvolc balance |
| NHI Tool | S2+L8/9 SWIR | 20–30 m | depende usuario | global on-demand | NHI flag |
| **Copernicus-v1** | **S2+L8/9** | **10–30 m** | **2×día** | **46 entidades Chile** | **Cambio + thermal + composites** |

---

<a id="6"></a>
## 6. El caso de Chile: nuestro sistema vs MIROVA

### Qué hace Copernicus-v1 hoy

- **46 entidades monitoreadas**: 43 volcanes chilenos + 3 vistas zoom específicas (Melimoyu Conos Eruptivos, Mentolat Sismicidad VT, Hudson Última Erupción).
- **Dos sensores complementarios**:
  - Sentinel-2 (10 m RGB, 20 m SWIR) — frecuencia 5 días por satélite, ~1.7–4.6 días combinados con la constelación S2A+S2B+S2C.
  - Landsat 8/9 (30 m RGB/SWIR, 100→30 m TIR) — frecuencia 8 días combinados.
- **Hora de paso sobre Chile** (empírico, 1526 observaciones): 10:43–10:55 hora Chile, prácticamente constante.
- **Disponibilidad L2A**: 6–12 h después del paso.
- **Composites generados automáticamente**: RGB color natural, ThermalFalseColor (B12-B11-B04), SWIR Landsat (B7-B6-B4), THERMAL Landsat (B10).
- **Estado actual** (mayo 2026, 46 volcanes analizados): 40 NORMAL · 6 ATENCION · 0 ALERTA. En ATENCION: Cay, Hudson, Maca, Ollague, Parinacota, Tupungatito (todos por anomalía térmica).

### Frecuencia combinada por volcán (3 satélites Sentinel-2)

Empírico de los 1526 pasos analizados (Coppola 2019 + nuestras observaciones):

| Volcán | Días entre pasos S2 (combinado) | Comentario |
|---|---|---|
| Villarrica, Melimoyu | 2.3 d | Mejor cobertura (paths cruzados) |
| Mayoría SVZ | 3–4 d | Cobertura típica |
| Hudson | 4.1 d | |
| Lascar | 4.6 d | Path único, una pasada cada 5 |

### Ventajas sobre MIROVA

**Ventaja #1: resolución espacial 100× mayor (área).**

| | MIROVA | Copernicus-v1 |
|---|---|---|
| Píxel térmico | 1000 × 1000 m | 20 × 20 m (S2 SWIR) o 30 × 30 m (L8/9) |
| Área por píxel | 1.000.000 m² | 400–900 m² |
| Anomalía mínima detectable | ~7 m² @ 1000 °C (subpixel MODIS, ~10⁻⁵) | ~50 m² @ 1000 °C dentro de 1 píxel S2 |

Esto se traduce **directamente** en capacidad para detectar:
- Fumarolas pequeñas (Lascar, Lastarria) que MODIS pierde.
- Comienzo subpixel de lago de lava (Villarrica) antes que sea visible térmicamente.
- Cráteres anidados de complejos volcánicos (Planchón-Peteroa-Azufre 4 cráteres).

**Ventaja #2: validación cruzada con literatura UCN/SERNAGEOMIN.**

Peteroa 2018: Aguilera et al. 2021 detectaron la anomalía SWIR en Landsat 8 el 6 de diciembre, 4 semanas antes de la erupción del 14 enero 2019. **Esa misma escena Landsat la captura Copernicus-v1 hoy de forma automática.**

**Ventaja #3: composites diferenciados por propósito.**

MIROVA da un solo número (VRP) por fecha. Copernicus-v1 da el composite RGB para inspección morfológica, el ThermalFalseColor para interpretación visual rápida, y el THERMAL Landsat con calibración de temperatura absoluta para fumarolas frías.

### Limitaciones vs MIROVA (a corregir en próximos Sprints)

**Limitación #1: no calculamos VRP en Watts todavía.**

MIROVA reporta `VRP = 18.9 · A_pix · L_MIR_hot` directamente comparable con literatura mundial. Copernicus-v1 reporta z-score, % de píxeles anómalos y un nivel de alerta — útil para nosotros pero **no convertible** a Watts sin más cálculo.

**Solución roadmap (Sprint 1)**: implementar un **VRP_proxy_SWIR** vía bandas Sentinel-2 B11/B12. Calibrar empíricamente contra MIROVA-MODIS sobre fechas coincidentes en Lascar, Copahue, Villarrica, Nevados de Chillán, Lonquimay (todos esos están en MIROVA).

**Limitación #2: no calculamos TADR (tasa efusiva en m³/s).**

Para volcanes efusivos (Hudson, Cordón Caulle pre-2011) MIROVA convierte VRP → TADR vía:

```
TADR = VRP / c_rad
```

donde `c_rad` depende de la composición magmática:
- Basáltica: 1–4 × 10⁸ J/m³
- Intermedia: 1.5–9 × 10⁷ J/m³
- Ácida: 2–10 × 10⁶ J/m³

**Solución roadmap**: tabla de composición SiO₂ por volcán chileno + módulo `tadr_calculator.py`.

**Limitación #3: única referencia temporal es el píxel mismo.**

MIROVA tiene 20+ años de archivo continuo. Copernicus-v1 tiene ~2 años de S2 + ~1 año de L8/9. Para baseline robusto necesitamos integrar la base MIROVA pre-Sentinel-2 (2000–2015) como referencia retrospectiva.

### Tabla resumen: Copernicus-v1 vs MIROVA por caso de uso

| Caso de uso | MIROVA gana | Copernicus-v1 gana | Empate |
|---|---|---|---|
| Erupción efusiva grande (lava) | ✅ (VRP en W, TADR establecido) | | |
| Fumarola subpixel chilena (Lascar, Lastarria) | | ✅ (resolución 30× mayor) | |
| Domo en crecimiento (Chaitén-like) | | ✅ (morfología visible) | |
| Lago de lava persistente (Villarrica) | | | ✅ |
| Pre-erupción térmica sutil (Peteroa 2018) | | ✅ (Landsat SWIR alta-res) | |
| Cobertura nocturna | ✅ (MODIS pasa también de noche) | | |
| Eventos cortos (<6 h) | ✅ (4 obs/día MODIS Terra+Aqua) | | |
| Archivo histórico >5 años | ✅ (desde 2000) | | |
| Mapeo morfológico post-erupción | | ✅ (RGB 10 m) | |
| Detección SO₂ atmosférico | ❌ (no aplica) | ❌ (no aplica) | TROPOMI/S5P |

**Conclusión estratégica**: Copernicus-v1 **complementa** a MIROVA, no lo reemplaza. La estrategia óptima para SERNAGEOMIN es **mirar los dos**: MIROVA para latencia rápida y eventos energéticos grandes; Copernicus-v1 para resolución espacial fina, fumarolas subpixel chilenas y contexto morfológico.

---

<a id="7"></a>
## 7. Limitaciones reales del enfoque óptico

Es crítico ser honestos sobre lo que un sistema óptico Sentinel-2/Landsat **no puede hacer**.

### Limitación #1: Nubosidad

En la SVZ chilena (sur de paralelo 38°S) la cobertura nubosa es 30–50% del tiempo. Aguilera 2021 reportó **33% de escenas Landsat descartadas** sobre Peteroa por nubes (400 de 1208 imágenes en 36 años).

**Implicación**: las series temporales tienen huecos sistemáticos. Un volcán como Hudson, Melimoyu o Aguilera puede pasar 2–3 semanas sin ninguna escena clara.

**Mitigaciones disponibles**:
- Usar Sentinel-2 + Landsat 8/9 combinados (frecuencia efectiva 2–3 días).
- Filtrar con SCL (Scene Classification Layer) y reportar **gaps explícitamente** en el dashboard.
- Combinar con **Sentinel-1 SAR** (radar, all-weather) en una capa adicional — roadmap Sprint 3.

### Limitación #2: Hora de paso fija

Sentinel-2 pasa sobre Chile entre 10:43 y 10:55 hora local. Landsat 8/9 entre 10:30 y 10:50. **Eventos nocturnos no se capturan ópticamente**. Si una erupción inicia a las 22:00 y termina a las 06:00, no la vemos hasta el siguiente día.

**Mitigaciones**:
- MIROVA (MODIS) sí pasa de noche — combinar fuentes.
- Sentinel-5P (TROPOMI) tiene SO₂ con barridos más frecuentes — útil para detectar plumas eruptivas independiente de la hora.

### Limitación #3: Frecuencia limitada

Por satélite individual, Sentinel-2 vuelve cada 5 días, Landsat cada 16. Con constelaciones combinadas bajamos a 1.7–4.6 días.

**Eventos cortos** (strombolianas de minutos a horas) **se pierden** entre pasos.

Wright 2004 lo documentó para Stromboli: pese a strombolianas ~10/h, MODVOLC detectó solo 2 alertas en 19 meses. La energía por evento individual era insuficiente para subir el NTI por encima del umbral, y MODIS no pasaba en el momento exacto.

### Limitación #4: No penetra nubes ni vegetación densa

Las bandas ópticas (visible, NIR, SWIR, TIR) son **bloqueadas por nubes opacas y dosel vegetal**. Para penetrar necesitas radar (Sentinel-1 SAR, banda C, 5.4 GHz).

**Implicación**: en volcanes con vegetación densa al sur (Hornopirén, Yate, Melimoyu) las fumarolas freatomagmáticas tempranas pueden no ser visibles ópticamente.

### Limitación #5: Saturación a temperaturas magmáticas

Las bandas SWIR de Sentinel-2 saturan a reflectancia > 1.0 cuando hay lava activa intensa. Eso significa que **no podés cuantificar** la temperatura de una lava muy caliente con S2 — solo confirmar que está ahí.

Landsat 8/9 B10 (TIR) también satura, pero más tarde. Solución: usar **SWIR (B6/B7) cuando hay lava magmática (>700 °C)**, TIR (B10) cuando hay calor moderado (<300 °C). El equipo ya lo hace.

### Limitación #6: Plumas de ceniza atenúan la señal

Wright 2004 advierte: durante una erupción explosiva, la **pluma de ceniza atenúa la radiancia infrarroja** del cuerpo caliente abajo. Resultado: aparente "fin de erupción" en el monitoreo cuando en realidad la actividad continúa.

**Mitigación**: cruzar siempre con observaciones complementarias (cámaras SERNAGEOMIN OVDAS, sismicidad, deformación).

### Limitación #7: Ningún algoritmo es perfecto

Steffke & Harris 2011 concluyen:

> *"As the number of correctly identified anomalies increases, so too does the number of false positives. No algorithm can be expected to perform perfectly under current data restraints."*

Siempre habrá trade-off precision/recall. El umbral cero de NHI da ~15% falsos positivos globales. Si lo bajamos a -0.1 capturamos más, pero subimos falsos positivos. Si lo subimos a +0.1, perdemos detecciones reales.

**Implicación operacional**: el sistema satelital es un **filtro de atención**, no un sustituto del análisis humano. Toda alerta debe ser **revisada por un geólogo** antes de comunicarse externamente.

---

<a id="8"></a>
## 8. Glosario de términos clave

### Índices y métricas

- **NDVI** (Normalized Difference Vegetation Index): `(NIR - Red) / (NIR + Red)`. Mide salud vegetal. Rango [-1, +1]. Vegetación sana > 0.5.
- **NBR** (Normalized Burn Ratio): `(NIR - SWIR2) / (NIR + SWIR2)`. Mide severidad de quema. dNBR = NBR_pre - NBR_post cuantifica daño.
- **NDSI** (Normalized Difference Snow Index): `(Green - SWIR1) / (Green + SWIR1)`. > 0.4 indica nieve/hielo. Crítico para enmascarar glaciares.
- **NHI** (Normalized Hotspot Indices, Marchese 2019): `(B12-B11)/(B12+B11)` y `(B12-B8A)/(B12+B8A)`. > 0 indica hot spot SWIR. **El índice prioritario para Copernicus-v1.**
- **NTI** (Normalized Thermal Index, Wright 2002): `(L_MIR - L_TIR) / (L_MIR + L_TIR)`. Base de MODVOLC. Umbral global -0.80.
- **VRP** (Volcanic Radiative Power, Coppola 2016): potencia radiativa volcánica en Watts. `VRP = 18.9 · A_pix · L_MIR`.
- **VRE** (Volcanic Radiative Energy): integral del VRP en el tiempo, en Joules. `VRE = ∫ VRP dt`.
- **TADR** (Time-Averaged Discharge Rate): tasa efusiva promedio en m³/s. `TADR = VRP / c_rad`.
- **LST** (Land Surface Temperature): temperatura superficial absoluta en K, derivada de TIR.
- **dNHI**, **dNDVI**, etc.: la "d" prefija indica **diferencia bi-temporal** (post menos pre).

### Bandas espectrales

- **VIS** (Visible): 0.4–0.7 µm. Azul, verde, rojo.
- **NIR** (Near InfraRed): 0.7–1.3 µm. Sensible a vegetación.
- **SWIR** (Short-Wave InfraRed): 1.3–2.5 µm. Crítico para detección de calor volcánico.
- **MIR** (Mid InfraRed): 3–5 µm. Banda óptima para lava (~1000 °C). MODIS la tiene, Sentinel-2 y Landsat no.
- **TIR** (Thermal InfraRed): 8–14 µm. Temperatura superficial. Landsat sí, Sentinel-2 no.

### Productos y procesamiento

- **L1C** (Top of Atmosphere, ToA): producto Sentinel-2 sin corrección atmosférica. Reflectancia "vista desde el satélite".
- **L2A** (Bottom of Atmosphere, BoA): producto Sentinel-2 con corrección atmosférica. Reflectancia superficial. **Lo que usamos en Copernicus-v1.**
- **SCL** (Scene Classification Layer): capa de máscara del producto L2A que clasifica cada píxel (no_data / sombras / nubes / vegetación / etc.). Valores 8, 9, 10, 11 = nubes/cirros → descartar.
- **L1B** (Landsat): producto crudo radiométricamente calibrado.
- **TIRS** (Thermal Infrared Sensor): el instrumento térmico de Landsat 8/9.
- **OLI** (Operational Land Imager): el instrumento óptico de Landsat 8/9.
- **MSI** (MultiSpectral Instrument): el instrumento de Sentinel-2.

### Catálogos y estándares

- **STAC** (SpatioTemporal Asset Catalog): estándar de metadata para catálogos de imágenes satelitales. Soportado por Microsoft Planetary Computer, Copernicus Data Space.
- **COG** (Cloud Optimized GeoTIFF): formato GeoTIFF optimizado para acceso parcial vía HTTP. El visor `cog_viewer.html` lo usa.
- **MGRS** (Military Grid Reference System): sistema de tiles 100×100 km de Sentinel-2.

### Volcanología satelital

- **Hot spot**: píxel con anomalía térmica detectada por algún algoritmo.
- **Subpixel**: feature más chica que el píxel; afecta la señal pero no es resolvible espacialmente.
- **Stray light**: contaminación lumínica en una banda del sensor desde luz fuera del campo. B11 de Landsat TIRS sufre 0.61 K residual (Barsi 2022).
- **Cripto-domo**: domo endógeno que crece sin emerger a superficie. **No detectable térmicamente con MODIS** (Lascar, Colima pre-2002).
- **VEI** (Volcanic Explosivity Index): escala 0–8 de explosividad eruptiva.
- **VTF** (Volcanic Thermal Feature): cualquier feature térmica volcánica (lava, fumarola, lago de lava, domo caliente).

### Sistemas y observatorios

- **OVDAS**: Observatorio Volcanológico de los Andes del Sur, SERNAGEOMIN, Temuco.
- **CIGIDEN**: Centro de Investigación para la Gestión Integrada del Riesgo de Desastres, Chile.
- **Ckelar Volcanes**: Núcleo de Investigación en Riesgo Volcánico, UCN Antofagasta.
- **OAVV**: Observatorio Argentino de Vigilancia Volcánica, SEGEMAR-CONICET.
- **GVP**: Global Volcanism Program (Smithsonian).
- **INGV**: Istituto Nazionale di Geofisica e Vulcanologia (Italia).

---

<a id="9"></a>
## 9. Lecturas recomendadas

Ordenadas por dificultad creciente. Para cada una se indica el archivo PDF si está disponible localmente.

### Nivel introductorio

**1. Aguilera, Caro & Layana 2021** — *The Evolution of Peteroa Volcano Crater Lakes 1984–2020*
- Frontiers in Earth Science 9:722056 · DOI: 10.3389/feart.2021.722056
- 📄 `bibliografia/pdfs/Aguilera2022_Peteroa_Lakes.pdf`
- **Por qué empezar acá**: autores chilenos (UCN), en castellano técnico accesible, validación contra mediciones in-situ, fórmulas completas para Landsat TIR.

**2. Coppola et al. 2019** — *Thermal Remote Sensing for Global Volcano Monitoring: Experiences From the MIROVA System*
- Frontiers in Earth Science 7:362 · DOI: 10.3389/feart.2019.00362
- 📄 `bibliografia/pdfs/Coppola2019_MIROVA.pdf`
- **Por qué leerlo**: paper fundacional de MIROVA, el sistema que SERNAGEOMIN consume. Explica la arquitectura, casos arquetipos de "thermal unrest pre-VEI3" (Llaima incluido), niveles VRP Low/Med/High/Very High/Extreme.

**3. Marchese et al. 2019** — *A Multi-Channel Algorithm for Mapping Volcanic Thermal Anomalies by Means of Sentinel-2 MSI and Landsat-8 OLI Data*
- Remote Sensing 11(23):2876 · DOI: 10.3390/rs11232876
- ❌ PDF pendiente (MDPI bloqueado por curl, bajar manualmente)
- **Por qué crítico**: define **NHI**, el índice que vamos a implementar en Sprint 1. Homogeniza S2 + L8/9 con un único umbral.

### Nivel intermedio

**4. Wright et al. 2004** — *MODVOLC: near-real-time thermal monitoring of global volcanism*
- JVGR 135:29–49 · DOI: 10.1016/j.jvolgeores.2003.12.008
- 📄 `bibliografia/pdfs/Wright_2004_MODVOLC.pdf`
- **Por qué leerlo**: el clásico fundacional del monitoreo global. Define NTI > -0.80. Operacional desde 2002.

**5. Massimetti et al. 2020** — *Volcanic Hot-Spot Detection Using SENTINEL-2: A Comparison With MODIS–MIROVA Thermal Data Series*
- Remote Sensing 12(5):820 · DOI: 10.3390/rs12050820
- ❌ PDF pendiente (MDPI)
- **Por qué crítico**: adapta NHI a Sentinel-2 con umbrales calibrados. Es el benchmark global para detección S2. Pendiente de bajar manualmente.

**6. Valade et al. 2019** — *Towards Global Volcano Monitoring Using Multisensor Sentinel Missions and Artificial Intelligence: The MOUNTS Monitoring System*
- Remote Sensing 11(13):1528 · DOI: 10.3390/rs11131528
- ❌ PDF pendiente (MDPI)
- **Por qué leerlo**: arquitectura multi-sensor (SAR + óptico + TROPOMI) que queremos replicar en Sprint 3.

### Nivel avanzado

**7. Coppola et al. 2023** — *Global radiant flux from active volcanoes: the 2000–2019 MIROVA database*
- Frontiers in Earth Science 11:1240107 · DOI: 10.3389/feart.2023.1240107
- 📄 `bibliografia/pdfs/Coppola_2023_GlobalRadiantFlux_MIROVA.pdf`
- **Por qué leerlo**: catálogo global de referencia, define VRE formalmente, fórmula `VRE = Vol · c_rad`, niveles térmicos, ranking global. Base de datos descargable en https://osf.io/zm62w/.

**8. Murphy et al. 2013** — *MODIS and ASTER synergy for characterizing thermal volcanic activity*
- RSE 131:195–205 · DOI: 10.1016/j.rse.2012.12.005
- 📄 `bibliografia/pdfs/Pieri_Abrams_2004_ASTER_volcanoes.pdf` (filename engañoso, contiene Murphy 2013)
- **Por qué crítico**: estudia Lascar (Chile) y demuestra cuantitativamente que MODIS no lo detecta. Es la **justificación científica** del valor de Copernicus-v1 sobre MIROVA para volcanes fumarólicos chilenos.

**9. Liu et al. 2021** — *High-temperature Sentinel-2 hot spot detection over volcanic glaciated environments*
- ISPRS J. Photogramm. Remote Sens. · DOI: 10.1016/j.isprsjprs.2021.05.008
- ❌ PDF pendiente (Elsevier paywall, usar VPN institucional)
- **Por qué leerlo**: específicamente sobre cómo detectar hot spots cuando hay glaciar (Hudson, Villarrica, Lonquimay, Mocho).

**10. Chen et al. 2021** — *Remote Sensing Image Change Detection with Transformers (BIT)*
- IEEE TGRS · DOI: 10.1109/TGRS.2021.3095166
- 📄 `bibliografia/pdfs/Chen_2021_BIT_Transformer.pdf`
- **Por qué leerlo**: state-of-the-art en change detection genérico con deep learning. Es el modelo target si vamos a Sprint 3 de DL.

### Recursos online complementarios

- **MIROVA**: https://www.mirovaweb.it
- **MODVOLC**: http://modis.higp.hawaii.edu
- **Base de datos VRP MIROVA 2000–2019**: https://osf.io/zm62w/
- **NHI Tool en Google Earth Engine**: ver github.com/Volcanic-Risk-Group/NHI
- **Copernicus Data Space**: https://dataspace.copernicus.eu
- **USGS EarthExplorer** (Landsat): https://earthexplorer.usgs.gov
- **Microsoft Planetary Computer** (catalog STAC): https://planetarycomputer.microsoft.com

---

## Cierre

La detección satelital de cambios volcánicos es una herramienta de **filtro de atención**: convierte petabytes de imágenes en una lista corta de "mirar esto". No reemplaza el ojo geológico ni las observaciones de campo, pero permite hacer lo imposible: vigilar 46 volcanes simultáneamente, dos veces al día, con resolución de 10–30 metros.

Copernicus-v1 está hoy en un punto donde:
- ✅ La descarga automatizada y los composites funcionan robustamente (cron 2×día).
- ✅ Hay un sistema básico de change detection (z-score multi-banda) operacional sobre 46 entidades.
- ✅ El dashboard sirve como interfaz de inspección visual rutinaria.
- 🔧 Falta calibración cuantitativa contra MIROVA (VRP en Watts).
- 🔧 Falta implementar NHI homogéneo S2 + L8/9 (Sprint 1).
- 🔧 Falta incorporar SAR Sentinel-1 para penetrar nubes (Sprint 3).

El roadmap detallado de mejoras priorizadas está en `bibliografia/IMPLEMENTACION.md`.

**Para dudas o sugerencias sobre este documento**: revisar las notas técnicas en `bibliografia/notas/0X_*.md` que tienen las fórmulas completas y la trazabilidad por paper.

---

*Documento generado en mayo 2026 como parte del proyecto Copernicus-v1. Sintetiza 5 archivos temáticos de bibliografía + 4 notas técnicas + 15 PDFs locales. Mantener actualizado conforme avance la implementación.*
