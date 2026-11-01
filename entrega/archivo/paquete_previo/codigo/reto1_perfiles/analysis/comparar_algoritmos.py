# /// script
# dependencies = ["pandas<2.3", "pyarrow<17", "numpy<2", "scipy<1.14", "scikit-learn<1.6", "py_pcha"]
# ///
"""Reto 1: ¿qué algoritmo de segmentación conserva más información predictiva con el mismo número de segmentos? Protocolo: rasgos 2009-2018 → perfil de 2024, validación cruzada por entidad;
cada codificación (hard o suave) predice por regresión lineal sobre las pertenencias. Algoritmos: K-means, mezcla gaussiana (pertenencias suaves), análisis de arquetipos (pertenencias suaves),
K-means a nivel municipal, árbol supervisado; cotas: regresión sobre los 3 rasgos y sobre el perfil completo de 14 celdas (sexo × edad). También: ¿hay modos naturales? (HDBSCAN, mean-shift).
Run: uv run reto1_perfiles/analysis/comparar_algoritmos.py -> reto1_perfiles/reports/comparacion_algoritmos.csv"""
import os, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from py_pcha import PCHA
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans, HDBSCAN, MeanShift, estimate_bandwidth
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import adjusted_rand_score
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
K = 5; s = L.load(); A = ([2009, 2012, 2015, 2018], [2012, 2018], [2009, 2015], (2012, 2018)); Bw = ([2015, 2018, 2021, 2024], [2018, 2024], [2015, 2021], (2018, 2024))
past, full = L.features(s, *A), L.features(s, *Bw); common = past.index.intersection(full.index)
d24 = s[s.AELEC == 2024]; nat = d24.SV.sum() / (d24.SV.sum() + d24.NV.sum())
def r24(ged=None, sex=None): d = d24; d = d if ged is None else d[d.gedad.isin(ged)]; d = d if sex is None else d[d.SEXO == sex]; g = d.groupby("sid")[["SV", "NV"]].sum(); return (g.SV / (g.SV + g.NV)).reindex(common)
Y = pd.DataFrame({"nivel": r24() - nat, "joven": r24(["18-34"]) - r24(["55-74"]), "genero": r24(["18-34", "35-54"], 1) - r24(["18-34", "35-54"], 0)}); w = d24.groupby("sid")[["SV", "NV"]].sum().sum(axis=1).reindex(common).values
ok = Y.notna().all(axis=1).values & (w > 0); common = common[ok]; Y = Y[ok]; w = w[ok]; st = (common // 10000).values; Ys = ((Y - Y.mean()) / Y.std()).values
X3 = past.loc[common, L.CLUSTER].values
# perfil completo de 14 celdas (sexo × grupo de edad) de la ventana A, relativo a la tasa nacional de la celda
sa = s[s.AELEC.isin(A[0])]; cell = sa.groupby(["sid", "SEXO", "banda"])[["SV", "NV"]].sum(); nc = cell.groupby(["SEXO", "banda"]).sum(); p0 = (nc.SV / (nc.SV + nc.NV)); cell["r"] = (cell.SV + 30 * p0.reindex(cell.index.droplevel(0)).values) / (cell.SV + cell.NV + 30)
X14 = (cell.r.unstack(["SEXO", "banda"]) - p0.values[None, :]).reindex(common).fillna(0).values
# municipio: rasgos agregados a ese nivel
mun_of = pd.Series(s.groupby("sid").apply(lambda g: g.EDOCVE.iat[0] * 1000 + g.MPIOCVE.iat[0]), name="mun"); sm = s.copy(); sm["sid"] = sm.EDOCVE * 1000 + sm.MPIOCVE
Fm = L.features(sm, *A, min_n=3000); munc = mun_of.reindex(common).values
def r2(y, p, w): return 1 - (w * (y - p) ** 2).sum() / (w * (y - np.average(y, weights=w)) ** 2).sum()
def simplex_proj(V):
    """proyección euclídea de cada fila de V al símplex (suma 1, no negativas)"""
    n, k = V.shape; U = np.sort(V, axis=1)[:, ::-1]; css = np.cumsum(U, axis=1) - 1; ind = np.arange(1, k + 1); cond = U - css / ind > 0; rho = cond.sum(axis=1); theta = css[np.arange(n), rho - 1] / rho
    return np.maximum(V - theta[:, None], 0)
def weights_for(XC, X, iters=400):
    """pertenencias a arquetipos XC (dims × k) para los puntos X (n × dims): mínimos cuadrados sobre el símplex por gradiente proyectado"""
    k = XC.shape[1]; G = XC.T @ XC; L_ = np.linalg.eigvalsh(G).max() * 2; W_ = np.full((len(X), k), 1.0 / k); B = X @ XC
    for _ in range(iters): W_ = simplex_proj(W_ - (2 * (W_ @ G - B)) / L_)
    return W_
def archetype_weights(Xtr, Xte, k):
    XC, S, C, SSE, ve = PCHA(Xtr.T, noc=k, delta=0.1); XC = np.asarray(XC); return weights_for(XC, Xtr), weights_for(XC, Xte)
def encode(method, tr, te):
    sc = StandardScaler().fit(X3[tr]); a, b = sc.transform(X3[tr]), sc.transform(X3[te])
    if method == "K-means": km = KMeans(K, n_init=10, random_state=0).fit(a); return np.eye(K)[km.labels_], np.eye(K)[km.predict(b)]
    if method == "Mezcla gaussiana (suave)": g = GaussianMixture(K, covariance_type="full", n_init=3, random_state=0).fit(a); return g.predict_proba(a), g.predict_proba(b)
    if method == "Arquetipos (suave)": return archetype_weights(a[::3], np.vstack([a, b]), K) if False else (lambda XC: (weights_for(XC, a), weights_for(XC, b)))(np.asarray(PCHA(a[::3].T, noc=K, delta=0.1)[0]))
    if method == "K-means municipal": mt = np.unique(munc[tr]); F = Fm.reindex(mt).dropna(); sc2 = StandardScaler().fit(F[L.CLUSTER]); km = KMeans(K, n_init=10, random_state=0).fit(sc2.transform(F[L.CLUSTER])); lab = pd.Series(km.labels_, F.index)
    if method == "K-means municipal":
        def asg(idx):
            m = pd.Series(munc[idx]); Fi = Fm.reindex(m.unique()).dropna(); l2 = pd.Series(km.predict(sc2.transform(Fi[L.CLUSTER])), Fi.index); lab_s = m.map(l2); return np.eye(K)[lab_s.fillna(0).astype(int).values] * lab_s.notna().values[:, None]
        return asg(tr), asg(te)
    if method == "Árbol supervisado (hojas)": t = DecisionTreeRegressor(max_leaf_nodes=K, min_samples_leaf=int(.03 * len(tr)), random_state=0).fit(X3[tr], Ys[tr], sample_weight=w[tr]); la, lb = t.apply(X3[tr]), t.apply(X3[te]); u = np.unique(la); return (la[:, None] == u).astype(float), (lb[:, None] == u).astype(float)
    if method in ("K-means (perfil 14 celdas, PCA 5)", "Mezcla gaussiana (perfil 14 celdas, PCA 5)"):
        p = PCA(5).fit(X14[tr]); za, zb = p.transform(X14[tr]), p.transform(X14[te]); sd = za.std(axis=0); za, zb = za / sd, zb / sd
        if method.startswith("K-means"): km = KMeans(K, n_init=10, random_state=0).fit(za); return np.eye(K)[km.labels_], np.eye(K)[km.predict(zb)]
        g = GaussianMixture(K, covariance_type="full", n_init=3, random_state=0).fit(za); return g.predict_proba(za), g.predict_proba(zb)
    if method == "Lineal (3 rasgos)": return a, b
    if method == "Lineal (perfil 14 celdas, PCA 5)": p = PCA(5).fit(X14[tr]); return p.transform(X14[tr]), p.transform(X14[te])
rows = []
for method in ["K-means", "Mezcla gaussiana (suave)", "Arquetipos (suave)", "K-means municipal", "Árbol supervisado (hojas)", "K-means (perfil 14 celdas, PCA 5)", "Mezcla gaussiana (perfil 14 celdas, PCA 5)", "Lineal (3 rasgos)", "Lineal (perfil 14 celdas, PCA 5)"]:
    pr = {j: [] for j in range(3)}
    for tr, te in GroupKFold(5).split(X3, groups=st):
        Etr, Ete = encode(method, tr, te)
        for j in range(3): m = LinearRegression().fit(Etr, Ys[tr, j], sample_weight=w[tr]); pr[j].append(r2(Ys[te, j], m.predict(Ete), w[te]))
    rows.append(dict(metodo=method, **{f"R² {c}": np.mean(pr[j]) for j, c in enumerate(Y.columns)}, R2_medio=np.mean([np.mean(v) for v in pr.values()])))
R = pd.DataFrame(rows); pd.set_option("display.width", 220); print(R.round(3).to_string(index=False)); R.to_csv("reto1_perfiles/reports/comparacion_algoritmos.csv", index=False)
# estabilidad entre ventanas (secciones comunes): K-means (pureza), mezcla (acuerdo del argmax), arquetipos (acuerdo del argmax tras emparejar)
c2 = past.index.intersection(full.index); Xa, Xb = StandardScaler().fit_transform(past.loc[c2, L.CLUSTER]), StandardScaler().fit_transform(full.loc[c2, L.CLUSTER])
def match(la, lb): ct = pd.crosstab(la, lb).values; r_, c_ = linear_sum_assignment(-ct); return ct[r_, c_].sum() / ct.sum()
ka, kb = KMeans(K, n_init=10, random_state=0).fit_predict(Xa), KMeans(K, n_init=10, random_state=0).fit_predict(Xb)
ga, gb = GaussianMixture(K, covariance_type="full", n_init=3, random_state=0).fit(Xa), GaussianMixture(K, covariance_type="full", n_init=3, random_state=0).fit(Xb)
Sa, Sb = weights_for(np.asarray(PCHA(Xa[::3].T, noc=K, delta=0.1)[0]), Xa), weights_for(np.asarray(PCHA(Xb[::3].T, noc=K, delta=0.1)[0]), Xb)
print("\nestabilidad entre ventanas (2009-2018 vs 2015-2024), acuerdo tras emparejar segmentos: K-means %.3f | mezcla %.3f | arquetipos %.3f" % (match(ka, kb), match(ga.predict(Xa), gb.predict(Xb)), match(Sa.argmax(1), Sb.argmax(1))))
print("pertenencia máxima media (qué tan 'puro' es el perfil de una sección): mezcla %.2f | arquetipos %.2f" % (ga.predict_proba(Xa).max(1).mean(), Sa.max(1).mean()))
# ¿hay modos naturales?
rng = np.random.default_rng(0); sub = rng.choice(len(Xb), 15000, replace=False); hd = HDBSCAN(min_cluster_size=500).fit(Xb[sub]); lab = hd.labels_; bw = estimate_bandwidth(Xb[sub[:5000]], quantile=.2, random_state=0); ms = MeanShift(bandwidth=bw, bin_seeding=True).fit(Xb[sub])
print(f"modos: HDBSCAN (min 500) encuentra {len(set(lab)) - (1 if -1 in lab else 0)} grupos y {np.mean(lab == -1)*100:.0f}% de ruido; mean-shift (ancho {bw:.2f}) encuentra {len(set(ms.labels_))} modos")
