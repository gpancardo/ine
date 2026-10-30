# Reto 1: perfiles de participación (segmentación enfocada a política pública)

Informe: `reports/INFORME.md`. Figuras: `reports/fig/`. Tablas: `reports/*.csv`. Pendientes y criterios de decisión: `PLAN.md`.

Orden de ejecución (desde la raíz del repo, después de `shared/download_data.py` y `shared/build_panel.py`):
```
uv run reto1_perfiles/analysis/build_perfiles.py          # participación por sección × sexo × grupo de edad (data/processed/perfiles_*.parquet)
uv run reto1_perfiles/analysis/eda_perfiles.py            # panorama nacional por edad y sexo
uv run reto1_perfiles/analysis/confiabilidad_rasgos.py    # persistencia de cada rasgo entre ventanas disjuntas (decide qué rasgos agrupan)
uv run reto1_perfiles/analysis/tipologia.py               # rasgos por sección (tipologia_features.parquet) y diagnóstico de k
uv run reto1_perfiles/analysis/elegir_k.py                # k por validez temporal y estabilidad; IC por remuestreo de municipios
uv run reto1_perfiles/analysis/tipologia_final.py         # k=5, caracterización (perfiles, curvas, historial, regiones, contexto político)
uv run reto1_perfiles/analysis/reglas_segmentos.py        # reglas explícitas que reproducen la segmentación
uv run reto1_perfiles/analysis/validar_tipologia.py       # validación temporal (2009-2018 → 2024)
uv run reto1_perfiles/analysis/comparar_segmentaciones.py # K-means vs árbol supervisado, fuera de ventana y de entidad
uv run reto1_perfiles/analysis/comparar_algoritmos.py     # mezcla gaussiana, arquetipos, municipal, perfil de 14 celdas (E1 del plan)
uv run reto1_perfiles/analysis/robustez_tipologia.py      # nulo sin grupos, sensibilidad a encogimiento y umbrales, algoritmos alternativos
uv run reto1_perfiles/analysis/medios_perfiles.py         # radio, TV, internet, celular por perfil
uv run reto1_perfiles/analysis/migracion_hipotesis.py     # prueba de la hipótesis de emigración masculina con el censo
uv run reto1_perfiles/analysis/politica_publica.py        # votos recuperables por perfil, municipio y distrito (IC por remuestreo)
uv run reto1_perfiles/analysis/descriptores_sexo.py      # E4: descriptores del ECEG por sexo y perfil
uv run reto1_perfiles/analysis/diferenciacion_perfiles.py # E1b: η² por eje, distancias entre perfiles, fronteras
uv run reto1_perfiles/analysis/cohortes.py                # E6: 18-24 en t vs 25-34 en t+6 (mismo tipo de elección)
uv run reto1_perfiles/analysis/pertenencias.py            # E2/E3: pertenencias suaves por sección (arquetipos)
uv run reto1_perfiles/analysis/acciones_perfiles.py       # a quién (celdas sexo×edad) y dónde (distritos) por perfil → reports/NARRATIVA.md
uv run reto1_perfiles/analysis/rigor_perfiles.py 100    # bootstrap: ruido vs señal, persistencia por jurisdicción, aporte sobre estado/municipio, confianza de asignación, IC de contrastes (~25 min)
uv run reto1_perfiles/analysis/figuras.py                 # figuras 1 a 7
uv run reto1_perfiles/analysis/tablero.py                 # E8: reports/tablero.html (autocontenido; requiere politica_publica.py y rigor_perfiles.py)
```
`tip_lib.py` define los rasgos y los nombres de los perfiles; reutiliza la biblioteca de `shared/lib/`. `comparar_algoritmos.py` usa `numpy<2` (dependencia de `py_pcha`), declarado en su encabezado.
