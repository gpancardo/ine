# /// script
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Reto 1 (E4): descriptores del ECEG 2020 desagregados por sexo, por perfil (media ponderada por lista nominal).
Descriptores, no criterios de agrupación. Salida: reto1_perfiles/reports/descriptores_sexo.csv. Run: uv run reto1_perfiles/analysis/descriptores_sexo.py"""
import os
from pathlib import Path
import numpy as np, pandas as pd
os.chdir(Path(__file__).resolve().parents[2])
e = pd.read_parquet("data/processed/eceg.parquet")
e["sid"] = e.ENTIDAD.astype(int) * 10000 + e.SECCION.astype(int)
num = lambda c: pd.to_numeric(e[c], errors="coerce")
out = pd.DataFrame({"sid": e.sid})
for s in ("F", "M"):
    out[f"analf_{s}"] = num(f"P15YM_AN_{s}") / num(f"P_15YMAS_{s}").replace(0, np.nan)          # % analfabetas, 15+
    out[f"grad_prom_{s}"] = num(f"GRAPROES_{s}")                                                  # años promedio de escolaridad
    out[f"pea_{s}"] = num(f"PEA_{s}") / num(f"P_12YMAS_{s}").replace(0, np.nan)                  # % económicamente activas, 12+
    out[f"inac_{s}"] = num(f"PE_INAC_{s}") / num(f"P_12YMAS_{s}").replace(0, np.nan)             # % inactivas, 12+
    out[f"desocup_{s}"] = num(f"PDESOCUP_{s}") / num(f"PEA_{s}").replace(0, np.nan)              # tasa de desocupación
    out[f"pob18_{s}"] = num(f"P_18YMAS_{s}")
out = out.drop_duplicates("sid").set_index("sid")
F = pd.read_csv("reto1_perfiles/reports/tipologia_secciones.csv", usecols=["sid", "c", "ln24"]).set_index("sid")
D = F.join(out, how="inner")
desc = [c for c in out.columns if c != "pob18_F" and c != "pob18_M"]
rows = []
for c, g in D.groupby("c"):
    r = {"perfil": int(c), "secciones": len(g)}
    for col in desc:
        d = g[[col, "ln24"]].dropna(); r[col] = np.average(d[col], weights=d.ln24) if len(d) else np.nan
    rows.append(r)
T = pd.DataFrame(rows).set_index("perfil")
T.to_csv("reto1_perfiles/reports/descriptores_sexo.csv")
pd.set_option("display.width", 240); print(T.round(3).T.to_string())
