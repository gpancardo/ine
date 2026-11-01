# Hackathon INE 2026: Datos que construyen democracia

Datos base: Conteos Censales de Participación Ciudadana 2009-2024 (INE-DECEyEC), más ECEG 2020/2010, DENUE, SESNSP, CONEVAL, resultados históricos por casilla (Magar) y fuentes del INE. Cada reto tiene su carpeta; lo común vive en `shared/` y `data/`.

| Carpeta | Contenido | Entrada |
|---|---|---|
| `shared/` | Descargas (`download_data.py`, `download_extra.py`), construcción del panel (`build_panel.py`) y biblioteca común (`lib/`) | - |
| `reto1_perfiles/` | **Reto 1, perfiles ciudadanos de participación**: tipología de secciones por nivel, brecha de género y brecha de jóvenes, validada en el tiempo, con votos recuperables por grupo, municipio y distrito | `reto1_perfiles/README.md`, `reports/INFORME.md` |
| `reto2_prediccion/` | *(No entregado; exploratorio)* **Reto 2, predicción y escenarios de riesgo**: modelo, benchmark honesto, 13 familias de datos probadas, bandas de incertidumbre, prototipo web | `reto2_prediccion/README.md`, `reports/RESULTADOS.md` |
| `entrega/` | `Anahuacalli/`: carpeta final de entrega del Reto 1; `src/`: fuentes HTML de los entregables; `archivo/`: versiones previas | `entrega/Anahuacalli/00_LEEME.txt` |
| `data/` | `raw/` (ignorado por git) y `processed/` | - |

## Orden general (desde la raíz)
```
uv run shared/download_data.py ; uv run shared/download_extra.py ; uv run shared/build_panel.py
# después, el pipeline de cada reto (ver su README)
```
Los scripts se ejecutan siempre desde la raíz del repo; las rutas a `data/` y a la biblioteca compartida se resuelven desde la ubicación del script.

## Estado (2026-10-30): se entrega el Reto 1
- **Entrega: Reto 1.** La convocatoria permite un solo eje por equipo; las razones de la elección están en `reto1_perfiles/PLAN.md` §2. Los entregables (documento técnico, fichas, presentación, tablero y paquete .zip) están en `entrega/`, y sus fuentes HTML en `entrega/src/`.
- **Reto 2: no forma parte de la entrega.** Se conserva como trabajo exploratorio (R² honesto de 0.62 en 2021 y 0.71 en 2024). Parte de sus resultados se aprovechan en el Reto 1: la persistencia de rasgos y la lección de que la intermitencia es nacional.
