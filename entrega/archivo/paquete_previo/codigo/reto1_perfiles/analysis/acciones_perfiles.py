# /// script
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Reto 1: insumos operativos para la narrativa de cada perfil (2024).
(1) A quién: celdas sexo × edad con más no votantes dentro del perfil y su tasa frente a la misma celda del perfil 5 (referencia).
(2) Dónde: distritos federales donde el perfil es mayoritario y cuántos concentran la mitad del potencial de su criterio principal.
Run: uv run reto1_perfiles/analysis/acciones_perfiles.py"""
import os, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); sys.path.insert(0, "shared/lib"); import tip_lib as L
from common import ESTADOS
R = "reto1_perfiles/reports/"
T = pd.read_csv(R + "tipologia_secciones.csv", usecols=["sid", "c"]).set_index("sid")
s = pd.read_parquet("data/processed/perfiles_seccion.parquet").query("AELEC == 2024"); s = s[s.sid.isin(T.index)].assign(c=lambda d: d.sid.map(T.c))
g = s.groupby(["c", "SEXO", "banda"])[["SV", "NV"]].sum(); g["tasa"] = g.SV / (g.SV + g.NV); g["pct_novot"] = g.NV / g.groupby("c").NV.transform("sum")
g["ref_p5"] = g.tasa.xs(4, level="c").reindex(g.index.droplevel("c")).values; g["dif_ref_pp"] = 100 * (g.tasa - g.ref_p5)
g = g.reset_index().assign(sexo=lambda d: d.SEXO.map({0: "H", 1: "M"}), perfil=lambda d: d.c + 1)
top = g.sort_values(["c", "NV"], ascending=[True, False]).groupby("c").head(4)
print("== a quién: 4 celdas con más no votantes por perfil (2024)"); print(top[["perfil", "sexo", "banda", "NV", "pct_novot", "tasa", "dif_ref_pp"]].round(3).to_string(index=False))
top.to_csv(R + "acciones_celdas.csv", index=False)
D = pd.read_csv(R + "politica_distritos.csv"); D["edo"] = D.EDOCVE.map(ESTADOS); D["perfil"] = D.grupo + 1
PRINC = {1: "v_nivel", 2: "v_joven", 3: "v_genero", 4: "v_75", 5: "v_joven"}  # criterio principal de cada perfil
rows = []
for p, k in PRINC.items():
    d = D[D.perfil == p].sort_values(k, ascending=False); cum = d[k].cumsum() / d[k].sum()
    rows.append(dict(perfil=p, criterio=k, distritos_mayoritarios=len(d), distritos_mitad=int((cum < .5).sum() + 1), miles_votos=d[k].sum() / 1e3,
                     top5=", ".join(f"{e}-{int(n)}" for e, n in zip(d.edo.head(5), d.DEF.head(5)))))
O = pd.DataFrame(rows); print("\n== dónde: distritos federales con mayoría del perfil (300 en total)"); print(O.round(0).to_string(index=False)); O.to_csv(R + "acciones_distritos.csv", index=False)
assert len(D) == 300 and O.distritos_mayoritarios.sum() == 300
