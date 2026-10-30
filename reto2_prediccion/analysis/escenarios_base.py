# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""Piezas predictivas para los escenarios 2027: (a) choque estatal/municipal del ciclo anterior como predictor del actual (2021->2024);
(b) nivel nacional intermedia: backtest de reglas simples sobre 1994-2024. Run: uv run analysis/escenarios_base.py"""
import os, sys, pickle
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import harness as H
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb"))
r2 = lambda y, p: 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
te = {T: D[(D["T"] == T) & D.y_rel.notna()].assign(p=lambda d: P[("Ridge", T)].reindex(d.index)).dropna(subset=["p"]) for T in (2021, 2024)}
for T in te: te[T]["res"] = te[T].y_rel - te[T].p; te[T]["est"] = te[T].mun // 1000
print("(a) 2024 con choque 2021 trasladado, por nivel y factor λ (R² base %.3f)" % r2(te[2024].y_rel, te[2024].p))
for nm in ("est", "mun"):
    prev = te[2021].groupby(nm).res.mean(); x = te[2024][nm].map(prev).fillna(0)
    print(" ", nm, {lam: round(r2(te[2024].y_rel, te[2024].p + lam * x), 4) for lam in (0, 0.1, 0.2, 0.3, 0.5)})
# (b) nivel nacional (media de secciones, abstención por acta) 1994-2024
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994]
n = L.groupby("year").apply(lambda g: 1 - g.tot.sum() / g.lisnom.sum()); print("\nabstención nacional (acta, dip. federal):", n.round(3).to_dict())
MID = {1997, 2003, 2009, 2015, 2021}; rows = []
for T in (2009, 2015, 2021):
    pm = [y for y in n.index if y in MID and y <= T - 3]; pp = [y for y in n.index if y not in MID and y <= T - 3]
    s_mid = n[pm[-1]]; delta = n[pm[-1]] - n[pp[-1] if pp[-1] < pm[-1] else pp[-2]] if False else None
    last_p, prev_p = n[pp[-1]], n[pp[-2]]
    rows.append(dict(T=T, real=n[T], persist_mid=n[pm[-1]], persist_mid_mas_tendencia_pres=n[pm[-1]] + (last_p - prev_p), mid_menos_pres_ult=last_p + (n[pm[-1]] - n[[y for y in pp if y < pm[-1]][-1]])))
B = pd.DataFrame(rows).set_index("T"); print(B.round(3)); print("error abs medio:", {c: round((B[c] - B.real).abs().mean(), 3) for c in B.columns[1:]})
