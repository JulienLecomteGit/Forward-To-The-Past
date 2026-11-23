"""Thème visuel « Vice ciné-club 88 MPH » : assemble le CSS de l'app à partir des fichiers de interface/style/.

Rôle        : lire les feuilles de style rangées par zone d'écran et les recoller, dans l'ordre, en trois textes CSS.

Modifier un style : ouvrir le fichier .css de la zone concernée (liste ZONES ci-dessous), enregistrer, puis
relancer l'app (Streamlit ne surveille que les fichiers .py : une modification de .css seule ne recharge pas la page).
L'ordre de ZONES est l'ordre de la cascade CSS : une règle placée plus bas l'emporte. Ne pas le changer.

Utilise     : —
Utilisé par : app, vues (machine)
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

DOSSIER = Path(__file__).resolve().parent / "style"

ZONES = [  # ordre d'application des styles (ordinateur et mobile)
    "01_polices_et_base.css",          # polices locales, couleurs de la marque (variables --ft-…), fond, titres
    "02_titres_boutons_champs.css",    # titres de section, boutons, pastilles, champs de saisie, barres de défilement
    "03_navigation.css",               # barre du haut, barre de navigation, menu du membre
    "04_banniere.css",                 # bannière d'accueil (DeLorean)
    "05_cartes_film.css",              # cartes film : affiche, réactions ❤️ ➕ 🤮, score, chiffres
    "06_fiche_film.css",               # fiche film pleine page, puces (chips)
    "07_cartes_membres.css",           # « Qui passe la séance ? », jumeaux ciné, galerie d'avatars
    "08_profil.css",                   # en-tête du profil, niveau, préférences
    "09_jaquettes_et_admin.css",       # bandes de jaquettes, barres de répartition, cartes et tuiles de l'admin
    "10_pastilles_adn_badges.css",     # pastilles en grille (genres, décennies, humeurs), ADN ciné, badges
    "11_mes_films.css",                # Mes films : lignes compactes, outils de recherche et de tri
    "12_convecteur_temporel.css",      # 88 MPH › Convecteur : compteur, convecteur, billet, animations
    "13_time_circuits.css",            # Time Circuits (afficheurs de dates de la DeLorean)
    "14_destination_annee.css",        # 88 MPH › Destination année : cartes d'années
    "15_onglets_et_boutons_80s.css",   # onglets et boutons biseautés « coucher de soleil »
    "16_divers.css",                   # étapes de l'inscription, coche, panneau LED, ligne de séance, étoiles
]


def _lire(nom: str) -> str:
    """Contenu d'un fichier CSS du dossier interface/style."""
    return (DOSSIER / nom).read_text(encoding="utf-8")


# Chaque texte commence par un saut de ligne, exactement comme les chaînes CSS d'origine (V9) : le kit compare
# le CSS au caractère près.
CSS = "\n" + "".join(_lire(nom) for nom in ZONES)  # thème complet (toujours injecté)
CSS_MOBILE = "\n" + _lire("mobile.css")            # ajouté quand l'affichage « Mobile » est actif
CSS_CADRE = "\n" + _lire("cadre_telephone.css")    # ajouté en « Mobile » sur ordinateur (cadre de téléphone)


def style(css: str) -> None:
    """CSS injecté dans le flux principal (un st.html « style seul » irait dans le conteneur d'événements,
    vidé à chaque relance de fragment)."""
    st.html(f'<style>{css}</style><span class="ft-css"></span>')


def injecter_theme(mobile: bool, cadre: bool) -> None:
    """Injecte le CSS de base, plus le CSS mobile et le cadre de téléphone si besoin."""
    style(CSS + (CSS_MOBILE if mobile else "") + (CSS_CADRE if mobile and cadre else ""))
