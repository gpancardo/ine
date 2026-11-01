# /// script
# dependencies = ["pandas", "pyarrow", "numpy", "scikit-learn"]
# ///
"""Reto 1: elección de k por validez temporal (rasgos 2009-2018 -> perfil de 2024) y estabilidad entre ventanas. Run: uv run reto1_perfiles/analysis/elegir_k.py -> reto1_perfiles/reports/elegir_k.csv"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
s = L.load()
past = L.features(s, [2009, 2012, 2015, 2018], [2012, 2018], [2009, 2015], (2012, 2018)); full = L.features(s, [2015, 2018, 2021, 2024], [2018, 2024], [2015, 2021], (2018, 2024)); common = past.index.intersection(full.index)
d24 = s[s.AELEC == 2024]; nat = d24.SV.sum() / (d24.SV.sum() + d24.NV.sum())
def r(ged=None, sex=None): d = d24; d = d if ged is None else d[d.gedad.isin(ged)]; d = d if sex is None else d[d.SEXO == sex]; g = d.groupby("sid")[["SV", "NV"]].sum(); return (g.SV / (g.SV + g.NV)).reindex(common)
t = pd.DataFrame({"nivel": r() - nat, "joven": r(["18-34"]) - r(["55-74"]), "gen": r(["18-34", "35-54"], 1) - r(["18-34", "35-54"], 0)}, index=common); w = d24.groupby("sid")[["SV", "NV"]].sum().sum(axis=1).reindex(common)
def r2g(y, g): d = pd.concat([y, g, w], axis=1).dropna(); y_, g_, w_ = d.iloc[:, 0], d.iloc[:, 1], d.iloc[:, 2]; mu = y_.groupby(g_).transform("mean"); return 1 - ((y_ - mu) ** 2 * w_).sum() / ((y_ - np.average(y_, weights=w_)) ** 2 * w_).sum()
Xp = StandardScaler().fit_transform(past.loc[common, L.CLUSTER]); Xf = StandardScaler().fit_transform(full.loc[common, L.CLUSTER]); rows = []
for k in range(2, 13):
    a = KMeans(k, n_init=10, random_state=0).fit_predict(Xp); b = KMeans(k, n_init=10, random_state=0).fit_predict(Xf); lab = pd.Series(a, common); ct = pd.crosstab(a, b, normalize="index")
    rows.append(dict(k=k, R2_nivel=r2g(t.nivel, lab), R2_joven=r2g(t.joven, lab), R2_genero=r2g(t.gen, lab), ARI_ventanas=adjusted_rand_score(a, b), pureza=float((ct.max(axis=1) * pd.Series(a).value_counts(normalize=True).sort_index()).sum())))
R = pd.DataFrame(rows); R["R2_medio"] = R[["R2_nivel", "R2_joven", "R2_genero"]].mean(axis=1); print(R.round(3).to_string(index=False)); R.to_csv("reto1_perfiles/reports/elegir_k.csv", index=False)
# IC95% por remuestreo de municipios (200 réplicas) para k de 3 a 8; la convocatoria pide de 4 a 6 perfiles
mun = s.drop_duplicates("sid").set_index("sid").eval("EDOCVE * 1000 + MPIOCVE").reindex(common); rng = np.random.default_rng(0); um = mun.unique(); out = []
labs = {k: pd.Series(KMeans(k, n_init=10, random_state=0).fit_predict(Xp), common) for k in range(3, 9)}; labf = {k: KMeans(k, n_init=10, random_state=0).fit_predict(Xf) for k in range(3, 9)}
w0 = w.copy()
for b in range(200):
    cnt = pd.Series(rng.multinomial(len(um), np.full(len(um), 1 / len(um))), um); w = w0 * mun.map(cnt).values; keep = (w > 0).values
    for k in range(3, 9):
        rep = np.repeat(np.arange(len(common))[keep], mun.map(cnt).values[keep].astype(int))
        out.append(dict(b=b, k=k, R2_medio=np.mean([r2g(t[c], labs[k]) for c in ("nivel", "joven", "gen")]), ARI=adjusted_rand_score(labs[k].values[rep], labf[k][rep])))
w = w0; Q = pd.DataFrame(out); ci = Q.groupby("k").agg(R2_lo=("R2_medio", lambda x: x.quantile(.025)), R2_hi=("R2_medio", lambda x: x.quantile(.975)), ARI_lo=("ARI", lambda x: x.quantile(.025)), ARI_hi=("ARI", lambda x: x.quantile(.975)))
d = Q.pivot(index="b", columns="k", values="R2_medio"); ci["P(R2 > k−1)"] = [np.nan] + [(d[k] > d[k - 1]).mean() for k in range(4, 9)]
print("\nIC95% por remuestreo de municipios"); print(ci.round(3).to_string()); ci.to_csv("reto1_perfiles/reports/elegir_k_ic.csv")
