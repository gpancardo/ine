"""Tabla de diseño sección × elección objetivo T con rezagos relativos al nivel nacional.
y_rel = abst_T − nat_T.  Features: a1 = T−3, a2 = T−6, a3 = T−9 (también relativos)."""
import numpy as np, pandas as pd
from sklearn.neighbors import NearestNeighbors
import common as c

CENSO = [x for x in c.eceg_features().columns if x != "pobtot"] + ["log_pob"]
GROUPS = {
    "lag":    ["a1", "a2", "d12"],
    "lag3":   ["a3"],
    "hist":   ["mean_prev", "mean_same", "mean_oth", "sd_prev"],
    "age":    ["gap_jm1", "gap_f1"],
    "census": CENSO,
    "space":  ["nb_a1", "nb_a2", "nb_d12", "nb_sd_a1"],
    "mun":    ["mun_a1", "mun_a2", "mun_n"],
    "struct": ["tipo_U", "tipo_R", "log_ln1"],
    "qual":   ["ns1"],
    "gob":    ["gob_T", "gob_1", "gob_2"],
    "sem":    ["P1", "M1", "P2", "M2", "is_mid", "P1_mid", "M1_mid"],
    "state":  ["ent"],
}
CORE = ["lag"]
ALL_NOSTATE = ["lag", "age", "census", "space", "mun", "struct", "qual"]


def cols(groups):
    return [x for g in groups for x in GROUPS[g]]


def build(targets=(2015, 2018, 2021, 2024, 2027), k=8):
    w = c.load_wide(balanced=False)
    geo = c.load_geo()
    sids = geo.index.intersection(w.index)  # solo secciones con polígono (marco 2021)
    w = w.loc[sids]
    cen = np.c_[geo.loc[sids].geometry.centroid.x, geo.loc[sids].geometry.centroid.y]
    nn = NearestNeighbors(n_neighbors=k + 1).fit(cen).kneighbors(cen)[1][:, 1:]
    nat = {y: w[f"abst_{y}"].mean() for y in c.YEARS}

    def rel(y):
        return w[f"abst_{y}"] - nat[y]

    def nbmean(v):
        with np.errstate(all="ignore"):
            m = v[nn]
            return np.nanmean(m, 1), np.nanstd(m, 1)

    def munloo(s):  # media municipal sin la propia sección
        g = s.groupby(w.mun); n = g.transform("count"); t = g.transform("sum")
        return ((t - s.fillna(0)) / (n - s.notna()).replace(0, np.nan)).where(s.notna() | True), n

    out = []
    for T in targets:
        y1, y2, y3 = T - 3, T - 6, T - 9
        d = pd.DataFrame(index=w.index)
        d["T"] = T
        d["y_rel"] = rel(T) if T in c.YEARS else np.nan
        d["nat_T"] = nat.get(T, np.nan)
        d["ln_T"] = w[f"ln_{T}"] if T in c.YEARS else np.nan
        d["a1"], d["a2"] = rel(y1), rel(y2)
        d["a3"] = rel(y3) if y3 in c.YEARS else np.nan
        d["d12"] = d.a1 - d.a2
        ys = [y for y in c.YEARS if y <= y1]
        R = pd.concat({y: rel(y) for y in ys}, axis=1)
        same = [y for y in ys if (y in c.MID) == (T in c.MID)]
        d["mean_prev"], d["sd_prev"] = R.mean(1), R.std(1)
        d["mean_same"] = R[same].mean(1) if same else np.nan
        d["mean_oth"] = R[[y for y in ys if y not in same]].mean(1)
        pres = [y for y in ys if y not in c.MID][::-1]; mid = [y for y in ys if y in c.MID][::-1]  # más reciente primero
        nanc = pd.Series(np.nan, index=w.index)
        d["P1"], d["P2"] = (R[pres[0]] if pres else nanc), (R[pres[1]] if len(pres) > 1 else nanc)
        d["M1"], d["M2"] = (R[mid[0]] if mid else nanc), (R[mid[1]] if len(mid) > 1 else nanc)
        d["is_mid"] = float(T in c.MID); d["P1_mid"] = d.P1 * d.is_mid; d["M1_mid"] = d.M1 * d.is_mid
        d["gap_jm1"] = w[f"j_{y1}"] - w[f"m_{y1}"]
        d["gap_f1"] = w[f"f_{y1}"] - w[f"raw_{y1}"]
        for n_, s in (("a1", d.a1), ("a2", d.a2), ("d12", d.d12)):
            d[f"nb_{n_}"], sd = nbmean(s.values)
            if n_ == "a1":
                d["nb_sd_a1"] = sd
        d["mun_a1"], d["mun_n"] = munloo(d.a1)
        d["mun_a2"], _ = munloo(d.a2)
        for x in CENSO[:-1] + ["pobtot"]:
            d[x] = w[x]
        d["log_pob"] = np.log1p(w.pobtot)
        d["tipo_U"], d["tipo_R"] = (w.TIPOSEC == "U").astype(float), (w.TIPOSEC == "R").astype(float)
        d["log_ln1"] = np.log(w[f"ln_{y1}"])
        d["ns1"] = w[f"ns_{y1}"]
        d["ent"] = w.ent
        from calendar_gob import GOB
        for nm, yy in (("gob_T", T), ("gob_1", y1), ("gob_2", y2)):
            d[nm] = w.ent.isin(GOB[yy]).astype(float)
        d["mun"] = w.mun
        out.append(d)
    D = pd.concat(out)
    D = D[D.a1.notna() & D.a2.notna()]
    return D, nat


if __name__ == "__main__":
    D, nat = build()
    print({y: round(v, 4) for y, v in nat.items()})
    print(D.groupby("T").agg(n=("a1", "size"), y_na=("y_rel", lambda s: s.isna().sum()), na_census=("graproes", lambda s: s.isna().mean())))
    print(D[D["T"] == 2021][["y_rel", "a1", "a2", "nb_a1", "mun_a1"]].corr().round(3))
