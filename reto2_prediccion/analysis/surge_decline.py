# /// script
# dependencies = ["pandas", "pyarrow", "statsmodels"]
# ///
"""Oleada y declive: ¿la fuerza del partido ganador de la última presidencial predice una sobre-abstención en la intermedia siguiente, en todos los ciclos?
Panel largo (Magar). Dentro de cada elección T: y ~ P1 + M1 + [fuerza del ganador en P1] (+ su ganancia vs. la presidencial previa). Run: uv run analysis/surge_decline.py"""
import os
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
os.chdir(Path(__file__).resolve().parents[2])
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994].copy()
vc = [c for c in L if c.startswith("v_") and c != "v_edosecn"]; ORDER = ["morena", "pri", "pan", "prd"]
bl = {c: next((p for p in ORDER if p in c), "otro") for c in vc}
B = pd.DataFrame({p: L[[c for c in vc if bl[c] == p]].sum(axis=1) for p in ORDER}); S = B.div(B.sum(axis=1).replace(0, np.nan), axis=0); S["sid"], S["year"] = L.sid.values, L.year.values
W = L.pivot(index="sid", columns="year", values="abst_m").clip(0, 1); LN = L.pivot(index="sid", columns="year", values="lisnom"); REL = W - W.mean()
SH = {p: S.pivot(index="sid", columns="year", values=p) for p in ORDER}
WIN = {1994: "pri", 2000: "pan", 2006: "pan", 2012: "pri", 2018: "morena", 2024: "morena"}  # partido/bloque del presidente electo
MID = {1997, 2003, 2009, 2015, 2021, 2027}; rows = []
for T in (2003, 2006, 2009, 2012, 2015, 2018, 2021, 2024):
    ys = [y for y in W.columns if y <= T - 3]; pres = [y for y in ys if y not in MID][::-1]; mid = [y for y in ys if y in MID][::-1]
    if len(pres) < 2 or not mid: continue
    p1, p2, party = pres[0], pres[1], WIN[pres[0]]
    d = pd.DataFrame({"y": REL[T], "P1": REL[p1], "M1": REL[mid[0]], "sw": SH[party][p1], "dsw": SH[party][p1] - SH[party][p2], "ln": LN[T]}).dropna().query("ln >= 100")
    d = d[d.sw.between(0, 1)]; z = lambda s: (s - s.mean()) / s.std(); d["sw"], d["dsw"] = z(d.sw), z(d.dsw)
    for nm, cols in (("fuerza", ["sw"]), ("fuerza+ganancia", ["sw", "dsw"])):
        m = sm.OLS(d.y, sm.add_constant(d[["P1", "M1"] + cols])).fit(cov_type="cluster", cov_kwds={"groups": d.index // 10000})
        rows.append(dict(T=T, tipo="intermedia" if T in MID else "presidencial", ganador_P1=f"{party} ({p1})", spec=nm, **{f"{c} (pp/SD)": m.params[c] * 100 for c in cols}, t_sw=m.tvalues["sw"], n=len(d)))
R = pd.DataFrame(rows); pd.set_option("display.width", 220); print(R.round(2).to_string(index=False)); R.to_csv("reto2_prediccion/reports/surge_decline.csv", index=False)
