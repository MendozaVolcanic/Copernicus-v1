# 🔎 Metodología de búsqueda y descarga bibliográfica

**Proyecto:** Copernicus-v1 — monitoreo satelital volcánico
**Carpeta:** `bibliografia/`
**Última actualización:** 2026-05-16
**Objetivo:** consolidar el *cómo* del trabajo bibliográfico (no el *qué*) para que cualquier sesión futura — humana o agente — pueda replicar el workflow sin repetir errores.

> Este documento es **el manual operativo**. Para *qué* se encontró y *cómo se cita*, ver [BIBLIOGRAFIA.md](BIBLIOGRAFIA.md) y los 5 archivos temáticos.

> 📚 **Guía maestra cross-proyecto**: este documento es la versión específica de Copernicus-v1 (editorial behavior, MDPI/Elsevier/Wiley). La **capa común** que aplica a todos los proyectos del workspace está en [`C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_INVESTIGACION.md`](../../../../GUIA_MAESTRA_INVESTIGACION.md). Leer la maestra cuando hagas búsqueda nueva, especialmente para principio rector "agotar local antes que online" (§1), canonicalidad de autores (§6) y anti-patrones cross-proyecto (§10).

---

## 1. Estrategia general

El trabajo bibliográfico del proyecto sigue una secuencia repetible de **4 fases**:

```
BÚSQUEDA  →  TRIAJE  →  DESCARGA  →  EXTRACCIÓN/FICHA
   (1)         (2)         (3)              (4)
```

Cada fase tiene fuentes preferentes, herramientas y un criterio de "listo" antes de pasar a la siguiente. Saltarse el triaje (ir a descargar todo lo encontrado) cuesta horas en PDFs irrelevantes; saltarse la verificación de archivo (ir directo a la ficha) llena la carpeta `pdfs/` de HTML disfrazado de PDF.

---

## 2. Fase 1 — Búsqueda

### 2.1 Fuentes confiables (por orden de uso preferente)

| Fuente | URL/MCP | Ventaja | Cuándo usarla |
|---|---|---|---|
| **Crossref** | `api.crossref.org/works?query=...` | DOI canónico, metadatos limpios | Verificar cita exacta, resolver DOI a partir de título |
| **Semantic Scholar** | `api.semanticscholar.org` | Backreferences y forward citations, abstract, "influential citations" | Mapear el árbol de citas alrededor de un paper seminal |
| **NASA ADS** | `ui.adsabs.harvard.edu` | El mejor índice para remote sensing / geofísica | Búsqueda temática profunda en satelital |
| **arXiv** | `arxiv.org/abs/...` | Preprints open access de papers Elsevier/IEEE/Wiley | Bypass de paywall cuando el autor subió preprint |
| **ResearchGate** | manual via navegador | Autores suben PDFs cuando el journal cobra | Plan B para Elsevier/Springer |
| **Google Scholar** | `scholar.google.com` | Mejor para descubrimiento amplio, peor metadata | Primera pasada exploratoria, no para citar |
| **MCP `perplexity`** | configurado globalmente | Citas con frescura, expansión semántica | Cuando no sabés qué buscar todavía |
| **MCP `context7`** | local | Documentación técnica viva (APIs, SDKs) | Solo para herramientas, NO papers |

### 2.2 Herramientas dentro de Claude Code

| Herramienta | Para qué | Notas |
|---|---|---|
| `WebSearch` | Búsqueda amplia inicial | Devuelve snippets, no descarga |
| `WebFetch` | Leer una URL específica (abstract, landing page) | Devuelve markdown limpio, NO sirve para PDFs (binarios) |
| `mcp__perplexity` | Búsqueda con citas en tiempo real | Mejor para "estado del arte de X en 2024-2025" |
| `Agent` con `subagent_type=Explore` | Búsquedas paralelas independientes | Una pregunta por agente, máx 2-3 en paralelo |

### 2.3 Patrones de búsqueda que funcionaron

**Encontrar el paper seminal:**
1. Buscar el algoritmo por nombre (`"MODVOLC algorithm"`, `"NHI Sentinel-2"`)
2. Tomar el paper más citado → ese es el seminal
3. Hacer backward (qué cita) y forward (qué lo cita) en Semantic Scholar

**Encontrar aplicación a un volcán específico:**
1. `"<Volcán>" + "remote sensing" + "<sensor>"` (ej. `"Villarrica" "MODIS" thermal`)
2. Filtrar por journal: *Journal of Volcanology and Geothermal Research*, *Remote Sensing of Environment*, *Remote Sensing (MDPI)*, *Bulletin of Volcanology*
3. Para autores chilenos agregar afiliaciones: `"SERNAGEOMIN"`, `"Universidad Católica del Norte"`, `"OVDAS"`

**Encontrar review consolidado:**
- `"review" + topic + año reciente` (ej. `"review change detection volcano remote sensing 2023"`)
- Reviews ahorran 50 papers de lectura individual

### 2.4 Criterio de "búsqueda lista"

- [ ] Identificado al menos 1 paper seminal por subtema
- [ ] Cubierto últimos 3-5 años (para no quedar obsoleto)
- [ ] Cubierto autores latinoamericanos cuando aplica (Aguilera, Layana, Romero, Naranjo, Bertin, Lara)
- [ ] Lista priorizada de N candidatos a descargar (no descargar todos)

---

## 3. Fase 2 — Triaje (decidir qué bajar)

**Regla:** bajar 15 PDFs útiles vale más que 50 PDFs nunca leídos.

### 3.1 Señales de "vale la pena bajar"

- Paper seminal de un algoritmo que vas a implementar
- Aplicación al mismo sensor que el proyecto usa (S2 L2A, L8/9 OLI/TIRS)
- Volcán chileno o andino directo
- Review reciente del tema
- Dataset abierto de validación (AVTOD, LEVIR-CD, OSCD)
- Cita ≥ 50 veces y < 10 años (Semantic Scholar lo muestra)

### 3.2 Señales de "no bajar"

- Solo abstract en idioma no-EN/ES sin traducción
- Sensor obsoleto (Landsat 5 TM solo, ASTER pre-2008 sin contexto)
- Topic colateral (caso aislado de un volcán fuera de los 46 del proyecto)
- Conference paper sin journal version (preferir journal cuando existe)
- Preprint sin actualizar en >2 años (probablemente abandonado)

### 3.3 Output del triaje

Una tabla en el archivo temático correspondiente con:
```
| # | Autor año | Título corto | DOI/URL | ¿Bajar? | Prioridad |
|---|---|---|---|---|---|
```
Esto se ve en los 5 archivos temáticos actuales como columna "PDF" (✅/❌).

---

## 4. Fase 3 — Descarga

### 4.1 Comportamiento de cada editorial (verificado en este proyecto)

| Editorial | Comportamiento `curl/wget` | Funciona desde navegador | Mecanismo recomendado |
|---|---|---|---|
| **MDPI** (Remote Sensing, Sensors, Electronics) | ❌ Akamai bloquea bots, devuelve 403 o HTML genérico | ✅ Sí (open access) | Browser manual O `mcp__playwright` para automatizar |
| **Elsevier** (RSE, JVGR, ISPRS) | ❌ Paywall, devuelve HTML de landing | Solo con sesión institucional | ResearchGate / arXiv preprint / VPN SERNAGEOMIN |
| **Wiley** (G3, JGR) | ❌ Paywall | Solo con sesión institucional | ResearchGate / arXiv |
| **Springer/Nature** | Mixto: Nature SciData/SciRep abiertos vía DOI; resto paywall | Sí para SciData/SciRep | DOI directo si SciData; ResearchGate si paywall |
| **IEEE** (TGRS, JSTARS, IGARSS) | ❌ Paywall | Solo con sesión institucional | arXiv preprint (muchos autores suben) |
| **Taylor & Francis** (IJRS) | ❌ Paywall | Solo con sesión institucional | ResearchGate |
| **Geological Society of London** | Mixto | Algunos open | DOI directo, verificar |
| **arXiv** | ✅ `curl https://arxiv.org/pdf/<id>.pdf` funciona | ✅ Sí | curl directo |
| **USGS / NASA / ESA** | ✅ Reports gubernamentales open | ✅ Sí | curl directo |
| **Andean Geology** (SERNAGEOMIN) | ✅ Open access nacional | ✅ Sí | DOI directo (10.5027/andgeoV...) |
| **GitHub releases** (datasets, código) | ✅ | ✅ | `gh release download` o curl |

### 4.2 Comandos concretos que funcionaron

**arXiv / fuentes abiertas:**
```powershell
curl -L -o pdfs/Autor_Año_Tema.pdf "https://arxiv.org/pdf/2106.05095.pdf"
```

**MDPI vía Playwright MCP (cuando hay que automatizar):**
```
mcp__playwright__navigate → URL del paper
mcp__playwright__find → botón "Download PDF"
mcp__playwright__click → descargar
```
Pero en la práctica: **abrir en navegador del usuario es más rápido**.

**Resolver DOI a URL final:**
```powershell
curl -L -I "https://doi.org/10.1080/01431168908903939"
# Mirar el header `location:` final
```

### 4.3 Convención de nombres

Patrón estable usado en `pdfs/`:
```
Autor_Año_TemaCorto.pdf
```
Ejemplos:
- `Wright_2004_MODVOLC.pdf`
- `Coppola_2023_GlobalRadiantFlux_MIROVA.pdf`
- `Barsi2022_L9_TIRS2_commissioning.pdf`

**Reglas:**
- Sin espacios (subrayado o nada)
- Sin acentos
- Sin caracteres especiales que rompan PowerShell/Bash
- Año en 4 dígitos siempre
- Tema en CamelCase o subrayado

### 4.4 VERIFICACIÓN POST-DESCARGA (crítica — lección aprendida)

**Caso real del proyecto** (`IMPLEMENTACION.md:281`):
> `Romero2024_SVZ_Review.pdf` (37 KB) **es solo HTML del journal**, no PDF.

**Checklist obligatorio después de cada descarga:**

```powershell
# 1. Tamaño razonable (papers reales: 200 KB – 30 MB)
Get-Item pdfs/Autor_Año.pdf | Select-Object Name, Length

# 2. Magic bytes empiezan con %PDF
(Get-Content pdfs/Autor_Año.pdf -TotalCount 1 -Encoding Byte | ForEach-Object {[char]$_}) -join ''
# Debe empezar con: %PDF-1.x

# 3. Abrir y confirmar visualmente las primeras páginas
```

**Banderas rojas:**
- Tamaño < 100 KB para un paper de journal → casi siempre es paywall HTML
- Magic bytes empiezan con `<!DOCTYPE` o `<html` → es HTML disfrazado
- Tamaño exactamente 5 KB / 14 KB / 27 KB → patrón típico de landing pages

Si el PDF resulta inválido, **renombrarlo con sufijo `_landingpage_paywall.pdf`** (ej. `Steffke_Harris_2011_landingpage_paywall.pdf`) para no confundirlo con descargas reales, y dejarlo en pendientes.

### 4.5 Estrategias de bypass (orden de preferencia)

1. **Preprint arXiv** — buscar `autor + título + arxiv` en Google. Muchos autores suben preprint.
2. **Página del autor** — buscar página personal/lab; suelen tener PDFs propios.
3. **ResearchGate** — login, pedir copia al autor si no está pública.
4. **VPN institucional SERNAGEOMIN o universidad** — acceso directo al journal.
5. **Sci-Hub** — opción de último recurso. Legalmente gris en muchos países. Documentar uso solo si necesario.
6. **Email al autor** — para papers viejos sin preprint, suele funcionar.

---

## 5. Fase 4 — Extracción y ficha

### 5.1 Convertir PDF a texto/markdown utilizable

**Regla:** ANTES de leer un PDF con `Read`, convertirlo con `markitdown` (skill `anthropic-skills:markitdown`). Ahorra 50-80% de tokens y entrega markdown estructurado.

```
skill markitdown → input PDF → output .md
```

**Salida típica en este proyecto:** `bibliografia/notas/_extracted/<paper>.txt` o equivalente.

### 5.2 Ficha técnica por paper

Cuando un paper es central, se hace una nota en `bibliografia/notas/` con:

```markdown
# <Nombre del paper o tema>

**Cita completa:** Autor (Año). Título. *Revista*, vol(num), pp. doi:...
**PDF:** `bibliografia/pdfs/Archivo.pdf`
**Páginas leídas:** rango

### Resumen ejecutivo
2-3 frases del aporte.

### Fórmulas / Algoritmos (texto exacto)
Pseudocódigo o ecuaciones literales del paper, no parafraseadas.

### Aplicabilidad a Copernicus-v1
Mapeo concreto: qué banda S2/L8/L9 cubre el rol de qué banda original.

### Limitaciones / Caveats
Lo que el paper dice que NO funciona o requiere supuestos.
```

Patrón seguido en `notas/01_MIROVA_MODVOLC.md` y similares.

### 5.3 Cuándo NO hacer ficha

- Papers leídos solo para contexto general (basta con entrada en archivo temático)
- Papers que se descartaron tras lectura (mover a "Descartados" en archivo temático con motivo)
- Reviews superficiales (1 párrafo en el temático alcanza)

---

## 6. Lecciones aprendidas críticas (no repetir)

1. **`curl/wget` contra editoriales con Akamai (MDPI, Elsevier) devuelve HTML disfrazado de éxito.** Status 200 + contenido HTML. SIEMPRE verificar magic bytes y tamaño post-descarga.

2. **Tamaño es proxy de validez.** PDFs reales de papers: 200 KB – 30 MB. Por debajo casi siempre es landing/paywall.

3. **`Romero2024_SVZ_Review.pdf` de 37 KB sigue en `pdfs/`** — es HTML. Sirve como recordatorio físico de la lección anterior. Pendiente re-bajar desde Andean Geology directo.

4. **Vantor = Maxar Intelligence rebranding (oct-2025).** URLs comerciales antiguas redirigen. Documentar cambios de branding en `imagenes_comerciales_alta_resolucion.md`.

5. **PlanetScope NO tiene SWIR** — bandas BGR+NIR únicamente. No reemplaza S2/Landsat para anomalías térmicas. Solo morfología diaria 3m.

6. **NICFI (Planet Education) NO cubre Chile** — el programa free solo es trópicos. Para 3m en Chile hay que ir por Planet Education & Research directo.

7. **MDPI bloquea bots pero los papers son open access.** No vale la pena pelearse con Akamai: abrir en browser real es 30s vs 30min de debugging.

8. **DOIs sin URL final pueden tardar.** Resolver con `curl -L -I https://doi.org/<doi>` antes de programar descarga.

9. **Nombres de archivo con espacios o caracteres especiales rompen scripts.** Convención `Autor_Año_Tema.pdf` no es opcional.

10. **Conference papers ≠ journal papers.** Cuando existe la versión journal, preferirla siempre (más completa, peer-reviewed).

11. **No bajar todo lo encontrado.** El triaje (Fase 2) existe porque bajar 50 PDFs y leer 5 es peor que bajar 15 PDFs y leer 15.

12. **Subagentes para descargas paralelas masivas.** Máx 2 paralelos contra el mismo dominio (rate limits). Pedir resumen <500 tokens, no volcar contenido en contexto.

13. **Persistir hallazgo *en el momento*.** Si descubrís que un publisher cambió URL, o un autor liberó preprint, anotalo acá inmediatamente — no al final de la sesión.

---

## 7. Contactos y canales útiles

(Mismos de [BIBLIOGRAFIA.md](BIBLIOGRAFIA.md#-contactos-institucionales-sugeridos) — duplicados acá para acceso rápido.)

| Institución | Contacto / canal | Para qué |
|---|---|---|
| **VOLCANOMS UCN** (Antofagasta) | F. Aguilera, J. Layana | Antecedente nacional directo, datasets chilenos |
| **OVDAS-SERNAGEOMIN** (Temuco) | observatorios volcanes Andes Sur | Validación in-situ, alertas oficiales |
| **INGV Italia** | Coppola, Massimetti, Marchese | Autores principales NHI/MIROVA |
| **HIGP Hawaii** | Wright | MODVOLC autor original |
| **University of Bristol** | Biggs, Anantrasirichai | Deep learning sobre Sentinel-1/InSAR |

---

## 8. Workflow recomendado para una nueva ronda bibliográfica

Paso a paso para la próxima vez que se necesite expandir la bibliografía:

1. **Definir pregunta concreta** (ej. "métodos para detectar lagos volcánicos calientes con S2"). Sin pregunta, no hay triaje posible.

2. **Búsqueda en paralelo** (subagentes Explore):
   - Agente 1: Semantic Scholar + Crossref → papers seminales del topic
   - Agente 2: NASA ADS → aplicaciones remote sensing del topic
   - Agente 3: Google Scholar → revisión reciente últimos 3 años
   - Cada agente devuelve top-10 con DOI y abstract resumido (<500 tokens).

3. **Triaje** consolidado en una tabla. Marcar ✅/❌/maybe. Bajar solo ✅.

4. **Descarga** respetando el comportamiento de cada editorial (tabla §4.1). Verificar magic bytes y tamaño cada vez (§4.4).

5. **Conversión** con `markitdown` antes de leer.

6. **Ficha técnica** en `notas/` solo para los 3-5 papers centrales del lote. El resto va como entrada en el archivo temático correspondiente.

7. **Actualizar índices:**
   - `BIBLIOGRAFIA.md` → tabla maestra y PDFs descargados
   - Archivo temático correspondiente
   - Si hay nueva lección de búsqueda/descarga → actualizar **este** documento (§6)

8. **Commit con mensaje específico**: `docs(bibliografia): agregar N papers sobre <topic>` + lista de archivos.

---

## 9. Cómo mantener este documento

Este archivo es **vivo**. Cualquier sesión que aprenda algo nuevo sobre búsqueda/descarga (publisher cambió de plataforma, nueva API útil, nueva fuente, error nuevo) debe:

1. Agregar línea a la lección correspondiente en §6, o crear nueva lección.
2. Si es una fuente: agregar a tabla §2.1 o §4.1.
3. Si es un comando: agregar a §4.2.
4. Commit con mensaje `docs(bibliografia): actualizar metodología — <qué se aprendió>`.

**No editar para "limpieza estética"** sin razón técnica. La densidad de información importa más que la prolijidad.
