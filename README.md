# Hackathon INE 2026: Datos que construyen democracia

Datos base: Conteos Censales de Participación Ciudadana 2009-2024 (INE-DECEyEC), más ECEG 2020/2010, DENUE, SESNSP, CONEVAL, resultados históricos por casilla (Magar) y fuentes del INE. Cada reto tiene su carpeta; lo común vive en `shared/` y `data/`.

| Carpeta | Contenido | Entrada |
|---|---|---|
| `shared/` | Descargas (`download_data.py`, `download_extra.py`), construcción del panel (`build_panel.py`) y biblioteca común (`lib/`) | - |
| `reto1_perfiles/` | **Reto 1, perfiles ciudadanos de participación**: tipología de secciones por nivel, brecha de género y brecha de jóvenes, validada en el tiempo, con votos recuperables por grupo, municipio y distrito | `reto1_perfiles/README.md`, `reports/INFORME.md` |
| `reto2_prediccion/` | **Reto 2, predicción y escenarios de riesgo**: modelo, benchmark honesto, 13 familias de datos probadas, bandas de incertidumbre, prototipo web | `reto2_prediccion/README.md`, `reports/RESULTADOS.md` |
| `data/` | `raw/` (ignorado por git) y `processed/` | - |

## Orden general (desde la raíz)
```
uv run shared/download_data.py ; uv run shared/download_extra.py ; uv run shared/build_panel.py
# después, el pipeline de cada reto (ver su README)
```
Los scripts se ejecutan siempre desde la raíz del repo; las rutas a `data/` y a la biblioteca compartida se resuelven desde la ubicación del script.

## Estado (2026-10-12)
- Reto 2: cerrado en lo analítico (R² honesto 0.62 en 2021 y 0.71 en 2024; ver conclusión en su README). Falta el semáforo con bandas y los dos escenarios.
- Reto 1: tipología de 5 perfiles validada con ventanas disjuntas, potencial por municipio con IC, 7 figuras e informe; pendientes y criterios de decisión en `reto1_perfiles/PLAN.md` (comparación sobre el perfil completo, descriptores del INEGI, cohortes, tablero).
- Registro de equipos: hasta el 15 de octubre de 2026; entrega de proyectos: 31 de octubre, 23:59.
