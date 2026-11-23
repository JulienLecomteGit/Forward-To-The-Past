"""Tuiles de chiffres : tuile simple (Mon Rewind, carnet), carte KPI et tuile de score de l'admin.

Utilise     : —
Utilisé par : vues (mes_films, profil), vues/admin (onglet_qualite, onglet_vue_ensemble, simulation)
"""
from __future__ import annotations

from html import escape


def tuile(titre: str, valeur: str, detail: str = "") -> str:
    """Tuile de chiffre clé : titre, grande valeur, détail."""
    return (f'<div class="ft-tuile"><p>{escape(titre)}</p><div class="grand">{escape(valeur)}</div>'
            f'<div class="ft-petit">{escape(detail)}</div></div>')


def tuile_kpi(titre: str, valeur: str, sous: str, ton: str = "neutre", aide: str = "") -> str:
    """Carte KPI : même structure pour toutes (titre / valeur / pastille) → textes alignés d'une carte à l'autre.
    ton : hausse, baisse ou neutre."""
    fleche = {"hausse": "↑ ", "baisse": "↓ "}.get(ton, "")
    return (f'<div class="ft-tuile ft-kpi" title="{escape(aide, quote=True)}"><p>{escape(titre)}</p><div class="grand">{escape(valeur)}</div>'
            f'<span class="ft-delta {ton}">{fleche}{escape(sous)}</span></div>')


def tuile_score(couleur: str, titre: str, valeur: str, *pieds: str) -> str:
    """Tuile de score de l'admin (qualité, simulation) : titre, grande valeur, puis lignes de détail (HTML déjà prêt)."""
    return (f'<div class="ad-score" style="--c:{couleur}"><p>{escape(titre)}</p><div class="grand">{valeur}</div>'
            + "".join(pieds) + "</div>")
