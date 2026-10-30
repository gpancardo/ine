# /// script
# dependencies = ["pandas", "pyarrow", "scikit-learn", "lightgbm"]
# ///
"""Panel largo (1994-2024): features de perfil histórico por sección, entrenando con muchas transiciones. Run: uv run analysis/extra_test5.py"""
import os, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); os.chdir(Path(__file__).resolve().parents[2])
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from lightgbm import LGBMRegressor
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994]
W = L.pivot(index="sid", columns="year", values="abst_m").clip(0, 1); LN = L.pivot(index="sid", columns="year", values="lisnom"); REL = W - W.mean()
YR = sorted(W.columns); MID = {1997, 2003, 2009, 2015, 2021, 2027}

def build(T):
    ys = [y for y in YR if y <= T - 3]; pres = [y for y in ys if y not in MID][::-1]; mid = [y for y in ys if y in MID][::-1]
    same = [y for y in ys if (y in MID) == (T in MID)]; oth = [y for y in ys if y not in same]
    d = pd.DataFrame(index=W.index); d["T"] = T; d["y"] = REL[T]; d["ln"] = LN[T]
    for i in range(2): d[f"P{i+1}"] = REL[pres[i]]; d[f"M{i+1}"] = REL[mid[i]]
    mid_ = float(T in MID); d["is_mid"] = mid_; d["P1_mid"] = d.P1 * mid_; d["M1_mid"] = d.M1 * mid_
    d["h_same"] = REL[same].mean(1); d["h_oth"] = REL[oth].mean(1); d["h_sd"] = REL[ys].std(1); d["h_same_sd"] = REL[same].std(1)
    gaps = [REL[m] - REL[m - 3] for m in ys if m in MID and (m - 3) in ys]; d["h_gap"] = pd.concat(gaps, axis=1).mean(1)
    d["h_same1"] = REL[same[-1]] if same else np.nan  # última del mismo tipo
    return d.dropna(subset=["P1", "M1", "y"]).query("ln >= 100")
TS = [2006, 2009, 2012, 2015, 2018, 2021, 2024]; D = {T: build(T) for T in TS}
REF = ["P1", "M1", "P2", "M2", "is_mid", "P1_mid", "M1_mid"]; HIST = ["h_same", "h_oth", "h_sd", "h_same_sd", "h_gap"]
sets = {"REF": REF, "+ hist": REF + HIST}
lin = lambda: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(10.0))
lgb = lambda: make_pipeline(SimpleImputer(strategy="median"), LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=31, min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=8))
r2 = lambda y, p: 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
rows = []
for T in (2012, 2018, 2021, 2024):
    avail = [t for t in TS if t <= T - 3]
    for trn, tt in (("últimas2 sin 2015", [t for t in avail if t != 2015][-2:]), ("todas sin 2015", [t for t in avail if t != 2015]), ("todas", avail)):
        if not tt: continue
        tr = pd.concat([D[t] for t in tt]); te = D[T]
        for n, cs in sets.items():
            for mn, mk in (("Ridge", lin), ("LGBM", lgb)):
                rows.append(dict(T=T, train=trn, set=n, model=mn, r2=r2(te.y, mk().fit(tr[cs].values, tr.y.values).predict(te[cs].values))))
R = pd.DataFrame(rows).pivot_table(index=["train", "model", "set"], columns="T", values="r2"); print(R.round(3).to_string()); R.to_csv("reto2_prediccion/reports/extra_hist_largo.csv")
