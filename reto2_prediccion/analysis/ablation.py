# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""Ablación leave-one-group-out desde el modelo amplio (S10) y a nivel de feature dentro de 'sem'. IC95% bootstrap por municipio.
Run: uv run analysis/ablation.py -> reto2_prediccion/reports/ablation.csv"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import features as F, harness as H, stats_util as U
from sklearn.linear_model import Ridge

D, nat = H.init()
FULL = ["sem", "age", "census", "space", "mun", "struct", "qual"]
MODELS = {"Ridge": lambda: H.lin(Ridge(10.0)), "LightGBM": H.lgbm}


def err2(mk, cols, T):
    Xtr, ytr, Xte, yte, te = H.split(D, T, cols if isinstance(cols, list) and cols and cols[0] in F.GROUPS else None) if False else (None,) * 5
    tr = D[D["T"].isin(H.FOLDS[T]) & D.y_rel.notna()]; te = D[(D["T"] == T) & D.y_rel.notna()]
    m = mk().fit(tr[cols].values, tr.y_rel.values)
    return (te.y_rel - m.predict(te[cols].values)) ** 2, te.mun


rows = []
for mn, mk in MODELS.items():
    for T in (2021, 2024):
        ref_e, mun = err2(mk, F.cols(FULL), T)
        rr, ci = U.boot_rmse(ref_e, mun)
        rows.append(dict(modelo=mn, test=T, variante="REFERENCIA: todo (S10)", rmse=rr, delta=0, lo=np.nan, hi=np.nan, p=np.nan))
        for g in FULL:  # quitar un grupo
            e, _ = err2(mk, F.cols([x for x in FULL if x != g]), T)
            d, lo, hi, p = U.boot_delta(e, ref_e, mun); rows.append(dict(modelo=mn, test=T, variante=f"− {g}", rmse=float(np.sqrt(e.mean())), delta=d, lo=lo, hi=hi, p=p))
        e, _ = err2(mk, F.cols(["sem"]), T); d, lo, hi, p = U.boot_delta(e, ref_e, mun)
        rows.append(dict(modelo=mn, test=T, variante="solo sem (P1,M1,P2,M2,tipo)", rmse=float(np.sqrt(e.mean())), delta=d, lo=lo, hi=hi, p=p))
        e, _ = err2(mk, F.cols(["lag"]), T); d, lo, hi, p = U.boot_delta(e, ref_e, mun)
        rows.append(dict(modelo=mn, test=T, variante="solo lag posicional (a1,a2,Δ)", rmse=float(np.sqrt(e.mean())), delta=d, lo=lo, hi=hi, p=p))
        print(mn, T, "ok", flush=True)

# nivel feature dentro de 'sem' (Ridge), referencia = sem completo
sem = F.cols(["sem"])
for T in (2021, 2024):
    ref_e, mun = err2(MODELS["Ridge"], sem, T)
    for f in sem:
        e, _ = err2(MODELS["Ridge"], [x for x in sem if x != f], T); d, lo, hi, p = U.boot_delta(e, ref_e, mun)
        rows.append(dict(modelo="Ridge[sem]", test=T, variante=f"− {f}", rmse=float(np.sqrt(e.mean())), delta=d, lo=lo, hi=hi, p=p))
A = pd.DataFrame(rows); A.to_csv("reto2_prediccion/reports/ablation.csv", index=False)
pd.set_option("display.width", 200)
print(A.round(4).to_string(index=False))
