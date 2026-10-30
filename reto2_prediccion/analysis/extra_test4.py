# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""Historia larga por sección (1994-2024, Magar) como features de perfil + calendario estatal verificado. Run: uv run analysis/extra_test4.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import features as F, harness as H, stats_util as U
from sklearn.linear_model import Ridge
D, nat = H.init()
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994]
W = L.pivot(index="sid", columns="year", values="abst_m").clip(0, 1); REL = W - W.mean()
MID = {1997, 2003, 2009, 2015, 2021}; YR = sorted(W.columns)
rows = []
for T in sorted(D["T"].unique()):
    ys = [y for y in YR if y <= T - 3]; same = [y for y in ys if (y in MID) == (T in MID)]; oth = [y for y in ys if y not in same]
    # brecha de ciclo: intermedia menos la presidencial anterior inmediata, promediada sobre ciclos
    gaps = [REL[m] - REL[m - 3] for m in ys if m in MID and (m - 3) in ys]
    f = pd.DataFrame({"T": T, "h_same": REL[same].mean(1), "h_oth": REL[oth].mean(1), "h_sd": REL[ys].std(1), "h_n": REL[ys].notna().sum(1),
                      "h_gap": pd.concat(gaps, axis=1).mean(1) if gaps else np.nan, "h_same_sd": REL[same].std(1)})
    f["h_same_minus_a1"] = f.h_same - D[D["T"] == T].a1.reindex(f.index)
    rows.append(f.reset_index())
X = pd.concat(rows).set_index(["T", "sid"]); keys = pd.MultiIndex.from_arrays([D["T"], D.index])
HC = list(X.columns)
for c in HC: D[c] = X[c].reindex(keys).values
# calendario estatal verificado con Magar: fracción de municipios con elección concurrente con gubernatura / congreso local en el año
cc = pd.read_csv("data/raw/magar_mun/aymu1989-on.concurrence.csv"); cc["yr"] = cc.date // 10000
S = cc.groupby(["edon", "yr"]).agg(g_gob=("dconcgob", "mean"), g_dipl=("dconcdipl", "mean")).reset_index()
ent = (D.mun // 1000).values
for c in ("g_gob", "g_dipl"):
    D[c] = S.set_index(["edon", "yr"])[c].reindex(pd.MultiIndex.from_arrays([ent, D["T"].values])).fillna(0).values
print("cobertura h_same/h_gap en test:", D[D["T"].isin([2021, 2024])][["h_same", "h_gap", "h_n"]].describe().round(2).to_string())
REF = F.cols(["sem"]) + F.cols(["age"])
sets = {"REF S2": REF, "+ hist larga (same,oth,sd)": REF + ["h_same", "h_oth", "h_sd", "h_same_sd"], "+ brecha de ciclo": REF + ["h_gap"],
        "+ hist larga + brecha": REF + HC, "+ calendario verificado": REF + ["g_gob", "g_dipl"], "+ todo": REF + HC + ["g_gob", "g_dipl"]}
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
pd.set_option("display.width", 200); print(R.round(4).to_string(index=False)); R.to_csv("reto2_prediccion/reports/extra_hist_test.csv", index=False)
