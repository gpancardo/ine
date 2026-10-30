# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""¿Clusters geográfico-culturales (definidos sin info del año objetivo) capturan choques persistentes?
Por clustering: (i) R² si se conociera el choque medio del cluster en T (techo), (ii) corr del choque 2021->2024, (iii) R² 2024 trasladando el choque 2021. Run: uv run analysis/cluster_test.py"""
import os, sys, pickle
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import harness as H, common as c
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb")); geo = c.load_geo()
r2 = lambda y, p: 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
xy = np.c_[geo.geometry.centroid.x, geo.geometry.centroid.y]; xy = pd.DataFrame(xy, index=geo.index, columns=["x", "y"])
census = c.eceg_features().drop(columns=["pobtot"]); CUL = ["pct_indigena", "pct_sin_relig", "graproes", "pct_analf", "pct_nac_otra_ent", "pct_soltero", "pct_internet", "pct_piso_tierra", "pct_auto", "pct_sin_servsalud" if False else "sin_servsalud", "pct_65mas", "pct_0_14", "hacinamiento"]
base = D[D["T"] == 2024].index.intersection(D[D["T"] == 2021].index).intersection(xy.index).intersection(census.index)
Z = lambda df: pd.DataFrame(StandardScaler().fit_transform(df.fillna(df.median())), index=df.index, columns=df.columns)
xyz, cul = Z(xy.loc[base]), Z(census.loc[base, CUL])
L = pd.read_parquet("data/processed/long_magar.parquet"); W = L[L.year.between(1994, 2018)].pivot(index="sid", columns="year", values="abst_m").clip(0, 1); W = W - W.mean()
tra = Z(W.reindex(base).fillna(0))  # trayectoria hasta 2018, común a ambos folds (sin 2021/2024)
specs = {}
for k in (32, 100, 300): specs[f"geo k={k}"] = (xyz.values, k)
for k in (20, 100): specs[f"cultural k={k}"] = (cul.values, k)
for k in (100, 300): specs[f"geo+cultural k={k}"] = (np.c_[xyz.values * 3, cul.values], k)
for k in (50, 200): specs[f"trayectoria k={k}"] = (tra.values, k)
for k in (100,): specs[f"geo+cult+trayectoria k={k}"] = (np.c_[xyz.values * 3, cul.values, tra.values], k)
te = {}
for T in (2021, 2024):
    t = D[(D["T"] == T) & D.y_rel.notna()].loc[lambda d: d.index.isin(base)].copy(); t["p"] = P[("Ridge", T)].reindex(t.index); t = t.dropna(subset=["p"]); t["res"] = t.y_rel - t.p; te[T] = t
com = te[2021].index.intersection(te[2024].index)
rows = []
for nm, (X, k) in specs.items():
    lab = pd.Series(MiniBatchKMeans(k, n_init=3, random_state=0, batch_size=8192).fit_predict(X), index=base)
    o = {"clustering": nm}
    for T in (2021, 2024):
        t = te[T]; g = lab.reindex(t.index); gg = t.res.groupby(g.values); n = gg.transform("count"); loo = ((gg.transform("sum") - t.res) / (n - 1).replace(0, np.nan)).fillna(0)
        o[f"techo {T} (choque conocido)"] = r2(t.y_rel, t.p + loo)
    a = te[2021].res.groupby(lab.reindex(te[2021].index).values).mean(); b = te[2024].res.groupby(lab.reindex(te[2024].index).values).mean(); j = a.index.intersection(b.index)
    o["corr choque 21→24"] = np.corrcoef(a[j], b[j])[0, 1]
    prev = lab.reindex(te[2024].index).map(a).fillna(0)
    for lam in (0.3, 0.6): o[f"R² 2024 con λ={lam}"] = r2(te[2024].y_rel, te[2024].p + lam * prev)
    rows.append(o)
R = pd.DataFrame(rows).set_index("clustering"); print(f"base R² 2024 = {r2(te[2024].y_rel, te[2024].p):.4f}, 2021 = {r2(te[2021].y_rel, te[2021].p):.4f}"); pd.set_option("display.width", 220); print(R.round(3).to_string()); R.to_csv("reto2_prediccion/reports/cluster_test.csv")
