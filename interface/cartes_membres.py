"""Cartes membres (« Qui passe la séance ce soir ? », jumeaux ciné) et galerie d'avatars cliquable.

Utilise     : medias (avatars)
Utilisé par : vues (auth, machine, profil)
"""
from __future__ import annotations

from html import escape

import streamlit as st

from medias import avatars


def carte_membre_html(cle_avatar: str, nom: str, pseudo: str = "", genres: str = "", extra: str = "", choisi: bool = False) -> str:
    """Carte d'un membre ou d'un avatar (image, nom, pseudo, genres, mention)."""
    return (f'<div class="fm-carte{" choisi" if choisi else ""}"><img src="{avatars.url(cle_avatar)}" alt="Avatar {escape(avatars.nom(cle_avatar))}">'
            f'<div class="fm-nom">{escape(nom)}</div>' + (f'<div class="fm-pseudo">{escape(pseudo)}</div>' if pseudo else "")
            + (f'<div class="fm-genres">{escape(genres)}</div>' if genres else "")
            + (f'<span class="fm-extra">{escape(extra)}</span>' if extra else "") + "</div>")


def carte_membre_cliquable(cle: str, html: str, libelle: str, rappel, args) -> None:
    """Carte HTML recouverte d'un bouton invisible qui déclenche `rappel(*args)`."""
    with st.container(key=f"clic_{cle}"):
        st.html(html)
        st.button(libelle, key=f"cliq_{cle}", on_click=rappel, args=args)


def grille_avatars(prefixe: str, choisi: str, rappel, categorie: str | None = None) -> None:
    """Grille des avatars d'une catégorie ; un clic appelle `rappel(cle_avatar)`."""
    with st.container(key="gmembres_avatars", horizontal=True):
        for cle in avatars.par_categorie(categorie):
            carte_membre_cliquable(f"av_{prefixe}_{cle}", carte_membre_html(cle, avatars.nom(cle), choisi=cle == choisi),
                                   avatars.nom(cle), rappel, (cle,))
