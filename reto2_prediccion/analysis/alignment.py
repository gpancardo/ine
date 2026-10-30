# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "statsmodels"]
# ///
"""Alineación vertical (presidente–gobernador–presidente municipal) y abstención. (1) panel estado×elección: choque estatal ~ gobernador alineado con el presidente / gubernatura concurrente, FE de año;
(2) panel sección×elección con FE de sección y estado×año: presidente municipal alineado con gobernador / presidente. Run: uv run analysis/alignment.py"""
import os, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.formula.api as smf
warnings.filterwarnings("ignore"); os.chdir(Path(__file__).resolve().parents[2])
from sklearn.linear_model import Ridge
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994]
W = L.pivot(index="sid", columns="year", values="abst_m").clip(0, 1); LN = L.pivot(index="sid", columns="year", values="lisnom"); REL = W - W.mean(); YR = sorted(W.columns); MID = {1997, 2003, 2009, 2015, 2021}
fam = lambda s: np.select([s.fillna("").str.contains("morena"), s.fillna("").str.contains("pri"), s.fillna("").str.contains("pan"), s.fillna("").str.contains("prd")], ["morena", "pri", "pan", "prd"], "otro")
PRES = {1994: "pri", 1997: "pri", 2000: "pri", 2003: "pan", 2006: "pan", 2009: "pan", 2012: "pan", 2015: "pri", 2018: "pri", 2021: "morena", 2024: "morena"}  # presidente en funciones en la fecha de la federal
gob = pd.read_csv("data/raw/magar_mun/goed1970-on.incumbents.csv"); gob["din"] = pd.to_datetime(gob["date.in"].astype("Int64").astype(str), format="%Y%m%d", errors="coerce"); gob["fam"] = fam(gob.part)
def gov_at(T):
    cut = pd.Timestamp(f"{T}-06-15"); g = gob[gob.din <= cut].sort_values("din").drop_duplicates("edon", keep="last").set_index("edon"); return g.fam, g.yr
# ---- (1) choque estatal: residuo del Ridge honesto del panel largo (como cluster_rev)
def build(T):
    ys = [y for y in YR if y <= T - 3]; pres = [y for y in ys if y not in MID][::-1]; mid = [y for y in ys if y in MID][::-1]; m = float(T in MID)
    d = pd.DataFrame({"y": REL[T], "ln": LN[T], "P1": REL[pres[0]], "M1": REL[mid[0]], "P2": REL[pres[1]], "M2": REL[mid[1]]}); d["is_mid"] = m; d["P1_mid"] = d.P1 * m; d["M1_mid"] = d.M1 * m
    return d.dropna(subset=["P1", "M1", "y"]).query("ln >= 100")
TS = [2006, 2009, 2012, 2015, 2018, 2021, 2024]; D = {T: build(T) for T in TS}; F_ = ["P1", "M1", "P2", "M2", "is_mid", "P1_mid", "M1_mid"]; rows = []
for T in (2012, 2015, 2018, 2021, 2024):
    tt = [t for t in TS if t <= T - 3 and t != 2015][-2:]; tr = pd.concat([D[t] for t in tt]); mu = tr[F_].median()
    mdl = Ridge(10.0).fit(tr[F_].fillna(mu).values, tr.y.values); te = D[T].copy(); te["res"] = te.y - mdl.predict(te[F_].fillna(mu).values); te["edon"] = te.index // 10000
    s = te.groupby("edon").res.mean().rename("shock").to_frame(); gf, gy = gov_at(T); s["gfam"] = gf.reindex(s.index); s["gyr"] = gy.reindex(s.index); s["T"] = T; s["pres"] = PRES[T]
    s["aligned"] = (s.gfam == s.pres).astype(float); s["gob_conc"] = (s.gyr + 0 >= 0).astype(float) * 0
    rows.append(s.reset_index())
S = pd.concat(rows)
# gubernatura concurrente: elección de gobernador el mismo año T
S["gob_conc"] = [float((gob[(gob.edon == e) & (gob.yr == T)].shape[0]) > 0) for e, T in zip(S.edon, S["T"])]
S["opos"] = ((S.gfam != S.pres) & (S.gfam.isin(["pri", "pan", "prd", "morena"]))).astype(float); S["mid"] = S["T"].isin(MID).astype(float)
print("[1] choque estatal (pp) ~ gobernador alineado con presidente + gubernatura concurrente; FE de año; EE por estado; n =", len(S))
for lab, d in (("todas", S), ("intermedias", S[S.mid == 1]), ("presidenciales", S[S.mid == 0])):
    m = smf.ols("shock ~ aligned + gob_conc + C(T)", d).fit(cov_type="cluster", cov_kwds={"groups": d.edon}); print(f"  {lab:15s} aligned={m.params['aligned']*100:+.2f}pp (t={m.tvalues['aligned']:.1f})  gob_conc={m.params['gob_conc']*100:+.2f}pp (t={m.tvalues['gob_conc']:.1f})  n={len(d)}")
m = smf.ols("shock ~ aligned*mid + gob_conc + C(T)", S).fit(cov_type="cluster", cov_kwds={"groups": S.edon}); print("  interacción aligned×intermedia:", {k: (round(m.params[k] * 100, 2), round(m.tvalues[k], 1)) for k in ("aligned", "aligned:mid")})
by = S.groupby(["T", "aligned"]).shock.mean().unstack() * 100; print("  choque medio por año (pp), alineado=0/1:\n", by.round(2).to_string())
S.to_csv("reto2_prediccion/reports/alignment_state.csv", index=False)
# ---- (2) alineación municipal con FE de sección y estado×año
pn = pd.read_parquet("data/processed/panel.parquet", columns=["EDOCVE", "SECCION", "MPIOCVE"]).drop_duplicates(["EDOCVE", "SECCION"]); pn["sid"] = pn.EDOCVE * 10000 + pn.SECCION; pn["ife"] = pn.EDOCVE * 1000 + pn.MPIOCVE
long = W.stack().rename("y").reset_index().merge(LN.stack().rename("ln").reset_index(), on=["sid", "year"]).query("ln >= 100").merge(pn[["sid", "ife"]], on="sid")
inc = pd.read_csv("data/raw/magar_mun/aymu1989-on.incumbents.csv", low_memory=False)[["ife", "yr", "part"]].dropna(subset=["ife"]).sort_values(["ife", "yr"]); inc["fam"] = fam(inc.part)
mf = {}
for T in YR:
    prev = inc[inc.yr < T].drop_duplicates("ife", keep="last").set_index("ife").fam; mf[T] = prev
long["mfam"] = [mf[t].get(i, np.nan) for t, i in zip(long.year, long.ife)]; long = long.dropna(subset=["mfam"])
long["est"] = long.sid // 10000; gv = {T: gov_at(T)[0] for T in YR}; long["gfam"] = [gv[t].get(e, np.nan) for t, e in zip(long.year, long.est)]; long["pfam"] = long.year.map(PRES)
long["al_mg"] = (long.mfam == long.gfam).astype(float); long["al_mp"] = (long.mfam == long.pfam).astype(float); long["al_ambos"] = long.al_mg * long.al_mp; long["mid"] = long.year.isin(MID).astype(float)
long = long[long.groupby("sid").sid.transform("size") >= 3]
def twfe(d, cols):
    d = d.copy(); d["sy"] = d.est * 10000 + d.year; V = d[["y"] + cols].copy()
    for _ in range(8): V = V - V.groupby(d.sid.values).transform("mean"); V = V - V.groupby(d.sy.values).transform("mean")
    return V
def fit(d, X, tag):
    V = twfe(d, X); Xm = V[X].values; b = np.linalg.lstsq(Xm, V.y.values, rcond=None)[0]; e = V.y.values - Xm @ b; bread = np.linalg.pinv(Xm.T @ Xm); meat = np.zeros((len(X), len(X)))
    for _, ix in d.groupby("ife").indices.items(): s_ = Xm[ix].T @ e[ix]; meat += np.outer(s_, s_)
    se = np.sqrt(np.diag(bread @ meat @ bread)); return pd.DataFrame({"coef_pp": b * 100, "t": b / se, "muestra": tag}, index=X)
X = ["al_mg", "al_mp"]; res = [fit(long, X, "todas"), fit(long[long.year <= 2012], X, "1994-2012"), fit(long[long.year >= 2015], X, "2015-2024"), fit(long[long.mid == 1], X, "intermedias"), fit(long[long.mid == 0], X, "presidenciales")]
R = pd.concat(res).reset_index(names="var"); print("\n[2] abstención de la sección (pp) ~ presidente municipal alineado con gobernador / con presidente (FE sección y estado×año; EE por municipio); obs =", len(long))
print(R.pivot(index="var", columns="muestra", values="coef_pp").round(2).to_string()); print("t:"); print(R.pivot(index="var", columns="muestra", values="t").round(1).to_string()); R.to_csv("reto2_prediccion/reports/alignment_mun.csv", index=False)
