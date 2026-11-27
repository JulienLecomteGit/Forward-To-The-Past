"""Paramètres du catalogue de films (fichier CSV) : nom, emplacements possibles, colonnes obligatoires, libellés.

Utilise     : —
Utilisé par : demo (generation), donnees (catalogue), etat (cache), interface (textes),
              vues (auth, explorer, fiche, machine)
"""
from pathlib import Path

# Nom du fichier catalogue, cherché dans data/ puis dans le Drive (voir chemin_csv)
CSV_NOM = "Catalogue_CNC_VF.csv"
DOSSIER_PROJET = Path("Formation Data Analyst", "Projets", "Convaincre le CNC de financer votre projet")
DANS_PROJET = Path("Données", "Finalisées", "catalogue_Final_enrichi", CSV_NOM)
REQUIS = ("tconst", "titre_affiche", "originalTitle", "startYear", "runtimeMinutes", "genre_source",
          "original_language", "origine_production", "film_francais", "entrees_france", "saga",
          "averageRating", "numVotes", "overview", "poster_path", "acteurs_principaux", "acteurs_nconst",
          "realisateurs", "realisateurs_nconst")

# Langues originales et origines de production : codes du CSV → libellés affichés sur la fiche film
LANGUES = {"en": "Anglais", "fr": "Français", "it": "Italien", "de": "Allemand", "es": "Espagnol", "ja": "Japonais",
           "zh": "Chinois", "cn": "Cantonais", "ru": "Russe", "sv": "Suédois", "ar": "Arabe", "fa": "Persan",
           "pl": "Polonais", "da": "Danois", "ko": "Coréen", "pt": "Portugais", "el": "Grec", "nl": "Néerlandais",
           "tr": "Turc", "hi": "Hindi", "he": "Hébreu", "hu": "Hongrois"}
ORIGINES_PRODUCTION = {"Prod_100%_France": "100 % française", "Co_production_Française": "Coproduction française",
                       "Étrangère": "Étrangère", "Origine inconnue": "Origine inconnue"}

# Période couverte par le catalogue (curseurs « Période » et « année de destination », bannière d'accueil)
ANNEE_MIN, ANNEE_MAX = 1960, 2016
