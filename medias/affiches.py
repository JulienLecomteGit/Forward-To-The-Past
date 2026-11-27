"""Affiches des films : image locale (static/affiches, fonctionne sans internet) sinon serveur d'images TMDB ;
affiche de remplacement « introuvable » si le film n'a pas de jaquette.

Utilise     : config (chemins)
Utilisé par : interface (cartes, jaquettes), recherche (index), vues (auth, fiche, machine)
"""
from __future__ import annotations

import re
from functools import lru_cache
from urllib.parse import quote

from config.chemins import AFFICHE_INTROUVABLE, DOSSIER_AFFICHES, URL_STATIQUE, URL_TMDB_IMAGES

# Adresse web de l'affiche de remplacement (espaces et accent encodés : « Affiche%20r%C3%A9tro… »)
URL_INTROUVABLE = URL_STATIQUE + quote(AFFICHE_INTROUVABLE)
CHEMIN_TMDB_VALIDE = re.compile(r"/[A-Za-z0-9_-]+\.(?:jpg|jpeg|png)")  # forme d'un poster_path TMDB


@lru_cache(maxsize=1)
def affiches_locales() -> frozenset:
    """Noms des jaquettes présentes dans static/affiches (ensemble vide si le dossier manque)."""
    dossier = DOSSIER_AFFICHES
    return frozenset(p.name for p in dossier.glob("*.jpg")) if dossier.is_dir() else frozenset()


def url_affiche(chemin: str, taille: str = "w342") -> str:
    """Affiche locale vérifiée (static/affiches, fonctionne hors-ligne) sinon serveur d'images TMDB ;
    affiche de remplacement si le chemin est vide ou invalide (une erreur 404 de TMDB est gérée par le CSS)."""
    chemin = (chemin or "").strip()
    if not CHEMIN_TMDB_VALIDE.fullmatch(chemin):
        return URL_INTROUVABLE
    nom = chemin.lstrip("/")
    return URL_STATIQUE + "affiches/" + nom if nom in affiches_locales() else URL_TMDB_IMAGES + taille + chemin
