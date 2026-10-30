# /// script
# dependencies = ["pandas", "pyarrow", "scikit-learn", "lightgbm", "numpy"]
# ///
"""¿Alineación política + gubernatura concurrente mejoran la predicción ex ante? Rolling-origin en el panel largo (entrena con todos los objetivos pasados desde 2006, sin 2015).
Run: uv run analysis/alignment_pred.py"""
import os, warnings
from pathlib import Path
import numpy as np, pandas as pd
warnings.filterwarnings("ignore"); os.chdir(Path(__file__).resolve().parents[2])
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from lightgbm import LGBMRegressor
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994]
W = L.pivot(index="sid", columns="year", values="abst_m").clip(0, 1); LN = L.pivot(index="sid", columns="year", values="lisnom"); REL = W - W.mean(); YR = sorted(W.columns); MID = {1997, 2003, 2009, 2015, 2021, 2027}
fam = lambda s: np.select([s.fillna("").str.contains("morena"), s.fillna("").str.contains("pri"), s.fillna("").str.contains("pan"), s.fillna("").str.contains("prd")], ["morena", "pri", "pan", "prd"], "otro")
PRES = {1994: "pri", 1997: "pri", 2000: "pri", 2003: "pan", 2006: "pan", 2009: "pan", 2012: "pan", 2015: "pri", 2018: "pri", 2021: "morena", 2024: "morena", 2027: "morena"}
gob = pd.read_csv("data/raw/magar_mun/goed1970-on.incumbents.csv"); gob["din"] = pd.to_datetime(gob["date.in"].astype("Int64").astype(str), format="%Y%m%d", errors="coerce"); gob["fam"] = fam(gob.part)
def gov_at(T): g = gob[gob.din <= pd.Timestamp(f"{T}-06-15")].sort_values("din").drop_duplicates("edon", keep="last").set_index("edon"); return g.fam
pn = pd.read_parquet("data/processed/panel.parquet", columns=["EDOCVE", "SECCION", "MPIOCVE"]).drop_duplicates(["EDOCVE", "SECCION"]); pn["sid"] = pn.EDOCVE * 10000 + pn.SECCION; pn["ife"] = pn.EDOCVE * 1000 + pn.MPIOCVE; IFE = pn.set_index("sid").ife
inc = pd.read_csv("data/raw/magar_mun/aymu1989-on.incumbents.csv", low_memory=False)[["ife", "yr", "part"]].dropna(subset=["ife"]).sort_values(["ife", "yr"]); inc["fam"] = fam(inc.part)
def build(T):
    ys = [y for y in YR if y <= T - 3]; pres = [y for y in ys if y not in MID][::-1]; mid = [y for y in ys if y in MID][::-1]; m = float(T in MID)
    d = pd.DataFrame({"y": REL[T] if T in REL else np.nan, "ln": LN[T] if T in LN else 1000.0, "P1": REL[pres[0]], "M1": REL[mid[0]], "P2": REL[pres[1]], "M2": REL[mid[1]]}); d["is_mid"] = m; d["P1_mid"] = d.P1 * m; d["M1_mid"] = d.M1 * m
    est = pd.Series(d.index // 10000, d.index); gf = est.map(gov_at(T)); mf = IFE.reindex(d.index).map(inc[inc.yr < T].drop_duplicates("ife", keep="last").set_index("ife").fam)
    d["gc"] = est.map(lambda e: float(((gob.edon == e) & (gob.yr == T)).any())).values  # gubernatura concurrente (verificada con Magar)
    d["ga"] = (gf == PRES[T]).astype(float).values; d["ma"] = (mf == PRES[T]).astype(float).values; d["mg"] = (mf.values == gf.values).astype(float)
    for c in ("gc", "ga", "ma", "mg"): d[c + "_mid"] = d[c] * m
    return d.dropna(subset=["P1", "M1"]).query("ln >= 100")
TS = [2006, 2009, 2012, 2015, 2018, 2021, 2024, 2027]; D = {T: build(T) for T in TS}
REF = ["P1", "M1", "P2", "M2", "is_mid", "P1_mid", "M1_mid"]; AL = ["gc", "ga", "ma", "mg"]; ALI = AL + [c + "_mid" for c in AL]
sets = {"REF": REF, "+ gubernatura concurrente": REF + ["gc", "gc_mid"], "+ alineación (gob, mun-pres, mun-gob)": REF + ["ga", "ma", "mg", "ga_mid", "ma_mid", "mg_mid"], "+ todo": REF + ALI}
lin = lambda: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(10.0))
lgb = lambda: make_pipeline(SimpleImputer(strategy="median"), LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=31, min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=8))
r2 = lambda y, p: 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum(); rows = []
for T in (2012, 2015, 2018, 2021, 2024):
    tt = [t for t in TS if 2006 <= t <= T - 3 and t != 2015 and t != 2027]; tr = pd.concat([D[t] for t in tt]).dropna(subset=["y"]); te = D[T].dropna(subset=["y"])
    for n, cs in sets.items():
        for mn, mk in (("Ridge", lin), ("LGBM", lgb)): rows.append(dict(T=T, set=n, model=mn, r2=r2(te.y, mk().fit(tr[cs].values, tr.y.values).predict(te[cs].values)), ntr=len(tt)))
R = pd.DataFrame(rows).pivot_table(index=["model", "set"], columns="T", values="r2"); pd.set_option("display.width", 200); print(R.round(3).to_string()); R.to_csv("reto2_prediccion/reports/alignment_pred.csv")
print("\nmedia de ganancia vs REF (5 pruebas):"); 
for mn in ("Ridge", "LGBM"):
    base = R.loc[(mn, "REF")]; print(mn, {s: round(float((R.loc[(mn, s)] - base).mean()), 4) for s in sets if s != "REF"}, "| mínimo:", {s: round(float((R.loc[(mn, s)] - base).min()), 3) for s in sets if s != "REF"})
