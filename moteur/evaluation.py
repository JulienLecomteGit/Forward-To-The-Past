"""Évaluation hors-ligne du moteur (onglet admin « Qualité du moteur ») : on cache 20 % des films aimés de chaque membre
et on mesure si le moteur les retrouve, comparé à « les plus populaires » et « au hasard ».

Utilise     : donnees (catalogue), moteur (communaute, profil_membre, recommandation)
Utilisé par : vues/admin (onglet_qualite)
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd

from donnees.catalogue import Catalogue
from moteur.communaute import Communaute
from moteur.profil_membre import profil_membre
from moteur.recommandation import pour_toi

_METHODES = ("Moteur (réglages testés)", "Les plus populaires", "Au hasard")


def evaluer(cat: Catalogue, lignes, prefs_par_membre: dict, p: dict, k: int = 10, part: float = 0.2,
            nb_max: int = 80, graine: int = 42, details: bool = False):
    """Cache 20 % des films aimés de chaque membre et mesure si le moteur les retrouve dans son top k.

    Comparaison avec deux références naïves : « les plus populaires » et « au hasard ».
    """
    rng = np.random.default_rng(graine)
    comm = Communaute(cat, lignes)
    par_membre = _interactions_par_membre(lignes)
    candidats = _membres_testes(par_membre, prefs_par_membre, nb_max, rng)
    bilan = _Bilan()
    ordre_pop = np.argsort(-cat.entrees, kind="stable")
    exemples = []
    q = dict(p, masquer_vus=True)
    for uid in candidats:
        caches, pr = _cacher_une_partie(cat, par_membre[uid], prefs_par_membre[uid], uid, part, rng)
        if not caches:  # aucun film caché n'est encore dans le catalogue : membre ignoré (évite une division par zéro)
            continue
        connus = set(pr.aimes) | set(pr.detestes) | pr.vus | pr.liste
        reco = pour_toi(cat, pr, q, comm, n=k).indices
        if details:
            exemples.append({"uid": uid, "caches": sorted(caches), "reco": reco, "aimes": pr.aimes[-8:]})
        populaires = [int(j) for j in ordre_pop if j not in connus][:k]
        pool = np.setdiff1d(np.arange(cat.n), list(connus))
        hasard = rng.choice(pool, k, replace=False).tolist()
        for nom, liste in zip(_METHODES, (reco, populaires, hasard)):
            bilan.ajouter(cat, nom, liste, caches, k)
    res = bilan.tableau(cat, k)
    return (res, exemples) if details else res


def _interactions_par_membre(lignes) -> dict:
    """{membre: {type: {tconst: valeur}, "_dates": {tconst: date la plus récente}}}."""
    par_membre = defaultdict(lambda: defaultdict(dict))
    for uid, t, typ, val, date in lignes:
        par_membre[uid][typ][t] = val
        par_membre[uid]["_dates"][t] = max(date or "", par_membre[uid]["_dates"].get(t, ""))
    return par_membre


def _membres_testes(par_membre: dict, prefs_par_membre: dict, nb_max: int, rng) -> list:
    """Membres avec au moins 8 j'aime, tirés au hasard s'ils sont plus de nb_max."""
    candidats = [u for u in sorted(par_membre)
                 if u in prefs_par_membre and len(par_membre[u]["like"]) >= 8]
    if len(candidats) > nb_max:
        candidats = sorted(rng.choice(candidats, nb_max, replace=False).tolist())
    return candidats


def _cacher_une_partie(cat: Catalogue, interactions: dict, prefs: dict, uid, part: float, rng) -> tuple:
    """Retire au hasard une part des j'aime (et leurs vus / notes / liste) ; renvoie (films cachés, profil sans eux)."""
    inter = {typ: dict(v) for typ, v in interactions.items()}
    likes = list(inter.get("like", {}))
    rng.shuffle(likes)
    nb_cache = max(1, int(round(len(likes) * part)))
    caches = {cat.position[t] for t in likes[:nb_cache] if t in cat.position}
    inter["like"] = {t: None for t in likes[nb_cache:]}
    for t in likes[:nb_cache]:
        for typ in ("vu", "note", "liste"):
            inter.get(typ, {}).pop(t, None)
    return caches, profil_membre(cat, prefs, inter, uid)


class _Bilan:
    """Accumule, méthode par méthode, les mesures de chaque membre testé puis les résume en tableau."""

    def __init__(self):
        """Mesures vides pour chaque méthode comparée."""
        self.mesures = {m: [] for m in _METHODES}
        self.vus_reco = {m: set() for m in _METHODES}
        self.genres_reco = {m: [] for m in _METHODES}
        self.pop_reco = {m: [] for m in _METHODES}

    def ajouter(self, cat: Catalogue, nom: str, liste: list, caches: set, k: int) -> None:
        """Note la sélection d'une méthode pour un membre : films retrouvés, diversité, popularité."""
        touches = len(set(liste) & caches)
        self.mesures[nom].append((touches > 0, touches / k, touches / len(caches)))
        self.vus_reco[nom] |= set(liste)
        self.genres_reco[nom].append(len({cat.genre_code[j] for j in liste}))
        self.pop_reco[nom].append(float(np.mean(cat.pop[liste])) if liste else 0)

    def tableau(self, cat: Catalogue, k: int) -> pd.DataFrame:
        """Tableau final : une ligne par méthode (réussite, précision, rappel, couverture…)."""
        lignes_res = []
        for nom, m in self.mesures.items():
            if not m:
                continue
            a = np.array(m, dtype=float)
            lignes_res.append({
                "Méthode": nom,
                "Membres testés": len(m),
                f"Taux de réussite @{k}": a[:, 0].mean(),
                f"Précision @{k}": a[:, 1].mean(),
                f"Rappel @{k}": a[:, 2].mean(),
                "Couverture catalogue": len(self.vus_reco[nom]) / cat.n,
                "Genres différents / sélection": float(np.mean(self.genres_reco[nom])),
                "Popularité moyenne (0-1)": float(np.mean(self.pop_reco[nom])),
            })
        return pd.DataFrame(lignes_res)
