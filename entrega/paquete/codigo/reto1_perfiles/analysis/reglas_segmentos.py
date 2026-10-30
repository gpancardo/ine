# /// script
# dependencies = ["pandas", "pyarrow", "numpy", "scikit-learn"]
# ///
"""Reto 1: reglas explícitas que reproducen la segmentación (árbol sustituto sobre las etiquetas de K-means). Permite clasificar cualquier sección o municipio con umbrales en las unidades originales.
Fidelidad medida con validación cruzada por entidad. Run: uv run reto1_perfiles/analysis/reglas_segmentos.py  -> reto1_perfiles/reports/reglas_segmentos.txt"""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.tree import DecisionTreeClassifier, export_text
sys.path.insert(0, str(Path(__file__).parent)); os.chdir(Path(__file__).resolve().parents[2]); import tip_lib as L
T = pd.read_csv("reto1_perfiles/reports/tipologia_secciones.csv"); X = T[L.CLUSTER].values; y = T.c.values; g = T.EDOCVE.values; out = []
for k in (5, 6, 8, 10, 12):
    t = DecisionTreeClassifier(max_leaf_nodes=k, min_samples_leaf=300, random_state=0); pr = cross_val_predict(t, X, y, groups=g, cv=GroupKFold(5)); w = T.ln24.values
    out.append(f"hojas={k:2d}: fidelidad por entidad (validación cruzada) = {(pr == y).mean():.3f} (ponderada por lista nominal {np.average(pr == y, weights=w):.3f})")
print("\n".join(out)); t = DecisionTreeClassifier(max_leaf_nodes=8, min_samples_leaf=300, random_state=0).fit(X, y)
txt = "\n".join(out) + "\n\nReglas (8 hojas; nivel = participación relativa al nivel nacional promedio 2015-2024, en puntos de proporción; brechas = proporciones; class = número de perfil − 1, p. ej. class: 0 es el perfil 1):\n" + export_text(t, feature_names=L.CLUSTER, decimals=3)
open("reto1_perfiles/reports/reglas_segmentos.txt", "w").write(txt); print("\n" + export_text(t, feature_names=L.CLUSTER, decimals=3))
