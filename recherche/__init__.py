"""Recherche prédictive (titre, vignette, année) : petit composant HTML/JS sans dépendance.

Le catalogue est exporté une fois en JSON dans static/ (servi par Streamlit) ; le navigateur filtre
ensuite à chaque lettre tapée, sans relancer la page. Python ne reçoit que le choix final :
{"type": "film", "tconst": …} ou {"type": "texte", "q": …}.

Le composant est déclaré ici (module « recherche ») : son nom technique « recherche.fttp_recherche » ne
change pas, le CSS s'appuie dessus. Fichiers : composants/recherche/index.html (HTML/JS), recherche/index.py (index).

Utilise     : config (chemins), recherche (index)
Utilisé par : vues (explorer, machine, mes_films), vues/admin (onglet_reglages)
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from config.chemins import DOSSIER_COMPOSANT_RECHERCHE
from recherche.index import fichier_index

_COMPOSANT = components.declare_component("fttp_recherche", path=str(DOSSIER_COMPOSANT_RECHERCHE))


def champ(cat, cle: str, placeholder: str, mode: str = "film", valeur: str = "", restreindre=None,
          personnes: bool = False, libelle: str = "") -> dict | None:
    """Affiche la barre de recherche ; renvoie le choix de l'utilisateur une seule fois (sinon None).

    mode « film »    : on choisit un film (Entrée = première suggestion) ;
    mode « explorer » : texte libre possible (acteur, réalisateur, mot du titre) + films ;
    mode « liste »    : suggestions limitées aux films de `restreindre`, texte libre = filtre.
    """
    ev = _COMPOSANT(fichier=fichier_index(cat), placeholder=placeholder, mode=mode, valeur=valeur or "",
                    restreindre=list(restreindre) if restreindre is not None else None, personnes=personnes, libelle=libelle,
                    key=cle, default=None)
    ss = st.session_state
    if isinstance(ev, dict) and ev.get("n") != ss.get(f"_rch_{cle}"):
        ss[f"_rch_{cle}"] = ev.get("n")
        return ev
    return None


def premier(cat, texte: str) -> int | None:
    """Position du meilleur film pour ce texte, ou None."""
    trouves = cat.chercher(texte, 1)
    return int(trouves[0]) if trouves else None
