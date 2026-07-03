# Plan de Migración — Reducción de tamaño del repo Copernicus-v1

**Fecha**: 2026-05-17
**Autor**: Auditoría infra (Claude)
**Estado**: Propuesta operativa — ningún paso destructivo ejecutado todavía
**Audiencia**: Nicolás Mendoza (SERNAGEOMIN)

---

## TL;DR

El repo pasó de ~0 a **21 GB en 4 meses** (de los cuales **19 GB son `.git`**). A este ritmo cruza el soft warning de GitHub (5 GB) ya hoy, y llega al hard cap (100 GB) en ~18 meses. El problema NO son los PNGs (120 MB) sino los **PPTX regenerados por el cron** (99 archivos × ~10 MB c/u, cada regeneración deja un blob completo nuevo en el historial → top 13 blobs más pesados son todos PPTX).

**Recomendación: Plan combinado A+B**
1. **Hoy mismo (Paso 0)**: dejar de versionar PPTX y GIFs grandes → corta el crecimiento sin tocar historia
2. **Semana 1 (Paso 1, Opción A)**: Git LFS para los pocos binarios que sí necesitan versionado
3. **Semana 2-3 (Paso 2, Opción B)**: Migrar PNGs/GIFs/PPTX a Cloudflare R2 (mismo precedente que `Landsat-v1`)
4. **Mes 2+ (Paso 3, Opción C, opcional)**: `filter-repo` solo si superamos 40 GB con la historia vieja

---

## 1. Diagnóstico (datos reales 2026-05-17)

### Tamaño actual del repo

| Métrica | Valor |
|---|---|
| **Carpeta total en disco** | **21 GB** |
| **`.git`** | **19 GB** |
| **Working tree (HEAD)** | **2.0 GB** |
| **Objetos en pack** | 27.747 |
| **Tamaño en pack** | 16.62 GiB |
| **Objetos loose** | 2.522 (1.63 GiB) |
| **Packs** | 18 |
| **Commits totales** | 861 |
| **Commits últimos 30 días** | 132 (~4.4/día) |
| **Edad del repo** | 2026-01-18 (4 meses) |

> Comando: `git count-objects -vH` y `du -sh .git docs .`

### Top blobs en historia (el problema real)

| Rank | Tamaño | Archivo | Tipo |
|---|---|---|---|
| 1 | 14.0 MB | `data/sentinel2/Llaima/reportes/Llaima_Evaluacion_Mensual_2026-01.pptx` (×4 versiones) | PPTX |
| 2 | 13.1 MB | `docs/sentinel2/Planchon-Peteroa/.../*_2026-02.pptx` | PPTX |
| 3 | 11.5 MB | `docs/sentinel2/Villarrica/reportes/*_2026-02.pptx` (×4 versiones) | PPTX |
| 4 | 11.0 MB | `data/sentinel2/Villarrica/reportes/*_2026-01.pptx` (×4 versiones) | PPTX |
| 5 | 10.4 MB | `bibliografia/pdfs/Coppola2019_MIROVA.pdf` | PDF |
| 6 | 9.3 MB | `data/sentinel2/Llaima/timelapses/Llaima_RGB_*.gif` | GIF |
| 7 | 8.7 MB | `data/sentinel2/Villarrica/timelapses/*_RGB_2026-01.gif` | GIF |

**Patrón crítico**: el mismo PPTX (`Llaima_Evaluacion_Mensual_2026-01.pptx`) aparece **4 veces** con tamaños idénticos. Cada regeneración del cron crea un nuevo blob de 14 MB. Git no puede deduplicar PPTX (son ZIPs comprimidos internamente). Si el cron regenera 99 PPTX 2×/día = ~2 GB/día de blobs nuevos en historia.

### Distribución por tipo (en HEAD, sin historia)

| Tipo | Cantidad | Tamaño HEAD | Crecimiento mensual estimado |
|---|---|---|---|
| **PPTX** | 99 | **859 MB** | **~4 GB/mes** (peor ofensor) |
| **GIF** | 184 | 328 MB | ~1.5 GB/mes |
| **PNG** | 2.152 | 120 MB | ~0.5 GB/mes |
| **PDF** | 15 | 49 MB | ~50 MB/mes (bibliografía estable) |
| Código + HTML + JSON | — | ~10 MB | despreciable |

### Top directorios en `docs/`

```
1.6G   docs/sentinel2/      ← imágenes + reportes (el grueso)
218M   docs/timelapses/
217M   docs/reportes/
9.2M   docs/alertas/
5.5M   docs/plantillas/
```

### Proyección de crecimiento

- **Tasa observada**: 19 GB de `.git` en 4 meses = **4.75 GB/mes en historia**
- A este ritmo:
  - **50 GB**: ~7 meses (≈ diciembre 2026)
  - **100 GB hard cap**: ~17 meses (≈ octubre 2027)
  - GitHub Pages empieza a degradar respuesta y clones tardan minutos ya desde **30 GB**

> Comando de auditoría usado:
> ```bash
> git rev-list --objects --all \
>   | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
>   | grep '^blob' | sort -k3 -n -r | head -20
> ```

---

## 2. Tres opciones evaluadas

### OPCIÓN A — Git LFS para PPTX/GIFs/PNGs (no destructivo, incremental)

**Cómo funciona**: LFS reemplaza el archivo en git por un puntero de 130 B; el binario real vive en un store separado de GitHub. La historia anterior no se toca, pero **archivos nuevos** dejan de pesar en `.git`.

**Pros**:
- Cero riesgo de pérdida (no reescribe historia)
- Reversible
- Compatible con cron de GitHub Actions sin cambios al frontend (URLs siguen siendo paths relativos)
- `git clone` ya no baja los binarios completos; solo los que el checkout necesita

**Contras**:
- **No reduce el tamaño actual** (19 GB siguen ahí), solo frena el crecimiento
- **Cuotas GitHub LFS**:
  - Free: 1 GB storage + 1 GB/mes de bandwidth → **se agota en horas** con nuestro volumen
  - Data Pack: $5/mes por 50 GB storage + 50 GB bandwidth
  - Con 4-5 GB/mes de PPTX generamos ~60 GB/año → **$60/año** (1 data pack alcanza)
- LFS objects también cuentan para el límite de 100 GB del repo si crecen mucho
- Operacionalmente: cualquier collaborator debe `git lfs install` o ve punteros vacíos
- Si pasamos el cap de bandwidth, GitHub bloquea descargas hasta el mes siguiente (puede romper GitHub Pages)

**Setup mínimo**:
```bash
git lfs install
git lfs track "*.pptx" "*.gif" "docs/sentinel2/**/*.png"
git add .gitattributes
git commit -m "chore: track binarios pesados con Git LFS"
git push
```

**Verificación**: `git lfs ls-files` debe listar archivos trackeados; `git lfs status` muestra qué subirá.

---

### OPCIÓN B — Cloudflare R2 (externalizar completamente, precedente Landsat-v1)

**Cómo funciona**: los PNGs/GIFs/PPTX dejan de vivir en git. El cron sube cada archivo a un bucket R2 después de generarlo. El frontend hace fetch a `https://copernicus-v1.<accountid>.r2.dev/<volcan>/<fecha>.png` en vez de path relativo.

**Pros**:
- **Costo real**: $0.015/GB/mes storage + **$0 egress** (R2 no cobra salida, ventaja decisiva vs S3)
- 100 GB de PNGs = **$1.50/mes** = ~$18/año (pagable de bolsillo)
- No hay cap de bandwidth como LFS → no se rompe Pages
- Repo `.git` se mantiene pequeño para siempre (~100 MB de código + bibliografía)
- CDN global gratis incluido en R2
- Precedente: `Landsat-v1` ya lo usa con éxito → know-how + credenciales reutilizables

**Contras**:
- Requiere modificar **frontend** (URLs relativas → URLs absolutas a R2). Variable de entorno tipo `IMG_BASE_URL` para poder switchear fácilmente
- Cron workflow `copernicus.yml` necesita paso extra de upload (`boto3` o `rclone` o `aws s3` con endpoint R2)
- Si R2 se cae, el dashboard pierde imágenes (mitigable con fallback a path relativo durante 1 mes de transición)
- Credenciales R2 en GitHub Secrets (`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`)
- Histórico (1.6 GB en HEAD) requiere subida inicial one-shot

**Costo total estimado** (incluyendo crecimiento futuro):
- Año 1 (0 → 60 GB acumulados): promedio 30 GB × $0.015 × 12 = **$5.40**
- Año 2-3 (60 → 180 GB): **$15–25/año**
- Operacionalmente despreciable

---

### OPCIÓN C — `git filter-repo` agresivo (destructivo)

**Cómo funciona**: reescribe toda la historia de git para borrar blobs viejos de directorios específicos. Repo pasa de 19 GB a probablemente **2-3 GB**.

**Pros**:
- Resuelve el problema de raíz (la historia vieja también se reduce)
- Después de ejecutarlo, clones son rápidos otra vez

**Contras**:
- **Reescribe TODOS los SHAs** → cualquier clone existente queda inválido (incluyendo el local de Nicolás, GitHub Pages cache, forks)
- Requiere `git push --force` (destructivo)
- Si alguien tiene cambios locales sin pushear, **se pierden** silenciosamente
- Tags, releases, PRs cerrados quedan con SHAs muertos
- GitHub Actions cache se invalida

**Cuándo usarlo**: solo si el repo supera 40 GB y los Paso 0-2 no fueron suficientes. Antes hacer **backup completo** con `git clone --mirror` a un drive externo.

**Comando ilustrativo (NO EJECUTAR sin coordinación)**:
```bash
# 1. Backup ANTES
git clone --mirror . ../Copernicus-v1.git.backup-pre-filter

# 2. Instalar filter-repo
pip install git-filter-repo

# 3. Borrar PPTX viejos de la historia (mantiene los del HEAD actual)
git filter-repo --path-glob '**/*.pptx' --invert-paths --refs refs/heads/main

# 4. Cleanup
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 5. Force push (coordinar con todos los collaborators ANTES)
git push --force origin main
```

---

## 3. Recomendación

### Opción combinada A+B (con C reservado como último recurso)

| Fase | Opción | Riesgo | Costo |
|---|---|---|---|
| **Inmediato** | Paso 0 (gitignore) | Nulo | $0 |
| Semana 1 | Opción A (LFS para lo que se debe versionar) | Bajo | $0–5/mes |
| Semana 2-3 | Opción B (R2 para imágenes/GIFs/PPTX) | Medio | ~$2/mes |
| Mes 2+ | Opción C (solo si pasamos 40 GB) | Alto | $0 |

**Justificación**:
- R2 es **claramente el endgame correcto** ($2/mes vs $60/año de LFS; sin cap de bandwidth; mismo patrón que `Landsat-v1`)
- LFS es un puente útil para 1-2 binarios que sí necesitan estar en git (ej. `plantillas/Cambios_morfologicos.pptx` que es código del proyecto)
- `filter-repo` solo si la historia vieja sigue pesando demasiado después de B

---

## 4. Pasos accionables (orden ascendente de riesgo)

### Paso 0 — HOY MISMO (no destructivo, ataca la causa raíz)

**Objetivo**: que el próximo cron NO agregue 30 MB de binarios a la historia.

1. Agregar al `.gitignore`:
   ```gitignore
   # === Binarios generados por cron — NO versionar (servir desde R2 o release) ===
   docs/sentinel2/*/reportes/*.pptx
   docs/sentinel2/*/timelapses/*.gif
   docs/reportes/*.pptx
   docs/timelapses/*.gif
   # PPTX en raíz data/ son legacy — también ignorar
   data/sentinel2/*/reportes/*.pptx
   data/sentinel2/*/timelapses/*.gif
   ```

2. **Modificar el cron `copernicus.yml`** para que NO haga `git add` de esos paths. Ejemplo de filtro defensivo:
   ```yaml
   - name: Commit (excluyendo binarios pesados)
     run: |
       git add docs/sentinel2/**/*.json docs/sentinel2/**/metadata*
       git add docs/fechas_disponibles_copernicus.json
       # NO hacer git add . — agregaría PPTX/GIFs
       git commit -m "auto: update metadata $(date -u +%F)" || true
   ```

3. **Importante**: los archivos ya commiteados siguen ahí. El `.gitignore` solo previene nuevos commits. Para limpiar la historia → Opción C.

**Verificación**:
```bash
git check-ignore docs/sentinel2/Villarrica/reportes/test.pptx
# debe imprimir el archivo (= está ignorado)
```

### Paso 1 — Semana 1 (Git LFS para activos que sí deben versionarse)

Solo para archivos que son **código** del proyecto (plantillas, PDFs de bibliografía):

```bash
git lfs install
git lfs track "bibliografia/pdfs/*.pdf"
git lfs track "docs/plantillas/*.pptx"
git add .gitattributes
git commit -m "chore(infra): trackear PDFs/plantillas con Git LFS"
git push
```

**Verificación**:
```bash
git lfs ls-files
# debe listar los PDFs de bibliografia/
```

### Paso 2 — Semanas 2-3 (Cloudflare R2)

**2.1 Crear bucket R2**:
1. Login Cloudflare → R2 → Create bucket → nombre: `copernicus-v1-assets`
2. Crear API token con permisos `Object Read & Write` para ese bucket
3. Guardar credenciales en GitHub Secrets:
   - `R2_ACCOUNT_ID`
   - `R2_ACCESS_KEY_ID`
   - `R2_SECRET_ACCESS_KEY`
   - `R2_BUCKET=copernicus-v1-assets`
4. Habilitar `r2.dev` public URL en el bucket (gratis) o configurar dominio custom

**2.2 Subir histórico inicial** (one-shot, ~1.6 GB):

```python
# upload_to_r2.py
import boto3
from pathlib import Path
import os

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
    aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    region_name="auto",
)

BUCKET = os.environ["R2_BUCKET"]
ROOT = Path("docs/sentinel2")

for f in ROOT.rglob("*"):
    if f.is_file() and f.suffix.lower() in {".png", ".gif", ".pptx"}:
        key = f.relative_to("docs").as_posix()  # sentinel2/Villarrica/...
        print(f"Uploading {key} ({f.stat().st_size//1024} KB)")
        s3.upload_file(str(f), BUCKET, key)
```

**2.3 Modificar workflow `copernicus.yml`** — agregar paso post-descarga:

```yaml
- name: Upload nuevos PNGs/PPTX a R2
  env:
    R2_ACCOUNT_ID: ${{ secrets.R2_ACCOUNT_ID }}
    R2_ACCESS_KEY_ID: ${{ secrets.R2_ACCESS_KEY_ID }}
    R2_SECRET_ACCESS_KEY: ${{ secrets.R2_SECRET_ACCESS_KEY }}
    R2_BUCKET: ${{ secrets.R2_BUCKET }}
  run: |
    pip install boto3
    python scripts/upload_to_r2.py
```

**2.4 Modificar frontend** — agregar variable global en `docs/index.html`:

```html
<script>
  // Switch entre path relativo (legacy) y R2 (nuevo)
  window.IMG_BASE_URL = "https://copernicus-v1-assets.<accountid>.r2.dev/";
  // window.IMG_BASE_URL = "";  // fallback a paths relativos durante transición
</script>
```

Y en cada lugar donde se construye una URL de imagen:
```js
const url = `${window.IMG_BASE_URL}sentinel2/${volcan}/${fecha}_RGB.png`;
```

**2.5 Período de gracia**: mantener PNGs en git **1 mes** con fallback en JS. Si R2 falla, frontend usa paths relativos. Después del mes, borrar de HEAD (no de historia todavía).

### Paso 3 — Mes 2+ (filter-repo, SOLO si necesario)

Pre-requisitos:
- [ ] R2 estable 30+ días
- [ ] Repo todavía supera 40 GB
- [ ] Nicolás confirma que está dispuesto a invalidar clones
- [ ] **Backup completo** `git clone --mirror` antes
- [ ] Notificar a contributors (si los hay) con 1 semana de anticipación

Ver comando en Opción C arriba.

---

## 5. Snippets útiles

### Listar candidatos a R2 (qué subir primero)

```bash
# Top 50 archivos más pesados en HEAD
find docs data -type f \( -name "*.png" -o -name "*.gif" -o -name "*.pptx" \) \
  -exec du -b {} + | sort -n -r | head -50
```

### Verificar tamaño de LFS antes de push

```bash
git lfs ls-files --size
git lfs status
```

### Medir el repo en cualquier momento

```bash
echo "=== Working tree ===" && du -sh . --exclude=.git
echo "=== .git ==="          && du -sh .git
echo "=== Pack stats ==="    && git count-objects -vH
echo "=== Top 10 blobs ==="  && \
  git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob"' | sort -k3 -n -r | head -10
```

### Subir un archivo suelto a R2 con `aws-cli` (alternativa a boto3)

```bash
aws s3 cp imagen.png s3://copernicus-v1-assets/sentinel2/Villarrica/ \
  --endpoint-url=https://<accountid>.r2.cloudflarestorage.com
```

---

## 6. Métricas de seguimiento

Crear `bibliografia/REPO_SIZE_TRACKING.md` con tabla mensual:

| Fecha | `.git` | HEAD | Δ vs mes anterior | Acciones |
|---|---|---|---|---|
| 2026-05-17 | 19 GB | 2.0 GB | baseline | Paso 0 pendiente |
| 2026-06-17 | (esperado <20 GB tras Paso 0) | | | |

**Cron mensual sugerido** (`.github/workflows/size_audit.yml`):
```yaml
on:
  schedule:
    - cron: "0 12 1 * *"  # día 1 de cada mes
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - run: |
          SIZE_GIT=$(du -sb .git | cut -f1)
          SIZE_HEAD=$(du -sb --exclude=.git . | cut -f1)
          echo "::warning::Repo .git=$((SIZE_GIT/1024/1024/1024))GB HEAD=$((SIZE_HEAD/1024/1024/1024))GB"
          # opcional: fail si >40GB
          [ $SIZE_GIT -gt 42949672960 ] && exit 1 || exit 0
```

---

## 7. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| R2 cae durante cron | Baja | Frontend sin imágenes | Fallback JS a path relativo + retry exponencial |
| Cron sigue commiteando binarios pese al gitignore | Media | Crecimiento continúa | Audit en CI: fallar el workflow si `git diff --cached --stat` muestra `*.pptx` |
| Force-push de filter-repo destruye trabajo local | Alta si no se coordina | Pérdida de commits | Backup `clone --mirror` + aviso 1 semana antes |
| LFS bandwidth se agota → Pages cae | Media | Dashboard sin imágenes | NO usar LFS para archivos servidos por Pages; eso es justamente para qué usamos R2 |
| URL de R2 cambia (rebrand Cloudflare) | Baja | Romper todos los links | Configurar dominio custom desde el día 1: `assets.copernicus.mendozavolcanic.dev` |

---

## 8. Próximos pasos sugeridos para Nicolás

**Acción HOY (5 minutos, cero riesgo)**:
1. Revisar este documento
2. Aprobar el Paso 0 (agregar reglas a `.gitignore`)
3. Modificar `copernicus.yml` para no hacer `git add .` ciego

**Acción esta semana**:
1. Crear cuenta Cloudflare (si no existe) y bucket R2
2. Avisar al asistente para que escriba el `upload_to_r2.py` y modifique workflow

**Decisión pendiente**:
- ¿Mantenemos PPTX en el repo (vía LFS) o se sirven 100% desde R2?
  - Argumento R2: $1.50/mes y se acabó el problema
  - Argumento LFS: PPTX son entregables a SERNAGEOMIN, tener versionado puede ser útil
  - **Recomendado**: PPTX a R2 (entrega) + plantillas en LFS (código)

---

## Referencias

- Auditoría infra: `AUDITORIA_INFRA_2026-05-17.md` (raíz del proyecto)
- Precedente: `Landsat-v1` repo usa R2 desde el día 1
- Cloudflare R2 pricing: https://developers.cloudflare.com/r2/pricing/
- Git LFS pricing: https://docs.github.com/en/billing/managing-billing-for-git-large-file-storage
- `git-filter-repo`: https://github.com/newren/git-filter-repo
