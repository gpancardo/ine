# Código del Reto 1: Cinco tipos de ciudadanía electoral

Hackathon INE 2026, eje Reto 1 (perfiles ciudadanos de participación). Repositorio completo: https://github.com/gpancardo/ine

## Contenido
| Carpeta | Qué hay |
|---|---|
| `shared/` | Descarga de datos (`download_data.py`, `download_extra.py`), construcción del panel (`build_panel.py`) y biblioteca común (`lib/`) |
| `reto1_perfiles/analysis/` | Pipeline del análisis; el orden de ejecución está en `reto1_perfiles/README.md` |
| `reto1_perfiles/reports/` | `INFORME.md` (informe técnico completo), `NARRATIVA.md` y las tablas con las que se verifican las cifras del documento técnico, las fichas y la presentación |

## Verificar las cifras sin volver a correr nada
Cada cifra de los entregables cita su tabla en `reto1_perfiles/reports/`. Las tres tablas por sección (`tipologia_secciones.csv`, `politica_secciones.csv` y `tipologia_pertenencias.csv`, 32 MB en total) no se incluyen en este paquete por tamaño y están en el repositorio.

## Reproducir desde cero
Requisitos: [uv](https://docs.astral.sh/uv/). Cada script declara sus dependencias en su encabezado; no hay que instalar nada más. Todo se ejecuta desde esta carpeta (la raíz del código):
```
uv run shared/download_data.py ; uv run shared/download_extra.py ; uv run shared/build_panel.py
# después, el pipeline de reto1_perfiles/README.md
```
El paso más lento es `rigor_perfiles.py` (bootstrap de unas 2.5 horas en una laptop). Los scripts que fijan `numpy<2` se corren con `uv run --python 3.12`.

## Fuentes y fecha de descarga
Todas son públicas y agregadas; no se usan datos personales. Se descargaron en octubre de 2026.
- **INE-DECEyEC, Conteos Censales de Participación Ciudadana 2009-2024** (sección × sexo × edad): base de la segmentación.
- **INE-INEGI, Estadísticas Censales a Escalas Geoelectorales 2020 y 2010** (ECEG): descriptores de escolaridad, lengua, conectividad y migración. Son ecológicos, es decir, describen la sección y no a las personas.
- **INE, Cartografía electoral**: marco seccional para mapas y tablero.
- **INEGI DENUE**, **SESNSP**, **CONEVAL** y resultados históricos por casilla (Magar, github.com/emagar/elecRetrns): se usan como complemento y no intervienen en la segmentación.

Los sitios del INE son aplicaciones web y sus rutas cambian. Si una descarga falla, la URL vigente se localiza en el sitio (las rutas usadas están documentadas en el encabezado de cada script de descarga). Con cada nueva publicación de la CCPC basta repetir la descarga y el pipeline para actualizar los perfiles.
