"""Carga y features compartidos. Importar desde los scripts de analysis/."""
from pathlib import Path
import numpy as np, pandas as pd

P = Path(__file__).resolve().parents[2] / "data" / "processed"
YEARS = [2009, 2012, 2015, 2018, 2021, 2024]
MID = {2009, 2015, 2021, 2027}  # elecciones intermedias (2027 = objetivo)
ESTADOS = {1: "AGS", 2: "BC", 3: "BCS", 4: "CAMP", 5: "COAH", 6: "COL", 7: "CHIS", 8: "CHIH", 9: "CDMX", 10: "DGO", 11: "GTO",
           12: "GRO", 13: "HGO", 14: "JAL", 15: "MEX", 16: "MICH", 17: "MOR", 18: "NAY", 19: "NL", 20: "OAX", 21: "PUE", 22: "QRO",
           23: "QROO", 24: "SLP", 25: "SIN", 26: "SON", 27: "TAB", 28: "TAMPS", 29: "TLAX", 30: "VER", 31: "YUC", 32: "ZAC"}


def load_long():
    """Panel sección-año con abstención 'ajustada' = NV/(SV+NV) (excluye NS: cuadernillos sin captura)."""
    p = pd.read_parquet(P / "panel.parquet")
    p["sid"] = p.EDOCVE * 10000 + p.SECCION
    p["abst_raw"] = 1 - p.SV / p.LN
    p["ns_sh"] = p.NS / p.LN
    p["abst"] = p.NV / (p.SV + p.NV).replace(0, np.nan)
    for k in "jam":
        p[f"abst_{k}"] = 1 - p[f"SV_{k}"] / p[f"LN_{k}"].replace(0, np.nan)
    p["abst_f"] = 1 - p.SV_f / p.LN_f.replace(0, np.nan)
    return p


def eceg_features(fname="eceg.parquet"):
    """Razones sociodemográficas por sección (sid) del ECEG indicado (2020 por defecto). '*' (dato suprimido) -> NaN."""
    e = pd.read_parquet(P / fname)
    e.columns = [c.lower() if c.lower() in ("entidad", "seccion") else c for c in e.columns]; e = e.rename(columns={"entidad": "ENTIDAD", "seccion": "SECCION"})
    e.columns = [c.strip() for c in e.columns]
    num = e.drop(columns=[c for c in ("NOM_ENT", "NOM_MUN") if c in e]).apply(pd.to_numeric, errors="coerce")
    num = num.rename(columns={"POB65_MA": "POB65_MAS"})  # ECEG 2010 trunca el nombre
    if "TVIVPARHAB" not in num: num["TVIVPARHAB"] = num.get("VIVPAR_HAB", np.nan)
    for k in ("PCON_DISC",):
        if k not in num: num[k] = np.nan
    r = lambda a, b: num[a] / num[b].replace(0, np.nan)
    f = pd.DataFrame({
        "sid": num.ENTIDAD * 10000 + num.SECCION,
        "pobtot": num.POBTOT,
        "graproes": num.GRAPROES,
        "pct_18_24": r("P_18A24", "P_18YMAS"),
        "pct_65mas": r("POB65_MAS", "POBTOT"),
        "pct_0_14": r("POB0_14", "POBTOT"),
        "pct_analf": r("P15YM_AN", "P_15YMAS"),
        "pct_sin_esc": r("P15YM_SE", "P_15YMAS"),
        "pct_18_24_asiste": r("P18A24A", "P_18A24"),
        "pea": r("PEA", "P_12YMAS"),
        "desocup": r("PDESOCUP", "PEA"),
        "sin_servsalud": r("PSINDER", "POBTOT"),
        "pct_indigena": r("P3YM_HLI", "P_3YMAS"),
        "pct_discap": r("PCON_DISC", "POBTOT"),
        "pct_nac_otra_ent": r("PNACOE", "POBTOT"),
        "pct_soltero": r("P12YM_SOLT", "P_12YMAS"),
        "pct_sin_relig": r("PSIN_RELIG", "POBTOT"),
        "hacinamiento": num.PRO_OCUP_C,
        "pct_piso_tierra": r("VPH_PISODT", "TVIVPARHAB"),
        "pct_internet": r("VPH_INTER", "TVIVPARHAB"),
        "pct_pc": r("VPH_PC", "TVIVPARHAB"),
        "pct_auto": r("VPH_AUTOM", "TVIVPARHAB"),
        "pct_sin_agua": r("VPH_AGUAFV", "TVIVPARHAB"),
        "pct_sin_drenaje": r("VPH_NODREN", "TVIVPARHAB"),
        "pct_deshabitada": r("VIVPAR_DES", "TVIVPAR"),
    })
    return f.drop_duplicates("sid").set_index("sid")


def load_wide(balanced=True):
    """Tabla ancha por sid: abst_<año>, abst_j/a/m_<año>, ln_<año>, ns_<año> + ECEG + estructura.
    balanced=True: solo secciones presentes en las 6 elecciones y con ECEG."""
    p = load_long()
    cols = {"abst": "abst", "abst_raw": "raw", "abst_j": "j", "abst_a": "a", "abst_m": "m", "abst_f": "f", "LN": "ln", "ns_sh": "ns"}
    w = None
    for y in YEARS:
        d = p[p.AELEC == y].set_index("sid")[list(cols)].rename(columns={k: f"{v}_{y}" for k, v in cols.items()})
        w = d if w is None else w.join(d, how="outer")
    meta = p.sort_values("AELEC").groupby("sid").last()[["EDOCVE", "MPIOCVE", "MPIONOM", "TIPOSEC", "DEF"]]  # último año disponible
    w = w.join(meta).join(eceg_features())
    if balanced:
        w = w[w[[f"abst_{y}" for y in YEARS]].notna().all(axis=1) & w.graproes.notna()]
    w["ent"] = (w.index // 10000).astype(int)
    w["mun"] = w.ent * 1000 + w.MPIOCVE.astype(int)
    return w


def load_geo():
    import geopandas as gpd
    g = gpd.read_file(P / "secciones.gpkg")
    g["sid"] = g.ENTIDAD * 10000 + g.SECCION
    return g.drop_duplicates("sid").set_index("sid")
