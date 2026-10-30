"""Crosswalk municipal INE -> INEGI por nombre dentro de cada estado. Salida: data/processed/mun_crosswalk.csv"""
import difflib, re, unicodedata
from pathlib import Path
import pandas as pd

def norm(s):
    s = unicodedata.normalize("NFKD", str(s).lower()).encode("ascii", "ignore").decode()
    s = re.sub(r"\b(de|del|la|las|los|el|y|heroica|villa)\b", " ", s); return re.sub(r"[^a-z0-9]", "", s)

def build():
    p = pd.read_parquet("data/processed/panel.parquet", columns=["AELEC", "EDOCVE", "MPIOCVE", "MPIONOM"])
    ine = p[p.AELEC == 2024].drop_duplicates(["EDOCVE", "MPIOCVE"]).rename(columns={"EDOCVE": "ent", "MPIOCVE": "cve_ine", "MPIONOM": "nom_ine"})
    ine["key"] = ine.ent * 1000 + ine.cve_ine
    c = pd.read_csv("data/raw/coneval/pobreza_mun_2020.csv", encoding="latin-1").rename(columns={"clave_entidad": "ent", "clave_municipio": "cve_inegi", "municipio": "nom_inegi"})[["ent", "cve_inegi", "nom_inegi"]]
    ine["n"], c["n"] = ine.nom_ine.map(norm), c.nom_inegi.map(norm)
    rows, miss = [], []
    for e, g in ine.groupby("ent"):
        pool = c[c.ent == e].set_index("n").cve_inegi.to_dict()
        for _, r in g.iterrows():
            k = r.n if r.n in pool else (difflib.get_close_matches(r.n, pool.keys(), 1, 0.85) or [None])[0]
            if k is None:  # contención de nombre (p. ej. 'sanpedrotlaquepaque' ⊃ 'tlaquepaque'), solo si es única
                cand = [q for q in pool if len(q) >= 5 and (q in r.n or r.n in q)]
                k = cand[0] if len(cand) == 1 else None
            if k is None: miss.append((e, r.cve_ine, r.nom_ine)); continue
            rows.append(dict(mun_ine=int(r.key), mun_inegi=int(pool[k]), nom_ine=r.nom_ine, exacto=r.n == k))
    x = pd.DataFrame(rows); x.to_csv("data/processed/mun_crosswalk.csv", index=False)
    return x, miss

if __name__ == "__main__":
    x, miss = build()
    print(x[x.mun_inegi.duplicated(keep=False)].sort_values("mun_inegi").to_string()); print("emparejados:", len(x), "exactos:", int(x.exacto.sum()), "| duplicados INEGI:", int(x.mun_inegi.duplicated().sum()), "| sin pareja:", len(miss)); print(miss[:15])
