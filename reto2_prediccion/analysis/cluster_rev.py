# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn"]
# ///
"""¿Se revierte el choque de cluster entre ciclos consecutivos de forma estable (panel largo, 5 pares)? Si sí, λ<0 es explotable ex ante.
Run: uv run analysis/cluster_rev.py"""
import os, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import common as c
from sklearn.cluster import MiniBatchKMeans
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994]
W = L.pivot(index="sid", columns="year", values="abst_m").clip(0, 1); LN = L.pivot(index="sid", columns="year", values="lisnom"); REL = W - W.mean()
YR = sorted(W.columns); MID = {1997, 2003, 2009, 2015, 2021, 2027}
geo = c.load_geo(); xy = pd.DataFrame(np.c_[geo.geometry.centroid.x, geo.geometry.centroid.y], index=geo.index, columns=["x", "y"])
cen = c.eceg_features(); CUL = ["pct_indigena", "pct_sin_relig", "graproes", "pct_analf", "pct_nac_otra_ent", "pct_soltero", "pct_internet", "pct_piso_tierra", "pct_auto", "sin_servsalud", "pct_65mas", "pct_0_14", "hacinamiento"]
base = W.index.intersection(xy.index).intersection(cen.index)
Z = lambda df: pd.DataFrame(StandardScaler().fit_transform(df.fillna(df.median())), index=df.index, columns=df.columns)
xyz, cul = Z(xy.loc[base]), Z(cen.loc[base, CUL])
LAB = {"geo k=100": MiniBatchKMeans(100, n_init=3, random_state=0, batch_size=8192).fit_predict(xyz.values),
       "cultural k=100": MiniBatchKMeans(100, n_init=3, random_state=0, batch_size=8192).fit_predict(cul.values),
       "geo+cultural k=100": MiniBatchKMeans(100, n_init=3, random_state=0, batch_size=8192).fit_predict(np.c_[xyz.values * 3, cul.values])}
LAB = {k: pd.Series(v, index=base) for k, v in LAB.items()}

def build(T):
    ys = [y for y in YR if y <= T - 3]; pres = [y for y in ys if y not in MID][::-1]; mid = [y for y in ys if y in MID][::-1]
    d = pd.DataFrame(index=base); d["y"] = REL[T].reindex(base); d["ln"] = LN[T].reindex(base); m = float(T in MID)
    for i in range(2): d[f"P{i+1}"] = REL[pres[i]].reindex(base); d[f"M{i+1}"] = REL[mid[i]].reindex(base)
    d["is_mid"] = m; d["P1_mid"] = d.P1 * m; d["M1_mid"] = d.M1 * m
    return d.dropna(subset=["P1", "M1", "y"]).query("ln >= 100")
TS = [2006, 2009, 2012, 2015, 2018, 2021, 2024]; D = {T: build(T) for T in TS}
F_ = ["P1", "M1", "P2", "M2", "is_mid", "P1_mid", "M1_mid"]; r2 = lambda y, p: 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
RES = {}
for T in (2012, 2015, 2018, 2021, 2024):
    tt = [t for t in TS if t <= T - 3 and t != 2015][-2:]; tr = pd.concat([D[t] for t in tt]); mu = tr[F_].median()
    m = Ridge(10.0).fit(tr[F_].fillna(mu).values, tr.y.values); te = D[T].copy(); te["p"] = m.predict(te[F_].fillna(mu).values); te["res"] = te.y - te.p; RES[T] = te
print("R² base:", {T: round(r2(RES[T].y, RES[T].p), 3) for T in RES})
PAIRS = [(2009, 2012), (2012, 2015), (2015, 2018), (2018, 2021), (2021, 2024)]; PAIRS = [(a, b) for a, b in PAIRS if a in RES and b in RES]
def cmean(T, lab): return RES[T].res.groupby(lab.reindex(RES[T].index).values).mean()
rows = []
for nm, lab in LAB.items():
    sl = {}
    for a, b in PAIRS:
        x, y = cmean(a, lab), cmean(b, lab); j = x.index.intersection(y.index); sl[(a, b)] = (np.corrcoef(x[j], y[j])[0, 1], np.polyfit(x[j], y[j], 1)[0])
    print(nm, "corr/pendiente por par:", {f"{a}→{b}": (round(v[0], 2), round(v[1], 2)) for (a, b), v in sl.items()})
    for a, b in PAIRS:  # λ estimada con pares anteriores (b' < b), aplicada a b
        prev = [sl[p][1] for p in PAIRS if p[1] < b]
        if not prev: continue
        lam = float(np.mean(prev)); te = RES[b]; shift = te.index.map(lambda s: 0).values
        x = cmean(a, lab); add = lab.reindex(te.index).map(x).fillna(0).values
        rows.append(dict(clustering=nm, par=f"{a}→{b}", lam_previa=round(lam, 3), r2_base=r2(te.y, te.p), r2_con_lambda=r2(te.y, te.p + lam * add), r2_lambda_neg03=r2(te.y, te.p - 0.3 * add)))
R = pd.DataFrame(rows); pd.set_option("display.width", 200); print(R.round(4).to_string(index=False)); R.to_csv("reto2_prediccion/reports/cluster_rev.csv", index=False)
