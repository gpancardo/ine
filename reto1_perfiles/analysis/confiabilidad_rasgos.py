# /// script
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Reto 1: ¿qué rasgos de perfil persisten entre ventanas de elecciones disjuntas (A = 2009-2015, B = 2018-2024)? Se agrupa solo con los persistentes.
Run: uv run reto1_perfiles/analysis/confiabilidad_rasgos.py -> reto1_perfiles/reports/confiabilidad_rasgos.csv"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
s = L.load(); s["mun"] = s.EDOCVE * 1000 + s.MPIOCVE; s["ged2"] = s.banda.map({"18-24": "Y", "25-34": "Y", "35-44": "A", "45-54": "A", "55-64": "M", "65-74": "M", "75+": "E"})
def rate(years, sex=None, ged=None, by="sid", bands=None):
    d = s[s.AELEC.isin(years)]; d = d if sex is None else d[d.SEXO == sex]; d = d if ged is None else d[d.ged2.isin(ged)]; d = d if bands is None else d[d.banda.isin(bands)]
    g = d.groupby(by)[["SV", "NV"]].sum(); return g.SV / (g.SV + g.NV), g.SV + g.NV
def feats(Y, P, M_, by):
    f = {}; nat = {y: s[s.AELEC == y].SV.sum() / (s[s.AELEC == y][["SV", "NV"]].sum().sum()) for y in Y}
    f["nivel_rel"] = sum(rate([y], by=by)[0] - nat[y] for y in Y) / len(Y)       # relativo al nivel nacional de cada elección
    f["gen_18_54"] = rate(Y, 1, ["Y", "A"], by)[0] - rate(Y, 0, ["Y", "A"], by)[0]; f["gen_55mas"] = rate(Y, 1, ["M", "E"], by)[0] - rate(Y, 0, ["M", "E"], by)[0]
    f["brecha_joven"] = rate(Y, None, ["Y"], by)[0] - rate(Y, None, ["M"], by)[0]; f["caida_75"] = rate(Y, None, ["E"], by)[0] - rate(Y, None, ["M"], by)[0]
    f["joven_H"] = rate(Y, 0, ["Y"], by)[0] - rate(Y, 0, ["M"], by)[0]; f["joven_M"] = rate(Y, 1, ["Y"], by)[0] - rate(Y, 1, ["M"], by)[0]
    f["interm"] = rate(P, by=by)[0] - rate(M_, by=by)[0]; f["interm_jov"] = rate(P, None, ["Y"], by)[0] - rate(M_, None, ["Y"], by)[0]
    f["h25_34_rel"] = rate(Y, 0, None, by, ["25-34"])[0] - rate(Y, None, None, by, ["25-34"])[0]  # hombres 25-34 vs todos 25-34
    return pd.DataFrame(f)
out = {}
for by in ("sid", "mun"):
    A = feats([2009, 2012, 2015], [2012], [2009, 2015], by); B = feats([2018, 2021, 2024], [2018, 2024], [2021], by); c = A.index.intersection(B.index)
    out[("sección" if by == "sid" else "municipio")] = pd.Series({k: round(A.loc[c, k].corr(B.loc[c, k]), 3) for k in A.columns})
R = pd.DataFrame(out); R.index.name = "rasgo"; print("correlación entre ventanas disjuntas (A=2009-2015, B=2018-2024)"); print(R.to_string()); R.to_csv("reto1_perfiles/reports/confiabilidad_rasgos.csv")
