# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "pyogrio"]
# ///
"""Reto 1 (E8): tablero con mapa, autocontenido (un solo HTML; Leaflet 1.9.4 incrustado, funciona sin conexión salvo el mapa base) para Juntas Locales y Distritales:
perfil, confianza y votos recuperables por sección, con agregación por estado, distrito federal y municipio, mapa sincronizado y descarga en CSV de la selección.
Geometría: cartografía electoral del INE (data/processed/secciones.gpkg); distritos según la CCPC 2024 (el campo DISTRITO del shapefile viene casi vacío).
Insumos: politica_publica.py y rigor_perfiles.py. Run: uv run reto1_perfiles/analysis/tablero.py -> reto1_perfiles/reports/tablero.html"""
import json, os, sys
from pathlib import Path
import geopandas as gpd, pandas as pd
from shapely.geometry import mapping
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); sys.path.insert(0, "shared/lib"); import tip_lib as L
from common import ESTADOS
R = "reto1_perfiles/reports/"; HERE = Path(__file__).parent
S = pd.read_csv(R + "politica_secciones.csv").set_index("sid").join(pd.read_csv(R + "rigor_asignacion.csv").set_index("sid"))
assert len(S) == 64096 and S.confianza_asignacion.notna().all()
# geometría: secciones → distritos (DEF de la CCPC 2024) y municipios; simplificación en metros (EPSG:6372) antes de pasar a lat/lon
g = gpd.read_file("data/processed/secciones.gpkg"); g["sid"] = g.ENTIDAD * 10000 + g.SECCION; g = g.drop_duplicates("sid").set_index("sid")
P = pd.read_parquet("data/processed/panel.parquet", columns=["AELEC", "EDOCVE", "SECCION", "DEF"]).query("AELEC == 2024"); P["sid"] = P.EDOCVE * 10000 + P.SECCION
g["kdef"] = P.drop_duplicates("sid").set_index("sid").DEF.reindex(g.index).pipe(lambda d: g.ENTIDAD * 100 + d); g["kmun"] = g.ENTIDAD * 1000 + g.MUNICIPIO
assert S.index.isin(g.index).all() and g.kdef.notna().mean() > 0.98  # secciones sin DEF 2024: desaparecidas antes de 2024
def polys(key, tol):
    d = g.dropna(subset=[key]).dissolve(key)[["geometry"]]; d["geometry"] = d.simplify(tol); d = d.to_crs(4326)
    return {str(int(k)): mapping(geom) for k, geom in d.geometry.items()}
def rnd(o, n=3): return [rnd(x, n) for x in o] if isinstance(o, (list, tuple)) else round(o, n)
geo = {lvl: {k: dict(type=v["type"], coordinates=rnd(v["coordinates"])) for k, v in polys(key, tol).items()} for lvl, key, tol in (("def", "kdef", 600), ("mun", "kmun", 300))}
pts = g.loc[S.index].representative_point().to_crs(4326)
muns = S.drop_duplicates("mun").set_index("mun").MPIONOM.to_dict()
rows = [[int(i), int(r.EDOCVE), int(r.DEF), int(r.mun), int(r.c) + 1, r.TIPOSEC, int(r.ln24), round(100 * r.nivel_abs, 1), round(r.v_nivel), round(r.v_genero), round(r.v_joven), round(r.v_75),
         round(r.confianza_asignacion, 2), round(p.y, 4), round(p.x, 4)] for (i, r), p in zip(S.iterrows(), pts)]
data = dict(rows=rows, geo=geo, muns={str(k): v for k, v in muns.items()}, edos={str(k): v for k, v in ESTADOS.items()}, nombres={str(k + 1): v for k, v in L.NOMBRES.items()})
html = ((HERE / "tablero_plantilla.html").read_text().replace("/*LEAFLET_CSS*/", (HERE / "vendor/leaflet-1.9.4.min.css").read_text())
        .replace("/*LEAFLET_JS*/", (HERE / "vendor/leaflet-1.9.4.min.js").read_text()).replace("/*DATA*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":"))))
Path(R + "tablero.html").write_text(html); print(f"tablero.html: {len(html) / 1e6:.1f} MB, {len(rows):,} secciones, {len(geo['def'])} distritos, {len(geo['mun'])} municipios")
