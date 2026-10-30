# /// script
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Eventos municipales con efectos fijos de sección y estado×año (panel largo 1994-2024). Identifica efectos municipales dentro de la sección.
Run: uv run analysis/panel_events.py"""
import os
from pathlib import Path
import numpy as np, pandas as pd
os.chdir(Path(__file__).resolve().parents[2])
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[L.year >= 1994]
W = L.pivot(index="sid", columns="year", values="abst_m").clip(0, 1); LN = L.pivot(index="sid", columns="year", values="lisnom")
long = W.stack().rename("y").reset_index().merge(LN.stack().rename("ln").reset_index(), on=["sid", "year"]); long = long[long.ln >= 100]
inc = pd.read_csv("data/raw/magar_mun/aymu1989-on.incumbents.csv", low_memory=False); inc["mg"] = pd.to_numeric(inc.mg, errors="coerce")
inc = inc.sort_values(["ife", "yr"]); inc["res_t"] = inc.groupby("ife")["race.after"].shift(1).fillna("")  # desenlace de ESTA elección para el titular previo
# mapeo sección -> municipio vía el panel de conteos (ife = EDOCVE*1000+MPIOCVE)
pn = pd.read_parquet("data/processed/panel.parquet", columns=["EDOCVE", "SECCION", "MPIOCVE"]).drop_duplicates(["EDOCVE", "SECCION"]); pn["sid"] = pn.EDOCVE * 10000 + pn.SECCION; pn["ife"] = pn.EDOCVE * 1000 + pn.MPIOCVE
long = long.merge(pn[["sid", "ife"]], on="sid")
ev = inc[inc.yr.isin(sorted(long.year.unique()))][["ife", "yr", "mg", "res_t", "part"]].drop_duplicates(["ife", "yr"]).rename(columns={"yr": "year"})
ev["muni"] = 1.0; ev["abierta"] = (ev.res_t.str.startswith("Term-limited") | ev.res_t.str.startswith("Out")).astype(float); ev["alt"] = ev.res_t.str.contains("lost|beaten").astype(float); ev["reel"] = ev.res_t.str.startswith("Reelected").astype(float)
ev["morena"] = ev.part.fillna("").str.contains("morena").astype(float); ev["mg0"] = ev.mg.fillna(ev.mg.median()); ev["mg0"] -= ev.mg0.mean()
long = long.merge(ev[["ife", "year", "muni", "abierta", "alt", "reel", "morena", "mg0"]], on=["ife", "year"], how="left").fillna({"muni": 0, "abierta": 0, "alt": 0, "reel": 0, "morena": 0, "mg0": 0}); long = long[long.muni == 1]  # solo municipios con elección concurrente: contraste dentro de ellos
long = long[long.groupby("sid").sid.transform("size") >= 3]; long["est"] = long.sid // 10000; long["mid"] = long.year.isin({1997, 2003, 2009, 2015, 2021}).astype(float)
X = ["abierta", "alt", "reel", "morena", "mg0"]
def twfe(d, cols):
    """Doble demeaning (sección y estado×año) por proyecciones alternadas; ponderado igual."""
    d = d.copy(); d["sy"] = d.est * 10000 + d.year; V = d[["y"] + cols].copy()
    for _ in range(8):
        V = V - V.groupby(d.sid.values).transform("mean"); V = V - V.groupby(d.sy.values).transform("mean")
    return V
def fit(d, tag):
    V = twfe(d, X); b = np.linalg.lstsq(V[X].values, V.y.values, rcond=None)[0]; e = V.y.values - V[X].values @ b
    # SE agrupados por municipio
    Xm = V[X].values; bread = np.linalg.pinv(Xm.T @ Xm); meat = np.zeros((len(X), len(X)))
    for _, ix in d.groupby("ife").indices.items(): s = Xm[ix].T @ e[ix]; meat += np.outer(s, s)
    se = np.sqrt(np.diag(bread @ meat @ bread)); out = pd.DataFrame({"coef_pp": b * 100, "t": b / se}, index=X); out["muestra"] = tag; return out
res = [fit(long, "todas"), fit(long[long.year <= 2012], "1994-2012"), fit(long[long.year >= 2015], "2015-2024"), fit(long[long.mid == 1], "intermedias"), fit(long[long.mid == 0], "presidenciales")]
R = pd.concat(res).reset_index(names="var"); pd.set_option("display.width", 200); print(R.pivot(index="var", columns="muestra", values="coef_pp").round(2).to_string()); print("\nt:"); print(R.pivot(index="var", columns="muestra", values="t").round(1).to_string())
print(f"\nn obs {len(long)}, secciones {long.sid.nunique()}"); R.to_csv("reto2_prediccion/reports/panel_events.csv", index=False)
