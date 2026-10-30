# /// script
# dependencies = ["pandas<2.3", "pyarrow<17", "numpy<2", "scikit-learn<1.6", "scipy<1.14", "py_pcha"]
# ///
"""Reto 1 (E2/E3): pertenencias suaves por sección. Arquetipos (k=5) sobre los tres rasgos estandarizados de la tipología, y la etiqueta dura de K-means
(la misma de tipologia_secciones.csv). Salidas: reto1_perfiles/reports/tipologia_pertenencias.csv (pesos de cada arquetipo que suman 1, arquetipo principal, perfil K-means).
Run: uv run reto1_perfiles/analysis/pertenencias.py  (numpy<2 por py_pcha)"""
import os, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from py_pcha import PCHA
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
K = 5; R = Path("reto1_perfiles/reports")
F = pd.read_parquet("data/processed/tipologia_features.parquet").dropna(subset=L.CLUSTER)
F = F.join(pd.read_csv(R / "tipologia_secciones.csv", usecols=["sid", "c"]).set_index("sid").c, how="left")
X = StandardScaler().fit_transform(F[L.CLUSTER].values)
XC = np.asarray(PCHA(X[::3].T, noc=K, delta=0.1)[0])   # vértices (dims × k), ajustados con 1/3 de las secciones
def simplex_proj(V):
    n, k = V.shape; U = np.sort(V, axis=1)[:, ::-1]; css = np.cumsum(U, axis=1) - 1; ind = np.arange(1, k + 1); cond = U - css / ind > 0; rho = cond.sum(axis=1); theta = css[np.arange(n), rho - 1] / rho
    return np.maximum(V - theta[:, None], 0)
def weights_for(XC, X, iters=400):
    k = XC.shape[1]; G = XC.T @ XC; L_ = np.linalg.eigvalsh(G).max() * 2; W = np.full((len(X), k), 1.0 / k); B = X @ XC
    for _ in range(iters): W = simplex_proj(W - (2 * (W @ G - B)) / L_)
    return W
W = weights_for(XC, X)
P = pd.DataFrame(W, index=F.index, columns=[f"arq{k}" for k in range(K)])
P["arquetipo_principal"] = P.values.argmax(1); P["peso_principal"] = P.iloc[:, :K].max(1)
P["perfil_kmeans"] = F.c.values
P["residuo_ajuste"] = np.sqrt(((X - W @ XC.T) ** 2).sum(1))
P.round(4).reset_index(names="sid").to_csv(R / "tipologia_pertenencias.csv", index=False)
print("pertenencia principal media: %.2f" % P.peso_principal.mean())
ct = pd.crosstab(P.perfil_kmeans, P.arquetipo_principal); print("tabla perfil K-means × arquetipo principal (filas: perfil):"); print(ct.to_string())
print("residuo medio de la aproximación (SD):", round(P.residuo_ajuste.mean(), 3))
