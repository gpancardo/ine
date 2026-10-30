# /// script
# dependencies = ["pandas", "pyarrow", "scikit-learn", "lightgbm"]
# ///
"""¿Aporta la composición partidista (voto por bloque, margen, nulos) de las elecciones pasadas a la predicción ex ante?
Mismo esquema que long_backtest.py (rolling-origin, entrena solo con objetivos pasados, sin 2015). Run: uv run analysis/party_test.py"""
import os, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); os.chdir(Path(__file__).resolve().parents[2])
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from lightgbm import LGBMRegressor

L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994].copy()
vc = [c for c in L if c.startswith("v_") and c != "v_edosecn"]
ORDER = ["morena", "pri", "pan", "prd"]  # ponytail: coalición se asigna al primer partido nombrado; aproximación
bloc = {}
for c in vc:
    bloc[c] = next((p for p in ORDER if p in c), "otro")
B = pd.DataFrame({p: L[[c for c in vc if bloc[c] == p]].sum(axis=1) for p in ORDER + ["otro"]})
tot = B.sum(axis=1).replace(0, np.nan)
S = (B.div(tot, axis=0)).add_prefix("s_")
top = np.sort(S[["s_" + p for p in ORDER]].values, axis=1)
L = pd.concat([L[["sid", "year", "abst_m", "lisnom"]], S], axis=1)
L["margin"] = top[:, -1] - top[:, -2]
PF = ["s_morena", "s_pri", "s_pan", "s_prd", "s_otro", "margin"]
W = L.pivot(index="sid", columns="year", values="abst_m").clip(0, 1); LN = L.pivot(index="sid", columns="year", values="lisnom")
PW = {f: L.pivot(index="sid", columns="year", values=f) for f in PF}
nat = W.mean(); REL = W - nat
YEARS = sorted(W.columns); MID = {1997, 2003, 2009, 2015, 2021, 2027}


def build(T):
    ys = [y for y in YEARS if y <= T - 3]; pres = [y for y in ys if y not in MID][::-1]; mid = [y for y in ys if y in MID][::-1]
    d = pd.DataFrame(index=W.index); d["T"] = T; d["y"] = REL[T]; d["ln"] = LN[T]
    for i in range(2):
        d[f"P{i+1}"] = REL[pres[i]]; d[f"M{i+1}"] = REL[mid[i]]
    d["is_mid"] = float(T in MID); d["P1_mid"] = d.P1 * d.is_mid; d["M1_mid"] = d.M1 * d.is_mid
    for f in PF:
        d[f"{f}_P1"] = PW[f][pres[0]]; d[f"{f}_M1"] = PW[f][mid[0]]
        d[f"{f}_swing"] = PW[f][pres[0]] - PW[f][pres[1]]  # cambio entre las dos últimas presidenciales
    last = max(ys); d["lastyr_mid"] = float(last in MID)
    return d.dropna(subset=["P1", "M1", "y"]).query("ln >= 100")


TS = [2006, 2009, 2012, 2018, 2021, 2024]; D = {T: build(T) for T in TS}
REF = ["P1", "M1", "P2", "M2", "is_mid", "P1_mid", "M1_mid"]
parts = {"partido P1/M1": [f"{f}_{k}" for f in PF for k in ("P1", "M1")], "swing": [f"{f}_swing" for f in PF]}
sets = {"REF": REF, "+ partido": REF + parts["partido P1/M1"], "+ partido+swing": REF + parts["partido P1/M1"] + parts["swing"]}
lin = lambda: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(10.0))
lgb = lambda: make_pipeline(SimpleImputer(strategy="median"), LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=31, min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=8))
r2 = lambda y, p: 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
rows = []
for T in (2009, 2012, 2018, 2021, 2024):
    tr = pd.concat([D[t] for t in TS if 2006 <= t <= T - 3 and t != 2015]); te = D[T]
    for n, cs in sets.items():
        for mn, mk in (("Ridge", lin), ("LGBM", lgb)):
            rows.append(dict(T=T, set=n, model=mn, r2=r2(te.y, mk().fit(tr[cs].values, tr.y.values).predict(te[cs].values)), ntrain=len(tr)))
R = pd.DataFrame(rows).pivot_table(index=["set", "model"], columns="T", values="r2"); print(R.round(3).to_string()); R.to_csv("reto2_prediccion/reports/party_test.csv")
