"""Navigation entre les écrans (mémorisée dans la session) : aller à une page, ouvrir une fiche film, revenir, se déconnecter.

Utilise     : —
Utilisé par : app, interface (cartes), vues (explorer, fiche, machine, mes_films, profil), vues/admin (connexion)
"""
from __future__ import annotations

import streamlit as st


def ouvrir_fiche(tconst: str, origine: str) -> None:
    """Ouvre la fiche d'un film en retenant la page d'où l'on vient (pour « Retour »)."""
    ss = st.session_state
    if ss.get("page") != "fiche":
        ss["page_avant"] = ss.get("page", "accueil")
    ss["fiche"], ss["fiche_origine"], ss["page"] = tconst, origine, "fiche"


def aller(page: str) -> None:
    """Change de page et ferme la fiche ouverte."""
    st.session_state["page"] = page
    st.session_state.pop("fiche", None)


def retour() -> None:
    """Bouton « ← Retour » de la fiche film : revient à la page d'où elle a été ouverte."""
    ss = st.session_state
    ss["page"] = ss.pop("page_avant", "accueil")
    ss.pop("fiche", None)


def deconnecter() -> None:
    """Oublie le membre et les étapes en cours, puis revient à l'accueil."""
    for k in ("uid", "fiche", "fiche_origine", "page_avant", "inscription", "roue", "dest_annee"):
        st.session_state.pop(k, None)
    st.session_state["page"] = "accueil"
