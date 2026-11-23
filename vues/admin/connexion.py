"""Espace admin › écran du code d'accès (5 essais puis 60 s d'attente) et mot de passe attendu.

Mot de passe : secrets.toml (ADMIN_MDP) > variable d'environnement FTTP_ADMIN_MDP > « 007 » (démo).

Utilise     : config (acces), donnees (journal), etat (navigation)
Utilisé par : vues (admin)
"""
from __future__ import annotations

import hmac
import os
import time

import streamlit as st

from config.acces import BLOCAGE_ADMIN_S, CODE_ADMIN_DEMO, ESSAIS_MAX
from donnees import journal
from etat.navigation import aller


def mdp_attendu() -> tuple[str, bool]:
    """Mot de passe admin : secrets.toml > variable d'environnement > « 007 » (démo)."""
    try:
        return str(st.secrets["ADMIN_MDP"]), False
    except Exception:
        pass
    if os.environ.get("FTTP_ADMIN_MDP"):
        return os.environ["FTTP_ADMIN_MDP"], False
    return CODE_ADMIN_DEMO, True


def afficher(ctx):
    """Écran « Accès réservé » : saisie du mot de passe admin, blocage après trop d'essais."""
    ss = st.session_state
    _, c, _ = st.columns([1, 1.3, 1]) if not ctx.mobile else (None, st.container(), None)
    with c:
        st.html('<div style="text-align:center;margin-top:1.5rem"><div style="font-size:3rem">🔐</div>'
                '<h2 style="margin:.2rem 0">Accès réservé</h2>'
                '<p class="ft-petit">Statistiques des membres et réglages du moteur de recommandation.</p></div>')
        reste = ss.get("admin_bloque", 0) - time.time()
        with st.form("admin_login"):
            mdp = st.text_input("Code d'accès", type="password", placeholder="•••")
            ok = st.form_submit_button("Entrer", type="primary", width="stretch", disabled=reste > 0)
        if reste > 0:
            st.warning(f"Trop d'essais : nouvel essai possible dans {int(reste) + 1} s.")
        elif ok:
            attendu, _ = mdp_attendu()
            if hmac.compare_digest(mdp.encode(), attendu.encode()):
                ss.admin_ok, ss.admin_essais = True, 0
                journal.journaliser(ss.get("uid"), "admin_connexion")
                st.rerun()
            ss.admin_essais = ss.get("admin_essais", 0) + 1
            journal.journaliser(ss.get("uid"), "admin_echec")
            if ss.admin_essais >= ESSAIS_MAX:
                ss.admin_bloque, ss.admin_essais = time.time() + BLOCAGE_ADMIN_S, 0
            st.error("Code incorrect.")
        st.button("Retour", icon=":material/arrow_back:", on_click=aller, args=("accueil",), width="stretch")
