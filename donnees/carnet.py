"""Carnet de séance (table seances) : date, lieu, note et avis d'un film vu ; une séance vaut « déjà vu » pour le moteur.

Utilise     : donnees (base)
Utilisé par : etat (actions, contexte)
"""
from __future__ import annotations

from donnees.base import connexion, maintenant


def seances(uid: int) -> dict:
    """{tconst: {date_seance, lieu, note, avis}} du plus récent au plus ancien."""
    with connexion() as con:
        return {r["tconst"]: dict(r) for r in con.execute(
            "SELECT tconst, date_seance, lieu, note, avis FROM seances WHERE utilisateur_id = ? "
            "ORDER BY date_seance DESC, id DESC", (uid,))}


def enregistrer_seance(uid: int, tconst: str, date_seance: str, lieu: str, note: int | None, avis: str) -> None:
    """Ajoute ou met à jour une séance ; elle vaut « vu » et, si notée, une note pour le moteur."""
    with connexion() as con:
        con.execute("INSERT INTO seances(utilisateur_id, tconst, date_seance, lieu, note, avis, date) VALUES(?,?,?,?,?,?,?)"
                    " ON CONFLICT(utilisateur_id, tconst) DO UPDATE SET date_seance=excluded.date_seance, lieu=excluded.lieu,"
                    " note=excluded.note, avis=excluded.avis, date=excluded.date",
                    (uid, tconst, date_seance, lieu, note, (avis or "").strip()[:500], maintenant()))
        con.execute("INSERT OR IGNORE INTO interactions(utilisateur_id, tconst, type, valeur, source, date) VALUES(?,?,?,?,?,?)",
                    (uid, tconst, "vu", None, "carnet", maintenant()))
        if note:
            con.execute("INSERT INTO interactions(utilisateur_id, tconst, type, valeur, source, date) VALUES(?,?,?,?,?,?)"
                        " ON CONFLICT(utilisateur_id, tconst, type) DO UPDATE SET valeur=excluded.valeur, date=excluded.date",
                        (uid, tconst, "note", float(note), "carnet", maintenant()))
        con.execute("DELETE FROM interactions WHERE utilisateur_id=? AND tconst=? AND type='liste'", (uid, tconst))


def retirer_seance(uid: int, tconst: str) -> None:
    """Supprime la séance d'un film et les « vu » / notes ajoutés par le carnet."""
    with connexion() as con:
        con.execute("DELETE FROM seances WHERE utilisateur_id=? AND tconst=?", (uid, tconst))
        con.execute("DELETE FROM interactions WHERE utilisateur_id=? AND tconst=? AND type IN ('vu','note') AND source='carnet'",
                    (uid, tconst))
