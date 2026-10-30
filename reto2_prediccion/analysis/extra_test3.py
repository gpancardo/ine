# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""Calendario municipal (concurrencia ayuntamiento/federal/gubernatura/congreso local) y competitividad de la última elección municipal. Run: uv run analysis/extra_test3.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import features as F, harness as H, stats_util as U
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

D, nat = H.init()
M = Path("data/raw/magar_mun")
cc = pd.read_csv(M / "aymu1989-on.concurrence.csv"); cc["yr"] = cc.date // 10000
am = pd.read_csv(M / "aymu1970-on.csv", low_memory=False)[["emm", "yr", "ife", "edon", "v01", "v02", "tot", "lisnom"]]
am["mun"] = am.ife
inc = pd.read_csv(M / "aymu1989-on.incumbents.csv", low_memory=False)[["emm", "yr", "mg"]]
m = cc.merge(am[["emm", "yr", "ife", "tot", "lisnom"]], on=["emm", "yr"], how="left").merge(inc, on=["emm", "yr"], how="left")
m["mun"] = m.ife; m = m.dropna(subset=["mun"]); m["mun"] = m.mun.astype(int)
for c_ in ("tot", "lisnom", "mg"): m[c_] = pd.to_numeric(m[c_], errors="coerce")
m["mpart"] = m.tot / m.lisnom
rows = []
for T in (2012, 2015, 2018, 2021, 2024):
    cur = m[m.yr == T].drop_duplicates("mun").set_index("mun")
    prev = m[(m.yr <= T - 1) & (m.yr >= T - 7)].sort_values("yr").drop_duplicates("mun", keep="last").set_index("mun")
    out = pd.DataFrame({"T": T}, index=sorted(set(D[D["T"] == T].mun)))
    out["muni_T"] = out.index.isin(cur.index).astype(float)
    out["conc_dipf_T"] = cur.dconcdipf.reindex(out.index).fillna(0)
    out["conc_gob_T"] = cur.dconcgob.reindex(out.index).fillna(0)
    out["conc_dipl_T"] = cur.dconcdipl.reindex(out.index).fillna(0)
    out["mg_prev"] = prev.mg.reindex(out.index)
    out["mpart_prev"] = prev.mpart.reindex(out.index)
    rows.append(out.reset_index(names="mun"))
X = pd.concat(rows)
print(X.groupby("T")[["muni_T", "conc_dipf_T", "conc_gob_T", "conc_dipl_T", "mg_prev", "mpart_prev"]].mean().round(3))
keys = pd.MultiIndex.from_frame(D[["T", "mun"]])
for c in ["muni_T", "conc_dipf_T", "conc_gob_T", "conc_dipl_T", "mg_prev", "mpart_prev"]:
    D[c] = X.set_index(["T", "mun"])[c].reindex(keys).values
REF = F.cols(["sem"]) + F.cols(["age"])
sets = {"REF S2": REF, "+ calendario T (oráculo)": REF + ["muni_T", "conc_dipf_T", "conc_gob_T", "conc_dipl_T"],
        "+ margen/participación municipal previa": REF + ["mg_prev", "mpart_prev"], "+ ambos": REF + ["muni_T", "conc_dipf_T", "conc_gob_T", "conc_dipl_T", "mg_prev", "mpart_prev"]}
E = {}; rows = []
for n, cs in sets.items():
    for T in (2021, 2024):
        tr = D[D["T"].isin(H.FOLDS[T]) & D.y_rel.notna()]; te = D[(D["T"] == T) & D.y_rel.notna()]; mu = tr[cs].mean().fillna(0)
        for mn, mk in (("Ridge", lambda: H.lin(Ridge(10.0))), ("LGBM", H.lgbm)):
            p = mk().fit(tr[cs].fillna(mu).values, tr.y_rel.values).predict(te[cs].fillna(mu).values); e = (te.y_rel.values - p) ** 2
            E[(n, mn, T)] = pd.Series(e, index=te.index); rows.append(dict(set=n, modelo=mn, test=T, rmse=np.sqrt(e.mean()), r2=H.score(te.y_rel.values, p)["r2"]))
R = pd.DataFrame(rows)
for i, r in R.iterrows():
    if r.set == "REF S2": continue
    te = D[(D["T"] == r.test) & D.y_rel.notna()]; d, lo, hi, _ = U.boot_delta(E[(r.set, r.modelo, r.test)], E[("REF S2", r.modelo, r.test)], te.mun, B=500); R.loc[i, ["d", "lo", "hi"]] = [d, lo, hi]
pd.set_option("display.width", 200); print(R.round(4).to_string(index=False)); R.to_csv("reto2_prediccion/reports/extra_calendario_test.csv", index=False)
