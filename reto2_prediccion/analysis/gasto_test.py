# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost", "statsmodels"]
# ///
"""Gasto de campaña (INE, fiscalización; diputaciones federales MR) por distrito vs. choque distrital de la federal (residuo del Ridge honesto).
Explicativo (el gasto final se conoce tras la campaña) y con gasto del ciclo anterior (T-3). Run: uv run analysis/gasto_test.py"""
import os, sys, pickle, unicodedata
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.formula.api as smf
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import harness as H
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb"))
NOM = ["AGUASCALIENTES", "BAJA CALIFORNIA", "BAJA CALIFORNIA SUR", "CAMPECHE", "COAHUILA", "COLIMA", "CHIAPAS", "CHIHUAHUA", "CIUDAD DE MEXICO", "DURANGO", "GUANAJUATO", "GUERRERO", "HIDALGO", "JALISCO", "MEXICO", "MICHOACAN", "MORELOS", "NAYARIT", "NUEVO LEON", "OAXACA", "PUEBLA", "QUERETARO", "QUINTANA ROO", "SAN LUIS POTOSI", "SINALOA", "SONORA", "TABASCO", "TAMAULIPAS", "TLAXCALA", "VERACRUZ", "YUCATAN", "ZACATECAS"]
norm = lambda s: ''.join(c for c in unicodedata.normalize("NFD", str(s).upper().strip()) if unicodedata.category(c) != "Mn")
EDON = {n: i + 1 for i, n in enumerate(NOM)}; ALIAS = {"COAHUILA DE ZARAGOZA": 5, "MICHOACAN DE OCAMPO": 16, "VERACRUZ DE IGNACIO DE LA LLAVE": 30, "DISTRITO FEDERAL": 9, "CDMX": 9, "ESTADO DE MEXICO": 15}
money = lambda s: pd.to_numeric(s.astype(str).str.replace(r"[$,\s]", "", regex=True), errors="coerce")
def spend(y):
    f = {2018: "g2018", 2021: "g2021", 2024: "g2024"}[y]; d = pd.read_csv(f"data/raw/sif/{f}.csv", encoding="utf-8-sig" if y == 2024 else "latin-1", low_memory=False); d.columns = [norm(c) if True else c for c in d.columns]
    pick = lambda *ks: next(c for c in d.columns if all(k in c for k in ks))
    cargo = pick("CARGO"); sub = pick("SUBNIVEL"); ent = pick("ENTIDAD FEDERATIVA") if y == 2018 else pick("ESTADO ELECCION")
    d = d[d[cargo].astype(str).str.contains("DIPUT") & d[cargo].astype(str).str.contains("MR")].copy(); d["edon"] = d[ent].map(lambda s: EDON.get(norm(s), ALIAS.get(norm(s), np.nan)))
    d["disn"] = pd.to_numeric(d[sub].astype(str).str.extract(r"Distrito\s+(\d+)", flags=2)[0], errors="coerce"); tot = pick("TOTAL GASTOS")
    media_cols = [c for c in d.columns if any(k in c for k in ("RADIO", "INTERNET", "VIA PUBLICA", "DIARIOS"))]; d["tot"] = money(d[tot]); d["media"] = sum(money(d[c]).fillna(0) for c in media_cols)
    d["radiotv"] = sum(money(d[c]).fillna(0) for c in d.columns if "RADIO" in c); d["internet"] = sum(money(d[c]).fillna(0) for c in d.columns if "INTERNET" in c)
    tope = [c for c in d.columns if "TOPE" in c]; d["tope"] = money(d[tope[0]]) if tope else np.nan
    g = d.groupby(["edon", "disn"]).agg(tot=("tot", "sum"), media=("media", "sum"), radiotv=("radiotv", "sum"), internet=("internet", "sum"), tope=("tope", "sum"), ncand=("tot", "size")).reset_index(); g["year"] = y; return g
S = pd.concat([spend(y) for y in (2018, 2021, 2024)]); print("distritos por año:", S.groupby("year").size().to_dict(), "| gasto medio por distrito (millones $):", (S.groupby("year").tot.mean() / 1e6).round(2).to_dict(), "| %sin edon:", S.edon.isna().mean().round(3))
def secmap(y):
    f = Path("data/raw/magar") / (f"dip{y}-pre-trife.csv" if y == 2024 else f"dip{y}.csv"); m = pd.read_csv(f, usecols=["edon", "seccion", "disn", "lisnom"], low_memory=False)
    for c in m: m[c] = pd.to_numeric(m[c], errors="coerce")
    m = m.dropna(); m["disn"] = m.disn % 100  # algunos años codifican edon*100+distrito
    m["sid"] = (m.edon * 10000 + m.seccion).astype(int); return m.groupby("sid").agg(edon=("edon", "first"), disn=("disn", "agg" if False else "first"), ln=("lisnom", "sum"))
rows = {}
for T in (2021, 2024):
    t = D[(D["T"] == T) & D.y_rel.notna()].copy(); t["p"] = P[("Ridge", T)].reindex(t.index); t = t.dropna(subset=["p"]); t["res"] = t.y_rel - t.p; sm = secmap(T); t = t.join(sm[["edon", "disn"]], how="inner")
    g = t.groupby(["edon", "disn"]).agg(res=("res", "mean"), n=("res", "size"), a1=("a1", "mean")).reset_index(); lnd = sm.groupby(["edon", "disn"]).ln.sum().rename("ln_d").reset_index(); g = g.merge(lnd, on=["edon", "disn"])
    for lag in (0, 1):
        sy = S[S.year == (T - 3 if lag else T)].copy(); sy.columns = [c if c in ("edon", "disn") else f"{c}_{'prev' if lag else 'cur'}" for c in sy.columns]; g = g.merge(sy.drop(columns=[c for c in sy if c.startswith("year")]), on=["edon", "disn"], how="left")
    for k in ("cur", "prev"):
        g[f"lg_pc_{k}"] = np.log((g[f"tot_{k}"] + 1) / g.ln_d * 1000); g[f"med_sh_{k}"] = g[f"media_{k}"] / g[f"tot_{k}"].replace(0, np.nan); g[f"ncand_{k}"] = g[f"ncand_{k}"]
        g[f"tope_sh_{k}"] = g[f"tot_{k}"] / g[f"tope_{k}"].replace(0, np.nan)
    g["T"] = T; rows[T] = g
G = pd.concat(rows.values()); G.to_csv("reto2_prediccion/reports/gasto_distrito.csv", index=False)
print(f"distritos con gasto: 2021 {rows[2021].tot_cur.notna().sum()}, 2024 {rows[2024].tot_cur.notna().sum()}; con gasto previo: {rows[2021].tot_prev.notna().sum()}, {rows[2024].tot_prev.notna().sum()}")
z = lambda s: (s - s.mean()) / s.std()
for T, g in rows.items():
    g = g.dropna(subset=["lg_pc_cur"]).copy(); sd = g.res.std()
    print(f"\n[{T}] n distritos={len(g)}; sd del choque distrital={sd*100:.2f} pp; corr(choque, log gasto/elector)={np.corrcoef(g.res, g.lg_pc_cur)[0,1]:.3f}")
    for lab, fm in (("gasto actual", "res ~ z_cur + C(edon)"), ("gasto actual + abst. previa", "res ~ z_cur + a1 + C(edon)"), ("gasto del ciclo anterior (T-3)", "res ~ z_prev + C(edon)"), ("share en medios actual", "res ~ zm_cur + C(edon)")):
        g["z_cur"] = z(g.lg_pc_cur); g["z_prev"] = z(g.lg_pc_prev); g["zm_cur"] = z(g.med_sh_cur); d = g.dropna(subset=[c for c in ("z_cur", "z_prev", "zm_cur") if c in fm.replace("zm_cur", "zm_cur")]) if False else g.dropna(subset=["z_cur"] + (["z_prev"] if "z_prev" in fm else []) + (["zm_cur"] if "zm_cur" in fm else []))
        m = smf.wls(fm, d, weights=d.n).fit(cov_type="cluster", cov_kwds={"groups": d.edon}); k = [x for x in m.params.index if x.startswith("z")][0]
        print(f"  {lab:34s} {k}={m.params[k]*100:+.2f} pp/SD (t={m.tvalues[k]:.1f})  R²={m.rsquared:.3f}  n={len(d)}")
