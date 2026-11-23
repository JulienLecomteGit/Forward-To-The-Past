"""Petits calculs numériques réutilisés par le moteur et les données de démo.

Utilise     : —
Utilisé par : demo (generation), donnees (catalogue), moteur (recommandation)
"""
import math

import numpy as np
import pandas as pd


def proximite(valeurs, ref, ecart_max) -> np.ndarray:
    """1 quand la valeur égale la référence, puis décroît jusqu'à 0 à « ecart_max » d'écart (NaN → 0)."""
    if ref is None or (isinstance(ref, float) and math.isnan(ref)):
        return np.zeros(len(valeurs))
    return np.nan_to_num(np.maximum(0, 1 - np.abs(valeurs - ref) / max(ecart_max, 1e-9)), nan=0.0)


def ramener_entre_0_et_1(x: np.ndarray, exclure=None) -> np.ndarray:
    """Divise par le maximum (le meilleur vaut 1) ; « exclure » met d'abord ces positions à 0."""
    x = np.asarray(x, dtype=float).copy()
    if exclure is not None:
        x[exclure] = 0
    m = x.max() if len(x) else 0
    return x / m if m > 0 else x


def rang_percentile(x: np.ndarray) -> np.ndarray:
    """Rang de chaque valeur entre 0 et 1 (1 = la plus grande), ex-aequo au rang moyen."""
    return pd.Series(x).rank(pct=True, method="average").fillna(0).to_numpy()
