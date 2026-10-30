# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""Pruebas de rigor y validez. Run: uv run analysis/rigor.py -> reto2_prediccion/reports/rigor_*.csv"""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import features as F, harness as H, stats_util as U
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.model_selection import GroupKFold

D, nat = H.init()
cfg = json.load(open("reto2_prediccion/reports/best_config.json")); G = cfg["groups"]; CS = F.cols(G)
preds = pd.read_pickle("data/processed/benchmark_preds.pkl")
P = pd.set_option("display.width", 220)
out = {}


def test_set(T): return D[(D["T"] == T) & D.y_rel.notna()]

# ---------- 1. IC95% (bootstrap por municipio) y diferencias pareadas vs. baseline P1 y vs. Ridge ----------
rows = []
for T in (2021, 2024):
    te = test_set(T); y = te.y_rel; mun = te.mun
    E = {n: (y - preds[(n, T)].reindex(te.index)) ** 2 for (n, t) in preds if t == T}
    E["Baseline_P1"] = (y - te.P1) ** 2; E["Baseline_a1"] = (y - te.a1) ** 2; E["Baseline_Const0"] = y ** 2
    for n, e in E.items():
        ok = e.notna(); r, (lo, hi) = U.boot_rmse(e[ok], mun[ok])
        rows.append(dict(test=T, modelo=n, rmse=r, lo=lo, hi=hi, **{f"d_vs_P1": np.nan, "d_lo": np.nan, "d_hi": np.nan, "p": np.nan}))
        if n != "Baseline_P1":
            ok &= E["Baseline_P1"].notna(); d, dlo, dhi, p = U.boot_delta(e[ok], E["Baseline_P1"][ok], mun[ok])
            rows[-1].update(d_vs_P1=d, d_lo=dlo, d_hi=dhi, p=p)
R1 = pd.DataFrame(rows); R1.to_csv("reto2_prediccion/reports/rigor_ci.csv", index=False); print("== IC95% bootstrap por municipio; Δ vs Baseline_P1 (neg = mejor) ==\n", R1.round(4).to_string(index=False))

# ---------- 2. Heterogeneidad y calibración (mejor modelo = Ridge) ----------
rows = []
for T in (2021, 2024):
    te = test_set(T).copy(); te["p"] = preds[("Ridge", T)].reindex(te.index); te["e"] = te.y_rel - te.p
    sl = LinearRegression().fit(te[["p"]], te.y_rel); rows.append(dict(test=T, corte="calibración (y ~ pred)", grupo=f"pendiente={sl.coef_[0]:.3f} intercepto={sl.intercept_:.4f}", n=len(te), rmse=np.sqrt((te.e ** 2).mean())))
    for nm, key in (("tipo", pd.Series(np.where(te.tipo_U == 1, "U", np.where(te.tipo_R == 1, "R", "M")), index=te.index)), ("tamaño (LN_T)", pd.qcut(te.ln_T, 4, labels=["Q1 chico", "Q2", "Q3", "Q4 grande"])),
                    ("gubernatura en T", te.gob_T.map({1.0: "sí", 0.0: "no"}))):
        for k, g in te.groupby(key): rows.append(dict(test=T, corte=nm, grupo=str(k), n=len(g), rmse=np.sqrt((g.e ** 2).mean())))
    st = te.groupby("ent").e.apply(lambda s: np.sqrt((s ** 2).mean())).sort_values()
    for k in list(st.index[:3]) + list(st.index[-5:]): rows.append(dict(test=T, corte="estado (3 mejores / 5 peores)", grupo=F.c.ESTADOS[int(k)], n=int((te.ent == k).sum()), rmse=st[k]))
R2 = pd.DataFrame(rows); R2.to_csv("reto2_prediccion/reports/rigor_heterogeneidad.csv", index=False); print("\n== Heterogeneidad / calibración (Ridge) ==\n", R2.round(4).to_string(index=False))

# ---------- 3. Placebo: etiquetas barajadas en entrenamiento => R² debe ser ≈ 0 ----------
rng = np.random.default_rng(0); rows = []
for T in (2021, 2024):
    tr = D[D["T"].isin(H.FOLDS[T]) & D.y_rel.notna()]; te = test_set(T)
    for nm, y_tr in (("barajado global", rng.permutation(tr.y_rel.values)), ("barajado dentro de municipio", tr.groupby("mun").y_rel.transform(lambda s: rng.permutation(s.values)).values)):
        m = H.lin(Ridge(10.0)).fit(tr[CS].values, y_tr); rows.append(dict(test=T, placebo=nm, r2=H.score(te.y_rel.values, m.predict(te[CS].values))["r2"]))
R3 = pd.DataFrame(rows); R3.to_csv("reto2_prediccion/reports/rigor_placebo.csv", index=False); print("\n== Placebo (R² esperado ≈ 0) ==\n", R3.round(4).to_string(index=False))

# ---------- 4. Sensibilidad a decisiones de limpieza (Ridge sobre config elegida) ----------
rows = []
base_D = D
w_all = F.c.load_wide(False)
def evalD(Dx, trT, T, label, cols=CS):
    tr = Dx[Dx["T"].isin(trT) & Dx.y_rel.notna()]; te = Dx[(Dx["T"] == T) & Dx.y_rel.notna()]
    m = H.lin(Ridge(10.0)).fit(tr[cols].values, tr.y_rel.values); s = H.score(te.y_rel.values, m.predict(te[cols].values), te.ln_T.values)
    rows.append(dict(test=T, variante=label, n_test=len(te), rmse=s["rmse"], r2=s["r2"], rmse_pond=s["rmse_w"]))
for T in (2021, 2024):
    evalD(D, H.FOLDS[T], T, "decisión adoptada: sin 2015 como objetivo, LN>=100")
    evalD(D, [2015] + H.FOLDS[T], T, "incluyendo 2015 como objetivo")
    for thr in (0, 300, 1000):
        Dn, _ = F.build(); Dn = Dn[~(Dn["T"].isin([2015, 2018, 2021, 2024]) & (Dn.ln_T < thr))]; evalD(Dn, H.FOLDS[T], T, f"LN mínimo = {thr}")
    ns = w_all["ns_2021" if T == 2021 else "ns_2024"].reindex(D.index)
    clean = D[(D["T"] != T) | (ns.values < 0.05)]; evalD(clean, H.FOLDS[T], T, "evaluar solo secciones con NS_T < 5%")
    Dw = D[(D.y_rel.abs() < 0.4) | D.y_rel.isna()]; evalD(Dw, H.FOLDS[T], T, "recortar |y_rel| ≥ 0.40 (outliers)")
R4 = pd.DataFrame(rows); R4.to_csv("reto2_prediccion/reports/rigor_sensibilidad_limpieza.csv", index=False); print("\n== Sensibilidad a limpieza ==\n", R4.round(4).to_string(index=False))

# ---------- 5. Estabilidad por semilla (modelos con aleatoriedad) ----------
rows = []
for T in (2021, 2024):
    for nm, mk in (("LightGBM", lambda s: H.lgbm(random_state=s)), ("CatBoost", lambda s: __import__("catboost").CatBoostRegressor(iterations=400, depth=6, learning_rate=.08, verbose=0, random_seed=s, thread_count=8))):
        r = [H.run(lambda: mk(s), G, T)[0]["rmse"] for s in range(3)]; rows.append(dict(test=T, modelo=nm, rmse_media=np.mean(r), rmse_sd=np.std(r)))
R5 = pd.DataFrame(rows); R5.to_csv("reto2_prediccion/reports/rigor_semillas.csv", index=False); print("\n== Semillas ==\n", R5.round(5).to_string(index=False))

# ---------- 6. Techo y descomposición del error (diagnóstico, no es un modelo desplegable) ----------
rows = []
w = F.c.load_wide(False)
for T in (2021, 2024):
    d = test_set(T).copy(); y = d.y_rel.values; r2 = lambda p: 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    tr = D[D["T"].isin(H.FOLDS[T]) & D.y_rel.notna()]; sem = F.cols(["sem"])
    pt = H.lin(Ridge(10.0)).fit(tr[CS].values, tr.y_rel.values).predict(d[CS].values)
    po = H.lin(LinearRegression()).fit(d[sem].values, y).predict(d[sem].values)  # pesos de rezago del propio año
    res = y - po; gm = d.assign(res=res).groupby("mun").res; loo = ((gm.transform("sum") - res) / (gm.transform("count") - 1).replace(0, np.nan)).fillna(0).values
    P_ = np.zeros(len(d))
    for a, b in GroupKFold(5).split(d, groups=d.mun):
        P_[b] = H.lgbm().fit(d.iloc[a][F.cols(F.ALL_NOSTATE)].values, y[a]).predict(d.iloc[b][F.cols(F.ALL_NOSTATE)].values)
    pa = w[f"abst_{T}"].reindex(d.index); nn = (w[f"ln_{T}"] * (1 - w[f"ns_{T}"])).reindex(d.index); bv = (pa * (1 - pa) / nn).mean()
    for k, v in (("honesto: modelo elegido (temporal)", r2(pt)), ("oráculo: pesos de rezago del propio año", r2(po)), ("oráculo + media municipal LOO del residuo (FUGA)", r2(po + loo)),
                 ("estático: LGBM todas las features, mismo año, CV por municipio", r2(P_)), ("ruido binomial (fracción de varianza irreducible)", bv / np.var(y))):
        rows.append(dict(test=T, concepto=k, valor=v))
R6 = pd.DataFrame(rows); R6.to_csv("reto2_prediccion/reports/rigor_techo.csv", index=False); print("\n== Techo / descomposición (R² relativo) ==\n", R6.round(3).to_string(index=False))

# ---------- 7. Incertidumbre del nivel nacional (domina el error absoluto) ----------
natd = {y: float(v) for y, v in nat.items()}
rows = []
for T in (2021, 2024):
    same = natd[T - 6]; adj = natd[T - 3]; trend = natd[T - 6] + (natd[T - 6] - natd[T - 12]) if (T - 12) in natd else np.nan
    for k, v in (("persistencia mismo tipo (T−6)", same), ("elección adyacente (T−3)", adj), ("tendencia lineal del mismo tipo", trend)):
        rows.append(dict(test=T, metodo_nivel=k, nat_pred=v, nat_real=natd[T], error_pp=(v - natd[T]) * 100))
R7 = pd.DataFrame(rows); R7.to_csv("reto2_prediccion/reports/rigor_nivel_nacional.csv", index=False); print("\n== Nivel nacional (media de secciones), error en pp ==\n", R7.round(4).to_string(index=False))
