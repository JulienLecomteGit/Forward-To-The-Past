"""Barres de répartition colorées avec légende (« recette » du moteur, goûts d'un membre) et pastilles de goûts.

Utilise     : config (affichage)
Utilisé par : vues (accueil, profil), vues/admin (onglet_reglages, simulation)
"""
from __future__ import annotations

from html import escape

from config.affichage import COULEURS_BARRES, EMOJI_GENRE


def barre(parts: list[tuple[str, float]], legende: bool = True, pourcent: bool = True) -> str:
    """Barre de répartition colorée + légende (« recette » du moteur, goûts d'un membre)."""
    tot = sum(max(v, 0) for _, v in parts) or 1
    segs = "".join(f'<i style="width:{100 * max(v, 0) / tot:.2f}%;background:{COULEURS_BARRES[k % len(COULEURS_BARRES)]}" title="{escape(lab)}"></i>'
                   for k, (lab, v) in enumerate(parts) if v > 0)
    html = f'<div class="ft-barre">{segs}</div>'
    if legende:
        html += '<div class="ft-legende">' + "".join(
            f'<span style="--c:{COULEURS_BARRES[k % len(COULEURS_BARRES)]}">{escape(lab)} <b>{(100 * v / tot):.0f} %</b></span>' if pourcent else
            f'<span style="--c:{COULEURS_BARRES[k % len(COULEURS_BARRES)]}">{escape(lab)} <b>{v:g}</b></span>'
            for k, (lab, v) in enumerate(parts) if v > 0) + "</div>"
    return html


def gouts_html(gouts: list[tuple[str, float]], titre: str = "Ce que le moteur a compris de toi :") -> str:
    """Puces « genre + pourcentage » des 5 goûts principaux (vide s'il n'y en a pas)."""
    if not gouts:
        return ""
    return (f'<div class="ft-gouts"><span class="lab">{escape(titre)}</span>' + "".join(
        f'<span class="ft-gout">{EMOJI_GENRE.get(g, "🎞️")} {escape(g)} <em>{v:.0%}</em></span>' for g, v in gouts[:5]) + "</div>")
