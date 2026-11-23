"""Petits morceaux de texte et de HTML des films : logo, année · genre · durée, note, origine, étoiles, résumé court.

Utilise     : config (affichage, catalogue)
Utilisé par : app, interface (cartes, jaquettes), vues (auth, fiche, machine, mes_films)
"""
from __future__ import annotations

import math
from html import escape

from config.affichage import EMOJI_GENRE
from config.catalogue import ORIGINES_PRODUCTION


def logo_html() -> str:
    """Logo texte du bandeau."""
    return '<div class="ft-logo">⚡ FORWARD TO THE PAST <b>·</b> CINÉ-CLUB</div>'


def meta_film(f: dict) -> str:
    """Ligne courte « année · genre · durée » d'un film (éléments inconnus omis)."""
    morceaux = []
    if f.get("annee") == f.get("annee"):
        morceaux.append(str(int(f["annee"])))
    if f.get("genre"):
        morceaux.append(f"{EMOJI_GENRE.get(f['genre'], '🎞️')} {f['genre']}")
    if f.get("duree") == f.get("duree") and f.get("duree"):
        morceaux.append(f"{int(f['duree'])} min")
    return " · ".join(morceaux)


def note_txt(note) -> str:
    """Note au format français « 7,4 » (vide si inconnue)."""
    return "" if note is None or (isinstance(note, float) and math.isnan(note)) else f"{note:.1f}".replace(".", ",")


def origine_txt(f: dict) -> str:
    """Libellé de l'origine de production (ex. « France », « Coproduction »)."""
    return ORIGINES_PRODUCTION.get(f.get("origine", ""), f.get("origine", ""))


def etoiles(n) -> str:
    """Note de 0 à 5 dessinée en étoiles pleines et vides."""
    n = int(n or 0)
    return "★" * n + "☆" * (5 - n)


def resume_court(f: dict) -> str:
    """« Réalisé par … », ou à défaut le titre original."""
    reals = ", ".join(f.get("real_noms") or ())
    return f"Réalisé par {reals}" if reals else (f.get("original") or "")


def balise_affiche(url: str, titre: str, paresseuse: bool = True) -> str:
    """Balise <img> d'une affiche (le titre est gardé dans data-t) ; « paresseuse » = chargée seulement quand visible."""
    chargement = ' loading="lazy"' if paresseuse else ""
    return f'<img src="{url}" alt=""{chargement} data-t="{escape(titre, quote=True)}">'
