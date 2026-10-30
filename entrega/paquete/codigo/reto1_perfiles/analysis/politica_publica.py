# /// script
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Reto 1: del perfil a la acción. Votos por elección que se recuperarían si cada brecha se cerrara al nivel de secciones comparables (mismo tipo U/M/R), con base 2024:
nivel (hasta el percentil 75 de pares), brecha de género (hombres 18-54 como las mujeres de su sección), jóvenes 18-34 (hasta el p75 de pares) y 75+ (como el grupo 55-74 de su sección).
Incluye intervalos por remuestreo de municipios (500 réplicas) y sensibilidad al punto de referencia. Los criterios se solapan: no se suman.
La intermitencia no se usa para focalizar (no persiste entre ventanas de elecciones). Run: uv run reto1_perfiles/analysis/politica_publica.py"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
pd.set_option("display.width", 250); pd.set_option("display.float_format", lambda v: f"{v:,.3f}")
T = pd.read_csv("reto1_perfiles/reports/tipologia_secciones.csv").set_index("sid")
s = pd.read_parquet("data/processed/perfiles_seccion.parquet"); s = s[s.AELEC == 2024].copy(); s["g"] = s.banda.map({"18-24": "J", "25-34": "J", "35-44": "A", "45-54": "A", "55-64": "M", "65-74": "M", "75+": "E"})
def grp(mask): d = s[mask].groupby("sid")[["LN", "SV", "NV"]].sum(); d["r"] = d.SV / (d.SV + d.NV); return d
J, E_, M_ = grp(s.g == "J"), grp(s.g == "E"), grp(s.g == "M"); Hm, Mj = grp((s.SEXO == 0) & s.g.isin(["J", "A"])), grp((s.SEXO == 1) & s.g.isin(["J", "A"]))
P = pd.read_parquet("data/processed/panel.parquet", columns=["AELEC", "EDOCVE", "SECCION", "MPIOCVE", "MPIONOM", "DEF", "TIPOSEC"]).query("AELEC == 2024"); P["sid"] = P.EDOCVE * 10000 + P.SECCION; P = P.drop_duplicates("sid").set_index("sid")
D = T[["c", "nivel_abs", "ln24"]].join(P[["MPIOCVE", "MPIONOM", "DEF", "TIPOSEC"]]); D["EDOCVE"] = T.EDOCVE; D["mun"] = D.EDOCVE * 1000 + D.MPIOCVE
D["rj"] = J.r.reindex(D.index); q = lambda v, p: v.groupby(D.TIPOSEC).transform(lambda x: x.quantile(p))
def potencial(pct):
    out = pd.DataFrame(index=D.index); out["v_nivel"] = D.ln24 * np.clip(q(D.nivel_abs, pct) - D.nivel_abs, 0, None); out["v_joven"] = J.LN.reindex(D.index) * np.clip(q(D.rj, pct) - D.rj, 0, None)
    return out.fillna(0)
V0 = potencial(.75); D["v_nivel"], D["v_joven"] = V0.v_nivel, V0.v_joven
D["v_genero"] = (Hm.LN * np.clip(Mj.r - Hm.r, 0, None)).reindex(D.index).fillna(0); D["v_75"] = (E_.LN * np.clip(M_.r - E_.r, 0, None)).reindex(D.index).fillna(0)
V = ["v_nivel", "v_genero", "v_joven", "v_75"]; G = D.groupby("c")[V].sum() / 1e6; G.insert(0, "LN_millones", D.groupby("c").ln24.sum() / 1e6); G.loc["Total"] = G.sum()
# intervalos: remuestreo de municipios
mg = D.groupby(["mun", "c"])[V].sum().reset_index(); muns = mg.mun.unique(); rng = np.random.default_rng(0); idx = {m: g for m, g in mg.groupby("mun")}; boots = []
for b in range(500):
    pick = rng.choice(muns, len(muns)); d = pd.concat([idx[m] for m in pick]); t = d.groupby("c")[V].sum() / 1e6; t.loc["Total"] = t.sum(); boots.append(t)
B = np.stack([b.reindex(G.index)[V].values for b in boots]); lo, hi = np.percentile(B, 2.5, axis=0), np.percentile(B, 97.5, axis=0)
CI = pd.DataFrame({f"{v} IC95%": [f"{G.loc[i, v]:.2f} ({lo[j, k]:.2f}-{hi[j, k]:.2f})" for j, i in enumerate(G.index)] for k, v in enumerate(V)}, index=G.index)
print("== votos recuperables (millones) por perfil y criterio (IC95% por remuestreo de municipios; criterios no sumables)"); print(CI.to_string()); G.to_csv("reto1_perfiles/reports/politica_grupos.csv"); CI.to_csv("reto1_perfiles/reports/politica_grupos_ic.csv")
print("\n== sensibilidad del punto de referencia (millones de votos, total nacional)"); sens = {f"p{int(p*100)}": potencial(p).sum() / 1e6 for p in (.5, .6, .75, .9)}; print(pd.DataFrame(sens).T.round(2).to_string())
pd.DataFrame(sens).T.to_csv("reto1_perfiles/reports/politica_sensibilidad.csv")
D[["EDOCVE", "DEF", "mun", "MPIONOM", "TIPOSEC", "c", "ln24", "nivel_abs"] + V].round(1).to_csv("reto1_perfiles/reports/politica_secciones.csv")  # insumo del tablero
M = D.groupby("mun").agg(nombre=("MPIONOM", "first"), edo=("EDOCVE", "first"), ln=("ln24", "sum"), grupo=("c", lambda x: x.value_counts().index[0]), pureza=("c", lambda x: x.value_counts(normalize=True).iloc[0]), **{k: (k, "sum") for k in V}).reset_index(); M.to_csv("reto1_perfiles/reports/politica_municipios.csv", index=False)
Dd = D.groupby(["EDOCVE", "DEF"]).agg(ln=("ln24", "sum"), grupo=("c", lambda x: x.value_counts().index[0]), **{k: (k, "sum") for k in V}).reset_index(); Dd.to_csv("reto1_perfiles/reports/politica_distritos.csv", index=False)
for k, nm in (("v_nivel", "nivel"), ("v_genero", "brecha de género"), ("v_joven", "jóvenes")):
    t = M.sort_values(k, ascending=False).head(8); print(f"\n== 8 municipios con más votos recuperables por {nm} (miles)"); print(t.assign(miles=t[k] / 1e3, ln_mil=t.ln / 1e3, perfil=t.grupo.map(L.NOMBRES))[["nombre", "edo", "perfil", "ln_mil", "miles"]].round(1).to_string(index=False))
x = M.v_nivel.sort_values(ascending=False); cum = x.cumsum() / x.sum(); print(f"\nel {100*(cum <= .5).sum()/len(M):.1f}% de los municipios ({(cum <= .5).sum()}) concentra el 50% de los votos recuperables por nivel")
