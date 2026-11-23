"""Affiches des films : image locale (static/affiches, fonctionne sans internet) sinon serveur d'images TMDB.

Utilise     : config (chemins)
Utilisé par : interface (cartes, jaquettes), recherche (index), vues (auth, fiche, machine)
"""
from __future__ import annotations

from functools import lru_cache

from config.chemins import DOSSIER_AFFICHES, URL_STATIQUE, URL_TMDB_IMAGES


@lru_cache(maxsize=1)
def affiches_locales() -> frozenset:
    """Noms des jaquettes présentes dans static/affiches (ensemble vide si le dossier manque)."""
    dossier = DOSSIER_AFFICHES
    return frozenset(p.name for p in dossier.glob("*.jpg")) if dossier.is_dir() else frozenset()


def url_affiche(chemin: str, taille: str = "w342") -> str:
    """Affiche locale vérifiée (static/affiches, fonctionne hors-ligne) sinon serveur d'images TMDB."""
    if not chemin:
        return ""
    nom = chemin.lstrip("/")
    return URL_STATIQUE + "affiches/" + nom if nom in affiches_locales() else URL_TMDB_IMAGES + taille + chemin
