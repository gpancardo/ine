# /// script
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Reto 1: panorama nacional por edad y sexo (ciclo de vida, brecha de género, jóvenes, adultos mayores, cohortes). Run: uv run reto1_perfiles/analysis/eda_perfiles.py"""
import os, json
from pathlib import Path
import numpy as np, pandas as pd
os.chdir(Path(__file__).resolve().parents[2]); pd.set_option("display.width", 220)
e = pd.read_parquet("data/processed/perfiles_edad.parquet"); s = pd.read_parquet("data/processed/perfiles_seccion.parquet")
rate = lambda d: d.SV.sum() / (d.SV.sum() + d.NV.sum())
print("== participación nacional (SV/(SV+NV)) por elección y sexo (0=H, 1=M)")
print(pd.DataFrame({y: {sx: rate(g[g.SEXO == sx]) for sx in (0, 1)} | {"todos": rate(g)} for y, g in s.groupby("AELEC")}).round(3).to_string())
print("\n== participación por banda de edad y elección (ambos sexos)")
t = s.groupby(["AELEC", "banda"]).apply(rate).unstack("banda"); print(t.round(3).to_string())
print("\n== brecha de género (M−H, puntos) por banda y elección")
g = s.groupby(["AELEC", "banda", "SEXO"]).apply(rate).unstack("SEXO"); print(((g[1] - g[0]) * 100).unstack("banda").round(1).to_string())
print("\n== quién falta en 2024 y 2021: reparto de los no votantes por banda y sexo (%, de NV total)")
for y in (2021, 2024):
    d = s[s.AELEC == y]; nv = d.groupby(["banda", "SEXO"]).NV.sum(); ln = d.groupby(["banda", "SEXO"]).LN.sum(); print(y, "NV total:", int(nv.sum()), "| LN:", int(ln.sum()))
    print(pd.DataFrame({"% de no votantes": (nv / nv.sum() * 100).round(1), "% de la LN": (ln / ln.sum() * 100).round(1)}).unstack("SEXO").to_string())
print("\n== diferencia presidencial−intermedia por banda (2024−2021 y 2018−2015, puntos): intermitencia")
dm = (t.loc[2024] - t.loc[2021]) * 100; dm2 = (t.loc[2018] - t.loc[2015]) * 100; print(pd.DataFrame({"2024−2021": dm, "2018−2015": dm2}).round(1).T.to_string())
print("\n== cohortes: participación de quienes tenían 18-19 años en cada presidencial, y a los 21-22 / 24-25 en la intermedia siguiente (≈3 años después)")
e["rate"] = e.SV / (e.SV + e.NV)
def p(y, lo, hi, sex=None): d = e[(e.AELEC == y) & e.EDAD.between(lo, hi)]; d = d if sex is None else d[d.SEXO == sex]; return rate(d)
for y in (2009, 2012, 2015, 2018, 2021, 2024):
    print(y, "18-19:", round(p(y, 18, 19), 3), "| 20-24:", round(p(y, 20, 24), 3), "| 25-29:", round(p(y, 25, 29), 3), "| 65+:", round(p(y, 65, 120), 3), "| 75+:", round(p(y, 75, 120), 3))
print("\n== por tipo de sección (U/M/R) 2024 y 2021")
for y in (2021, 2024):
    print(y, {tp: round(rate(e[(e.AELEC == y) & (e.TIPOSEC == tp)]), 3) for tp in "UMR"})
