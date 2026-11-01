# /// script
# dependencies = ["pandas", "pyarrow", "openpyxl", "geopandas"]
# ///
"""Agrega conteos (sección x sexo x edad) -> panel sección-año; une ECEG 2020 y geometría.
Run: uv run shared/build_panel.py   ->  data/processed/{panel.parquet, eceg.parquet, secciones.gpkg}"""
import io, zipfile
from pathlib import Path
import pandas as pd

RAW, OUT = Path("data/raw"), Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)
COLS = ["AELEC", "EDOCVE", "MPIOCVE", "MPIONOM", "SECCION", "TIPOSEC", "DEF", "SEXO", "EDAD", "LN", "SV", "NV", "NS"]
NUM = ["AELEC", "EDOCVE", "MPIOCVE", "SECCION", "DEF", "SEXO", "EDAD", "LN", "SV", "NV", "NS"]
AGE = {"j": (18, 24), "a": (25, 59), "m": (60, 200)}  # joven / adulto / mayor


def agg(df):
    df["f"] = df.SEXO == 1
    g = df.groupby(["AELEC", "EDOCVE", "SECCION"])
    r = g[["LN", "SV", "NV", "NS"]].sum()
    meta = g[["MPIOCVE", "MPIONOM", "TIPOSEC", "DEF"]].first()
    for k, (lo, hi) in AGE.items():
        m = df.EDAD.between(lo, hi)
        s = df[m].groupby(["AELEC", "EDOCVE", "SECCION"])[["LN", "SV"]].sum().add_suffix(f"_{k}")
        r = r.join(s)
    f = df[df.f].groupby(["AELEC", "EDOCVE", "SECCION"])[["LN", "SV"]].sum().add_suffix("_f")
    return meta.join(r).join(f)


def panel():
    parts = []
    for z in sorted((RAW / "conteos").glob("*.zip")):
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                if not n.endswith(".csv"):
                    continue
                with zf.open(n) as fh:
                    try:
                        df = pd.read_csv(fh, encoding="utf-8-sig", usecols=COLS, low_memory=False)
                    except UnicodeDecodeError:
                        df = pd.read_csv(zf.open(n), encoding="latin-1", usecols=COLS, low_memory=False)
                for c in NUM:  # ponytail: celdas con espacios -> NaN; se reportan en el EDA como NS/faltantes
                    df[c] = pd.to_numeric(df[c], errors="coerce")
                df = df[df.EDAD.notna() & df.SECCION.notna()]
                parts.append(agg(df))
        print("ok", z.name, flush=True)
    p = pd.concat(parts).reset_index().fillna({c: 0 for c in ["LN_j", "SV_j", "LN_a", "SV_a", "LN_m", "SV_m", "LN_f", "SV_f"]})
    p.to_parquet(OUT / "panel.parquet")
    return p


def eceg():
    dfs = []
    for f in sorted((RAW / "eceg").glob("ECEG *.xlsx")):
        dfs.append(pd.read_excel(f, sheet_name=0))
        print("ok", f.name, flush=True)
    e = pd.concat(dfs, ignore_index=True)
    e.columns = [c.strip() for c in e.columns]
    e.to_parquet(OUT / "eceg.parquet")
    return e


def geo():
    import geopandas as gpd
    gs = []
    for z in sorted((RAW / "shp").glob("*.zip")):
        shp = next(n for n in zipfile.ZipFile(z).namelist() if n.upper().endswith("SECCION.SHP"))
        gs.append(gpd.read_file(f"zip://{z}!{shp}").to_crs(6372))
    g = pd.concat(gs, ignore_index=True)
    g.to_file(OUT / "secciones.gpkg", driver="GPKG")
    return g


if __name__ == "__main__":
    p = pd.read_parquet(OUT / "panel.parquet") if (OUT / "panel.parquet").exists() else panel()  # borrar para recalcular
    e = pd.read_parquet(OUT / "eceg.parquet") if (OUT / "eceg.parquet").exists() else eceg()
    g = geo()
    print(p.shape, e.shape, g.shape); print(g.columns.tolist()); print(p.groupby("AELEC").size())
