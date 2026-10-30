# /// script
# dependencies = ["pandas", "pyarrow", "numpy", "scikit-learn"]
# ///
"""Validación temporal sin solapamiento: grupos construidos SOLO con 2009-2018 (k=5) vs. perfil observado en 2024.
(1) concordancia (ARI) con los grupos de 2015-2024; (2) varianza de los rasgos de 2024 explicada por los grupos del pasado, frente a grupos al azar, estados y
a la regresión lineal sobre los rasgos continuos del pasado (cota de lo que la discretización puede retener). La intermitencia (2024 − 2021) se incluye como control: no se espera que persista.
Run: uv run reto1_perfiles/analysis/validar_tipologia.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
s = L.load(); K = 5
past = L.features(s, [2009, 2012, 2015, 2018], [2012, 2018], [2009, 2015], (2012, 2018)); full = L.features(s, [2015, 2018, 2021, 2024], [2018, 2024], [2015, 2021], (2018, 2024))
kp = KMeans(K, n_init=20, random_state=0).fit(StandardScaler().fit_transform(past[L.CLUSTER])); past["c"] = kp.labels_
full["c"] = KMeans(K, n_init=20, random_state=0).fit_predict(StandardScaler().fit_transform(full[L.CLUSTER]))
common = past.index.intersection(full.index); print(f"secciones en ambas ventanas: {len(common)}; ARI(grupos 2009-2018 vs 2015-2024) = {adjusted_rand_score(past.loc[common, 'c'], full.loc[common, 'c']):.3f}")
d24 = s[s.AELEC == 2024]; nat24 = d24.SV.sum() / (d24.SV.sum() + d24.NV.sum())
def r(y, ged=None, sex=None):
    d = s[s.AELEC == y]; d = d if ged is None else d[d.gedad.isin(ged)]; d = d if sex is None else d[d.SEXO == sex]; g = d.groupby("sid")[["SV", "NV"]].sum(); return (g.SV / (g.SV + g.NV)).reindex(common)
t = pd.DataFrame(index=common); t["nivel (rel. nacional)"] = r(2024) - nat24; t["brecha jóvenes 18-34 vs 55-74"] = r(2024, ["18-34"]) - r(2024, ["55-74"]); t["brecha de género 18-54"] = r(2024, ["18-34", "35-54"], 1) - r(2024, ["18-34", "35-54"], 0)
t["caída 75+ vs 55-74"] = r(2024, ["75+"]) - r(2024, ["55-74"]); t["intermitencia 2024−2021 (control)"] = r(2024) - r(2021)
t["c"] = past.loc[common, "c"]; t["est"] = t.index // 10000; t["n"] = d24.groupby("sid")[["SV", "NV"]].sum().sum(axis=1).reindex(common); rng = np.random.default_rng(0); t["azar"] = rng.permutation(t.c.values)
def r2g(y, g, w): d = pd.concat([y, g, w], axis=1).dropna(); y_, g_, w_ = d.iloc[:, 0], d.iloc[:, 1], d.iloc[:, 2]; mu = y_.groupby(g_).transform("mean"); return 1 - ((y_ - mu) ** 2 * w_).sum() / ((y_ - np.average(y_, weights=w_)) ** 2 * w_).sum()
Xp = StandardScaler().fit_transform(past.loc[common, L.CLUSTER]); rows = []
for v in [c for c in t.columns if c not in ("c", "est", "n", "azar")]:
    d = t[v].dropna(); ok = d.index; lr = LinearRegression().fit(Xp[t.index.get_indexer(ok)], d.values, sample_weight=t.n.loc[ok].values); pr = lr.predict(Xp[t.index.get_indexer(ok)]); w = t.n.loc[ok]
    rl = 1 - ((d - pr) ** 2 * w).sum() / ((d - np.average(d, weights=w)) ** 2 * w).sum()
    rows.append({"rasgo de 2024": v, f"R² grupos del pasado (k={K})": r2g(t[v], t.c, t.n), "R² grupos al azar": r2g(t[v], t.azar, t.n), "R² estado (32)": r2g(t[v], t.est, t.n), "R² lineal en rasgos continuos del pasado": rl})
R = pd.DataFrame(rows); print(R.round(3).to_string(index=False)); R.to_csv("reto1_perfiles/reports/validacion_tipologia.csv", index=False)
ct = pd.crosstab(past.loc[common, "c"], full.loc[common, "c"], normalize="index"); print("\nmatriz de transición (filas: grupo 2009-2018; columnas: grupo 2015-2024), %:"); print((ct * 100).round(0).to_string())
print("pureza media ponderada (máx de cada fila):", round(float((ct.max(axis=1) * past.loc[common, "c"].value_counts(normalize=True).sort_index()).sum()), 3))
