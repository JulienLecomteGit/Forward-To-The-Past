"""Bandes de jaquettes non cliquables, avec pastilles (🆕, ↑2, ✅…) : aperçus et tests de l'admin.

Utilise     : interface (textes), medias (affiches), outils (texte)
Utilisé par : vues/admin (onglet_qualite, onglet_reglages, simulation)
"""
from __future__ import annotations

from html import escape

from interface.textes import balise_affiche
from medias.affiches import url_affiche
from outils.texte import annee_txt


def jaquettes(cat, indices, marques: dict | None = None, classes: dict | None = None, col: int | None = None) -> str:
    """Bande de jaquettes non cliquables, avec pastille (🆕, ↑2, ✅…) et classe CSS par film."""
    marques, classes = marques or {}, classes or {}
    items = []
    for j in indices:
        f = cat.df.iloc[int(j)]
        url = url_affiche(f["affiche"], "w185")
        titre = escape(f["titre"])
        img = balise_affiche(url, f["titre"]) if url else f'<div class="fj-vide">{titre}</div>'
        badge = ""
        if j in marques:
            txt, cls = marques[j] if isinstance(marques[j], tuple) else (marques[j], "")
            badge = f'<span class="fj-badge {cls}">{txt}</span>'
        annee = annee_txt(f["annee"])
        items.append(f'<div class="fj-item {classes.get(j, "")}" title="{escape(f["titre"], quote=True)}"><div class="fj-img">{img}{badge}</div>'
                     f'<div class="fj-titre">{titre}</div><div class="fj-sous">{annee} · {escape(f["genre"])}</div></div>')
    style = f' style="--fj-col:{col}"' if col else ""
    return f'<div class="fj-bande"{style}>' + "".join(items) + "</div>"
