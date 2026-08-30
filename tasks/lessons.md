# Lecciones aprendidas — Copernicus-v1 / Landsat-v1

Patrones y errores para no repetir. (Se carga al inicio de sesión.)

## Arquitectura de datos satelitales

- **Hay DOS catálogos en CDSE**: Sentinel Hub Catalog API (`sh.dataspace…`, **consume PU**) y OData Catalogue (`catalogue.dataspace…`, **GRATIS, sin token, sin PU**). Para DETECTAR imágenes nuevas usar siempre OData; el que cuesta PU solo para renderizar (Process API).
- **Watcher pattern (deteccion event-driven)**: un job barato gatea el pipeline caro. Copernicus: `scripts/watcher_odata.py` (OData) → gate de descarga. Landsat: `scripts/watcher_m2m.py` (M2M scene-search Chile-wide, 1 query) → gate. Marcador en `docs/.s2_last_pub.json` / `docs/.landsat_last_pub.json` evita re-disparos. Dispatch manual debe forzar `has_new=true`.
- **USGS M2M es gratis** (10k descargas/día, sin tarjeta). Devuelve `publishDate` con offset `-05` (solo horas) → Python `%z` no lo parsea hasta 3.11; normalizar a `-0500` (`if re.search(r"[+-]\d{2}$", s): s += "00"`).
- **Frescura real S2 sobre Chile**: paso 14:26-14:37 UTC; L2A publicado mediana 4.7h, P95 11.7h, BIMODAL (picos 18-20 UTC y 01-02 UTC). Cron concentrado en esos picos. Landsat publica ~T+1d a horas variables → cron horario.
- **CORS importa en el browser, no en Python/curl**. Un endpoint que anda en Python puede dar `Failed to fetch` en el navegador. Verificar SIEMPRE en navegador real (Chrome MCP) antes de afirmar que algo funciona client-side.

## COG viewer — por qué NO migrar a client-side (verificado 2026-06)

Spike de visor client-side (OpenLayers + COG público) descartado tras prueba hands-on. 3 blockers para sitio estático SIN build step:
1. **CORS**: bucket Earth Search `c1-l2a` (`e84-earth-search-sentinel-data`) NO tiene CORS. El clásico `sentinel-cogs` (colección `sentinel-2-l2a`) SÍ.
2. **Reproyección**: COG en UTM por zona; OpenLayers WebGLTile no reproyecta a 3857. Renderer se congela.
3. **Dependencias**: `ol/source/GeoTIFF` desde CDN exige versión exacta de geotiff.js (`TypeError evictedBlocks.clear`) → necesita bundler.
→ **Server-side tiling (PC titiler) es la arquitectura correcta** para visor interactivo en sitio estático. PC sirve fresco T+1d. Mantener `cog_viewer.html`.
- **PC titiler `assets` debe ir como params REPETIDOS** (`assets=B04&assets=B03`), NO comma-joined (da 404). Expresiones (NDVI) necesitan `asset_as_band=true`.

## Workflows / GitHub Actions

- **Repo público = Actions ilimitados** (no aplican los 2000 min/mes). El límite real es PU de CDSE, no minutos.
- **Cron secuencial de 46 volcanes da timeout**. Partir en matrix paralela por zona (Norte/Centro/Sur/Austral) + job consolidador. Cada artifact debe contener SOLO su zona (sino se pisan los CSV al mergear).
- **Pages no se redespliega con un push simple** si el deploy es por workflow. Disparar `deploy.yml` o esperar al cron consolidador.
- **`except Exception` que silencia imports faltantes** ocultó dos bugs (numpy, pandas faltantes en `ppt_timelapses_workflow.yml` → filtro de nubes se saltaba). Instalar TODAS las deps que el script importa.
- **JSON pisado por workflow paralelo**: `buscar_fechas_workflow.yml` regeneraba el JSON desde la API y, en 403, escribía arrays vacíos pisando el correcto. Desactivado; el JSON lo regenera el downloader escaneando el filesystem.
- **`.claude/worktrees/` commiteado como submódulo fantasma** rompió `pages-build-deployment` en Landsat-v1 (`fatal: No url found for submodule`). `.claude/` debe estar en `.gitignore`.
- **Pages artifact ≤1GB (2026-06-08)**: el artifact = `docs/` entero. Las imágenes (sentinel2 ~1.9GB + timelapses ~263MB) lo pasaban de 1GB ("Deployment might fail"). PERO el dashboard las sirve desde **raw.githubusercontent** (`REPO_BASE`), NO desde Pages → eran peso muerto. Fix: el deploy arma `_site` con `rsync -a --exclude 'sentinel2/' --exclude 'timelapses/' docs/ _site/` y sube eso (~30MB); las imágenes siguen en git (raw las sirve). **Hay DOS deploys: `copernicus.yml` Y `deploy.yml`** — los dos necesitan el fix. Antes de excluir carpetas, pasar a `REPO_BASE` las páginas que cargaban con ruta relativa (change_detection, comparación 2×2 de index, gif_builder, sala_monitoreo) — si no, dan 404 al salir de Pages.

## Cuenta CDSE / PU

- Consumo se dispara con: cada evalscript extra (+33% por POST/escena), dispatches manuales de debugging, `buscar_fechas` cada 6h. Régimen estacionario con watcher: ~3k PU/mes de 30k (~10%, ~9× de margen).
- Cuota resetea el día 1 del mes. Tener cuenta backup. Secrets son write-only (no se leen por API).
- **Fuga de PU detectada y tapada (2026-06-07)**: el workflow instalaba deps a mano (`pip install requests pandas pytz Pillow`) y se olvidaba de `tifffile`. `SWIR_raw` hacía el POST (gastaba PU), recibía el TIFF y fallaba en `import tifffile` → **0 `.npz` en 2810 PNG**, ~33% de PU tirado por escena, y VRP-real de `change_analysis.py` muerto. Fix raíz: workflows usan `pip install -r requirements.txt` (centraliza deps, evita "olvidé una"). **Verificar siempre que el workflow instale lo que el script importa, no una lista a mano.**
- **Cuántos PU cuesta cada cosa**: render por escena = N POSTs (1 por composite). Hoy son **3** (RGB, ThermalFalseColor, SWIR_B8A). Agregar/quitar un composite mueve ±33%. La detección OData (watcher) es GRATIS, no cuenta.
- **SWIR_raw REMOVIDO de Copernicus (2026-06-07)**: el VRP calibrado en Watts (Coppola/Wooster) lo hace el proyecto aparte **VRP Chile**; acá no se duplica (ahorra 1 POST/escena). El evalscript `EVALSCRIPT_SWIR_RAW` queda dormido en `config_sentinel2.py` por si se quiere revivir, pero NO está en el loop de descarga. `change_analysis.py` cae al proxy del PNG (no hay `.npz`).
- **Ventana de búsqueda configurable** (`--dias`, default 60; workflow usa **15**): limita el backfill. Bajarla NO afecta el régimen estacionario (las escenas nuevas se bajan dentro de los 15 días de su paso igual). Subirla solo sirve para recuperar un hueco viejo grande.
- **El ~3k/mes era OPTIMISTA / desactualizado (2026-06-07)**: un dispatch real mostró la cuenta **403 "Insufficient processing units"** = SECA. El consumo real venía más alto (la fuga de SWIR_raw + dispatches). **No confiar en el número documentado para decir "hay margen": verificar con un dispatch o el dashboard de CDSE.** El balance de PU NO se puede leer por API (secrets write-only) → mirar el dashboard web de CDSE.

## Falla silenciosa de cuota — y failover multi-cuenta (IMPLEMENTADO 2026-06-07)

**El bug que lo destapó**: cuando la cuenta está sin PU, el catálogo devuelve **403 en la BÚSQUEDA** (antes de cualquier descarga). Ese 403 caía en el `except RequestException` → `return []` → "No hay imágenes" → **job VERDE con 0 descargas**. El fail-fast (lección #4) solo cubría el *token*, no la búsqueda. Resultado: una cuenta seca se veía "sana" por días.

**Fix + failover** (en `SentinelHubAuth`, `search_images`, `download_image`):
- **`CREDENTIAL_SETS`** en `config_sentinel2.py`: lee `SH_CLIENT_ID`/`SECRET` (primaria) + `SH_CLIENT_ID_2`/`SECRET_2`, `_3`... (env). Los workflows pasan los `_2` como env (vacíos si no existen → 1 cuenta, sin romper).
- **`es_error_cuota(response)`**: distingue 403-de-cuota ("insufficient/processing unit/credit/quota") de 403-credenciales-malas. **Es 403, NO 429** (CDSE manda 403 con ese texto).
- **`rotate_account()`**: en 403-cuota, rota a la cuenta siguiente y re-pide token. Si se agotan TODAS → `SystemExit` → **run en ROJO** (ya no se disfraza de éxito).
- Token 401/403 (creds malas): rota si hay backup; si no, `SystemExit`.
- **Activación**: cargar `SH_CLIENT_ID_2`/`SH_CLIENT_SECRET_2` como GitHub Secrets. El código ya está; se activa solo.
- Tests: `test_descarga.py` cubre `es_error_cuota`, `rotate_account`, fetch con rotación, y search-403 con/sin backup.

## Frontend / Sala de Monitoreo

- **localStorage es por-origen, COMPARTIDO entre pestañas**. 4 kioskos en el mismo navegador pisaban la zona entre sí. Solución: persistir la zona en la URL de cada pestaña (`history.replaceState`), no en localStorage.
- **revision_volcanes.html**: vistas zoom son sub-áreas (cráter) → radio mínimo 0.1 km (no 0.3 del volcán completo). Pre-llenar lat/lon del padre. No descartar en silencio: avisar qué falta y de qué volcán.

## Composites / evalscripts

- **Agregar un composite visible toca 4 capas**: (1) `EVALSCRIPT_*` + registro en `EVALSCRIPTS` (`config_sentinel2.py`); (2) el loop de descarga en `procesar_volcan` (`sentinel2_downloader.py`); (3) el loop de timelapses (`timelapse_generator_auto.py`) + su label por-tipo + la detección de cuantización MAXCOVERAGE (`'swir'`/`'thermal'`/`'falso'` en el nombre); (4) el dashboard (`docs/index.html`). Tests en `test_evalscripts.py` (LINEAL vs sRGB, bandas, orden) y conteos en `test_descarga.py` (`len(res)`, `call_count`).
- **SWIR_B8A (2026-06-07)**: 4º composite = B12/B11/B8A. Igual que el thermal pero 3er canal B8A (NIR-angosto 865nm, 20m nativo) en vez de B04 (rojo 10m) → sin resampling, mejor separa anomalía/veg/nieve. LINEAL (gamma aplana la anomalía roja). Dashboard: toggle global `composite2` con botón en la card SWIR del timelapse automático; todas las vistas leen esa var.
- **Cuantización GIF**: cualquier composite con B12/B11 (rojos puros de anomalía) necesita `MAXCOVERAGE`, no ADAPTIVE/MEDIANCUT (descartan los outliers rojos). La detección en `timelapse_generator_auto.py` matchea `thermal`/`falso`/`swir` en el nombre del tipo.
- **Bug import por firma cambiada (2026-06-07)**: `spectral_downloader.py` llamaba `SentinelHubDownloader()` sin el arg `auth` (la firma cambió a `__init__(self, auth)`) → el workflow de índices fallaba siempre. Lección: al cambiar una firma de `__init__`, grepear TODOS los `ClaseX(` del repo.

## Dashboard — estructura real (cuidado con código legacy)

- **`loadImages()` + `rgb-container`/`thermal-container` son legacy/rotos**: esos ids NO existen en el HTML estático (el `#timeline` está `display:none`). La vista individual REAL = `#timelapse-automatico` (cards RGB + SWIR con GIFs `timelapse-rgb-auto`/`timelapse-thermal-auto`) + la comparación 2×2 (`actualizarComparacion`). Antes de "agregar al panel individual", confirmar en navegador qué se ve de verdad — no asumir por el nombre de la función.
- Verificación client-side: `preview_eval` para flippear estado y leer URLs/labels es más confiable que screenshot (el dashboard dispara ~49 fetches a raw.githubusercontent y el screenshot puede timeoutear sin que nada esté roto).

## Convenciones

- Vistas zoom en `config_sentinel2.py:VOLCANES` con campo `vista_zoom_de` apuntando al padre. Regenerar `docs/volcanes.js` con `scripts/generar_volcanes_js.py` tras cualquier cambio de coords.
- Tests en `tests/` (pytest). Actualizar conteos hardcodeados (46→49 entidades, etc.) al agregar volcanes/zooms.

## El calendario anunciaba pasadas que NO ocurrían: fases espurias (2026-08-14)

- **Cómo se detectó**: backtesting. Parándose en un corte del pasado, calculando las pasadas con SOLO el histórico anterior y comparando contra lo que realmente ocurrió. Resultado inicial: **cobertura 98,8-100%** (nunca se pierde una imagen real) pero **acierto de sólo 82-89% en S2 y 68-89% en Landsat** → 1 de cada 5 pasadas anunciadas no producía imagen. Para un turno que planifica con eso, es información que no se cumple.
- **Causa raíz**: el generador tomaba **todas** las fases orbitales (`día_ordinal % ciclo`) vistas en la ventana de 35 d y las proyectaba con igual peso. Las fases que aparecen 1-2 veces son **solapes marginales del borde del swath** —el volcán cae en el filo de la traza y a veces queda afuera—, no pasadas regulares.
- **La separación es nítida** (backtest): en S2, fase vista **≥3 veces → 100% de acierto**; vista ≤2 → **27%**. En Landsat el umbral es 2 (ciclo de 16 d: una fase regular sólo alcanza a aparecer 2 veces en 35 d): **≥2 → 100%**, 1 vez → 80%.
- **Fix**: no se descartan (sería ocultar información), se **califican**. Campo `confianza: alta|baja` por pasada, con umbral derivado del ciclo (`VENTANA_FASES_DIAS // CICLO_DIAS`, mínimo 2): da 3 para S2 y 2 para Landsat sin hardcodear. En el calendario, las de baja confianza se pintan **huecas** (borde sin relleno) y el tooltip dice "PROBABLE (pasada de borde)". KPI nuevo: "de ellas seguras".
- **Impacto**: S2 marca 299/834 (36%) como probables; Landsat sólo 8/377 (2%).
- **Lección de método**: una predicción se valida con **backtesting**, no mirando si "parece razonable". Y hay que medir **dos** métricas: acierto (¿lo anunciado ocurre?) y cobertura (¿nos perdemos algo?) — acá la cobertura era perfecta y el acierto malo, y sólo una de las dos lo habría mostrado.

## Las pasadas SON deterministas: medido empíricamente (2026-08-14)

- **La órbita no cambia y se puede calendarizar.** Medida la hora real de captura sobre escenas del catálogo OData: **Villarrica 14,54 UTC ± 5 min** (120 escenas / 120 días) y **Lascar 14,62 UTC ± 25 segundos** (30 escenas). Es órbita heliosincrónica: cruza cada punto a la misma hora solar por diseño. **No hubo ningún cambio de órbita** en el histórico.
- **Los intervalos entre imágenes son un conjunto CERRADO**: sobre 2.671 intervalos de S2, sólo aparecen **1, 2, 3 y 5 días** — el 100% de los casos, nunca un 4, 6 o 7. Test de periodicidad: 5 d cumple 86,9%, 10 d 87,9%, **20 d 97,8%**. Landsat: **8 d 98,4%**, 16 d 98,3%, 32 d 98,8%.
- **La revisita NO es igual para todos los volcanes — depende de la latitud.** Centro-sur (Chillán, Longaví, Tatara ~36°S): patrón 1+2+3, **revisita 2,2 d**. Norte (Taapaca, Parinacota, Guallatiri, San Pedro ~18-22°S): patrón 2+3+5, **revisita 4,2 d**. Causa: las trazas orbitales convergen hacia los polos → más solape entre pasadas adyacentes a mayor latitud. **Un volcán del norte se ve casi la mitad de seguido**, y eso cambia cuánto puede tardar en detectarse un cambio. Publicado por volcán en `proximas_pasadas.json` como `revisita_mediana_d`.
- **No hay demoras de días en S2**: 0 casos >24 h en 150 escenas (máx observado 20,3 h). El "clúster de ~60 h" que figuraba en la nota de abajo es de la latencia hasta el dashboard (git log), no del proveedor.
- **Cómo medirlo sin gastar PU**: el catálogo **OData es gratis y sin token** (`PublicationDate` − `ContentDate/Start`). Es el mismo endpoint del watcher. Script: `scratchpad/latencia_odata.py`.
- **Horizonte del generador**: `generar_proximas_pasadas.py` guardaba sólo **las 6 pasadas más cercanas** (~14 d), insuficiente para una vista mensual. Ahora usa `HORIZONTE_DIAS = 35` y publica todas las de ese rango (834 entradas). Consumidores (`countdown.js`, Sala) usan el primer futuro, así que más entradas no rompen nada.
- **`toISOString()` corre la fecha un día en Chile** (UTC-4/-3) y desalineaba el calendario. Usar ISO local armado a mano con `getFullYear/getMonth/getDate`.

## Latencia de publicación y cuenta regresiva (2026-06-12)

- ⚠️ **Ojo: hay DOS latencias distintas y se confundían** (aclarado 2026-08-09). (a) **Latencia del PROVEEDOR** = captura → publicación en el catálogo de ESA; (b) **latencia hasta NUESTRO dashboard** = la anterior + el ciclo del cron + el commit. Lo medido abajo con git log es (b). Medido con OData (`PublicationDate` − `ContentDate/Start`, gratis y sin PU) sobre **150 escenas reales**, la latencia (a) es bastante MEJOR: **Villarrica mediana 5,6 h · P95 12,6 h · máx 20,3 h · 0 casos >24 h en 120 escenas/120 días**; Lascar mediana 5,8 h, máx 11,3 h. Al comunicar "cuánto tarda la imagen", decir cuál de las dos se está citando.
- **Latencia real captura→publicación (auditada con git log `--diff-filter=A`)**, excluyendo backfills (cargas masivas contaminan con falsos "+28 días"). **Esto es la latencia (b), hasta el dashboard**:
  - **S2**: modo 6,3–7,6 h tras el paso (67% de escenas), mediana 7,6 h, 73% <24 h. Clúster secundario ~60 h (nuboso/L2A demorado).
  - **Landsat**: nunca <30 h. Modos ~30 h (33%) y ~44 h (62%), mediana 44 h, 95% <48 h. La intuición "casi un día" es optimista: es 1,25–2 días.
- **Contador en Sala = paso (casi-certeza orbital) + ventana de imagen (distribución), NO número al minuto.** Mostrar falsa precisión ("falta 2h14m") se equivoca seguido por latencia variable + nubes. Decisión: cuenta regresiva al paso + rango ("~6-8h" / "~1-2 días"). Estado "imagen en camino" cuando el paso ya ocurrió, dentro del horizonte de latencia, y la imagen aún no está (comparar `proxima_combinada[].fecha` vs última fecha en `fechasS2/fechasLandsat`).
- **metadata.csv de Landsat MEZCLA formatos**: el header dice `satelite` pero en filas nuevas esa columna trae el `scene_id` completo (`LC08_L2SP_...`), no `landsat-8`. Parsear el satélite por regex `LC08`/`LC09` sobre scene_id (fuente confiable), no por la columna. Un filtro ingenuo `== 'Landsat-8'` descartaba SILENCIOSAMENTE las filas nuevas → ancla de predicción vieja por semanas (la fase salía bien igual por ser módulo-16, pero la última observación estaba mal).
- **Predicción de pasadas Landsat**: ciclo 16 d exacto por satélite (L8/L9 desfasados 8 d → combinada ~8 d). Boundary `< hoy` (no `<=`): un paso de HOY se conserva como próximo porque la imagen se publica 1-2 días después (sigue pendiente). El generador S2 usa `<= hoy` (latencia corta, no hace falta).

## Git con repos pesados de imágenes + OneDrive (2026-06-12)

- **El cron commitea seguido reescribiendo ~126 PNGs binarios**. Si quedaste atrás N commits, `git pull --rebase` baja un pack enorme y se cuelga ("fatal: fetch-pack: invalid index-pack output" justo en el timeout). Solución: `git fetch --depth=1 origin <branch>` (solo el snapshot del tip, segundos) + reaplicar tu commit con `git rebase --onto <tip> <viejo-origin> HEAD`. Como tus cambios suelen ser solo HTML, no hay conflicto con los datos. Efecto colateral: el repo local queda shallow → correr `git fetch --unshallow` después con buena conexión.
- El stall se agrava porque el `.git` vive en OneDrive (sincroniza miles de objetos chicos a la vez durante index-pack). `git -c core.fsync=none` ayuda algo. `git ls-remote` rápido + fetch lento = problema de tamaño/disco, no de auth.
- **`git push ... | tail -3` ENMASCARA el fallo (2026-08-14)**: en un pipe, `$?` y el `||` ven el exit code del ÚLTIMO comando (`tail`, siempre 0), no el de `git push`. Un push rechazado reportaba `EXIT=0` y el bloque `|| { rebase; push }` nunca se disparaba → parecía pusheado y no lo estaba. **Nunca poner un pipe entre `git push` y el `||`/`$?`**; capturar la salida a archivo o chequear `${PIPESTATUS[0]}`.
- **`git rebase --onto X BASE HEAD` deja DETACHED HEAD (2026-07-26)**: al pasar `HEAD` como argumento explícito, git rebasea pero **no mueve la rama** — queda `main` en el commit viejo y el push falla con "behind". Estando EN la rama, usar `git rebase --onto origin/main <base>` **sin el tercer argumento**: ahí sí actualiza `refs/heads/<rama>` ("Successfully rebased and updated refs/heads/main"). Si ya quedó detached: verificar los archivos del commit rebasado y recién ahí `git checkout -B main <sha>`.
- **Push de commits de código durante ventana de cron (2026-07-14)**: el cron pushea PNGs cada ~15 min → tu push rebota non-fast-forward casi seguro. Flujo que funcionó: `fetch --depth=1` (background, foreground timeoutea) → `rebase --onto origin/main <base>` (limpio porque los commits de código no tocan `docs/sentinel2/`) → `push`. Si el fetch da `early EOF`/`curl 56 connection reset` (pack pesado + red), **reintentar con `-c http.postBuffer=524288000`** (funcionó al 2º intento). Un fetch background colgado deja `git`/`git-remote-https` vivos + `.git/shallow.lock`: matar los procesos y `rm .git/shallow.lock` antes de reintentar (si no, `fatal: Unable to create shallow.lock: File exists`). El push deja el repo SHALLOW → `git fetch --unshallow` después con buena conexión.

## Landsat: imagenes 100% negras (nodata) y huecos de actualizacion (2026-06-12)

- **Sintoma**: algunos volcanes (Parinacota, San Pedro, Nevado de Longavi...) mostraban su "ultima imagen" en negro total. Eran PNGs de ~1940 bytes, mean=0.0, 100% pixeles <8.
- **Causa raiz**: el M2M scene-search filtra por **MBR** (rectangulo envolvente), pero el footprint WRS-2 real es un **paralelogramo rotado**. Una escena de un path adyacente (sidelap) intersecta el MBR del volcan sin cubrirlo realmente -> el `rasterio` window-read sobre el bbox da todo nodata (ceros) -> composite negro. El downloader lo guardaba igual y, por ser la fecha mas nueva, pasaba a ser la imagen mostrada. Distinguir por scene_id: la buena y la negra son de path/row distinto (ej. San Pedro bueno `233075`, negro `001075`).
- **Fix**: `_sin_cobertura(arr_rgb)` rechaza la escena si >90% es nodata. RGB se genera PRIMERO como prueba de cobertura; si es negra se descarta la escena entera (sin guardar ni registrar metadata). Umbral 0.9 conserva cobertura parcial real. Limpieza one-off borro 17 PNGs negros en 8 volcanes + regenero el JSON de fechas.
- **Hueco de actualizacion (Lascar)**: distinto problema. Lascar solo recibe path 233 (no tiene sidelap util). Ultima real 05-26; las proximas (06-03 L8, 06-11 L9) no llegaron: 06-11 es muy reciente (Landsat publica T+1-2d), 06-03 requiere ver logs M2M del cron (con creds). `MAX_CLOUD_COVER=100` => NO es filtro de nubes. No es bug de cache del dashboard: el JSON refleja los PNG reales en disco. Verificar contra metadata.csv + tamano de PNG, no asumir.
- **Verificacion de imagen "rara"**: cargar el PNG con PIL y mirar `mean()` y `frac(<8 en los 3 canales)`. mean~0 => nodata; mean alto + poco negro => imagen real.

## Lascar "hueco" = latencia de procesamiento USGS, NO bug nuestro (2026-06-12, verificado con creds)

- Con credenciales M2M, `scene_search` de Lascar (60d) devuelve 6 escenas, todas path 233/076, cadencia EXACTA de 8 días, la más nueva 05-26. Las posteriores (06-03 L8, 06-11 L9) **USGS todavía no las publicó a Level-2**. El dashboard estaba bien; el pipeline estaba bien.
- **Clave: la latencia de procesamiento L2 de USGS es muy variable**. Leerla del `displayId` `LC0X_L2SP_PPPRRR_<adquisicion>_<procesamiento>_...`: la escena 05-18 se procesó 05-28 (**T+10 días**), la 05-02 el 05-14 (**T+12**), pero la 05-26 el 05-27 (T+1). El dataset `landsat_ot_c2_l2` solo tiene L2 ya procesado (no RT/T2), así que una escena reciente puede tardar hasta ~2 semanas en aparecer. El cron la toma ~1h después de publicada.
- **Implicancia para el contador**: la ventana "~1-2 días" de Landsat es el caso TÍPICO (mediana ~44h), pero la cola es larga por USGS. La auditoría git previa (95% <48h) tiene survivorship bias: solo cuenta escenas que SÍ llegaron, no las que siguen pendientes en USGS.
- **Cómo diagnosticar un "hueco" de un volcán**: correr `set -a; . ./.env; set +a; python landsat_downloader.py --volcan X --dias 15`, o `M2MClient().scene_search(...)` directo para listar fecha+cloud+displayId. Distingue al instante "USGS no lo tiene" de "lo descartamos por nodata/nubes". Token M2M local en `.env` (gitignored), generado en ERS → Profile Home → Application Tokens → scope solo "M2M API".

## Híbrido Landsat L2 + relleno L1-RT (2026-06-12)

- **Problema**: L2 (reflectancia de superficie) tiene cola de procesamiento USGS de hasta ~12d. L1 (TOA) sale ~T+1 como Real-Time. Solución: L2 primario; si falta, bajar L1 para no tener hueco; upgradear a L2 cuando USGS lo publica.
- **Datasets M2M**: `landsat_ot_c2_l2` y `landsat_ot_c2_l1`. Bandas L1 = `_B2/_B3/_B4/_B6/_B7/_B10.TIF` (sin prefijo SR_/ST_).
- **Conversión L1 (constantes Collection-2, sin MTL)**: reflectancia TOA ρ=(2e-5·DN−0.1)/sin(sun_elev); la **elevación solar viene en scene-search con metadataType="full"** (`Sun Elevation L0RA`). Térmico B10: L=3.342e-4·DN+0.1 ; BT=K2/ln(K1/L+1)−273.15 ; K1/K2 por satélite (L8 774.8853/1321.0789, L9 799.0284/1329.2405).
- **El watcher DEBE mirar ambos datasets**. Si solo mira L2, el cron no se dispara con la L1 fresca y el híbrido no da frescura. La L1 Chile-wide tiene >100 escenas en 5d -> subir maxResults. El repo es público (Pages) -> minutos de Actions ilimitados, disparar seguido está OK.
- **Nivel por fecha**: columna `nivel` en metadata.csv; en filas viejas se infiere del scene_id (`_L1`->L1, si no L2). Algunas imágenes viejas (04-25) YA eran L1 (scene_id `LC08_L1TP_...`) -> la detección las marca bien. `niveles_actuales()` solo cuenta si el PNG RGB existe (la retención borra PNGs).
- **Idempotencia**: best-por-fecha (L2>L1) + comparar con nivel en disco. Re-run = 0 descargas; upgrade L1->L2 sobreescribe. El filtro `_sin_cobertura` (nodata) sigue aplicando a ambos niveles.
- **Integridad de datos**: `niveles_landsat.json` ({volcan:{fecha:'L1'}}) marca las provisionales; badge ámbar 'L1' en Sala e index Landsat (el geólogo debe saber TOA-provisional vs L2-final).
- **Token M2M local**: `.env` gitignored. Generar en ERS -> Profile Home -> Application Tokens -> "Create Application Token", scope solo "M2M API" (se muestra 60s, no se recupera).

## DOS (dark-object subtraction) para RGB L1 (2026-06-12)

- El RGB L1 (TOA) se ve lavado/azulado porque arrastra la radiancia de camino atmosferica (bruma), dependiente de longitud de onda: en Lascar 06-03 el haze por banda fue R=0.021, G=0.031, **B=0.052** (Rayleigh dispersa mas el azul). Eso es el "velo" del TOA.
- **Fix**: restar por banda el objeto oscuro (percentil 1 de pixeles validos, `refl[refl>0.01]`). Aproxima la correccion atmosferica del L2. Resultado: sombras vuelven a negro (p1->0), se va el tinte azul, RGB con tonos tierra naturales (R>G>B). Solo L1; el L2 ya viene corregido. Aplicado en `_reflectancia()` para RGB y SWIR.
- Verificar de-hazing: comparar means por canal (deben separarse R>G>B) y p1 (debe caer a ~0). Guardar 2 PNGs y mirarlos con Read (vision) es la prueba de oro.

## Sala Landsat: mostrar siempre la última L1 (no esperar L2) (2026-06-12)

- **Decisión de monitoreo**: la Sala (kiosko) prioriza FRESCURA. Con revisita combinada ~8d y L2 que tarda hasta ~12d, cuando sale la L2 de una fecha ya suele haber una L1 más reciente de la pasada siguiente -> mostrar L1 da la imagen más nueva. La Sala elige `max(fechas L1 de niveles_landsat.json)`; si el volcán no tiene ninguna L1, cae a la última disponible (L2). El downloader sigue híbrido (la L2 mejora el dashboard detallado e historial).
- **Ventana del contador**: pasó a "~1 día" (L1-RT ~T+0/T+1 + cron horario). Antes (solo L2) era "~1-2 días o más". El badge L1 dejó de decir "provisional/se reemplaza por L2" -> ahora "la más reciente disponible".
- **El cron ya hace el backfill solo**: tras pushear el código híbrido, el watcher (que ahora mira L1+L2) disparó el cron y bajó 77 imágenes (más que mi corrida local). Lección: después de cambiar el downloader, **dejar que el cron haga el backfill** en vez de correrlo local y pelear con el push divergente.
- **Gotcha CDN**: `raw.githubusercontent.com` cachea por archivo ~5min y el `?t=` no siempre lo evita; dos JSON del mismo commit pueden servirse con distinta frescura (vi niveles con 06-11 y fechas sin él). No es bug de datos. La carga de imagen por fecha es robusta igual (el PNG existe si niveles lo lista).

## El re-render de RGB SÍ gasta PU (re-descarga server-side) (2026-06-16)

- **Corrección a una suposición errónea**: re-renderizar el histórico tras un cambio de evalscript (ej. el fix True Color con `HighlightCompressVisualizer`) NO es gratis. El RGB se renderiza *server-side* en Sentinel Hub (el evalscript se ejecuta en sus servidores), así que `--sobrescribir` **re-descarga** cada escena = 1 POST = gasta PU. Ver `sentinel2_downloader.py:634` ("re-descarga aunque el archivo ya exista") y `:701-703`. Solo `SWIR_raw` tenía `.npz` local; el RGB nunca se guarda crudo, por eso no hay re-render local.
- **Magnitud**: 10 volcanes nevados × ventana → 134 escenas (30d) / 258 (60d) / 541 (historia completa). Con cuentas de PU justas, esto importa.
- **Decisión tomada**: NO re-renderizar histórico viejo. Las descargas nuevas ya salen con el evalscript corregido; re-render puntual de un mes solo si hace falta y hay PU.
- **Meta-lección**: un subagente afirmó "cero PU, re-procesa desde .npz local" — era falso. Verificar siempre las afirmaciones de costo/PU de subagentes contra el código antes de actuar (regla "no adivinar valores instrumentales").

## El repo LOCAL desactualizado se disfrazó de "cron caído" (2026-07-26)

- **Síntoma**: al portar el temporizador al dashboard de Landsat-v1, el badge no aparecía en 38 de 43 volcanes. `docs/proximas_pasadas_landsat.json` tenía `generado_utc: 2026-06-16` (40 días) y solo 5 volcanes conservaban un paso futuro → `info()` devolvía `null` correctamente.
- **Diagnóstico equivocado y su corrección**: concluí "el cron de Landsat no publica" mirando **solo el archivo local**. Falso. `gh run list` mostró el cron corriendo **cada hora, todos en success**, y el JSON **remoto** (raw) estaba al día (`generado_utc` de minutos antes, 43/43 volcanes con paso futuro). Lo viejo era **mi clon local**, parado en `6d01217` del 2026-06-16 — 40 días de commits del bot sin traer.
- **Por poco escribo un dato peor que el que había**: alcancé a regenerar el JSON local (el script corre sin red, solo pandas + metadata en disco) y estuve a punto de commitearlo. Como la **metadata local también estaba 40 días vieja**, ese JSON habría pisado el del cron con una predicción calculada sobre datos peores. Descartado con `git checkout --`.
- **Reglas que salen de esto**:
  1. Antes de declarar "el pipeline está roto", **comparar contra el REMOTO** (`curl` a raw / `gh run list`), no contra el working tree. Un clon viejo produce exactamente los mismos síntomas que un cron muerto.
  2. En repos donde **el bot commitea seguido**, el clon local envejece rápido y en silencio: `git log -1 --date=short` del archivo sospechoso es el primer chequeo.
  3. Verificar si el HTML/código remoto divergió antes de commitear ediciones hechas sobre base vieja (acá `index.html` remoto era **idéntico**: los 40 días eran solo datos, así que las ediciones aplicaban limpio; si hubiera divergido, commitear habría borrado 40 días de cambios).
- **Estructura real del cron de Landsat** (sana, para no volver a sospechar): `landsat.yml` corre cada hora, pero el job de descarga —y con él el paso "Regenerar prediccion"— está tras el gate `if: needs.detectar.outputs.has_new == 'true'`. Los runs de ~35-42 s son solo el watcher (sin novedad); los de 8-17 min son los que descargaron. **La predicción se regenera solo cuando llega imagen nueva**, lo cual es correcto pero significa que su frescura depende de la revisita (~8 d combinada) y de la cola L2 de USGS.

## countdown.js: componente compartido Sala ↔ dashboard (2026-07-26)

- **El temporizador de pasadas vivía solo en `sala_monitoreo.html`**. Al pedirlo también en el dashboard se extrajo a **`docs/countdown.js`** (fuente única) en vez de duplicar ~160 líneas + CSS que iban a divergir. API: `configurar()` / `cargarFuentes()` / `info()` / `crearBadge(volcan, sensor, 'overlay'|'inline')` / `actualizarTodos()` / `iniciarTick()`. El CSS viaja dentro del JS (se inyecta una vez, id `countdown-css`), con el **posicionamiento en modificadores** (`cd-overlay` absoluto sobre la imagen para la Sala, `cd-inline` en el flujo para el dashboard) — sin eso el mismo badge no sirve en dos layouts distintos.
- **Trampa de las referencias reasignadas**: el host hace `predS2 = j` en cada fetch, así que si el módulo se configura una sola vez queda apuntando al **objeto viejo** y el badge se congela. Hay que re-llamar `configurar()` **después de cada carga** (en la Sala se hizo con `sincronizarCountdown()`, llamada en `init` y en `refrescarDatos`).
- **Orden de inicialización en el dashboard**: `window.onload` llamaba `cambiarZona()` (render) y las predicciones se cargaban después → los paneles se pintaban sin badge y solo aparecía al cambiar de zona. Fix: `inicializarCountdown().finally(() => cambiarZona())`. `cargarFuentes()` nunca lanza, así que si el JSON falla el dashboard renderiza igual (sin badge).
- **`index.html` NO tiene modo Landsat** (verificado: `landsat` aparece 2 veces, ambas enlaces salientes al repo `Landsat-v1` y a la página standalone). El `CLAUDE.md` del proyecto afirma que el dashboard tiene "modos Individual/Multi/Personal/Riesgosos de Landsat" — **está desactualizado**. Los 4 modos de index.html son todos S2; `proximas_pasadas_landsat.json` tampoco existe en este repo (vive en Landsat-v1).
- **`cargarPanelesList` (Personal+Riesgosos) y `loadMultiVolcanoViewZona` ya usan `innerHTML` con `${volcan}` interpolado** (deuda preexistente que viola la regla del proyecto). Para no empeorarlo, el badge se inserta **después** del `appendChild` del panel con `createElement` (`agregarCountdownAPanel`), no dentro del template string.

## Las imágenes llegan en PAQUETE, no de a una: la alerta es por evento (2026-07-26)

- **Dato medido sobre el índice de fechas** (no estimación): los volcanes que comparten una misma fecha de imagen son **mediana 38 en S2** (p90=45, máx=48, de 51 entidades) y **36 en Landsat** (p50=4 por las pasadas parciales, p90=36). Fechas S2 recientes: 45, 41, 48 volcanes. Causa: el cron descarga por zonas en paralelo y **consolida en un único commit**, así que el JSON de fechas salta de golpe.
- **Implicancia de diseño**: cualquier notificación "por volcán" es inviable — un paquete normal daría ~40 alertas simultáneas (con locución de 11 s = más de 7 min de voces encimadas). La alerta debe ser **por EVENTO** ("llegó un paquete"), con la lista de volcanes como detalle.
- **Coalescencia implementada** (`SecuenciaAlerta` en `sala_monitoreo.html`): 1ª emisión inmediata; mientras la secuencia está activa las novedades siguientes solo **engordan el aviso visual**, sin sonido extra ni reinicio del contador. Esto cubre el caso real de paquete partido: **S2 y Landsat son JSON de repos distintos** y `raw` cachea ~5 min, así que llegan en ciclos separados. Verificado: 45 imágenes de golpe → 1 reproducción; +36 Landsat después → sigue en 1; aviso pasa a 81.
- **Repetición con acuse de recibo**: 3 emisiones cada 10 min; click en el aviso corta las pendientes. Verificado acelerando los timers (patch de `setTimeout`): exactamente 3 emisiones y se detiene (no queda un timer colgado).

## Procesar una locución de voz para alerta con ffmpeg (2026-07-26)

- **Diagnóstico primero, con espectrograma leído como imagen** (`showspectrumpic` + `showwavespic` → `Read`): reveló armónicos de voz limpios en DC–4,5 kHz pero **hiss de banda ancha en 4,5–20 kHz** (micrófono de celular), rumble en DC y sibilancia puntual. Sin eso se procesa a ciegas.
- **Cadena que funcionó** (`highpass=90` → `afftdn=nr=14:tn=1` → `agate` suave (release 320 ms para no cortar colas de palabras) → `deesser` → EQ (−2 dB @300 Hz, +3 dB @2,8 kHz presencia) → `lowpass=11000` → `loudnorm=I=-16:TP=-1.5`). **SNR 33,7 → 40,7 dB** con la voz intacta.
- **Trampas medidas**: (a) `acompressor` con `makeup` **empeoró** el SNR (levanta el piso de ruido junto con la voz) — quitarlo, `loudnorm` ya nivela; (b) comparar "nivel de ruido absoluto" entre variantes **engaña** porque cada una normaliza a distinto nivel → comparar **SNR (voz − ruido)**; (c) `loudnorm` **resamplea la salida a 192 kHz** si no se fuerza `-ar 48000` (dejaba un WAV de 4,2 MB para 11 s).
- **Audio en el repo**: `docs/audio/` (NO `docs/lib/`, que está gitignored por la regla `lib/` de Python y necesita `git add -f`). mp3 mono 96 kbps ≈ 12 KB/s.
- **Verificar reproducción sin oír**: monkey-patch de `AudioContext.prototype.createBufferSource` para contar `start()` reales. Distingue "sonó" de "creí que sonó".

## Sonido de alerta en la Sala (kiosko): autoplay y la carrera pointerdown/click (2026-07-17)

- **El navegador BLOQUEA el audio hasta que hay un gesto del usuario.** En un kiosko desatendido eso significa que `AudioContext` nace `suspended` y la alerta **no suena nunca, sin avisar** — falla silenciosa, justo lo que la lección #4 prohíbe. Fix: el estado del audio se muestra en el footer con 3 estados (`activo` / `silenciado` / `bloqueado` ámbar parpadeando), el botón hace de gesto de desbloqueo, y `sonar()` devuelve `false` + loguea cuando no pudo emitir. **Nunca asumir que `play()`/`resume()` funcionó.**
- **Carrera `pointerdown` → `click` (bug real, 2 iteraciones para encontrarlo)**: se enganchó un desbloqueo oportunista en `pointerdown` de todo el documento para aprovechar cualquier gesto. Pero al apretar el propio botón de sonido, el `pointerdown` ponía el ctx en `running` ANTES de que corriera el `click` → `alternar()` leía estado `activo` y **silenciaba justo cuando el operador quiso activar** (el botón decía "Activar sonido" y silenciaba). Fix: el handler oportunista ignora eventos que vienen de `#btn-sonido` (`ev.target.closest('#btn-sonido')`), que ya tiene su propio handler. **Lección general: un desbloqueo global de audio no debe pisar al control que lo administra.**
- **Sonido SINTETIZADO con Web Audio (oscilador), no un .mp3**: cero bytes al repo (que venía de purgar `.git` 26 GB → 2.6 GB), sin CORS ni caché ~5min de raw, y afinable. Arpegio A5-C#6-E6 + repique con envelope exponencial (campanilla, no beep). Verificación: monkey-patch de `AudioContext.prototype.createOscillator` para **contar las notas realmente programadas** (4, con sus frecuencias) — probar audio por "se oye" no es posible headless, contar osciladores sí.
- **La firma de detección solo miraba S2**: `firmaUltimasFechas()` ignoraba Landsat, así que una Landsat nueva no disparaba re-render (ni sonido). Extendida a ambos sensores vía `mapaUltimasFechas()` (`"<sensor> <volcan>" -> última fecha`). El diff `detectarNuevas()` **solo cuenta fechas que AVANZARON**: si la retención borra una fecha, la firma cambia pero no se anuncia como novedad (verificado: 0 notas en retroceso).

## gif_builder.html portado a gifenc (2026-07-14)

- **`gif_builder.html` (Constructor GIF interactivo) usaba gif.js** → NeuQuant aplasta los rojos de anomalía térmica chica (mismo bug que ppt_builder tenía). Portado al mismo `gifenc`/`rgb444` ya probado: `import('./lib/gifenc.esm.js')` → por frame `quantize(data,256,{format:'rgb444'})` + `applyPalette` + `enc.writeFrame(index,W,H,{palette,delay:ms,repeat:idx===0?0:undefined})`. Se quitó `<script src="lib/gif.js">` (ya no se usa; RGB y thermal ambos por gifenc).
- **Encode gifenc es SÍNCRONO** (no usa workers como gif.js). En el loop de frames hay que `await new Promise(r=>setTimeout(r,0))` tras cada `writeFrame` para refrescar la barra de progreso y no congelar la UI. Canvas con `getContext('2d',{willReadFrequently:true})` porque hay un `getImageData` por frame.
- **Verificación (navegador real, code-path de la página)**: frames de anomalía de Lascar dieron retención de rojos 90-121% con gifenc, vs 0/45 documentado con gif.js. Detector de anomalía en falso color térmico = **rojo dominante por margen** (`r>120 && r-g>40 && r-b>40`), NO rojo puro con G/B bajos (R≈G≈B en frames grises sin anomalía da 0, no es bug). El `screenshot` del preview timeoutea con el GIF animando → verificar por JS contando píxeles, no por captura.

## Purga del .git en disco lleno: NO usar git gc, borrar .git y re-clonar (2026-07-03)

- **Contexto**: repo `.git` de 26 GB con el disco del sistema al 99%. La purga nuclear (`purgar_historico_completo.yml`, orphan-reset) reduce el REMOTO a ~3 GB corriendo en el runner (disco fresco), pero el clon LOCAL sigue en 26 GB.
- **Trampa del gc**: `git gc --prune=now` para reclamar el espacio local **desempaqueta los objetos inalcanzables a loose antes de podarlos** (`repack -A`) → necesita ~tamaño-del-repo de scratch → en disco lleno explota a 0 bytes y falla dejando un `tmp_pack` parcial. **No correr gc para adelgazar en disco lleno.**
- **Salida correcta**: como el remoto ya es chico y el working tree está intacto, `rm -rf .git` (libera los 26 GB al instante) + `git init` + `remote add` + `git fetch origin main` + `git checkout -f -B main origin/main`. Reconstruye un `.git` de ~2.6 GB. Cero pérdida (todo está en el orphan remoto + working tree). **Verificar el working tree ANTES de borrar `.git`.**
- **Bug del script de purga**: `limpiar_imagenes_antiguas.py` borra TODOS los `.pptx`, incluida `docs/plantillas/Cambios_morfologicos.pptx` (que el ppt_builder NECESITA). Recuperada vía `raw.githubusercontent.com/<repo>/<sha-viejo>/...` (GitHub retiene objetos inalcanzables ~90d). Guard agregado al script.
- **Coordinación**: pausar crons (`gh workflow disable`) antes del force-push, re-activarlos (`gh workflow enable`) después. NO olvidar el re-enable.
- **`git add -A` del orphan respeta `.gitignore`**: los libs de `docs/lib/` (gif.js, gifenc) sobrevivieron SOLO porque estaban trackeados antes (el `--orphan` hereda el índice). Archivos force-added siguen tracked; untracked-gitignored se caen.
- **Fetch lento**: sobre repo grande / red lenta, fetch/push timeoutean en foreground → usar `run_in_background`. NO mezclar `nohup` con el background del tool (queda sin trackear).

## Retención, validación de tonalidad y falsos diagnósticos (2026-08-17)

**El patrón que apareció 3 veces el mismo día: una política de TIEMPO colgada de un evento de datos.**
- `limpiar_imagenes_antiguas()` vivía dentro de `if resultados:` → solo limpiaba volcanes que bajaron algo ese día. En invierno casi ninguna corrida trae nada → retención apagada justo cuando más crece el archivo.
- Los jobs de zona borran en su workspace efímero y suben artifact, pero **`download-artifact` SUPERPONE: agrega y sobrescribe, nunca borra**. Sobre el checkout completo del consolidador lo viejo sigue presente → los borrados jamás llegaban al `git add -A`. **3.01 GB acumulados desde marzo con la política diciendo 60 días.**
- Al mover la purga al job `consolidar` **se reintrodujo el bug**: ese job declara `needs:[descarga]` y `descarga` corre con `if: has_new=='true'`. Sin productos nuevos ambos se saltan. Verificado: run con `detectar=success, descarga=skipped, consolidar=skipped`.
- **Regla:** para cualquier limpieza/expiración preguntar *«si hoy no llega ni un dato, ¿corre igual?»*. Si no, está mal cableada. Se resolvió con `retencion_diaria.yml`, cron propio, grupo `push-main`.
- **Orden que importa:** purgar ANTES de regenerar `fechas_disponibles_*.json`; al revés el índice lista fechas borradas → 404.
- `DIAS_RETENCION` y `DIAS_BUSQUEDA_DEFAULT` se mueven JUNTAS. Búsqueda 60 con retención 45 = bajar imágenes para borrarlas en la misma corrida, gastando PU.

**Validación de tonalidad: la escena de prueba es parte del test.**
- El fix RGB de junio (`HighlightCompressVisualizer(0,0.4)`) se validó contra Chillán 2026-06-11 y 06-13, con **81.8% y 88.2% de nube**: escenas donde la nieve no está en cuadro y el defecto no puede manifestarse. Ese mismo día Lonquimay 06-13 (25% nube) ya estaba al 82.5% de blanco. **Nunca estuvo arreglado.**
- **Ningún punto de quiebre fijo cubre los dos regímenes.** Sonda de reflectancia cruda (Lonquimay 2026-08-12): mediana 0.937, p90=1.000, 96.4% de píxeles >0.4. Con `maxVal=0.8` el invierno queda impecable y **el verano se destruye (79.4% negro)**. Solución: gamma sRGB sobre reflectancia cruda, sin ganancia — no tiene punto de quiebre.
- **Probar SIEMPRE los dos extremos**: día despejado de invierno con nieve Y escena de verano con terreno oscuro. Filtrar por nubosidad `<20%`, no aceptar la primera fecha disponible.
- Métricas que sirven para RGB: **% de blanco puro** y **entropía de la banda roja** (antes 1.52 bits, después 5.15). `auditoria_imagenes.py` solo mide SWIR — por eso la auditoría de esa misma mañana no vio nada.
- **Arnés barato**: monkeypatch `sd.EVALSCRIPTS['RGB']` antes de `dl.download_image(...)`. Probar una variante = 2 renders; el backfill completo = ~950. Verificar antes de gastar.
- Distinguir "archivo guardado corrupto" de "el pipeline lo produce así": re-renderizar con el MISMO evalscript. Si la saturación se reproduce al dígito (82.3% → 82.3%), es el pipeline.

**Falsos diagnósticos, dos formas.**
- **El verde no prueba el efecto.** La retención estuvo rota 5 meses con todos los runs en `success`, porque descargar y commitear sí funcionaba. Tras disparar la purga salió verde en 2m7s; la prueba real fue ir a `main` y confirmar el commit de 6591 archivos y el rango de fechas. **Nunca reportar "funciona" con el ✅ como evidencia.**
- **Coincidencia temporal ≠ causa.** El dashboard quedó en blanco el día que tocamos varias cosas; se culpó al cache-buster `?t=${Date.now()}` y quedó escrito en un commit. Era falso: GitHub tenía incidente `critical` y `raw` devolvía 429 **hasta para `volcanes.js`, 13 KB**. Prueba discriminante barata: si un archivo chico también falla, no es saturación por volumen. Revisar `https://www.githubstatus.com/api/v2/status.json` antes de culpar al código propio.

**Trampa del historial: el orphan reset rompe la arqueología.**
- `5c6fd333` es commit raíz, así que ahí TODO aparece como `A` (agregado) y `git log -S` / `git log -- <archivo>` no pueden datar nada anterior. Llevó a concluir falsamente cuándo cambió el evalscript. Profundidad total: 28 commits.

**Coordinación entre sesiones concurrentes.**
- Con dos sesiones en el mismo repo el working tree cambia bajo los pies entre comandos. Usar `git commit -o <path>` (ruta explícita) para no barrer trabajo ajeno; `git add -A` es peligroso.
- El `concurrency: push-main` serializa **workflows**, no sesiones humanas. 15 escritores a `main`, los 15 en el grupo.
