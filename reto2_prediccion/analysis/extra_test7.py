# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""Acceso físico a votar: casillas por sección (n, electores por casilla, % extraordinarias; del año T-3) y geometría de la sección (área, densidad, compacidad, distancia al centro municipal).
Run: uv run analysis/extra_test7.py"""
import os, sys, re
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import features as F, harness as H, stats_util as U, common as c
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
D, nat = H.init(); geo = c.load_geo(); cen = c.eceg_features()
# --- casillas por sección y año
def casillas(y):
    f = Path("data/raw/magar") / (f"dip{y}-pre-trife.csv" if y == 2024 else f"dip{y}.csv")
    d = pd.read_csv(f, usecols=["edon", "seccion", "casilla", "lisnom"], low_memory=False); d["sid"] = pd.to_numeric(d.edon, errors="coerce") * 10000 + pd.to_numeric(d.seccion, errors="coerce")
    d = d.dropna(subset=["sid"]); d["sid"] = d.sid.astype(int); k = d.casilla.astype(str).str.upper(); d = d[~k.str.contains("S")]; d["ext"] = k.loc[d.index].str.contains("E").astype(float)
    g = d.groupby("sid").agg(ncas=("casilla", "size"), ext=("ext", "mean"), ln=("lisnom", "sum")); g["ln_cas"] = g.ln / g.ncas; return g[["ncas", "ext", "ln_cas"]]
CAS = {y: casillas(y) for y in (2015, 2018, 2021)}
for T in D["T"].unique():
    pass
cols = ["ncas", "ext", "ln_cas"]
for k in cols: D["cas_" + k] = np.nan
for T in (2018, 2021, 2024):  # fila T usa casillas de T-3
    m = D["T"] == T; g = CAS[T - 3]
    for k in cols: D.loc[m, "cas_" + k] = g[k].reindex(D.index[m]).values
D["cas_ln_cas_log"] = np.log(D.cas_ln_cas); D["cas_ext_any"] = (D.cas_ext > 0).astype(float)
# --- geometría
g = geo.copy(); area = g.geometry.area / 1e6; per = g.geometry.length / 1e3; ctr = g.geometry.centroid
G = pd.DataFrame({"geo_log_area": np.log(area), "geo_compact": 4 * np.pi * area / per ** 2}, index=g.index)
pob = cen.pobtot.reindex(G.index); G["geo_log_dens"] = np.log1p(pob / area)
mun = (D.mun.groupby(level=0).first()).reindex(G.index); xy = pd.DataFrame({"x": ctr.x, "y": ctr.y}, index=G.index)
big = pob.groupby(mun.values).transform("idxmax") if False else None
w = pob.fillna(0); mx = (xy.x * w).groupby(mun.values).transform("sum") / w.groupby(mun.values).transform("sum"); my = (xy.y * w).groupby(mun.values).transform("sum") / w.groupby(mun.values).transform("sum")
G["geo_dist_centro_km"] = np.log1p(np.hypot(xy.x - mx, xy.y - my) / 1e3)  # distancia a centro de masa poblacional del municipio
for k in G: D[k] = G[k].reindex(D.index).values
GRP = {"casillas": ["cas_ncas", "cas_ext", "cas_ln_cas_log", "cas_ext_any"], "geometría": list(G.columns)}
REF = F.cols(["sem"]) + F.cols(["age"]); sets = {"REF S2": REF, "+ casillas (acceso)": REF + GRP["casillas"], "+ geometría": REF + GRP["geometría"], "+ ambos": REF + GRP["casillas"] + GRP["geometría"]}
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
pd.set_option("display.width", 200); print(R.round(4).to_string(index=False)); R.to_csv("reto2_prediccion/reports/extra_acceso_test.csv", index=False)
print("\nTecho estático (LGBM, mismo año, CV por municipio), R²:")
for T in (2021, 2024):
    d = D[(D["T"] == T) & D.y_rel.notna()].reset_index(drop=True); y = d.y_rel.values
    for n in ("REF S2", "+ casillas (acceso)", "+ geometría", "+ ambos"):
        cs = sets[n]; P_ = np.zeros(len(d))
        for a, b in GroupKFold(5).split(d, groups=d.mun): P_[b] = H.lgbm().fit(d.iloc[a][cs].values, y[a]).predict(d.iloc[b][cs].values)
        print(f"  {T} {n:24s} R²={1 - ((y - P_) ** 2).sum() / ((y - y.mean()) ** 2).sum():.3f}")
