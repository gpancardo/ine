# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost", "statsmodels"]
# ///
"""Diseño de frontera estatal: pares de secciones a <3 km a ambos lados de una frontera estatal. ¿Qué diferencias estatales explican la diferencia de choque?
Run: uv run analysis/border_design.py"""
import os, sys, pickle
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.formula.api as smf
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import harness as H, common as c
from sklearn.neighbors import NearestNeighbors
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb")); geo = c.load_geo()
xy = pd.DataFrame(np.c_[geo.geometry.centroid.x, geo.geometry.centroid.y], index=geo.index, columns=["x", "y"])
inc = pd.read_csv("data/raw/magar_mun/aymu1989-on.incumbents.csv", low_memory=False); cc = pd.read_csv("data/raw/magar_mun/aymu1989-on.concurrence.csv"); cc["yr"] = cc.date // 10000
fam = lambda s: s.fillna("").str.contains("morena")
rows = []
for T in (2021, 2024):
    t = D[(D["T"] == T) & D.y_rel.notna()].copy(); t["p"] = P[("Ridge", T)].reindex(t.index); t = t.dropna(subset=["p"]).loc[lambda d: d.index.isin(xy.index)]; t["res"] = t.y_rel - t.p; t["est"] = t.mun // 1000
    cur = inc[inc.yr == T]; s_morena = fam(cur.part).groupby(cur.edon).mean(); s_open = cur["race.after"].fillna("").str.startswith("Term-limited").groupby(cur.edon).mean()
    s_gob = cc[cc.yr == T].groupby("edon").dconcgob.mean(); s_mun = cc[cc.yr == T].groupby("edon").size()
    st = pd.DataFrame({"morena": s_morena, "gob": s_gob, "n_mun_elec": s_mun}).fillna(0)
    X = xy.loc[t.index].values; d, i = NearestNeighbors(n_neighbors=9).fit(X).kneighbors(X); a = np.repeat(np.arange(len(t)), 8); b = i[:, 1:].ravel(); dd = d[:, 1:].ravel()
    m = (t.est.values[a] != t.est.values[b]) & (dd < 3000) & (a < b)
    A, B = t.iloc[a[m]], t.iloc[b[m]]; df = pd.DataFrame({"dres": A.res.values - B.res.values, "ea": A.est.values, "eb": B.est.values, "dist": dd[m]})
    for k in st: df["d_" + k] = st[k].reindex(df.ea).values - st[k].reindex(df.eb).values
    df["par"] = df.ea.astype(str) + "-" + df.eb.astype(str); df["T"] = T; df = df.dropna(); rows.append(df)
    print(f"\n[{T}] pares transfronterizos <3 km: {len(df)} en {df.par.nunique()} fronteras; sd(Δchoque)={df.dres.std():.3f}  (referencia: sd entre secciones al azar del mismo estado ≈ {np.sqrt(2) * t.res.std():.3f})")
    mod = smf.ols("dres ~ d_morena + d_gob + d_n_mun_elec", df).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df.par)[0]}); print(mod.summary().tables[1])
    fb = df.groupby("par").dres.agg(["mean", "size"]).query("size>=30"); print("fronteras con mayor salto medio de choque (pp, n≥30 pares):\n", (fb["mean"].sort_values().iloc[[0, 1, 2, -3, -2, -1]] * 100).round(1).to_string())
pd.concat(rows).to_csv("reto2_prediccion/reports/border_pairs.csv", index=False)
