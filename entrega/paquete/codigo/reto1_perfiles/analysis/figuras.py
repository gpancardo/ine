# /// script
# dependencies = ["pandas", "pyarrow", "numpy", "matplotlib", "geopandas"]
# ///
"""Reto 1: figuras estáticas (paleta de referencia validada; categorías por facetas, no por varios colores). Run: uv run reto1_perfiles/analysis/figuras.py"""
import os, sys
from pathlib import Path
import textwrap, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared" / "lib")); sys.path.insert(0, str(Path(__file__).parent))
import common as c, tip_lib as L
os.chdir(Path(__file__).resolve().parents[2]); R = Path("reto1_perfiles/reports"); OUT = R / "fig"; OUT.mkdir(exist_ok=True, parents=True)
SURF, INK, INK2, MUTE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"; BLUE, ORANGE, RED, NEUT = "#2a78d6", "#eb6834", "#e34948", "#f0efec"; N = L.NOMBRES; K = 5
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": GRID, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
T = pd.read_csv(R / "tipologia_secciones.csv").set_index("sid"); share = T.groupby("c").ln24.sum() / T.ln24.sum() * 100; P = pd.read_csv(R / "tipologia_perfiles.csv").set_index("c")
cur = pd.read_csv(R / "tipologia_curvas_2024.csv", index_col=[0, 1]) * 100; bands = list(cur.columns)
# ---- Fig 1: curvas edad × sexo
fig, ax = plt.subplots(2, 3, figsize=(12, 6.2), sharey=True)
for k, a in zip(range(K), ax.ravel()):
    for sx, col, lab in ((1, BLUE, "Mujeres"), (0, ORANGE, "Hombres")):
        y = cur.loc[(k, sx)].values; a.plot(range(len(bands)), y, color=col, lw=2, marker="o", ms=4, mfc=SURF, mew=1.5); a.text(len(bands) - 1 + .18, y[-1], lab, color=INK2, fontsize=8.5, ha="left", va="center")
    a.set_title(f"{N[k]}\n{share[k]:.0f}% de la lista nominal", fontsize=10, loc="left", color=INK); a.grid(axis="y", color=GRID, lw=.8); a.set_ylim(25, 90); a.set_xticks(range(len(bands))); a.set_xticklabels(bands, fontsize=8); a.set_xlim(-.3, len(bands) - 1 + 1.5)
ax.ravel()[5].axis("off"); ax.ravel()[5].text(0, .6, transform=ax.ravel()[5].transAxes, s="Cada panel: participación 2024 por grupo de edad.\nLa lectura útil es la distancia entre las dos líneas\n(brecha de género) y la pendiente de 18 a 54 años\n(brecha de jóvenes).", fontsize=9.5, color=INK2, va="center")
fig.suptitle("Participación 2024 por edad y sexo, según perfil de la sección (% de la lista nominal con marca de voto)", x=.01, ha="left", fontsize=11.5); fig.supylabel("Participación (%)", fontsize=9); fig.tight_layout(rect=(0.02, 0, 1, .95)); fig.savefig(OUT / "fig1_curvas_edad_sexo.png", dpi=170); plt.close(fig)
# ---- Fig 2: perfil (z entre grupos, anotado)
rows = [("nivel_abs", "Participación promedio 2015-2024 (%)", 100, "{:.0f}"), ("brecha_genero_18_54", "Brecha de género 18-54 (M−H, pp)", 100, "{:.0f}"), ("brecha_joven", "Jóvenes 18-34 vs 55-74 (pp)", 100, "{:.0f}"), ("caida_75", "75+ vs 55-74 (pp)", 100, "{:.0f}"), ("%R", "Secciones rurales (%)", 1, "{:.0f}"), ("pct_indigena", "Lengua indígena (%)", 100, "{:.0f}"), ("graproes", "Escolaridad promedio (años)", 1, "{:.1f}"), ("pct_internet", "Hogares con internet (%)", 100, "{:.0f}"), ("pct_nac_otra_ent", "Nacidos en otra entidad (%)", 100, "{:.0f}")]
Z = np.array([(P[r[0]] - P[r[0]].mean()) / P[r[0]].std() for r in rows]); cm = LinearSegmentedColormap.from_list("div", [RED, NEUT, BLUE]); fig, a = plt.subplots(figsize=(12, 5.4)); a.imshow(Z, cmap=cm, vmin=-2, vmax=2, aspect="auto")
for i, r in enumerate(rows):
    for j in range(K): a.text(j, i, r[3].format(P.loc[j, r[0]] * r[2]), ha="center", va="center", fontsize=9.5, fontweight="bold" if abs(Z[i, j]) > 1.1 else "normal")
a.set_xticks(range(K)); a.set_xticklabels([textwrap.fill(N[j], 17) for j in range(K)], fontsize=8.5); a.set_yticks(range(len(rows))); a.set_yticklabels([r[1] for r in rows], fontsize=9)
a.axhline(2.5, color=SURF, lw=3); a.text(K - .42, 1.0, "Criterios\nde agrupación", fontsize=8.5, color=INK2, va="center", ha="left"); a.text(K - .42, 5.5, "Descripción", fontsize=8.5, color=INK2, va="center", ha="left"); a.set_xlim(-.5, K - .5)
a.tick_params(length=0); [sp.set_visible(False) for sp in a.spines.values()]; a.xaxis.tick_top(); a.set_title("Perfil de cada grupo (color: desviación respecto al promedio de los cinco grupos; azul = más, rojo = menos)", fontsize=10.5, loc="left", pad=44)
fig.tight_layout(); fig.savefig(OUT / "fig2_perfil_grupos.png", dpi=170); plt.close(fig)
# ---- Fig 3: mapa de puntos por perfil
geo = c.load_geo(); cen = pd.DataFrame({"x": geo.geometry.centroid.x, "y": geo.geometry.centroid.y}, index=geo.index).join(T[["c"]], how="inner"); fig, ax = plt.subplots(2, 3, figsize=(12, 7.4))
for k, a in zip(range(K), ax.ravel()):
    o = cen[cen.c != k]; h = cen[cen.c == k]; a.scatter(o.x, o.y, s=.35, c="#d9d8d3", lw=0); a.scatter(h.x, h.y, s=.9, c=BLUE, lw=0); a.set_title(f"{N[k]}\n{len(h):,} secciones · {share[k]:.0f}% de la lista nominal", fontsize=9.5, loc="left"); a.set_aspect("equal"); a.axis("off")
ax.ravel()[5].axis("off"); fig.suptitle("Dónde está cada perfil (cada punto es una sección electoral; marco cartográfico 2021)", x=.01, ha="left", fontsize=11.5); fig.tight_layout(rect=(0, 0, 1, .96)); fig.savefig(OUT / "fig3_mapa_perfiles.png", dpi=170); plt.close(fig)
# ---- Fig 4: votos recuperables con IC
G = pd.read_csv(R / "politica_grupos.csv", index_col=0).drop(index="Total"); G.index = G.index.astype(int); ci = pd.read_csv(R / "politica_grupos_ic.csv", index_col=0).drop(index="Total"); ci.index = ci.index.astype(int)
lens = [("v_nivel", "Nivel de participación\n(hasta el p75 de comparables)"), ("v_genero", "Brecha de género\n(hombres 18-54 como las mujeres)"), ("v_joven", "Jóvenes 18-34\n(hasta el p75 de comparables)"), ("v_75", "75 años y más\n(como el grupo 55-74)")]
fig, ax = plt.subplots(1, 4, figsize=(13, 4.2), sharey=True)
for a, (k, t) in zip(ax, lens):
    v = G.loc[range(K), k].values; lo = ci[f"{k} IC95%"].str.extract(r"\(([\d.]+)-([\d.]+)\)").astype(float).loc[range(K)].values; a.barh(range(K), v, color=BLUE, height=.62); a.errorbar(v, range(K), xerr=[v - lo[:, 0], lo[:, 1] - v], fmt="none", ecolor=INK2, elinewidth=1, capsize=2.5)
    a.set_title(t, fontsize=9.5, loc="left"); a.invert_yaxis(); a.grid(axis="x", color=GRID, lw=.8); a.set_axisbelow(True); a.set_xlim(0, lo[:, 1].max() * 1.28); a.set_yticks(range(K)); a.set_yticklabels([N[j] for j in range(K)], fontsize=8.5)
    for i, x in enumerate(v): a.text(lo[i, 1] + lo[:, 1].max() * .02, i, f"{x:.2f}", va="center", fontsize=8.5, color=INK2)
fig.suptitle("Votos recuperables por elección con 2024 como base (millones, IC95% por remuestreo de municipios; cada panel es un criterio distinto y no se suman)", x=.01, ha="left", fontsize=10.5); fig.tight_layout(rect=(0, 0, 1, .93)); fig.savefig(OUT / "fig4_votos_recuperables.png", dpi=170); plt.close(fig)
# ---- Fig 5: concentración municipal
M = pd.read_csv(R / "politica_municipios.csv"); x = M.v_nivel.sort_values(ascending=False).values; cum = np.cumsum(x) / x.sum(); n50 = int((cum <= .5).sum()); fig, a = plt.subplots(figsize=(7.2, 4.2))
a.plot(np.arange(1, len(x) + 1) / len(x) * 100, cum * 100, color=BLUE, lw=2); a.plot([0, 100], [0, 100], color=MUTE, lw=1, ls=(0, (4, 3))); a.scatter([n50 / len(x) * 100], [50], color=BLUE, s=36, zorder=3, edgecolor=SURF, lw=1.5)
a.annotate(f"{n50} municipios ({n50/len(x)*100:.1f}%)\nconcentran la mitad", (n50 / len(x) * 100, 50), xytext=(14, 36), fontsize=9.5, arrowprops=dict(arrowstyle="-", color=MUTE, lw=.8)); a.text(55, 40, "Distribución pareja", color=MUTE, fontsize=8.5, rotation=34)
a.set_xlabel("Municipios ordenados de mayor a menor potencial (% acumulado)"); a.set_ylabel("Votos recuperables por nivel (% acumulado)"); a.grid(color=GRID, lw=.8); a.set_xlim(0, 100); a.set_ylim(0, 100); a.set_title("El potencial de participación se concentra en pocos municipios", fontsize=10.5, loc="left"); fig.tight_layout(); fig.savefig(OUT / "fig5_concentracion.png", dpi=170); plt.close(fig)
# ---- Fig 6: historial por elección (cada perfil contra el promedio de las secciones tipificadas)
H = pd.read_csv(R / "tipologia_historial.csv", index_col=0) * 100; yrs = [int(y) for y in H.columns]; nat = H.loc["nacional (secciones tipificadas)"].values; fig, ax = plt.subplots(2, 3, figsize=(12, 6), sharey=True)
for k, a in zip(range(K), ax.ravel()):
    a.plot(range(6), nat, color=MUTE, lw=1.5, ls=(0, (4, 3))); a.plot(range(6), H.loc[str(k)].values, color=BLUE, lw=2, marker="o", ms=4, mfc=SURF, mew=1.5); a.set_title(f"{N[k]}", fontsize=10, loc="left"); a.set_xticks(range(6)); a.set_xticklabels([str(y)[2:] if False else y for y in yrs], fontsize=8); a.grid(axis="y", color=GRID, lw=.8); a.set_ylim(30, 75)
    for i in (0, 5): a.text(i, H.loc[str(k)].values[i] + 2.2, f"{H.loc[str(k)].values[i]:.0f}", fontsize=8.5, color=INK2, ha="center")
ax.ravel()[5].axis("off"); ax.ravel()[5].text(0, .6, transform=ax.ravel()[5].transAxes, s="Línea azul: el perfil. Línea punteada:\npromedio de las secciones tipificadas.\nPresidenciales: 2012, 2018, 2024;\nintermedias: 2009, 2015, 2021.", fontsize=9.5, color=INK2, va="center")
fig.suptitle("Historial de participación por elección (%, lista nominal con marca de voto)", x=.01, ha="left", fontsize=11.5); fig.tight_layout(rect=(0, 0, 1, .95)); fig.savefig(OUT / "fig6_historial.png", dpi=170); plt.close(fig)
# ---- Fig 7: conectividad y medios por perfil
Mr = pd.read_csv(R / "medios_perfiles.csv", index_col=0) * 100; cols = [("radio_2020", "Radio"), ("tv_2020", "Televisión"), ("stvp_2020", "TV de paga"), ("cel_2020", "Celular"), ("inter_2020", "Internet"), ("pc_2020", "Computadora"), ("sinrtv_2020", "Sin radio ni TV")]
Zm = Mr.loc[[str(i) for i in range(K)], [x[0] for x in cols]].values; cm2 = LinearSegmentedColormap.from_list("seq", ["#cde2fb", "#2a78d6", "#0d366b"]); fig, a = plt.subplots(figsize=(10.5, 3.9)); a.imshow(Zm, cmap=cm2, vmin=0, vmax=100, aspect="auto")
for i in range(K):
    for j in range(len(cols)): a.text(j, i, f"{Zm[i, j]:.0f}", ha="center", va="center", fontsize=10, color="white" if Zm[i, j] > 55 else INK)
a.set_xticks(range(len(cols))); a.set_xticklabels([x[1] for x in cols], fontsize=9); a.set_yticks(range(K)); a.set_yticklabels([N[j] for j in range(K)], fontsize=9); a.xaxis.tick_top(); a.tick_params(length=0); [sp.set_visible(False) for sp in a.spines.values()]
a.set_title("Hogares con cada medio, por perfil (% de viviendas particulares habitadas)\nCenso 2020, secciones ponderadas por lista nominal", fontsize=10, loc="left", pad=34); fig.tight_layout(); fig.savefig(OUT / "fig7_medios.png", dpi=170); plt.close(fig)
print(sorted(p.name for p in OUT.glob("*.png")))
