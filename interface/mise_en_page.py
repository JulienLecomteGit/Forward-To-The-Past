"""Éléments de mise en page : titre de section (avec sous-titre) et grande bannière d'accueil (DeLorean).

Utilise     : —
Utilisé par : vues (accueil, auth, explorer, fiche, machine, mes_films, profil),
              vues/admin (onglet_journal, onglet_membres, onglet_qualite, onglet_reglages, onglet_vue_ensemble,
              simulation)
"""
from __future__ import annotations

from html import escape

import streamlit as st


def section(titre: str, sous_titre: str = "") -> None:
    """Titre de rubrique avec sous-titre facultatif."""
    st.html(f'<div class="ft-section"><h3>{escape(titre)}</h3>' + (f"<p>{escape(sous_titre)}</p>" if sous_titre else "") + "</div>")


def banniere(ligne1_html: str, ligne2: str, texte: str, pastille: str = "⚡ FORWARD TO THE PAST · CINÉ-CLUB 88 MPH") -> None:
    """Grande bannière d'en-tête de page (pastille, titre sur deux lignes, texte)."""
    st.html(f'<div class="ft-banniere"><div class="ft-ban-img"></div><div class="ft-ban-voile"></div><div class="ft-ban-texte">'
            f'<span class="ft-pastille">{escape(pastille)}</span><h1>{ligne1_html}<span>{escape(ligne2)}</span></h1>'
            f'<p>{texte}</p></div></div>')


def colonnes(mobile: bool, spec, meme_conteneur: bool = False, **options):
    """Colonnes sur ordinateur, blocs empilés sur mobile.

    Ordinateur : st.columns(spec, **options). Mobile : un conteneur par colonne, dans l'ordre (ou le MÊME conteneur
    répété si meme_conteneur=True : les éléments s'y ajoutent les uns sous les autres).
    spec : nombre de colonnes ou liste des largeurs relatives, comme st.columns.
    """
    if not mobile:
        return st.columns(spec, **options)
    n = spec if isinstance(spec, int) else len(spec)
    if meme_conteneur:
        return (st.container(),) * n
    return tuple(st.container() for _ in range(n))


def selon_ecran(mobile: bool, valeurs: tuple):
    """Choisit la valeur adaptée à l'écran : valeurs = (ordinateur, mobile), par exemple FILMS_PAR_RANGEE = (4, 2)."""
    return valeurs[1] if mobile else valeurs[0]
