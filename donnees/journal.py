"""Journal d'activité (table evenements) : connexions, recherches, fiches ouvertes, actions de l'admin.

Utilise     : donnees (base)
Utilisé par : donnees (membres, reglages), etat (actions), vues (explorer, fiche),
              vues/admin (connexion, onglet_avatars, onglet_journal, onglet_membres, onglet_reglages)
"""
from __future__ import annotations

import json

from donnees.base import connexion, maintenant


def journaliser(uid, type_: str, detail=None) -> None:
    """Ajoute un événement au journal d'activité (détail converti en JSON si besoin)."""
    if isinstance(detail, (dict, list)):
        detail = json.dumps(detail, ensure_ascii=False)
    with connexion() as con:
        con.execute("INSERT INTO evenements(utilisateur_id, type, detail, date) VALUES(?,?,?,?)",
                    (uid, type_, detail, maintenant()))
