# /// script
# dependencies = ["pandas", "pyarrow", "numpy", "scikit-learn"]
# ///
"""Calidad estadística de la tipología de secciones (k=6, tres rasgos): (1) ¿hay estructura de grupos más allá de un continuo? (silueta frente a un nulo normal multivariante),
(2) sensibilidad al encogimiento M y al umbral de registros, (3) K-means ponderado por lista nominal, (4) algoritmos alternativos (mezcla gaussiana, Ward), la confiabilidad de los rasgos está en confiabilidad_rasgos.py.
Run: uv run reto1_perfiles/analysis/robustez_tipologia.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.metrics import adjusted_rand_score as ARI, silhouette_score
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
rng = np.random.default_rng(0); K = 5; Y = [2015, 2018, 2021, 2024]; PR, MD = [2018, 2024], [2015, 2021]
s = L.load(); base = L.features(s, Y, PR, MD, (2018, 2024)); Xb = StandardScaler().fit_transform(base[L.CLUSTER]); kb = KMeans(K, n_init=20, random_state=0).fit(Xb); lab = pd.Series(kb.labels_, base.index)
sub = rng.choice(len(Xb), 15000, replace=False); sil = silhouette_score(Xb[sub], kb.labels_[sub]); rows = [("Silueta real (k=6)", sil)]
# (1) nulo: normal multivariante con la misma media y covarianza (sin grupos), 20 réplicas
mu, cov = Xb.mean(0), np.cov(Xb.T); nul = []
for b in range(20):
    Z = rng.multivariate_normal(mu, cov, size=len(Xb)); zs = rng.choice(len(Z), 15000, replace=False); nul.append(silhouette_score(Z[zs], KMeans(K, n_init=3, random_state=b).fit_predict(Z)[zs]))
print(f"[1] estructura: silueta real {sil:.3f} | nulo normal multivariante (20 réplicas) media {np.mean(nul):.3f}, rango {min(nul):.3f}-{max(nul):.3f}")
# marginales no normales: nulo con permutación independiente de columnas (conserva las marginales, destruye la dependencia)
pn = []
for b in range(10):
    Z = np.column_stack([rng.permutation(Xb[:, j]) for j in range(Xb.shape[1])]); zs = rng.choice(len(Z), 15000, replace=False); pn.append(silhouette_score(Z[zs], KMeans(K, n_init=3, random_state=b).fit_predict(Z)[zs]))
print(f"    nulo con columnas permutadas (10 réplicas): media {np.mean(pn):.3f}")
# (2) sensibilidad M y umbral
print("\n[2] sensibilidad (ARI contra la solución base, secciones comunes)")
for nm, kw in (("M=0 (sin encogimiento)", dict(m=0.0)), ("M=10", dict(m=10.0)), ("M=100", dict(m=100.0)), ("umbral 400 registros", dict(min_n=400)), ("umbral 1500 registros", dict(min_n=1500))):
    F2 = L.features(s, Y, PR, MD, (2018, 2024), **kw); c2 = F2.index.intersection(base.index); l2 = KMeans(K, n_init=10, random_state=0).fit_predict(StandardScaler().fit_transform(F2.loc[c2, L.CLUSTER]))
    print(f"    {nm:28s} secciones {len(F2):6d}  ARI = {ARI(lab.loc[c2], l2):.3f}")
# (3) ponderado por lista nominal
w = base.n_total.values; lw = KMeans(K, n_init=20, random_state=0).fit_predict(Xb, sample_weight=w); print(f"\n[3] K-means ponderado por registros: ARI vs sin ponderar = {ARI(lab, lw):.3f}")
# (4) alternativos
gm = GaussianMixture(K, covariance_type="full", n_init=3, random_state=0).fit(Xb); print(f"[4] mezcla gaussiana (mismo k): ARI vs K-means = {ARI(lab, gm.predict(Xb)):.3f}")
bic = {k: GaussianMixture(k, covariance_type="full", n_init=2, random_state=0).fit(Xb).bic(Xb) for k in (3, 4, 5, 6, 7, 8, 10, 12)}; print("    BIC por k:", {k: round(v / 1e3) for k, v in bic.items()}, "(miles; menor es mejor)")
ag = AgglomerativeClustering(K, linkage="ward").fit_predict(Xb[sub]); print(f"    Ward (submuestra 15 mil): ARI vs K-means = {ARI(lab.values[sub], ag):.3f}")
rows = [("silueta real (k=%d)" % K, sil), ("silueta nulo normal multivariante (media de 20)", float(np.mean(nul))), ("silueta nulo con columnas permutadas (media de 10)", float(np.mean(pn))), ("ARI K-means ponderado vs sin ponderar", ARI(lab, lw)), ("ARI mezcla gaussiana vs K-means", ARI(lab, gm.predict(Xb))), ("ARI Ward (submuestra) vs K-means", ARI(lab.values[sub], ag))]
pd.DataFrame(rows, columns=["prueba", "valor"]).to_csv("reto1_perfiles/reports/robustez_tipologia.csv", index=False)
