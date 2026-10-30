# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost", "statsmodels"]
# ///
"""Información intra-año: incidencia delictiva ene-may del año de la elección (SESNSP mensual) vs el mismo periodo del año previo, como señal del choque municipal.
Run: uv run analysis/intrayear_crime.py"""
import os, sys, pickle
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.formula.api as smf
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import harness as H
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb"))
MES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo"]; cols = ["Año", "Cve. Municipio", "Tipo de delito", "Subtipo de delito"] + MES + ["Junio"]
s = pd.read_csv("data/raw/sesnsp/extracted/Municipal-Delitos-2015-2025_ago2026.csv", encoding="latin-1", usecols=cols)
s["cat"] = np.select([s["Subtipo de delito"].eq("Homicidio doloso"), s["Tipo de delito"].eq("Extorsión"), s["Tipo de delito"].str.startswith("Robo", na=False), s["Subtipo de delito"].eq("Lesiones dolosas")], ["hom", "ext", "robo", "les"], "otro")
s["ene_may"] = s[MES].sum(axis=1); s["total"] = s[MES + ["Junio"]].sum(axis=1)
g = s.groupby(["Cve. Municipio", "Año", "cat"]).ene_may.sum().unstack("cat").fillna(0); g["todo"] = g.sum(axis=1)
xw = pd.read_csv("data/processed/mun_crosswalk.csv").drop_duplicates("mun_inegi").set_index("mun_inegi").mun_ine
rows = {}
for T in (2021, 2024):
    t = D[(D["T"] == T) & D.y_rel.notna()].copy(); t["p"] = P[("Ridge", T)].reindex(t.index); t = t.dropna(subset=["p"]); t["res"] = t.y_rel - t.p
    m = t.groupby("mun").agg(res=("res", "mean"), n=("res", "size"), a1=("a1", "mean"), ln=("ln_T", "sum")).query("n >= 3 and ln > 1000"); m["est"] = m.index // 1000
    for k in ("hom", "ext", "robo", "todo"):
        a = g[k].xs(T, level="Año").rename(index=xw); b = g[k].xs(T - 1, level="Año").rename(index=xw); a, b = a[~a.index.duplicated()], b[~b.index.duplicated()]
        m[f"d_{k}"] = (np.log1p(a.reindex(m.index) ) - np.log1p(b.reindex(m.index)))  # cambio log ene-may T vs T-1
        m[f"r_{k}"] = np.log1p(a.reindex(m.index) / m.ln * 1e4)                            # tasa ene-may T por 10 mil electores
    rows[T] = m
z = lambda s_: (s_ - s_.mean()) / s_.std()
for T, m in rows.items():
    print(f"\n[{T}] municipios={len(m)} con datos de delitos: {m.d_hom.notna().sum()}")
    for k in ("hom", "ext", "robo", "todo"):
        for pre, nm in (("d_", "cambio ene-may vs año previo"), ("r_", "tasa ene-may")):
            d = m.dropna(subset=[pre + k]).copy(); d["x"] = z(d[pre + k])
            fit = smf.wls("res ~ x + C(est)", d, weights=d.n).fit(cov_type="cluster", cov_kwds={"groups": d.est}); print(f"  {k:5s} {nm:30s} {fit.params['x']*100:+.2f} pp/SD (t={fit.tvalues['x']:.1f}) n={len(d)}")
