# Auditoría de calidad de imágenes — Copernicus-v1 y Landsat-v1

**Fecha:** 17 de agosto de 2026 · **Objeto auditado:** las 3.457 imágenes en falso color SWIR
publicadas en el dashboard (2.865 Sentinel-2 + 592 Landsat 8/9) · **Instrumento:**
[`auditoria_imagenes.py`](auditoria_imagenes.py) · **Costo:** 0 Processing Units (lee sólo PNG en disco)

Instanciación de [`PLANTILLA_CAZA_DE_BRECHAS.md`](../../../PLANTILLA_CAZA_DE_BRECHAS.md),
variante D (bugs latentes), sobre **la salida renderizada** — el tercer modo de verificación.

---

## Por qué esta auditoría mira los PNG y no el código

El bug que la originó **no existe en el código**. El evalscript de
[`config_sentinel2.py`](config_sentinel2.py) es correcto, la compresión es lossless y la selección
de escena funciona. El defecto vivía en los píxeles de un archivo guardado. Ninguna revisión de
fuente podía verlo, y de hecho ninguna lo vio en un mes.

> Regla de la plantilla: *«leer el código fuente no prueba nada sobre lo que sale renderizado»*.
> Aplica literalmente acá.

---

## Hallazgos confirmados

### B1 · Anomalía térmica borrada en el archivo publicado — **confirmado, reparado**

**Lente:** artefacto · **Eje:** B4 (fallo silencioso) · **Severidad si ocurre:** alta

Villarrica 2026-07-03 se publicó con el canal SWIR topado en **79/255** y la anomalía térmica
ausente. La escena sí la tenía: al re-descargarla con el **mismo evalscript y la misma ganancia**,
aparecieron 176 píxeles rojos y R max 255. Afectó a `ThermalFalseColor` y `SWIR_B8A` a la vez.

**Reproducción:** comparar el PNG guardado contra un re-render de la escena → diferencia media de
sólo 2,4/255 en el resto de la imagen, pero canal rojo truncado.

**Descartado con evidencia** (para que nadie vuelva a recorrerlo): la ganancia del evalscript · la
compresión (`save_compressed` es lossless) · `mosaickingOrder` (`mostRecent` y `leastCC` idénticos)
· que hubiera dos satélites (S2B no cubre Villarrica: 0 % de píxeles válidos).

**Causa raíz: no determinada.** Con el repo en shallow clone no hay historial para reconstruirla. La
hipótesis consistente es una descarga sobre un producto aún incompleto — S2A se publicó 8 h después
de S2B, y el cron corre 2×día. **No está cerrada.**

**Estado:** los dos PNG reparados en disco, sin commitear. **Alcance real: 1 caso confirmado de 4
verificados** — no es sistemático.

---

### B2 · Nieve y lava se pintan del mismo color — **confirmado, abierto**

**Lente:** artefacto · **Eje:** A1 (dimensión colapsada) · **Severidad:** alta · **Frecuencia:** constante

Éste es el problema de "imágenes quemadas", y es más grave que un asunto estético.

Lo que distingue físicamente una roca caliente de la nieve **no es el brillo** — las dos son
brillantes en SWIR — sino **cuál de las dos bandas domina**:

```
NHI = (B12 − B11) / (B12 + B11)          (Marchese et al. 2019)

roca caliente →  B12 > B11  →  NHI > 0    el pico de emisión se corre hacia 2,2 µm
nieve         →  B12 < B11  →  NHI < 0    el hielo absorbe más en 2,2 µm
```

El falso color pinta B12 en rojo y B11 en verde. **Cuando las dos saturan en 255, la diferencia
entre ellas se destruye**: rojo = verde, o sea NHI = 0. Nieve y lava quedan del mismo blanco, y
ninguna inspección visual del PNG puede ya separarlas. La saturación no oscurece la imagen: **borra
justamente la magnitud que discrimina el fenómeno.**

**Evidencia medida:**

| Escena | Píxeles con ambas SWIR saturadas | Qué son según el NHI crudo |
|---|---|---|
| Lascar 2026-07-01 | **640.000 = 100 % de la imagen** | desierto brillante, ningún calor |
| Villarrica 2026-06-26 | 64.228 | **todos** nieve (NHI −0,29 a −0,12) |

**Alcance:** 540 fechas quemadas — **304 en Sentinel-2 (51 volcanes)** y **236 en Landsat (39
volcanes)**. 115 con más del 60 % de la escena ciega.

**Por qué pasa:** la ganancia lineal 2,5 está calibrada para terreno de reflectancia media. El
desierto de Atacama tiene B12 ≈ 0,56 → 0,56 × 2,5 = 1,4 → saturado. Los volcanes del norte y los
de nieve permanente quedan quemados **por construcción**, no por una escena mala.

**Cierre propuesto** (mitigación + fondo, ambos etiquetados):
- *Mitigación, hoy:* la auditoría marca cada imagen con su **fracción ciega**. Publicar ese número
  junto a la imagen para que quien la interpreta sepa cuándo el blanco no significa nada.
- *Fondo:* **el NHI no debe leerse nunca del PNG** — se calcula del crudo, donde la saturación no
  existe. Es el quick win nº 1 que la bibliografía del proyecto ya recomienda y sigue sin
  implementarse.
- *Abierto, decisión tuya:* ganancia diferenciada por zona (el norte desértico necesita ~1,5, no
  2,5). Toca el evalscript y **rompe la comparabilidad histórica de las series**, así que no lo hice.

---

### P1 · Nada compara lo publicado contra lo que la escena contenía — **la brecha de proceso**

**Lente:** proceso · **Ejes:** P5 (medición equivocada) + P1 (sin bucle de retroalimentación)

El pipeline verifica que la descarga **ocurrió**, no que la imagen **sirve**. Mide actividad, no
resultado. Por eso B1 sobrevivió un mes: no falló nada — el workflow dio verde, el archivo se
escribió con su tamaño normal, el dashboard lo mostró. Sólo un ojo humano sobre la imagen lo detectó.

Y el bucle está cortado en el otro sentido: cuando vos viste el problema, **nada en el sistema
recibió esa señal**. No hay ruta de vuelta desde "esta imagen está mal" hasta el pipeline.

**Cierre:** correr `auditoria_imagenes.py` en el workflow y fallar el job ante hallazgos de
severidad alta nuevos. *Fondo:* definir quién revisa esa salida y con qué cadencia — sin
responsable y sin disparador, no es una solución de proceso.

---

### T1 · La brecha que no cae en ninguno de los 27 ejes

*(Regla dura 7: si sólo devuelvo hallazgos que encajan en los ejes, no sé si descubrí algo o si el
instrumento se autoconfirmó.)*

**El archivo histórico es inmutable en la práctica, y eso convierte cada bug de render en permanente.**

Ningún eje cubre esto. No es P11 (trazabilidad: sí se puede saber qué se bajó), ni P6 (cadencia: el
cron corre bien), ni A7 (deriva: nada envejece). Es una propiedad estructural: el pipeline sólo
descarga **fechas que no tiene**. Una fecha ya presente nunca se vuelve a mirar, correcta o no. El
mecanismo de dedup que evita gastar PU es el mismo que **garantiza que un error de render sea para
siempre**.

Consecuencia: los 540 casos quemados y cualquier futuro B1 son deuda permanente, salvo intervención
manual. Y crece: cada día suma imágenes que nadie volverá a mirar.

**Cierre:** que `--dias N` pueda re-bajar por **calidad medida** y no sólo por ausencia de archivo.
La auditoría ya produce el listado de qué merece re-descarga.

---

## Cómo se protege el instrumento de sí mismo

La plantilla advierte que un instrumento vivo puede medir la magnitud equivocada. **Pasó acá, en
esta misma auditoría:** la primera versión reportó **1.822** casos de "calor no visible". Eran
**ruido de cuantización** — con R=21 y G=19, un solo nivel de diferencia en 8 bits, el NHI da 0,05
sin significado físico. Al poner un piso de señal quedaron **324**: 1.498 eran falsos.

Por eso el script corre **6 controles positivos antes de cada ejecución** y se niega a reportar si
alguno falla. Dos existen específicamente para separar las ramas que se confundieron:

```
[ok] ruido oscuro            -> NO debe reportar calor
[ok] anomalía con NHI real   -> SÍ debe reportar calor
```

Un control cuyas dos ramas no son separables es decorativo.

---

## Resultado completo

| Tipo | Sentinel-2 | Landsat | Severidad alta | Qué significa |
|---|---|---|---|---|
| **QUEMADA** | 304 | 236 | 115 | fracción ciega ≥ 20 %: calor y nieve indistinguibles |
| **CALOR_NO_VISIBLE** | 324 | 291 | 0 | NHI positivo real que el falso color no muestra rojo |
| **NODATA** | 16 | 66 | 82 | escena mayormente fuera de la pasada |
| **REQUIERE_VERIFICACION** | 25 | 0 | 0 | posible B1 — **exige contrastar contra la escena** |
| **PLANA** | 11 | 19 | 0 | sin contraste utilizable |

```bash
python auditoria_imagenes.py --landsat ../Landsat-v1 --detalle
```

### Lo que esta auditoría NO puede afirmar

- **Sobre un PNG se prueba que una imagen está ciega, no que le falta una anomalía.** Los 25
  `REQUIERE_VERIFICACION` son sospechas. De 4 contrastados contra la fuente, **1 era bug real** y
  los otros 3 eran escenas sin anomalía. Tratarlos como confirmados repetiría el error que ya
  cometí en el diagnóstico.
- Los 324 `CALOR_NO_VISIBLE` sobrevivieron al filtro de ruido, pero **ninguno fue verificado contra
  su escena cruda**. Son la cola pendiente más interesante: si son reales, hay actividad térmica que
  el dashboard no está mostrando.
- La causa raíz de B1 sigue abierta.

---

## Oportunidades *(lista aparte — no compiten con las brechas)*

| # | Eje | Oportunidad |
|---|---|---|
| O1 | activo infrautilizado | El NHI es calculable con las bandas que **ya se descargan**. Sin pedir nada nuevo se obtiene un discriminante calor/nieve cuantitativo. |
| O5 | barato de medir | ¿Los 324 `CALOR_NO_VISIBLE` son actividad real? Se contesta bajando ~10 crudos. |
| O4 | reutilizable | El detector sirve para cualquier proyecto del workspace que publique falso color SWIR. |
| O2 | automatizable | La fracción ciega puede viajar en el metadata y mostrarse en el dashboard. |

---

*Instrumento: `auditoria_imagenes.py`. Reproducible, 0 PU, con controles positivos obligatorios.*
