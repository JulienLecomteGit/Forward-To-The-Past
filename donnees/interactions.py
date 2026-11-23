"""Avis des membres (table interactions) : ❤️ j'aime, 🤮 pas pour moi, ➕ à voir, déjà vu, notes.

Utilise     : config (donnees), donnees (base)
Utilisé par : etat (actions, cache, contexte), vues (accueil, profil),
              vues/admin (chargement, onglet_membres, onglet_qualite, onglet_reglages, simulation)
"""
from __future__ import annotations

from config.donnees import TYPES_INTERACTION
from donnees.base import connexion, maintenant


def interactions(uid: int) -> dict:
    """{type: {tconst: valeur}} pour un membre."""
    res = {t: {} for t in TYPES_INTERACTION}
    dates = {}  # date de la dernière action sur chaque film (sert à donner plus de poids aux actions récentes)
    with connexion() as con:
        for r in con.execute("SELECT tconst, type, valeur, date FROM interactions WHERE utilisateur_id = ? ORDER BY date",
                             (uid,)):
            res[r["type"]][r["tconst"]] = r["valeur"]
            dates[r["tconst"]] = r["date"]
    res["_dates"] = dates
    return res


def basculer(uid: int, tconst: str, type_: str, source: str = "") -> bool:
    """Active/désactive une interaction. Retourne True si elle est maintenant active."""
    with connexion() as con:
        existe = con.execute("SELECT id FROM interactions WHERE utilisateur_id=? AND tconst=? AND type=?",
                             (uid, tconst, type_)).fetchone()
        if existe:
            con.execute("DELETE FROM interactions WHERE id = ?", (existe["id"],))
            return False
        con.execute("INSERT INTO interactions(utilisateur_id, tconst, type, valeur, source, date) VALUES(?,?,?,?,?,?)",
                    (uid, tconst, type_, None, source, maintenant()))
        # J'aime et Pas pour moi s'excluent ; aimer ou noter implique « vu ».
        oppose = {"like": "dislike", "dislike": "like"}.get(type_)
        if oppose:
            con.execute("DELETE FROM interactions WHERE utilisateur_id=? AND tconst=? AND type=?", (uid, tconst, oppose))
        if type_ in ("like", "dislike"):
            con.execute("DELETE FROM interactions WHERE utilisateur_id=? AND tconst=? AND type='liste'", (uid, tconst))
        return True


def noter(uid: int, tconst: str, note: float | None, source: str = "") -> None:
    """Enregistre, remplace ou efface (note=None) la note d'un membre pour un film."""
    with connexion() as con:
        if note is None:
            con.execute("DELETE FROM interactions WHERE utilisateur_id=? AND tconst=? AND type='note'", (uid, tconst))
            return
        con.execute("INSERT INTO interactions(utilisateur_id, tconst, type, valeur, source, date) VALUES(?,?,?,?,?,?)"
                    " ON CONFLICT(utilisateur_id, tconst, type) DO UPDATE SET valeur=excluded.valeur, date=excluded.date",
                    (uid, tconst, "note", float(note), source, maintenant()))
        con.execute("INSERT OR IGNORE INTO interactions(utilisateur_id, tconst, type, valeur, source, date)"
                    " VALUES(?,?,?,?,?,?)", (uid, tconst, "vu", None, source, maintenant()))


def toutes_interactions():
    """Toutes les interactions (pour le filtrage collaboratif et les stats admin)."""
    with connexion() as con:
        return [tuple(r) for r in con.execute("SELECT utilisateur_id, tconst, type, valeur, date FROM interactions")]


def version_communaute() -> str:
    """Empreinte légère qui change dès qu'une interaction est ajoutée ou retirée (clé de cache)."""
    with connexion() as con:
        r = con.execute("SELECT COUNT(*), COALESCE(MAX(id), 0) FROM interactions").fetchone()
    return f"{r[0]}-{r[1]}"
