# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""(1) Cargas de respuesta al cambio nacional por estado/municipio/sección (histórico 1994+), como features; (2) persistencia del choque estatal/municipal.
Run: uv run analysis/extra_test6.py"""
import os, sys, pickle
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import features as F, harness as H, stats_util as U
from sklearn.linear_model import Ridge
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb"))
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994]
W = L.pivot(index="sid", columns="year", values="abst_m").clip(0, 1); REL = W - W.mean(); YR = sorted(W.columns); MID = {1997, 2003, 2009, 2015, 2021, 2027}
ent = pd.Series(W.index // 10000, W.index); mun_of = D.mun.groupby(level=0).first()
# --- (1) brecha de ciclo (respuesta al paso presidencial->intermedia o inverso) a distintos niveles
rows = []
for T in sorted(D["T"].unique()):
    ys = [y for y in YR if y <= T - 3]
    if T in MID: pairs = [(REL[y] - REL[y - 3]) for y in ys if y in MID and y - 3 in ys]       # pres -> intermedia
    else: pairs = [(REL[y] - REL[y - 3]) for y in ys if y not in MID and y - 3 in ys and (y - 3) in MID]  # intermedia -> pres
    g = pd.concat(pairs, axis=1).mean(1); df = pd.DataFrame({"T": T, "g_sec": g})
    df["g_est"] = g.groupby(ent.reindex(df.index).values).transform("mean"); df["g_mun"] = g.groupby(mun_of.reindex(df.index).values).transform("mean")
    rows.append(df.reset_index())
X = pd.concat(rows).set_index(["T", "sid"]); keys = pd.MultiIndex.from_arrays([D["T"], D.index])
for c in X: D[c] = X[c].reindex(keys).values
REF = F.cols(["sem"]) + F.cols(["age"]); sets = {"REF S2": REF, "+ carga estado": REF + ["g_est"], "+ carga municipio": REF + ["g_mun"], "+ carga sección": REF + ["g_sec"], "+ estado+mun+sec": REF + ["g_est", "g_mun", "g_sec"]}
E = {}; out = []
for n, cs in sets.items():
    for T in (2021, 2024):
        tr = D[D["T"].isin(H.FOLDS[T]) & D.y_rel.notna()]; te = D[(D["T"] == T) & D.y_rel.notna()]; mu = tr[cs].mean().fillna(0)
        for mn, mk in (("Ridge", lambda: H.lin(Ridge(10.0))), ("LGBM", H.lgbm)):
            p = mk().fit(tr[cs].fillna(mu).values, tr.y_rel.values).predict(te[cs].fillna(mu).values); e = (te.y_rel.values - p) ** 2
            E[(n, mn, T)] = pd.Series(e, index=te.index); out.append(dict(set=n, modelo=mn, test=T, rmse=np.sqrt(e.mean()), r2=H.score(te.y_rel.values, p)["r2"]))
R = pd.DataFrame(out)
for i, r in R.iterrows():
    if r.set == "REF S2": continue
    te = D[(D["T"] == r.test) & D.y_rel.notna()]; d, lo, hi, _ = U.boot_delta(E[(r.set, r.modelo, r.test)], E[("REF S2", r.modelo, r.test)], te.mun, B=500); R.loc[i, ["d", "lo", "hi"]] = [d, lo, hi]
pd.set_option("display.width", 200); print(R.round(4).to_string(index=False)); R.to_csv("reto2_prediccion/reports/extra_cargas_test.csv", index=False)
# --- (2) persistencia del choque (residuo del modelo honesto) 2021 -> 2024 por estado y municipio
res = {}
for T in (2021, 2024):
    te = D[(D["T"] == T) & D.y_rel.notna()]; p = P[("Ridge", T)].reindex(te.index); r = (te.y_rel - p).dropna(); res[T] = r
for nm, key in (("estado", lambda i: i // 10000), ("municipio", lambda i: D.mun.groupby(level=0).first().reindex(i).values)):
    a = res[2021].groupby(key(res[2021].index)).mean(); b = res[2024].groupby(key(res[2024].index)).mean(); j = a.index.intersection(b.index)
    print(f"persistencia choque {nm}: corr(2021, 2024) = {np.corrcoef(a[j], b[j])[0,1]:.3f} (n={len(j)})")
