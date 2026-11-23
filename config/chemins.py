"""Emplacements des dossiers et adresses web de l'app, calculés une fois depuis la racine du projet.

Utilise     : —
Utilisé par : demo (generation), donnees (base), etat (cache), medias (affiches, avatars), recherche (index)
"""
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent  # dossier du projet (celui qui contient app.py)
DOSSIER_DATA = RACINE / "data"                    # catalogue CSV et base SQLite
DOSSIER_STATIC = RACINE / "static"                # fichiers servis tels quels par Streamlit (server.enableStaticServing)
DOSSIER_AFFICHES = DOSSIER_STATIC / "affiches"    # affiches locales (fonctionnent sans internet)
DOSSIER_AVATARS = DOSSIER_STATIC / "avatars"      # images des avatars + avatars.json (libellés, catégories)
DOSSIER_COMPOSANT_RECHERCHE = RACINE / "composants" / "recherche"  # barre de recherche prédictive (HTML/JS)
BDD_PAR_DEFAUT = DOSSIER_DATA / "fttp.db"         # remplaçable par la variable d'environnement FTTP_BDD

URL_STATIQUE = "app/static/"                      # adresse web de static/ vue depuis le navigateur
URL_TMDB_IMAGES = "https://image.tmdb.org/t/p/"   # serveur d'images TMDB (affiches absentes en local)
