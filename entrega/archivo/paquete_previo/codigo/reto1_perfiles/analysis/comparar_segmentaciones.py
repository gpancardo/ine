# /// script
# dependencies = ["pandas", "pyarrow", "numpy", "scikit-learn"]
# ///
"""Reto 1: ¿K-means o segmentación por reglas? Comparación fuera de ventana (rasgos 2009-2018 → perfil de 2024) y fuera de estados (validación cruzada por entidad).
Métodos: K-means; árbol de regresión multisalida (hojas = segmentos con reglas explícitas) con y sin tipo de sección; regresión lineal (cota); azar.
Métrica: R² ponderado por registros de los tres rasgos de 2024 (nivel relativo, brecha de jóvenes, brecha de género 18-54). Run: uv run reto1_perfiles/analysis/comparar_segmentaciones.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
s = L.load(); past = L.features(s, [2009, 2012, 2015, 2018], [2012, 2018], [2009, 2015], (2012, 2018)); full = L.features(s, [2015, 2018, 2021, 2024], [2018, 2024], [2015, 2021], (2018, 2024)); common = past.index.intersection(full.index)
tp = pd.read_parquet("data/processed/panel.parquet", columns=["AELEC", "EDOCVE", "SECCION", "TIPOSEC"]).query("AELEC == 2024"); tp["sid"] = tp.EDOCVE * 10000 + tp.SECCION; tp = tp.drop_duplicates("sid").set_index("sid").TIPOSEC
d24 = s[s.AELEC == 2024]; nat = d24.SV.sum() / (d24.SV.sum() + d24.NV.sum())
def r(ged=None, sex=None): d = d24; d = d if ged is None else d[d.gedad.isin(ged)]; d = d if sex is None else d[d.SEXO == sex]; g = d.groupby("sid")[["SV", "NV"]].sum(); return (g.SV / (g.SV + g.NV)).reindex(common)
Y = pd.DataFrame({"nivel": r() - nat, "joven": r(["18-34"]) - r(["55-74"]), "genero": r(["18-34", "35-54"], 1) - r(["18-34", "35-54"], 0)}); w = d24.groupby("sid")[["SV", "NV"]].sum().sum(axis=1).reindex(common).values
ok = Y.notna().all(axis=1).values & (w > 0); common = common[ok]; Y = Y[ok]; w = w[ok]
X = past.loc[common, L.CLUSTER].copy(); X["urb"] = tp.reindex(common).map({"U": 0, "M": 1, "R": 2}).fillna(1).values; st = (common // 10000).values; Ys = (Y - Y.mean()) / Y.std()
def r2(y, p, w): return 1 - (w * (y - p) ** 2).sum() / (w * (y - np.average(y, weights=w)) ** 2).sum()
def cv(method, **kw):
    out = {c: [] for c in Y.columns}
    for tr, te in GroupKFold(5).split(X, groups=st):
        if method == "kmeans":
            sc = StandardScaler().fit(X.iloc[tr][L.CLUSTER]); km = KMeans(kw["k"], n_init=10, random_state=0).fit(sc.transform(X.iloc[tr][L.CLUSTER])); gt, ge = km.labels_, km.predict(sc.transform(X.iloc[te][L.CLUSTER]))
        elif method == "arbol":
            cols = L.CLUSTER + (["urb"] if kw["urb"] else []); t = DecisionTreeRegressor(max_leaf_nodes=kw["k"], min_samples_leaf=int(.03 * len(tr)), random_state=0).fit(X.iloc[tr][cols].values, Ys.iloc[tr].values, sample_weight=w[tr]); gt, ge = t.apply(X.iloc[tr][cols].values), t.apply(X.iloc[te][cols].values)
        elif method == "azar": rng = np.random.default_rng(0); gt, ge = rng.integers(0, kw["k"], len(tr)), rng.integers(0, kw["k"], len(te))
        for j, cname in enumerate(Y.columns):
            ytr = Ys.iloc[tr, j].values; m = pd.Series(ytr * w[tr]).groupby(gt).sum() / pd.Series(w[tr]).groupby(gt).sum(); pred = pd.Series(ge).map(m).fillna(0).values; out[cname].append(r2(Ys.iloc[te, j].values, pred, w[te]))
    return {c: np.mean(v) for c, v in out.items()}
rows = []
for k in (4, 5, 6, 8):
    for nm, kw in (("K-means", dict(method="kmeans", k=k)), ("Árbol (3 rasgos)", dict(method="arbol", k=k, urb=False)), ("Árbol (3 rasgos + tipo de sección)", dict(method="arbol", k=k, urb=True)), ("Azar", dict(method="azar", k=k))):
        o = cv(**kw); rows.append(dict(metodo=nm, segmentos=k, **{f"R² {c}": v for c, v in o.items()}, R2_medio=np.mean(list(o.values()))))
lin = {c: [] for c in Y.columns}
for tr, te in GroupKFold(5).split(X, groups=st):
    for j, cname in enumerate(Y.columns): m = LinearRegression().fit(X.iloc[tr][L.CLUSTER], Ys.iloc[tr, j], sample_weight=w[tr]); lin[cname].append(r2(Ys.iloc[te, j].values, m.predict(X.iloc[te][L.CLUSTER]), w[te]))
rows.append(dict(metodo="Regresión lineal (cota continua)", segmentos=0, **{f"R² {c}": np.mean(v) for c, v in lin.items()}, R2_medio=np.mean([np.mean(v) for v in lin.values()])))
Rr = pd.DataFrame(rows); pd.set_option("display.width", 220); print(Rr.round(3).to_string(index=False)); Rr.to_csv("reto1_perfiles/reports/comparacion_segmentaciones.csv", index=False)
