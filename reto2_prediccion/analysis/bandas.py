# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""Bandas de incertidumbre por sección: ¿los cuantiles del residuo de un ciclo cubren el siguiente? Calibra en 2021, evalúa en 2024 (y a la inversa como referencia).
Variantes: global; por tipo de sección (urbana/rural/mixta); por tipo × tamaño; ajustada con el choque estatal (agrega ruido de nivel estatal). Run: uv run analysis/bandas.py"""
import os, sys, pickle
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import harness as H
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb"))
T_ = {}
for T in (2021, 2024):
    t = D[(D["T"] == T) & D.y_rel.notna()].copy(); t["p"] = P[("Ridge", T)].reindex(t.index); t = t.dropna(subset=["p"]); t["res"] = t.y_rel - t.p
    t["tipo"] = np.where(t.tipo_R == 1, "R", np.where(t.tipo_U == 1, "U", "M")); t["tam"] = pd.qcut(t.log_ln1, 4, labels=False, duplicates="drop"); t["est"] = t.mun // 1000; T_[T] = t
def band(cal, ev, by, lo=0.1, hi=0.9):
    if by is None: q = cal.res.quantile([lo, hi]); a, b = q.iloc[0], q.iloc[1]; L_, U_ = np.full(len(ev), a), np.full(len(ev), b)
    else:
        q = cal.groupby(by).res.quantile([lo, hi]).unstack(); k = ev.set_index(by).index if isinstance(by, str) else pd.MultiIndex.from_frame(ev[by]); q = q.reindex(k); L_, U_ = q.iloc[:, 0].fillna(cal.res.quantile(lo)).values, q.iloc[:, 1].fillna(cal.res.quantile(hi)).values
    inside = ((ev.res.values >= L_) & (ev.res.values <= U_)); return inside.mean(), (U_ - L_).mean(), inside
rows = []
for cal_T, ev_T in ((2021, 2024), (2024, 2021)):
    cal, ev = T_[cal_T], T_[ev_T]
    for nm, by in (("global", None), ("tipo sección", "tipo"), ("tipo × tamaño", ["tipo", "tam"])):
        cov, w, ins = band(cal, ev, by); ev = ev.assign(**{"in_" + nm: ins}); rows.append(dict(calibra=cal_T, evalua=ev_T, banda=nm, cobertura_80=cov, ancho_pp=w * 100))
    # cobertura por estado con la banda global: ¿qué tan heterogénea es?
    cs = ev.groupby("est")["in_global"].mean(); rows.append(dict(calibra=cal_T, evalua=ev_T, banda="(cobertura por estado, banda global): min/mediana/max", cobertura_80=f"{cs.min():.2f}/{cs.median():.2f}/{cs.max():.2f}", ancho_pp=np.nan))
R = pd.DataFrame(rows); pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 80); print(R.to_string(index=False)); R.to_csv("reto2_prediccion/reports/bandas.csv", index=False)
