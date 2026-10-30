# /// script
# dependencies = ["requests", "pandas", "geopandas", "scikit-learn", "lightgbm", "catboost", "shapely", "numpy"]
# ///
"""Reto 2 INE 2026: abstención 2027, benchmark, escenarios, GeoJSON.   Run: uv run pipeline_reto2.py

Datos: ./data/raw/ debe tener (estandarizado):
  secciones.csv   seccion_id,municipio,urbano,abst_2009,abst_2012,abst_2015,abst_2018,abst_2021,abst_2024,
                  escolaridad,pct_joven,pea,marginacion,brecha_joven,dist_casilla
  secciones.geojson  polígonos con propiedad seccion_id
  agebs.csv       seccion_id,ageb,poblacion,marginacion
Descarga: si existe ./data/sources.json ({"archivo.ext": "url"}), se baja a data/raw (zip se descomprime).
Sin datos -> genera datos SINTÉTICOS (demo) y lo avisa. No hay URLs oficiales hardcodeadas: pégalas en sources.json.
"""
import json, zipfile, warnings
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, requests
from shapely.geometry import box
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import Lasso, Ridge
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor

warnings.filterwarnings("ignore")
RAW, OUT = Path("data/raw"), Path("public")
YEARS = [2009, 2012, 2015, 2018, 2021, 2024]
SHOCK = {"brecha_joven": 0.90, "dist_casilla": 0.90}  # -10% en variables modificables


# ---------- PASO 0: descarga / fallback ----------
def download():
    RAW.mkdir(parents=True, exist_ok=True)
    src = Path("data/sources.json")
    if not src.exists():
        return
    for name, url in json.loads(src.read_text()).items():
        dest = RAW / name
        if dest.exists():
            continue
        try:
            r = requests.get(url, timeout=120, allow_redirects=True)
            r.raise_for_status()
            dest.write_bytes(r.content)
            if zipfile.is_zipfile(dest):
                zipfile.ZipFile(dest).extractall(RAW)
        except Exception as e:  # fallback: el usuario puede dejar el archivo a mano en data/raw
            print(f"[WARN] {name}: {e} -> coloca el archivo manualmente en {RAW}/")


def synthetic(n=20, seed=0):
    rng = np.random.default_rng(seed)
    N = n * n
    gx, gy = np.meshgrid(range(n), range(n))
    gx, gy = gx.ravel(), gy.ravel()
    urbano = ((gx - n / 2) ** 2 + (gy - n / 2) ** 2 < (n / 3) ** 2).astype(int)
    d = pd.DataFrame({
        "seccion_id": 1000 + np.arange(N),
        "municipio": [f"Municipio {1 + (x // 7) + 3 * (y // 7)}" for x, y in zip(gx, gy)],
        "urbano": urbano,
        "escolaridad": rng.normal(8, 1.5, N).clip(3, 14) + 1.5 * urbano,
        "pct_joven": rng.normal(.14, .03, N).clip(.05, .3),
        "pea": rng.normal(.55, .07, N).clip(.3, .8),
        "marginacion": rng.uniform(0, 1, N) * (1.2 - .6 * urbano),
        "brecha_joven": rng.uniform(.05, .35, N),
        "dist_casilla": rng.uniform(.2, 3, N),
    })
    z = rng.normal(0, 1, N)
    # nivel latente suave espacial + efectos observables
    lat = pd.Series(.25 * np.sin(gx / 3) + .25 * np.cos(gy / 4)).values
    base = (.38 + lat * .3 + .1 * d.marginacion - .015 * (d.escolaridad - 8) + .25 * d.brecha_joven
            + .02 * d.dist_casilla + .02 * z)
    for i, y in enumerate(YEARS):
        d[f"abst_{y}"] = (base + .03 * np.sin(i) + rng.normal(0, .02, N)).clip(.1, .85) * 100
    d["abst_2024"] += 3
    geom = [box(x, y, x + 1, y + 1) for x, y in zip(gx, gy)]
    g = gpd.GeoDataFrame(d[["seccion_id"]], geometry=geom, crs="EPSG:4326")
    ag = []
    for sid, m in zip(d.seccion_id, d.marginacion):
        for k in range(rng.integers(1, 4)):
            ag.append({"seccion_id": sid, "ageb": f"{sid:04d}-{k + 1:03d}-{rng.integers(0, 9)}",
                       "poblacion": int(rng.integers(300, 4000)),
                       "marginacion": str(pd.cut([m], [-1, .25, .5, .75, 9], labels=["Muy bajo", "Bajo", "Alto", "Muy alto"])[0])})
    return d, g, pd.DataFrame(ag)


def load():
    download()
    need = [RAW / f for f in ("secciones.csv", "secciones.geojson", "agebs.csv")]
    if all(p.exists() for p in need):
        return pd.read_csv(need[0]), gpd.read_file(need[1]), pd.read_csv(need[2])
    print("[WARN] Faltan datos reales en data/raw -> usando datos SINTÉTICOS de demostración")
    return synthetic()


# ---------- PASO 1: features ----------
def lag(df, geo, col, k=8):  # KNN k=8 sobre centroides ~ Queen; ponytail: libpysal Queen real si hay topología irregular
    c = geo.set_index("seccion_id").loc[df.seccion_id].geometry.centroid
    xy = np.c_[c.x, c.y]
    idx = NearestNeighbors(n_neighbors=k + 1).fit(xy).kneighbors(xy)[1][:, 1:]
    return df[col].values[idx].mean(1)


def feats(df, geo, y1, y2, y3):
    """y1,y2,y3 = años t-1,t-2,t-3 (train: 2021,2018,2015 -> 2024; inferencia: 2024,2021,2018 -> 2027)."""
    X = df[["urbano", "escolaridad", "pct_joven", "pea", "marginacion", "brecha_joven", "dist_casilla"]].copy()
    X["y_prev"], X["y_prev2"], X["y_prev3"] = df[f"abst_{y1}"], df[f"abst_{y2}"], df[f"abst_{y3}"]
    X["delta"] = X.y_prev - X.y_prev2
    X["lag_y_prev"] = lag(df, geo, f"abst_{y1}")
    return X


def semaforo(v):
    return pd.cut(v, [-1, 35, 45, 55, 101], labels=["Bajo", "Medio", "Alto", "Crítico"]).astype(str)


def main():
    df, geo, agebs = load()
    X, y = feats(df, geo, 2021, 2018, 2015), df.abst_2024

    # ---------- PASO 2: benchmark ----------
    tr, te = train_test_split(df.index, test_size=.2, random_state=42)
    sc = lambda m: make_pipeline(StandardScaler(), m)
    base = [("ridge", sc(Ridge(1.0))), ("rf", RandomForestRegressor(100, random_state=0, n_jobs=-1)),
            ("lgbm", LGBMRegressor(n_estimators=200, learning_rate=.05, verbose=-1, random_state=0))]
    models = {
        "Baseline_Naive": None,
        "Lasso_Regression": sc(Lasso(.05)),
        "Ridge_Regression": sc(Ridge(1.0)),
        "Random_Forest": RandomForestRegressor(100, random_state=0, n_jobs=-1),
        "LightGBM_Regressor": LGBMRegressor(n_estimators=200, learning_rate=.05, verbose=-1, random_state=0),
        "CatBoost_Regressor": CatBoostRegressor(iterations=300, verbose=0, random_seed=0),
        "Stacking_Ensemble": StackingRegressor(base, final_estimator=Ridge(1.0), cv=5),
    }
    rows, fitted = [], {}
    for name, m in models.items():
        if m is None:
            p = X.loc[te, "y_prev"]
        else:
            m.fit(X.loc[tr], y[tr]); fitted[name] = m; p = m.predict(X.loc[te])
        rows.append({"modelo": name, "rmse": mean_squared_error(y[te], p) ** .5,
                     "mae": mean_absolute_error(y[te], p), "r2": r2_score(y[te], p)})
    res = pd.DataFrame(rows)
    win = res.loc[res.rmse.idxmin(), "modelo"]
    res["ganador"] = res.modelo == win
    OUT.mkdir(exist_ok=True)
    (OUT / "benchmark_results.json").write_text(res.round(4).to_json(orient="records", indent=2))
    print(res.round(3).to_string(index=False), f"\nGanador: {win}")
    if win == "Baseline_Naive":
        win = res[res.modelo != "Baseline_Naive"].sort_values("rmse").iloc[0].modelo
        print(f"[WARN] Baseline ganó; simulación usa {win}")
    model = fitted[win]

    # ---------- PASO 3: escenarios (features desplazadas: 2024,2021,2018 -> 2027) ----------
    X27 = feats(df, geo, 2024, 2021, 2018)
    Xm = X27.copy()
    for c, f in SHOCK.items():
        Xm[c] = Xm[c] * f
    inercial = np.clip(model.predict(X27), 0, 100)
    mitigado = np.clip(model.predict(Xm), 0, 100)

    # ---------- PASO 4: GeoJSON ----------
    out = pd.DataFrame({
        "seccion_id": df.seccion_id, "municipio": df.municipio,
        "abstencion_real_2024": df.abst_2024.round(2),
        "prediccion_2027_inercial": inercial.round(2), "prediccion_2027_mitigado": mitigado.round(2),
        "diferencia_impacto": (inercial - mitigado).round(2),
        "semaforo_riesgo": semaforo(inercial),
        "semaforo_mitigado": semaforo(mitigado),
        "escolaridad": df.escolaridad.round(2), "pct_joven": df.pct_joven.round(3),
        "marginacion": df.marginacion.round(3), "brecha_joven": df.brecha_joven.round(3),
        "dist_casilla": df.dist_casilla.round(2), "urbano": df.urbano,
    })
    ag = (agebs.groupby("seccion_id").apply(lambda g: g[["ageb", "poblacion", "marginacion"]].to_dict("records"))
          .rename("agebs_vinculadas"))
    out = out.merge(ag, left_on="seccion_id", right_index=True, how="left")
    out["agebs_vinculadas"] = out.agebs_vinculadas.apply(lambda v: v if isinstance(v, list) else [])
    g = geo[["seccion_id", "geometry"]].merge(out, on="seccion_id")
    g["geometry"] = g.geometry.simplify(0.0001)
    g.to_file(OUT / "secciones_reto2.geojson", driver="GeoJSON")  # ponytail: agebs como lista -> fiona/pyogrio puede serializar como string; ver abajo
    # pyogrio escribe listas de dicts como cadena: reescribimos como JSON anidado real
    gj = json.loads((OUT / "secciones_reto2.geojson").read_text())
    lut = out.set_index("seccion_id").agebs_vinculadas
    for f in gj["features"]:
        f["properties"]["agebs_vinculadas"] = lut[f["properties"]["seccion_id"]]
    (OUT / "secciones_reto2.geojson").write_text(json.dumps(gj))
    print(out.semaforo_riesgo.value_counts().to_dict(), "| impacto medio:", out.diferencia_impacto.mean().round(3))


if __name__ == "__main__":
    main()
