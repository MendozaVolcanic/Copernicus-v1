# Visualización de Change Detection — Bibliografía y Propuestas para `change_detection.html`

Búsqueda enfocada en **cómo mostrar visualmente** dónde ocurren los cambios entre dos imágenes (fecha A vs fecha B), no en cómo detectarlos algorítmicamente (ese tema ya está cubierto en `algoritmos_deteccion_cambios.md`). El foco es producir overlays/composites/heatmaps que un usuario pueda interpretar en el browser, con énfasis en cambios térmicos volcánicos S2/L8/L9.

Estado actual de la página `docs/change_detection.html`: muestra dos imágenes (anterior + reciente) RGB y ThermalFalseColor lado a lado, pero no las combina visualmente. Las imágenes están ya descargadas como PNGs en `docs/sentinel2/<volcan>/<fecha>_RGB.png` y `_ThermalFalseColor.png`. Todo lo siguiente es implementable **client-side sin descargar nada nuevo**.

---

## A. Composiciones bi-temporales RGB (los clásicos)

### 1. Howarth & Wickware — Procedures for change detection using Landsat digital data
- **Año:** 1981 · **IJRS** 2(3), 277–291 · **DOI:** 10.1080/01431168108948362
- **OA:** No (clásico bibliográfico, citas >900)
- **Aplicabilidad:** Define el "multi-date color composite": cargar banda X de fecha A en canal rojo, misma banda de fecha B en verde+azul. Lo que aparece en cian = ganancia (apareció en B); lo que aparece en rojo = pérdida (desapareció). Aplicable directamente a SWIR2 (B12) para resaltar aparición/desaparición de anomalías térmicas. **Implementación: trivial en canvas 2D.**

### 2. Coppin P., Jonckheere I., Nackaerts K., Muys B., Lambin E. — Digital change detection methods in ecosystem monitoring: a review
- **Año:** 2004 · **IJRS** 25(9), 1565–1596 · **DOI:** 10.1080/0143116031000101675
- **OA:** Parcial (preprint en KU Leuven repository)
- **Aplicabilidad:** Tabla 2 del paper compara 7 técnicas de visualización (image differencing, ratioing, RGB-multidate, CVA-pseudocolor). Recomienda RGB-multidate como técnica de inspección visual más interpretable por no-expertos. Útil como justificación pedagógica para SERNAGEOMIN.

### 3. Lu D., Mausel P., Brondízio E., Moran E. — Change detection techniques
- **Año:** 2004 · **IJRS** 25(12), 2365–2401 · **DOI:** 10.1080/0143116031000139863
- **OA:** Sí (researchgate)
- **Aplicabilidad:** Sección 3.2 "Visualization methods" describe el "write-function memory insertion" (WFMI) — equivalente conceptual del canvas compositing con globalCompositeOperation. Justifica usar R=A, G=B, B=B para resaltar **ganancias** en cian sobre fondo gris-neutro (sin cambio).

---

## B. Heatmaps de diferencia y Z-score visualization

### 4. Bovolo F., Bruzzone L. — A theoretical framework for unsupervised change detection based on Change Vector Analysis in polar domain
- **Año:** 2007 · **IEEE TGRS** 45(1), 218–236 · **DOI:** 10.1109/TGRS.2006.885408
- **OA:** No (IEEE)
- **Aplicabilidad:** Define el "magnitude image" como heatmap escalar de cambio. La representación en pseudo-color (HSV con H = ángulo CVA, V = magnitud) sigue siendo el state-of-the-art para mostrar "tipo + intensidad" de cambio en una sola imagen. **Versión simplificada implementable:** diff de un solo canal (SWIR2) → colormap turbo/inferno en canvas.

### 5. Eastman J.R., Fulk M. — Long sequence time series evaluation using standardized principal components
- **Año:** 1993 · **PE&RS** 59(8), 1307–1312
- **OA:** No (clásico)
- **Aplicabilidad:** Origen del **"standardized z-score image"** — restar la media histórica píxel a píxel y dividir por la desviación. Convertirlo a colormap divergente (azul→blanco→rojo) es la forma estándar de mostrar "anomalía respecto al comportamiento normal del píxel". Sienta la base para la métrica `z_score_termico` que ya calculamos en `change_analysis.py` pero NO mostramos espacialmente.

### 6. Kennedy R.E., Yang Z., Cohen W.B. — Detecting trends in forest disturbance and recovery using yearly Landsat time series: LandTrendr (con visualizations)
- **Año:** 2010 · **RSE** 114(12), 2897–2910 · **DOI:** 10.1016/j.rse.2010.07.008
- **OA:** Sí
- **Aplicabilidad:** Figs. 5–7 muestran formato canónico para visualización de cambio temporal: año de disturbance + magnitud en composite RGB. Aplicable a futuro si Copernicus-v1 acumula >2 años de stack temporal.

---

## C. Highlight overlays sobre imagen base (la opción más legible para usuarios)

### 7. Pesaresi M., Gerhardinger A., Kayitakire F. — A robust built-up area presence index by anisotropic rotation-invariant textural measure (PANTEX) — método de overlay
- **Año:** 2008 · **IEEE JSTARS** 1(3) · **DOI:** 10.1109/JSTARS.2008.2002869
- **OA:** Parcial
- **Aplicabilidad:** Técnica de overlay: imagen base en escala de grises + máscara binaria de cambio en color saturado con alpha=0.6. Es la forma menos confusa de mostrar "dónde hay cambio" — el usuario reconoce el terreno y los cambios saltan. **Patrón directamente trasladable a Leaflet o canvas 2D simple.**

### 8. Hansen M.C. et al. — High-Resolution Global Maps of 21st-Century Forest Cover Change
- **Año:** 2013 · **Science** 342, 850–853 · **DOI:** 10.1126/science.1244693
- **OA:** Sí (Science Open)
- **Aplicabilidad:** Aunque es global forestry, su visualización (https://earthenginepartners.appspot.com/science-2013-global-forest) es el **ejemplo paradigmático** de overlay: imagen base satelital tenue + pérdidas en rojo brillante con transparencia variable según magnitud. Es exactamente lo que queremos para anomalías térmicas. Inspiración de diseño UX directa.

---

## D. Visualización térmica volcánica específica

### 9. Marchese F., Filizzola C., Genzano N., Mazzeo G., Pergola N., Tramutoli V. — Assessment of volcanic thermal radiance through MIROVA and RST_VOLC algorithms: case study Mt. Etna
- **Año:** 2011 · **JVGR** 200, 220–230 · **DOI:** 10.1016/j.jvolgeores.2010.12.014
- **OA:** Parcial (preprint CNR-IMAA)
- **Aplicabilidad:** Figs 3–6 muestran cómo MIROVA visualiza VRP espacialmente: punto caliente sobre imagen RGB con tamaño proporcional a Watts. Para Copernicus-v1 podemos pintar **píxeles NHI>umbral con color proporcional a (B12-B11)** sobre el RGB base.

### 10. Massimetti F., Coppola D., Laiolo M., Valade S., Cigolini C., Ripepe M. — Volcanic Hot-Spot Detection Using SENTINEL-2 (sección de visualización)
- **Año:** 2020 · **Remote Sensing** 12(5), 820 · **DOI:** 10.3390/rs12050820
- **OA:** Sí (MDPI)
- **Aplicabilidad:** Fig 4 muestra el composite SWIR-SWIR-NIR con anomalías marcadas en amarillo encima. Validamos que el patrón "false-color + overlay binario" es el estándar de la comunidad volcanológica. Lo tenemos ya, falta el overlay.

### 11. Plank S., Marchese F., Genzano N., Nolde M., Martinis S. — The short life of the volcanic island New Late'iki — Sentinel-2 + Landsat visual pipeline
- **Año:** 2020 · **Remote Sensing** 12(22), 3779 · **DOI:** 10.3390/rs12223779
- **OA:** Sí (MDPI)
- **Aplicabilidad:** Pipeline visual end-to-end: NDWI temporal + dNHI overlay sobre RGB. Modelo de referencia para mostrar evolución morfológica (no solo térmica) volcán a volcán. Útil para Hudson, Calbuco, Chaitén donde hay cambios glaciar/dome.

### 12. Aufaristama M., Hoskuldsson A., Jonsdottir I., Ulfarsson M.O., Erlangga I., Thordarson T. — New insights for monitoring the Conical Seamount and Tinakula volcanoes (Solomon Islands) by integrating Sentinel-2 and PlanetScope
- **Año:** 2020 · **Frontiers in Earth Science** 8, 121 · **DOI:** 10.3389/feart.2020.00121
- **OA:** Sí
- **Aplicabilidad:** Figs 4–5: workflow de visualización "before/after + difference + thermal overlay" en 4 paneles. Layout directamente replicable en `change_detection.html`.

---

## E. Bi-temporal classification y SAR (referencias de fondo)

### 13. Bruzzone L., Prieto D.F. — Automatic analysis of the difference image for unsupervised change detection
- **Año:** 2000 · **IEEE TGRS** 38(3), 1171–1182 · **DOI:** 10.1109/36.843009
- **OA:** No
- **Aplicabilidad:** Define la clasificación binaria "change/no-change" con histograma EM. La forma estándar de mostrar el resultado es máscara binaria roja sobre imagen base. Patrón ya usado por todos los visualizadores Copernicus EMS.

### 14. Wegmüller U., Werner C., Strozzi T., Wiesmann A. — Multi-temporal interferometric SAR coherence change detection
- **Año:** 2016 · **Procs IGARSS** · **DOI:** 10.1109/IGARSS.2016.7729844
- **OA:** Parcial
- **Aplicabilidad:** Solo para futuro si añadimos Sentinel-1: la coherencia se visualiza como escala grayscale + máscara de pérdida coherente en rojo. No aplicable hoy con S2/L8 únicamente.

---

# 🎨 PROPUESTAS DE VISUALIZACIÓN PARA `change_detection.html`

Las 4 técnicas que siguen están ordenadas de menor a mayor esfuerzo. **Todas operan sobre los PNGs ya descargados** (`docs/sentinel2/<volcan>/<fecha>_RGB.png` y `_ThermalFalseColor.png`); ninguna requiere bajar bandas crudas adicionales ni cambiar el cron de descarga.

Esfuerzos asumen JS vanilla + canvas 2D (lo que ya usa el dashboard). Sin frameworks nuevos. Sin Leaflet (la página actual no es geo-referenciada todavía — los PNGs son recortes ya proyectados).

---

## Técnica 1 — RGB-multidate compositing (Howarth 1981 / Lu 2004) — **ESFUERZO BAJO (~1 día)**

**Qué muestra:** Una sola imagen donde:
- **Cian** = aparición de anomalía térmica (estaba frío, ahora caliente)
- **Rojo** = desaparición (estaba caliente, ahora frío)
- **Gris/blanco** = sin cambio significativo

**Bandas usadas:** Canal rojo (SWIR2) del PNG ThermalFalseColor de fecha A y fecha B. Ya descargado.

**Por qué es la primera:** Una imagen, una mirada, todo el cambio. El SWIR2 del thermal false color ya está cargado con la información térmica que importa. No requiere matemática nueva, solo recombinación de canales.

**Pseudocódigo (vanilla JS + canvas 2D):**

```javascript
async function renderCompositeRGB(canvasId, urlA, urlB) {
    const [imgA, imgB] = await Promise.all([loadImg(urlA), loadImg(urlB)]);
    const c = document.getElementById(canvasId);
    c.width = imgA.naturalWidth;
    c.height = imgA.naturalHeight;
    const ctx = c.getContext('2d');

    // Pintar A y B en canvases temporales para extraer pixel data
    const tmpA = drawToOffscreen(imgA);
    const tmpB = drawToOffscreen(imgB);
    const dataA = tmpA.getImageData(0, 0, c.width, c.height).data;
    const dataB = tmpB.getImageData(0, 0, c.width, c.height).data;
    const out = ctx.createImageData(c.width, c.height);

    for (let i = 0; i < dataA.length; i += 4) {
        const rA = dataA[i];      // canal R (SWIR2) fecha A
        const rB = dataB[i];      // canal R (SWIR2) fecha B
        // RGB-multidate: R=A, G=B, B=B → aparición=cian, desaparición=rojo
        out.data[i]     = rA;
        out.data[i + 1] = rB;
        out.data[i + 2] = rB;
        out.data[i + 3] = 255;
    }
    ctx.putImageData(out, 0, 0);
}

function loadImg(src) {
    return new Promise((res, rej) => {
        const im = new Image();
        im.crossOrigin = 'anonymous';
        im.onload = () => res(im);
        im.onerror = rej;
        im.src = src;
    });
}

function drawToOffscreen(img) {
    const c = document.createElement('canvas');
    c.width = img.naturalWidth;
    c.height = img.naturalHeight;
    const ctx = c.getContext('2d');
    ctx.drawImage(img, 0, 0);
    return ctx;
}
```

**Dónde insertar:** Justo después de la sección `thermalSection` actual (línea ~572 de `change_detection.html`), añadir una tercera `imagen-card` con `<canvas id="composite-{volcan}">` y llamar `renderCompositeRGB()` en `renderDetalle()`.

**Limitación honesta:** Si las imágenes A y B tienen ligero offset de georreferencia (Sentinel-2 puede tener shift sub-pixel entre tomas), aparecerá un "halo" en los bordes de features. No es bug; es real. Aceptable para inspección visual rápida.

---

## Técnica 2 — Heatmap de diferencia con colormap divergente (Eastman & Fulk 1993, Bovolo & Bruzzone 2007) — **ESFUERZO BAJO-MEDIO (~1.5 días)**

**Qué muestra:** Mapa píxel-por-píxel de `(SWIR2_B − SWIR2_A)` con colormap divergente (azul=enfrió, blanco=sin cambio, rojo=calentó). Equivalente conceptual del z-score escalar que ya calculamos numéricamente pero no mostramos.

**Bandas usadas:** Canal rojo de ThermalFalseColor de A y B. Misma data que Técnica 1.

**Por qué vale la pena además de la 1:** El RGB-multidate es cualitativo (cian/rojo); el heatmap es cuantitativo (intensidad codificada). Vienen juntos: un usuario novato usa la 1, un geólogo usa la 2 para estimar magnitud.

**Pseudocódigo:**

```javascript
// Colormap turbo simplificado (5 stops) — robusto para divergent diff
const TURBO_STOPS = [
    [-100, [49, 54, 149]],   // azul fuerte (enfriamiento extremo)
    [-30,  [171, 217, 233]], // azul claro
    [0,    [255, 255, 255]], // blanco (sin cambio)
    [30,   [253, 174, 97]],  // naranja
    [100,  [165, 0, 38]]     // rojo fuerte (calentamiento extremo)
];

function interpolateTurbo(diff) {
    diff = Math.max(-100, Math.min(100, diff));
    for (let i = 0; i < TURBO_STOPS.length - 1; i++) {
        const [v0, c0] = TURBO_STOPS[i];
        const [v1, c1] = TURBO_STOPS[i + 1];
        if (diff >= v0 && diff <= v1) {
            const t = (diff - v0) / (v1 - v0);
            return [
                Math.round(c0[0] + t * (c1[0] - c0[0])),
                Math.round(c0[1] + t * (c1[1] - c0[1])),
                Math.round(c0[2] + t * (c1[2] - c0[2]))
            ];
        }
    }
    return [128, 128, 128];
}

async function renderDiffHeatmap(canvasId, urlA, urlB, threshold = 15) {
    const [imgA, imgB] = await Promise.all([loadImg(urlA), loadImg(urlB)]);
    const c = document.getElementById(canvasId);
    c.width = imgA.naturalWidth;
    c.height = imgA.naturalHeight;
    const ctx = c.getContext('2d');
    const dataA = drawToOffscreen(imgA).getImageData(0, 0, c.width, c.height).data;
    const dataB = drawToOffscreen(imgB).getImageData(0, 0, c.width, c.height).data;
    const out = ctx.createImageData(c.width, c.height);

    for (let i = 0; i < dataA.length; i += 4) {
        const diff = dataB[i] - dataA[i];  // R_B - R_A
        if (Math.abs(diff) < threshold) {
            // sin cambio → gris translúcido
            out.data[i] = out.data[i + 1] = out.data[i + 2] = 180;
            out.data[i + 3] = 60;
        } else {
            const [r, g, b] = interpolateTurbo(diff);
            out.data[i]     = r;
            out.data[i + 1] = g;
            out.data[i + 2] = b;
            out.data[i + 3] = 255;
        }
    }
    ctx.putImageData(out, 0, 0);
}
```

**Mejora opcional (semi-cuantitativa):** En lugar de B-A crudo, normalizar `diff / sigma_historico` usando `v.z_score_termico` ya disponible en `change_results.json`. Eso lo convierte en un mapa de z-score real, alineado con los thresholds del paper Eastman 1993.

---

## Técnica 3 — Highlight overlay sobre imagen base (Hansen 2013 style) — **ESFUERZO MEDIO (~2 días)**

**Qué muestra:** El RGB color natural (familiar al geólogo) **debajo** + una máscara semi-transparente roja **encima** marcando solo los píxeles con cambio térmico significativo. El usuario reconoce el cráter, el flanco glaciar, etc., y los cambios saltan a la vista.

**Bandas usadas:** RGB de fecha B (base contextual) + máscara generada de la diferencia SWIR2 con threshold = media + 2σ (mismo criterio que `change_analysis.py`).

**Por qué la mejor opción UX para SERNAGEOMIN:** Es el patrón Hansen/Global Forest Watch — probadamente legible por audiencias no-técnicas (autoridades, prensa). El RGB de fondo da contexto geográfico; el overlay rojo dice exactamente "acá hay algo nuevo".

**Pseudocódigo (canvas con dos capas + slider de opacidad):**

```javascript
async function renderHighlightOverlay(containerId, urlRgbB, urlThermalA, urlThermalB) {
    const wrap = document.getElementById(containerId);
    wrap.style.position = 'relative';

    const baseCanvas = document.createElement('canvas');
    baseCanvas.style.position = 'absolute';
    baseCanvas.style.top = '0';
    baseCanvas.style.left = '0';

    const overlayCanvas = document.createElement('canvas');
    overlayCanvas.style.position = 'absolute';
    overlayCanvas.style.top = '0';
    overlayCanvas.style.left = '0';
    overlayCanvas.style.opacity = '0.65';

    wrap.appendChild(baseCanvas);
    wrap.appendChild(overlayCanvas);

    const [rgbB, thA, thB] = await Promise.all(
        [urlRgbB, urlThermalA, urlThermalB].map(loadImg)
    );

    const W = rgbB.naturalWidth, H = rgbB.naturalHeight;
    [baseCanvas, overlayCanvas].forEach(c => { c.width = W; c.height = H; });

    // 1) Pintar base RGB
    baseCanvas.getContext('2d').drawImage(rgbB, 0, 0);

    // 2) Calcular diff y pintar solo píxeles >threshold en rojo
    const dA = drawToOffscreen(thA).getImageData(0, 0, W, H).data;
    const dB = drawToOffscreen(thB).getImageData(0, 0, W, H).data;
    const out = overlayCanvas.getContext('2d').createImageData(W, H);

    // Calcular media + 2σ de la diferencia (criterio change_analysis.py)
    let sum = 0, sumSq = 0, n = 0;
    for (let i = 0; i < dA.length; i += 4) {
        const d = dB[i] - dA[i];
        sum += d; sumSq += d * d; n++;
    }
    const mean = sum / n;
    const sigma = Math.sqrt(sumSq / n - mean * mean);
    const threshold = mean + 2 * sigma;

    for (let i = 0; i < dA.length; i += 4) {
        const diff = dB[i] - dA[i];
        if (diff > threshold) {
            out.data[i]     = 248;  // #f85149 (rojo SERNAGEOMIN alerta)
            out.data[i + 1] = 81;
            out.data[i + 2] = 73;
            out.data[i + 3] = 220;
        } else {
            out.data[i + 3] = 0;  // transparente
        }
    }
    overlayCanvas.getContext('2d').putImageData(out, 0, 0);

    // 3) Slider de opacidad
    const slider = document.createElement('input');
    slider.type = 'range';
    slider.min = 0;
    slider.max = 100;
    slider.value = 65;
    slider.oninput = () => { overlayCanvas.style.opacity = slider.value / 100; };
    wrap.appendChild(slider);
}
```

**Resultado UX:** El usuario ve el volcán a color natural, mueve el slider para alternar entre "solo contexto" y "solo cambios". Probadamente legible.

---

## Técnica 4 — NHI overlay con colormap proporcional (Marchese 2019 / Massimetti 2020) — **ESFUERZO MEDIO-ALTO (~3 días + nueva descarga)**

**Qué muestra:** Visualización fiel al state-of-the-art volcanológico: solo los píxeles con `NHI_SWIR = (B12-B11)/(B12+B11) > 0` se pintan, con color escalado según intensidad (amarillo→naranja→rojo→blanco saturado).

**Bandas requeridas:** B11 y B12 separadamente (no solo el ThermalFalseColor). Estas hoy se generan dentro del evalscript pero **no se guardan como PNGs individuales**. Requiere modificar `config_sentinel2.py` para añadir un evalscript adicional `NHI_VIZ` que devuelva los dos canales separados, y un campo nuevo en `indices_disponibles`.

**Por qué dejarla para después:** Es la más "correcta" científicamente, pero rompe el principio de "implementación de 1 día con lo que ya tenemos". Es el siguiente paso natural cuando las Técnicas 1–3 estén deployed.

**Pseudocódigo (asume PNG `<fecha>_NHI_SWIR.png` ya generado):**

```javascript
async function renderNHIOverlay(canvasId, urlRgb, urlNhi) {
    const [imgRgb, imgNhi] = await Promise.all([loadImg(urlRgb), loadImg(urlNhi)]);
    const c = document.getElementById(canvasId);
    c.width = imgRgb.naturalWidth;
    c.height = imgRgb.naturalHeight;
    const ctx = c.getContext('2d');
    ctx.drawImage(imgRgb, 0, 0);

    const nhiData = drawToOffscreen(imgNhi).getImageData(0, 0, c.width, c.height).data;
    const overlay = ctx.createImageData(c.width, c.height);

    // PNG NHI ya viene mapeado: 0 → NHI<=0 (frío), 255 → NHI=1 (muy caliente)
    for (let i = 0; i < nhiData.length; i += 4) {
        const v = nhiData[i];
        if (v < 130) { overlay.data[i + 3] = 0; continue; }
        // Colormap "fuego": amarillo → rojo → blanco
        if (v < 180) { overlay.data[i]=255; overlay.data[i+1]=200; overlay.data[i+2]=0; }
        else if (v < 220) { overlay.data[i]=255; overlay.data[i+1]=80; overlay.data[i+2]=0; }
        else { overlay.data[i]=255; overlay.data[i+1]=255; overlay.data[i+2]=200; }
        overlay.data[i + 3] = 200;
    }
    ctx.putImageData(overlay, 0, 0);
    ctx.globalCompositeOperation = 'lighten';  // mezclar overlay con base
}
```

---

## Orden de implementación recomendado

1. **Día 1:** Técnica 1 (RGB-multidate). Una sola función nueva, una `imagen-card` nueva. Win inmediato.
2. **Día 2:** Técnica 2 (Heatmap divergente). Reutiliza el `loadImg`+`drawToOffscreen` de la 1.
3. **Días 3–4:** Técnica 3 (Highlight overlay con slider). La que más le va a gustar a SERNAGEOMIN para reportes.
4. **Sprint 2:** Técnica 4 (NHI overlay) — requiere modificar evalscripts y agregar nuevo PNG a la descarga 2×día.

Cada técnica suma un panel nuevo en `change_detection.html` sin tocar los existentes. Backwards-compatible total.

---

## Consideraciones técnicas finales

- **CORS:** Los PNGs son same-origin (GitHub Pages), `crossOrigin='anonymous'` debería funcionar. Verificar con un test mínimo antes de empezar la 1.
- **Performance:** Imágenes S2 a ~500×500 px = 250k píxeles, loop simple sin Web Worker es <50 ms en hardware modesto. No optimizar antes de medir.
- **Hook de seguridad:** Las propuestas usan `createElement`+`appendChild`+`canvas.getContext('2d').putImageData`. **No usan `innerHTML`** → cumple la regla crítica de CLAUDE.md.
- **Alignment sub-pixel:** Si las dos fechas tienen offset, hay opción de añadir un paso de phase-correlation client-side (un FFT 2D pequeño), pero es **complejidad innecesaria para Sprint 1**. Solo añadir si los usuarios reportan halos molestos.
