"""Les deux modes du moteur. « Tu as aimé X ? » (similaires : film → films proches) et « Pour toi » (pour_toi :
membre → films). Chaque critère vaut entre 0 et 1 ; les réglages de l'admin sont des poids (0 à 10).

Utilise     : config (reglages_moteur), donnees (catalogue), moteur (communaute, profil_membre, selection),
              outils (calcul)
Utilisé par : moteur (evaluation, explications), vues (accueil, auth, explorer, fiche, machine),
              vues/admin (onglet_membres, onglet_reglages, simulation)
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config.reglages_moteur import COMPOSANTES, DECENNIES, FORMATS_DUREE
from donnees.catalogue import Catalogue
from moteur.communaute import Communaute
from moteur.profil_membre import Profil, gouts, poids_recence
from moteur.selection import selectionner
from outils.calcul import proximite, ramener_entre_0_et_1


@dataclass
class Resultat:
    """Résultat d'une recommandation : films choisis, score de chaque film du catalogue, valeur de chaque critère
    (composantes) et poids utilisés — de quoi expliquer chaque choix.
    """
    indices: list[int]
    scores: np.ndarray
    composantes: dict
    poids: dict
    mode: str  # "film" ou "membre"
    source: int | None = None
    contexte: dict = field(default_factory=dict)

    def score_100(self, j: int) -> int:
        """Score du film j ramené sur 100 (plafonné à 99) pour l'affichage."""
        maxi = sum(abs(w) for k, w in self.poids.items() if k not in ("popularite",) and w > 0) + abs(self.poids.get("popularite", 0))
        return int(np.clip(round(100 * self.scores[j] / maxi), 0, 99)) if maxi else 0

    def contributions(self, j: int) -> dict:
        """Part de chaque critère dans le score du film j (poids × valeur du critère)."""
        return {k: float(self.poids.get(k, 0) * self.composantes[k][j]) for k in self.composantes}


def credit_commun(ids, index, tailles, poids=None) -> np.ndarray:
    """Bonus de chaque film selon les personnes (acteurs ou réalisateurs) qu'il partage avec la liste `ids` ;
    une personne présente dans beaucoup de films compte moins.
    """
    bonus = np.zeros(len(tailles))
    for personne in ids:
        films = index.get(personne)
        if films is None:
            continue
        w = poids[personne] if poids is not None else 1
        bonus[films] += w / np.sqrt(len(ids) * np.maximum(tailles[films], 1))
    return bonus


def similaires(cat: Catalogue, i: int, p: dict, comm: Communaute | None = None, exclure=(), n=None) -> Resultat:
    """« Tu as aimé X ? » : note chaque film selon sa ressemblance avec le film i, puis sélectionne."""
    comp = {
        "genre": ((cat.genre_code == cat.genre_code[i]) & (cat.genre_code[i] >= 0)).astype(float),
        "epoque": proximite(cat.annee, cat.annee[i], p["tolerance"]),
        "duree": proximite(cat.duree, cat.duree[i], 60),
        "histoire": ramener_entre_0_et_1(cat.sim_resume(i), exclure=i),
        "casting": ramener_entre_0_et_1(credit_commun(cat.acteurs[i], cat.index_acteurs, cat.tailles_acteurs, cat.poids_acteur), exclure=i),
        "realisation": ramener_entre_0_et_1(credit_commun(cat.real[i], cat.index_real, cat.tailles_real), exclure=i),
        "communaute": ramener_entre_0_et_1(comm.item(i), exclure=i) if comm else np.zeros(cat.n),
        "qualite": cat.qualite,
        "popularite": (cat.pop - 0.5) * 2,
        "francais": cat.fr.astype(float),
    }
    poids = {k: float(p.get(k, 0)) for k in COMPOSANTES}
    score = sum(poids[k] * comp[k] for k in COMPOSANTES)
    choix = selectionner(cat, score, p, exclure=exclure, source=i, n=n)
    return Resultat(choix, score, comp, poids, "film", source=i)


def pour_toi(cat: Catalogue, pr: Profil, p: dict, comm: Communaute | None = None, n=None, filtre=None,
             exclure_liste=True) -> Resultat:
    """« Pour toi » : chaque critère donne une note entre 0 et 1 à chaque film pour ce membre ; le score est
    leur somme pondérée par les réglages de l'admin, puis selectionner choisit les films à montrer."""
    wd, wh = float(p["declare"]), float(p["historique"])
    rec = float(p.get("recence", 0))
    aimes = np.array(pr.aimes, dtype=int)
    sig = np.array(pr.signaux, dtype=int)                       # aimés + « à voir »
    w = np.asarray(pr.force, float) * poids_recence(pr.dates, rec)  # récents et 5★ pèsent plus
    neg = np.array(pr.detestes, dtype=int)
    wn = poids_recence(pr.dates_neg, rec)
    ctx = {}
    comp_genre, cible = _critere_genre(cat, pr, p, ctx)
    comp_epoque = _critere_epoque(cat, pr, sig, w, wd, wh)
    comp_duree = _critere_duree(cat, pr, sig, wd, wh)
    comp_histoire, penalite = _critere_histoire(cat, sig, w, neg, wn, ctx)
    comp_casting, comp_real = _criteres_casting_realisation(cat, sig, w, ctx)
    comp_comm = _critere_communaute(cat, pr, comm, aimes, w, ctx)
    exclus_norm = sig if len(sig) else None
    comp = {"genre": comp_genre, "epoque": comp_epoque, "duree": comp_duree, "histoire": comp_histoire,
            "casting": ramener_entre_0_et_1(comp_casting, exclure=exclus_norm),
            "realisation": ramener_entre_0_et_1(comp_real, exclure=exclus_norm),
            "communaute": comp_comm, "qualite": cat.qualite, "popularite": (cat.pop - 0.5) * 2,
            "francais": cat.fr.astype(float)}
    poids = _poids_du_membre(p, pr, wd)
    score = sum(poids[k] * comp[k] for k in COMPOSANTES) - 0.6 * poids["histoire"] * penalite
    exclure = _films_a_exclure(pr, p, exclure_liste)
    choix = selectionner(cat, score, p, exclure=list(exclure), n=n, filtre=filtre, cible=cible)
    return Resultat(choix, score, comp, poids, "membre", contexte=ctx)


def _melange(decl, hist, wd: float, wh: float, sig):
    """Mélange « ce que le membre a déclaré » et « ce qu'il a fait » selon les poids de l'admin.
    Sans aucun film aimé ou à voir, seul le déclaré compte."""
    if not len(sig):
        return decl
    return (wd * decl + wh * hist) / ((wd + wh) or 1.0)


def _critere_genre(cat: Catalogue, pr: Profil, p: dict, ctx: dict) -> tuple:
    """Genres : répartition des goûts (déclarés + signaux pondérés − rejets). Renvoie (critère, cible de diversité)."""
    repartition = gouts(cat, pr, p)
    g_aff = repartition / repartition.max() if repartition.max() > 0 else repartition
    comp_genre = np.where(cat.genre_code >= 0, g_aff[np.maximum(cat.genre_code, 0)], 0)
    cible = {k: float(v) for k, v in enumerate(repartition) if v >= 0.06}
    tot_c = sum(cible.values())
    cible = {k: v / tot_c for k, v in cible.items()} if tot_c else {}
    ctx["gouts"] = sorted(((cat.genres[k], v) for k, v in cible.items()), key=lambda x: -x[1])
    return comp_genre, cible


def _critere_epoque(cat: Catalogue, pr: Profil, sig, w, wd: float, wh: float):
    """Décennies : déclarées (+ voisines à moitié) + signaux pondérés."""
    d_decl = {d: 0.0 for d in DECENNIES}
    for d in pr.decennies:
        for dd, wdd in ((d, 1.0), (d - 10, 0.4), (d + 10, 0.4)):
            if dd in d_decl:
                d_decl[dd] = max(d_decl[dd], wdd)
    d_hist = {d: 0.0 for d in DECENNIES}
    if len(sig):
        comptes = pd.Series(w).groupby(cat.decennie[sig]).sum()
        for d, c in comptes.items():
            if d in d_hist:
                d_hist[d] = c / comptes.max()
    d_aff = {d: _melange(d_decl[d], d_hist[d], wd, wh, sig) for d in DECENNIES}
    return np.array([d_aff.get(d, 0) for d in cat.decennie])


def _critere_duree(cat: Catalogue, pr: Profil, sig, wd: float, wh: float):
    """Durée : format déclaré et durée médiane des films aimés."""
    if pr.format_duree in FORMATS_DUREE:
        cible_d, tol = FORMATS_DUREE[pr.format_duree]
        decl = proximite(cat.duree, cible_d, tol)
    else:
        decl = np.zeros(cat.n)
    hist = proximite(cat.duree, float(np.nanmedian(cat.duree[sig])), 40) if len(sig) else decl
    return _melange(decl, hist, wd, wh, sig) if (pr.format_duree in FORMATS_DUREE or len(sig)) else np.zeros(cat.n)


def _critere_histoire(cat: Catalogue, sig, w, neg, wn, ctx: dict) -> tuple:
    """Histoire : proche d'un film aimé (le plus récent pèse plus) et éloigné des films rejetés.
    Renvoie (critère, pénalité de ressemblance aux films rejetés)."""
    if len(sig):
        S = (cat.tfidf[sig] @ cat.tfidf.T).toarray() * w[:, None]
        S[:, sig] = 0
        comp_histoire = ramener_entre_0_et_1(S.max(axis=0))
        ctx["graine_histoire"] = sig[S.argmax(axis=0)]
    else:
        comp_histoire = np.zeros(cat.n)
    penalite = np.zeros(cat.n)
    if len(neg):
        penalite = ((cat.tfidf[neg] @ cat.tfidf.T).toarray() * wn[:, None]).max(axis=0)
    return comp_histoire, penalite


def _criteres_casting_realisation(cat: Catalogue, sig, w, ctx: dict) -> tuple:
    """Casting / réalisation : personnes présentes dans les films aimés (valeurs brutes, normalisées ensuite)."""
    poids_act, poids_real = defaultdict(float), defaultdict(float)
    for j, wj in zip(sig, w):
        for a in cat.acteurs[j]:
            poids_act[a] += cat.poids_acteur.get(a, 0) * wj
        for r in cat.real[j]:
            poids_real[r] += wj
    comp_casting, comp_real = np.zeros(cat.n), np.zeros(cat.n)
    for a, wa in poids_act.items():
        films = cat.index_acteurs[a]
        comp_casting[films] += wa / np.sqrt(np.maximum(cat.tailles_acteurs[films], 1))
    for r, wr in poids_real.items():
        films = cat.index_real[r]
        comp_real[films] += wr / np.sqrt(np.maximum(cat.tailles_real[films], 1))
    ctx["poids_act"], ctx["poids_real"] = poids_act, poids_real
    return comp_casting, comp_real


def _critere_communaute(cat: Catalogue, pr: Profil, comm: Communaute | None, aimes, w, ctx: dict):
    """Communauté : membres aux goûts proches (les j'aime récents comptent plus)."""
    if comm is not None and len(aimes):
        brut, voisins = comm.membre(aimes, exclure_uid=pr.uid, poids=w[:len(aimes)])
        brut[aimes] = 0
        comp_comm = ramener_entre_0_et_1(brut)
        ctx["voisins"] = voisins
    else:
        comp_comm = np.zeros(cat.n)
    return comp_comm


def _poids_du_membre(p: dict, pr: Profil, wd: float) -> dict:
    """Poids de l'admin, ajustés par le style et l'origine choisis à l'inscription (ligne éditoriale du membre)."""
    poids = {k: float(p.get(k, 0)) for k in COMPOSANTES}
    poids["popularite"] += {"cultes": 3.0, "pepites": -3.0}.get(pr.style, 0) * wd / 5
    poids["qualite"] += (2.0 if pr.style == "pepites" else 0) * wd / 5
    poids["francais"] += {"francais": 4.0, "international": -2.0}.get(pr.origine, 0) * wd / 5
    return poids


def _films_a_exclure(pr: Profil, p: dict, exclure_liste: bool) -> set:
    """Films déjà aimés, rejetés, vus (si l'admin les masque) et, au besoin, déjà dans la liste du membre."""
    exclure = set(pr.aimes) | set(pr.detestes) | (pr.vus if p.get("masquer_vus", True) else set())
    if exclure_liste:
        exclure |= pr.liste
    return exclure
