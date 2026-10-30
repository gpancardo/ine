# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""Prueba de variables adicionales (pobreza/ingreso CONEVAL, violencia SESNSP, ECEG 2010Δ, DENUE) en el backtest. Run: uv run analysis/extra_test.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import features as F, harness as H, stats_util as U, common as c
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

D, nat = H.init()
cw = pd.read_csv("data/processed/mun_crosswalk.csv"); cw = cw[~cw.mun_inegi.duplicated(keep=False)]  # ambiguos -> NaN
D["mun_inegi"] = D.mun.map(cw.set_index("mun_ine").mun_inegi)
mx = pd.read_parquet("data/processed/mun_extra.parquet")
SNAP = {2015: 2010, 2018: 2015, 2021: 2015, 2024: 2020, 2027: 2020}; PREV = {2010: None, 2015: 2010, 2020: 2015}
POV = ["plp", "plp_e", "pobreza", "vul_ing", "ic_rezedu", "ic_asalud", "ic_segsoc", "ic_cv", "ic_sbv", "ic_ali"]
CR = ["hom", "ext", "robo", "narco", "total"]
G = {"pov": [f"pov_{v}" for v in POV], "pov_d": [f"povd_{v}" for v in POV], "crime": [f"cr_{k}" for k in CR] + [f"cr3_{k}" for k in CR], "crime_d": [f"crd_{k}" for k in CR]}
for T in (2015, 2018, 2021, 2024, 2027):
    m = (D["T"] == T).values; keys = D.loc[m, "mun_inegi"]; snap = SNAP[T]
    for v in POV:
        D.loc[m, f"pov_{v}"] = mx[f"{v}_{snap}"].reindex(keys).values
        D.loc[m, f"povd_{v}"] = (mx[f"{v}_{snap}"] - mx[f"{v}_{PREV[snap]}"]).reindex(keys).values if PREV[snap] else np.nan
    y1 = min(T - 1, 2025)
    for k in CR:
        r = lambda y: mx[f"{k}_r_{y}"] if f"{k}_r_{y}" in mx else pd.Series(np.nan, index=mx.index)
        w3 = pd.concat([r(y) for y in range(y1 - 2, y1 + 1)], axis=1).mean(1); w3p = pd.concat([r(y) for y in range(y1 - 5, y1 - 2)], axis=1).mean(1)
        D.loc[m, f"cr_{k}"] = np.log1p(r(y1)).reindex(keys).values; D.loc[m, f"cr3_{k}"] = np.log1p(w3).reindex(keys).values
        D.loc[m, f"crd_{k}"] = (np.log1p(w3) - np.log1p(w3p)).reindex(keys).values
print("cobertura municipal (no nulos) T=2021:", {g: round(D[D["T"] == 2021][cols[0]].notna().mean(), 3) for g, cols in G.items()})
SEM, AGE = F.cols(["sem"]), F.cols(["age"]); REF = SEM + AGE
sets = {"REF S2": REF, "+ pobreza/ingreso (nivel)": REF + G["pov"], "+ pobreza/ingreso (nivel+Δ)": REF + G["pov"] + G["pov_d"], "+ violencia (nivel)": REF + G["crime"], "+ violencia (nivel+Δ)": REF + G["crime"] + G["crime_d"],
        "+ pobreza + violencia": REF + G["pov"] + G["crime"], "+ todo (pobreza,violencia,Δ)": REF + sum(G.values(), [])}
E = {}; rows = []
for n, cs in sets.items():
    for T in (2021, 2024):
        tr = D[D["T"].isin(H.FOLDS[T]) & D.y_rel.notna()]; te = D[(D["T"] == T) & D.y_rel.notna()]; mu = tr[cs].mean().fillna(0)
        for mn, mk in (("Ridge", lambda: H.lin(Ridge(10.0))), ("LGBM", H.lgbm)):
            m_ = mk().fit(tr[cs].fillna(mu).values, tr.y_rel.values); p = m_.predict(te[cs].fillna(mu).values); e = (te.y_rel.values - p) ** 2
            E[(n, mn, T)] = pd.Series(e, index=te.index); rows.append(dict(set=n, modelo=mn, test=T, rmse=np.sqrt(e.mean()), r2=H.score(te.y_rel.values, p)["r2"]))
R = pd.DataFrame(rows)
for i, r in R.iterrows():
    if r.set == "REF S2": continue
    te = D[(D["T"] == r.test) & D.y_rel.notna()]; d, lo, hi, _ = U.boot_delta(E[(r.set, r.modelo, r.test)], E[("REF S2", r.modelo, r.test)], te.mun, B=500); R.loc[i, ["d", "lo", "hi"]] = [d, lo, hi]
pd.set_option("display.width", 220); print(R.round(4).to_string(index=False)); R.to_csv("reto2_prediccion/reports/extra_mun_test.csv", index=False)

# techo estático dentro del año (CV por municipio): ¿aportan poder explicativo aunque no transfieran?
print("\nTecho estático (LGBM, mismo año, CV por municipio), R²:")
for T in (2021, 2024):
    d = D[(D["T"] == T) & D.y_rel.notna()].reset_index(drop=True); y = d.y_rel.values
    for n in ("REF S2", "+ todo (pobreza,violencia,Δ)"):
        cs = sets[n]; P_ = np.zeros(len(d))
        for a, b in GroupKFold(5).split(d, groups=d.mun):
            P_[b] = H.lgbm().fit(d.iloc[a][cs].values, y[a]).predict(d.iloc[b][cs].values)
        print(f"  {T} {n:32s} R²={1 - ((y - P_) ** 2).sum() / ((y - y.mean()) ** 2).sum():.3f}")
