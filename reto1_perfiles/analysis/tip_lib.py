"""Rasgos de perfil de participación por sección (compartidos por tipologia*.py, validar_tipologia.py, robustez_tipologia.py, politica_publica.py).
Rasgos de AGRUPACIÓN: los persistentes entre ventanas de elecciones disjuntas (r de 0.5 a 0.7 entre 2009-2015 y 2018-2024): nivel relativo al nacional, brecha de género 18-54 y brecha de jóvenes.
Rasgos de DESCRIPCIÓN: caída de 75+, brecha de género 55+, intermitencia (presidencial − intermedia; NO persiste: r=0.28 en secciones, 0.07 en municipios) y tendencia."""
import numpy as np, pandas as pd
G = {"18-34": ["18-24", "25-34"], "35-54": ["35-44", "45-54"], "55-74": ["55-64", "65-74"], "75+": ["75+"]}; INV = {b: g for g, bs in G.items() for b in bs}
CLUSTER = ["nivel", "brecha_genero_18_54", "brecha_joven"]
DESCRIBE = ["nivel_abs", "caida_75", "brecha_genero_55mas", "intermitencia", "tendencia"]
M = 30.0  # pseudo-observaciones del encogimiento hacia la tasa nacional del subconjunto
NOMBRES = {0: "Baja participación del norte urbano", 1: "Rezago juvenil urbano", 2: "Rural con brecha masculina", 3: "Urbano de participación media-alta", 4: "Alta participación comunitaria"}

def load():
    s = pd.read_parquet("data/processed/perfiles_seccion.parquet"); s["gedad"] = s.banda.map(INV); return s

def features(s, years, pres, mid, trend=(None, None), min_n=800, m=None):
    """years: elecciones de la ventana; pres/mid: subconjuntos para la intermitencia; trend=(a, b): tasa(b) − tasa(a). Solo secciones presentes en todas las elecciones."""
    s = s[s.AELEC.isin(years)]; mm = M if m is None else m
    def sub(ys, sex=None, ged=None):
        d = s[s.AELEC.isin(ys)]; d = d if sex is None else d[d.SEXO == sex]; d = d if ged is None else d[d.gedad.isin(ged)]
        g = d.groupby("sid")[["SV", "NV"]].sum(); p0 = g.SV.sum() / (g.SV.sum() + g.NV.sum()); g["r"] = (g.SV + mm * p0) / (g.SV + g.NV + mm); g["n"] = g.SV + g.NV; g["p0"] = p0; return g
    ok = s.groupby("sid").AELEC.nunique(); ok = ok[ok == len(years)].index; F = pd.DataFrame(index=ok); a = sub(years)
    F["nivel"] = sum(sub([y]).pipe(lambda g: g.r - g.p0).reindex(ok) for y in years) / len(years)   # relativo al nivel nacional de cada elección
    F["nivel_abs"] = a.r.reindex(ok); F["n_total"] = a.n.reindex(ok)
    F["brecha_joven"] = (sub(years, ged=["18-34"]).r - sub(years, ged=["55-74"]).r).reindex(ok)
    F["brecha_genero_18_54"] = (sub(years, 1, ["18-34", "35-54"]).r - sub(years, 0, ["18-34", "35-54"]).r).reindex(ok)
    F["brecha_genero_55mas"] = (sub(years, 1, ["55-74", "75+"]).r - sub(years, 0, ["55-74", "75+"]).r).reindex(ok)
    F["caida_75"] = (sub(years, ged=["75+"]).r - sub(years, ged=["55-74"]).r).reindex(ok)
    F["intermitencia"] = (sub(pres).r - sub(mid).r).reindex(ok)
    F["tendencia"] = (sub([trend[1]]).r - sub([trend[0]]).r).reindex(ok) if trend[0] else np.nan
    return F[F.n_total >= min_n].dropna(subset=[c for c in F.columns if c != "tendencia"] if trend[0] is None else None)
