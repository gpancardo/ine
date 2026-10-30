# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "scikit-learn", "lightgbm", "catboost"]
# ///
"""Ecosistema de medios del hogar (Censo/ECEG): radio, TV, TV de paga, celular, teléfono fijo, internet, sin radio ni TV; niveles 2020, 2010 y cambio 2010->2020.
Run: uv run analysis/extra_test8.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); os.chdir(Path(__file__).resolve().parents[2])
import features as F, harness as H, stats_util as U, common as c
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
D, nat = H.init()
def media(fname, den):
    e = pd.read_parquet(f"data/processed/{fname}.parquet"); e.columns = [x.strip() for x in e.columns]; e = e.rename(columns={"entidad": "ENTIDAD", "seccion": "SECCION"})
    num = e[[x for x in e.columns if x.startswith("VPH_") or x in ("ENTIDAD", "SECCION", den, "TVIVPARHAB", "TVIVPARH")]].apply(pd.to_numeric, errors="coerce"); d = num[den].replace(0, np.nan)
    f = pd.DataFrame({"sid": num.ENTIDAD * 10000 + num.SECCION}); 
    for k in ("RADIO", "TV", "CEL", "TELEF", "INTER", "PC", "STVP", "SINRTV"):
        if f"VPH_{k}" in num: f[k.lower()] = num[f"VPH_{k}"] / d
    return f.drop_duplicates("sid").set_index("sid")
m20, m10 = media("eceg", "TVIVPARHAB"), media("eceg2010", "TVIVPARH")
G = {"m20": m20.add_prefix("m20_"), "m10": m10.add_prefix("m10_")}; com = [k for k in m20 if k in m10]; G["dm"] = (m20.loc[:, com] - m10.reindex(m20.index)[com]).add_prefix("dm_")
for gname, t in G.items():
    for col in t.columns: D[col] = t[col].replace([np.inf, -np.inf], np.nan).reindex(D.index).values
cols = {k: list(t.columns) for k, t in G.items()}
REF = F.cols(["sem"]) + F.cols(["age"]); sets = {"REF S2": REF, "+ medios 2020 (nivel)": REF + cols["m20"], "+ medios 2010 (nivel)": REF + cols["m10"], "+ cambio de medios 2010→2020": REF + cols["dm"], "+ todo medios": REF + sum(cols.values(), [])}
E = {}; out = []
for n, cs in sets.items():
    for T in (2021, 2024):
        tr = D[D["T"].isin(H.FOLDS[T]) & D.y_rel.notna()]; te = D[(D["T"] == T) & D.y_rel.notna()]; mu = tr[cs].mean().fillna(0)
        for mn, mk in (("Ridge", lambda: H.lin(Ridge(10.0))), ("LGBM", H.lgbm)):
            p = mk().fit(tr[cs].fillna(mu).values, tr.y_rel.values).predict(te[cs].fillna(mu).values); e = (te.y_rel.values - p) ** 2
            E[(n, mn, T)] = pd.Series(e, index=te.index); out.append(dict(set=n, modelo=mn, test=T, rmse=np.sqrt(e.mean()), r2=H.score(te.y_rel.values, p)["r2"]))
R = pd.DataFrame(out)
for i, r in R.iterrows():
    if r.set == "REF S2": continue
    te = D[(D["T"] == r.test) & D.y_rel.notna()]; d, lo, hi, _ = U.boot_delta(E[(r.set, r.modelo, r.test)], E[("REF S2", r.modelo, r.test)], te.mun, B=500); R.loc[i, ["d", "lo", "hi"]] = [d, lo, hi]
pd.set_option("display.width", 200); print(R.round(4).to_string(index=False)); R.to_csv("reto2_prediccion/reports/extra_medios_test.csv", index=False)
print("\nTecho estático (LGBM, mismo año, CV por municipio), R²:")
for T in (2021, 2024):
    d = D[(D["T"] == T) & D.y_rel.notna()].reset_index(drop=True); y = d.y_rel.values
    for n in ("REF S2", "+ medios 2020 (nivel)", "+ cambio de medios 2010→2020", "+ todo medios"):
        cs = sets[n]; P_ = np.zeros(len(d))
        for a, b in GroupKFold(5).split(d, groups=d.mun): P_[b] = H.lgbm().fit(d.iloc[a][cs].values, y[a]).predict(d.iloc[b][cs].values)
        print(f"  {T} {n:30s} R²={1 - ((y - P_) ** 2).sum() / ((y - y.mean()) ** 2).sum():.3f}")
# correlación simple del choque municipal 2021/2024 con medios (sección, dentro de estado)
