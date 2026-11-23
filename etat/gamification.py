"""Gamification : points d'expérience (XP), niveau atteint et badges avec leur progression.

Utilise     : config (gamification), etat (contexte)
Utilisé par : vues (profil)
"""
from __future__ import annotations

import numpy as np

from config.gamification import NIVEAUX
from etat.contexte import Ctx


def xp(ctx: Ctx, nb_connexions: int = 0) -> int:
    """Points d'expérience : 50 au départ + points par réaction, note, vu et connexion (plafonnée)."""
    i = ctx.inter
    return (50 + 5 * len(i.get("like", {})) + 3 * len(i.get("liste", {})) + 5 * len(i.get("note", {}))
            + 2 * len(i.get("vu", {})) + len(i.get("dislike", {})) + 2 * min(nb_connexions, 60))


def niveau(points: int) -> tuple[int, str, float, int]:
    """(numéro, titre, progression vers le niveau suivant 0-1, points restants)."""
    k = max(i for i, (seuil, _) in enumerate(NIVEAUX) if points >= seuil)
    if k == len(NIVEAUX) - 1:
        return k + 1, NIVEAUX[k][1], 1.0, 0
    bas, haut = NIVEAUX[k][0], NIVEAUX[k + 1][0]
    return k + 1, NIVEAUX[k][1], (points - bas) / (haut - bas), haut - points


def badges(ctx: Ctx) -> list[dict]:
    """Badges avec progression : icône, titre, condition, valeur atteinte, objectif."""
    cat, pr, i = ctx.cat, ctx.profil, ctx.inter
    aimes = np.array(pr.aimes, dtype=int) if pr else np.array([], int)
    sagas = [cat.saga[j] for j in aimes if cat.saga[j]]
    max_saga = max((sagas.count(s) for s in set(sagas)), default=0)
    liste = [
        ("🎬", "Premier coup de cœur", "Aimer un premier film", len(aimes), 1),
        ("💯", "Cinéphile en herbe", "10 films aimés", len(aimes), 10),
        ("🏆", "Critique officiel", "10 films notés", len(i.get("note", {})), 10),
        ("🎟️", "Habitué des salles", "5 séances dans le carnet", len(ctx.seances), 5),
        ("🕰️", "Voyageur des décennies", "Des films aimés sur 4 décennies", len(set(cat.decennie[aimes])), 4),
        ("🇫🇷", "Ambassadeur du cinéma français", "5 films français aimés", int(cat.fr[aimes].sum()) if len(aimes) else 0, 5),
        ("🔗", "Collectionneur de sagas", "2 volets d'une même saga aimés", max_saga, 2),
        ("📼", "Vidéothèque pleine", "10 films à voir", len(i.get("liste", {})), 10),
        ("🌈", "Éclectique", "Des films aimés dans 6 genres", len(set(cat.genre_code[aimes])), 6),
    ]
    return [{"icone": ic, "titre": t, "condition": c, "valeur": min(v, obj), "objectif": obj, "ok": v >= obj}
            for ic, t, c, v, obj in liste]
