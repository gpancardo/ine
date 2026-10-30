# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost", "statsmodels"]
# ///
"""¿Qué hay debajo de los choques geográficos? (1) descomposición por nivel administrativo, (2) ¿respetan fronteras estatales?, (3) correlatos a nivel municipio y su estabilidad 2021 vs 2024.
Run: uv run analysis/underlying.py"""
import os, sys, pickle
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import harness as H, common as c
from sklearn.neighbors import NearestNeighbors
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb")); geo = c.load_geo(); cen = c.eceg_features()
xy = pd.DataFrame(np.c_[geo.geometry.centroid.x, geo.geometry.centroid.y], index=geo.index, columns=["x", "y"])
R = {}
for T in (2021, 2024):
    t = D[(D["T"] == T) & D.y_rel.notna()].copy(); t["p"] = P[("Ridge", T)].reindex(t.index); t = t.dropna(subset=["p"]).loc[lambda d: d.index.isin(xy.index)]
    t["res"] = t.y_rel - t.p; t["est"] = t.mun // 1000; R[T] = t
    # --- 1. descomposición de la varianza del residuo por jerarquía (R² de medias de grupo, ajustado por tamaño)
    v = t.res.var(); out = {}
    for nm, g in (("estado", t.est), ("municipio", t.mun)):
        gm = t.res.groupby(g.values).transform("mean"); n = t.res.groupby(g.values).transform("count"); k = g.nunique()
        out[nm] = 1 - (1 - (gm.var() / v)) * (len(t) - 1) / (len(t) - k)
    print(f"\n[{T}] fracción de var(residuo) explicada por: estado {out['estado']:.2f}, municipio {out['municipio']:.2f} (R² ajustado)")
    # --- 2. vecinos: correlación del residuo entre secciones vecinas, mismo estado vs distinto estado, por distancia
    X = xy.loc[t.index].values; d, i = NearestNeighbors(n_neighbors=9).fit(X).kneighbors(X); d, i = d[:, 1:].ravel(), i[:, 1:]
    a = np.repeat(np.arange(len(t)), 8); b = i.ravel(); same = t.est.values[a] == t.est.values[b]; r = t.res.values
    bins = pd.qcut(d, 4, duplicates="drop")
    tab = pd.DataFrame({"bin": bins, "same": same, "ra": r[a], "rb": r[b]}).groupby(["bin", "same"], observed=True).apply(lambda g: pd.Series({"corr": np.corrcoef(g.ra, g.rb)[0, 1], "n": len(g)}))
    print(f"[{T}] corr de residuos entre vecinas por distancia (m) y frontera estatal:\n{tab.round(3).to_string()}")
# --- 3. correlatos a nivel municipio con efectos fijos de estado
import statsmodels.formula.api as smf
CO = ["pct_indigena", "pct_sin_relig", "graproes", "pct_nac_otra_ent", "pct_internet", "pct_65mas", "pct_18_24", "pct_analf", "hacinamiento"]
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year.isin([2018, 2021])]
S = {}
for T, prev in ((2021, 2018), (2024, 2021)):
    t = R[T]; g = t.assign(**{k: cen[k].reindex(t.index) for k in CO}).groupby("mun").agg(res=("res", "mean"), est=("est", "first"), n=("res", "size"), a1=("a1", "mean"), a2=("a2", "mean"), **{k: (k, "mean") for k in CO}).dropna()
    g = g[g.n >= 3]; g["tend"] = g.a1 - g.a2
    p = L[L.year == prev].set_index("sid"); sh = (p.v_morena.fillna(0) + p.filter(like="morena").sum(axis=1).sub(p.v_morena.fillna(0)).fillna(0)) if False else None
    Z = (g[CO + ["tend", "a1"]] - g[CO + ["tend", "a1"]].mean()) / g[CO + ["tend", "a1"]].std()
    dfm = pd.concat([g[["res", "est"]], Z], axis=1)
    m = smf.wls("res ~ " + " + ".join(CO + ["tend", "a1"]) + " + C(est)", dfm, weights=g.n).fit()
    S[T] = m.params[CO + ["tend", "a1"]]; print(f"\n[{T}] municipio (n={len(g)}): R² de res ~ rasgos + FE estado = {m.rsquared:.3f};  solo FE estado = {smf.ols('res ~ C(est)', dfm).fit().rsquared:.3f}")
    print((m.params[CO + ["tend", "a1"]] / g.res.std()).round(2).to_string())
j = S[2021].index; print("\ncorr de coeficientes 2021 vs 2024:", round(np.corrcoef(S[2021][j], S[2024][j])[0, 1], 2))
for T in (2021, 2024):
    e = R[T].groupby("est").res.mean().sort_values(); print(f"\n[{T}] estados con mayor sobre-abstención vs. modelo (pp): ", (e.tail(4) * 100).round(1).to_dict(), "| menor:", (e.head(4) * 100).round(1).to_dict())
