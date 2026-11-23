"""Classement final d'une recommandation : pertinence, diversité (méthode MMR : pas 10 films quasi identiques),
calibrage sur les proportions de goûts du membre, et règle « un autre volet de la saga ».

Utilise     : donnees (catalogue)
Utilisé par : moteur (recommandation)
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from donnees.catalogue import Catalogue


def _ressemblance_entre(cat: Catalogue, cand: np.ndarray, k: int) -> np.ndarray:
    """Ressemblance entre propositions (pour la diversité) : genre + résumé + saga."""
    meme_genre = (cat.genre_code[cand] == cat.genre_code[k]).astype(float)
    resume = np.asarray((cat.tfidf[cand] @ cat.tfidf[k].T).todense()).ravel()
    saga = (cat.saga[cand] == cat.saga[k]) & (cat.saga[k] != "")
    return np.clip(0.5 * meme_genre + 1.5 * resume + 0.5 * saga, 0, 1)


def selectionner(cat: Catalogue, score: np.ndarray, p: dict, exclure=(), source=None, n=None, filtre=None,
               cible: dict | None = None) -> list[int]:
    """Classement final : pertinence, diversité (MMR) et, en mode membre, calibrage sur les proportions de goûts."""
    n = int(n or p["nb_reco"])
    s = _scores_admissibles(cat, score, p, exclure, source, filtre)
    ordre = np.argsort(-np.round(s, 9), kind="stable")
    valides = ordre[np.isfinite(s[ordre])]
    kappa = 0.12 * float(p.get("calibrage", 0)) if cible else 0.0
    cand = _candidats(cat, valides, n, kappa, cible)
    if not len(cand):
        return []
    choisis = _choix_diversifie(cat, s, cand, n, p, kappa, cible)
    _regle_saga(cat, p, s, ordre, source, choisis)
    return choisis


def _scores_admissibles(cat: Catalogue, score, p: dict, exclure, source, filtre):
    """Copie des scores où les films interdits valent −∞ : film source, exclus, sous la note minimale, hors filtre."""
    s = score.astype(float).copy()
    if source is not None:
        s[source] = -np.inf
    if len(exclure):
        s[list(exclure)] = -np.inf
    if p.get("note_min", 0) > 0:
        s[~(np.nan_to_num(cat.note, nan=0) >= p["note_min"])] = -np.inf
    if filtre is not None:
        s[~filtre] = -np.inf
    return s


def _candidats(cat: Catalogue, valides, n: int, kappa: float, cible):
    """Les meilleurs films admissibles (au moins 200), complétés si besoin par 40 films de chaque genre visé."""
    cand = valides[: max(200, n * 20)]
    if kappa > 0:  # chaque genre visé doit avoir des candidats, même s'il n'est pas dans le haut du classement
        extra = [valides[cat.genre_code[valides] == g][:40] for g in cible]
        cand = np.array(list(dict.fromkeys(np.concatenate([cand, *extra]).tolist())), dtype=int)
    return cand


def _choix_diversifie(cat: Catalogue, s, cand, n: int, p: dict, kappa: float, cible) -> list[int]:
    """Choisit les films un par un (MMR) : pertinent, mais différent de ceux déjà choisis, et, si calibrage,
    en favorisant les genres encore sous-représentés par rapport aux goûts du membre."""
    lam = 1 - 0.07 * float(p.get("diversite", 0))  # 0 → pure pertinence ; 10 → forte diversité
    rel = s[cand]
    rel = (rel - rel.min()) / (rel.max() - rel.min()) if rel.max() > rel.min() else np.ones(len(cand))
    choisis, deja = [], np.zeros(len(cand))
    pris = np.zeros(len(cand), bool)
    gc = cat.genre_code[cand]
    part_visee = np.array([cible.get(int(g), 0.0) for g in gc]) if kappa > 0 else None
    compte = defaultdict(int)
    for t in range(min(n, len(cand))):
        mmr = lam * rel - (1 - lam) * deja
        if kappa > 0:  # bonus aux genres encore « sous-représentés » par rapport aux goûts du membre
            deficit = part_visee * (t + 1) - np.array([compte[int(g)] for g in gc])
            mmr = mmr + kappa * np.clip(deficit, 0, 1)
        mmr[pris] = -np.inf
        k = int(np.argmax(mmr))
        pris[k] = True
        choisis.append(int(cand[k]))
        compte[int(gc[k])] += 1
        if lam < 1:
            deja = np.maximum(deja, _ressemblance_entre(cat, cand, cand[k]))
    return choisis


def _regle_saga(cat: Catalogue, p: dict, s, ordre, source, choisis: list) -> None:
    """Règle saga (héritée du moteur 1A) : garantir un autre volet si la saga est absente (remplace le dernier choix)."""
    if source is not None and p.get("saga", True) and cat.saga[source]:
        if not any(cat.saga[j] == cat.saga[source] for j in choisis):
            membres = [j for j in ordre if cat.saga[j] == cat.saga[source] and np.isfinite(s[j])]
            if membres:
                choisis[-1] = int(membres[0])
