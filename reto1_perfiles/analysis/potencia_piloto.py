# /// script
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Reto 1: poder estadístico de un piloto aleatorizado por sección dentro de municipio y perfil (propuesta de implementación). El ruido relevante es la variación del cambio de participación entre
secciones del mismo municipio (los choques municipales se cancelan con bloques). MDE = 2.8 × sd × sqrt(2/n) por brazo (alfa 0.05 bilateral, poder 0.80).
Run: uv run reto1_perfiles/analysis/potencia_piloto.py -> reto1_perfiles/reports/potencia_piloto.csv"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
T = pd.read_csv("reto1_perfiles/reports/tipologia_secciones.csv").set_index("sid"); s = pd.read_parquet("data/processed/perfiles_seccion.parquet"); s["g"] = s.banda.map({"18-24": "J", "25-34": "J", "35-44": "A", "45-54": "A", "55-64": "M", "65-74": "M", "75+": "E"})
def rate(y, mask=None):
    d = s[s.AELEC == y]; d = d if mask is None else d[mask(d)]; g = d.groupby("sid")[["SV", "NV"]].sum(); return (g.SV / (g.SV + g.NV)), (g.SV + g.NV)
rows = []
for nm, mk in (("Todas las personas", None), ("Jóvenes 18-34", lambda d: d.g == "J"), ("Hombres 25-44", lambda d: (d.SEXO == 0) & d.banda.isin(["25-34", "35-44"])), ("Mujeres 75+", lambda d: (d.SEXO == 1) & (d.banda == "75+"))):
    # cambio entre dos presidenciales consecutivas (2018 → 2024) como aproximación del ruido de un diseño pre-post; 2015 → 2021 para intermedias
    for lab, (a, b) in (("presidencial (2018→2024)", (2018, 2024)), ("intermedia (2015→2021)", (2015, 2021))):
        r0, n0 = rate(a, mk); r1, n1 = rate(b, mk); d = pd.concat([r1 - r0, n0.rename("n0"), n1.rename("n1")], axis=1, keys=["d", "n0", "n1"]).dropna(); d.columns = ["d", "n0", "n1"]
        d = d.join(T[["c", "EDOCVE", "MPIOCVE"]], how="inner"); d["mun"] = d.EDOCVE * 1000 + d.MPIOCVE; d["w"] = d.n0.clip(upper=2000)
        d = d[(d.n0 >= 100) & (d.n1 >= 100)]; d["dm"] = d.d - d.groupby("mun").d.transform("mean")  # variación dentro del municipio
        k = d.groupby("mun").d.transform("size"); d = d[k >= 3]; sd = float(np.sqrt((d.dm ** 2 * (k[d.index] / (k[d.index] - 1))).mean()))
        for n in (100, 250, 500, 1000): rows.append(dict(resultado=nm, ciclo=lab, secciones_por_brazo=n, sd_dentro_municipio_pp=100 * sd, MDE_pp=100 * 2.8 * sd * np.sqrt(2 / n)))
R = pd.DataFrame(rows); pd.set_option("display.width", 200); print(R.pivot_table(index=["resultado", "ciclo"], columns="secciones_por_brazo", values="MDE_pp").round(2).to_string()); print("\nsd dentro de municipio (pp):"); print(R.groupby(["resultado", "ciclo"]).sd_dentro_municipio_pp.first().round(2).to_string()); R.to_csv("reto1_perfiles/reports/potencia_piloto.csv", index=False)
