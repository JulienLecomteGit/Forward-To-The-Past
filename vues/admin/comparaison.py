"""Espace admin › comparaison de deux classements : pastilles 🆕 nouveau, ↑ monte, ↓ descend, et bilan chiffré.

Utilise     : —
Utilisé par : vues/admin (onglet_reglages, simulation)
"""
from __future__ import annotations


def comparer_classements(avant: list, apres: list) -> tuple[dict, dict, dict]:
    """Pastilles 🆕 / ↑ / ↓ du classement « après » comparé à « avant »."""
    rang = {j: k for k, j in enumerate(avant)}
    marques, classes, bilan = {}, {}, {"nouveaux": 0, "montent": 0, "descendent": 0, "stables": 0}
    for k, j in enumerate(apres):
        if j not in rang:
            marques[j], classes[j] = ("🆕", "nouveau"), "nouveau"
            bilan["nouveaux"] += 1
        elif rang[j] > k:
            marques[j] = (f"↑{rang[j] - k}", "monte")
            bilan["montent"] += 1
        elif rang[j] < k:
            marques[j] = (f"↓{k - rang[j]}", "descend")
            bilan["descendent"] += 1
        else:
            bilan["stables"] += 1
    return marques, classes, bilan


def bilan_html(bilan: dict) -> str:
    """Puces « nouveaux / montent / descendent / identiques » d'une comparaison de classements."""
    return ('<div class="ft-gouts"><span class="ft-gout">🆕 <em>' + str(bilan["nouveaux"]) + '</em> nouveaux</span>'
            f'<span class="ft-gout">↑ <em>{bilan["montent"]}</em> montent</span><span class="ft-gout">↓ <em>{bilan["descendent"]}</em> '
            f'descendent</span><span class="ft-gout">= <em>{bilan["stables"]}</em> identiques</span></div>')
