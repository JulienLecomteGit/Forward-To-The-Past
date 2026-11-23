"""Membres (tables utilisateurs et preferences) : inscription, connexion, profil, goûts déclarés, export et suppression RGPD, comptes de démonstration.

Utilise     : donnees (base, journal, securite)
Utilisé par : demo (generation), etat (contexte), vues (accueil, auth, profil),
              vues/admin (onglet_membres, onglet_qualite, onglet_reglages, simulation)
"""
from __future__ import annotations

import json

from donnees.base import connexion, maintenant, requete
from donnees.journal import journaliser
from donnees.securite import hacher, verifier


def creer_membre(email, prenom, nom, pseudo, mdp, avatar, tranche_age, ville, newsletter, preferences,
                 coups_de_coeur=(), est_fictif=False, date=None, mdp_hash=None) -> int:
    """Crée un compte avec ses préférences et ses coups de cœur ; renvoie son identifiant."""
    date = date or maintenant()
    with connexion() as con:
        cur = con.execute(
            "INSERT INTO utilisateurs(email, prenom, nom, pseudo, mdp_hash, avatar, tranche_age, ville, newsletter,"
            " consentement_rgpd, date_inscription, derniere_connexion, est_fictif) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (email.strip().lower(), prenom.strip(), nom.strip(), pseudo.strip() or prenom.strip(),
             mdp_hash or hacher(mdp), avatar, tranche_age, (ville or "").strip(), int(bool(newsletter)),
             date, date, date, int(est_fictif)))
        uid = cur.lastrowid
        ecrire_preferences(con, uid, preferences, date)
        for t in coups_de_coeur:
            con.execute("INSERT OR IGNORE INTO interactions(utilisateur_id, tconst, type, valeur, source, date)"
                        " VALUES(?,?,?,?,?,?)", (uid, t, "like", None, "inscription", date))
        con.execute("INSERT INTO evenements(utilisateur_id, type, detail, date) VALUES(?,?,?,?)",
                    (uid, "inscription", None, date))
    return uid


def email_existe(email: str) -> bool:
    """Vrai si un compte utilise déjà cette adresse (sans tenir compte des majuscules)."""
    with connexion() as con:
        return con.execute("SELECT 1 FROM utilisateurs WHERE email = ?", (email.strip().lower(),)).fetchone() is not None


def authentifier(email: str, mdp: str):
    """Vérifie e-mail + mot de passe ; renvoie l'identifiant du membre ou None."""
    with connexion() as con:
        row = con.execute("SELECT * FROM utilisateurs WHERE email = ?", (email.strip().lower(),)).fetchone()
    if row is None:
        verifier(mdp, hacher("leurre"))  # temps de réponse identique : n'indique pas si l'email existe
        return None
    if not verifier(mdp, row["mdp_hash"]):
        journaliser(row["id"], "connexion_echec")
        return None
    with connexion() as con:
        con.execute("UPDATE utilisateurs SET derniere_connexion = ? WHERE id = ?", (maintenant(), row["id"]))
    journaliser(row["id"], "connexion")
    return row["id"]


def membre(uid: int):
    """Fiche complète d'un membre (dictionnaire), ou None s'il n'existe pas."""
    with connexion() as con:
        row = con.execute("SELECT * FROM utilisateurs WHERE id = ?", (uid,)).fetchone()
    return dict(row) if row else None


def modifier_membre(uid: int, **champs) -> None:
    """Met à jour les champs autorisés du profil (prénom, pseudo, avatar…) ; ignore les autres."""
    autorises = {"prenom", "nom", "pseudo", "avatar", "tranche_age", "ville", "newsletter"}
    champs = {k: v for k, v in champs.items() if k in autorises}
    if not champs:
        return
    with connexion() as con:
        con.execute(f"UPDATE utilisateurs SET {', '.join(k + ' = ?' for k in champs)} WHERE id = ?",
                    (*champs.values(), uid))


def changer_mdp(uid: int, ancien: str, nouveau: str) -> bool:
    """Remplace le mot de passe si l'ancien est correct ; renvoie True si c'est fait."""
    with connexion() as con:
        row = con.execute("SELECT mdp_hash FROM utilisateurs WHERE id = ?", (uid,)).fetchone()
        if not row or not verifier(ancien, row["mdp_hash"]):
            return False
        con.execute("UPDATE utilisateurs SET mdp_hash = ? WHERE id = ?", (hacher(nouveau), uid))
    journaliser(uid, "mdp_modifie")
    return True


def supprimer_membre(uid: int) -> None:
    """Droit à l'effacement (RGPD art. 17) : supprime le membre, ses préférences et interactions."""
    with connexion() as con:
        con.execute("DELETE FROM utilisateurs WHERE id = ?", (uid,))
        con.execute("INSERT INTO evenements(utilisateur_id, type, detail, date) VALUES(NULL, 'suppression_compte', ?, ?)",
                    (f"membre #{uid}", maintenant()))


def export_membre(uid: int) -> dict:
    """Droit d'accès / portabilité (RGPD art. 15 et 20) : toutes les données du membre, hors hash."""
    with connexion() as con:
        m = dict(con.execute("SELECT * FROM utilisateurs WHERE id = ?", (uid,)).fetchone())
        m.pop("mdp_hash", None)
        prefs = preferences(uid, con)
        inter = [dict(r) for r in con.execute(
            "SELECT tconst, type, valeur, source, date FROM interactions WHERE utilisateur_id = ? ORDER BY date", (uid,))]
        evts = [dict(r) for r in con.execute(
            "SELECT type, detail, date FROM evenements WHERE utilisateur_id = ? ORDER BY date", (uid,))]
        sea = [dict(r) for r in con.execute(
            "SELECT tconst, date_seance, lieu, note, avis FROM seances WHERE utilisateur_id = ? ORDER BY date_seance", (uid,))]
    return {"membre": m, "preferences": prefs, "interactions": inter, "carnet_seances": sea, "evenements": evts,
            "export_le": maintenant()}


def ecrire_preferences(con, uid, p, date=None):
    """Écrit (ou remplace) les préférences d'un membre dans une connexion déjà ouverte."""
    con.execute(
        "INSERT INTO preferences(utilisateur_id, genres, decennies, format_duree, origine, style, maj)"
        " VALUES(?,?,?,?,?,?,?) ON CONFLICT(utilisateur_id) DO UPDATE SET genres=excluded.genres,"
        " decennies=excluded.decennies, format_duree=excluded.format_duree, origine=excluded.origine,"
        " style=excluded.style, maj=excluded.maj",
        (uid, json.dumps(list(p.get("genres", [])), ensure_ascii=False), json.dumps(list(p.get("decennies", []))),
         p.get("format_duree", "indifferent"), p.get("origine", "indifferent"), p.get("style", "indifferent"),
         date or maintenant()))


def enregistrer_preferences(uid: int, p: dict) -> None:
    """Enregistre les préférences modifiées depuis le profil et le note au journal."""
    with connexion() as con:
        ecrire_preferences(con, uid, p)
    journaliser(uid, "preferences_modifiees")


def preferences(uid: int, con=None) -> dict:
    """Préférences déclarées d'un membre (valeurs « indifférent » s'il n'en a pas)."""
    def lire(c):
        """Lecture effective, avec la connexion fournie ou une nouvelle."""
        r = c.execute("SELECT * FROM preferences WHERE utilisateur_id = ?", (uid,)).fetchone()
        if not r:
            return {"genres": [], "decennies": [], "format_duree": "indifferent", "origine": "indifferent",
                    "style": "indifferent"}
        return {"genres": json.loads(r["genres"]), "decennies": json.loads(r["decennies"]),
                "format_duree": r["format_duree"], "origine": r["origine"], "style": r["style"]}
    if con is not None:
        return lire(con)
    with connexion() as c:
        return lire(c)


def membres_demo() -> list[dict]:
    """Les 8 comptes de démonstration proposés sur la page d'accueil publique."""
    with connexion() as con:
        return [dict(r) for r in con.execute(
            "SELECT u.id, u.prenom, u.nom, u.pseudo, u.avatar, p.genres FROM utilisateurs u "
            "LEFT JOIN preferences p ON p.utilisateur_id = u.id WHERE u.est_demo = 1 ORDER BY u.id LIMIT 8")]


def connecter_demo(uid: int):
    """Connexion en un clic, réservée aux comptes de démonstration (est_demo = 1)."""
    with connexion() as con:
        r = con.execute("SELECT id FROM utilisateurs WHERE id = ? AND est_demo = 1", (uid,)).fetchone()
        if not r:
            return None
        con.execute("UPDATE utilisateurs SET derniere_connexion = ? WHERE id = ?", (maintenant(), uid))
    journaliser(uid, "connexion_demo")
    return uid


def liste_pour_selection() -> list[dict]:
    """Tous les membres pour les listes déroulantes de l'admin : comptes démo d'abord, puis réels, puis fictifs."""
    return requete("SELECT id, pseudo, prenom FROM utilisateurs ORDER BY est_demo DESC, est_fictif, id")
