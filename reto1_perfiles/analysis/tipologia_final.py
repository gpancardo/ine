# /// script
# dependencies = ["pandas", "pyarrow", "numpy", "scikit-learn", "geopandas"]
# ///
"""Reto 1: tipología final (k=5, tres rasgos persistentes) y caracterización: edad × sexo, historial por elección, región/entidad, censo 2020 (descriptores ecológicos).
No usa voto por partido: el INE es imparcial y la segmentación no debe depender de preferencias partidistas. Salidas: reto1_perfiles/reports/tipologia_*.csv. Run: uv run reto1_perfiles/analysis/tipologia_final.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); sys.path.insert(0, str(Path(__file__).parent))
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import common as c, tip_lib as L
os.chdir(Path(__file__).resolve().parents[2]); pd.set_option("display.width", 260); K = 5; R = Path("reto1_perfiles/reports")
F = pd.read_parquet("data/processed/tipologia_features.parquet")
tipo = pd.read_parquet("data/processed/panel.parquet", columns=["AELEC", "EDOCVE", "SECCION", "TIPOSEC"]).query("AELEC == 2024"); tipo["sid"] = tipo.EDOCVE * 10000 + tipo.SECCION; F = F.join(tipo.drop_duplicates("sid").set_index("sid").TIPOSEC)
F["c"] = KMeans(K, n_init=50, random_state=0).fit_predict(StandardScaler().fit_transform(F[L.CLUSTER]))
order = F.groupby("c").nivel.mean().sort_values().index; F["c"] = F.c.map({o: i for i, o in enumerate(order)})   # 0 = menor participación relativa
REG = {r: set(v) for r, v in {"Norte": [2, 3, 26, 8, 5, 19, 28, 25, 10], "Occidente y Bajío": [14, 6, 18, 16, 11, 1, 22, 24, 32], "Centro": [9, 15, 17, 13, 29, 21], "Sur y Sureste": [12, 20, 7, 30, 27, 4, 31, 23]}.items()}
F["region"] = F.EDOCVE.map({e: r for r, v in REG.items() for e in v})
cen = c.eceg_features().reindex(F.index)
for k in ["pct_indigena", "graproes", "pct_analf", "pct_internet", "pct_nac_otra_ent", "pct_sin_servsalud" if False else "sin_servsalud", "pct_65mas", "pct_18_24", "pea", "desocup"]: F[k] = cen[k]
w = F.ln24
def wmean(g, col): d = g[[col, "ln24"]].dropna(); return np.average(d[col], weights=d.ln24) if len(d) else np.nan
G = F.groupby("c"); T = pd.DataFrame({col: G.apply(lambda g, col=col: wmean(g, col)) for col in L.CLUSTER + L.DESCRIBE})
T["secciones"] = G.size(); T["LN24_millones"] = G.ln24.sum() / 1e6; T["%LN"] = G.ln24.sum() / F.ln24.sum() * 100
for t in "URM": T["%" + t] = G.TIPOSEC.apply(lambda x: (x == t).mean()) * 100
for k in ["graproes", "pct_analf", "pct_indigena", "pct_internet", "pct_nac_otra_ent", "sin_servsalud", "pct_65mas", "pct_18_24", "desocup"]: T[k] = G.apply(lambda g, k=k: wmean(g, k))
T.to_csv(R / "tipologia_perfiles.csv"); F.reset_index(names="sid").to_csv(R / "tipologia_secciones.csv", index=False)
print("== perfil (media ponderada por lista nominal)"); print(T.round(3).T.to_string())
reg = F.groupby(["c", "region"]).ln24.sum().unstack().fillna(0); reg = reg.div(reg.sum(axis=1), axis=0) * 100; reg.to_csv(R / "tipologia_regiones.csv"); print("\n== % de la lista nominal de cada grupo por región"); print(reg.round(0).to_string())
ent = F.groupby(["EDOCVE", "c"]).ln24.sum().unstack().fillna(0); entp = ent.div(ent.sum(axis=1), axis=0) * 100; entp.index = [c.ESTADOS[i] for i in entp.index]; entp.to_csv(R / "tipologia_estados.csv"); print("\n== % de la lista nominal de cada estado por grupo (estados con mayor concentración en cada grupo)")
for k in range(K): print(k, ", ".join(f"{i} {v:.0f}%" for i, v in entp[k].sort_values(ascending=False).head(5).items()))
# historial de participación por elección y grupo (secciones con las seis elecciones) y curvas edad × sexo 2024
s = pd.read_parquet("data/processed/perfiles_seccion.parquet").merge(F[["c"]], left_on="sid", right_index=True)
hist = s.groupby(["c", "AELEC"]).apply(lambda d: d.SV.sum() / (d.SV.sum() + d.NV.sum())).unstack("AELEC"); nat = s.groupby("AELEC").apply(lambda d: d.SV.sum() / (d.SV.sum() + d.NV.sum())); hist.loc["nacional (secciones tipificadas)"] = nat
hist.to_csv(R / "tipologia_historial.csv"); print("\n== participación por elección y grupo"); print((hist * 100).round(1).to_string())
cur = s[s.AELEC == 2024].groupby(["c", "SEXO", "banda"]).apply(lambda d: d.SV.sum() / (d.SV.sum() + d.NV.sum())).unstack("banda"); cur.to_csv(R / "tipologia_curvas_2024.csv"); print("\n== 2024 por grupo, sexo (0=H, 1=M) y edad (%)"); print((cur * 100).round(1).to_string())
