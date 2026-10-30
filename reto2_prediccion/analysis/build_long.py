# /// script
# dependencies = ["pandas", "pyarrow"]
# ///
"""Panel largo 1991-2024 de participación por sección desde resultados por casilla de diputados federales
(Magar, E. (2018) Recent Mexican election vote returns repository, github.com/emagar/elecRetrns, MIT; compilado de resultados oficiales INE/IFE).
Abstención_m = 1 - votos_totales / lista_nominal (acta de cómputo; excluye casillas especiales).  Run: uv run analysis/build_long.py"""
import os, re
from pathlib import Path
import numpy as np, pandas as pd
os.chdir(Path(__file__).resolve().parents[2])
YEARS = [1991, 1994, 1997, 2000, 2003, 2006, 2009, 2012, 2015, 2018, 2021, 2024]
PARTY = ["pan", "pri", "prd", "pvem", "pt", "mc", "morena", "pes", "pna", "conve", "pps", "parm", "pfcrn"]
rows = []
for y in YEARS:
    f = Path("data/raw/magar") / (f"dip{y}-pre-trife.csv" if y == 2024 else f"dip{y}.csv")
    d = pd.read_csv(f, low_memory=False)
    d.columns = [c.strip() for c in d.columns]
    tot = "tot" if "tot" in d else "total"
    d["tot"] = pd.to_numeric(d[tot], errors="coerce"); d["lisnom"] = pd.to_numeric(d["lisnom"], errors="coerce")
    d["seccion"] = pd.to_numeric(d["seccion"], errors="coerce"); d["edon"] = pd.to_numeric(d["edon"], errors="coerce")
    n0 = len(d); cas = d["casilla"].astype(str).str.upper()
    d = d[(d.seccion > 0) & d.edon.between(1, 32) & (d.lisnom > 0) & ~cas.str.startswith("S") & d.tot.notna()]
    d["sid"] = (d.edon * 10000 + d.seccion).astype(int)
    META = {"edon", "seccion", "casilla", "disn", "inegi", "ife", "mun", "nr", "nul", "nulos", "tot", "total", "lisnom", "status", "nota", "nota.emm", "latitude", "longitude", "observaciones", "tepjf", "sid"}
    vote = [c for c in d.columns if c not in META and pd.api.types.is_numeric_dtype(d[c])]  # votos por partido y coalición
    agg = {"tot": ("tot", "sum"), "lisnom": ("lisnom", "sum"), "nul": ("nul" if "nul" in d else ("nulos" if "nulos" in d else "tot"), "sum")}
    for c_ in vote: agg["v_" + c_] = (c_, "sum")
    g = d.groupby("sid").agg(**agg); g["year"] = y; g["abst_m"] = 1 - g.tot / g.lisnom
    rows.append(g.reset_index()); print(y, "casillas", n0, "->", len(d), "| secciones", len(g), "| particip. nacional", round(g.tot.sum() / g.lisnom.sum(), 4), "| p>1:", int((g.abst_m < 0).sum()), flush=True)
L = pd.concat(rows, ignore_index=True); L.to_parquet("data/processed/long_magar.parquet"); print(L.shape)
