# /// script
# dependencies = ["pandas", "numpy", "scikit-learn"]
# ///
"""Reto 1 (E1b): qué tan diferenciados son los perfiles. Sobre los tres rasgos estandarizados (tip_lib.CLUSTER):
η² por eje (varianza entre perfiles / total, ponderada por lista nominal), distancia estandarizada entre centroides,
y proporción de secciones cerca de una frontera (distancia al 2º centroide ≤ 1.1 × distancia al más cercano).
Salidas: reto1_perfiles/reports/diferenciacion_perfiles.csv (η² y frontera por perfil) y diferenciacion_centroides.csv. Run: uv run reto1_perfiles/analysis/diferenciacion_perfiles.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
R = Path("reto1_perfiles/reports"); F = pd.read_csv(R / "tipologia_secciones.csv").dropna(subset=L.CLUSTER + ["c"])
X = StandardScaler().fit_transform(F[L.CLUSTER].values); w = F.ln24.values; c = F.c.values.astype(int); K = c.max() + 1
mu = np.array([np.average(X[c == k], axis=0, weights=w[c == k]) for k in range(K)])
grand = np.average(X, axis=0, weights=w)
eta2 = {}
for j, col in enumerate(L.CLUSTER):
    between = sum(w[c == k].sum() * (mu[k, j] - grand[j]) ** 2 for k in range(K)); total = (w * (X[:, j] - grand[j]) ** 2).sum()
    eta2[col] = between / total
D = np.sqrt(((mu[:, None, :] - mu[None, :, :]) ** 2).sum(-1))
print("η² por eje (sobre rasgos estandarizados):", {k: round(v, 3) for k, v in eta2.items()})
print("distancia entre centroides (en SD):"); print(pd.DataFrame(D, index=range(K), columns=range(K)).round(2).to_string())
dist = np.sqrt(((X[:, None, :] - mu[None, :, :]) ** 2).sum(-1)); srt = np.sort(dist, axis=1)
frontera = srt[:, 1] <= 1.1 * srt[:, 0]
rows = [dict(perfil=k, secciones=int((c == k).sum()), frontera_pct=100 * np.average(frontera[c == k], weights=w[c == k]),
             dist_vecino_mas_cercano=np.min(D[k][np.arange(K) != k])) for k in range(K)]
T = pd.DataFrame(rows).set_index("perfil")
T.loc["total"] = [F.shape[0], 100 * np.average(frontera, weights=w), np.nan]
T.round(3).to_csv(R / "diferenciacion_perfiles.csv")
pd.DataFrame(D, index=range(K), columns=range(K)).round(3).to_csv(R / "diferenciacion_centroides.csv")
pd.DataFrame({"eta2": eta2}).round(4).to_csv(R / "diferenciacion_eta2.csv")
print(T.round(2).to_string())
