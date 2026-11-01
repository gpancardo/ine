# /// script
# dependencies = ["requests"]
# ///
"""Descarga datos oficiales a data/raw/ (idempotente).  Run: uv run shared/download_data.py
Fuentes (URLs descubiertas inspeccionando ine.mx y cartografia.ine.mx con navegador headless, oct-2026):
  1. INE Conteos Censales de Participación 2009-2024 (sección x sexo x edad: LN, SV, NV)
  2. INE-INEGI Estadísticas Censales a Escalas Geoelectorales 2020 (ECEG, 227 indicadores por sección)
  3. INE Cartografía: shapefile de secciones (marco seccional ECEG corte 2021)
Si INE cambia las rutas, re-descubrirlas con un navegador (ver README de cada sección en el sitio)."""
import sys
from pathlib import Path
import requests

RAW = Path("data/raw")
INE = "https://www.ine.mx/wp-content/uploads"
CARTO = "https://cartografia.ine.mx"
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0"


def get(url, dest: Path):
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = S.get(url, timeout=300, stream=True)
    if r.status_code != 200:
        sys.exit(f"[ERROR] {r.status_code} {url}  -> ruta cambiada; descárgalo a mano a {dest}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with open(tmp, "wb") as f:
        for ch in r.iter_content(1 << 20):
            f.write(ch)
    tmp.rename(dest)
    print("ok", dest, f"{dest.stat().st_size / 1e6:.1f} MB")


def main():
    for y in (2009, 2012, 2015, 2018, 2021):
        get(f"{INE}/2022/04/DatosAbiertos_DECEyEC_ConteosCensales{y}.zip", RAW / "conteos" / f"{y}.zip")
    get(f"{INE}/2025/08/DatosAbiertos_DECEyEC_ConteosCensales2024.zip", RAW / "conteos" / "2024.zip")
    get(f"{INE}/2025/06/Manual-Conteos-Censales-2009-2024.pdf", RAW / "conteos" / "manual.pdf")

    for f in S.get(f"{CARTO}/sige8/api/estadisticos?producto=ECEG&corte=2020", timeout=60).json():
        get(f"{CARTO}/mapoteca/{f['path']}{f['archivo']}", RAW / "eceg" / f["archivo"])
    for e in range(1, 33):
        for f in S.get(f"{CARTO}/sige8/api/estadisticos/marcoseccional?producto=ECEG&corte=2021&entidad={e}", timeout=60).json():
            get(f"{CARTO}/mapoteca/{f['path']}{f['archivo']}", RAW / "shp" / f["archivo"])


if __name__ == "__main__":
    main()
