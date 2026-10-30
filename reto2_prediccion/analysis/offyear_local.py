# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "statsmodels"]
# ///
"""Señal del año(s) previo(s): participación en elecciones municipales FUERA de ciclo federal (T-4..T-1) vs. su elección municipal previa;
¿predice el choque municipal de la federal T? Residuos del Ridge honesto del panel largo. Run: uv run analysis/offyear_local.py"""
import os, warnings
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.formula.api as smf
warnings.filterwarnings("ignore"); os.chdir(Path(__file__).resolve().parents[2])
from sklearn.linear_model import Ridge
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994]
W = L.pivot(index="sid", columns="year", values="abst_m").clip(0, 1); LN = L.pivot(index="sid", columns="year", values="lisnom"); REL = W - W.mean()
pn = pd.read_parquet("data/processed/panel.parquet", columns=["EDOCVE", "SECCION", "MPIOCVE"]).drop_duplicates(["EDOCVE", "SECCION"]); pn["sid"] = pn.EDOCVE * 10000 + pn.SECCION; pn["ife"] = pn.EDOCVE * 1000 + pn.MPIOCVE; MUN = pn.set_index("sid").ife
YR = sorted(W.columns); MID = {1997, 2003, 2009, 2015, 2021, 2027}; FED = set(YR)
def build(T):
    ys = [y for y in YR if y <= T - 3]; pres = [y for y in ys if y not in MID][::-1]; mid = [y for y in ys if y in MID][::-1]; m = float(T in MID)
    d = pd.DataFrame({"y": REL[T], "ln": LN[T], "P1": REL[pres[0]], "M1": REL[mid[0]], "P2": REL[pres[1]], "M2": REL[mid[1]]}); d["is_mid"] = m; d["P1_mid"] = d.P1 * m; d["M1_mid"] = d.M1 * m
    return d.dropna(subset=["P1", "M1", "y"]).query("ln >= 100")
TS = [2006, 2009, 2012, 2015, 2018, 2021, 2024]; D = {T: build(T) for T in TS}; F_ = ["P1", "M1", "P2", "M2", "is_mid", "P1_mid", "M1_mid"]
am = pd.read_csv("data/raw/magar_mun/aymu1970-on.csv", low_memory=False, usecols=["ife", "yr", "tot", "lisnom", "status"])
for c in ("tot", "lisnom"): am[c] = pd.to_numeric(am[c], errors="coerce")
am["mpart"] = am.tot / am.lisnom; am = am.dropna(subset=["mpart"]).query("0 < mpart <= 1 and lisnom >= 200").sort_values(["ife", "yr"])
am["mpart_prev"] = am.groupby("ife").mpart.shift(1); am["yr_prev"] = am.groupby("ife").yr.shift(1); am["dpart"] = am.mpart - am.mpart_prev
rows = []
for T in (2015, 2018, 2021, 2024):
    tt = [t for t in TS if t <= T - 3 and t != 2015][-2:]; tr = pd.concat([D[t] for t in tt]); mu = tr[F_].median()
    mdl = Ridge(10.0).fit(tr[F_].fillna(mu).values, tr.y.values); te = D[T].copy(); te["res"] = te.y - mdl.predict(te[F_].fillna(mu).values); te["mun"] = MUN.reindex(te.index).values
    g = te.groupby("mun").res.agg(["mean", "size"]).query("size >= 3").rename(columns={"mean": "res"}); g["est"] = g.index // 1000
    off = am[(am.yr < T) & (am.yr >= T - 4) & ~am.yr.isin(FED) & am.dpart.notna() & (am.yr_prev <= am.yr - 2)].sort_values("yr").drop_duplicates("ife", keep="last").set_index("ife")
    g["dpart"] = off.dpart.reindex(g.index); g["mpart"] = off.mpart.reindex(g.index); g["yr_off"] = off.yr.reindex(g.index)
    d = g.dropna(subset=["dpart"]).copy(); n = len(d)
    if n < 30: rows.append(dict(T=T, n_mun=n, nota="muestra insuficiente")); continue
    d["dp_z"] = (d.dpart - d.dpart.mean()) / d.dpart.std()
    r_raw = np.corrcoef(d.dpart, d.res)[0, 1]
    # dentro de estado (quita contexto estatal): efectos fijos si hay ≥2 estados
    m = smf.ols("res ~ dp_z + C(est)", d).fit(cov_type="HC1") if d.est.nunique() > 1 else smf.ols("res ~ dp_z", d).fit(cov_type="HC1")
    rows.append(dict(T=T, n_mun=n, n_estados=d.est.nunique(), años_off=sorted(d.yr_off.unique().astype(int).tolist()), corr_cruda=r_raw, coef_pp_por_sd=m.params["dp_z"] * 100, t=m.tvalues["dp_z"]))
R = pd.DataFrame(rows); pd.set_option("display.width", 220); print(R.round(3).to_string(index=False)); R.to_csv("reto2_prediccion/reports/offyear_local.csv", index=False)
