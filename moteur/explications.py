"""Explications « Pourquoi ce film ? » : traduit les critères qui ont le plus pesé en phrases lisibles
(« 🎭 Même genre : Comédie », « 🌟 Avec Jean Reno »…), de la plus forte à la plus faible contribution.

Utilise     : donnees (catalogue), moteur (recommandation), outils (texte)
Utilisé par : interface (cartes), vues (machine)
"""
from __future__ import annotations

import math

from donnees.catalogue import Catalogue
from moteur.recommandation import Resultat
from outils.texte import format_entrees


def _ans(n):
    """« 1 an » ou « n ans »."""
    return f"{n} an{'s' if n > 1 else ''}"


def pourquoi(cat: Catalogue, res: Resultat, j: int, maxi: int = 3) -> list[str]:
    """Raisons lisibles, de la plus forte à la plus faible contribution."""
    f = cat.df.iloc[j]
    raisons = []
    if res.mode == "film" and res.source is not None and cat.saga[res.source] and cat.saga[j] == cat.saga[res.source]:
        raisons.append(f"🔗 Autre volet de la saga {f['saga']}")
    contrib = sorted(((v, k) for k, v in res.contributions(j).items() if v > 0.15), reverse=True)
    for _, k in contrib:
        r = _raison(cat, res, j, k, f)
        if r and r not in raisons:
            raisons.append(r)
        if len(raisons) >= maxi:
            break
    return raisons or ["🎞️ Une proposition pour élargir tes horizons"]


def _raison(cat, res, j, k, f):
    """Phrase pour le critère k (« genre », « casting »…), ou None s'il n'y a rien de parlant à dire."""
    phrase = _PHRASES.get(k)
    return phrase(cat, res, j, f) if phrase else None


def _phrase_genre(cat, res, j, f):
    """🎭 Même genre (film → films) ou genre aimé (Pour toi)."""
    return f"🎭 Même genre : {f['genre']}" if res.mode == "film" else f"🎭 Tu aimes : {f['genre']}"


def _phrase_epoque(cat, res, j, f):
    """📅 Écart d'années avec le film de départ, ou décennie préférée du membre."""
    if math.isnan(f["annee"]):  # film sans année : rien à dire sur l'époque
        return None
    src = cat.df.iloc[res.source] if res.source is not None else None
    if res.mode == "film" and src is not None and not math.isnan(src["annee"]):
        n = int(abs(f["annee"] - src["annee"]))
        return "📅 Sorti la même année" if n == 0 else f"📅 {_ans(n)} d'écart ({int(f['annee'])})"
    return f"📅 Tes années {str(int(cat.decennie[j]))[2:]}"


def _phrase_duree(cat, res, j, f):
    """⏳ Durée proche ou format qui convient (rien si la durée est inconnue)."""
    if math.isnan(f["duree"]):
        return None
    return f"⏳ Durée proche ({int(f['duree'])} min)" if res.mode == "film" else f"⏳ Format qui te va ({int(f['duree'])} min)"


def _phrase_histoire(cat, res, j, f):
    """📖 Mots communs des résumés, ou film aimé dont l'histoire est la plus proche."""
    if res.mode == "film":
        mots = cat.termes_communs(res.source, j)
        return "📖 Histoire proche" + (f" ({', '.join(mots)})" if mots else "")
    g = res.contexte.get("graine_histoire")
    if g is not None:
        return f"📖 Proche de « {cat.df.iloc[int(g[j])]['titre']} »"
    return None


def _phrase_casting(cat, res, j, f):
    """🌟 Acteurs en commun (au plus 2), ou acteur que le membre apprécie."""
    if res.mode == "film":
        source = set(cat.acteurs[res.source])
        communs = sorted((p for p in dict.fromkeys(cat.acteurs[j]) if p in source),  # ordre du générique, puis poids : toujours le même
                         key=lambda p: -cat.poids_acteur.get(p, 0))
        noms = [cat.noms[p] for p in communs if p in cat.noms][:2]
        return "🌟 Avec " + " et ".join(noms) if noms else None
    pa = res.contexte.get("poids_act", {})
    meilleurs = sorted((p for p in cat.acteurs[j] if p in pa), key=lambda p: -pa[p])
    if meilleurs and meilleurs[0] in cat.noms:
        return f"🌟 Avec {cat.noms[meilleurs[0]]}, que tu apprécies"
    return None


def _phrase_realisation(cat, res, j, f):
    """🎬 Réalisateur en commun ou réalisateur que le membre aime."""
    reference = set(cat.real[res.source]) if res.mode == "film" else set(res.contexte.get("poids_real", {}))
    noms = [cat.noms[p] for p in dict.fromkeys(cat.real[j]) if p in reference and p in cat.noms]  # ordre du catalogue : toujours le même
    if noms:
        return f"🎬 Réalisé par {noms[0]}" + ("" if res.mode == "film" else ", que tu aimes")
    return None


def _phrase_communaute(cat, res, j, f):
    """👥 Signal des membres aux goûts proches."""
    return "👥 Ceux qui ont aimé ce film l'adorent aussi" if res.mode == "film" else "👥 Adoré par des membres qui ont tes goûts"


def _phrase_qualite(cat, res, j, f):
    """⭐ Note IMDb (rien si inconnue)."""
    return f"⭐ Très bien noté ({f['note']:.1f}/10)".replace(".", ",") if not math.isnan(f["note"]) else None


def _phrase_popularite(cat, res, j, f):
    """🎟️ Entrées en salles en France."""
    return f"🎟️ Carton en salles ({format_entrees(f['entrees'])} entrées)"


def _phrase_francais(cat, res, j, f):
    """🇫🇷 Film français."""
    return "🇫🇷 Cinéma français"


# Critère du moteur → fonction qui écrit sa phrase (paramètres : catalogue, résultat, film j, ligne du film).
_PHRASES = {
    "genre": _phrase_genre,
    "epoque": _phrase_epoque,
    "duree": _phrase_duree,
    "histoire": _phrase_histoire,
    "casting": _phrase_casting,
    "realisation": _phrase_realisation,
    "communaute": _phrase_communaute,
    "qualite": _phrase_qualite,
    "popularite": _phrase_popularite,
    "francais": _phrase_francais,
}
