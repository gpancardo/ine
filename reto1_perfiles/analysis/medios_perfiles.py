# /// script
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Reto 1: ecosistema de medios y conectividad de cada perfil (Censo 2020 por sección, ponderado por lista nominal): radio, TV, TV de paga, celular, internet, computadora, teléfono fijo y
hogares sin radio ni TV; adopción de internet y celular 2010→2020. Es un descriptor ecológico (hogares de la sección, no personas): sirve para elegir canales, no para inferir conducta individual.
Run: uv run reto1_perfiles/analysis/medios_perfiles.py -> reto1_perfiles/reports/medios_perfiles.csv"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
pd.set_option("display.width", 220)
def media(fname, den):
    e = pd.read_parquet(f"data/processed/{fname}.parquet"); e.columns = [x.strip() for x in e.columns]; e = e.rename(columns={"entidad": "ENTIDAD", "seccion": "SECCION"})
    num = e[[x for x in e.columns if x.startswith("VPH_") or x in ("ENTIDAD", "SECCION", den)]].apply(pd.to_numeric, errors="coerce"); d = num[den].replace(0, np.nan)
    f = pd.DataFrame({"sid": num.ENTIDAD * 10000 + num.SECCION})
    for k in ("RADIO", "TV", "STVP", "CEL", "TELEF", "INTER", "PC", "SINRTV"):
        if f"VPH_{k}" in num: f[k.lower()] = num[f"VPH_{k}"] / d
    return f.drop_duplicates("sid").set_index("sid")
m20, m10 = media("eceg", "TVIVPARHAB"), media("eceg2010", "TVIVPARH")
T = pd.read_csv("reto1_perfiles/reports/tipologia_secciones.csv").set_index("sid")
X = m20.reindex(T.index).add_suffix("_2020").join(m10.reindex(T.index)[["inter", "cel", "pc"]].add_suffix("_2010")); X["c"] = T.c; X["ln24"] = T.ln24
X["d_internet"] = X.inter_2020 - X.inter_2010; X["d_celular"] = X.cel_2020 - X.cel_2010
cols = ["radio_2020", "tv_2020", "stvp_2020", "cel_2020", "inter_2020", "pc_2020", "telef_2020", "sinrtv_2020", "d_internet", "d_celular"]
wm = lambda g, c: np.average(g[c].dropna(), weights=g.loc[g[c].notna(), "ln24"])
R = pd.DataFrame({c: X.groupby("c").apply(lambda g, c=c: wm(g, c)) for c in cols}); R.loc["nacional"] = [wm(X, c) for c in cols]; R.to_csv("reto1_perfiles/reports/medios_perfiles.csv")
print((R * 100).round(0).rename(columns=lambda c: c.replace("_2020", "")).to_string()); print("\nperfil:", {i: L.NOMBRES[i] for i in range(5)})
