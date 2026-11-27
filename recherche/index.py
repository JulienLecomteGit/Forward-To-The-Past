"""Index de la recherche prédictive : exporte une fois le catalogue (films triés par popularité + personnes) en JSON
dans static/, pour que le navigateur filtre à chaque lettre sans relancer la page.

Utilise     : config (chemins), medias (affiches)
Utilisé par : recherche
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter

import streamlit as st

from config.chemins import DOSSIER_STATIC
from medias.affiches import CHEMIN_TMDB_VALIDE, affiches_locales

VERSION = "3"  # à changer pour forcer la régénération de l'index


@st.cache_resource(show_spinner=False, max_entries=2)
def _index(_cat, empreinte: str) -> str:
    """Écrit static/recherche_<empreinte>.json (films triés par popularité + personnes) et renvoie son nom."""
    nom = f"recherche_{empreinte}.json"
    chemin = DOSSIER_STATIC / nom
    if not chemin.exists():
        for vieux in DOSSIER_STATIC.glob("recherche_*.json"):
            vieux.unlink(missing_ok=True)
        df, locales = _cat.df, affiches_locales()
        films = []
        for j in _cat.par_popularite:
            f = df.iloc[int(j)]
            aff = f["affiche"]
            if not CHEMIN_TMDB_VALIDE.fullmatch(aff.strip()):
                aff = ""                   # sans jaquette : le composant affiche l'affiche de remplacement
            code = ("L/" + aff.lstrip("/")) if aff and aff.lstrip("/") in locales else aff
            annee = int(f["annee"]) if f["annee"] == f["annee"] else None
            films.append([f["tconst"], f["titre"], f["original"] if f["original"] != f["titre"] else "", annee, f["genre"],
                          code, ", ".join(f["real_noms"][:1])])
        reals = Counter(p for r in _cat.real for p in r)
        acteurs = Counter(p for a in _cat.acteurs for p in a)
        personnes = [[_cat.noms[p], n, "r" if reals[p] >= acteurs[p] else "a"]
                     for p, n in (reals + acteurs).most_common() if n >= 3 and p in _cat.noms]
        chemin.write_text(json.dumps({"films": films, "personnes": personnes}, ensure_ascii=False, separators=(",", ":")),
                          encoding="utf-8")
    return nom


def fichier_index(cat) -> str:
    """Fichier d'index du champ de recherche, recréé seulement si le catalogue change."""
    empreinte = hashlib.sha1(("|".join(cat.df.tconst) + VERSION).encode()).hexdigest()[:10]
    return _index(cat, empreinte)
