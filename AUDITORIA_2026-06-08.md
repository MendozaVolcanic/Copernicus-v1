# Auditoría exhaustiva — Copernicus-v1

**Fecha:** 2026-06-08
**Alcance:** auditoría multi-dimensión del repositorio completo (backend Python, frontend del dashboard, workflows de GitHub Actions, tests, integridad de datos, seguridad y documentación).

---

## Metodología

- **57 agentes** especializados desplegados en paralelo sobre distintas dimensiones del sistema.
- **Verificación adversarial:** cada hallazgo preliminar fue re-examinado por un agente independiente que intentó refutarlo (¿es real?, ¿ya está resuelto?, ¿el `line` apunta al código correcto?).
- **Resultado:** **47 hallazgos totales → 44 confirmados** tras la verificación adversarial (3 descartados por falsos positivos o por estar ya resueltos).

### Distribución por severidad (44 confirmados)

| Severidad | Cantidad |
|---|---:|
| 🔴 **Crítico** | 1 |
| 🟠 **Alto** | 3 |
| 🟡 **Medio** | 16 |
| ⚪ **Bajo** | 24 |
| **Total** | **44** |

---

## Resumen ejecutivo

El sistema funciona y vigila los 43 volcanes, pero arrastra **tres riesgos urgentes** que comprometen la confiabilidad operativa:

1. **El `.git` ya pesa 25 GB y crece ~4.75 GB/mes** porque el plan de migración a LFS nunca se ejecutó y `copernicus.yml` sigue haciendo `git add -A` de cada PPTX/GIF. A este ritmo los clones/push se vuelven inviables en ~3 meses.
2. **Varios feeds de vigilancia (Sala kiosko, Próximas Pasadas, Change Detection) muestran datos viejos con apariencia de frescos** sin ninguna señal de alarma — el modo de falla más peligroso en vigilancia volcánica.
3. **Dos agujeros concretos de seguridad/correctitud:** inyección de comandos vía issue en `ppt_via_issue.yml` (un externo ejecuta código en un runner con acceso a secrets) e imágenes rotas 404 en `change_detection.html` para 10 volcanes activos (Nevados de Chillán, Puyehue) justo cuando un analista abre el detalle para confirmar una ATENCIÓN/ALERTA.

Además, las acciones Node20 (`checkout@v4`/`setup-python@v4`) vencen en ~2 días, lo que podría detener todos los crones.

**La salud de fondo es buena** (la suite de tests existe, el fail-fast en auth ya está aplicado), pero la **deuda de datos** y la **falta de indicadores de stale** son los temas a atacar primero.

---

## Hallazgos críticos y altos (prioridad máxima)

| # | Sev. | Área | Archivo:línea | Problema (resumen) |
|---|---|---|---|---|
| 1 | 🔴 Crítico | Integridad de datos | `copernicus.yml:237` | El plan `MIGRACION_REPO_LFS` nunca se ejecutó: `.git` ya pesa **25 GB** y sigue creciendo por `git add -A`. Cada PPTX de ~10 MB deja un blob permanente antes de ser borrado. Cruza 40 GB en ~3 meses → clones/push inviables. |
| 2 | 🟠 Alto | Frontend correctitud/seg. | `change_detection.html:883-895,918,934-937` | `renderDetalle()` no usa `encodeURIComponent`: **10 volcanes con espacios/guiones** (Nevados de Chillán, Puyehue-Cordón Caulle, etc.) dan 404 → el analista no ve las imágenes Anterior vs Reciente que justifican el semáforo al confirmar una ATENCIÓN/ALERTA. |
| 3 | 🟠 Alto | Frontend UX/kiosko | `sala_monitoreo.html:597-605,865-890` | La Sala (pantalla desatendida 24/7) **no avisa cuando TODO el feed está stale**. Si el cron se cae, `refrescarDatos()` solo hace `console.warn` y el operador ve un panel verde con datos de días atrás. |
| 4 | 🟠 Alto | GitHub Actions / CI | `ppt_via_issue.yml:24-33,134` | **Inyección de comandos:** el body de un issue (controlado por cualquiera) se interpola sin sanitizar en `git commit -m`. Un externo puede ejecutar código en un runner con `contents: write` y acceso a `SH_CLIENT_*`/`GITHUB_TOKEN`. |

---

## Síntesis priorizada

### 🟢 Quick wins (riesgo bajo, alto retorno — varios ya aplicados en sesión)

1. **Migrar `checkout@v4` → `@v5` y `setup-python@v4` → `@v5` en TODOS los workflows.** *(GitHub Actions)* — Node20 vence en ~2 días; si GitHub lo apaga, los crones dejan de correr y los datos quedan stale sin alerta. Es un find/replace mecánico.
2. **Agregar `encodeURIComponent` a las URLs de imagen en `change_detection.html` `renderDetalle()`.** *(Frontend)* — 10 volcanes con espacios/guiones dan 404 y el analista no ve las imágenes que justifican el semáforo.
3. **Derivar `VOLCANES_ACTIVOS` del config en `timelapse_generator_auto.py`** (no lista de 43 hardcodeada). *(Python análisis)* — el generador del cron diario saltea las 6 vistas zoom; mismo bug ya corregido en el gemelo `timelapse_generator.py` pero solo en uno de los dos.
4. **Ejecutar el Paso 0 del plan LFS:** ignorar PPTX/GIF por-volcán en `.gitignore` y eliminar `git add -A`. *(Integridad de datos)* — riesgo nulo, frena el crecimiento del `.git` en seco.
5. **Corregir docstring de `gif_optimizer` (MEDIANCUT → MAXCOVERAGE).** *(Python análisis)* — una palabra evita una regresión peligrosa: un editor que confíe en el docstring podría destruir 44/44 píxeles rojos de anomalía térmica.
6. **Reemplazar `via.placeholder.com` por placeholder local en los 3 `onerror` de timelapse.** *(Frontend UX)* — el servicio fue discontinuado en 2024; cero red, cero dependencia de terceros.
7. **Unificar `concurrency` a un grupo compartido en los 3 workflows que pushean a main.** *(GitHub Actions)* — se solapan en cron; `rebase -X theirs` puede descartar silenciosamente el commit del otro bot. 1 línea cada uno.
8. **Alinear `redescargar_todos_volcanes.yml` al patrón seguro** (`merge -X ours` → `rebase -X theirs`). *(GitHub Actions)* — `merge -X ours` descarta el lado remoto: imágenes nuevas se pierden silenciosamente.
9. **Eliminar el reset manual de token cada 5 volcanes en `spectral_downloader.py`.** *(Python downloader)* — código muerto (`get_token` ya auto-renueva); su `except Exception: pass` traga fallas de auth.
10. **Hacer dinámico el label «Todos (46)» en `sala_monitoreo.html`** y actualizar conteos a 49. *(Frontend)* — el botón dice 46 pero se renderizan 49 cards.
11. **Actualizar README/STATUS/CLAUDE** con cifras reales (49 entidades, free tier 30k PU, repo 25 GB). *(Integridad de datos)* — el README decía «necesitas pagar €60/mes» cuando el tier gratis alcanza, y subestimaba el repo 30×.

### 🟠 Alto impacto (cambios de mayor calado, prioridad alta)

- **Indicador global de stale en la Sala kiosko:** banda de alarma si el feed supera N días. *(Frontend UX)*
- **Cerrar la inyección de comandos en `ppt_via_issue.yml`** (env vars + heredoc + validación contra lista cerrada). *(GitHub Actions)*
- **Mover el avance del marcador del watcher al éxito de la descarga consolidada.** *(Integridad de datos)* — si la descarga falla, el producto queda «más viejo que el marcador» y nunca se reintenta: una imagen puede perderse para siempre.
- **Corregir la dedup de misma fecha:** imagen vieja en disco con metadata de OTRO satélite/nubosidad. *(Python downloader)* — el CSV puede decir «S2B, 15% nubes» mientras el PNG es el viejo «S2A, 80%».
- **Manejar 429/503 (rate-limit) como transitorio con backoff y `Retry-After`,** no como error fatal. *(Python downloader)*
- **Indicador de frescura en Próximas Pasadas:** banner si `generado_utc` supera el umbral del cron. *(Próximas Pasadas)*
- **Corregir DST en hora Chile** (Python `zoneinfo` + HTML `toLocaleString America/Santiago`). *(Próximas Pasadas)* — el offset UTC-4 fijo deja la hora 1h corrida ~7 meses al año.
- **Acotar el `except Exception` del loop por volcán en `sentinel2_downloader.py` `main()`.** *(Python downloader)* — un bug real termina el run en VERDE con datos faltantes.
- **Reescribir el test de dedup para invocar `procesar_volcan` real** (no re-implementar la lógica). *(Tests)*

### 🔵 Proyectos grandes (refactors estructurales, planificar como sprint)

- **Unificar `metadata.csv` y filesystem a una sola fuente de verdad (filesystem).** *(Integridad de datos)* — `metadata.csv` crece sin límite y queda desincronizado (123 filas vs 38 PNG en Villarrica); la predicción ancla a metadata, no al disco.
- **Definir UN solo deployer de Pages** y limpiar el doble-deploy (`deploy.yml` vs `copernicus.yml`). *(GitHub Actions)*
- **Migrar los 4 sitios de `innerHTML` con `onclick` interpolado a `createElement`+`addEventListener` en `index.html`.** *(Frontend)* — viola la regla del hook de seguridad y rompe el zoom para nombres con apóstrofo/comilla.
- **Eliminar código muerto `loadImages`/`loadMultiVolcanoView`** y arreglar el click-en-calendario. *(Frontend)* — `loadImages` referencia IDs del DOM inexistentes y lanza `TypeError` en cada cambio de volcán (~150 líneas muertas).
- **Decidir destino de los 3 módulos legacy** (`change_detector`/`firms`/`alert`) y el workflow deshabilitado. *(Python análisis)*
- **Completar `proxima_combinada`** intercalando todos los ciclos de los 3 satélites y refrescar el box de 24h. *(Próximas Pasadas)*
- **Agregar tests de `generar_proximas_pasadas`** (DST, wraparound, guarda de historial vacío). *(Tests)*
- **Limpiar tests de feature removida** (`calcular_vrp_real`/`SWIR_raw`) y fixtures fantasma. *(Tests)*
- **Centralizar la ventana de retención** y reescribir metadata al limpiar imágenes antiguas. *(Python downloader)* — hay 3 ventanas distintas (15 búsqueda / 30 timelapse / 60 retención) sin fuente única.

---

## Tabla completa de los 44 hallazgos confirmados

| # | Área | Sev. | Archivo:línea | Problema (resumen) | Recomendación (resumen) | Esf. |
|---|---|---|---|---|---|---|
| 1 | Próximas Pasadas | 🟡 M | `generar_proximas_pasadas.py:115-121` | Offset Chile fijo UTC-4 (Python y HTML) ignora DST → 1h mal ~7 meses/año; afecta countdowns y ventana 24h | Derivar hora local con `zoneinfo('America/Santiago')`; en HTML construir Date en UTC y formatear con `toLocaleString` | M |
| 2 | Próximas Pasadas | ⚪ B | `proximas_pasadas.html:183` | El resumen «24 horas» nunca se actualiza tras la carga inicial (`renderProxima24h` fuera del `setInterval`); JSON nunca se re-fetchea | Incluir `renderProxima24h()` en el `setInterval`; re-fetch periódico del JSON cada 15-30 min | S |
| 3 | Próximas Pasadas | 🟡 M | `proximas_pasadas.html:178-180` | La UI no advierte si el JSON está viejo: stale silencioso (solo texto plano, sin umbral ni alarma) | Calcular antigüedad de `generado_utc`; banner de advertencia si supera umbral (~18h); badge por-card si la última observación >14-20d | S |
| 4 | Próximas Pasadas | 🟡 M | `generar_proximas_pasadas.py:97-101` | `proxima_combinada` solo guarda el primer ciclo por satélite → timeline de pasadas incompleto (máx 3 entradas); `[:6]` es código muerto | Intercalar TODOS los ciclos proyectados de los 3 satélites, ordenar por fecha, filtrar > hoy, recortar a 6 | S |
| 5 | Frontend correctitud/seg. | 🟠 H | `change_detection.html:883-895,918,934-937` | No usa `encodeURIComponent`: imágenes 404 para 10 volcanes con espacios/guiones (varios activos); el analista no ve Anterior vs Reciente | Envolver `nombre` con `encodeURIComponent` en todas las URLs de `renderDetalle`; extraer helper `imgUrl()` | S |
| 6 | Frontend correctitud/seg. | ⚪ B | `sala_monitoreo.html:358,113` | Conteo «Todos (46)» hardcodeado contradice las 49 entidades reales que se renderizan | Label dinámico `Todos (${TODOS_VOLCANES.length})`; actualizar comentarios y CLAUDE.md a «49 (43+6)» | S |
| 7 | Frontend correctitud/seg. | ⚪ B | `index.html:1609-1669,1592,1606,2011-2092` | `loadImages()`/`loadMultiVolcanoView()` son código muerto que lanza `TypeError` en cada carga de volcán (IDs del DOM inexistentes) | Quitar llamadas en `loadTimeline`/`selectDate` y borrar ambas funciones (~150 líneas); redirigir click-en-calendario a la comparación real | M |
| 8 | Frontend correctitud/seg. | ⚪ B | `index.html:1900,1907,1985,1997,2068,2080` | Nombre de volcán interpolado en `onclick` vía `innerHTML`: viola la regla `createElement`+`textContent`, rompe con apóstrofo/comilla | Reemplazar por `createElement`+`addEventListener`; el closure captura `volcan` sin pasar por string | M |
| 9 | Frontend correctitud/seg. | ⚪ B | `index.html:1611-1612,1893-1894,1977-1978,2344-2346` | Cache-buster `?t=Date.now()` en cada `<img>` fuerza re-descargas de PNG pesados en el muro kiosko (choca con rate-limit de raw.githubusercontent) | Usar la FECHA de la imagen como cache key (la URL ya es única por contenido); dejar cache-buster solo en JSON de índice | S |
| 10 | Frontend UX/access. | 🟡 M | `index.html:2350,2354,2418` | Placeholder de timelapse roto: `via.placeholder.com` fue discontinuado en 2024 → imagen rota o redirección a terceros | Reemplazar la `<img>` por un `div` local con `textContent` «Timelapse no disponible» (createElement) o data: URI SVG inline | S |
| 11 | Frontend UX/access. | ⚪ B | `index.html:1985,1997,2068,2080` | `innerHTML` con datos dinámicos (nombre + data-URL base64) en la vista multi-volcán; viola la regla del hook de seguridad | Construir el `<img>` con `createElement` y `addEventListener`; reutilizar helper `el()`/`clearEl()` | M |
| 12 | Frontend UX/access. | 🟠 H | `sala_monitoreo.html:597-605,865-890` | El kiosko de la Sala no avisa cuando TODO el feed está stale; `refrescarDatos()` falla silenciosamente (solo `console.warn`) | Calcular edad de la imagen más reciente vs revisita esperada (~2-3d S2); banda de alarma si supera N días; detectar K ciclos de refresco fallidos | M |
| 13 | Frontend UX/access. | ⚪ B | `sala_monitoreo.html:800-813` | Imágenes satelitales sin `alt` y controles clickeables sin acceso por teclado (sin `role`/`tabindex`) | Agregar `img.alt`; `role="button"`+`tabindex="0"`+keydown (Enter/Espacio) o convertir a `<button>` | S |
| 14 | Frontend UX/access. | ⚪ B | `proximas_pasadas.html:56-59` | Grid con tarjeta mínima 360px desborda en móvil angosto (~320-360px); única página del set sin `@media query` | Bajar mínimo a `minmax(min(100%,360px),1fr)` o añadir `@media (max-width:480px)` con `1fr` | S |
| 15 | Python downloader/auth | 🟡 M | `sentinel2_downloader.py:605-628` | Imagen reusada de disco queda con metadata de OTRO satélite/nubosidad (dedup vs `MODO_SOBRESCRITURA`): el CSV miente sobre la escena mostrada | Al hacer skip por `os.path.exists`, no appendear metadata del dedup-winner; o incluir satélite en el nombre; o forzar re-descarga si difiere (opción más simple) | M |
| 16 | Python downloader/auth | ⚪ B | `spectral_downloader.py:110-117` | Refresh manual de token cada 5 volcanes es código muerto (`get_token` ya auto-renueva) y el `except Exception: pass` traga fallas de auth | Eliminar el bloque `if i % 5 == 0`; si se quiere forzar renovación, hacerlo sin el `except: pass` | S |
| 17 | Python downloader/auth | 🟡 M | `sentinel2_downloader.py:72-86,237-265,363-389` | `es_error_cuota` no cubre 429 ni `Retry-After`: rate-limit transitorio se trata como error fatal → imagen perdida sin señal | Tratar 429/503 como transitorio: `sleep(retry_after o backoff)` + `continue` sin consumir presupuesto de cuentas; leer `Retry-After` | M |
| 18 | Python downloader/auth | 🟡 M | `sentinel2_downloader.py:711-722` | El `except Exception` en `main()` traga TODO error por volcán (KeyError, pandas, FS) → run VERDE con datos faltantes | Acotar el `except` a excepciones esperadas o acumular fallos y `sys.exit(1)` al final; imprimir `traceback.format_exc()` | S |
| 19 | Python downloader/auth | ⚪ B | `sentinel2_downloader.py:459-495` | Retención de 60d vs ventana de búsqueda de 15d: 3 ventanas sin fuente única; borrado por orden lexicográfico de strings frágil | Centralizar retención en `config_sentinel2.py` (`RETENCION_DIAS`); parsear fecha con `strptime` y saltar nombres que no parsean | S |
| 20 | Python downloader/auth | ⚪ B | `sentinel2_downloader.py:278,287` | Parsing STAC frágil: lee campos OData/legacy (`startDate`, `cloudCover`) inexistentes en el STAC actual; funciona solo por el último fallback; default `0` peligroso para dedup | Simplificar a claves STAC reales (`datetime`, `eo:cloud_cover`) con manejo explícito de None; quitar nombres OData muertos | S |
| 21 | Python análisis/gen. | 🟡 M | `timelapse_generator_auto.py:20-33,316` | Timelapses del dashboard saltan las 6 vistas zoom (lista de 43 hardcodeada); el gemelo `timelapse_generator.py` ya fue corregido | Derivar la lista del config: `[n for n,c in VOLCANES.items() if c.get("activo")]` (single source of truth) | S |
| 22 | Python análisis/gen. | ⚪ B | `generar_proximas_pasadas.py:60,72` | Crashea con `KeyError: 'volcan'` si ningún volcán tiene `metadata.csv` (DataFrame vacío sin columnas); el cron falla y el JSON no se regenera | Guarda temprana `if historial.empty or 'volcan' not in columns`; o `cargar_historial` retorna DataFrame con columnas tipadas | S |
| 23 | Python análisis/gen. | ⚪ B | `ppt_generator.py:128-129` | Rutas `/tmp` hardcodeadas: no existe en Windows (entorno local del usuario) y el nombre sin tipo/timestamp puede colisionar | Usar `tempfile.gettempdir()` / `NamedTemporaryFile`; portable a Windows y evita colisiones | S |
| 24 | Python análisis/gen. | ⚪ B | `change_detector.py (archivo completo)` | 3 módulos legacy (`change_detector`, `firms_integration`, `alert_generator`) solo los usa un workflow deshabilitado; umbrales obsoletos y divergentes | Borrar los 3 + el workflow `deteccion_cambios.yml`, o moverlos a `legacy/` con README; mínimo, docstring «LEGACY — no usar» | S |
| 25 | Python análisis/gen. | ⚪ B | `gif_optimizer.py:142-144,170-171` | El docstring dice MEDIANCUT pero el código usa MAXCOVERAGE (correcto); riesgo de que un editor «corrija» y destruya 44/44 píxeles rojos | Corregir el docstring a MAXCOVERAGE, alineado con el print y la lección de CLAUDE.md | S |
| 26 | GitHub Actions / CI | 🟠 H | `ppt_via_issue.yml:24-33,134` | Inyección de comandos: input de issue no confiable interpolado en `git commit -m`; externo ejecuta código con `contents: write` y acceso a secrets | Pasar valores solo como `env:` y referenciar `"$VOLCAN"`; validar contra lista cerrada de VOLCANES; heredoc en `$GITHUB_OUTPUT`; restringir trigger | M |
| 27 | GitHub Actions / CI | 🟡 M | `deploy.yml:3-29` | `deploy.yml` dispara doble despliegue de Pages en cada push del bot; grupos de concurrency distintos → race, puede publicar `_site` más viejo | Elegir UN solo deployer; quitar el deploy de `copernicus.yml` o el trigger `push` de `deploy.yml`; o unificar grupo de concurrency | S |
| 28 | GitHub Actions / CI | ⚪ B | `deploy.yml:7-13` | `workflow_run.workflows` lista nombres de workflow inexistentes → ese trigger nunca dispara (config muerta engañosa) | Eliminar el bloque `workflow_run` (redundante con `push`) o corregir los nombres a los reales | S |
| 29 | GitHub Actions / CI | 🟡 M | `.github/workflows/ (múltiples)` | `checkout@v4`/`setup-python@v4` corren sobre Node20 en deprecación (deadline ~16-jun-2026); si GitHub lo apaga, los crones fallan → datos stale | Subir a `@v5` (o pin a SHA) en TODOS los workflows; verificar `upload/download-artifact@v4`; probar con `workflow_dispatch` | S |
| 30 | GitHub Actions / CI | 🟡 M | `copernicus.yml:28-30` (+ change_analysis, spectral) | 3 workflows de escritura pushean a main en distinto cron sin concurrency compartida; `rebase -X theirs` puede descartar el commit del otro bot | Grupo de concurrency COMPARTIDO (`group: repo-write-main`, `cancel-in-progress: false`) en los tres | S |
| 31 | GitHub Actions / CI | 🟡 M | `redescargar_todos_volcanes.yml:98-116` | `merge origin/main -X ours` descarta el lado remoto: imágenes nuevas subidas por `copernicus.yml` durante la re-descarga se pierden | Alinear al patrón seguro (`merge --ff-only` + `pull --rebase -X theirs` con abort) o sumar al grupo de concurrency compartido | S |
| 32 | GitHub Actions / CI | ⚪ B | `deteccion_cambios.yml:8-9,118-120` (+ `sentinel2_auto_DESHABILITADO.yml`) | Workflows DESHABILITADO/legacy retienen `contents: write` y secrets sin necesidad; `deteccion_cambios` usa `-X ours` inseguro | Eliminar los workflows muertos (la historia git los conserva) o quitarles `contents: write`+secrets y migrar `-X ours` → `-X theirs` | M |
| 33 | Integridad de datos | 🔴 C | `copernicus.yml:237` | El plan `MIGRACION_REPO_LFS` nunca se ejecutó: `.git` ya pesa 25 GB y crece ~4.75 GB/mes por `git add -A`; cruza 40 GB en ~3 meses | Ejecutar Paso 0: ignorar PPTX/GIF por-volcán en `.gitignore` + adds explícitos; audit defensivo; luego decidir LFS vs R2; `filter-repo` con backup | M |
| 34 | Integridad de datos | 🟡 M | `sentinel2_downloader.py:459-495` | `metadata.csv` crece sin límite y queda desincronizado del filesystem (123 filas vs 38 PNG en Villarrica); dos fuentes de verdad divergentes | Reescribir `metadata.csv` al limpiar PNGs (mismo umbral 60d) o derivar del filesystem; unificar a UNA fuente (el disco) | M |
| 35 | Integridad de datos | 🟡 M | `copernicus.yml:68-82` | El marcador del watcher avanza al detectar, no al descargar; si la descarga falla, el producto queda «más viejo que el marcador» y nunca se reintenta | Avanzar el marcador solo al éxito de la descarga consolidada; o usarlo como ventana inferior, no como gate de reintento | M |
| 36 | Integridad de datos | ⚪ B | `STATUS.md:5` | Conteo de entidades inconsistente en toda la doc: el código tiene 49 (43+6), los docs dicen 43/46 | Actualizar a «49 entidades (43 volcanes + 6 vistas zoom)» en README/STATUS/CLAUDE; mejor, apuntar a `config_sentinel2.py`; auditar tests por `==46` |  S |
| 37 | Integridad de datos | 🟡 M | `README.md:333-347` | README documenta cifras de recursos groseramente erróneas (repo 800 MB vs 25 GB real; free tier 10k PU vs 30k; «requiere plan €60/mes») | Reescribir «Uso de Recursos» con números reales (free tier 30k, ~3k consumidos, watcher OData a 0 PU); corregir tamaño del repo; quitar plan de pago | S |
| 38 | Integridad de datos | ⚪ B | `STATUS.md:49` | STATUS describe cron obsoleto (2×/día 10/20 UTC) que ya no existe; el real es watcher `*/15 17-21` + `*/15 0-3`; hora de paso desactualizada | Actualizar STATUS: fecha, conteo 49, arquitectura watcher, hora de paso 14:26-14:37 UTC | S |
| 39 | Tests y calidad | ⚪ B | `test_change_analysis.py:91-145` (+ `conftest.py:112-142`) | `calcular_vrp_real` y sus 6 tests prueban una feature ya removida (`SWIR_raw`); fixtures fantasma → falsa cobertura sobre VRP-en-Watts | Skip con motivo documentado, o borrar los 6 tests + fixtures + la rama muerta de `change_analysis.py`; borrar fixtures `tmp_png_*` sin uso | S |
| 40 | Tests y calidad | ⚪ B | `test_descarga.py:91-133` | El test de failover no cubre el modelo real per-proceso: la matrix por zona arranca 4 procesos con `active=0` cada uno (estado no compartido) | Test que documente el contrato per-proceso (2 `SentinelHubAuth` separados, uno rota y el otro sigue en `active=0`); comentario en el código | M |
| 41 | Tests y calidad | 🟡 M | `test_descarga.py:138-162` | El test de dedup re-implementa la lógica en vez de llamar a `procesar_volcan`: es una tautología (cambiar `<` por `<=` deja el test verde) | Reescribir para ejercitar `procesar_volcan` real con searcher mock (2 escenas misma fecha, cloud 80 y 15); caso `cloud_cover` None/ausente | M |
| 42 | Tests y calidad | ⚪ B | `generar_proximas_pasadas.py:115-121` | `calcular_hora_chile` hardcodea UTC-4 sin DST y no tiene ningún test; la hora se va 1h en verano | Corregir con `zoneinfo('America/Santiago')` o documentar el offset fijo; agregar `tests/test_proximas_pasadas.py` (verano vs invierno, wraparound medianoche) | M |
| 43 | Tests y calidad | ⚪ B | `test_config.py:36-56` | Conteos hardcodeados (49/43/6) y `tests/README.md` aún dice 46; cada alta/baja obliga a editar 3 asserts | Reemplazar conteos mágicos por invariante derivada (`len(principales)+len(zoom)==len(VOLCANES)`); actualizar `tests/README.md` y CLAUDE.md | S |
| 44 | Tests y calidad | ⚪ B | `test_json_outputs.py:26-99` | Tests de JSON públicos usan `skipif(not exists)` y muestreo de 5: un JSON vaciado/corrupto pasa silencioso (skip = verde) | Separar «existe» de «es válido»: test sin `skipif` que assertee que ambos JSON existen y no están vacíos; quitar el `[:5]` (iterar los ~49) | S |

> **Leyenda esfuerzo:** S = pequeño (minutos–1h) · M = medio (varias horas–1 día).

---

## Lo que NO se auditó (gaps de cobertura)

La auditoría fue exhaustiva pero no total. Estos frentes quedaron **fuera de alcance o sin profundizar** y conviene cubrirlos en una pasada posterior:

1. **Observabilidad / logging (todo el backend Python).** Ningún módulo usa `logging`: 0 de 18 archivos lo importan, hay 295 llamadas a `print()`. Sin niveles (INFO/WARN/ERROR) ni timestamps, un 403 de cuota no se distingue del output normal en los logs de Actions. No hay métrica de imágenes descargadas vs esperadas que permita detectar degradación.
2. **Inyección en workflow disparado por issue (`ppt_via_issue.yml`) — análisis profundo.** Más allá del hallazgo #26: confirmar si `volcan='$(...)'` o con backticks ejecuta shell, si el gate de label es suficiente, y el alcance real del `GITHUB_TOKEN`. Revisar también `ppt_individual_workflow.yml`.
3. **Supply chain / SRI en frontend (`cog_viewer.html`).** Leaflet 1.9.4 se carga desde unpkg.com **sin `integrity` ni `crossorigin`** (0 usos de `integrity=` en todo `docs/`). Las libs vendoreadas (gif.js 0.2.0 de 2018, jszip, pptxgen) no tienen hash ni chequeo de CVEs.
4. **CVEs y pinning de dependencias Python (`requirements.txt`).** Usa floors `>=` sin techo ni lockfile; builds no reproducibles entre runs. Pillow y tifffile históricamente acumulan CVEs de parsing (relevante: el pipeline procesa PNG/TIFF de origen externo). Verificar si hay Dependabot activado.
5. **Licencia y cumplimiento legal.** No existe `LICENSE`/`COPYING` pese a ser un dashboard público (→ «todos los derechos reservados» por defecto, choca con reutilización académica/SERNAGEOMIN). Verificar attribution statements de Copernicus/Sentinel-2 y Landsat, y los notices de licencia de las libs vendoreadas.
6. **Tests ausentes en módulos secundarios.** 10 de 11 módulos sin ningún test: `alert_generator`, `change_detector`, `firms_integration`, `gif_cache`, `gif_optimizer`, `image_compression`, `spectral_downloader`, `timelapse_generator`, `timelapse_generator_auto`, `generar_proximas_pasadas`. Priorizar `alert_generator` (genera los `.md` de ALERTA), `gif_optimizer` (cuantización MAXCOVERAGE) e `image_compression` (puede corromper datos científicos). Tampoco se sabe si `scripts/` (watcher_odata, etc.) tienen tests.
7. **Repo hermano `Landsat-v1` (dependencia externa de datos).** El dashboard consume imágenes Landsat desde raw.githubusercontent del repo externo. No se auditó: manejo de error/fallback si está caído o renombra archivos, rate limits/latencia de CDN, riesgo de URL mal codificada con nombres con espacios, ni el pipeline propio de `Landsat-v1`.
8. **Integridad de datos: drift doc/repo y volumen versionado.** Existe `MIGRACION_REPO_LFS.md` pero NO hay `.gitattributes` ni LFS. Se versionan en git plano 4447 PNGs, 2098 `.md` de alertas (data derivada regenerable) y 136 timelapses. Confirmar si hay purga efectiva o el repo crece sin techo.
9. **Accesibilidad profunda.** Los 8 `<img>` dinámicos de `index.html` tienen 0 atributos `alt`. Auditar a fondo: navegación por teclado en modos Multi/Zona/Personal, contraste WCAG AA de los colores de estado, operabilidad sin mouse de toggles y calendario, roles ARIA, `aria-live` en countdowns y alertas, `lang=es` en todos los HTML.
10. **Módulos poco usados no auditados (`firms_integration`, `change_detector`, `gif_cache`).** `firms_integration` construye URL con la `NASA_FIRMS_API_KEY` embebida en el path (verificar que no se loguee). `change_detector` (209 líneas) parece duplicar/preceder a `change_analysis.py` (1678) — ¿código muerto o segunda implementación divergente? `gif_cache` — revisar invalidación (puede servir un GIF viejo).
11. **Manejo de secretos en runtime y superficie de fuga.** 4 clases de secreto (`SH_CLIENT_ID/SECRET` + `_2/_3`, `NASA_FIRMS_API_KEY`, `GITHUB_TOKEN`). Confirmar que los mensajes de error verbosos nunca imprimen el VALOR del token, que el token CDSE no se escribe a disco accesible en `docs/`, y que ningún `.md`/JSON de salida embebe credenciales.
12. **Resiliencia de Próximas Pasadas y predicción (sub-auditado).** `generar_proximas_pasadas.py` (158 líneas) sin tests. Auditar: comportamiento si el cron falla un día (¿countdowns negativos?), manejo de la constelación 2A/2B/2C (¿2C ya operativo cambia las predicciones?), y zona horaria/DST chileno. `proximas_pasadas.html` (350 líneas) no se auditó en profundidad.

---

> **Nota:** Este informe se generó el **2026-06-08**; varios quick wins se aplicaron en la misma sesión (ver `git log`). El estado de cada hallazgo debe contrastarse contra los commits posteriores a esa fecha antes de actuar.
