# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "matplotlib"]
# ///
"""Mapa de los cinco perfiles con la paleta de la presentación (morado INE), sin títulos: los nombres van en el HTML.
Run (desde la raíz): uv run --python 3.12 entrega/src/mapa_presentacion.py  ->  entrega/src/mapa_perfil_{1..5}.png"""
import os, sys
from pathlib import Path
import pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[2]; os.chdir(ROOT); sys.path.insert(0, str(ROOT / "shared" / "lib")); import common as c
MORADO, LILA = (79 / 255, 40 / 255, 117 / 255), (168 / 255, 125 / 255, 209 / 255)
T = pd.read_csv("reto1_perfiles/reports/tipologia_secciones.csv").set_index("sid")
geo = c.load_geo(); cen = pd.DataFrame({"x": geo.geometry.centroid.x, "y": geo.geometry.centroid.y}, index=geo.index).join(T[["c"]], how="inner")
for k in range(5):
    fig, a = plt.subplots(figsize=(6, 3.9))
    a.scatter(cen.x, cen.y, s=.5, color="#ebe6f0", linewidths=0, rasterized=True)
    d = cen[cen.c == k]; a.scatter(d.x, d.y, s=1.4, color=MORADO, linewidths=0, rasterized=True)
    a.set_aspect("equal"); a.axis("off"); fig.savefig(f"entrega/src/mapa_perfil_{k + 1}.png", dpi=150, facecolor="white", bbox_inches="tight", pad_inches=0); plt.close(fig)
print("ok")
