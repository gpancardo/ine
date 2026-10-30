# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""ECEG 2010->2020 (cambio sociodemográfico) y DENUE (economía local) en el backtest. Run: uv run analysis/extra_test2.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import features as F, harness as H, stats_util as U, common as c
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

D, nat = H.init()
f20, f10 = c.eceg_features(), c.eceg_features("eceg2010.parquet")
common = f20.index.intersection(f10.index); print(f"secciones con ECEG 2010 y 2020: {len(common)} de {len(f20)} (2020) / {len(f10)} (2010)")
keep = [x for x in f20.columns if x in f10.columns and x != "pobtot"]
dl = (f20.loc[common, keep] - f10.loc[common, keep]).add_prefix("d_"); dl["d_log_pob"] = np.log(f20.loc[common, "pobtot"] / f10.loc[common, "pobtot"].replace(0, np.nan))
f10c = f10[keep].add_prefix("v10_")
dn = pd.read_parquet("data/processed/denue_sections.parquet").reindex(f20.index).fillna(0); pt = f20.pobtot.replace(0, np.nan)
den = pd.DataFrame({"den_est_pc": np.log1p(dn.n_est / pt * 1000), "den_emp_pc": np.log1p(dn.emp_est / pt * 1000), "den_grande": dn.n_grande / dn.n_est.replace(0, np.nan),
                    "den_comercio": dn.n_comercio / dn.n_est.replace(0, np.nan), "den_manuf": dn.n_manuf / dn.n_est.replace(0, np.nan), "den_fin": dn.n_fin / dn.n_est.replace(0, np.nan),
                    "den_educ": dn.n_educ / dn.n_est.replace(0, np.nan), "den_salud": dn.n_salud / dn.n_est.replace(0, np.nan), "den_gob": dn.n_gob / dn.n_est.replace(0, np.nan)})
G = {"eceg_d": list(dl.columns), "eceg10": list(f10c.columns), "denue": list(den.columns)}
for g, tbl in (("eceg_d", dl), ("eceg10", f10c), ("denue", den)):
    for col in tbl.columns: D[col] = tbl[col].replace([np.inf, -np.inf], np.nan).reindex(D.index).values
REF = F.cols(["sem"]) + F.cols(["age"])
sets = {"REF S2": REF, "+ ECEG 2010→2020 cambio": REF + G["eceg_d"], "+ ECEG 2010 nivel": REF + G["eceg10"], "+ DENUE (economía local)": REF + G["denue"], "+ todo INEGI nuevo": REF + sum(G.values(), [])}
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
pd.set_option("display.width", 220); print(R.round(4).to_string(index=False)); R.to_csv("reto2_prediccion/reports/extra_inegi_test.csv", index=False)
print("\nTecho estático (LGBM, mismo año, CV por municipio), R²:")
for T in (2021, 2024):
    d = D[(D["T"] == T) & D.y_rel.notna()].reset_index(drop=True); y = d.y_rel.values
    for n in ("REF S2", "+ DENUE (economía local)", "+ ECEG 2010→2020 cambio", "+ todo INEGI nuevo"):
        cs = sets[n]; P_ = np.zeros(len(d))
        for a, b in GroupKFold(5).split(d, groups=d.mun): P_[b] = H.lgbm().fit(d.iloc[a][cs].values, y[a]).predict(d.iloc[b][cs].values)
        print(f"  {T} {n:30s} R²={1 - ((y - P_) ** 2).sum() / ((y - y.mean()) ** 2).sum():.3f}")
