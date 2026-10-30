# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""A) selección de configuración de features (dev=fold 2021)  B) benchmark multimodelo (ambos folds).
Run: uv run analysis/benchmark.py  ->  reto2_prediccion/reports/feature_configs.csv, reto2_prediccion/reports/benchmark.csv, public/benchmark_results.json"""
import json, os, sys, time
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib"))
os.chdir(Path(__file__).resolve().parents[2])  # rutas relativas a la raíz del proyecto
import features as F, harness as H

D, nat = H.init()
Path("reports").mkdir(exist_ok=True)
print({T: len(D[(D["T"] == T)]) for T in D["T"].unique()})

# ---------- A) configuraciones de features: LightGBM y Ridge, fold 2021 (dev) y 2024 (confirmación) ----------
CONFIGS = {
    "S0 lag posicional (a1,a2,Δ) [referencia]": ["lag"],
    "S1 sem (P1,M1,P2,M2,tipo)": ["sem"],
    "S2 sem+edad/sexo": ["sem", "age"],
    "S3 sem+censo": ["sem", "census"],
    "S4 sem+espacial": ["sem", "space"],
    "S5 sem+municipal": ["sem", "mun"],
    "S6 sem+estructura": ["sem", "struct"],
    "S7 sem+calidad(NS)": ["sem", "qual"],
    "S8 sem+gubernaturas": ["sem", "gob"],
    "S9 sem+historia": ["sem", "hist"],
    "S10 sem+todo (sin estado)": ["sem", "age", "census", "space", "mun", "struct", "qual"],
    "S11 sem+todo+estado": ["sem", "age", "census", "space", "mun", "struct", "qual", "state"],
    "S12 solo censo+estructura (sin historia)": ["census", "struct"],
}
rows = []
for name, g in CONFIGS.items():
    for mn, mk in (("Ridge", lambda: H.lin(__import__("sklearn.linear_model", fromlist=["Ridge"]).Ridge(10.0))), ("LightGBM", H.lgbm)):
        for T in (2021, 2024):
            t0 = time.time(); s, _, _ = H.run(mk, g, T)
            rows.append(dict(config=name, modelo=mn, test=T, n_feat=len(F.cols(g)), **s)); print(name, mn, T, round(s["rmse"], 4), f"{time.time() - t0:.0f}s", flush=True)
fc = pd.DataFrame(rows); fc.to_csv("reto2_prediccion/reports/feature_configs.csv", index=False)
pv = fc.pivot_table(index="config", columns=["modelo", "test"], values="rmse")
pv["media"] = pv.mean(axis=1); print(pv.round(4).sort_values("media").to_string())
BEST = pv.media.idxmin(); print("CONFIG ELEGIDA (min RMSE medio, ambos modelos y folds):", BEST)

# ---------- B) benchmark multimodelo sobre la config elegida + líneas base ----------
from sklearn.linear_model import Lasso, Ridge, LinearRegression
g = CONFIGS[BEST]
cols_base = {"Baseline_a1 (elección adyacente)": ["a1"], "Baseline_P1 (última presidencial)": ["P1"], "Baseline_M1 (última intermedia)": ["M1"], "Baseline_media_historia": ["mean_prev"]}
MODELS = {"OLS_sem (P1,M1,P2,M2)": (lambda: H.lin(LinearRegression()), ["sem"]), "Lasso": (lambda: H.lin(Lasso(0.0005)), g), "Ridge": (lambda: H.lin(Ridge(10.0)), g),
          "Random_Forest": (H.rf, g), "LightGBM": (H.lgbm, g), "CatBoost": (H.cat, g), "Stacking": (H.stack, g)}
res, preds = [], {}
for T in (2021, 2024):
    te = D[(D["T"] == T) & D.y_rel.notna()]
    res.append(dict(modelo="Baseline_Const0 (media nacional)", test=T, **H.score(te.y_rel.values, 0 * te.y_rel.values, te.ln_T.values)))
    for n, cs in cols_base.items():
        t2 = te.dropna(subset=cs); res.append(dict(modelo=n, test=T, **H.score(t2.y_rel.values, t2[cs[0]].values, t2.ln_T.values)))
    for n, (mk, gg) in MODELS.items():
        t0 = time.time(); s_, p, te2 = H.run(mk, gg, T); preds[(n, T)] = pd.Series(p, index=te2.index)
        res.append(dict(modelo=n, test=T, **s_)); print(n, T, round(s_["rmse"], 4), f"{time.time() - t0:.0f}s", flush=True)
R = pd.DataFrame(res); R.to_csv("reto2_prediccion/reports/benchmark.csv", index=False)
pvb = R.pivot_table(index="modelo", columns="test", values=["rmse", "mae", "r2"]); pvb["rmse_medio"] = pvb["rmse"].mean(axis=1)
print(pvb.round(4).sort_values("rmse_medio").to_string())
json.dump({"config": BEST, "groups": g}, open("reto2_prediccion/reports/best_config.json", "w"))
Path("data/processed").mkdir(parents=True, exist_ok=True); pd.to_pickle(preds, "data/processed/benchmark_preds.pkl")
