# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""¿Qué tan fina tendría que ser la información del año objetivo (choque medio por estado/distrito/municipio) para llegar a 0.82?
R² de (predicción honesta Ridge + media LOO del residuo por grupo). Run: uv run analysis/info_needed.py"""
import os, sys, pickle
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import harness as H
D, nat = H.init(); P = pickle.load(open("data/processed/benchmark_preds.pkl", "rb"))
r2 = lambda y, p: 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()
rows = []
for T in (2021, 2024):
    f = "dip2024-pre-trife.csv" if T == 2024 else f"dip{T}.csv"
    m = pd.read_csv(f"data/raw/magar/{f}", usecols=["edon", "seccion", "disn"], low_memory=False)
    m["sid"] = pd.to_numeric(m.edon, errors="coerce") * 10000 + pd.to_numeric(m.seccion, errors="coerce"); m = m.dropna().astype({"sid": int})
    dis = m.groupby("sid").disn.agg(lambda s: s.mode().iat[0])
    te = D[(D["T"] == T) & D.y_rel.notna()].copy(); te["p"] = P[("Ridge", T)].reindex(te.index); te = te.dropna(subset=["p"])
    te["dist"] = (te.index.map(dis).astype(float) + (te.mun // 1000) * 1000).values; te["est"] = te.mun // 1000
    te["res"] = te.y_rel - te.p; rng = np.random.default_rng(0)
    out = {"T": T, "honesto": r2(te.y_rel, te.p)}
    for nm, g in (("estado", te.est), ("distrito", te.dist), ("municipio", te.mun), ("azar 300 grupos", pd.Series(rng.integers(0, 300, len(te)), te.index))):
        gg = te.groupby(g.values).res; n = gg.transform("count"); loo = ((gg.transform("sum") - te.res) / (n - 1).replace(0, np.nan)).fillna(0)
        k = n / (n + 5)  # encogimiento ligero hacia 0 en grupos chicos
        out[f"+choque {nm} (n={g.nunique()})"] = r2(te.y_rel, te.p + loo * (n - 1) / (n - 1 + 5)) if False else r2(te.y_rel, te.p + loo)
    rows.append(out)
R = pd.DataFrame(rows).set_index("T"); pd.set_option("display.width", 220); print(R.round(3).T.to_string()); R.to_csv("reto2_prediccion/reports/info_needed.csv")
