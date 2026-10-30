# /// script
# dependencies = ["pandas", "pyarrow"]
# ///
"""Reto 1: tablas de participación por grupo de edad × sexo a partir de los Conteos Censales (cuadernillos de la lista nominal).
  data/processed/perfiles_seccion.parquet : sección × elección × (sexo, grupo de edad) -> LN, SV, NV, NS  (formato largo compacto)
  data/processed/perfiles_edad.parquet    : elección × tipo de sección × sexo × edad (años) -> LN, SV, NV, NS  (ciclo de vida y cohortes)
Participación = SV/(SV+NV): excluye NS (cuadernillos sin captura). Run: uv run reto1_perfiles/analysis/build_perfiles.py"""
import os, zipfile
from pathlib import Path
import pandas as pd
os.chdir(Path(__file__).resolve().parents[2])
BANDS = [18, 25, 35, 45, 55, 65, 75, 200]; LAB = ["18-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"]
cols = ["AELEC", "EDOCVE", "MPIOCVE", "SECCION", "TIPOSEC", "DEF", "SEXO", "EDAD", "LN", "SV", "NV", "NS"]; sec, ed = [], []
for z in sorted(Path("data/raw/conteos").glob("*.zip")):
    with zipfile.ZipFile(z) as zf:
        for n in zf.namelist():
            if not n.endswith(".csv"): continue
            try: d = pd.read_csv(zf.open(n), encoding="utf-8-sig", usecols=cols, low_memory=False)
            except UnicodeDecodeError: d = pd.read_csv(zf.open(n), encoding="latin-1", usecols=cols, low_memory=False)
            for c in cols[:3] + cols[3:4] + cols[5:]: d[c] = pd.to_numeric(d[c], errors="coerce")
            d = d.dropna(subset=["EDAD", "SECCION", "SEXO"]); d = d[d.SEXO.isin([0, 1]) & (d.EDAD >= 18)]
            d["banda"] = pd.cut(d.EDAD, BANDS, right=False, labels=LAB)
            sec.append(d.groupby(["AELEC", "EDOCVE", "MPIOCVE", "SECCION", "SEXO", "banda"], observed=True)[["LN", "SV", "NV", "NS"]].sum().reset_index())
            ed.append(d.groupby(["AELEC", "TIPOSEC", "SEXO", "EDAD"])[["LN", "SV", "NV", "NS"]].sum().reset_index())
    print("ok", z.name, flush=True)
s = pd.concat(sec, ignore_index=True); s["sid"] = (s.EDOCVE * 10000 + s.SECCION).astype(int); s["banda"] = s.banda.astype(str)
s = s.groupby(["AELEC", "sid", "SEXO", "banda"], as_index=False).agg(EDOCVE=("EDOCVE", "first"), MPIOCVE=("MPIOCVE", "first"), LN=("LN", "sum"), SV=("SV", "sum"), NV=("NV", "sum"), NS=("NS", "sum"))
s.to_parquet("data/processed/perfiles_seccion.parquet"); print(s.shape, s.groupby("AELEC").sid.nunique().to_dict())
e = pd.concat(ed, ignore_index=True).groupby(["AELEC", "TIPOSEC", "SEXO", "EDAD"], as_index=False)[["LN", "SV", "NV", "NS"]].sum(); e.to_parquet("data/processed/perfiles_edad.parquet"); print(e.shape)
