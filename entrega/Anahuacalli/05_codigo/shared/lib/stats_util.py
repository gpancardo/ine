"""Bootstrap por clúster (municipio) de RMSE y de diferencias pareadas de RMSE."""
import numpy as np, pandas as pd

def cluster_stats(err2: pd.Series, mun: pd.Series):
    g = pd.DataFrame({"e": err2.values, "m": mun.values}).groupby("m").e.agg(["sum", "count"])
    return g["sum"].values, g["count"].values

def boot_rmse(err2, mun, B=2000, seed=0):
    S, N = cluster_stats(err2, mun); rng = np.random.default_rng(seed); k = len(S)
    w = rng.multinomial(k, np.ones(k) / k, size=B)
    r = np.sqrt((w @ S) / (w @ N)); return float(np.sqrt(S.sum() / N.sum())), np.percentile(r, [2.5, 97.5])

def boot_delta(err2_a, err2_b, mun, B=2000, seed=0):
    """ΔRMSE = RMSE(a) − RMSE(b), pareado; <0 => a mejor. Devuelve (delta, lo, hi, p≈ prop. de réplicas con signo opuesto)."""
    d = pd.DataFrame({"a": err2_a.values, "b": err2_b.values, "m": mun.values}).groupby("m").agg(sa=("a", "sum"), sb=("b", "sum"), n=("a", "count"))
    rng = np.random.default_rng(seed); k = len(d); w = rng.multinomial(k, np.ones(k) / k, size=B)
    n = w @ d.n.values; r = np.sqrt((w @ d.sa.values) / n) - np.sqrt((w @ d.sb.values) / n)
    pt = np.sqrt(d.sa.sum() / d.n.sum()) - np.sqrt(d.sb.sum() / d.n.sum())
    lo, hi = np.percentile(r, [2.5, 97.5]); p = 2 * min((r >= 0).mean(), (r <= 0).mean())
    return float(pt), float(lo), float(hi), float(max(p, 1 / B))
