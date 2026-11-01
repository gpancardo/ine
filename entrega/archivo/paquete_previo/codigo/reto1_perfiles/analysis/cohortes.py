# /// script
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Reto 1 (E6): cohortes aproximadas. Compara 18-24 años en la elección t con 25-34 años en t+6 (misma familia de elección: intermedia→intermedia,
presidencial→presidencial, porque el tipo de elección cambia la participación). Es aproximación: la banda 25-34 en t+6 incluye parte de la misma generación
y parte de otra; por eso se reporta como diferencia de bandas, no como seguimiento individual. Desagregado por sexo y por perfil (tipologia_secciones.csv).
Salida: reto1_perfiles/reports/cohortes.csv. Run: uv run reto1_perfiles/analysis/cohortes.py"""
import os
from pathlib import Path
import numpy as np, pandas as pd
os.chdir(Path(__file__).resolve().parents[2])
s = pd.read_parquet("data/processed/perfiles_seccion.parquet")
perfil = pd.read_csv("reto1_perfiles/reports/tipologia_secciones.csv", usecols=["sid", "c"]).set_index("sid").c
def part(d): g = d[["SV", "NV"]].sum(); return g.SV / (g.SV + g.NV)
rows = []
for t, t2 in [(2009, 2015), (2012, 2018), (2015, 2021), (2018, 2024)]:
    for sexo, nombre in [(None, "total"), (0, "hombres"), (1, "mujeres")]:
        base = s if sexo is None else s[s.SEXO == sexo]
        j = base[(base.AELEC == t) & (base.banda == "18-24")].groupby("sid")[["SV", "NV"]].sum()
        k = base[(base.AELEC == t2) & (base.banda == "25-34")].groupby("sid")[["SV", "NV"]].sum()
        idx = j.index.intersection(k.index); j, k = j.loc[idx], k.loc[idx]
        p0 = j.SV / (j.SV + j.NV); p1 = k.SV / (k.SV + k.NV)
        r = dict(cohorte_entrada=t, sexo=nombre, perfil="todos", t_mas6=t2, p_18_24=part(j), p_25_34_t6=part(k), cambio_pp=100 * (part(k) - part(j)), secciones=len(idx))
        rows.append(r)
        for c in sorted(perfil.dropna().unique()):
            ids = idx.intersection(perfil[perfil == c].index)
            if len(ids) == 0: continue
            rows.append(dict(cohorte_entrada=t, sexo=nombre, perfil=int(c), t_mas6=t2, p_18_24=part(j.loc[ids]), p_25_34_t6=part(k.loc[ids]), cambio_pp=100 * (part(k.loc[ids]) - part(j.loc[ids])), secciones=len(ids)))
C = pd.DataFrame(rows)
C = C.round(4); C.to_csv("reto1_perfiles/reports/cohortes.csv", index=False)
pd.set_option("display.width", 220); print(C[C.sexo == "total"].to_string(index=False)); print(C[C.perfil == "todos"].to_string(index=False))
