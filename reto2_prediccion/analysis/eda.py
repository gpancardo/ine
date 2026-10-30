# /// script
# dependencies = ["pandas", "pyarrow", "geopandas", "matplotlib", "scikit-learn", "scipy"]
# ///
"""EDA: figuras -> reto2_prediccion/reports/fig/, números -> reto2_prediccion/reports/eda_stats.json.  Run: uv run analysis/eda.py"""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib"))
os.chdir(Path(__file__).resolve().parents[2])  # rutas relativas a la raíz del proyecto
import common as c

FIG = Path("reto2_prediccion/reports/fig"); FIG.mkdir(parents=True, exist_ok=True)
INK, MUTED, GRID, SURF = "#0b0b0b", "#898781", "#e1e0d9", "#fcfcfb"
B, O, A = "#2a78d6", "#eb6834", "#1baf7a"
SEQ = LinearSegmentedColormap.from_list("seq", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": GRID, "axes.labelcolor": INK,
                     "text.color": INK, "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": .6, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "savefig.dpi": 140})
S = {}
YEARS = c.YEARS
shade = lambda ax: [ax.axvspan(y - .5, y + .5, color="#f0efec", zorder=0) for y in YEARS if y in c.MID]  # intermedias sombreadas


def save(name):
    plt.tight_layout(); plt.savefig(FIG / f"{name}.png"); plt.close()


# ---- nacional (LN-ponderado, panel completo) ----
p = c.load_long()
g = p.groupby("AELEC")
nat = pd.DataFrame({"abst_adj": g.NV.sum() / (g.SV.sum() + g.NV.sum()), "abst_raw": 1 - g.SV.sum() / g.LN.sum(),
                    "ns": g.NS.sum() / g.LN.sum(), "ln": g.LN.sum(), "n_sec": g.size()})
for k, n in (("j", "joven 18-24"), ("a", "adulto 25-59"), ("m", "mayor 60+")):
    nat[f"raw_{k}"] = 1 - g[f"SV_{k}"].sum() / g[f"LN_{k}"].sum()
nat["raw_f"] = 1 - g.SV_f.sum() / g.LN_f.sum(); nat["raw_h"] = 1 - (g.SV.sum() - g.SV_f.sum()) / (g.LN.sum() - g.LN_f.sum())
S["nacional"] = nat.round(4).to_dict("index")

fig, ax = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [2, 1]})
shade(ax[0]); ax[0].plot(YEARS, nat.abst_adj * 100, color=B, lw=2, marker="o", ms=7, label="Ajustada NV/(SV+NV)")
ax[0].plot(YEARS, nat.abst_raw * 100, color=O, lw=2, marker="o", ms=7, label="Cruda 1−SV/LN")
ax[0].set_xticks(YEARS); ax[0].set_ylabel("% abstención"); ax[0].set_title("Abstención nacional (sombreado = intermedia)", loc="left", fontsize=10)
ax[0].legend(frameon=False); ax[1].bar([str(y) for y in YEARS], nat.ns * 100, color=A, width=.55)
ax[1].set_title("% lista nominal sin dato (NS)", loc="left", fontsize=10); ax[1].grid(axis="x", visible=False)
save("f01_nacional_ciclo")

fig, ax = plt.subplots(figsize=(7.5, 3.8)); shade(ax)
for k, lab, col in (("j", "Joven 18–24", O), ("a", "Adulto 25–59", B), ("m", "Mayor 60+", A)):
    ax.plot(YEARS, nat[f"raw_{k}"] * 100, color=col, lw=2, marker="o", ms=7, label=lab)
ax.set_xticks(YEARS); ax.set_ylabel("% abstención (cruda)"); ax.legend(frameon=False); ax.set_title("Abstención por edad", loc="left", fontsize=10)
save("f02_edad")
S["brecha_joven_mayor_pp"] = ((nat.raw_j - nat.raw_m) * 100).round(1).to_dict()

# ---- sección (panel balanceado) ----
w = c.load_wide()
S["n_secciones_balanceadas"] = len(w); S["n_secciones_total_2024"] = int(nat.n_sec[2024])
ab = w[[f"abst_{y}" for y in YEARS]]
fig, ax = plt.subplots(figsize=(7.5, 3.8)); shade(ax)
bp = ax.boxplot([ab[f"abst_{y}"] * 100 for y in YEARS], positions=YEARS, widths=1.4, showfliers=False, patch_artist=True,
                medianprops=dict(color=INK, lw=1.5), boxprops=dict(facecolor="#9ec5f4", edgecolor=B), whiskerprops=dict(color=B), capprops=dict(color=B))
ax.set_xticks(YEARS); ax.set_xticklabels(YEARS); ax.set_ylabel("% abstención por sección"); ax.set_title("Dispersión entre secciones (caja = IQR, bigotes 1.5·IQR)", loc="left", fontsize=10)
save("f03_dispersion")
S["sd_seccion"] = ab.std().round(4).to_dict(); S["iqr_seccion"] = (ab.quantile(.75) - ab.quantile(.25)).round(4).to_dict()

cor = ab.corr(); S["corr_secciones"] = cor.round(3).to_dict()
fig, ax = plt.subplots(figsize=(4.8, 4.2)); ax.grid(False)
im = ax.imshow(cor.values, cmap=SEQ, vmin=.3, vmax=1)
ax.set_xticks(range(6)); ax.set_xticklabels(YEARS); ax.set_yticks(range(6)); ax.set_yticklabels(YEARS)
for i in range(6):
    for j in range(6): ax.text(j, i, f"{cor.values[i, j]:.2f}", ha="center", va="center", color="white" if cor.values[i, j] > .7 else INK, fontsize=9)
ax.set_title("Correlación entre años (secciones)", loc="left", fontsize=10); save("f04_persistencia")

tip = {"U": "Urbana", "M": "Mixta", "R": "Rural"}
fig, ax = plt.subplots(figsize=(7.5, 3.8)); shade(ax)
for t, col in (("U", B), ("M", A), ("R", O)):
    ax.plot(YEARS, [w[w.TIPOSEC == t][f"abst_{y}"].mean() * 100 for y in YEARS], color=col, lw=2, marker="o", ms=7, label=tip[t])
ax.set_xticks(YEARS); ax.set_ylabel("% abstención (media de secciones)"); ax.legend(frameon=False); ax.set_title("Urbano / mixto / rural", loc="left", fontsize=10)
save("f05_tipo")
S["tipo_2021"] = {t: round(w[w.TIPOSEC == t].abst_2021.mean(), 4) for t in "UMR"}

st = w.groupby("ent")[["abst_2021", "abst_2024"]].mean().sort_values("abst_2021")
st.index = [c.ESTADOS[i] for i in st.index]
fig, ax = plt.subplots(figsize=(7.5, 6)); ax.barh(st.index, st.abst_2021 * 100, color=B, height=.7); ax.grid(axis="y", visible=False)
ax.set_xlabel("% abstención 2021 (media de secciones)"); ax.set_title("Estados: abstención 2021", loc="left", fontsize=10); save("f06_estados")
S["estados_2021_top5"] = st.abst_2021.tail(5).round(3).to_dict(); S["estados_2021_bottom5"] = st.abst_2021.head(5).round(3).to_dict()
# varianza entre/within estado y municipio (ICC simple)
tot = w.abst_2021.var()
S["var_entre_estado"] = round(w.groupby("ent").abst_2021.transform("mean").var() / tot, 3)
S["var_entre_municipio"] = round(w.groupby("mun").abst_2021.transform("mean").var() / tot, 3)

# ---- covariables ECEG ----
feat = [x for x in c.eceg_features().columns if x != "pobtot"] + ["pobtot"]
w["ln_ln2021"] = np.log(w.ln_2021)
cc = w[feat + ["ln_ln2021"]].corrwith(w.abst_2021, method="spearman").sort_values()
S["spearman_abst2021"] = cc.round(3).to_dict()
fig, ax = plt.subplots(figsize=(7.5, 6.5)); ax.barh(cc.index, cc.values, color=[O if v < 0 else B for v in cc.values], height=.7); ax.grid(axis="y", visible=False)
ax.set_xlabel("Spearman con abstención 2021 (azul +, naranja −)"); ax.set_title("Qué acompaña a la abstención (censo 2020)", loc="left", fontsize=10); save("f07_correlaciones")

# ---- espacial: Moran's I con KNN(8) sobre centroides ----
from sklearn.neighbors import NearestNeighbors
geo = c.load_geo().loc[w.index]
cen = np.c_[geo.geometry.centroid.x, geo.geometry.centroid.y]
idx = NearestNeighbors(n_neighbors=9).fit(cen).kneighbors(cen)[1][:, 1:]
np.save("data/processed/knn8_idx.npy", idx); pd.Series(w.index).to_csv("data/processed/knn8_sid.csv", index=False)
def moran(x):  # W estandarizada por filas, k=8: I = Σ z_i (Wz)_i / Σ z²
    z = x - x.mean(); return float((z * z[idx].mean(1)).sum() / (z ** 2).sum())
S["moran_I"] = {y: round(moran(w[f"abst_{y}"].values), 3) for y in YEARS}
S["moran_I_residuo_2021_vs_2015"] = round(moran((w.abst_2021 - w.abst_2015).values), 3)
wall = c.load_wide(False); wall = wall[wall.abst_2021.notna()]
S["n_secciones_con_dato_2021"] = len(wall); S["pct_secciones_2021_en_balanceado"] = round(len(w) / len(wall), 3)
g2 = c.load_geo().join(wall.abst_2021, how="inner"); g2["v"] = g2.abst_2021 * 100; g2["geometry"] = g2.geometry.simplify(400)
fig, ax = plt.subplots(figsize=(9, 6)); g2.plot(column="v", cmap=SEQ, ax=ax, linewidth=0, legend=True, vmin=20, vmax=75, legend_kwds={"shrink": .6, "label": "% abstención 2021"})
ax.set_axis_off(); ax.set_title("Abstención por sección, 2021", loc="left", fontsize=10); save("f08_mapa_2021")

# ---- calidad de datos ----
S["calidad"] = {"LN_max_seccion": int(p.LN.max()), "secciones_LN_menor_100_2024": int((p[p.AELEC == 2024].LN < 100).sum()),
                "abst_cero_o_uno_2024": int(((p[p.AELEC == 2024].abst <= 0) | (p[p.AELEC == 2024].abst >= 1)).sum()),
                "secciones_sin_eceg_o_no_balanceadas": int(c.load_wide(False).shape[0] - len(w))}
S["tamano_balanceadas_vs_resto_ln2021_mediana"] = [float(w.ln_2021.median()), float(c.load_wide(False).drop(w.index).ln_2021.median())]
json.dump(S, open("reto2_prediccion/reports/eda_stats.json", "w"), indent=1, ensure_ascii=False, default=float)
print(json.dumps({k: S[k] for k in ("nacional", "brecha_joven_mayor_pp", "tipo_2021", "var_entre_estado", "var_entre_municipio", "moran_I", "calidad", "tamano_balanceadas_vs_resto_ln2021_mediana", "sd_seccion")}, indent=0, ensure_ascii=False, default=float)[:3500])
print(cc.round(2).to_string())
