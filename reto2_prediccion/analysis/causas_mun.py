# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost", "statsmodels"]
# ///
"""Explicar (no predecir) el choque municipal 2021/2024 con variables político-jurisdiccionales: sede abierta, alternancia, reelección, margen, partido en el poder.
Con efectos fijos de estado. ¿Los mismos factores operan en ambos años? Run: uv run analysis/causas_mun.py"""
import os, sys, pickle
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.formula.api as smf
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import harness as H
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb"))
inc = pd.read_csv("data/raw/magar_mun/aymu1989-on.incumbents.csv", low_memory=False); inc["mg"] = pd.to_numeric(inc.mg, errors="coerce"); inc["mun"] = inc.ife
cc = pd.read_csv("data/raw/magar_mun/aymu1989-on.concurrence.csv"); cc["yr"] = cc.date // 10000; cc = cc.merge(inc[["emm", "yr", "mun"]].drop_duplicates(), on=["emm", "yr"])
fam = lambda s: np.select([s.fillna("").str.contains("morena"), s.fillna("").str.contains("pan"), s.fillna("").str.contains("pri")], ["morena", "pan", "pri"], "otro")
rows = {}
for T in (2021, 2024):
    t = D[(D["T"] == T) & D.y_rel.notna()].copy(); t["p"] = P[("Ridge", T)].reindex(t.index); t = t.dropna(subset=["p"]); t["res"] = t.y_rel - t.p
    g = t.groupby("mun").agg(res=("res", "mean"), n=("res", "size"), a1=("a1", "mean")).query("n >= 3"); g["est"] = g.index // 1000
    prev = inc[(inc.yr == T - 3)].drop_duplicates("mun").set_index("mun"); cur = inc[inc.yr == T].drop_duplicates("mun").set_index("mun")
    ra = prev["race.after"].reindex(g.index).fillna("")  # resultado de la elección T para el periodo que empezó en T-3
    g["sede_abierta"] = (ra.str.startswith("Term-limited") | ra.str.startswith("Out")).astype(float); g["reeleccion"] = ra.str.startswith("Reelected").astype(float)
    g["alternancia"] = ra.str.contains("lost|beaten").astype(float); g["fallecido"] = ra.str.contains("Dead").astype(float)
    g["mg"] = cur.mg.reindex(g.index); g["mg2"] = g.mg ** 2
    g["muni_T"] = g.index.isin(cur.index).astype(float)
    g["gana"] = pd.Series(fam(cur.part.reindex(g.index)), g.index); g["previo"] = pd.Series(fam(prev.part.reindex(g.index)), g.index)
    g["gob"] = cc[cc.yr == T].drop_duplicates("mun").set_index("mun").dconcgob.reindex(g.index).fillna(0)
    rows[T] = g
CAUSAS = "sede_abierta + reeleccion + alternancia + mg + C(gana) + C(previo) + gob"
out = {}
for T, g in rows.items():
    d = g[g.muni_T == 1].dropna(subset=["mg"])
    m0 = smf.wls("res ~ C(est)", d, weights=d.n).fit(); m1 = smf.wls(f"res ~ C(est) + {CAUSAS}", d, weights=d.n).fit()
    mx = smf.wls(f"res ~ C(est) + {CAUSAS} + a1", d, weights=d.n).fit()
    print(f"\n[{T}] municipios con elección concurrente n={len(d)}: R² solo estado {m0.rsquared:.3f} → + causas {m1.rsquared:.3f} → + abstención previa {mx.rsquared:.3f}")
    ci = m1.conf_int(); keep = [k for k in m1.params.index if not k.startswith("C(est)") and k != "Intercept"]
    out[T] = m1.params[keep]; print((m1.params[keep] * 100).round(2).to_frame("coef (pp)").assign(t=m1.tvalues[keep].round(1)).to_string())
j = out[2021].index.intersection(out[2024].index); print("\ncorr de coeficientes 2021 vs 2024 (causas):", round(np.corrcoef(out[2021][j], out[2024][j])[0, 1], 2), "n =", len(j))
