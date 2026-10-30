# /// script
# dependencies = ["pandas", "pyarrow", "scikit-learn", "lightgbm"]
# ///
"""Backtest rolling-origin sobre el panel largo 1994-2024 (acta-based). Run: uv run analysis/long_backtest.py"""
import os, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); os.chdir(Path(__file__).resolve().parents[2])
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from lightgbm import LGBMRegressor

L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994]
W = L.pivot(index="sid", columns="year", values="abst_m").clip(0, 1); LN = L.pivot(index="sid", columns="year", values="lisnom")
nat = W.mean(); REL = W - nat
YEARS = sorted(W.columns); MID = {1997, 2003, 2009, 2015, 2021, 2027}
def build(T, nlag=3):
    ys = [y for y in YEARS if y <= T - 3]; pres = [y for y in ys if y not in MID][::-1]; mid = [y for y in ys if y in MID][::-1]
    d = pd.DataFrame(index=W.index); d["T"] = T; d["y"] = REL[T] if T in REL else np.nan; d["ln"] = LN[T] if T in LN else np.nan
    for i in range(nlag):
        d[f"P{i+1}"] = REL[pres[i]] if len(pres) > i else np.nan; d[f"M{i+1}"] = REL[mid[i]] if len(mid) > i else np.nan
    d["is_mid"] = float(T in MID); d["P1_mid"] = d.P1 * d.is_mid; d["M1_mid"] = d.M1 * d.is_mid
    return d.dropna(subset=["P1", "M1"])
TS = [2003, 2006, 2009, 2012, 2015, 2018, 2021, 2024]; D = {T: build(T) for T in TS}
for T in TS: D[T] = D[T][(D[T].ln >= 100) | D[T].ln.isna()]
FEAT = {"P1,M1": ["P1", "M1"], "P1,M1,P2,M2": ["P1", "M1", "P2", "M2"], "+P3,M3": ["P1", "M1", "P2", "M2", "P3", "M3"], "+tipo": ["P1", "M1", "P2", "M2", "is_mid", "P1_mid", "M1_mid"], "+P3,M3,tipo": ["P1", "M1", "P2", "M2", "P3", "M3", "is_mid", "P1_mid", "M1_mid"]}
lin = lambda: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(10.0))
r2 = lambda y, p: 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
print("elección | n | R² Const0 | R² P1 | R² M1 | R² (mejor naive mismo-tipo) |", " | ".join(f"Ridge[{k}] todas / últimas3" for k in list(FEAT)[:1]))
rows = []
for T in (2009, 2012, 2015, 2018, 2021, 2024):
    te = D[T][D[T].y.notna()]; prev = [t for t in TS if t < T and t >= 2003]  # transiciones de entrenamiento disponibles (objetivos pasados)
    out = dict(T=T, n=len(te), const0=r2(te.y, 0 * te.y), P1=r2(te.y, te.P1), M1=r2(te.y, te.M1))
    for lab, tt in (("todas", prev), ("ult3", prev[-3:])):
        tr = pd.concat([D[t] for t in tt]); tr = tr[tr.y.notna()]
        for fk, cols in FEAT.items():
            m = lin().fit(tr[cols].values, tr.y.values); out[f"{fk}|{lab}"] = r2(te.y, m.predict(te[cols].values))
    out["ntrain_T"] = len(prev); rows.append(out)
R = pd.DataFrame(rows).set_index("T"); pd.set_option("display.width", 250); print(R.round(3).T.to_string())
R.to_csv("reto2_prediccion/reports/long_backtest.csv")
# oráculo: pesos del propio año
orc = {T: LinearRegression().fit(D[T][D[T].y.notna()][["P1", "M1"]].fillna(0), D[T][D[T].y.notna()].y).score(D[T][D[T].y.notna()][["P1", "M1"]].fillna(0), D[T][D[T].y.notna()].y) for T in (2009, 2012, 2015, 2018, 2021, 2024)}
print("R² oráculo (pesos del propio año, P1,M1):", {k: round(v, 3) for k, v in orc.items()})
cf = {T: LinearRegression().fit(D[T][D[T].y.notna()][["P1", "M1"]].fillna(0), D[T][D[T].y.notna()].y).coef_.round(2).tolist() for T in TS if D[T].y.notna().any()}
print("coeficientes [P1, M1] por elección:", cf)
