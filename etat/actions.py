"""Actions des boutons (callbacks) : ❤️ ➕ 🤮 vu, note, carnet de séance, et messages (toasts) qui les confirment.

Règle : un callback n'affiche rien lui-même, il met un message en file d'attente (annoncer).

Utilise     : config (messages), donnees (base, carnet, interactions, journal)
Utilisé par : app, interface (cartes), vues (fiche, machine, mes_films, profil),
              vues/admin (onglet_avatars, onglet_journal, onglet_membres, onglet_reglages)
"""
from __future__ import annotations

import streamlit as st

from config.messages import MESSAGES
from donnees import base, carnet, interactions, journal


def annoncer(texte: str, icone: str = "✨") -> None:
    """Met un toast en file d'attente. Un callback ne doit rien afficher lui-même : pendant la relance
    d'un fragment (fiche film), Streamlit remplacerait les premiers éléments de la page."""
    st.session_state.setdefault("toasts", []).append((texte, icone))


def afficher_toasts() -> None:
    """Affiche puis vide les messages en attente (posés par annoncer pendant un clic)."""
    for texte, icone in st.session_state.pop("toasts", []):
        st.toast(texte, icon=icone)


def basculer(tconst: str, type_: str, source: str = "") -> None:
    """Ajoute ou retire une réaction (❤️, ➕, 🤮, vu) pour le membre connecté, avec message."""
    uid = st.session_state.get("uid")
    if not uid:
        return
    actif = interactions.basculer(uid, tconst, type_, source)
    journal.journaliser(uid, f"{type_}_{'ajout' if actif else 'retrait'}", {"tconst": tconst, "source": source})
    icone, texte = MESSAGES[(type_, actif)]
    annoncer(texte, icone)


def noter(tconst: str, cle: str, source: str = "") -> None:
    """Enregistre la note choisie avec les étoiles (0 à 4 à l'écran → 1 à 5 en base)."""
    uid = st.session_state.get("uid")
    valeur = st.session_state.get(cle)
    if not uid:
        return
    note = None if valeur is None else float(valeur + 1)  # st.feedback « stars » renvoie 0 à 4
    interactions.noter(uid, tconst, note, source)
    journal.journaliser(uid, "note", {"tconst": tconst, "note": note})
    annoncer(f"Note enregistrée : {'★' * int(note)} · +5 XP" if note else "Note retirée", "⭐")


def enregistrer_seance(tconst: str, cle: str) -> None:
    """Enregistre la séance saisie dans le carnet (date, lieu, note, avis)."""
    ss = st.session_state
    uid = ss.get("uid")
    if not uid:
        return
    date_s = ss.get(f"{cle}_date")
    note = ss.get(f"{cle}_note")
    carnet.enregistrer_seance(uid, tconst, date_s.isoformat() if date_s else base.maintenant()[:10],
                           ss.get(f"{cle}_lieu") or "cinema", None if note is None else int(note) + 1, ss.get(f"{cle}_avis", ""))
    journal.journaliser(uid, "seance_ajout", {"tconst": tconst})
    annoncer("Séance ajoutée à ton carnet · +5 XP", "🎟️")


def retirer_seance(tconst: str) -> None:
    """Retire la séance d'un film du carnet du membre connecté."""
    uid = st.session_state.get("uid")
    if uid:
        carnet.retirer_seance(uid, tconst)
        annoncer("Séance retirée du carnet", "🗑️")
