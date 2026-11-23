"""Chargements mis en mémoire (cache Streamlit) : catalogue de films, communauté des membres, réglages du moteur.

Utilise     : config (catalogue, chemins, reglages_moteur), donnees (catalogue, interactions, reglages),
              moteur (communaute)
Utilisé par : app, etat (contexte), vues/admin (onglet_qualite, onglet_reglages)
"""
from __future__ import annotations

import hashlib

import streamlit as st

from config.catalogue import CSV_NOM
from config.chemins import RACINE
from config.reglages_moteur import PARAMS_DEFAUT
from donnees import interactions, reglages
from donnees.catalogue import Catalogue, chemin_csv, lire_catalogue
from moteur.communaute import Communaute


@st.cache_resource(max_entries=2, show_spinner="Allumage du moteur… 88 % … 100 % ⚡")
def _catalogue(empreinte: str, _contenu: bytes) -> Catalogue:
    """Version mise en cache : relue seulement si l'empreinte du fichier CSV change."""
    return lire_catalogue(_contenu)


def catalogue() -> Catalogue | None:
    """Catalogue prêt à l'emploi : CSV du dossier data/, sinon fichier déposé par l'utilisateur ;
    None (avec un message) s'il n'y en a pas.
    """
    try:
        source = chemin_csv(RACINE)
    except FileNotFoundError as e:
        st.error(str(e))
        return None
    if source is None:
        st.info(f"Place **{CSV_NOM}** dans le dossier `data/` du projet, ou charge-le ici.")
        fichier = st.file_uploader(f"Catalogue · {CSV_NOM}", type=["csv"])
        if fichier is None:
            return None
        contenu = fichier.getvalue()
    else:
        contenu = source.read_bytes()
    try:
        return _catalogue(hashlib.sha256(contenu).hexdigest(), contenu)
    except (OSError, UnicodeError, ValueError) as e:
        st.error(f"Impossible d'ouvrir le catalogue : {e}")
        return None


@st.cache_resource(max_entries=3, show_spinner=False)
def _communaute(_cat: Catalogue, version: str) -> Communaute:
    """Version mise en cache. `version` ne sert pas dans le calcul : c'est la clé du cache, qui change à chaque
    nouvelle interaction en base et force alors le recalcul (vulture le signale à tort comme inutilisé).
    """
    return Communaute(_cat, interactions.toutes_interactions())


def communaute(cat) -> Communaute:
    """Données communautaires à jour (recalculées seulement si les interactions ont changé)."""
    return _communaute(cat, interactions.version_communaute())


def parametres() -> dict:
    """Réglages actuels du moteur."""
    return reglages.lire_parametres(PARAMS_DEFAUT)
