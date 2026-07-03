# Tests Copernicus-v1

Suite de **smoke tests** con pytest. Objetivo: piso mínimo de protección
contra regresiones obvias en el config, evalscripts, funciones de change
detection y outputs JSON públicos.

## Cómo correr

Desde la raíz del proyecto (`Copernicus-v1/`):

```bash
# Todos los tests (rápidos)
pytest tests/ -v

# Solo un módulo
pytest tests/test_config.py -v

# Excluir los marcados como lentos (por defecto ya se corren todos)
pytest tests/ -v -m "not slow"

# Con coverage (requiere `pip install pytest-cov`)
pytest tests/ --cov=. --cov-report=term-missing
```

Pre-requisitos:
- Python 3.11+
- `pytest`, `numpy`, `Pillow` (ya en `requirements.txt`)
- `scipy` (opcional; sin él, los tests de Mahalanobis se skipean)

## Qué cubre

| Archivo | Cubre |
|---|---|
| `test_config.py` | 46 entidades, rangos lat/lon de Chile, zonas válidas, IDs únicos, vistas zoom, **regresión Chillán/Antuco** |
| `test_evalscripts.py` | RGB con sRGB, Thermal LINEAL, orden de bandas B12/B11/B04 |
| `test_change_analysis.py` | NHI S2 y Landsat, VRP, NDSI glaciar, Mahalanobis (sobre PNGs sintéticos 100×100) |
| `test_json_outputs.py` | `fechas_disponibles_copernicus.json` (orden ASC, formato YYYY-MM-DD, claves válidas), `change_results.json` (campos `estado`, `nhi_estado`, `mahalanobis_estado`, `z_score_estado`) |
| `test_descarga.py` | Fail-fast 401/403, dedup misma fecha, skip si PNG ya existe (todo mockeado, sin red) |

## Qué NO cubre (por ahora)

- Descarga real desde Copernicus Data Space (requiere credenciales y red)
- Generación de GIFs (lenta; cubrir con tests marcados `@pytest.mark.slow`)
- Generación de PPT (`ppt_generator.py`)
- Frontend (dashboard HTML) — usar Playwright en proyecto aparte
- Workflows de GitHub Actions

## Cómo agregar tests

1. Crear archivo `tests/test_<area>.py`.
2. Para imágenes de prueba, **no commitear PNGs** — usar fixtures de `conftest.py`
   (`tmp_png_lineal`, `tmp_png_srgb`, `tmp_png_thermal_*`).
3. Si el test depende de red, **mockear con `unittest.mock.patch`** sobre
   `requests.post`/`requests.get` — nunca golpear APIs reales.
4. Marcar con `@pytest.mark.slow` si tarda más de 1s.
5. Ejecutar localmente antes de commit.

## Convenciones

- Cada test prueba **una** cosa.
- Los nombres empiezan con `test_` y describen la condición esperada.
- Fixtures comunes viven en `conftest.py`.
- Tests deterministas: `np.random.default_rng(seed=42)` siempre que se use random.
- Sin acceso a red ni a archivos grandes.

## Política de fallos

- Si un test falla **revelando un bug**: documentar en `AUDITORIA_PYTHON_*.md`, no parchar el test.
- Si el test está mal hecho: arreglar el test.
- Si el sistema cambió legítimamente: actualizar el test.
