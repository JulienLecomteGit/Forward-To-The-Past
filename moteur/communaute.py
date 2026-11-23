"""Filtrage collaboratif : matrice membres × films des « j'aime », films aimés par les mêmes membres, membres aux goûts
proches (« jumeaux ciné »), tendances des 30 derniers jours.

Utilise     : donnees (catalogue)
Utilisé par : etat (cache, contexte), moteur (evaluation, recommandation), vues/admin (simulation)
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
from scipy import sparse

from donnees.catalogue import Catalogue


class Communaute:
    """Matrice membres × films des « j'aime » (j'aime + notes ≥ 4)."""

    def __init__(self, cat: Catalogue, lignes):
        """Construit la matrice membres × films aimés et la liste des j'aime datés."""
        positifs = defaultdict(set)
        self.dates = []
        for uid, tconst, type_, valeur, date in lignes:
            j = cat.position.get(tconst)
            if j is None:
                continue
            if type_ == "like" or (type_ == "note" and (valeur or 0) >= 4):
                positifs[uid].add(j)
                self.dates.append((j, date))
        self.uids = sorted(positifs)
        self.ligne = {u: r for r, u in enumerate(self.uids)}
        rows = [self.ligne[u] for u in self.uids for _ in positifs[u]]
        cols = [j for u in self.uids for j in positifs[u]]
        self.U = sparse.csr_matrix((np.ones(len(rows), np.float32), (rows, cols)), shape=(len(self.uids), cat.n))
        self.UT = self.U.T.tocsr()
        self.nb_film = np.asarray(self.U.sum(axis=0)).ravel()
        self.nb_user = np.asarray(self.U.sum(axis=1)).ravel()
        self.n = cat.n

    def item(self, i: int) -> np.ndarray:
        """Cosinus entre films sur les membres qui les aiment."""
        if not len(self.uids) or self.nb_film[i] == 0:
            return np.zeros(self.n)
        co = np.asarray((self.UT @ self.UT[i].T).todense()).ravel()
        co[i] = 0
        return co / np.sqrt(np.maximum(self.nb_film * self.nb_film[i], 1))

    def membre(self, aimes, exclure_uid=None, k: int = 25, poids=None) -> tuple[np.ndarray, list[tuple[int, float]]]:
        """Score des films via les k membres les plus proches (cosinus sur les j'aime, récents pondérés plus fort)."""
        if not len(self.uids) or not len(aimes):
            return np.zeros(self.n), []
        v = np.zeros(self.n, np.float32)
        v[list(aimes)] = 1 if poids is None else np.asarray(poids, np.float32)
        sims = self.U @ v / (np.sqrt(np.maximum(self.nb_user, 1)) * max(float(np.sqrt((v ** 2).sum())), 1e-9))
        if exclure_uid in self.ligne:
            sims[self.ligne[exclure_uid]] = 0
        voisins = np.argsort(-sims)[:k]
        voisins = voisins[sims[voisins] > 0]
        if not len(voisins):
            return np.zeros(self.n), []
        score = np.asarray(self.U[voisins].T @ sims[voisins]).ravel()
        return score, [(self.uids[r], float(sims[r])) for r in voisins]

    def tendances(self, jours: int = 30) -> np.ndarray:
        """Nombre de j'aime reçus par chaque film sur les `jours` derniers jours."""
        limite = (datetime.now() - timedelta(days=jours)).strftime("%Y-%m-%d")
        compte = np.zeros(self.n)
        for j, d in self.dates:
            if d >= limite:
                compte[j] += 1
        return compte
