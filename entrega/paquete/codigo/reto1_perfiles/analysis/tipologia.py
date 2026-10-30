# /// script
# dependencies = ["pandas", "pyarrow", "numpy", "scikit-learn", "scipy"]
# ///
"""Reto 1: rasgos de la tipología (data/processed/tipologia_features.parquet) y diagnóstico de k con los tres rasgos persistentes.
Run: uv run reto1_perfiles/analysis/tipologia.py   ->  reto1_perfiles/reports/tipologia_k.csv"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); pd.set_option("display.width", 220); import tip_lib as L
s = L.load(); F = L.features(s, [2015, 2018, 2021, 2024], [2018, 2024], [2015, 2021], (2018, 2024))
meta = s[s.AELEC == 2024].groupby("sid").agg(EDOCVE=("EDOCVE", "first"), MPIOCVE=("MPIOCVE", "first"), ln24=("LN", "sum")); F = F.join(meta).dropna(subset=["EDOCVE"]); F.to_parquet("data/processed/tipologia_features.parquet")
print("secciones con las 4 elecciones y n≥800:", len(F)); print(F.describe().round(3).T[["mean", "std", "min", "max"]].to_string())
X = StandardScaler().fit_transform(F[L.CLUSTER]); print("\ncorrelaciones entre rasgos de agrupación:\n", pd.DataFrame(X, columns=L.CLUSTER).corr().round(2).to_string())
rng = np.random.default_rng(0); sub_i = rng.choice(len(X), 15000, replace=False); rows = []
for k in range(2, 11):
    km = KMeans(k, n_init=5, random_state=0).fit(X); sil = silhouette_score(X[sub_i], km.labels_[sub_i]); aris = []
    for b in range(5):
        i1, i2 = rng.choice(len(X), len(X) // 2, replace=False), rng.choice(len(X), len(X) // 2, replace=False)
        k1, k2 = KMeans(k, n_init=3, random_state=b).fit(X[i1]), KMeans(k, n_init=3, random_state=b + 10).fit(X[i2]); aris.append(adjusted_rand_score(k1.predict(X), k2.predict(X)))
    rows.append(dict(k=k, silueta=sil, estabilidad_ARI=np.mean(aris), inercia=km.inertia_))
R = pd.DataFrame(rows); print("\n", R.round(3).to_string(index=False)); R.to_csv("reto1_perfiles/reports/tipologia_k.csv", index=False)
