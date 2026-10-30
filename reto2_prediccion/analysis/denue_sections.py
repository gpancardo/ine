# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "shapely"]
# ///
"""DENUE (INEGI) -> conteos agregados por sección electoral mediante unión espacial de puntos. Solo se leen actividad (SCIAN),
tamaño y coordenadas; se descartan nombres, domicilios y contactos. Run: uv run analysis/denue_sections.py -> data/processed/denue_sections.parquet"""
import os, zipfile
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
os.chdir(Path(__file__).resolve().parents[2])
MID = {"0 a 5 personas": 3, "6 a 10 personas": 8, "11 a 30 personas": 20, "31 a 50 personas": 40, "51 a 100 personas": 75, "101 a 250 personas": 175, "251 y más personas": 400}
geo = gpd.read_file("data/processed/secciones.gpkg"); geo["sid"] = geo.ENTIDAD * 10000 + geo.SECCION
parts = []
for z in sorted(Path("data/raw/denue").glob("denue_*.zip")):
    ent = int(z.stem.split("_")[1])
    with zipfile.ZipFile(z) as zf:
        csv = next(n for n in zf.namelist() if n.endswith(".csv") and "conjunto_de_datos" in n)
        d = pd.read_csv(zf.open(csv), encoding="latin-1", usecols=["codigo_act", "per_ocu", "latitud", "longitud"], dtype=str)
    d = d.dropna(subset=["latitud", "longitud"]); d["lat"], d["lon"] = pd.to_numeric(d.latitud, errors="coerce"), pd.to_numeric(d.longitud, errors="coerce"); d = d.dropna(subset=["lat", "lon"])
    pts = gpd.GeoDataFrame(d[["codigo_act", "per_ocu"]], geometry=gpd.points_from_xy(d.lon, d.lat), crs="EPSG:4326").to_crs(geo.crs)
    j = gpd.sjoin(pts, geo[geo.ENTIDAD == ent][["sid", "geometry"]], how="inner", predicate="within")
    j["sc2"] = j.codigo_act.str[:2]; j["emp"] = j.per_ocu.map(MID).fillna(3)
    g = j.groupby("sid")
    agg = pd.DataFrame({"n_est": g.size(), "emp_est": g.emp.sum(), "n_grande": g.apply(lambda x: (x.emp >= 20).sum()),
                        "n_comercio": g.apply(lambda x: x.sc2.isin(["43", "46"]).sum()), "n_manuf": g.apply(lambda x: x.sc2.isin(["31", "32", "33"]).sum()),
                        "n_fin": g.apply(lambda x: (x.sc2 == "52").sum()), "n_educ": g.apply(lambda x: (x.sc2 == "61").sum()), "n_salud": g.apply(lambda x: (x.sc2 == "62").sum()),
                        "n_gob": g.apply(lambda x: (x.sc2 == "93").sum())})
    parts.append(agg); print("ok", z.name, len(d), "puntos ->", int(j.shape[0]), "en sección", flush=True)
out = pd.concat(parts); out = out.groupby(level=0).sum(); out.to_parquet("data/processed/denue_sections.parquet"); print(out.shape, out.n_est.sum())
