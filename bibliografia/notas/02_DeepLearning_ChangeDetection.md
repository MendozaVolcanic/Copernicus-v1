# 02 — Deep Learning para Change Detection en Teledetección

Notas técnicas accionables para migrar `change_analysis.py` (actual: Z-score) hacia DL en Copernicus-v1.

---

## 1. Remote Sensing Image Change Detection with Transformers (BIT)

**Cita completa:** Chen, H., Qi, Z., & Shi, Z. (2021). *Remote Sensing Image Change Detection with Transformers*. IEEE Transactions on Geoscience and Remote Sensing. arXiv:2103.00208v3.
**PDF:** `bibliografia/pdfs/Chen_2021_BIT_Transformer.pdf`
**Páginas leídas:** 1–13 (introducción, arquitectura, experimentos, ablations, discusión)
**Repo código:** https://github.com/justchenhao/BIT_CD (PyTorch, oficial)

### Resumen ejecutivo
Propone **BIT (Bitemporal Image Transformer)**: una capa transformer que reemplaza la última etapa convolucional de ResNet18 para change detection binario en imágenes ópticas de alta resolución. La idea clave es comprimir cada imagen a un vocabulario muy pequeño (L=4 tokens) y modelar contexto espacio-temporal vía self-attention sobre tokens en lugar de píxeles, con coste computacional 3x menor que la baseline puramente convolucional y F1 superior.

### Arquitectura del modelo

Pipeline en 3 etapas:

1. **CNN backbone** (ResNet18 truncado en stage 4): extrae feature maps `X1, X2 ∈ R^(H×W×C)` con C=32, H=W=H_img/4.
2. **BIT module**:
   - **Semantic Tokenizer** (Siamese): point-wise conv `W ∈ R^(C×L)` + softmax espacial → atención `A_i ∈ R^(HW×L)`. Tokens `T_i = A_i^T · X_i ∈ R^(L×C)`. Con **L=4** (óptimo).
   - **Transformer Encoder** (depth=1): MSA + MLP sobre concat `[T1; T2] ∈ R^(2L×C)` con positional embedding aprendido. PreNorm. Salida: `T1_new, T2_new`.
   - **Transformer Decoder Siamese** (depth=8): cross-attention donde Query = features pixel-space `X_i`, Key/Value = tokens `T_i_new`. Refina cada feature map.
3. **Prediction Head**: `|X1_new − X2_new|` → conv 3×3 → upsample → BCE binaria.

```python
import torch
import torch.nn as nn

class SemanticTokenizer(nn.Module):
    def __init__(self, C=32, L=4):
        super().__init__()
        self.conv = nn.Conv2d(C, L, 1)  # point-wise
    def forward(self, x):                 # x: (B, C, H, W)
        att = self.conv(x).flatten(2)     # (B, L, HW)
        att = att.softmax(dim=-1)         # spatial softmax
        x_flat = x.flatten(2).transpose(1, 2)  # (B, HW, C)
        tokens = att @ x_flat             # (B, L, C)
        return tokens

class BIT(nn.Module):
    def __init__(self, C=32, L=4, enc_depth=1, dec_depth=8, heads=8):
        super().__init__()
        self.tokenizer = SemanticTokenizer(C, L)
        self.pos_emb = nn.Parameter(torch.randn(1, 2*L, C))
        enc_layer = nn.TransformerEncoderLayer(C, heads, 2*C,
                                               norm_first=True, batch_first=True)
        self.encoder = nn.TransformerEncoder(enc_layer, enc_depth)
        dec_layer = nn.TransformerDecoderLayer(C, heads, 2*C,
                                               norm_first=True, batch_first=True)
        self.decoder = nn.TransformerDecoder(dec_layer, dec_depth)
        self.head = nn.Conv2d(C, 2, 3, padding=1)

    def forward(self, x1, x2):
        B, C, H, W = x1.shape
        t1, t2 = self.tokenizer(x1), self.tokenizer(x2)
        T = torch.cat([t1, t2], dim=1) + self.pos_emb     # (B, 2L, C)
        T = self.encoder(T)
        t1_new, t2_new = T.split(t1.size(1), dim=1)
        # decoder: query = pixel features, kv = tokens
        x1_q = x1.flatten(2).transpose(1, 2)              # (B, HW, C)
        x2_q = x2.flatten(2).transpose(1, 2)
        x1r = self.decoder(x1_q, t1_new).transpose(1, 2).reshape(B, C, H, W)
        x2r = self.decoder(x2_q, t2_new).transpose(1, 2).reshape(B, C, H, W)
        diff = torch.abs(x1r - x2r)
        return self.head(diff)                            # logits 2-class
```

### Dataset usado para entrenar
- **LEVIR-CD**: 637 pares 1024×1024, 0.5 m/px, edificios (Google Earth).
- **WHU-CD**: 32 507×15 354 px, 0.075 m/px, edificios post-terremoto.
- **DSIFN-CD**: 6 ciudades chinas, multi-clase (edificios, carreteras, vegetación, agua).
- Crops 256×256, augmentation estándar (flip, rotación, blur, color jitter).

**Para Copernicus-v1**: NO tenemos labels supervisados de change detection. Opciones:
- Pre-entrenar con LEVIR-CD/WHU-CD (no es volcánico — gap de dominio severo).
- Generar pseudo-labels con `change_analysis.py` Z-score actual y fine-tunear.
- Sintéticos: simular cambios térmicos/morfológicos sobre escenas Sentinel-2 limpias.

### Tarea / loss function
- **Tarea**: change detection binario pixel-wise (cambio / no-cambio).
- **Loss**: cross-entropy estándar 2-clases (los autores no usan focal/dice). Sin pesos por clase explícitos.
- **Métricas**: Precision, Recall, F1, IoU, Overall Accuracy.

### Resultados / benchmarks (Tabla I del paper, F1 / IoU %)

| Modelo         | Params (M) | FLOPs (G) | LEVIR F1/IoU | WHU F1/IoU  | DSIFN F1/IoU |
|----------------|-----------:|----------:|-------------:|------------:|-------------:|
| FC-EF          |       1.35 |      3.57 | 83.40 / 71.53 | 69.37 / 53.11 | 61.09 / 43.98 |
| FC-Siam-Di     |       1.35 |      4.73 | 86.31 / 75.92 | 58.81 / 41.66 | 62.54 / 45.50 |
| FC-Siam-Conc   |       1.55 |      5.33 | 83.69 / 71.96 | 66.63 / 49.95 | 59.71 / 42.56 |
| DTCDSCN        |      41.07 |      7.21 | 87.67 / 78.05 | 71.95 / 56.19 | 63.72 / 46.76 |
| STANet         |      16.93 |      6.58 | 87.26 / 77.40 | 82.32 / 69.95 | 64.56 / 47.66 |
| IFNet          |      50.71 |     41.18 | 88.13 / 78.77 | 83.40 / 71.52 | 60.10 / 42.96 |
| SNUNet         |      12.03 |     27.44 | 88.16 / 78.83 | 83.50 / 71.67 | 66.18 / 49.45 |
| **BIT (ours)** |   **3.55** |   **4.35** | **89.31 / 80.68** | **83.98 / 72.39** | **69.26 / 52.97** |

**Ablation studies (clave)**:
- Quitar tokenizer: F1 cae ~1.5–7 pts → tokenizer es crítico (los tokens densos saturan al transformer).
- Quitar Transformer Encoder: caída en los 3 datasets → MSA modela contexto espacio-temporal.
- Quitar Transformer Decoder: caída notable → cross-attention es clave para refinar pixel-space.
- Token length L: barrido {2,4,8,16,32}. **L=4 óptimo**; L=32 hiere performance (redundancia).
- Encoder depth: 1 capa basta. Decoder depth: 8 da el mejor F1.
- Positional embedding: requerido en encoder, NO en decoder.

**Hiperparámetros recomendados** (de `BIT_CD` repo + paper): SGD, lr=0.01, momentum=0.99, weight_decay=5e-4, batch=8, 200 epochs, lr step decay, input 256×256.

### Aplicabilidad a Copernicus-v1
- **Tipo de cambio**: morfológico/espectral en RGB de alta resolución → directamente útil para detectar lahares, flujos piroclásticos, cambios en domos, depósitos de tefra en Sentinel-2 RGB (10 m). Menos directo para anomalías térmicas (B12 SWIR Sentinel-2 / B10 Landsat TIRS) — habría que tratar los thermal composites como otro "RGB" de 3 bandas.
- **Encaje con pipeline actual**: `change_analysis.py` usa Z-score multi-temporal sobre series. BIT es bitemporal (2 fechas). Estrategia: aplicarlo como segundo filtro tras Z-score — dado un pixel "candidato" Z-score, validar con BIT sobre `(t-1, t)`.
- **Hardware inference**: 3.55M params, 4.35 GFLOPs sobre 256×256 → corre en CPU en segundos por tile, GPU consumer (8 GB) holgado para fine-tuning.
- **Esfuerzo integración**: medio. Repo PyTorch público y limpio. Necesita: (a) labels o pseudo-labels, (b) wrapper que tile las escenas Sentinel-2 (cada volcán ~256–512 px típico), (c) GPU para fine-tune (Colab T4 sirve).

### Limitaciones reportadas
- Solo binario; multi-clase requiere extender la prediction head.
- Sensible al pre-procesado: pares mal co-registrados destruyen la atención.
- Cambios sub-pixel o muy difusos no los captura (el tokenizer L=4 sesga hacia "cambios concentrados").
- Entrenado con HR óptica edificios; transferencia a 10 m / 30 m volcánica no probada en el paper.

### Ideas de aplicación específica para volcanes chilenos
- Pre-entrenar con LEVIR-CD → fine-tune con pares Sentinel-2 etiquetados manualmente para casos: **Calbuco abril 2015** (depósito de tefra muy visible RGB pre/post), **Cordón Caulle 2011** (cambio masivo morfológico), **Chillán 2008–en curso** (crecimiento de domo, varios episodios), **Villarrica 2015** (cambio en cráter).
- Adaptar a 6 canales (RGB + SWIR thermal pre/post) modificando `nn.Conv2d` de entrada.
- Combinar con timelapse: usar BIT en sliding window temporal (t, t+1) y agregar flags por mes.

---

## 2. Largescale demonstration of machine learning for the detection of volcanic deformation in Sentinel-1 satellite imagery (Gaddes/Biggs 2022)

**Cita completa:** Biggs, J., Anantrasirichai, N., Albino, F., Lazecký, M., & Maghsoudi, Y. (2022). *Largescale demonstration of machine learning for the detection of volcanic deformation in Sentinel-1 satellite imagery*. Bulletin of Volcanology, 84:100. https://doi.org/10.1007/s00445-022-01608-x
**PDF:** `bibliografia/pdfs/Gaddes_2022_ML_Sentinel1_Deformation.pdf`
**Páginas leídas:** 1–14 (métodos, resultados regionales, performance, atmósfera, coherencia, limitaciones)
**Repo código:** Algoritmo de detección: https://github.com/anantrasirichai (modelos en releases). Procesamiento InSAR: COMET-LiCSAR portal http://comet.nerc.ac.uk/COMET-LiCS-portal/

### Resumen ejecutivo
Aplicación a escala global del CNN de Anantrasirichai 2018/2019b sobre **~600,000 interferogramas Sentinel-1 wrapped** de >1000 volcanes Holocenos (2015–2020). De los 16 volcanes con detecciones persistentes, 5 tuvieron erupciones, 6 deformación lenta, 2 deformación no-volcánica, 3 artefactos atmosféricos. **Umbral de detección global: 5.9 cm** (1.2 cm/año). Demuestra viabilidad operacional pero también que coherencia y atmósfera son los limitantes principales.

### Arquitectura del modelo
**Backbone**: AlexNet pre-entrenada en ImageNet, fine-tuneada para 2 clases.
- Input: parche **224×224 grayscale** (8-bit) de un interferograma wrapped (sliding window con stride 28 px sobre el tile completo).
- Salida: probabilidad por parche `P ∈ [0,1]` de "contiene deformación + atmósfera" vs "solo atmósfera".
- Probabilidades de parches se mergean con pesos gaussianos para producir mapa por imagen y `P_max`.
- **Threshold operacional**: `P_max > 0.5` → flag (escogido conservador para minimizar falsos negativos).

```python
import torch.nn as nn
from torchvision.models import alexnet

class VolcanicDeformationCNN(nn.Module):
    """Anantrasirichai 2018/2019b style — AlexNet fine-tune binario."""
    def __init__(self, n_classes=2):
        super().__init__()
        base = alexnet(weights="IMAGENET1K_V1")
        # Adaptar 1 canal de entrada (grayscale wrapped interferogram)
        base.features[0] = nn.Conv2d(1, 64, kernel_size=11, stride=4, padding=2)
        # Cabeza 2 clases
        base.classifier[6] = nn.Linear(4096, n_classes)
        self.net = base

    def forward(self, x):                       # x: (B, 1, 224, 224)
        return self.net(x)                       # logits

# Inferencia por imagen completa con sliding window:
# patches = sliding_window(image, size=224, stride=28)
# probs = softmax(model(patches), dim=-1)[:, 1]
# prob_map = gaussian_merge(probs, positions)
# P_max = prob_map.max()
```

### Dataset usado para entrenar
- **Train**: combinación de (a) interferogramas reales con/sin deformación curados manualmente (~30k de Anantrasirichai 2018), (b) **interferogramas sintéticos** generados con modelos atmosféricos globales y fuentes de deformación analíticas (Mogi, sill, dyke) — Anantrasirichai 2019b.
- Clases: D+S+T (deformación + estratificada + turbulenta) vs S+T (solo atmósfera).
- **Test (este paper)**: 592,224 wrapped interferograms de 1084 volcanes, generados automáticamente por COMET-LiCSAR.

**Para Copernicus-v1**: este pipeline es para **InSAR (Sentinel-1)**, no óptico. Si queremos deformación, requeriría: cuenta CEDA/JASMIN o procesamiento InSAR propio (snap2stamps, ISCE) — fuera del alcance actual del proyecto que usa Sentinel-2 + Landsat ópticos. Reusable conceptualmente: la idea de **datos sintéticos + AlexNet fine-tune** se puede transferir a anomalías térmicas ópticas.

### Tarea / loss function
- Clasificación binaria por parche (224×224).
- Loss: cross-entropy estándar.
- Métrica reportada: detection threshold (cm de desplazamiento) ajustando sigmoide `f(x) = 1 / (1 + exp(-a(x-b)))` a probabilidad vs desplazamiento máximo.

### Resultados / benchmarks

| Métrica                                | Valor                                                |
|----------------------------------------|------------------------------------------------------|
| Imágenes procesadas                    | 592 224                                               |
| Volcanes cubiertos                     | 1 084                                                 |
| Flags totales (`P > 0.5`)              | 3 323 en 366 volcanes                                 |
| Volcanes con detecciones persistentes  | 16 (5 erupciones, 6 unrest, 2 no-volc, 3 atm.)        |
| Umbral global                          | **5.9 cm** (1.2 cm/año en 5 años)                    |
| Umbral Tambora (low-relief)            | 2.1 cm                                                |
| Umbral Domuyo (high-relief)            | 9.9 cm                                                |
| Umbral Laguna del Maule (Chile)        | 5.5 cm                                                |
| Umbral Etna                            | 6.3 cm                                                |

**Análisis de performance**:
- **Coherencia**: caso Chillán (Chile) — uplift ~10–12 cm/año pero solo 1 detección porque coherencia media = 0.13–0.20 (vs 0.24–0.33 en Maule/Domuyo). Coherencia < 0.20 ≈ algoritmo no funciona.
- **Atmósfera**: Fujisan tuvo 165 falsos positivos (segundo más alto), reducidos a 64 con corrección GACOS. Volcanes tropicales (Agung, Lawu) particularmente afectados.
- **Casos chilenos**: Laguna del Maule (61 flags), Domuyo Argentina (63 flags), Chillán (1 flag — limitado por coherencia y nieve estacional).

### Aplicabilidad a Copernicus-v1
- **Tipo de cambio**: deformación cm-escala (precursor de erupciones por intrusión magmática). Complementario a térmico (que es co-eruptivo).
- **Encaje con pipeline actual**: requiere agregar Sentinel-1 SAR al proyecto (hoy solo S2 + L8/9 ópticos). El portal LiCSAR ofrece interferogramas pre-procesados gratis para muchos volcanes — se puede consumir como nuevo módulo `insar_downloader.py` paralelo a `sentinel2_downloader.py`.
- **Hardware**: AlexNet fine-tune corre en CPU para inferencia, GPU consumer para entrenar.
- **Esfuerzo integración**: ALTO. Procesamiento InSAR no trivial (snaphu, GACOS). Camino más simple: **consumir LiCSAR portal directamente**. Modelo entrenado de Anantrasirichai está disponible.

### Limitaciones reportadas
- Coherencia baja (vegetación densa, nieve, agua) anula detección.
- Artefactos atmosféricos en alto relieve y trópico → falsos positivos persistentes.
- Deformación en serie temporal acumulada (no en interferograma individual) requiere unwrapping correcto, que falla con deformaciones extremas (Sierra Negra 2018: 8.5 m reales → 2 m aliased).
- Cambios en *tasa* de deformación son difíciles de capturar con CNN sobre imagen acumulada (caso Reykjanes/Fagradalsfjall).
- Modelo entrenado mayoritariamente con Etna/Erte Ale/Sierra Negra/Cerro Negro → sub-representación de calderas silícicas grandes.

### Ideas de aplicación específica para volcanes chilenos
- Volcanes chilenos con detección esperada (alta coherencia, deformación conocida): **Laguna del Maule, Cerro Hudson, Calbuco, Villarrica, Lascar**.
- Volcanes "perdidos" por baja coherencia: **Chillán** (nieve), **Cordón Caulle** (vegetación post-eruptiva). Necesitarán processing tailored (ML interferograms estacionales).
- Estrategia: módulo nuevo `insar_monitor.py` que (a) tira polling al portal LiCSAR, (b) aplica el modelo Anantrasirichai pre-entrenado, (c) cruza alertas con `alert_generator.py` actual. Erupción detectada por **térmico (rápido) + deformación (precursor)** sería un alert tier elevado.

---

## 3. Anantrasirichai 2022 — Autoencoders para anomaly detection volcánica (Sentinel-1)

**ATENCIÓN**: el archivo `Anantrasirichai2022_ML_Sentinel1.pdf` **NO se encuentra** en `bibliografia/pdfs/`. La carpeta sí contiene Chen 2021 y Gaddes 2022, pero no este tercer paper. Las notas siguientes están elaboradas a partir de las **referencias cruzadas en Gaddes 2022** (que cita explícitamente Anantrasirichai et al. 2018, 2019a, 2019b — el modelo de detección por CNN supervisada). Antes de implementar, **descargar el PDF correcto** y completar/corregir esta sección.

**Cita probable (a verificar):** Anantrasirichai, N., et al. (2022). *A deep learning approach to detecting volcano deformation from satellite imagery using synthetic datasets / autoencoder-based anomaly detection*. (verificar título y journal exacto al obtener PDF).
**Repo asociado:** https://github.com/nantheera o búsqueda en perfiles del Visual Information Lab, University of Bristol.

### Resumen ejecutivo (basado en literatura referenciada)
La línea de trabajo Anantrasirichai et al. propone CNN supervisado entrenado mayoritariamente con **interferogramas sintéticos** para superar la escasez de etiquetas reales. El modelo de 2 clases (D+S+T vs S+T) es el que despliega Gaddes 2022. Versiones posteriores exploran autoencoders convolucionales para anomaly detection no-supervisada — útil cuando no hay labels positivos.

### Arquitectura típica autoencoder para anomaly detection (template)

```python
import torch.nn as nn

class ConvAutoencoder(nn.Module):
    """Template para anomaly detection volcánica no supervisada.
    Reconstrucción de interferogramas 'normales' (sin deformación).
    Anomalía = error de reconstrucción alto."""
    def __init__(self, in_ch=1, latent=128):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Conv2d(in_ch, 32, 3, 2, 1), nn.ReLU(),   # 224 -> 112
            nn.Conv2d(32, 64, 3, 2, 1),    nn.ReLU(),   # 112 -> 56
            nn.Conv2d(64, 128, 3, 2, 1),   nn.ReLU(),   #  56 -> 28
            nn.Conv2d(128, latent, 3, 2, 1), nn.ReLU(), #  28 -> 14
        )
        self.dec = nn.Sequential(
            nn.ConvTranspose2d(latent, 128, 4, 2, 1), nn.ReLU(),
            nn.ConvTranspose2d(128, 64,    4, 2, 1), nn.ReLU(),
            nn.ConvTranspose2d(64,  32,    4, 2, 1), nn.ReLU(),
            nn.ConvTranspose2d(32,  in_ch, 4, 2, 1), nn.Sigmoid(),
        )
    def forward(self, x):
        z = self.enc(x)
        return self.dec(z)

# Loss: MSE entre input y reconstrucción.
# Score de anomalía: error_pixel = (x - x_hat)**2  ->  mapa de anomalías.
# Threshold por percentil sobre training set "normal".
```

### Dataset y entrenamiento (estándar reportado en la familia de papers)
- Train: solo interferogramas "normales" (sin deformación, pre-eruptivos lejanos en el tiempo).
- Augmentation con sintéticos atmosféricos (capas estratificadas + turbulentas).
- Loss: MSE reconstrucción.
- Inferencia: error por pixel + clustering espacial → anomalía localizada.

### Aplicabilidad a Copernicus-v1
- **Caso de uso fuerte**: anomaly detection sobre **thermal composites Sentinel-2 (B12) y Landsat TIRS B10** sin necesidad de etiquetas. Encajaría exactamente en el slot que ocupa Z-score actual en `change_analysis.py`, con la ventaja de aprender la *distribución espacial* de "normalidad" (cada volcán tiene baseline distinto).
- **Implementación realista**: train un autoencoder por volcán (o uno global con embedding de volcán) con todas las imágenes históricas Sentinel-2 disponibles del proyecto. Threshold de error por percentil 99 del training. Comparar con Z-score como baseline.

### Limitaciones esperadas
- Autoencoders aprenden a reconstruir cualquier cosa si la red es muy capaz → fugas de anomalías. Solución: regularización (VAE, denoising AE) o restringir capacidad.
- Cambios estacionales (nieve) se aprenden como "normales" si están en train — bueno para reducir FP estacionales, malo si la anomalía coincide con cambio estacional.
- Sin label de positivos, no hay F1 reportable hasta validar contra historial conocido (Calbuco 2015, etc.).

### Acción siguiente OBLIGATORIA
**Localizar y descargar el PDF correcto antes de implementar**. Probables candidatos:
- Anantrasirichai et al., "An application of deep learning to detect ground deformation in volcanic regions" (Remote Sensing of Environment / IEEE TGRS / Bulletin of Volcanology).
- Búsqueda Google Scholar: `Anantrasirichai 2022 autoencoder volcanic Sentinel-1`.

---

## Síntesis para Copernicus-v1 (roadmap propuesto)

| Fase | Modelo | Datos | Esfuerzo | Beneficio esperado |
|------|--------|-------|----------|-------------------|
| 1 | Autoencoder convolucional sobre Sentinel-2 thermal (B12) | Histórico propio del proyecto | Bajo (sin labels) | Reemplazo directo de Z-score, sensible a contexto espacial |
| 2 | BIT fine-tune (LEVIR-CD pretrained) | Pseudo-labels Z-score + curado manual de Calbuco/Caulle/Chillán | Medio | Detección morfológica RGB de eventos eruptivos |
| 3 | Anantrasirichai/Gaddes CNN sobre LiCSAR | LiCSAR portal + modelo pre-entrenado | Alto | Precursores de deformación (semanas-meses antes) |

**Hardware mínimo**: GPU 8 GB para fine-tune (Colab T4 / RTX 3060). Inferencia operacional en CPU para los 3 modelos.

**Skills sugeridas a invocar al implementar**: `python-pro`, `test-driven-development`, `verification-before-completion`, `data-visualization` para validación visual de mapas de cambio.
