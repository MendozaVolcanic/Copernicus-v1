# AUDITORÍA EXHAUSTIVA — Código Python Copernicus-v1

**Fecha:** 2026-05-17
**Auditor:** Claude (Opus 4.7)
**Alcance:** 14 scripts Python (5.511 LOC) en raíz del proyecto.
**Foco:** bugs latentes, performance, mantenibilidad, robustez, calidad algorítmica, test coverage.

---

## 1. Resumen ejecutivo

- **Bug crítico bloqueante**: `spectral_downloader.py` importa `SentinelDownloader` que **no existe** en `sentinel2_downloader.py` (la clase real es `SentinelHubDownloader`). El script falla con `ImportError` antes de ejecutar nada. Esto explica por qué los PNGs NDVI/NBR/SWIR_Anomaly están vacíos para muchos volcanes.
- **Cero tests automatizados**. No hay carpeta `tests/`, no hay `test_*.py`, no hay fixtures, no hay CI verificando lógica. Todo el sistema (NHI, VRP, Mahalanobis, downloads) depende de validación manual.
- **Acoplamiento severo a paths hardcoded estilo Unix** en flujos críticos (`/tmp/`, `/usr/share/fonts/...`, `docs/sentinel2/...`). El proyecto solo corre en CI Linux: en Windows local (entorno declarado del usuario) varios scripts caen sin avisar.
- **Duplicación masiva**: `timelapse_generator.py` ↔ `timelapse_generator_auto.py` repiten ~250 líneas idénticas (`agregar_escala_kilometros`, `agregar_overlay_copernicus`, `descargar_logo_copernicus`, `crear_logo_copernicus_texto`, lista `VOLCANES_ACTIVOS`). Misma lista en `ppt_generator.py`. Cinco fuentes de verdad para los 46 volcanes.
- **Calidad algorítmica desigual**: NHI y VRP están implementados según Marchese 2019 / Coppola 2016 pero con **proxy SWIR no calibrado** (factor empírico `L_proxy_factor=50`) sobre PNGs LINEAL clip 0-1, no sobre radiancia TOA — la "métrica en Watts" comparable a MIROVA es nominalmente correcta pero numéricamente aproximada. Bien documentado en docstrings, pero el README/dashboard no advierte el caveat.

---

## 2. Tabla de hallazgos por severidad

| ID | Severidad | Archivo:línea | Categoría | Síntesis |
|----|-----------|---------------|-----------|----------|
| H01 | 🔴 | spectral_downloader.py:27 | Bug crítico | Import inexistente `SentinelDownloader` rompe el script entero |
| H02 | 🔴 | ppt_generator.py:128-129 | Bug cross-platform | `/tmp/` hardcoded — falla en Windows local del usuario |
| H03 | 🔴 | timelapse_generator.py:92 / 159 / 186 / 187 / timelapse_generator_auto.py:64 / 108 / 128 / 129 / ppt_generator.py | Bug cross-platform | Fuentes `/usr/share/fonts/.../DejaVuSans*.ttf` solo existen en Linux |
| H04 | 🔴 | sentinel2_downloader.py:421 (`Path(metadata_path).parent.mkdir`) y todos los `docs/sentinel2/{vol}/...` con f-strings | Bug latente | Mezcla `os.path.join` + f-strings con `/` — funciona pero rompe semántica si CWD cambia; varios scripts asumen CWD=raíz repo |
| H05 | 🔴 | change_analysis.py:991, 1004 | Bug NameError potencial | `PRIORIDAD_ESTADO` se usa en `analizar_cambio_volcan` (línea 991) pero está definido DESPUÉS, en línea 1069 (módulo se carga top-down → ok en runtime porque la función se llama tras carga, pero rompe si se importa antes de definir el dict) |
| H06 | 🔴 | sentinel2_downloader.py:565-567 | Robustez | `except Exception as e` traga TODO en bucle de volcanes — un solo error de red da `SUCCESS` falso (anti-patrón ya documentado en lecciones #4) |
| H07 | 🔴 | change_analysis.py:1262, 1265 | Path frágil | Rutas relativas a `..\Mirova-v1\...` y `..\NHI-Tool\...` — silent skip si no existen (cross-referencia se pierde sin warning) |
| H08 | 🟠 | gif_optimizer.py:160-170, ppt_generator.py:75-89 | Memory leak | Frames de GIF no cerrados (`Image.open` + `seek`); en lotes >40 volcanes acumula gigabytes en RAM |
| H09 | 🟠 | change_analysis.py:213 | Performance | `np.stack(arrays)` carga 8-10 imágenes 800×800×3 enteras en RAM por volcán; se podría streamear mediana con `np.percentile` por chunks |
| H10 | 🟠 | timelapse_generator.py vs *_auto.py | DRY | ~250 líneas duplicadas (overlay, escala, logo). Bug en una no se propaga a la otra |
| H11 | 🟠 | timelapse_generator.py:31-44, *_auto.py:20-33, ppt_generator.py:29-44, change_analysis.py:104-115, alert_generator.py | DRY | Lista de 43+3 volcanes redefinida en ≥5 archivos. `config_sentinel2.VOLCANES` debería ser fuente única |
| H12 | 🟠 | change_analysis.py:67-92 | Magic numbers | 15+ constantes (umbrales NHI/VRP/NDSI/zscore/cobertura) hardcoded como globals. Difícil A/B testing y reproducibilidad. Deberían estar en YAML/JSON versionado |
| H13 | 🟠 | sentinel2_downloader.py:491 | Antipattern | `MODO_SOBRESCRITURA = False` definido DENTRO del bucle interior — debería ser parámetro o constante de módulo |
| H14 | 🟠 | change_analysis.py:1252-1253, 1313-1314, change_detector.py:48-49 | Robustez | `except Exception as e: return None/error` traga errores. Sin logging estructurado, falla silenciosa en producción |
| H15 | 🟠 | ppt_generator.py:91-95, gif_optimizer.py:307-308 | Antipattern | `except Exception` con `import shutil` dentro — re-import + fallback que oculta el bug original |
| H16 | 🟠 | sentinel2_downloader.py:235-239 | Retry logic incompleta | Solo reintenta en 401. Ignora 429 (rate limit), 503 (service unavailable), timeouts. Falta backoff exponencial |
| H17 | 🟠 | change_analysis.py:127-141 | Algoritmo | Máscara de nubes por brillo+saturación es muy simple. Marchese 2019 recomienda usar la SCL de S2 L2A (banda 8A) o al menos NDSI. El método actual marca cráteres nevados como "nube" |
| H18 | 🟠 | change_analysis.py:538-578 | Algoritmo | `filtro_ndsi_glaciar` usa canal G del RGB sRGB como proxy de B03 lineal — la propia docstring admite "aproximación burda". Falsos negativos en glaciares activos |
| H19 | 🟠 | change_analysis.py:514 | Algoritmo | `L_proxy_factor = 50` es un magic number sin cita bibliográfica. Coppola/Wooster usan radiancia MIR calibrada (W·m⁻²·sr⁻¹·µm⁻¹) — aquí PNG normalizado clip 0-1. La métrica VRP_MW no es comparable directamente a MIROVA |
| H20 | 🟠 | generar_proximas_pasadas.py:39-43 | Algoritmo | Interpolación lineal de hora UTC entre lon=-73.5 y -67. Funciona dentro de Chile pero rompe en bordes (lon < -73.5: extrapola fuera del rango clampeado). El comentario dice "lineal interpolando" pero clampa duro a [14:40, 14:58] |
| H21 | 🟠 | sentinel2_downloader.py:373 | Bug data | `fecha = nombre.split('_')[0]` — si el volcán tiene "_" en nombre (`Hudson_Ultima_Erupcion`) esto sigue funcionando porque la fecha va PRIMERO. Pero rompe si alguien renombra archivos. Frágil. |
| H22 | 🟠 | change_analysis.py:1408-1419 | Robustez | Historial se carga con `json.load`, si el archivo está corrupto (escrito durante crash) se reemplaza con `{}` silenciosamente y se pierden los 30 registros previos. Falta backup atómico (.tmp + rename) |
| H23 | 🟠 | ppt_generator.py:200, 196 | Antipattern | Búsqueda "volcán" en texto de slide es case-insensitive pero match contra 46 volcanes en bucle. O(N×M) por cada shape — y si dos volcanes tienen substring común (`San Jose` ⊂ `San Pedro`? no, pero similares) puede haber matches cruzados |
| H24 | 🟡 | change_analysis.py:23-24 | Cross-platform | `sys.stdout.reconfigure(encoding='utf-8')` solo en win32 — falla en Python <3.7. OK para 3.12 declarado, pero quitar el guard si solo se soporta 3.12 |
| H25 | 🟡 | timelapse_generator.py:50, 62 | URL frágil | `COPERNICUS_LOGO_URL` y el fallback de identity.copernicus.eu son URLs externas que pueden romperse silenciosamente (función ya tiene fallback texto, ok). Considerar cachear el PNG en el repo |
| H26 | 🟡 | image_compression.py:103-108 | Antipattern | `except Exception` → fallback a `image.save(output_path)` sin loggear qué falló. Si compression_level era inválido el log no lo dice |
| H27 | 🟡 | firms_integration.py:74 | Validación | `if len(cols) < 11: continue` silencia filas malformadas. Sin contador, no se sabe cuántas se perdieron |
| H28 | 🟡 | sentinel2_downloader.py:172, 254 | DRY | `create_bbox` duplicada en `SentinelHubSearcher` y `SentinelHubDownloader`. Una sola función auxiliar de módulo |
| H29 | 🟡 | change_detector.py (entero, 209 LOC) | Código muerto | El módulo nuevo es `change_analysis.py` (1455 LOC). `change_detector.py` sigue ahí pero no se usa desde ningún cron. Eliminar o marcar deprecated |
| H30 | 🟡 | alert_generator.py (entero) | Código muerto | No se invoca desde ningún workflow `.github/workflows/`. Si está pendiente de integrar, agregar TODO; si no, archivar |
| H31 | 🟡 | Todos | Type hints | Cero `def f(x: str) -> dict:`. mypy --strict no pasa. Geólogo + agentes futuros se beneficiarían |
| H32 | 🟡 | change_analysis.py:265-316, 783-1062 | Mantenibilidad | `clasificar_con_zscore` (52 LOC) y `analizar_cambio_volcan` (~280 LOC) son funciones gigantes. Subdividir en `clasificar_por_zscore`, `evaluar_consistencia`, `armar_resultado_final` |

---

## 3. Detalle por hallazgo

### 🔴 H01 — `spectral_downloader.py` import inexistente

**Archivo:** `spectral_downloader.py:27`
```python
from sentinel2_downloader import SentinelDownloader
```
**Realidad:** `sentinel2_downloader.py` define `SentinelHubAuth`, `SentinelHubSearcher`, `SentinelHubDownloader`. No existe `SentinelDownloader`.

**Impacto:** El workflow de NDVI/NBR/SWIR_Anomaly nunca corrió desde que se renombró la clase. Esto explica directamente por qué `change_analysis.analizar_indices_espectrales` cae al `path_nueva` no existente y los disponibles[] suele venir vacío.

**Sugerencia:** Importar `SentinelHubAuth` y `SentinelHubDownloader`, instanciar manualmente (`auth = SentinelHubAuth(); downloader = SentinelHubDownloader(auth)`). Línea 59 también está rota: `downloader = SentinelDownloader()` no acepta args ni existe.

---

### 🔴 H02 — `/tmp/` hardcoded en `ppt_generator.py`

**Archivo:** `ppt_generator.py:128-129`
```python
temp_rgb = f"/tmp/{volcan_nombre}_RGB.gif"
temp_thermal = f"/tmp/{volcan_nombre}_Thermal.gif"
```

**Impacto:** En Windows (PC del usuario) `/tmp/` no existe — `shutil.copy2` cae con `FileNotFoundError`. El except línea 91 lo traga y devuelve el path inexistente, que después `slide.shapes.add_picture` rechaza. Solo funciona en GitHub Actions (Ubuntu runner).

**Sugerencia:** `tempfile.gettempdir()` o `tempfile.NamedTemporaryFile(suffix='.gif', delete=False)`.

---

### 🔴 H03 — Fuentes Linux hardcoded

**Archivos:** `timelapse_generator.py:92, 159, 186-187`; `timelapse_generator_auto.py:64, 108, 128-129`; logos.

```python
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
```

**Impacto:** En Windows cae al `except` y usa `ImageFont.load_default()` (~8px Pillow fixed). Overlay queda ilegible. El usuario probablemente no testea timelapses local por esto.

**Sugerencia:** Bundlar `assets/fonts/DejaVuSans-Bold.ttf` en el repo y cargar relativo. O detectar OS y usar `C:/Windows/Fonts/arial.ttf` en fallback.

---

### 🔴 H04 — Paths relativos asumen CWD=raíz

**Archivos:** múltiples. Ejemplos:
- `sentinel2_downloader.py:365` → `f"docs/sentinel2/{volcan_nombre}"`
- `timelapse_generator.py:286` → `f"docs/sentinel2/{volcan_nombre}"`
- `change_analysis.py:30-35` usa `BASE_DIR = os.path.dirname(os.path.abspath(__file__))` (✅ correcto), pero otros scripts NO.

**Impacto:** Si cron corre desde otro CWD (cron en Linux suele ser `$HOME`), todos los `docs/...` apuntan a otro lado. En Actions funciona porque `working-directory: ./Copernicus-v1`. Local cualquier ejecución manual desde otro folder rompe.

**Sugerencia:** Patrón unificado: `BASE_DIR = Path(__file__).resolve().parent` y `DOCS = BASE_DIR / "docs"`. Eliminar todos los strings `"docs/..."` literales.

---

### 🔴 H05 — `PRIORIDAD_ESTADO` referenciada antes de definir

**Archivo:** `change_analysis.py:991` usa `PRIORIDAD_ESTADO`, definida línea 1069.

**Impacto:** Funciona en runtime (Python resuelve nombres a llamada de función, no a definición), pero:
1. Linters lo marcan.
2. Si alguien refactoriza y mueve la función a otro módulo sin la constante, no detecta.
3. Si se llama `analizar_cambio_volcan` desde un test ANTES de que el módulo termine de cargar (no típico, pero posible con import circular), `NameError`.

**Sugerencia:** Mover `PRIORIDAD_ESTADO` arriba con las otras constantes (línea ~100).

---

### 🔴 H06 — `except Exception` traga errores en bucle principal

**Archivo:** `sentinel2_downloader.py:565-567`
```python
except Exception as e:
    print(f" Error: {e}")
    continue
```

**Impacto:** Ya documentado como anti-patrón (lección #4 del CLAUDE.md). Aún así sigue ahí. Si 43 volcanes fallan, el workflow termina con SUCCESS pero `actualizar_metadata` jamás se llamó. El JSON `fechas_disponibles_copernicus.json` se regenera vacío y borra el calendario.

**Sugerencia:** Capturar `requests.RequestException` específicamente. `Exception` debería re-raisar o al menos incrementar un contador de fallos y abortar si fallos > 20%.

---

### 🔴 H07 — Cross-referencias silently-failing

**Archivo:** `change_analysis.py:32-35`
```python
LANDSAT_DIR = os.path.join(BASE_DIR, "..", "Landsat-v1", "docs", "landsat")
NHI_DIR = os.path.join(BASE_DIR, "..", "NHI-Tool", "docs", "nhi_data")
MIROVA_CSV = os.path.join(BASE_DIR, "..", "Mirova-v1", "monitoreo_satelital", "registro_vrp_maestro_publicable.csv")
```

**Impacto:** Si esas carpetas no existen (clones parciales, CI sin checkout de los repos hermanos), funciones como `obtener_estado_nhi` y `obtener_vrp_mirova` devuelven `None` sin avisar. El usuario podría creer que su volcán no tiene VRP cuando en realidad no se leyó el CSV.

**Sugerencia:** En `main()`, validar al arranque y loggear: `if not MIROVA_CSV.exists(): logger.warning("Cross-ref MIROVA deshabilitado")`.

---

### 🟠 H08 — PIL Image no cerrado en loops de GIF

**Archivos:** `gif_optimizer.py:294-302`, `ppt_generator.py:71-80`, `timelapse_generator.py:343-358`.

```python
gif = Image.open(ejemplo)
frames = []
while True:
    frames.append(gif.copy())  # no se cierra el handle
    gif.seek(gif.tell() + 1)
```

**Impacto:** 46 volcanes × 2 tipos × ~12 frames × 800×800×3 bytes = ~1.3 GB en RAM. En Actions runner (7 GB) sobrevive, pero local en laptop con browser abierto puede OOM. Y nunca se llama `gif.close()` ni se usa `with`.

**Sugerencia:** `with Image.open(...) as gif: frames = [f.copy() for f in ImageSequence.Iterator(gif)]`.

---

### 🟠 H09 — `np.stack` de imágenes completas

**Archivo:** `change_analysis.py:213`
```python
stack = np.stack(arrays, axis=0)
mediana = np.median(stack, axis=0).astype(np.uint8)
```

**Impacto:** 10 imágenes × 800×800×3 × 8 bytes (float median intermedio) ≈ 153 MB por volcán solo para la mediana. Multiplicado por 46 volcanes secuenciales no es problema (se libera), pero si alguien paraleliza, RAM explota.

**Sugerencia:** `np.median` ya es óptimo en memoria; el problema es que `arrays` (lista python) sostiene N copias. Liberar tras stack: `del arrays`.

---

### 🟠 H10 — Duplicación entre `timelapse_generator.py` y `_auto.py`

Funciones idénticas: `descargar_logo_copernicus`, `crear_logo_copernicus_texto`, `agregar_escala_kilometros`, `agregar_overlay_copernicus`.

**Sugerencia:** Extraer a `timelapse_common.py` y que ambos generadores importen. Reduce ~250 LOC.

---

### 🟠 H11 — Lista de volcanes duplicada en 5 archivos

`VOLCANES_ACTIVOS` aparece en:
- `timelapse_generator.py:31-44`
- `timelapse_generator_auto.py:20-33`
- `ppt_generator.py:29-44`
- `change_analysis.py:103-115` (variante `ZONAS`)
- Implícita en `config_sentinel2.VOLCANES`

**Impacto:** Cuando se agregaron las 3 vistas zoom (Hudson_Ultima_Erupcion, etc.), `ppt_generator.py` SÍ las incluye (línea 43), `timelapse_generator.py` NO (línea 44). Así que las vistas zoom no tienen timelapse pero sí PPT — inconsistencia visible.

**Sugerencia:** `from config_sentinel2 import get_active_volcanoes; VOLCANES_ACTIVOS = list(get_active_volcanoes())`. Una línea, fuente única.

---

### 🟠 H12 — 15+ magic numbers en `change_analysis.py`

Líneas 67-92: `UMBRAL_NUBE_BRILLO=220`, `UMBRAL_NUBE_SATURACION=15`, `ZONA_CENTRAL_RATIO=0.6`, `MIN_PIXELES_VALIDOS=0.20`, `UMBRAL_CAMBIO_PIXEL=25`, `UMBRAL_NDSI_NIEVE=0.4`, `NHI_HOT_PIXEL_UMBRAL=5`, `NHI_STRICT_PIXEL_UMBRAL=2`, `NHI_MAX_UMBRAL_ATENCION=0.4`, `NHI_VALOR_UMBRAL=0.30`, `NHI_VALOR_UMBRAL_STRICT=0.20`, `NHI_BRILLO_MIN_SWIR=0.35`, `A_PIXEL_S2_SWIR_M2=400.0`, `VRP_COEF_WOOSTER=18.9`.

**Sugerencia:** `config_change_detection.yaml` (versionado) con todos los umbrales y carga con `yaml.safe_load`. Permite A/B testing y reproducibilidad por commit.

---

### 🟠 H13 — `MODO_SOBRESCRITURA` dentro del loop

**Archivo:** `sentinel2_downloader.py:491`
```python
for tipo in ['RGB', 'ThermalFalseColor']:
    output_path = get_image_path(nombre_volcan, fecha, tipo)
    MODO_SOBRESCRITURA = False  # ← cada iteración redefine
    if os.path.exists(output_path) and not MODO_SOBRESCRITURA:
```

**Sugerencia:** Mover a constante de módulo (línea ~30) o flag CLI `--force`.

---

### 🟠 H14 — Logging por `print`, no `logging`

Todo el código usa `print()`. Implicaciones:
- No se puede silenciar por nivel.
- No hay timestamps automáticos.
- En Actions, los emojis 🎬 ⚠️ aparecen como `?` si encoding falla.
- No hay forma de redirigir a syslog/Sentry.

**Sugerencia:** `logging.getLogger(__name__)` con formato `%(asctime)s %(levelname)s %(name)s %(message)s`.

---

### 🟠 H15 — Patrón `try: ... except: shutil.copy` esconde el bug

**Archivo:** `ppt_generator.py:91-95`
```python
except Exception as e:
    print(f"      ❌ Error: {e}")
    import shutil
    shutil.copy2(input_path, output_path)
    return output_path
```

**Impacto:** Si la compresión PIL falla (GIF corrupto, OOM, lo que sea), copia el original. El PPT queda con un GIF de 5 MB cuando se esperaba 1 MB. El usuario no sabe que la "compresión" falló.

---

### 🟠 H16 — Retry incompleto

**Archivo:** `sentinel2_downloader.py:300-346`

Solo reintenta en 401. Falta:
- **429 (rate limit)**: Copernicus tiene ~200 req/min — sin backoff cae si scrapeas 46 volcanes rápido.
- **503**: servidor saturado, retry con jitter.
- **Timeouts** (`requests.exceptions.Timeout`): cae directo al `except` y devuelve False sin reintentar.

**Sugerencia:** Usar `urllib3.util.Retry` o `tenacity`:
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2),
       retry=retry_if_exception_type((Timeout, ConnectionError)))
```

---

### 🟠 H17 — Máscara de nubes naive

**Archivo:** `change_analysis.py:127-141`
```python
mascara = (brillo > 220) & (rango_color < 15)
```

Esto marca como nube:
- Cráteres con depósito de azufre blanco (Lascar, Copahue).
- Glaciares fuertemente iluminados (Villarrica).
- Imágenes saturadas por refleo de roca felsica.

Y NO marca:
- Nubes finas (cirrus) que sí afectan SWIR.
- Sombras de nube (problema simétrico).

**Sugerencia:** Solicitar la banda SCL (Scene Classification Layer) de S2 L2A en un evalscript adicional. SCL ya separa nube/sombra/nieve/agua. Marchese 2019 lo recomienda explícitamente.

---

### 🟠 H18 — `filtro_ndsi_glaciar` aproximación documentadamente burda

**Archivo:** `change_analysis.py:546-578`. Docstring ya admite el problema. Usa canal G del PNG RGB (sRGB-encoded) como proxy de B03 lineal, y G del thermal (lineal) como B11. La gamma 2.2 aplicada es aproximada.

**Sugerencia:** Sprint 2 ya planeado en el roadmap. Descargar B03 y B11 puros (no compositados) por evalscript LINEAL. ~150 KB extra por imagen.

---

### 🟠 H19 — VRP "estimado" no calibrado

**Archivo:** `change_analysis.py:514`
```python
L_proxy_factor = 50.0
```

Sin cita bibliográfica. Coppola 2016 usa radiancia MIR (3.9µm) calibrada. Aquí PNG normalizado 2.5×B12 clip 0-1. El factor 50 es un guess que da números "razonables" en MW pero **no comparables** con MIROVA.

**Sugerencia:** Documentar en el dashboard "VRP estimado (no calibrado) — para comparación intra-Copernicus, no contra MIROVA". O descargar SWIR raw y calibrar a radiancia con factor TOA de Copernicus.

---

### 🟠 H20 — Predicción de hora UTC

**Archivo:** `generar_proximas_pasadas.py:39-43`. Interpolación lineal entre lon=-73.5 y lon=-67 OK dentro del rango. Pero:
- Hudson (lon=-72.96) está casi en el borde.
- Si en el futuro se agregan volcanes argentinos (lon > -67), clampa.

**Sugerencia:** Calcular desde TLE real de Sentinel-2 (CelesTrak) o desde STAC API timestamps reales.

---

### 🟠 H21 — Parse de fecha por split

`fecha = nombre.split('_')[0]` aparece en ≥6 lugares. Funciona porque fecha siempre va PRIMERO en el filename. Pero asumir es frágil.

**Sugerencia:** Regex `^(\d{4}-\d{2}-\d{2})_` o `datetime.strptime(nombre[:10], '%Y-%m-%d')` con validación.

---

### 🟠 H22 — Historial JSON sin escritura atómica

**Archivo:** `change_analysis.py:1439-1441`
```python
with open(history_path, 'w', encoding='utf-8') as f:
    json.dump(historial, f, ensure_ascii=False, indent=2)
```

Si crash entre `open(..., 'w')` y `dump` (kill, power loss), file queda truncado/vacío. El except line 1400 lo lee como `{}` y reinicia el historial.

**Sugerencia:** Pattern: escribir a `history_path + ".tmp"`, luego `os.replace(tmp, final)`. Atómico en POSIX y Windows >= Vista.

---

### 🟠 H23 — Match de nombre de volcán O(N×M)

**Archivo:** `ppt_generator.py:199-203`. Por cada shape con "volcán" en texto, itera los 46 volcanes y hace `.lower() in texto.lower()`. Si en el futuro hay un volcán cuyo nombre es substring de otro, match cruzado.

---

### 🟡 H24-H32

Detalles menores (cosmetic, deuda técnica, observabilidad). Ver tabla.

---

## 4. Calidad de algoritmos vs bibliografía

| Algoritmo | Implementado | Referencia | Conformidad |
|-----------|--------------|-----------|-------------|
| NHI_SWIR (B12-B11)/(B12+B11) | Sí (`_calcular_nhi_generico`) | Marchese 2019 | ✅ Fórmula correcta. Umbral 0.30 es estricto (paper usa >0, pero sobre TOA). Ajuste razonable para PNG normalizado. |
| NHI_SWNIR (B12-B04)/(B12+B04) | Sí | Massimetti 2020 | ✅ |
| VRP Wooster | Aproximado | Coppola 2016/Wooster 2003 | 🟠 Coeficiente 18.9 y A_pixel=400 m² correctos; pero L_proxy_factor=50 sin calibrar (H19) |
| NDSI | Sí (`filtro_ndsi_glaciar`) | Hall 1995, McFeeters 1996 | 🟠 Implementación aproximada (H18) |
| Mahalanobis multivariado | Sí (`calcular_mahalanobis`) | Zhang 2016 LSMAD | ✅ Cov + pseudo-inverse + regularización 1e-3 OK. Umbral d=3.0 ≈ χ²₃ 95% — correcto |
| Z-score temporal | Sí | Estándar | ✅ |
| Confirmación cruzada multi-sensor | Sí | Buena práctica | ✅ Bien implementada con triple_confirmacion |

**Veredicto algorítmico:** la base científica está bien. El gap es la **calibración** (PNG vs radiancia real) y la **validación** (sin tests ni ground truth contra MIROVA en CI).

---

## 5. Test coverage

**Estado actual:** 0%. Cero archivos `test_*.py`. Cero `tests/`. Cero CI que verifique lógica (solo deploy a Pages).

**Casos edge no cubiertos:**
1. PNG truncado mid-download → `Image.open` cae con `UnidentifiedImageError`.
2. CSV metadata.csv con encoding cp1252 (Excel lo guarda así).
3. Fechas duplicadas exactas (mismo satélite mismo día — improbable pero posible).
4. Volcán sin ninguna imagen aún (recién agregado).
5. Token Copernicus revocado mid-batch (no solo expirado).
6. Imágenes 100% nube — `MIN_PIXELES_VALIDOS` ya lo cubre, pero ¿qué pasa si las 10 del background son nubladas?
7. `np.median` sobre stack vacío — protegido (línea 209), ok.
8. `cargar_imagen` devuelve None → la mayoría de callers lo manejan, pero no todos (línea 819 sí).
9. Cambio de schema en respuesta de Copernicus API (`platform` → `platforms`).
10. Mahalanobis con matriz cov singular → ya regularizada con 1e-3.

**Recomendación de tests mínimos (Sprint 2):**
- `test_nhi_fixtures.py`: PNG sintético con pixeles rojos conocidos → assert `n_hot_pixels`.
- `test_clasificar_zscore.py`: combinaciones (alto-bajo) × (con-sin baseline) → estados.
- `test_metadata_io.py`: roundtrip CSV con nombres con guiones/espacios.
- `test_paths.py`: ejecutar scripts desde `/tmp` (CWD distinto) → no debe crashear.
- `test_change_analysis_smoke.py`: correr `analizar_cambio_volcan("Villarrica", "sentinel2")` con un fixture mínimo de 5 PNG.

**Cómo probar manualmente cada script (hasta tener tests):**

| Script | Comando smoke test | Output esperado |
|--------|---------------------|-----------------|
| `sentinel2_downloader.py` | `python sentinel2_downloader.py` con SH_CLIENT_ID dummy | Debe abortar con SystemExit (no continuar) |
| `change_analysis.py` | `python change_analysis.py --test` | JSON con 3 volcanes, no crash |
| `timelapse_generator.py` | `python timelapse_generator.py` con VOLCAN=Villarrica | GIF en `docs/sentinel2/Villarrica/timelapses_ppt/` |
| `gif_optimizer.py` | `python gif_optimizer.py` | Análisis de complejidad del primer GIF encontrado |
| `ppt_generator.py` | `python ppt_generator.py` con VOLCAN=Villarrica | PPTX en `docs/sentinel2/Villarrica/reportes/` |
| `generar_proximas_pasadas.py` | `python generar_proximas_pasadas.py` | `docs/proximas_pasadas.json` regenerado |
| `spectral_downloader.py` | **NO CORRE** — ver H01 | ImportError |

---

## 6. Plan de remediación priorizado

### Sprint A — bloqueantes (esta semana)

1. **H01** — Fix import en `spectral_downloader.py`. 10 min.
2. **H02 + H03** — Reemplazar `/tmp/` y `/usr/share/fonts/...` por `tempfile` y `Path` relativo a `assets/`. 30 min.
3. **H06** — Captura granular de excepciones en bucle principal del downloader, log estructurado, contador de fallos. 1h.
4. **H22** — Escritura atómica de `change_history.json` (tmpfile + rename). 15 min.

### Sprint B — calidad (próximas 2 semanas)

5. **H11 + H10** — Centralizar `VOLCANES_ACTIVOS` en `config_sentinel2.get_active_volcanoes()`; mover funciones comunes de timelapse a `timelapse_common.py`. 2h.
6. **H12** — `config_change_detection.yaml` con todos los umbrales. 1h.
7. **H16** — `tenacity` retry con backoff exponencial para todas las llamadas a Copernicus. 1h.
8. **H17** — Agregar evalscript SCL y máscara de nubes basada en banda SCL. 3h (incluye descarga + integración).
9. **Tests smoke** — pytest con 5 tests mínimos listados en sección 5. 4h.

### Sprint C — calibración y robustez (mes siguiente)

10. **H18 + H19** — Descargar B03/B11/B12 LINEAL raw (no compositados); calibrar `L_proxy_factor` contra MIROVA en fechas conocidas (Lascar, Villarrica). 1 semana.
11. **H14** — Migrar de `print` a `logging` con Sentry/syslog handler. 1 día.
12. **H29 + H30** — Decidir destino de `change_detector.py` y `alert_generator.py`: deprecar o integrar a workflows. 30 min decisión + tiempo de integración.
13. **H31** — Type hints + `mypy --strict` en CI. 2-3 días de typing.

---

## 7. Conclusión

El proyecto está **funcionalmente sólido** en lo que ejecuta (descarga S2, GIFs, PPT, change detection). La arquitectura algorítmica refleja correctamente la bibliografía moderna (Marchese, Coppola, Zhang). Pero la implementación arrastra:

- **Un bug crítico activo** (H01) que silenciosamente deshabilita los índices espectrales.
- **Cero tests** — todo cambio es ruleta rusa.
- **Cross-platform broken** (H02/H03) — solo corre en CI Linux.
- **Cinco fuentes de verdad** para 46 volcanes — bug-magnet garantizado.
- **VRP "comparable a MIROVA"** que en realidad no lo es (H19) — riesgo reputacional si SERNAGEOMIN lo cita.

Las fortalezas: documentación inline excelente (docstrings citan papers), evalscripts bien razonados (sRGB vs LINEAL es decisión correcta y documentada), cuantización MAXCOVERAGE es un hallazgo genuino, fail-fast en auth ya implementado.

Con ~2 semanas de trabajo enfocado en Sprint A+B, el proyecto pasa de "demo que funciona en Actions" a "sistema reproducible que un colega puede correr local sin pelearse".
