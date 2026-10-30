# /// script
# dependencies = ["pandas", "pyarrow", "numpy"]
# ///
"""Descomposición SVD de la matriz municipio × elección (abstención relativa al nivel nacional, 1994-2024), a la Moscú 2012-18. Run: uv run analysis/matrix_svd.py"""
import os
from pathlib import Path
import numpy as np, pandas as pd
os.chdir(Path(__file__).resolve().parents[2])
L = pd.read_parquet("data/processed/long_magar.parquet"); L = L[(L.year >= 1994) & (L.lisnom >= 100)]
pn = pd.read_parquet("data/processed/panel.parquet", columns=["EDOCVE", "SECCION", "MPIOCVE"]).drop_duplicates(["EDOCVE", "SECCION"]); pn["sid"] = pn.EDOCVE * 10000 + pn.SECCION; pn["ife"] = pn.EDOCVE * 1000 + pn.MPIOCVE
L = L.merge(pn[["sid", "ife"]], on="sid"); g = L.groupby(["ife", "year"]).apply(lambda d: 1 - d.tot.sum() / d.lisnom.sum()).unstack("year").dropna()
M = g.sub(g.mean(0), axis=1)  # relativo al nivel medio de cada elección
print(f"municipios con las {M.shape[1]} elecciones: {M.shape[0]}")
mu = M.mean(1); Mc = M.sub(mu, axis=0)  # quita nivel municipal
U, s, Vt = np.linalg.svd(M.values, full_matrices=False); ev = s ** 2 / (s ** 2).sum()
print("Varianza explicada (matriz con nivel municipal):", np.round(ev[:5], 3)); U2, s2, Vt2 = np.linalg.svd(Mc.values, full_matrices=False); ev2 = s2 ** 2 / (s2 ** 2).sum()
print("Varianza explicada (quitado el nivel municipal):", np.round(ev2[:5], 3))
yrs = list(M.columns); MID = {1997, 2003, 2009, 2015, 2021}
V = pd.DataFrame(Vt2[:4].T, index=yrs, columns=["PC1", "PC2", "PC3", "PC4"]).assign(tipo=["I" if y in MID else "P" for y in yrs]); print("\nCargas por elección (sin nivel municipal):\n", V.round(2).to_string())
for k in (1, 2, 3):  # residuo tras k componentes: ¿queda estructura entre elecciones consecutivas?
    R = Mc.values - (U2[:, :k] * s2[:k]) @ Vt2[:k]; C = np.corrcoef(R.T); print(f"rango {k}: var. residual {1 - ev2[:k].sum():.3f}; corr media residual entre elecciones consecutivas {np.mean([C[i, i+1] for i in range(len(yrs)-1)]):.2f}")
