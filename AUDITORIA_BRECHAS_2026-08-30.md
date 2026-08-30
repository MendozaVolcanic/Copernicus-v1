# Auditoría de brechas — Copernicus-v1 y Landsat-v1

**Fecha:** 30 de agosto de 2026 · **Método:** [`PLANTILLA_CAZA_DE_BRECHAS.md`](../../../PLANTILLA_CAZA_DE_BRECHAS.md),
tres lentes + variante D · **Costo:** 0 Processing Units (no se descargó ninguna escena nueva)

---

## Lo que encontré, en una frase

**El dashboard de detección de cambios lleva semanas diciéndole al turno que 34 de
51 volcanes están en ALERTA, y su medición de "cambio morfológico" tiene mediana
67 % con veinte casos en 100 % — está midiendo nieve, no morfología.** Debajo de
eso hay otras nueve brechas confirmadas, siete de ellas del mismo género que las
tres semillas: fallos que ninguna revisión de código podía ver porque no viven en
el código.

Segunda en importancia, y del tipo exacto de la semilla 3: **la corrección de
tonalidad RGB que Copernicus recibió el 18-ago nunca se propagó a Landsat**, así
que el mismo volcán el mismo día se ve 12 % blanco en un dashboard y 74 % en el
otro. Y tercera, de proceso: **la única alarma automática de Landsat no podía
dispararse**, porque el script que vigila convertía toda falla del API en "hoy no
hubo escena".

---

## Inventario de cobertura — qué miró cada auditoría previa

La plantilla pide esto antes de buscar nada, porque el modo de falla de la
auditoría repetida es que cada pasada recorre lo fácil y ninguna llega al fondo.

| Auditoría | Objeto | Lente | Zona ciega que dejó |
|---|---|---|---|
| `AUDITORIA_PYTHON_2026-05-17.md` | scripts `.py` | artefacto (fuente) | ninguna salida renderizada |
| `AUDITORIA_INFRA_2026-05-17.md` | workflows | proceso | no comparó run verde vs dato producido |
| `AUDITORIA_FRONTEND_2026-05-17.md` | HTML/JS | artefacto (fuente) | no cargó el dashboard servido |
| `AUDITORIA_2026-06-08.md` | general | mixta | — |
| `AUDITORIA_CALIDAD_IMAGENES.md` (17-ago) | **PNG publicados** | artefacto + 1 de proceso | **sólo el camino SWIR**; nunca abrió un `*_RGB.png` ni un `*_THERMAL.png` |

**Zonas que no había mirado ninguna, y que son el terreno de esta pasada:**
el camino RGB medido con criterio numérico · el camino THERMAL · la
**divergencia entre los dos repos** (nadie la había auditado nunca) · el
comportamiento del dashboard **servido** · la calibración de la detección de
cambios contra su propia tasa base.

---

# BRECHAS

Ordenadas por severidad. Cada una: lente y eje · evidencia reproducible · por qué
se escapó · cierre.

---

## B1 · La detección de cambios dejó de discriminar — **severidad crítica**

**Lente:** artefacto + proceso · **Ejes:** A1 (dimensión colapsada) · P5 (medición
equivocada) · A9 (factor humano: fatiga de alerta)

El JSON publicado hoy trae **34 ALERTA · 10 ATENCION · 7 NORMAL** sobre 51
entidades. Con dos tercios de los volcanes de Chile en rojo, el estado dejó de
cumplir su única función: ordenar cuál merece segunda mirada.

```bash
curl -s https://mendozavolcanic.github.io/Copernicus-v1/change_detection/change_results.json \
  | python -c "import json,sys; print(json.load(sys.stdin)['resumen'])"
# {'NORMAL': 7, 'ATENCION': 10, 'ALERTA': 34, 'NUBLADO': 0, 'SIN_DATOS': 0, 'ERROR': 0}
```

El delator no es el conteo sino la magnitud. `cambio_morfologico_pct` tiene
**mediana 67,0 %**, con **20 mediciones en 100,0 %** — Corcovado 100,0 · Calbuco
99,9 · Huequi 99,4 · Nevado de Longaví 100,0 (230.400 px, la escena entera).

Un volcán no cambia el 100 % de su superficie entre dos pasadas separadas por
días. Lo que se está midiendo ahí es nieve fresca, nube o ángulo solar de
invierno. **El instrumento está vivo y midiendo otra magnitud** — regla dura 8b.
Y `cambio_termico_pct` tiene mediana 3,13 % contra un umbral de ALERTA de >3 %:
media población cruza el umbral por construcción.

**Por qué se escapó:** todas las corridas salieron en verde. Verde certifica que
el script corrió, no que la proporción de alertas tenga sentido. **Nada comparaba
la tanda contra su propia tasa base.** Y `CLAUDE.md` seguía describiendo el estado
del 10-may: *"6 ATENCION · 0 ALERTA"*.

**Cierre — mitigación (aplicada):** `change_analysis.py` escribe un bloque
`diagnostico` con `alerta_pct`, la mediana morfológica y `calibracion_sospechosa`;
grita en el log y el dashboard pinta *"usa esta tabla para mirar, no para
priorizar"*. **Cierre de fondo (de Nicolás):** revisar 5–10 casos `override`
contra la escena cruda y decidir si se recalibra. Disparador: `alerta_pct > 25 %`
sostenido dos días.

---

## B2 · El umbral documentado ya no es el que decide — **alta**

**Lente:** proceso · **Eje:** P11 (trazabilidad)

`CLAUDE.md` documenta *"z>3.0 AND pct>3% → ALERTA"*. Pero el ensemble toma el
**peor de tres** (z-score, NHI, Mahalanobis) y **21 de las 34 ALERTA** llevan
`[Mahalanobis override] ... | Z-score era ATENCION` o `... era NORMAL`. Ese
mecanismo no está documentado en ningún archivo del repo.

```
ALERTA: 34 | con [Mahalanobis override] en el detalle: 24 | override Y alerta: 21
```

El código no cambió: lo que cambió fue que el histórico cruzó en silencio el
umbral `stack_historico.shape[0] >= 5` que activa Mahalanobis. `change_history.json`
fecha el vuelco: todo NORMAL hasta el 2026-08-10, escalado persistente desde el
2026-08-12.

**Por qué se escapó:** el cambio de comportamiento no vino de un commit sino de
que los datos acumulados cruzaron un umbral. `git log` no lo puede mostrar.

**Cierre:** documentado en `CLAUDE.md` en este mismo cambio. De fondo, el
diagnóstico de B1 lo hace visible cada corrida.

---

## B3 · Landsat nunca recibió la corrección de tonalidad — **alta**

**Lente:** proceso · **Eje:** P10 (duplicación y divergencia) — **es la semilla 3 otra vez**

Copernicus pasó a gamma sRGB el 18-ago tras medir que el realce lineal quemaba la
escena. Landsat sigue con `clip(reflectancia × 3.5, 0, 1)` — exactamente el
enfoque que Copernicus ya descartó. Medido sobre los PNG publicados, mismo volcán,
mismo día:

| Volcán · fecha | Copernicus (sRGB) | Landsat (lineal 3.5) |
|---|---|---|
| Villarrica 2026-08-22 | 12,2 % blanco · 5,63 bits | **73,9 % blanco · 2,91 bits** |
| Llaima 2026-08-22 | 14,4 % blanco · 5,81 bits | **87,1 % blanco · 1,52 bits** |
| Lascar (±2 d, sin nieve) | 3,4 % blanco · 7,41 bits | 46,6 % blanco · 5,27 bits |

Lascar está en el altiplano árido y sin nieve: descarta que sea sólo efecto de la
nieve. Peor caso medido por volcán: **Nevados de Chillán 95,4 % blanco, entropía
0,57 bits.**

Con el filtro de nubosidad puesto (sólo escenas con <20 % de nube, donde el blanco
es responsabilidad del render y no del cielo), el instrumento extendido cuenta
**58 casos de severidad alta en Landsat** y **64 en Sentinel-2** — sí, Sentinel-2
sigue teniendo 64 **después** del gamma: la curva nueva no resuelve nieve y hielo.

**Por qué se escapó:** `auditoria_imagenes.py --landsat` compara
`*_ThermalFalseColor.png` contra `*_SWIR.png`. **Nunca abrió un `*_RGB.png` en
ninguno de los dos repos.** Era estructuralmente ciego al defecto más extendido, y
de magnitud mayor que lo que sí medía.

**Cierre — mitigación (aplicada):** el instrumento ahora mide RGB en los dos
repos, con umbral numérico y filtro de nubosidad, y corre en CI.
⏸️ **Cierre de fondo: NO lo apliqué.** Cambiar la curva de Landsat toca la
tonalidad de una serie histórica, y la comparabilidad fotométrica de la serie RGB
es una decisión que está en pausa. Ver *Decisiones para Nicolás* §1.

---

## B4 · Un tercio de los frames de Landsat es un rectángulo de un solo color — **alta**

**Lente:** artefacto · **Ejes:** A1 (dimensión colapsada) · A6 (asimetría de consecuencias)

De los 592 PNG RGB de Landsat en disco, **209 (35,3 %) tienen entropía < 0,1**: un
único tono en toda la imagen. En Sentinel-2, 111 de 915 (12,1 %). Villarrica: 11
de 16.

La prueba de que no es "la escena no servía" y punto — Llaima 2026-07-21, misma
escena, mismo instante:

```
RGB      800x800 colores_unicos=     1 ej=[255, 255, 255] entropia=-0.00 kB=2
SWIR     800x800 colores_unicos=  2949 ej=[77, 62, 255]   entropia= 6.93 kB=315
THERMAL  800x800 colores_unicos=     1 ej=[0, 0, 255]     entropia=-0.00 kB=2
```

El SWIR de esa misma escena tiene textura de sobra. El RGB y el THERMAL salen
como un rectángulo blanco y uno azul, de 2 kB cada uno.

**Honestidad sobre el alcance:** con el filtro de nubosidad puesto, sólo **2 de
esos 196 frames planos de Landsat ocurrieron con cielo despejado**. Casi todos son
escenas genuinamente tapadas. **La brecha entonces no es que el render destruya
datos útiles a gran escala — es que se publican igual, sin ninguna marca.** El
operador que abre Villarrica ve un cuadrado blanco y no tiene cómo distinguir
"nublado" de "sin dato" de "bug", que es la asimetría A6: el falso negativo cuesta
muchísimo más que el falso positivo en turno volcanológico.

**Cierre — mitigación (aplicada):** el instrumento los cuenta y los clasifica
(`RGB_PLANA`), separando los que ocurrieron con cielo despejado (severidad alta)
de los genuinamente tapados (baja). **De fondo:** marcar el frame en el dashboard
y excluirlo del timelapse. No lo implementé — ver *Lo que decidí no hacer*.

---

## B5 · La única alarma de Landsat no podía dispararse — **alta**

**Lente:** proceso · **Ejes:** P9 (sin modo degradado) · B4 (fallo silencioso)

`alerta_cron_caido.yml` dice en su propio comentario que existe para cazar
*"credenciales M2M vencidas, USGS caído, timeout"*. No podía cazar ninguna de las
tres: sólo dispara con `conclusion == 'failure'`, y `scripts/watcher_m2m.py`
convertía **cualquier** excepción del API en:

```python
except Exception as e:
    set_output("has_new", "false")
    return          # exit 0, job verde
```

Es decir, la misma salida exacta que "hoy no hubo escena nueva". **Las dos ramas
del control no eran separables, así que el control era decorativo.**

En el registro se ve:

```bash
gh api repos/MendozaVolcanic/Landsat-v1/issues?labels=cron-failure   # -> []
# 300/300 runs recientes en 'success' (16 días)
```

**Por qué se escapó:** un `try/except` alrededor de una llamada de red se lee como
resiliencia razonable. Nadie probó nunca inyectando un token vencido.

**Cierre (aplicado):** reintentos para absorber lo transitorio; si igual falla,
`api_error=true` y `SystemExit` — el job va a rojo y la alarma dispara. "Sin
escenas nuevas" sigue saliendo verde. Verificado en las dos ramas.

---

## B6 · El botón "Cambios" de Landsat estuvo muerto desde siempre — **alta**

**Lente:** oportunidad convertida en brecha · **Ejes:** O1 (activo infrautilizado) · P10

`docs/change_detection.html` hacía `fetch('change_detection/change_results.json')`
**dentro de su propio repo**. Ese archivo no existe ni existió nunca, así que la
página mostraba desde siempre *"No se encontró change_results.json para
Landsat-v1"*.

Mientras tanto la respuesta ya estaba calculada un repo al lado:
`change_analysis.py` de Copernicus hace sparse-checkout de `Landsat-v1/docs/landsat`
en su cron de las 22:30 y publica, para las 51 entidades, un bloque
`por_sensor.landsat` con estado, NHI, z-score, Mahalanobis y VRP.

**Por qué se escapó:** cada repo se auditó por separado. Ninguna de las cinco
auditorías previas cruzó los dos.

**Cierre (aplicado):** la página lee el JSON publicado por Copernicus. Además el
panel de detalle muestra **qué dice Sentinel-2 del mismo volcán** y si los dos
sensores coinciden, confirman o discrepan — el único punto del sistema donde los
dos sensores se leen juntos.

---

## B7 · El GIF SWIR de Landsat borraba las anomalías térmicas — **media**

**Lente:** proceso · **Eje:** P10 (el fix se aplicó en un repo y no en el hermano)

`gif_optimizer.py` de Copernicus cubre `'thermal'`, `'falso'` y `'swir'`. Al
portarlo a Landsat la condición se simplificó a `tipo.upper() == 'THERMAL'`, así
que el GIF de SWIR —el composite de anomalías térmicas intensas de Landsat— caía
en la rama ADAPTIVE.

Reproducido sobre `docs/landsat/Descabezado Grande/2026-06-28_SWIR.png` (5 px rojos):

```
   64 colores  ADAPTIVE=  0   MAXCOVERAGE=  0
   96 colores  ADAPTIVE=  0   MAXCOVERAGE=  7
  128 colores  ADAPTIVE=  0   MAXCOVERAGE=  5
  256 colores  ADAPTIVE=  0   MAXCOVERAGE=  5
```

Y de punta a punta, armando el GIF con el código real: **0 de 8 px rojos
sobreviven antes; 8 de 8 después.**

**Alcance medido honestamente:** sólo 2 de 592 PNG SWIR del archivo Landsat tienen
píxeles rojos. Pero ése es exactamente el caso para el que existe MAXCOVERAGE —
el outlier raro y crítico, cuya frecuencia observada es baja porque el mecanismo
que lo borraba corría en silencio.

**Cierre (aplicado):** `tipo.upper() in ('THERMAL', 'SWIR')`.

---

## B8 · El KML seguía con Chillán en las coordenadas de Antuco — **media**

**Lente:** proceso · **Eje:** P10 — **la semilla 3, viva en un tercer archivo**

```
Nevados de Chillan   KML(-37.41096,-71.35231)  config(-36.87000,-71.38000)   60.20 km
pares distintos a <5 km dentro del KML:  Antuco <-> Nevados de Chillan  1.31 km
```

Corregido en `config_sentinel2.py` y en `docs/volcanes.js` hace meses; intacto en
el KML.

**Por qué se escapó:** el archivo es huérfano — ningún `.py`, `.html` ni `.yml`
del repo lo lee. Quedó fuera del camino de cualquier corrección. Un archivo que
nadie ejecuta no es inofensivo: es una referencia envenenada esperando a que
alguien lo abra en QGIS.

**Cierre (aplicado):** `scripts/generar_kml.py` lo deriva de `config_sentinel2.py`,
que pasa a ser el único dueño de las coordenadas, con un `--check` que falla si
divergen. Verificado: 43 placemarks, diferencia máxima contra el config 0,0006 km,
ningún par de volcanes distintos a menos de 5 km.

---

## B9 · Los dos repos apuntan a puntos distintos del mismo volcán — **media**

**Lente:** proceso · **Eje:** P10

Seis volcanes tienen centroides desincronizados entre `config_sentinel2.py` y
`config_landsat.py`, y los buffers también difieren:

| Volcán | Distancia | buffer COP | buffer LAND | desplazamiento / buffer |
|---|---|---|---|---|
| Mocho-Choshuenco | 2,35 km | 6,0 | 5,0 | 0,47× |
| Lanín | 2,29 km | 4,0 | 4,5 | 0,51× |
| Antillanca - Casablanca | 1,90 km | 5,5 | 5,5 | 0,35× |
| **Isluga** | 1,82 km | **1,0** | **3,5** | 0,52× |
| Melimoyu | 1,35 km | 7,0 | 7,0 | 0,19× |
| Antuco | 1,25 km | 3,0 | 3,0 | 0,42× |

En Isluga, Lanín y Mocho el desplazamiento es **medio radio de recorte**: los dos
dashboards muestran terreno parcialmente distinto para el mismo volcán. En Isluga
además el encuadre es 3,5× más ancho en Landsat. Comparar los dos sensores a ojo
para esos seis volcanes compara cosas distintas.

Los mismos seis valores estaban en el KML, o sea que la revisión de centroides se
hizo **sólo en Copernicus** y no se propagó ni a Landsat ni al KML.

**No lo corregí:** mover el centroide cambia el encuadre de la serie histórica de
Landsat para esos seis volcanes. Ver *Decisiones para Nicolás* §3.

---

## B10 · Nevados de Chillán quedó con un tercio de la cobertura de sus vecinos — **media**

**Lente:** proceso · **Ejes:** P1 (sin bucle de retroalimentación) · A4

Secuela no cerrada de la cuarentena de imágenes de Antuco. Landsat publicado hoy:

```
Nevados de Chillan   5 fechas: 07-21, 07-29, 08-06, 08-14, 08-22
Antuco              14 fechas: 07-05, 07-06, 07-13, 07-14, 07-21, 07-22, ...
Callaqui            14   Copahue 14   Lonquimay 14
```

Los vecinos tienen **pares** de días consecutivos porque los cubren dos paths
WRS-2 (232 y 233); Chillán sólo trae los del **path 233**. Su `metadata.csv` sólo
tiene escenas `..._233086_...`, mientras Antuco alterna `232086` y `233086` — y
está casi en la misma longitud.

Y de esas 5 fechas, **2 tienen `cloud_cover` 100**: quedan 3 miradas útiles en 45
días para uno de los 14 volcanes más peligrosos de Chile. El dashboard no dice
nada de esto.

**Cierre:** pendiente de diagnóstico — hay que determinar si es geometría real o
residuo del borrado. No lo cerré: exige descargas de verificación. Ver *Decisiones*.

---

## B11 · Ninguno de los dos dashboards leía la URL — **media**

**Lente:** artefacto + proceso · **Ejes:** A2 (tarea equivocada) · P4 (traspaso con pérdida)

```bash
grep -o "URLSearchParams\|location.search\|location.hash" cop_index.html land_index.html
# (vacío en los dos)
```

Consecuencias en turno: no había forma de mandarle a alguien *"mira Villarrica"*
sin explicarle los clics; recargar perdía la selección; y el botón entre los dos
dashboards abría el hermano en su volcán por defecto, tirando el contexto.

**Cierre (aplicado):** `?volcan=` en los dos, URL sincronizada con lo que se mira,
y el enlace cruzado lleva el volcán actual.

---

## B12 · La columna `satelite` de Landsat dejó de decir qué satélite es — **baja-media**

**Lente:** artefacto · **Ejes:** B10 (frontera externa) · A5 (supuesto no declarado)

En `metadata.csv` de Landsat, las filas viejas traen `landsat-8` / `landsat-9`
(17 filas en Antuco); las nuevas traen el scene ID completo, duplicando la columna
`scene_id` (50 filas). El dashboard muestra ese campo tal cual, así que donde
debería decir "Landsat 9" muestra `LC09_L1TP_232086_20260823_20260823_02_T1`.

Además, **42 de 43 volcanes tienen ~20 fechas con filas L1 y L2 para la misma
fecha** (809 filas L1 y 1.669 L2 sobre 2.478). El PNG se sobrescribe, así que los
frames más recientes de cada serie son L1 (reflectancia TOA, colección Real-Time,
no definitiva) y los viejos son L2 (reflectancia de superficie). El dashboard sí
marca "L1 provisional" en la UI — eso está bien resuelto —, pero el timelapse no,
y las dos radiometrías no son comparables entre sí.

---

## Una brecha que no cae en ninguno de los 27 ejes

*(Regla dura 7. Si sólo devuelvo hallazgos que encajan en los ejes, no sé si
descubrí algo o si el instrumento se autoconfirmó.)*

**Los dos repos comparten datos pero no comparten instrumento, y eso hace que
cada corrección tenga que descubrirse dos veces.**

No es P10 (duplicación) —eso describe el síntoma, no la causa—, ni P3 (dueño
ausente): Nicolás es dueño de los dos. Es una propiedad estructural de la
topología: `change_analysis.py` **lee** Landsat, `auditoria_imagenes.py` **sabe
leer** Landsat, `gif_optimizer.py` es casi el mismo archivo en los dos lados. El
flujo de datos es bidireccional, pero **el flujo de correcciones es unidireccional
y manual**: alguien tiene que acordarse de copiar. Las cuatro divergencias de esta
auditoría (B3 tonalidad, B7 MAXCOVERAGE, B8 KML, B9 coordenadas) son cuatro
instancias del mismo hecho, y las cuatro se descubrieron por accidente meses
después.

**El cierre no es un fix**: es decidir si los dos repos comparten un módulo
(`gif_optimizer`, `gif_cache`, la tabla de volcanes) o si se acepta la duplicación
y se instala un chequeo cruzado que falle cuando divergen. Hoy no hay ninguna de
las dos, y por eso la semilla 3 sigue apareciendo bajo formas nuevas.

---

# OPORTUNIDADES

*Lista aparte: no compiten con las brechas.*

| # | Eje | Oportunidad | Evidencia de que el activo ya existe |
|---|---|---|---|
| O1 | activo infrautilizado | **2.098 alertas en `docs/alertas/*.md`** (93 volcanes, desde el 31-mar) sin ninguna página que las liste | `grep -rl "alertas/" docs/*.html` → sin resultados |
| O2 | activo infrautilizado | El **NHI y el VRP en MW ya se calculan a diario para Landsat** y hasta hoy no se mostraban en su dashboard | `por_sensor.landsat` en `change_results.json` (cerrado en B6) |
| O3 | activo infrautilizado | `landsat_downloader.py` convierte B10 a Celsius y **descarta el array**: ni `temp_max_c` ni cobertura válida quedan en `metadata.csv` | el CSV no tiene esas columnas |
| O4 | barato de medir | **12 escenas declaradas ≥90 % de nube tienen entropía >4** (Hudson 2026-08-15 declara 92 % y mide 7,66 bits): el `cloud_cover` es de la escena Landsat completa (185×180 km), no del recorte de 24 km | correlación nube↔entropía = **−0,565**: útil pero grueso |
| O5 | automatizable | La fracción ciega y el % de blanco puro **ya se calculan**; podrían viajar en el metadata y mostrarse junto a la imagen | `auditoria_imagenes.py` los produce |
| O6 | reutilizable | `gif_cache.py` es casi idéntico en los dos repos; `gif_optimizer.py` y `ppt_generator.py` ya divergieron | diff línea a línea |
| O7 | activo infrautilizado | El archivo M2M profundo (2013+) **no cuesta nada** y no se usa para línea base: `DIAS_ATRAS = DIAS_RETENCION = 60` | `config_landsat.py:82` |
| O8 | subproducto | `change_results.json` no está declarado como salida consumible en `MAPA_WORKSPACE.md`; VRP Chile podría validarse contra él | — |

**Sobre O4, con honestidad:** mi primera hipótesis era que la nubosidad publicada
*miente*. La medición la refuta: sólo **3 de 136** escenas declaradas con ≤25 % de
nube salen planas. El número no miente, es **grueso** — describe una escena 60
veces más grande que el recorte. El valor está en el otro sentido: 12 miradas
despejadas a volcanes que hoy se descartan por un número que no las describe.

---

# LAS 20 IDEAS DE MEJORA

Ancla (a) = mirar muchos volcanes rápido · Ancla (b) = comparar un volcán consigo
mismo en el tiempo · **[×]** = hace que los dos sensores se lean juntos, sube de
prioridad.

## Operacional

| # | Idea | Dolor que resuelve | Esfuerzo | ¿En el otro repo? |
|---|---|---|---|---|
| 1 **[×]** | Badge ALERTA/ATENCION de `change_results.json` en cada tarjeta de Multi-Volcán y de "14 Riesgosos", con el **estado de los dos sensores** | (a) el juicio ya calculado no llega a la grilla donde se escanea | 0,5–1 d | El dato existe; ningún grid lo muestra |
| 2 | `docs/alertas.html`: línea de tiempo navegable de los 2.098 `.md` por volcán | (b) el historial es invisible fuera del repo crudo | 0,5–1 d | No existe en ninguno |
| 3 **[×]** | Ordenar la cola de `revision_turno.html` por estado de cambio y prellenar el chip "Anomalía" | (a) el prototipo ya cruza los dos repos pero ignora el análisis hecho | 0,5 d | N/A |
| 4 | Marcar en el dashboard los frames planos (`RGB_PLANA`) como "escena sin información" en vez de mostrar un cuadro blanco | (a) hoy un blanco no se distingue de "sin novedad" | 0,5 d | Mismo problema en los dos |
| 5 | Activar `NASA_FIRMS_API_KEY` (falta en `gh secret list`): el código de cruce con VIIRS ya está escrito y apagado | detección térmica independiente, gratis | 15 min | Landsat no tiene FIRMS |

## UX

| # | Idea | Dolor | Esfuerzo | ¿En el otro repo? |
|---|---|---|---|---|
| 6 **[×]** | Vista Individual con **Sentinel-2 y Landsat del mismo volcán lado a lado**, misma fecha o la más cercana | ancla (a) y (b) a la vez; hoy exige dos pestañas y comparar de memoria | 1–2 d | No existe en ninguno |
| 7 | "Copiar enlace de esta vista" (volcán + fecha + composite) | (a) pasar un caso a otra persona sin capturas | 2 h (la base ya está hecha) | Base aplicada en los dos |
| 8 | Atajos de teclado: ←/→ entre fechas, 1/2/3 entre composites, j/k entre volcanes | (a) escanear 43 volcanes a golpe de mouse es lento | 0,5 d | No |
| 9 | Antigüedad de la imagen coloreada ("hace 8 días" en ámbar sobre 7) en vez de sólo la fecha | (a) hoy hay que restar mentalmente | 3 h | No |
| 10 | Enlace o `mailto` de "reportar esta imagen" en `ayuda.html` | P1: hoy no hay ninguna ruta de vuelta del operador al sistema | 1 h | No existe en ninguno |

## Visualización

| # | Idea | Dolor | Esfuerzo | ¿En el otro repo? |
|---|---|---|---|---|
| 11 **[×]** | Barra de color con °C bajo el panel THERMAL | (a)(b) hoy el THERMAL es color sin escala; la tabla existe pero vive en `ayuda.html` | 3–4 h | Falta en los dos |
| 12 | Mostrar el % de nube como texto sobre cada miniatura del grid | (a) hoy la nube hay que *verla*, no leerla | 2–3 h | Mismo problema |
| 13 **[×]** | Sparkline de 60 días del z-score térmico junto a la miniatura | (b) la persistencia dice más que un punto aislado; `consecutive_elevated` ya se calcula | 1 d | Dato listo, sin usar |
| 14 | Marcar en el timelapse los frames L1 (provisionales) con un borde | (b) la serie mezcla dos radiometrías sin avisar en el GIF | 3 h | La UI ya lo marca; el GIF no |
| 15 | Regenerar timelapses en **WebP animado**: 278 MB → ~60–90 MB sin bajar resolución | carga del dashboard; además elimina la cuantización a 256 colores que obligó a MAXCOVERAGE | 1 d | Aplica a los dos |

## Investigación

| # | Idea | Dolor | Esfuerzo | ¿En el otro repo? |
|---|---|---|---|---|
| 16 | Calcular NHI de los floats crudos en `landsat_downloader.py`, no decodificando el PNG comprimido | (b) precisión de la serie temporal; hoy el NHI de Landsat se reconstruye desde un PNG | 1 d | La fórmula ya existe en Copernicus |
| 17 | Persistir `temp_max_c` y `cobertura_valida_pct` en `metadata.csv` (ya se calculan y se tiran) | (b) un número duro por fecha en vez de un color | 2 h | No |
| 18 | Botón "misma fecha, 5 años atrás" bajo demanda contra el archivo M2M (gratis) | (b) comparación interanual, hoy imposible con ventana de 60 días | 1 d | No existe en ninguno |

## Accesibilidad

| # | Idea | Dolor | Esfuerzo | ¿En el otro repo? |
|---|---|---|---|---|
| 19 | Los estados no dependen sólo del color: agregar forma o texto al badge ALERTA/ATENCION/NORMAL | ~8 % de los hombres tiene deficiencia rojo-verde; la sala se usa en turno compartido | 3 h | Falta en los dos |
| 20 | `aria-label` y contraste AA en los chips de estado y los botones de composite | sala con luz alta, lector de pantalla | 1 d | Sin auditar en ninguno |

## Las tres que parecen brillantes y son trampa

1. **Change detection propio para Landsat.** Reimplementaría ~1.700 líneas que ya
   corren a diario y ya cubren Landsat. La solución real era cambiar una URL (B6).
2. **Autoencoder / BIT-Transformer para detección de cambios.** Semanas de trabajo,
   caja negra, y dispara el requisito de explicación adicional de la Resolución
   CPLT N°372 — para reemplazar algo cuyo problema real hoy es de calibración, no
   de potencia del modelo.
3. **Guardar los GeoTIFF crudos "por si sirven".** Revierte el diseño de
   window-read barato y repite el crecimiento de repo que Copernicus ya sufrió.
   Lo que vale guardar son los escalares derivados (ideas 16 y 17), no el ráster.

---

# LO QUE DECIDÍ NO HACER, Y POR QUÉ

| Qué | Por qué no |
|---|---|
| **Cambiar la curva RGB de Landsat** | Toca la tonalidad de una serie histórica. La comparabilidad fotométrica de la serie RGB está explícitamente en pausa como decisión tuya, y ya cambió de curva dos veces. Levantado, no resuelto. |
| **Recalibrar los umbrales de change detection** | Es una decisión científica que exige contrastar contra escenas crudas, no un cambio de software. Instalé el aviso, no la corrección. |
| **Portar la retención con orphan reset a Landsat** | Reescribe historia: destructivo e irreversible. Landsat pesa 4,31 GB y crece, así que hay que hacerlo — pero con tu visto bueno. |
| **Mover los centroides de Landsat** | Cambia el encuadre de la serie histórica de seis volcanes. La decisión depende de si la revisión de centroides del 4-jun fue la autoritativa. |
| **Re-descargar el historial de Nevados de Chillán** | Antes hay que saber si la falta del path 232 es geometría o residuo del borrado. Diagnosticar primero, descargar después. |
| **Backfill de las fechas quemadas** | Ya estaba degradado a opcional y medido: se purga solo el 2026-10-01. Gastar ~950 renders no se justifica salvo que necesites mirar julio-agosto con la curva nueva antes de octubre. |
| **Tocar `docs/revision_turno.html` y `ESPEC_REVISION_TURNO_OVDAS.md`** | Son trabajo sin commitear de otra sesión. Todos mis commits van con ruta explícita. |

---

# DECISIONES PARA NICOLÁS

**1 · ¿La comparabilidad fotométrica de la serie RGB es un requisito?** ⏸️ *(en pausa
por decisión tuya; la auditoría la tocó, así que la levanto y espero)*
Si lo es, la curva de Landsat no se toca y hay que documentar la discontinuidad
del 18-ago en Copernicus. Si no lo es, Landsat debería recibir el gamma sRGB: hoy
publica escenas con 87 % de blanco donde Copernicus publica 14 %.
**Mi recomendación:** no es un requisito, y conviene decirlo por escrito. La serie
ya cambió de curva dos veces sin que nadie lo notara, lo que sugiere que nadie la
estaba usando fotométricamente. Pero es tu llamada.

**2 · Retención de repositorio en Landsat.** Pesa 4,31 GB y crece 2×/día sin freno
(la retención de 60 días borra el working tree, no la historia). Copernicus bajó
de 3,01 a 0,84 GB con un orphan reset. Es destructivo — pide tu autorización
explícita. **Recomiendo hacerlo**, con la advertencia conocida: el reset rompe
`git log -S`.

**3 · Centroides desincronizados (6 volcanes, hasta 2,35 km).** Alinear Landsat a
Copernicus cambia el encuadre de esas seis series. **Recomiendo alinear igual**,
aceptando el corte, y anotar la fecha del cambio en el `metadata.csv` — dos
dashboards mirando terreno distinto para el mismo volcán es peor que un corte
documentado.

**4 · Nevados de Chillán.** ¿Diagnostico por qué falta el path 232? Son 2–3
descargas M2M, gratis.

---

## Cómo se protege esta auditoría de sí misma

- Todos los números por volcán salen de agrupar **por volcán**, nunca por fecha: el
  filtro de nubosidad selecciona volcanes distintos cada día y los del norte no
  tienen nieve, así que promediar por fecha inventa patrones.
- El instrumento extendido corre **9 controles positivos** antes de reportar, tres
  de ellos nuevos y con ramas separables: blanco total → PLANA; terreno con
  textura → nada; medio quemado por nieve → blanco alto **pero entropía alta**.
- Dos hipótesis mías murieron al medirlas y quedan escritas: *"la nubosidad
  publicada miente"* (falso: correlación −0,565, sólo 3 casos de 136) y *"el
  realce está borrando escenas útiles a gran escala"* (falso: sólo 2 de 196
  frames planos ocurrieron con cielo despejado).
- El checkout local de Landsat estaba 13 días atrasado. Todo lo que afirma
  frescura se midió contra el remote (`gh api` / `raw.githubusercontent.com`).

*Ejes recorridos sin hallazgo nuevo: P2 (punto de inserción), P3 (dueño), P6
(cadencia del cron: correcta contra la revisita real), P7 (fricción), A3
(conocimiento tácito — requiere elicitación, ver abajo), A10 (benchmark externo).
La lista de volcanes de Landsat sí está sincronizada entre `config_landsat.py`,
`VOLCANES_DATA` y el dropdown de `ppt_individual.yml`. Los 43 nombres servidos
coinciden carácter por carácter entre los dos JSON. Todos los enlaces de los dos
dashboards resuelven 200.*

**Lo que esta auditoría no hizo:** la fase de elicitación. La plantilla dice que
es la de mayor rendimiento y la que más se omite. Las preguntas que faltan
hacerle al turno están en la plantilla §3 — sobre todo *"¿qué parte del
procedimiento te saltas cuando andas apurado?"* y *"¿cómo te enteras de que algo
salió mal?"*.
