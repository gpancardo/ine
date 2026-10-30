# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost", "scipy"]
# ///
"""Enfoques alternativos (geoespacial / física social / riesgo) contra la referencia S2 en el mismo backtest.
Run: uv run analysis/alt_approaches.py -> reto2_prediccion/reports/alt_approaches.csv, reto2_prediccion/reports/alt_diag.txt"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import features as F, harness as H, stats_util as U, common as c
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.neighbors import NearestNeighbors
from scipy.stats import spearmanr

D, nat = H.init()
w = c.load_wide(False); geo = c.load_geo(); sids = geo.index.intersection(w.index); w = w.loc[sids]
cen = np.c_[geo.loc[sids].geometry.centroid.x, geo.loc[sids].geometry.centroid.y]
NN = NearestNeighbors(n_neighbors=9).fit(cen).kneighbors(cen)[1][:, 1:]
def smooth(v):  # promedio de 8 vecinos; vecinos faltantes -> valor propio
    with np.errstate(all="ignore"): m = np.nanmean(v[NN], 1)
    return np.where(np.isnan(m), v, m)
rel = lambda y: (w[f"abst_{y}"] - nat[y]).values
PM = {2015: (2012, 2009), 2018: (2012, 2015), 2021: (2018, 2015), 2024: (2018, 2021), 2027: (2024, 2021)}
out = []
log = open("reto2_prediccion/reports/alt_diag.txt", "w")
def say(*a, **k): print(*a, flush=True); print(*a, file=log, flush=True)

# ---------- A. ¿persisten o se revierten los choques locales? ----------
res = {}
for T in (2015, 2018, 2021, 2024):
    d = D[(D["T"] == T) & D.y_rel.notna()]; sem = F.cols(["sem"])
    m = LinearRegression().fit(d[sem].fillna(0), d.y_rel); res[T] = pd.Series(d.y_rel.values - m.predict(d[sem].fillna(0)), index=d.index)
    D.loc[(D["T"] == T) & D.y_rel.notna(), "res_own"] = res[T].values
say("A. Autocorrelación del residuo (OLS en el propio año) entre transiciones consecutivas")
for a, b in ((2015, 2018), (2018, 2021), (2021, 2024)):
    j = pd.concat([res[a], res[b]], axis=1, join="inner"); j.columns = ["a", "b"]; j["mun"] = w.mun.reindex(j.index).values; j["ent"] = j.index // 10000
    mm = j.groupby("mun")[["a", "b"]].mean(); ee = j.groupby("ent")[["a", "b"]].mean()
    say(f"  res({a}) vs res({b}): sección r={j.a.corr(j.b):+.3f} | municipio r={mm.a.corr(mm.b):+.3f} | estado r={ee.a.corr(ee.b):+.3f}")
# feature de choque previo (residuo de T-3, sección y media municipal)
for T in (2018, 2021, 2024, 2027):
    mask = D["T"] == T; prev = res.get(T - 3)
    if prev is None: D.loc[mask, ["res1", "res1_mun"]] = np.nan; continue
    r = prev.reindex(D.index[mask]).values; D.loc[mask, "res1"] = r
    D.loc[mask, "res1_mun"] = pd.Series(r, index=D.index[mask]).groupby(D.loc[mask, "mun"].values).transform("mean").values

# ---------- D. difusión multi-escala (DeGroot) de P1 y M1 sobre el grafo de secciones ----------
for T in (2015, 2018, 2021, 2024, 2027):
    mask = (D["T"] == T).values; idx = D.index[mask]
    for nm, y in (("P1", PM[T][0]), ("M1", PM[T][1])):
        v = rel(y); s1 = smooth(v); s2 = smooth(s1); s4 = smooth(smooth(s2))
        for k, s in (("s1", s1), ("s2", s2), ("s4", s4)):
            D.loc[mask, f"{nm}_{k}"] = pd.Series(s, index=sids).reindex(idx).values
for k in ("P1_s1", "P1_s2", "P1_s4", "M1_s1", "M1_s2", "M1_s4"): D[k] = D[k]
DIFF = ["P1_s1", "P1_s2", "P1_s4", "M1_s1", "M1_s2", "M1_s4"]

# ---------- B. pendientes espacialmente variables: P1 y M1 por estado (ridge) / por región k-means ----------
from sklearn.cluster import KMeans
reg = pd.Series(KMeans(40, n_init=3, random_state=0).fit_predict(cen), index=sids)
def varying(dd, key, ks):
    cols = {}
    for g in ks:
        m = (key == g).astype(float)
        cols[f"i_{g}"] = m; cols[f"P1_{g}"] = m * dd.P1.values; cols[f"M1_{g}"] = m * dd.M1.values
    return pd.DataFrame(cols, index=dd.index)

SEM, AGE = F.cols(["sem"]), F.cols(["age"])
def fit_pred(T, build, mk):
    tr = D[D["T"].isin(H.FOLDS[T]) & D.y_rel.notna()]; te = D[(D["T"] == T) & D.y_rel.notna()]
    Xtr, Xte = build(tr), build(te); mu = Xtr.mean()
    m = mk().fit(Xtr.fillna(mu).values, tr.y_rel.values); p = m.predict(Xte.fillna(mu).values)
    return te, p
R = lambda a=10.0: (lambda: H.lin(Ridge(a)))
V = {
 "REF S2: sem+edad (Ridge)": (lambda d: d[SEM + AGE], R()),
 "A+ choque previo (res1 sección, municipio)": (lambda d: d[SEM + AGE + ["res1", "res1_mun"]], R()),
 "D+ difusión multi-escala (Ridge)": (lambda d: d[SEM + AGE + DIFF], R()),
 "D+ difusión multi-escala (LightGBM)": (lambda d: d[SEM + AGE + DIFF], H.lgbm),
 "B+ pendientes por estado (Ridge α=100)": (lambda d: pd.concat([d[SEM + AGE], varying(d, d.ent.values, sorted(D.ent.unique()))], axis=1), R(100.0)),
 "B+ pendientes por región k-means 40 (Ridge α=100)": (lambda d: pd.concat([d[SEM + AGE], varying(d, reg.reindex(d.index).values, range(40))], axis=1), R(100.0)),
 "A+D+B combinado (Ridge α=100)": (lambda d: pd.concat([d[SEM + AGE + DIFF + ["res1", "res1_mun"]], varying(d, d.ent.values, sorted(D.ent.unique()))], axis=1), R(100.0)),
}
E = {}; PRED = {}
for name, (b, mk) in V.items():
    for T in (2021, 2024):
        te, p = fit_pred(T, b, mk); e = (te.y_rel.values - p) ** 2; E[(name, T)] = pd.Series(e, index=te.index); PRED[(name, T)] = pd.Series(p, index=te.index)
        out.append(dict(variante=name, test=T, rmse=float(np.sqrt(e.mean())), r2=H.score(te.y_rel.values, p)["r2"]))
    say(name, [round(o["rmse"], 4) for o in out if o["variante"] == name], flush=True)
R_ = pd.DataFrame(out)
for i, r in R_.iterrows():  # Δ pareado vs referencia
    ref = E[("REF S2: sem+edad (Ridge)", r.test)]; e = E[(r.variante, r.test)]; te = D[(D["T"] == r.test) & D.y_rel.notna()]
    if r.variante.startswith("REF"): continue
    d, lo, hi, p = U.boot_delta(e, ref, te.mun, B=1000); R_.loc[i, ["d_vs_ref", "lo", "hi"]] = [d, lo, hi]
R_.to_csv("reto2_prediccion/reports/alt_approaches.csv", index=False)
pd.set_option("display.width", 200); say(R_.round(4).to_string(index=False))

# ---------- F. riesgo de DISMINUCIÓN de participación: ranking contra heurísticas ----------
say("\nF. Riesgo de deterioro relativo vs la última elección del mismo tipo (rank y precisión@10%)")
rows = []
for T in (2021, 2024):
    te = D[(D["T"] == T) & D.y_rel.notna()].copy(); same = te.M1 if T in c.MID else te.P1
    te["chg"] = te.y_rel - same                       # cambio relativo real (+ = más abstención respecto a sí misma)
    top = te.chg >= te.chg.quantile(.9)
    cand = {"Ridge S2 (pred − última mismo tipo)": PRED[("REF S2: sem+edad (Ridge)", T)].reindex(te.index) - same,
            "Difusión LightGBM": PRED[("D+ difusión multi-escala (LightGBM)", T)].reindex(te.index) - same,
            "Heurística: abstención alta en la última mismo tipo": same, "Heurística: tendencia (a1−a2)": te.a1 - te.a2,
            "Heurística: abstención alta en P1": te.P1, "Aleatorio": pd.Series(np.random.default_rng(0).random(len(te)), index=te.index)}
    for k, s in cand.items():
        ok = s.notna(); thr = s[ok].quantile(.9); flag = (s >= thr) & ok
        rows.append(dict(test=T, criterio=k, spearman=spearmanr(s[ok], te.chg[ok])[0], precision_top10=float((flag & top).sum() / flag.sum()), lift=float((flag & top).sum() / flag.sum() / .1)))
RF = pd.DataFrame(rows); RF.to_csv("reto2_prediccion/reports/alt_riesgo_ranking.csv", index=False); say(RF.round(3).to_string(index=False))
