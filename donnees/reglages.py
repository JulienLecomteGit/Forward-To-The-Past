"""Réglages du moteur enregistrés par l'admin (table parametres) : lecture, écriture, date de modification.

Utilise     : donnees (base, journal)
Utilisé par : etat (cache), vues/admin (onglet_reglages)
"""
from __future__ import annotations

import json

from donnees.base import connexion, maintenant
from donnees.journal import journaliser


def lire_parametres(defaut: dict) -> dict:
    """Réglages du moteur enregistrés par l'admin, complétés par les valeurs par défaut."""
    with connexion() as con:
        r = con.execute("SELECT valeur FROM parametres WHERE cle = 'moteur'").fetchone()
    p = dict(defaut)
    if r:
        p.update({k: v for k, v in json.loads(r["valeur"]).items() if k in defaut})
    return p


def ecrire_parametres(p: dict) -> None:
    """Enregistre les réglages du moteur et le note au journal."""
    with connexion() as con:
        con.execute("INSERT INTO parametres(cle, valeur, maj) VALUES('moteur', ?, ?) ON CONFLICT(cle)"
                    " DO UPDATE SET valeur=excluded.valeur, maj=excluded.maj", (json.dumps(p), maintenant()))
    journaliser(None, "admin_reglages", p)


def date_parametres() -> str | None:
    """Date du dernier enregistrement des réglages, ou None."""
    with connexion() as con:
        r = con.execute("SELECT maj FROM parametres WHERE cle = 'moteur'").fetchone()
    return r["maj"] if r else None
