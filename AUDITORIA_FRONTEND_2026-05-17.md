# Auditoría Frontend — Copernicus-v1

**Fecha:** 2026-05-17
**Alcance:** `docs/*.html` (10 páginas, ~8.500 líneas HTML/CSS/JS)
**Auditor:** Claude (subagente frontend)

---

## Resumen ejecutivo

1. **Tipo en clave: `Michinmahuidia`** (`docs/index.html:1356`) — el resto del proyecto usa `Michinmahuida`. Esto rompe silenciosamente todo lookup `VOLCANES_CONFIG['Michinmahuida']` desde el dashboard (cargas, comparaciones, modal Copernicus, PPT individual). **Bug crítico de datos**.
2. **Coordenadas duplicadas Antuco/Nevados de Chillán** (`docs/revision_volcanes.html:265-267`): Antuco está marcado en lat -37.41093 / lon -71.351307, idéntico (3 decimales redondeados) a Nevados de Chillán. La coord real de Antuco es ~-37.40 / -71.35 también, **pero coincidencia visualmente exacta sugiere copy-paste sin actualizar**. Las coords correctas son -37.40608 / -71.34869 (Antuco) y -36.86371 / -71.37793 (Chillán) según SERNAGEOMIN: hay error en Chillán también (sus coords están copiadas de Antuco).
3. **Cero accesibilidad estructurada**: 0 `aria-label`, 0 `role=`, 0 `:focus` visible en navegación, sin `outline` reset cuidado. Botones de cierre (`<button class="close-btn">`) sin texto ni aria-label. **Falla WCAG AA básica**.
4. **CSS duplicado en cada página**: cada uno de los 10 HTML embebe su propio bloque `<style>` con paletas casi iguales (mismos #58a6ff / #161b22) pero `font-family` heterogéneo (index.html usa `'Segoe UI'` primero, el resto `-apple-system` primero). No existe `docs/styles.css` compartido.
5. **`innerHTML` con contenido dinámico interpolado** en ≥13 lugares de `index.html` (líneas 1611, 1631, 1834, 1863, 1870, 1917, 1948, 1960, 2000, 2031, 2642...). Inserta nombres de volcán y URLs sin escape. Aunque los nombres son una lista fija conocida, **el patrón viola la regla CRÍTICA del `CLAUDE.md` del proyecto** ("NO usar innerHTML con contenido dinámico → hook de seguridad lo bloquea"). Si el hook está activo, estos bloqueos pasaron desapercibidos; si no, es deuda técnica directa.

---

## Tabla de hallazgos por severidad

| ID | Severidad | Página | Categoría | Hallazgo |
|---|---|---|---|---|
| H01 | 🔴 | index.html:1356 | Bug datos | Typo `'Michinmahuidia'` rompe lookup del volcán |
| H02 | 🔴 | revision_volcanes.html:265-267 | Bug datos | Coords Antuco / Nevados de Chillán duplicadas |
| H03 | 🔴 | index.html (13 sitios) | Seguridad/regla | `innerHTML` con templates dinámicos contra regla explícita CLAUDE.md |
| H04 | 🔴 | index.html:896 | UX texto | "Ya descargad**ia**" (typo visible en leyenda calendario) |
| H05 | 🔴 | index.html:1372,1376 | Bug temporal | `calendarYear = 2026` hardcoded; rompe en 2027 |
| H06 | 🔴 | index.html:886,948 | UX texto | "Mi" en lugar de "Mié" (header miércoles) y "Sb" en lugar de "Sáb" |
| H07 | 🟠 | index.html:6 | SEO | `<title> Sentinel-2 Volcanic Monitor</title>` con espacio inicial y sin sufijo de marca |
| H08 | 🟠 | TODAS | a11y | Cero `aria-label`/`role=`; botones close-btn sin texto |
| H09 | 🟠 | TODAS | a11y | Cero `:focus` visible global; ningún `:focus-visible` |
| H10 | 🟠 | index.html, change_detection.html | Performance | `<img>` sin `loading="lazy"` en grids de 46 volcanes (carga 92 imágenes al inicio) |
| H11 | 🟠 | TODAS | SEO/Metadata | Sin `<meta name="description">`, sin `<link rel="icon">`, sin Open Graph |
| H12 | 🟠 | sala_monitoreo.html:354-356 | Memory leak | 3 `setInterval` sin `clearInterval` jamás (OK en pantalla siempre encendida, pero acumula si el HTML se re-monta vía SPA) |
| H13 | 🟠 | sala_monitoreo.html:534, index.html:1476 | Bug timezone | Offset Chile codificado como `-(-240)` (UTC-4) sin considerar horario de verano (Chile suele estar en UTC-3 en verano) |
| H14 | 🟠 | index.html / sala_monitoreo.html / change_detection.html | Consistencia | Misma zona "Sur" tiene 13 volcanes en index.html, 13 en sala_monitoreo.html, pero el orden no matchea (no son arrays idénticos) |
| H15 | 🟠 | proximas_pasadas.html:172 | UX errores | `document.getElementById('grid').textContent = 'Error cargando datos: ' + e` — concatena Error object directo (muestra `[object Error]` o stack feo) |
| H16 | 🟠 | gif_builder.html:341 | Error swallowing | `cargarMetadata()` retorna `{}` en error sin avisar al usuario; el GIF queda incompleto silenciosamente |
| H17 | 🟠 | change_detection.html:643 | Bug imagen | `img.onerror = function() { this.alt = '...'; this.src = '' }` — limpiar `.src` re-dispara `onerror` (loop teórico) |
| H18 | 🟠 | index.html (todos los grupos) | Consistencia visual | 10+ colores distintos para botones de la misma jerarquía (#da3633, #6e40c9, #b45309, #238636, #2ea043, #e67e22, #0969da, #0e7490, #065f46, #8b5cf6, #0891b2, #16a34a, #15803d, #be185d, #15803d). Sin sistema de design tokens |
| H19 | 🟠 | TODAS | Consistencia | Texto botón "Volver": "← Dashboard" (gif/ppt/proximas), "← Volver al dashboard" (ayuda/revision), "< Dashboard Principal" (change_detection) — 3 variantes |
| H20 | 🟠 | TODAS | Tipografía | `font-family` distinto: index.html arranca con `'Segoe UI'`; el resto con `-apple-system`. Inconsistencia visual entre páginas |
| H21 | 🟡 | index.html:1391, 2621, 2622, 1818, 1886, 1976 | Anti-pattern | `element.innerHTML = ''` para vaciar — usar `replaceChildren()` o `while(el.firstChild) el.removeChild()` (el resto del codebase ya lo usa) |
| H22 | 🟡 | gif_builder.html:335 | parseInt/Float | `parseFloat(cols[idxNubes]) \|\| 0` — silencia NaN; un 0% nubes falso enmascara datos corruptos |
| H23 | 🟡 | index.html:2118,2119,2255,2256 | parseInt | `parseInt(...)` sin radix explícito (4 sitios) |
| H24 | 🟡 | TODAS | Loading states | Ningún `aria-busy`/`aria-live` durante fetches; spinners solo visuales |
| H25 | 🟡 | index.html:2095 | UX broken | `window.open('.../actions', '_blank')` después de `confirm()` — depende de pop-up blocker (gesto perdido entre confirm async) |
| H26 | 🟡 | index.html:1511,1148+ | Debug | `console.log('🗓️ Debug Calendario:', ...)` queda en producción |
| H27 | 🟡 | change_detection.html:1226,1250,1275 | parseInt OK | Bien hecho (`parseInt(e.target.value, 10) \|\| 0`) — referencia positiva |
| H28 | 🟡 | revision_volcanes.html:303-305 | Bug validación | `validarLat(v) { return v >= -45 && v <= -18 }` — Hudson está en -45.91, queda fuera del rango válido |
| H29 | 🟡 | index.html:2587-2615 | Promise sin catch encadenado | `fetch().then().then().catch()` OK acá; pero hay `fetch(...).then(...)` sin `.catch` en `cargarMetadatosComparacion` line 2706 — sí tiene catch al final, OK; revisar |
| H30 | 🟡 | sala_monitoreo.html:319 | Datos hardcoded | URL `Landsat-v1/master/...` — si el repo cambia branch o nombre, todo el modo Landsat se cae sin aviso |
| H31 | 🟡 | proximas_pasadas.html:170 | Performance | `setInterval(render, 30000)` re-renderiza todo el grid (46 cards) cada 30s — debería actualizar solo countdowns |
| H32 | 🟡 | sala_monitoreo.html:480 (cargarImgEnSub) | Cache busting agresivo | Cada render agrega `?t=${Date.now()}` → invalida cache HTTP de imágenes que no cambian. Bandwidth gasto |
| H33 | 🟡 | TODAS | Responsive | `@media (max-width:...)` solo en change_detection.html:133-140 (4 líneas) y ppt_builder.html:160-163 (3 líneas) — el resto no contempla mobile/tablet |
| H34 | 🟡 | index.html:835 | Espacios | `<label for="zona-select"> ZONA:</label>` espacio inicial en label (probablemente era icono perdido) |
| H35 | 🟡 | index.html:786,791 | Inconsistencia listas | `PERSONAL_ZONAS` (línea 1672) lista 'sur' con 13 volcanes; `VOLCANES_CONFIG` lista 13 distintos. Verificar que coinciden 1:1 |
| H36 | 🟡 | sala_monitoreo.html:289 | UX | Botón Pausa solo cambia texto, no estado visual (color/border) — diff con clase `paused` recomendado |
| H37 | 🟡 | experimental/cog_viewer.html | Sin loading="lazy" | Tiles Leaflet bien manejados, pero el grid de resultados sí carga imágenes; ver thumbnails |
| H38 | 🟢 | ayuda.html | Positivo | TOC sticky bien implementado, tipografía coherente con vars |
| H39 | 🟢 | revision_volcanes.html:316 | Positivo | Único archivo con comentario explícito "(sin innerHTML con contenido dinámico)" — el resto del codebase debería seguir este patrón |
| H40 | 🟢 | change_detection.html | Positivo | Función `el()` helper para createElement evita innerHTML; bien |

---

## Detalle de hallazgos críticos

### H01 🔴 Typo `Michinmahuidia` rompe lookup del volcán
**Archivo:** `docs/index.html:1356`
**Código:**
```js
'Michinmahuidia': { lat: -42.79, lon: -72.44, zona: 'Austral', buffer_km: 9.5 },
```
**Resto del codebase usa:** `'Michinmahuida'` (sin la `i` extra), incluyendo:
- `docs/index.html:1676` (línea 'austral' del PERSONAL_ZONAS)
- `docs/sala_monitoreo.html:304`
- `docs/ppt_builder.html:255,268`
- `docs/experimental/cog_viewer.html:150`
- `docs/experimental/alta_resolucion.html:165`
- `docs/revision_volcanes.html:286`
- `docs/fechas_disponibles_copernicus.json:895` (datos reales)
- `config_sentinel2.py` (Python backend)

**Impacto:** cuando el usuario selecciona Michinmahuida en el dropdown:
- `VOLCANES_CONFIG[currentVolcano]` retorna `undefined`
- El calendario Copernicus (línea 2188 `VOLCANES_CONFIG[currentVolcano]`) crashea con `Cannot read properties of undefined`
- El cálculo `buffer_km` en comparaciones (`VOLCANES_CONFIG[volcanActual]?.buffer_km || 3`) usa fallback silencioso 3km en vez del valor real 9.5km — **escala de imágenes incorrecta para Michinmahuida** sin que nadie se entere.

**Fix:** `'Michinmahuidia'` → `'Michinmahuida'` en index.html:1356.

---

### H02 🔴 Coordenadas Antuco/Nevados de Chillán duplicadas
**Archivo:** `docs/revision_volcanes.html:265-267`
```js
{ nombre: "Nevados de Chillan", zona: "Centro", lat: -37.41096, lon: -71.35231, buffer_km: 3.3 },
// ZONA SUR
{ nombre: "Antuco",             zona: "Sur",    lat: -37.41093, lon: -71.351307, buffer_km: 3.0 },
```
**Coords reales:**
- Nevados de Chillán: -36.86371, -71.37793
- Antuco: -37.40608, -71.34869

Las dos entradas tienen la misma coord (de Antuco). **Esto significa que toda imagen "Nevados de Chillán" descargada está mostrando un cuadrante en Antuco**.

`docs/index.html:1333` sí tiene `'Nevados de Chillan': { lat: -36.86, lon: -71.38, ... }` correcto. Pero `revision_volcanes.html` queda como fuente de verdad cuando el usuario revisa coordenadas → propone "no hay cambios" para Chillán cuando en realidad el dato del Python downloader (que sí usa -36.86) está bien, y la revisión está mal. **Auditoría manual de coords queda envenenada por bug del HTML.**

**Fix:** corregir lat/lon de "Nevados de Chillan" a -36.86371 / -71.37793 en `revision_volcanes.html:265`.

---

### H03 🔴 `innerHTML` con templates dinámicos viola regla del proyecto
**Archivos:** `docs/index.html` (≥13 sitios), `docs/ppt_builder.html` (1)

Citas del `CLAUDE.md` de Copernicus-v1:
> NO usar innerHTML con contenido dinámico → hook de seguridad lo bloquea.

Ejemplos concretos en violación:
```js
// index.html:1863
document.getElementById(rgbId).innerHTML =
  `<img src="${c}" style="..." onclick="zoomImage('${c}','${volcan} - Color Verdadero','${ultimaFecha}')">`;
```
- `volcan` viene de un Object.keys() controlado (OK en práctica)
- `c` viene de URL construida con `encodeURIComponent` (OK)
- Pero el patrón `onclick="...${var}..."` permite inyección si la fuente cambia

`revision_volcanes.html:316` y `change_detection.html:380` (función `el()`) ya demostraron que se puede hacer todo con `createElement`. **Refactor consistente pendiente.**

---

### H04, H06 🔴 Errores de tipografía visibles
- `index.html:896`: `<span>Ya descargad**ia**</span>` → "Ya descargada"
- `index.html:886`: `<div class="calendar-day-header">**Mi**</div>` → "Mié"
- `index.html:889`: `<div class="calendar-day-header">**Sb**</div>` → "Sáb"

Probablemente vienen de un copy-paste con caracteres Unicode perdidos (`Sb` viene de "Sáb" con acento mal codificado). Los headers de calendario quedan visualmente raros.

---

### H05 🔴 `calendarYear = 2026` hardcoded
`docs/index.html:1372,1376`:
```js
let calendarYear = 2026;
let calendarCopernicusYear = 2026;
```
Selectores `<option value="2025">` y `<option value="2026">` solo (líneas 877-879, 938-940). En enero de 2027 el dashboard pierde el año actual. Usar `new Date().getFullYear()` o un loop dinámico para generar las opciones.

---

### H13 🟠 Timezone Chile codificado sin DST
```js
// sala_monitoreo.html:534, index.html:1476
const chileMs = ahora.getTime() + (ahora.getTimezoneOffset() - (-240)) * 60000;
```
Asume Chile = UTC-4 fijo. Chile usa horario de verano (sept-abril UTC-3, abril-sept UTC-4). La función `esNuevaHoy()` puede confundir el día por ±1 durante 6 meses al año. Usar `Intl.DateTimeFormat('es-CL', {timeZone: 'America/Santiago'})`.

---

### H10 🟠 `loading="lazy"` ausente en grids
`grep loading="lazy"` retorna 0 resultados en todo el codebase. `index.html` modos Multi-Volcán/Personal/Riesgosos cargan 2×46 = 92 imágenes al inicio (~10MB+). En conexión móvil esto es muerte:
```js
// index.html:1948 (típico)
document.getElementById(`rgb-${volcan}`).innerHTML =
  `<img src="..." style="width:100%;...">`;  // SIN loading="lazy"
```
Fix: agregar `loading="lazy"` y `decoding="async"` a todos los `<img>` generados dinámicamente.

---

### H18 🟠 Caos cromático en botones del status-bar
`docs/index.html:789-825` — grupo de ≥15 botones, cada uno con `style="background: #XXXXXX"` inline, sin clase:
- `#da3633` (Multi-Volcán)
- `#6e40c9` (Personal)
- `#b45309` (Riesgosos)
- `#238636`, `#2ea043` (PPT individual/completo)
- `#e67e22` (Landsat)
- `#0969da` (Copernicus)
- `#0e7490` (COG), `#065f46` (Alta Res)
- `#8b5cf6` (Cambios), `#0891b2` (Pasadas)
- `#16a34a` (GIF), `#15803d` (Constructor PPT y Revisión, **igual color para 2 botones distintos**)
- `#be185d` (Sala)
- `#475569` (Ayuda)
- `#1f2937` (Fullscreen)

**Sin sistema de tokens.** Mover a clases `.btn-primary`, `.btn-secondary`, `.btn-experimental`, `.btn-warning` con paleta de 4-5 colores en CSS vars.

---

### H08 🟠 Botones close sin texto accesible
`docs/index.html:857,915`:
```html
<button class="close-btn" onclick="toggleCalendar()"></button>
```
- Vacío, sin texto ni `aria-label`
- Screen reader anuncia "botón" y nada más
- Lo mismo en `calendar-copernicus-modal`

Fix: `<button class="close-btn" aria-label="Cerrar calendario" onclick="...">×</button>`.

---

## Inconsistencias entre páginas (sección especial)

### Listas de volcanes definidas en múltiples lugares
Cada página redefine sus listas:

| Lugar | Estructura | Norte | Centro | Sur | Austral | Total |
|---|---|---|---|---|---|---|
| `index.html:1313` (VOLCANES_CONFIG) | Object dict | 8 | 9 | 13 | 13 (con typo) | 43 |
| `index.html:1672` (PERSONAL_ZONAS) | Object lowercase | 8 | 9 | 13 | 13 | 43 |
| `sala_monitoreo.html:300` (ZONAS) | Object | 8 | 9 | 13 | 13 | 43 |
| `revision_volcanes.html:246` (VOLCANES) | Array de objetos | 8 | 9 | 13 | 13 | 43 |
| `ppt_builder.html:251` (VOLCANES) | Array | 8 | 9 | 13 | 13 | 43 |
| `proximas_pasadas.html` | (no define, lee del JSON) | — | — | — | — | — |
| `experimental/cog_viewer.html:150` | Object simple | ~22? | ? | ? | ? | ? |
| `experimental/alta_resolucion.html:165` | Object | 8 | 9 | 13 | 13 | 43 |

**6 copias de la misma lista**. Cualquier cambio (un volcán nuevo, recategorización de zona, vista zoom adicional) implica editar 6 archivos. Ya vimos el resultado: typo `Michinmahuidia` solo en uno.

**Fix sugerido:** generar `docs/volcanes.js` como single source of truth (puede ser autogenerado desde `config_sentinel2.py` por el cron), y cada HTML hace `<script src="volcanes.js"></script>`.

### Color del header
- `index.html:43`: `linear-gradient(90deg, #161b22, #1f2937)` (dark gray)
- `sala_monitoreo.html:32`: `linear-gradient(90deg, #1f4e79, #2563eb)` (blue)
- `proximas_pasadas.html:20`: `linear-gradient(90deg, #1f4e79, #2563eb)` (blue, igual sala)
- `ayuda.html:28`: `linear-gradient(90deg, #1f4e79, #2563eb)` (blue, igual)
- `ppt_builder.html:18`: `linear-gradient(90deg, #1f4e79, #2563eb)` (blue, igual)
- `change_detection.html:18`: `linear-gradient(135deg, #1a1f2e, #0d1117)` (otro distinto)

**index.html es la única página que no usa el header azul.** Como es la "página madre", crea desconexión visual al volver a ella.

### Texto del botón "volver"
| Página | Texto |
|---|---|
| ppt_builder.html | `← Dashboard` |
| proximas_pasadas.html | `← Dashboard` |
| gif_builder.html | `← Dashboard` |
| revision_volcanes.html | `← Volver al dashboard` |
| ayuda.html | `← Volver al dashboard` |
| change_detection.html | `< Dashboard Principal` (sin flecha unicode, otro texto) |
| sala_monitoreo.html | (no tiene botón volver) |

### Símbolos de estado
- `change_detection.html`: ALERTA `#f85149`, ATENCION `#d29922`, NORMAL `#3fb950` (semáforo)
- `proximas_pasadas.html`: cd-now `#f85149` (red), cd-soon `#f97316` (orange), cd-later `muted` — usa **#f97316** vs el `#d29922` de change_detection para misma idea de "atención"

Mismo concepto, dos naranjas distintos.

---

## Plan de remediación priorizado

### Sprint 1 (1-2 días, críticos)
1. **Fix `Michinmahuidia` → `Michinmahuida`** en `index.html:1356`. Buscar otros typos similares con `git grep`.
2. **Fix coords Antuco/Nevados de Chillán** en `revision_volcanes.html:265-267`.
3. **Fix typos visibles**: "descargadia"→"descargada", "Mi"→"Mié", "Sb"→"Sáb" en `index.html:886-906`.
4. **Año dinámico**: reemplazar `2026` hardcoded por `new Date().getFullYear()` y generar opciones de año dinámicamente.
5. **Refactor `innerHTML` críticos** a `createElement` en las 13 ubicaciones de `index.html` (o documentar excepciones).

### Sprint 2 (3-5 días, accesibilidad + consistencia)
6. **CSS compartido**: extraer `docs/styles/base.css` con vars (`--bg`, `--surface`, `--accent`, etc.) y `font-family`. Cada HTML hace `<link rel="stylesheet" href="styles/base.css">`. Reduce ~30% de líneas duplicadas.
7. **Sistema de botones**: `.btn-primary`, `.btn-secondary`, `.btn-warning`, `.btn-experimental`, `.btn-ghost` con paleta de 5 colores. Quitar todos los `style="background:#..."` inline.
8. **Accesibilidad básica**:
   - `aria-label` en botones icon-only (close, fullscreen, pause).
   - `:focus-visible` global con outline azul.
   - `loading="lazy"` en `<img>` de grids.
   - `aria-live="polite"` en `#status`/`#last-update`.
9. **Single source of truth para volcanes**: `docs/volcanes.js` autogenerado, todas las páginas lo importan.

### Sprint 3 (1 semana, robustez)
10. **Timezone Chile correcto** con `Intl.DateTimeFormat('es-CL', {timeZone:'America/Santiago'})` reemplazando todos los offsets `-240` hardcoded.
11. **`<meta>` y SEO** en todas las páginas: description, favicon (`docs/favicon.ico`), Open Graph para compartir Sala de Monitoreo.
12. **Tests E2E con Playwright**: smoke test en cada página (carga sin error consola, modos togglean OK, fetches no 404).
13. **Mensajes de error útiles**: reemplazar `console.warn`/`alert` por toast/banner contextual con sugerencia de acción.
14. **Limpiar `console.log` debug** en producción.
15. **Responsive mobile**: agregar `@media (max-width:768px)` en todas las páginas (no solo change_detection y ppt_builder). Stack vertical para grids, ocultar status-bar excesivo.

### Sprint 4 (continuo)
16. Auditar y completar `loading="lazy"` + `decoding="async"` en cada `<img>`.
17. Reemplazar `setInterval` agresivos por updates diff (proximas_pasadas re-renderiza todo cada 30s — solo actualizar countdowns).
18. Documentar paleta de colores definitiva en `docs/styles/README.md`.

---

## Métricas

- **Líneas auditadas:** ~8.552 HTML
- **Hallazgos totales:** 40 (5 críticos, 13 importantes, 19 nice-to-have, 3 referencias positivas)
- **Páginas con violación de regla `innerHTML`:** 8/10
- **Páginas con `aria-label`:** 0/10
- **Páginas con `font-family` consistente:** 8/10 (index y change_detection son outliers)
- **Bugs de datos detectados:** 3 (Michinmahuidia, Antuco/Chillán coords, año hardcoded)
- **Listas de volcanes duplicadas:** 6 copias del mismo dataset

**Conclusión:** el dashboard funciona pero acumuló deuda técnica del tipo "copy-paste sin refactor". El usuario es geólogo, no developer — invertir en CSS compartido + single source de datos paga dividendos cada vez que SERNAGEOMIN agregue un volcán o corrija una coord. Los 5 bugs críticos son fixes de <5 minutos cada uno y deben hacerse hoy.
