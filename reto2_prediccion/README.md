# Reto 2: predicción de abstención por sección y escenarios 2027

Pronóstico de abstención por sección electoral (≈68 mil) para la intermedia de 2027. Resultados completos y rigor en `reports/RESULTADOS.md`; análisis exploratorio en `reports/EDA.md`.

**Conclusión corta.** Con datos públicos disponibles antes de la elección, el R² honesto (entrenar en elecciones pasadas, predecir la siguiente, sobre abstención relativa al nivel nacional) es 0.62 (2021) y 0.71 (2024); el mejor modelo es Ridge/Lasso sobre rezagos por tipo de elección y apenas supera a repetir la última presidencial. El error es un choque jurisdiccional (municipio y estado) que cambia de causa y signo entre elecciones y no se anticipa. Un R² de ~0.80 solo aparece conociendo ese choque a nivel distrital del propio año. Detalle en `reports/RESULTADOS.md` §6 y §11.

## Cómo reproducir

```
uv run shared/download_data.py      # conteos de participación, ECEG 2020, cartografía
uv run shared/download_extra.py     # ECEG 2010, DENUE, SESNSP, Magar (casillas, municipales, gubernaturas), RM 2022, gasto de campaña INE (idempotente)
uv run shared/build_panel.py        # data/processed/{panel,eceg}.parquet, secciones.gpkg
uv run reto2_prediccion/analysis/eda.py ; benchmark.py ; ablation.py ; rigor.py     # modelo, benchmark, ablación y rigor (§1-8)
```
Cada script de `reto2_prediccion/analysis/` se corre con `uv run reto2_prediccion/analysis/<nombre>.py` desde la raíz del repo (dependencias en el encabezado). Los sitios del INE son aplicaciones web: si un enlace cambia, se localiza con navegador (Chrome en `/usr/bin/google-chrome` + playwright). Los zips de RM 2022 y los CSV de fiscalización se bajan desde los botones de descarga de `computosrm2022.ine.mx` y `fiscalizacion.ine.mx/web/portalsif/descarga-de-reportes`.

## Índice de scripts (`reto2_prediccion/analysis/`)

| Script | Pregunta | Sección de RESULTADOS | Salida en `reports/` |
|---|---|---|---|
| `shared/lib/{common,features,harness,stats_util}.py` | Biblioteca compartida: panel, features, backtest (folds 2021/2024), IC por bootstrap de municipios | - | - |
| `eda.py` | Descripción de datos | EDA | `eda_stats.json`, `fig/` |
| `benchmark.py`, `ablation.py`, `rigor.py` | Modelos, ablación, IC, placebo, semillas, techo | §3-8 | `benchmark.csv`, `ablation.csv`, `rigor_*.csv` |
| `alt_approaches.py` | Persistencia de choques, difusión en grafo, GWR, demografía dinámica, riesgo | §9 | `alt_*.csv` |
| `build_long.py`, `long_backtest.py` | Panel largo 1991-2024 (Magar) y backtest con más historia | §6, §11.1 | `long_backtest.csv` |
| `extra_mun.py`, `extra_test.py` | CONEVAL (pobreza/ingreso/seguridad social) y violencia SESNSP | §11 | `extra_mun_test.csv` |
| `extra_test2.py` | ECEG 2010→2020 y DENUE | §11 | `extra_inegi_test.csv` |
| `party_test.py` | Voto por bloque partidista y margen | §11 | `party_test.csv` |
| `extra_test3.py` | Calendario municipal y margen de la última municipal | §11 | `extra_calendario_test.csv` |
| `extra_test4.py`, `extra_test5.py` | Perfil histórico 1994+ y calendario estatal verificado | §11.1 | `extra_hist_test.csv`, `extra_hist_largo.csv` |
| `info_needed.py` | R² si se conociera el choque por estado, distrito o municipio | §11.1 | `info_needed.csv` |
| `extra_test6.py`, `escenarios_base.py` | Cargas por jurisdicción, persistencia del choque, nivel nacional | §11.2 | `extra_cargas_test.csv` |
| `cluster_test.py`, `cluster_rev.py`, `cluster_pilot.py` | Clusters geográficos y culturales; reversión del choque | §11.3 | `cluster_*.csv/txt` |
| `underlying.py`, `underlying2.py` | Estructura jurisdiccional del choque | §11.4 | - |
| `causas_mun.py`, `surge_decline.py` | Causas político-jurisdiccionales; oleada y declive | §11.5 | `surge_decline.csv` |
| `border_design.py`, `panel_events.py`, `matrix_svd.py` | Frontera estatal, eventos municipales con efectos fijos, SVD | §11.6 | `border_pairs.csv`, `panel_events.csv` |
| `offyear_local.py`, `bandas.py` | Participación municipal fuera de ciclo; bandas de incertidumbre | §11.7 | `offyear_local.csv`, `bandas.csv` |
| `extra_test7.py`, `extra_test8.py` | Casillas y geometría; ecosistema de medios del hogar | §11.8-11.9 | `extra_acceso_test.csv`, `extra_medios_test.csv` |
| `rm2022_test.py`, `alignment.py`, `alignment_pred.py` | Revocación 2022 como movilización; alineación vertical | §11.10 | `alignment_*.csv` |
| `gasto_test.py` | Gasto de campaña por distrito | §11.11 | `gasto_distrito.csv` |
| `intrayear_crime.py` | Delitos ene-may del año de la elección | §11.12 | - |
| `calendar_gob.py`, `crosswalk.py`, `denue_sections.py` | Auxiliares (calendario de gubernaturas, cruce INE-INEGI de municipios, DENUE por sección) | - | - |

## Otros directorios
- `data/raw/` (ignorado) y `data/processed/` (compartidos con el Reto 1): fuentes y tablas derivadas, regenerables.
- `web/`: prototipo web Next.js (`cd reto2_prediccion/web && npm run dev`); `public/benchmark_results.json` es de la primera versión y no refleja `reports/`.
- `_obsoleto/` (en esta carpeta): pipeline inicial con datos sintéticos (`pipeline_reto2.py`), conservado por si la app depende de su formato.

## Pendiente
Panel de participación 2025 (elección judicial) por sección en SICEE, gubernaturas 2027 por estado y el semáforo final con bandas de ±9.5 pp (calibradas con 2021). Capacitación de funcionarios de casilla y representantes de partido por distrito no aparecen publicados como base descargable (§11.13).
