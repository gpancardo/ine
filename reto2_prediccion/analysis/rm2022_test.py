# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost", "statsmodels"]
# ///
"""Capacidad de movilización: participación por sección en la Revocación de Mandato 2022 (INE) vs. el choque de la federal 2024 (residuo del Ridge honesto).
Validación solo 2024 (no hay análogo para 2021): CV por municipio y por estado de una regresión del residuo. Run: uv run analysis/rm2022_test.py"""
import os, sys, pickle
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.formula.api as smf
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import harness as H
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb"))
f = "data/raw/rm2022/x/20220411_1845_REVOCACION_MANDATO_2022/20220411_1845_COMPUTOS_RM2022.csv"
c = pd.read_csv(f, skiprows=5, encoding="latin-1", quotechar="'"); c.columns = [x.replace("�", "").replace("Ã", "") for x in c.columns]
rev = [x for x in c.columns if x.startswith("QUE_SE_LE")][0]; sig = [x for x in c.columns if x.startswith("QUE_SIGA")][0]
c = c[(c.ID_ENTIDAD.between(1, 32)) & (c.TIPO_CASILLA != "S")].copy(); c["sid"] = c.ID_ENTIDAD * 10000 + pd.to_numeric(c.iloc[:, 6], errors="coerce")
for k in (rev, sig, "NULOS", "TOTAL_VOTOS_CALCULADOS", "LISTA_NOMINAL"): c[k] = pd.to_numeric(c[k], errors="coerce")
g = c.groupby("sid").agg(votos=("TOTAL_VOTOS_CALCULADOS", "sum"), ln=("LISTA_NOMINAL", "sum"), siga=(sig, "sum"), rev=(rev, "sum"), nulos=("NULOS", "sum"))
g["rm_part"] = (g.votos / g.ln).clip(0, 1); g["rm_siga"] = g.siga / g.ln; g["rm_rev"] = g.rev / g.ln
print(f"secciones con RM2022: {len(g)}; participación nacional {g.votos.sum() / g.ln.sum():.3f}")
T = 2024; t = D[(D["T"] == T) & D.y_rel.notna()].copy(); t["p"] = P[("Ridge", T)].reindex(t.index); t = t.dropna(subset=["p"]); t["res"] = t.y_rel - t.p
L = pd.read_parquet("data/processed/long_magar.parquet"); l21 = L[L.year == 2021].set_index("sid"); vv = [x for x in l21.columns if x.startswith("v_") and x != "v_edosecn"]
t["m21"] = l21[[x for x in vv if "morena" in x]].sum(axis=1).div(l21[vv].sum(axis=1)).reindex(t.index)
for k in ("rm_part", "rm_siga", "rm_rev"): t[k] = g[k].reindex(t.index)
t = t.dropna(subset=["rm_part", "m21"]); t["est"] = t.mun // 1000
for k in ("rm_part", "rm_siga", "rm_rev", "m21"): t[k + "_z"] = (t[k] - t[k].mean()) / t[k].std()
print(f"\nn={len(t)}; corr(residuo 2024, rm_part)={np.corrcoef(t.res, t.rm_part)[0,1]:.3f}; corr(rm_part, abst 2021 rel)={np.corrcoef(t.rm_part, t.a1)[0,1]:.3f}; corr(rm_part, m21)={np.corrcoef(t.rm_part, t.m21)[0,1]:.3f}")
for form in ("res ~ rm_part_z", "res ~ rm_part_z + m21_z", "res ~ rm_part_z + m21_z + C(est)", "res ~ rm_siga_z + rm_rev_z + m21_z + C(est)"):
    m = smf.ols(form, t).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(t.mun)[0]}); k = [x for x in m.params.index if x.startswith("rm_") or x == "m21_z"]
    print(f"{form:52s} R²={m.rsquared:.3f}  " + "  ".join(f"{x}={m.params[x]*100:+.2f}pp(t={m.tvalues[x]:.1f})" for x in k))
# CV: ¿el residuo 2024 se predice con rm2022 en jurisdicciones no vistas?
y = t.res.values; r2 = lambda p: 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
for nm, grp in (("por municipio", t.mun), ("por estado (32 grupos)", t.est)):
    for fs in (["rm_part_z"], ["rm_part_z", "m21_z"], ["rm_siga_z", "rm_rev_z", "m21_z"]):
        pr = np.zeros(len(t))
        for a, b in GroupKFold(8 if nm.startswith("por est") else 5).split(t, groups=grp):
            pr[b] = Ridge(1.0).fit(t.iloc[a][fs].values, y[a]).predict(t.iloc[b][fs].values)
        base = t.y_rel.values; r2tot = 1 - ((base - (t.p.values + pr)) ** 2).sum() / ((base - base.mean()) ** 2).sum()
        print(f"CV {nm:24s} {'+'.join(fs):32s} R² residuo={r2(pr):+.4f}  → R² total 2024: {r2tot:.4f} (base {1 - ((base - t.p.values) ** 2).sum() / ((base - base.mean()) ** 2).sum():.4f})")
