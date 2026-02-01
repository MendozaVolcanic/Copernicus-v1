# 🛰️ Copernicus-v1 - Sentinel-2 Volcanic Monitoring

Sistema automatizado de descarga y procesamiento de imágenes **Sentinel-2** para monitoreo de volcanes chilenos.

---

## 🌋 Volcanes Monitoreados

| Volcán | Región | Estado |
|--------|--------|--------|
| **Villarrica** | Araucanía | ✅ Activo |
| Llaima | Araucanía | 🔄 Pendiente |
| Nevados de Chillán | Ñuble | 🔄 Pendiente |
| Copahue | Biobío | 🔄 Pendiente |
| Puyehue-Cordón Caulle | Los Lagos | 🔄 Pendiente |
| Planchón-Peteroa | Maule | 🔄 Pendiente |
| Lascar | Antofagasta | 🔄 Pendiente |
| Lastarria | Antofagasta | 🔄 Pendiente |
| Isluga | Tarapacá | 🔄 Pendiente |
| Chaitén | Los Lagos | 🔄 Pendiente |

---

## 📊 Composiciones de Imagen

### **RGB (Color Real)**
- **Bandas:** B04 (Red), B03 (Green), B02 (Blue)
- **Uso:** Visualización natural del terreno
- **Resolución:** 10m/píxel

### **Thermal False Color (Falso Color Térmico)**
- **Bandas:** B12 (SWIR2), B11 (SWIR1), B04 (Red)
- **Uso:** Detección de anomalías térmicas, flujos de lava
- **Resolución:** 20m/píxel (B12, B11) + 10m/píxel (B04)

---

## 🚀 Características

- ✅ **Descarga automática diaria** (GitHub Actions)
- ✅ **Filtro de nubes** (< 30% cobertura)
- ✅ **Buffer de 15 km** alrededor del volcán
- ✅ **2 composiciones** por fecha (RGB + Thermal)
- ✅ **Metadata CSV** por volcán
- ✅ **Procesamiento on-demand** (PNG listo, no .zip completo)

---

## 📂 Estructura del Repositorio

```
Copernicus-v1/
├── .github/
│   └── workflows/
│       └── sentinel2_auto.yml      # Automatización diaria
├── scripts/
│   ├── config_sentinel2.py         # Configuración volcanes + OAuth
│   └── sentinel2_downloader.py     # Script descarga
├── data/
│   └── sentinel2/
│       └── Villarrica/             # Volcán piloto
│           ├── RGB/                # Imágenes color real
│           ├── ThermalFalseColor/  # Imágenes térmicas
│           └── metadata.csv        # Registro descargas
├── docs/
│   └── sentinel2_dashboard.html    # Visualizador (futuro)
├── requirements.txt
└── README.md
```

---

## ⚙️ Configuración Inicial

### **1. GitHub Secrets (CRÍTICO)**

Debes configurar 2 secrets en el repositorio:

```
Repo → Settings → Secrets and variables → Actions → New repository secret

Name: SH_CLIENT_ID
Value: [Tu Client ID de Copernicus]

Name: SH_CLIENT_SECRET
Value: [Tu Client Secret de Copernicus]
```

### **2. Obtener Credenciales OAuth**

Si no tienes credenciales:

1. Ir a: https://shapps.dataspace.copernicus.eu/dashboard/
2. Login con cuenta Copernicus
3. Create OAuth Client
   - Type: **Client Credentials** (NO single-page app)
   - Expiry: 90 o 365 días
4. Copiar Client ID y Client Secret
5. Configurar GitHub Secrets

---

## 🧪 Testing Manual

### **Ejecutar workflow manualmente:**

1. Ir a: **Actions** → **Descarga Sentinel-2**
2. Click en **Run workflow**
3. Esperar ~2-3 minutos
4. Verificar en `data/sentinel2/Villarrica/`:
   - `RGB/2025-XX-XX_RGB.png`
   - `ThermalFalseColor/2025-XX-XX_ThermalFalseColor.png`
   - `metadata.csv`

---

## 📋 Formato Metadata CSV

```csv
fecha,tipo,cobertura_nubosa,sensor,ruta_archivo,tamano_mb
2025-01-18,RGB,18.5,Sentinel-2A,RGB/2025-01-18_RGB.png,4.2
2025-01-18,ThermalFalseColor,18.5,Sentinel-2A,ThermalFalseColor/2025-01-18_ThermalFalseColor.png,3.8
```

**Campos:**
- `fecha`: YYYY-MM-DD
- `tipo`: RGB o ThermalFalseColor
- `cobertura_nubosa`: Porcentaje 0-100
- `sensor`: Sentinel-2A o Sentinel-2B
- `ruta_archivo`: Path relativo
- `tamano_mb`: Tamaño en MB

---

## 📊 Uso de Cuota Copernicus

### **Processing Units (PU):**
- ~100 PU por imagen
- 2 tipos × 1 volcán × día = 200 PU/día
- Límite free: **10,000 PU/mes**
- Capacidad: ~50 descargas/mes (muy holgado para 1 volcán diario)

### **Expansión futura (10 volcanes):**
- 2 tipos × 10 volcanes = 20 imágenes/día
- 2,000 PU/día × 30 días = **60,000 PU/mes**
- Requeriría plan de pago (~30 EUR/mes)

---

## 🔄 Frecuencia de Descarga

- **Automática:** Diaria a las **06:00 UTC** (03:00 Chile)
- **Manual:** Desde pestaña Actions
- **Sentinel-2:** Pasa cada **~3-5 días** sobre Chile
- **Estrategia:** Buscar últimos 7 días, tomar la más reciente con < 30% nubes

---

## 🔐 Seguridad

### **NUNCA commitear:**
- ❌ Credenciales OAuth en código
- ❌ Archivos .env con secrets
- ❌ Imágenes .zip completas (>100 MB)

### **SIEMPRE:**
- ✅ Usar GitHub Secrets
- ✅ Variables de entorno (`os.getenv`)
- ✅ .gitignore actualizado

---

## ⏰ Mantenimiento

### **Rotación de Credenciales (cada 90 días):**

1. Crear nuevo OAuth client en Copernicus
2. GitHub → Settings → Secrets → Actions
3. Editar `SH_CLIENT_ID` y `SH_CLIENT_SECRET`
4. Test manual del workflow
5. Eliminar cliente antiguo

**Recordatorio:** [Configurar alarma 15 días antes de expirar]

---

## 📚 Documentación Útil

- **Sentinel Hub API:** https://documentation.dataspace.copernicus.eu/APIs/SentinelHub.html
- **Process API:** https://docs.sentinel-hub.com/api/latest/api/process/
- **Evalscripts:** https://docs.sentinel-hub.com/api/latest/evalscript/
- **Copernicus Browser:** https://browser.dataspace.copernicus.eu/

---

## 🎯 Roadmap

### **V1.0 (Actual)**
- ✅ Descarga automatizada Villarrica
- ✅ 2 composiciones (RGB + Thermal)
- ✅ Metadata CSV

### **V2.0 (Próximo)**
- 🔄 Dashboard HTML interactivo
- 🔄 Comparación temporal (slider)
- 🔄 GitHub Pages deployment

### **V3.0 (Futuro)**
- 🔄 Activar 3-5 volcanes adicionales
- 🔄 Detección automática de cambios
- 🔄 Integración con MIROVA (cross-referencia)

---

## 👥 Créditos

- **Desarrollo:** Nicolás Mendoza
- **Asistencia:** Claude (Anthropic)
- **Fuente de datos:** Copernicus Sentinel-2 (ESA)
- **Infraestructura:** GitHub Actions

---

## 📄 Licencia

Proyecto académico/científico - Universidad/Institución

**Data:** Copernicus Sentinel data (free and open)
