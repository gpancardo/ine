# /// script
# dependencies = ["pandas", "pyarrow"]
# ///
"""Tabla municipal (clave INEGI): pobreza/ingreso CONEVAL 2010/2015/2020 y violencia SESNSP 2015-2025. -> data/processed/mun_extra.parquet
Run: uv run analysis/extra_mun.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
os.chdir(Path(__file__).resolve().parents[2])

POV = ["pobreza", "pobreza_e", "vul_ing", "plp", "plp_e", "ic_rezedu", "ic_asalud", "ic_segsoc", "ic_cv", "ic_sbv", "ic_ali", "carencias3"]
frames = []
for y in (2010, 2015, 2020):
    d = pd.read_csv(f"data/raw/coneval/pobreza_mun_{y}.csv", encoding="latin-1", thousands=",")
    d = d.rename(columns={"plb": "plp", "plbm": "plp_e"})  # CONEVAL renombró línea de bienestar -> línea de pobreza por ingresos (2018)
    d = d.set_index("clave_municipio")[["poblacion"] + POV].apply(lambda c: pd.to_numeric(c.astype(str).str.replace(",", "", regex=False), errors="coerce"))
    frames.append(d.add_suffix(f"_{y}"))
mx = pd.concat(frames, axis=1)

# SESNSP: conteos anuales por categoría
cols = ["Año", "Cve. Municipio", "Tipo de delito", "Subtipo de delito"] + ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
s = pd.read_csv("data/raw/sesnsp/extracted/Municipal-Delitos-2015-2025_ago2026.csv", encoding="latin-1", usecols=cols)
s["n"] = s[cols[4:]].sum(axis=1)
cat = np.select([s["Subtipo de delito"].eq("Homicidio doloso"), s["Tipo de delito"].eq("Feminicidio"), s["Tipo de delito"].eq("Extorsión"),
                 s["Tipo de delito"].eq("Secuestro"), s["Tipo de delito"].str.startswith("Robo", na=False), s["Subtipo de delito"].eq("Lesiones dolosas"),
                 s["Tipo de delito"].eq("Narcomenudeo")], ["hom", "fem", "ext", "sec", "robo", "les", "narco"], "otro")
s["cat"] = cat
cnt = s[s.cat != "otro"].groupby(["Cve. Municipio", "Año", "cat"]).n.sum().unstack("cat").fillna(0)
tot = s.groupby(["Cve. Municipio", "Año"]).n.sum().rename("total")
cr = cnt.join(tot)
cr.index.names = ["mun_inegi", "year"]
cr = cr.reset_index()
# población para tasas: instantánea CONEVAL más cercana en el tiempo
pop = mx[[f"poblacion_{y}" for y in (2010, 2015, 2020)]]
cr["pob"] = [pop.at[m, "poblacion_2015" if y < 2018 else "poblacion_2020"] if m in pop.index else np.nan for m, y in zip(cr.mun_inegi, cr.year)]
for k in ["hom", "fem", "ext", "sec", "robo", "les", "narco", "total"]:
    cr[f"{k}_r"] = cr[k] / cr.pob * 1e5
wide = cr.pivot(index="mun_inegi", columns="year", values=[f"{k}_r" for k in ["hom", "ext", "robo", "les", "narco", "total"]])
wide.columns = [f"{a}_{b}" for a, b in wide.columns]
out = mx.join(wide, how="outer"); out.index.name = "mun_inegi"
out.to_parquet("data/processed/mun_extra.parquet")
print(out.shape); print(out[["pobreza_2020", "plp_2020", "plp_e_2020", "hom_r_2018", "hom_r_2021", "hom_r_2024"]].describe().round(1).T)
print("tasa nacional de homicidio doloso por 100k (suma/pob):", {int(y): round(cr[cr.year == y].hom.sum() / cr[cr.year == y].pob.sum() * 1e5, 1) for y in (2015, 2018, 2021, 2024)})
