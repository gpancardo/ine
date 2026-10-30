"""Modelos y evaluación rolling-origin compartidos por benchmark/ablation/rigor."""
import warnings
import numpy as np, pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
import features as F

warnings.filterwarnings("ignore")
FOLDS = {2021: [2018], 2024: [2018, 2021]}  # test T -> targets de entrenamiento (solo pasado). 2015 EXCLUIDA como objetivo: ver reto2_prediccion/reports/DIAGNOSTICO.md
MIN_LN = 100  # secciones con <100 electores: ruido binomial domina (sd ≈ 5 pp)


class Const(BaseEstimator, RegressorMixin):  # predice 0 = "la sección está en la media nacional"
    def fit(self, X, y): return self
    def predict(self, X): return np.zeros(len(X))


class Col(BaseEstimator, RegressorMixin):  # persistencia: devuelve una columna (a1 o a2)
    def __init__(self, col=0): self.col = col
    def fit(self, X, y): return self
    def predict(self, X): return np.asarray(X)[:, self.col]


def lin(m): return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), m)
def lgbm(**k): return LGBMRegressor(**{**dict(n_estimators=150, learning_rate=.05, num_leaves=8, min_child_samples=300, subsample=.8, subsample_freq=1, colsample_bytree=.8, verbose=-1, random_state=0, n_jobs=8), **k})
def rf(): return make_pipeline(SimpleImputer(strategy="median"), RandomForestRegressor(100, min_samples_leaf=20, max_features=.33, random_state=0, n_jobs=8))
def cat(): return CatBoostRegressor(iterations=400, depth=6, learning_rate=.08, verbose=0, random_seed=0, thread_count=8)


def stack():
    base = [("ridge", lin(Ridge(10.0))), ("lgbm", lgbm()), ("rf", rf())]
    return StackingRegressor(base, final_estimator=Ridge(1.0), cv=3, n_jobs=1)  # ponytail: cv=3 aleatorio entre filas; ver rigor.py (fuga intra-municipio)


def get_D():
    D, nat = F.build()
    D = D[~(D["T"].isin([2015, 2018, 2021, 2024]) & (D.ln_T < MIN_LN))]  # filtro de ruido en train y test
    return D, nat


def split(D, test_T, groups, state_cat=False):
    cs = F.cols(groups)
    tr = D[D["T"].isin(FOLDS[test_T]) & D.y_rel.notna()]
    te = D[(D["T"] == test_T) & D.y_rel.notna()]
    return tr[cs], tr.y_rel, te[cs], te.y_rel, te


def score(y, p, w=None):
    e = np.asarray(y) - np.asarray(p)
    out = dict(rmse=float(np.sqrt(np.mean(e ** 2))), mae=float(np.mean(np.abs(e))))
    out["r2"] = float(1 - (e ** 2).sum() / ((y - y.mean()) ** 2).sum())
    if w is not None:  # ponderado por electores (personas, no secciones)
        w = np.asarray(w, float); out["rmse_w"] = float(np.sqrt((w * e ** 2).sum() / w.sum()))
    return out


def run(model, groups, test_T, state_cat=False):
    Xtr, ytr, Xte, yte, te = split(D_GLOBAL, test_T, groups)
    m = model() if callable(model) else model
    m.fit(Xtr.values, ytr.values)
    p = m.predict(Xte.values)
    return score(yte.values, p, te.ln_T.values), p, te


D_GLOBAL = None
def init():
    global D_GLOBAL
    D_GLOBAL, nat = get_D()
    return D_GLOBAL, nat
