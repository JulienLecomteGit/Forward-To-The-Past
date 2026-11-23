"""Espace admin › chargement des données de la base en tableaux (membres, avis, journal, préférences, séances)
et filtre « membres réels seulement ».

Utilise     : donnees (base, interactions)
Utilisé par : vues (admin), vues/admin (onglet_vue_ensemble)
"""
from __future__ import annotations

import pandas as pd

from donnees import base, interactions


def charger() -> dict:
    """Lit en une fois tout ce qu'affichent les onglets : membres, interactions, événements, préférences, séances."""
    m = pd.DataFrame(base.requete("SELECT id, email, prenom, nom, pseudo, avatar, tranche_age, ville, newsletter, "
                                 "date_inscription, derniere_connexion, est_fictif FROM utilisateurs"))
    i = pd.DataFrame(interactions.toutes_interactions(), columns=["uid", "tconst", "type", "valeur", "date"])
    e = pd.DataFrame(base.requete("SELECT id, utilisateur_id AS uid, type, detail, date FROM evenements"))
    p = pd.DataFrame(base.requete("SELECT * FROM preferences"))
    sea = pd.DataFrame(base.requete("SELECT utilisateur_id AS uid, tconst, date_seance, lieu, note FROM seances"),
                       columns=["uid", "tconst", "date_seance", "lieu", "note"])
    for df, col in ((m, "date_inscription"), (m, "derniere_connexion"), (i, "date"), (e, "date")):
        if len(df):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return {"membres": m, "inter": i, "evts": e, "prefs": p, "seances": sea}


def filtrer(d, fictifs: bool) -> dict:
    """Mêmes données limitées aux membres réels (sauf si les fictifs sont inclus)."""
    if fictifs or not len(d["membres"]):
        return d
    reels = set(d["membres"].loc[d["membres"].est_fictif == 0, "id"])
    return {"membres": d["membres"][d["membres"].id.isin(reels)], "inter": d["inter"][d["inter"].uid.isin(reels)],
            "evts": d["evts"][d["evts"].uid.isin(reels)], "prefs": d["prefs"][d["prefs"].utilisateur_id.isin(reels)],
            "seances": d["seances"][d["seances"].uid.isin(reels)]}
