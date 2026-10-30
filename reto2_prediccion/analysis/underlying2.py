# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""Correlación del residuo entre secciones vecinas a distancia igualada: mismo municipio / otro municipio mismo estado / otro estado. Run: uv run analysis/underlying2.py"""
import os, sys, pickle
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import harness as H, common as c
from sklearn.neighbors import NearestNeighbors
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb")); geo = c.load_geo()
xy = pd.DataFrame(np.c_[geo.geometry.centroid.x, geo.geometry.centroid.y], index=geo.index, columns=["x", "y"])
out = []
for T in (2021, 2024):
    t = D[(D["T"] == T) & D.y_rel.notna()].copy(); t["p"] = P[("Ridge", T)].reindex(t.index); t = t.dropna(subset=["p"]).loc[lambda d: d.index.isin(xy.index)]
    r = (t.y_rel - t.p).values; mun = t.mun.values; est = mun // 1000
    d, i = NearestNeighbors(n_neighbors=21).fit(xy.loc[t.index].values).kneighbors(xy.loc[t.index].values); d, i = d[:, 1:].ravel(), i[:, 1:]; a = np.repeat(np.arange(len(t)), 20); b = i.ravel()
    kind = np.where(mun[a] == mun[b], "mismo municipio", np.where(est[a] == est[b], "otro municipio, mismo estado", "otro estado"))
    df = pd.DataFrame({"d": d, "kind": kind, "ra": r[a], "rb": r[b]}); df["bin"] = pd.cut(df.d, [0, 700, 1500, 3000, 8000])
    tab = df.groupby(["bin", "kind"], observed=True).apply(lambda g: pd.Series({"corr": np.corrcoef(g.ra, g.rb)[0, 1] if len(g) > 50 else np.nan, "n": len(g)})).unstack("kind")
    print(f"\n[{T}] corr del residuo entre vecinas (distancia en m, igualada):\n{tab['corr'].round(2).to_string()}\nn:\n{tab['n'].astype(int).to_string()}")
