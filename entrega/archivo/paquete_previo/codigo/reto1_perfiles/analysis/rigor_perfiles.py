# /// script
# dependencies = ["pandas", "pyarrow", "numpy", "scikit-learn"]
# ///
"""Reto 1: rigor estadístico de la tipología.
(1) Ruido de muestreo frente a señal: bootstrap paramétrico (SV ~ Binomial(SV+NV, tasa observada) en cada celda sección × sexo × edad × elección) para obtener la varianza
    de ruido de cada rasgo, su confiabilidad (1 − ruido/varianza total), la correlación entre ventanas corregida por atenuación y el techo de R² alcanzable con resultados de 2024.
(2) Incertidumbre de asignación: proporción de réplicas en que cada sección cae en su mismo perfil.
(3) Valor dentro del estado: R² (ponderado) de los perfiles del pasado sobre 2024 con efectos fijos de estado o de municipio, para ver qué aportan los perfiles por encima de la geografía.
(4) Intervalos de los contrastes por celda sexo × edad (2024) frente al perfil 5: remuestreo de municipios (500 réplicas).
Run: uv run reto1_perfiles/analysis/rigor_perfiles.py [réplicas=50]"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
B = int(sys.argv[1]) if len(sys.argv) > 1 else 50; R = "reto1_perfiles/reports/"; rng = np.random.default_rng(0); pd.set_option("display.width", 250)
s0 = L.load()
WIN = {"final": ([2015, 2018, 2021, 2024], [2018, 2024], [2015, 2021], (2018, 2024)), "pasado": ([2009, 2012, 2015, 2018], [2012, 2018], [2009, 2015], (2012, 2018)),
       "A": ([2009, 2012, 2015], [2012], [2009, 2015]), "B": ([2018, 2021, 2024], [2018, 2024], [2021])}
def out24(s):
    """Rasgos observados de 2024 sin encogimiento (los mismos resultados que validar_tipologia.py)."""
    d = s[s.AELEC == 2024]; nat = d.SV.sum() / (d.SV.sum() + d.NV.sum())
    def r(ged=None, sex=None):
        x = d if ged is None else d[d.gedad.isin(ged)]; x = x if sex is None else x[x.SEXO == sex]; g = x.groupby("sid")[["SV", "NV"]].sum(); return g.SV / (g.SV + g.NV)
    n = d.groupby("sid")[["SV", "NV"]].sum().sum(axis=1)
    return pd.DataFrame({"nivel": r() - nat, "brecha_joven": r(["18-34"]) - r(["55-74"]), "brecha_genero_18_54": r(["18-34", "35-54"], 1) - r(["18-34", "35-54"], 0), "n": n})
def all_feats(s): return {k: L.features(s, *w) for k, w in WIN.items()} | {"y24": out24(s).dropna()}
F0 = all_feats(s0)
# --- tipología final reproducida (mismo procedimiento que tipologia_final.py) y verificación contra el archivo publicado
sc = StandardScaler().fit(F0["final"][L.CLUSTER]); km = KMeans(5, n_init=50, random_state=0).fit(sc.transform(F0["final"][L.CLUSTER]))
order = pd.Series(km.cluster_centers_[:, 0]).sort_values().index; remap = {o: i for i, o in enumerate(order)}; lab0 = pd.Series(km.labels_, F0["final"].index).map(remap)
pub = pd.read_csv(R + "tipologia_secciones.csv", usecols=["sid", "c"]).set_index("sid").c; assert (lab0.reindex(pub.index) == pub).mean() > 0.999, "la tipología no se reproduce"
cent = km.cluster_centers_
# --- (1)-(2) bootstrap paramétrico
reps = {k: [] for k in F0}; agree = pd.Series(0.0, index=lab0.index)
n_cell = (s0.SV + s0.NV).to_numpy(); p_cell = np.where(n_cell > 0, s0.SV / np.maximum(n_cell, 1), 0)
for b in range(B):
    s = s0.copy(); sv = rng.binomial(n_cell.astype(np.int64), p_cell); s["SV"] = sv; s["NV"] = n_cell - sv; Fb = all_feats(s)
    for k in F0: reps[k].append(Fb[k].reindex(F0[k].index))
    X = sc.transform(Fb["final"].reindex(lab0.index)[L.CLUSTER]); lb = pd.Series(((X[:, None, :] - cent[None]) ** 2).sum(-1).argmin(1), lab0.index).map(remap); agree += (lb == lab0)
    print(f"réplica {b + 1}/{B}", flush=True)
agree /= B
noise = {k: pd.concat(v).groupby(level=0).var() for k, v in reps.items()}
rows = []
for f in L.CLUSTER + ["intermitencia"]:
    rel = {w: 1 - noise[w][f].mean() / F0[w][f].var() for w in ("A", "B", "final")}; c = F0["A"].index.intersection(F0["B"].index); r = F0["A"].loc[c, f].corr(F0["B"].loc[c, f])
    rows.append(dict(rasgo=f, confiabilidad_A=rel["A"], confiabilidad_B=rel["B"], confiabilidad_final=rel["final"], r_observada=r, r_corregida=r / np.sqrt(rel["A"] * rel["B"])))
REL = pd.DataFrame(rows); print("\n== (1) confiabilidad por ruido de muestreo y persistencia corregida por atenuación (secciones; ventanas A=2009-2015, B=2018-2024)"); print(REL.round(3).to_string(index=False))
# (5) ¿el cambio entre ventanas es territorial fino o jurisdiccional? persistencia dentro de municipio/estado (desviación de la media del grupo) y entre grupos (medias)
MUN = s0.drop_duplicates("sid").set_index("sid").eval("EDOCVE * 1000 + MPIOCVE"); PN = pd.read_parquet("data/processed/panel.parquet", columns=["AELEC", "EDOCVE", "SECCION", "DEF"]).query("AELEC == 2024"); DIS = pd.Series((PN.EDOCVE * 100 + PN.DEF).values, PN.EDOCVE * 10000 + PN.SECCION).groupby(level=0).first(); c = F0["A"].index.intersection(F0["B"].index); rows5 = []
for f in L.CLUSTER + ["intermitencia"]:
    for nm, g in (("estado", c // 10000), ("distrito federal", DIS.reindex(c).fillna(-1).values), ("municipio", MUN.reindex(c).values)):
        a, b = F0["A"].loc[c, f], F0["B"].loc[c, f]; ga, gb = a.groupby(g).transform("mean"), b.groupby(g).transform("mean"); na, nb = noise["A"].loc[c, f], noise["B"].loc[c, f]
        relw = np.sqrt((1 - na.mean() / (a - ga).var()) * (1 - nb.mean() / (b - gb).var())); mg = pd.DataFrame({"a": a.groupby(g).mean(), "b": b.groupby(g).mean()})
        rows5.append(dict(rasgo=f, nivel=nm, r_dentro=(a - ga).corr(b - gb), r_dentro_corregida=(a - ga).corr(b - gb) / relw, r_entre_medias=mg.a.corr(mg.b), var_dentro_pct=100 * (a - ga).var() / a.var()))
W5 = pd.DataFrame(rows5); W5.to_csv(R + "rigor_persistencia_niveles.csv", index=False)
print("\n== (5) persistencia entre ventanas dentro de estado/municipio y entre sus medias (secciones; corregida = por ruido de muestreo)"); print(W5.round(3).to_string(index=False))
y = F0["y24"].dropna(); w = y.n; techo = {f: 1 - (w * noise["y24"][f]).sum() / (w * (y[f] - np.average(y[f], weights=w)) ** 2).sum() for f in L.CLUSTER}
print("\n== techo de R² con resultados de 2024 (proporción de varianza ponderada que no es ruido de muestreo)"); print(pd.Series(techo).round(3).to_string())
conf = pd.DataFrame({"c": lab0, "confianza": agree})
A = conf.groupby("c").confianza.describe(percentiles=[.1, .5])[["mean", "10%", "50%"]]; A["pct_conf_0.8"] = conf.groupby("c").confianza.apply(lambda x: (x >= .8).mean())
A.loc["total"] = [conf.confianza.mean(), conf.confianza.quantile(.1), conf.confianza.median(), (conf.confianza >= .8).mean()]
print("\n== (2) estabilidad de la asignación ante ruido de muestreo"); print(A.round(3).to_string()); agree.rename("confianza_asignacion").to_csv(R + "rigor_asignacion.csv")
# --- (3) R² dentro de estado y municipio (perfiles del pasado → rasgos de 2024)
P = F0["pasado"]; kp = KMeans(5, n_init=20, random_state=0).fit(StandardScaler().fit_transform(P[L.CLUSTER])); com = P.index.intersection(y.index)
D = y.loc[com].copy(); D["perfil"] = kp.labels_[P.index.get_indexer(com)]; D["est"] = com // 10000
mun = s0.drop_duplicates("sid").set_index("sid"); D["mun"] = (mun.EDOCVE * 1000 + mun.MPIOCVE).reindex(com).values
def r2_fe(v, groups, it=100):
    """R² ponderado de efectos fijos aditivos (proyecciones alternadas)."""
    yy = D[v].to_numpy(); ww = D.n.to_numpy(); res = yy - np.average(yy, weights=ww)
    for _ in range(it if len(groups) > 1 else 1):
        for g in groups: res = res - pd.Series(res * ww).groupby(D[g].values).transform("sum").values / pd.Series(ww).groupby(D[g].values).transform("sum").values
    tss = (ww * (yy - np.average(yy, weights=ww)) ** 2).sum(); return 1 - (ww * res ** 2).sum() / tss
W3 = pd.DataFrame({v: {"perfil": r2_fe(v, ["perfil"]), "estado": r2_fe(v, ["est"]), "estado + perfil": r2_fe(v, ["est", "perfil"]), "municipio": r2_fe(v, ["mun"]), "municipio + perfil": r2_fe(v, ["mun", "perfil"])} for v in L.CLUSTER}).T
W3["aporte del perfil sobre estado"] = W3["estado + perfil"] - W3["estado"]; W3["aporte del perfil sobre municipio"] = W3["municipio + perfil"] - W3["municipio"]
print("\n== (3) R² ponderado sobre rasgos de 2024 con perfiles construidos con 2009-2018 (en muestra; municipio con ~2,400 efectos fijos)"); print(W3.round(3).to_string())
# --- (4) contrastes por celda frente al perfil 5 con IC por remuestreo de municipios
s24 = s0[(s0.AELEC == 2024) & s0.sid.isin(pub.index)].assign(c=lambda d: d.sid.map(pub), mun=lambda d: d.EDOCVE * 1000 + d.MPIOCVE)
cube = s24.groupby(["mun", "c", "SEXO", "banda"])[["SV", "NV"]].sum().unstack(["c", "SEXO", "banda"], fill_value=0); muns = cube.index; SV, NN = cube.SV.to_numpy(), (cube.SV + cube.NV).to_numpy(); cols = cube.SV.columns
def rates(wv): return (wv @ SV) / np.maximum(wv @ NN, 1)
est = pd.Series(rates(np.ones(len(muns))), cols); bt = np.stack([rates(rng.multinomial(len(muns), np.full(len(muns), 1 / len(muns))).astype(float)) for _ in range(500)])
bt = pd.DataFrame(bt, columns=cols)
rows = []
for (c, sx, bd) in cols:
    if c == 4: continue
    d = bt[(c, sx, bd)] - bt[(4, sx, bd)]; rows.append(dict(perfil=c + 1, sexo="HM"[sx], banda=bd, tasa=est[(c, sx, bd)], dif_p5_pp=100 * (est[(c, sx, bd)] - est[(4, sx, bd)]), ic_lo=100 * d.quantile(.025), ic_hi=100 * d.quantile(.975)))
C = pd.DataFrame(rows); C.to_csv(R + "rigor_contrastes.csv", index=False)
print("\n== (4) diferencia con el perfil 5 en la misma celda (pp, IC95% por remuestreo de municipios), celdas 18-44"); print(C[C.banda.isin(["18-24", "25-34", "35-44"])].round(1).to_string(index=False))
REL.to_csv(R + "rigor_confiabilidad.csv", index=False); W3.to_csv(R + "rigor_dentro_estado.csv"); pd.Series(techo).to_csv(R + "rigor_techo_r2.csv"); A.to_csv(R + "rigor_asignacion_resumen.csv")
