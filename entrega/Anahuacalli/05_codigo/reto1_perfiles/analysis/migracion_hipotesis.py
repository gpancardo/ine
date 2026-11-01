# /// script
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Reto 1: ¿la brecha masculina del perfil 'Rural con brecha masculina' es compatible con hombres en la lista nominal que ya no residen ahí?
Compara, por sexo, la lista nominal 2024 de 18 años o más con la población residente de 18+ del Censo 2020 (ECEG). Si la razón LN/censo es mayor para hombres que para mujeres, hay hombres en la lista que el censo no cuenta
(emigrantes, entre otras causas). Se recalcula la brecha de género ajustando la lista de los hombres a la cobertura de las mujeres. Es una verificación de compatibilidad, no una medición de migración.
Run: uv run reto1_perfiles/analysis/migracion_hipotesis.py -> reto1_perfiles/reports/migracion_hipotesis.csv"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
pd.set_option("display.width", 200)
T = pd.read_csv("reto1_perfiles/reports/tipologia_secciones.csv").set_index("sid")
s = pd.read_parquet("data/processed/perfiles_seccion.parquet"); s = s[(s.AELEC == 2024)]; ln = s.groupby(["sid", "SEXO"])[["LN", "SV", "NV"]].sum().unstack("SEXO"); ln.columns = [f"{a}_{'H' if b == 0 else 'M'}" for a, b in ln.columns]
e = pd.read_parquet("data/processed/eceg.parquet"); e.columns = [c.strip() for c in e.columns]; e["sid"] = pd.to_numeric(e.ENTIDAD, errors="coerce") * 10000 + pd.to_numeric(e.SECCION, errors="coerce"); e = e.drop_duplicates("sid").set_index("sid")
for c in ("P_18YMAS_M", "P_18YMAS_F"): e[c] = pd.to_numeric(e[c], errors="coerce")
D = T[["c", "brecha_genero_18_54", "ln24"]].join(ln).join(e[["P_18YMAS_M", "P_18YMAS_F"]]).dropna(); D = D[(D.P_18YMAS_M >= 50) & (D.P_18YMAS_F >= 50)]
D["razon_H"] = D.LN_H / D.P_18YMAS_M; D["razon_M"] = D.LN_M / D.P_18YMAS_F; D["exceso_H"] = D.razon_H / D.razon_M            # >1: más hombres en la lista por cada hombre residente que mujeres por mujer residente
D["part_H"] = D.SV_H / (D.SV_H + D.NV_H); D["part_M"] = D.SV_M / (D.SV_M + D.NV_M); D["brecha_18mas"] = D.part_M - D.part_H
D["LN_H_aj"] = D.LN_H / D.exceso_H.clip(lower=1); D["part_H_aj"] = (D.SV_H / (D.SV_H + D.NV_H) * D.LN_H / D.LN_H_aj).clip(upper=1)   # NV se reduce proporcionalmente: hombres ausentes eliminados de NV
D["NV_H_aj"] = (D.NV_H - (D.LN_H - D.LN_H_aj)).clip(lower=0); D["part_H_aj"] = D.SV_H / (D.SV_H + D.NV_H_aj); D["brecha_aj"] = D.part_M - D.part_H_aj
g = D.groupby("c"); R = pd.DataFrame({"razón LN/censo hombres": g.apply(lambda d: d.LN_H.sum() / d.P_18YMAS_M.sum()), "razón LN/censo mujeres": g.apply(lambda d: d.LN_M.sum() / d.P_18YMAS_F.sum())}); R["exceso H/M"] = R.iloc[:, 0] / R.iloc[:, 1]
R["brecha 18+ (M−H, pp)"] = g.apply(lambda d: 100 * (d.SV_M.sum() / (d.SV_M.sum() + d.NV_M.sum()) - d.SV_H.sum() / (d.SV_H.sum() + d.NV_H.sum()))); R["brecha ajustada (pp)"] = g.apply(lambda d: 100 * (d.SV_M.sum() / (d.SV_M.sum() + d.NV_M.sum()) - d.SV_H.sum() / (d.SV_H.sum() + d.NV_H_aj.sum())))
R["% de la brecha explicada"] = 100 * (1 - R["brecha ajustada (pp)"] / R["brecha 18+ (M−H, pp)"]); R.index = [L.NOMBRES[i] for i in R.index]; print(R.round(2).to_string()); R.to_csv("reto1_perfiles/reports/migracion_hipotesis.csv")
print("\ncorrelación entre secciones del perfil rural: exceso H/M vs brecha de género 18-54:", round(D[D.c == 2].exceso_H.corr(D[D.c == 2].brecha_genero_18_54), 3), "| todas las secciones:", round(D.exceso_H.corr(D.brecha_genero_18_54), 3))
