"""Profil d'un membre pour le moteur : goûts déclarés à l'inscription + signaux laissés dans l'app (❤️, notes, ➕, 🤮),
avec plus de poids pour les actions récentes ; répartition de ses goûts par genre.

Utilise     : config (reglages_moteur), donnees (catalogue)
Utilisé par : etat (contexte), moteur (evaluation, recommandation), vues (auth, profil),
              vues/admin (onglet_membres, onglet_reglages, simulation)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from config.reglages_moteur import FORCE_REJET
from donnees.catalogue import Catalogue


@dataclass
class Profil:
    """Le membre vu par le moteur : préférences déclarées et signaux laissés dans l'app
    (films désignés par leur position dans le catalogue).
    """
    genres: list = field(default_factory=list)
    decennies: list = field(default_factory=list)
    format_duree: str = "indifferent"
    origine: str = "indifferent"
    style: str = "indifferent"
    aimes: list = field(default_factory=list)       # indices catalogue (j'aime + notes ≥ 4)
    detestes: list = field(default_factory=list)    # pas pour moi + notes ≤ 2
    vus: set = field(default_factory=set)
    liste: set = field(default_factory=set)
    uid: int | None = None
    signaux: list = field(default_factory=list)     # aimés puis « à voir » : tout ce qui dit « j'ai envie de ça »
    force: list = field(default_factory=list)       # 1.5 note 5★, 1 j'aime / 4★, 0.35 « à voir »
    dates: list = field(default_factory=list)       # date de chaque signal (récence)
    dates_neg: list = field(default_factory=list)   # date de chaque « pas pour moi »


def profil_membre(cat: Catalogue, prefs: dict, inter: dict, uid=None) -> Profil:
    """Construit le profil à partir des préférences déclarées et des interactions {type: {tconst: valeur}}."""
    pos = lambda t: cat.position.get(t)  # noqa: E731
    dates = inter.get("_dates", {})
    notes = inter.get("note", {})
    force = _force_des_films_aimes(inter, notes)
    aimes_t = [t for t in force if pos(t) is not None]
    neg_t = list(dict.fromkeys([t for t in inter.get("dislike", {})] + [t for t, v in notes.items() if v and v <= 2]))
    neg_t = [t for t in neg_t if pos(t) is not None and t not in force]
    liste_t = [t for t in inter.get("liste", {}) if pos(t) is not None and t not in force and t not in neg_t]
    vus = {pos(t) for typ in ("vu", "note", "like", "dislike") for t in inter.get(typ, {})}
    return Profil(
        genres=prefs.get("genres", []),
        decennies=[int(d) for d in prefs.get("decennies", [])],
        format_duree=prefs.get("format_duree", "indifferent"),
        origine=prefs.get("origine", "indifferent"),
        style=prefs.get("style", "indifferent"),
        aimes=[pos(t) for t in aimes_t],
        detestes=[pos(t) for t in neg_t],
        vus={j for j in vus if j is not None},
        liste={pos(t) for t in inter.get("liste", {}) if pos(t) is not None},
        uid=uid,
        signaux=[pos(t) for t in aimes_t + liste_t],
        force=[force[t] for t in aimes_t] + [0.35] * len(liste_t),
        dates=[dates.get(t, "") for t in aimes_t + liste_t],
        dates_neg=[dates.get(t, "") for t in neg_t],
    )


def _force_des_films_aimes(inter: dict, notes: dict) -> dict:
    """Film → intensité du signal positif : 1 pour un j'aime ou une note 4★, 1,5 pour une note 5★."""
    force = {}
    for t in inter.get("like", {}):
        force[t] = max(force.get(t, 0), 1.0)
    for t, v in notes.items():
        if (v or 0) >= 4:
            force[t] = max(force.get(t, 0), 1.5 if v >= 5 else 1.0)
    return force


def poids_recence(dates: list, recence: float) -> np.ndarray:
    """Poids 1 pour l'action la plus récente, divisé par 2 toutes les « 40 / réactivité » actions (0 = pas d'effet)."""
    n = len(dates)
    if not n:
        return np.zeros(0)
    if recence <= 0:
        return np.ones(n)
    ordre = sorted(range(n), key=lambda k: (dates[k] or "", k), reverse=True)  # du plus récent au plus ancien
    rang = np.empty(n)
    rang[ordre] = np.arange(n)
    return 0.5 ** (rang / (40.0 / recence))


def gouts(cat: Catalogue, pr: Profil, p: dict) -> np.ndarray:
    """Répartition des goûts du membre par genre (somme = 1) : déclarés + signaux récents − « pas pour moi »."""
    G = len(cat.genres)
    decl = np.zeros(G)
    for g in pr.genres:
        if g in cat.genres:
            decl[cat.genres.index(g)] = 1
    decl = decl / decl.sum() if decl.sum() else decl
    rec = float(p.get("recence", 0))
    sig = np.array(pr.signaux, dtype=int)
    if not len(sig):
        return decl
    w = np.asarray(pr.force, float) * poids_recence(pr.dates, rec)
    gc = cat.genre_code[sig]
    hist = np.bincount(gc[gc >= 0], weights=w[gc >= 0], minlength=G)
    neg = np.array(pr.detestes, dtype=int)
    if len(neg):
        wn = poids_recence(pr.dates_neg, rec)
        gn = cat.genre_code[neg]
        hist = np.maximum(hist - FORCE_REJET * np.bincount(gn[gn >= 0], weights=wn[gn >= 0], minlength=G), 0)
    hist = hist / hist.sum() if hist.sum() else hist
    wd, wh = float(p["declare"]), float(p["historique"])
    if not decl.sum():
        wd = 0.0
    t = (wd * decl + wh * hist) / ((wd + wh) or 1.0)
    return t / t.sum() if t.sum() else t
