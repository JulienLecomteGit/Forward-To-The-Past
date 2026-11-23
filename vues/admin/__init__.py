"""Espace admin (accès par code) : statistiques des membres, réglages vulgarisés du moteur, qualité,
avatars, journal & base. Ce fichier aiguille vers un fichier par onglet.

Fichiers : connexion · chargement · onglet_vue_ensemble · onglet_membres · onglet_reglages (+ comparaison) ·
onglet_qualite (+ simulation) · onglet_avatars · onglet_journal

Utilise     : vues/admin (chargement, connexion, onglet_avatars, onglet_journal, onglet_membres, onglet_qualite,
              onglet_reglages, onglet_vue_ensemble)
Utilisé par : app
"""
from __future__ import annotations

import streamlit as st

from vues.admin import (
    chargement,
    connexion,
    onglet_avatars,
    onglet_journal,
    onglet_membres,
    onglet_qualite,
    onglet_reglages,
    onglet_vue_ensemble,
)


def afficher(ctx):
    """Espace admin : écran de connexion, puis en-tête et les 6 onglets."""
    ss = st.session_state
    if not ss.get("admin_ok"):
        connexion.afficher(ctx)
        return
    _, defaut = connexion.mdp_attendu()
    c1, c2 = st.columns([3, 1])
    c1.markdown("## 🔒 Espace admin · salle des machines")
    c2.button("Quitter l'espace admin", icon=":material/logout:", width="stretch",
              on_click=lambda: (ss.update(admin_ok=False, page="accueil")))
    if defaut:
        st.caption("⚠️ Mot de passe de démonstration « 007 » actif. Avant toute mise en ligne, définis ADMIN_MDP dans "
                   "`.streamlit/secrets.toml` (voir README).")
    t1, t2, t3, t4, t6, t5 = st.tabs(["📊 Vue d'ensemble", "👥 Membres", "🎛️ Réglages du moteur", "🧪 Qualité du moteur",
                                       "🖼️ Avatars", "📜 Journal & base"])
    donnees = chargement.charger()
    with t1:
        onglet_vue_ensemble.afficher(ctx, donnees)
    with t2:
        onglet_membres.afficher(ctx, donnees)
    with t3:
        onglet_reglages.afficher(ctx)
    with t4:
        onglet_qualite.afficher(ctx)
    with t6:
        onglet_avatars.afficher(ctx)
    with t5:
        onglet_journal.afficher(ctx, donnees)
