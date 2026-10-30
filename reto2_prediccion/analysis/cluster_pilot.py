# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost", "scipy"]
# ///
"""Tipologías de trayectoria (k-means) con corte temporal honesto. Run: uv run analysis/cluster_pilot.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import features as F, harness as H, stats_util as U, common as c
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.linear_model import Ridge
from sklearn.neighbors import NearestNeighbors

D, nat = H.init(); w = c.load_wide(False); geo = c.load_geo()
log = open("reto2_prediccion/reports/cluster_pilot.txt", "w")
def say(*a): print(*a, flush=True); print(*a, file=log, flush=True)

def profile(years):
    X = pd.concat({y: w[f"abst_{y}"] - nat[y] for y in years}, axis=1).dropna()
    return X

# ---- 1. elección de k con elecciones 2009-2024 (descriptivo) ----
X = profile(c.YEARS); rng = np.random.default_rng(0); sub = X.sample(12000, random_state=0)
say(f"Secciones con las 6 elecciones: {len(X)}")
say("k | silhouette | estabilidad (ARI entre dos mitades)")
for k in range(2, 9):
    km = KMeans(k, n_init=5, random_state=0).fit(X); s = silhouette_score(sub, km.predict(sub))
    a, b = X.sample(frac=.5, random_state=1), X.drop(X.sample(frac=.5, random_state=1).index)
    ka, kb = KMeans(k, n_init=5, random_state=0).fit(a), KMeans(k, n_init=5, random_state=0).fit(b)
    ari = adjusted_rand_score(ka.predict(X), kb.predict(X)); say(f"{k} | {s:.3f} | {ari:.3f}")

# ---- 2. perfiles con k elegido ----
K = 5
km = KMeans(K, n_init=10, random_state=0).fit(X); lab = pd.Series(km.labels_, index=X.index)
cent = pd.DataFrame(km.cluster_centers_ * 100, columns=c.YEARS).round(1)
size = lab.value_counts(normalize=True).sort_index().round(3)
ww = w.loc[X.index]
prof = cent.assign(pct=size.values * 100, rural=ww.groupby(lab).TIPOSEC.apply(lambda s: (s == "R").mean()).values * 100,
                   urbano=ww.groupby(lab).TIPOSEC.apply(lambda s: (s == "U").mean()).values * 100,
                   graproes=ww.groupby(lab).graproes.mean().values, pct_18_24=ww.groupby(lab).pct_18_24.mean().values * 100,
                   sin_servsalud=ww.groupby(lab).sin_servsalud.mean().values * 100, abs_2024=ww.groupby(lab).abst_2024.mean().values * 100, abs_2021=ww.groupby(lab).abst_2021.mean().values * 100)
cyc = (ww[[f"abst_{y}" for y in c.MID if y in c.YEARS]].mean(1) - ww[[f"abst_{y}" for y in c.YEARS if y not in c.MID]].mean(1))
prof["brecha_ciclo_pp"] = (cyc.groupby(lab).mean() * 100).values
pd.set_option("display.width", 250); say("\nPerfiles (columnas de años = abstención relativa a la media nacional, pp):\n", prof.round(1).to_string())
top = ww.assign(l=lab).groupby("l").ent.apply(lambda s: ", ".join(f"{c.ESTADOS[int(e)]} {v:.0%}" for e, v in s.value_counts(normalize=True).head(4).items()))
say("\nEstados dominantes por grupo:\n", top.to_string())
# coherencia espacial
sids = geo.index.intersection(lab.index); cen = np.c_[geo.loc[sids].geometry.centroid.x, geo.loc[sids].geometry.centroid.y]
nn = NearestNeighbors(n_neighbors=9).fit(cen).kneighbors(cen)[1][:, 1:]; l = lab.loc[sids].values
same = (l[nn] == l[:, None]).mean(); exp = ((np.bincount(l) / len(l)) ** 2).sum()
say(f"\nCoherencia espacial: {same:.3f} de los vecinos comparten grupo vs {exp:.3f} esperado al azar")
mun_pure = ww.assign(l=lab).groupby("mun").l.agg(lambda s: s.value_counts(normalize=True).iloc[0]); say(f"Pureza municipal media (grupo modal): {mun_pure.mean():.3f}")
lab.rename("cluster").to_frame().to_csv("data/processed/clusters_k5.csv")

# ---- 3. ¿aporta al backtest? clusters construidos solo con elecciones previas al fold ----
SEM, AGE = F.cols(["sem"]), F.cols(["age"]); REF = SEM + AGE
res = []
for T, cutoff in ((2021, [2009, 2012, 2015, 2018]), (2024, [2009, 2012, 2015, 2018, 2021])):
    Xc = profile(cutoff); kmc = KMeans(K, n_init=10, random_state=0).fit(Xc); lc = pd.Series(kmc.labels_, index=Xc.index)
    tr = D[D["T"].isin(H.FOLDS[T]) & D.y_rel.notna()].copy(); te = D[(D["T"] == T) & D.y_rel.notna()].copy()
    # el entrenamiento usa objetivos <T: clusters con su propio corte sería lo ideal; aquí se usa el mismo corte (conservador: ligera fuga de corte hacia objetivos de entrenamiento)
    for d in (tr, te):
        d["cl"] = lc.reindex(d.index).fillna(-1).astype(int)
    def X_(d, mode):
        base = d[REF].copy()
        if mode == "intercepto": 
            for k in range(K): base[f"c{k}"] = (d.cl == k).astype(float)
        if mode == "pendientes":
            for k in range(K): m = (d.cl == k).astype(float); base[f"c{k}"] = m; base[f"P1_c{k}"] = m * d.P1.fillna(0); base[f"M1_c{k}"] = m * d.M1.fillna(0)
        return base
    E = {}
    for mode in ("ninguno", "intercepto", "pendientes"):
        Xtr, Xte = X_(tr, mode), X_(te, mode); mu = Xtr.mean()
        m = H.lin(Ridge(10.0)).fit(Xtr.fillna(mu).values, tr.y_rel.values); p = m.predict(Xte.fillna(mu).values); E[mode] = pd.Series((te.y_rel.values - p) ** 2, index=te.index)
    for mode in ("intercepto", "pendientes"):
        d_, lo, hi, _ = U.boot_delta(E[mode], E["ninguno"], te.mun, B=1000); res.append((T, mode, np.sqrt(E[mode].mean()), np.sqrt(E["ninguno"].mean()), d_, lo, hi))
say("\nBacktest: Ridge S2 + grupos (corte temporal honesto)\n  test | variante | RMSE | RMSE ref | Δ [IC95%]")
for r in res: say(f"  {r[0]} | {r[1]:10s} | {r[2]:.4f} | {r[3]:.4f} | {r[4]:+.4f} [{r[5]:+.4f},{r[6]:+.4f}]")
# error por grupo (¿dónde falla el modelo?) con clusters de 2027-view
for T in (2021, 2024):
    te = D[(D["T"] == T) & D.y_rel.notna()]; pr = pd.read_pickle("data/processed/benchmark_preds.pkl")[("Ridge", T)].reindex(te.index)
    e = ((te.y_rel - pr) ** 2).groupby(lab.reindex(te.index)).mean() ** .5
    say(f"RMSE del Ridge por grupo ({T}; grupos = 6 elecciones, solo descriptivo):", e.round(4).to_dict())
