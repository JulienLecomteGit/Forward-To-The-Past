"""Page « Pour toi » (accueil du membre) : bannière puis rubriques de recommandations en grilles de 4
(sélection perso, parce que tu as aimé, tendances, jumeau ciné, décennie, pépites, cinéma français, sagas).

Utilise     : config (affichage), donnees (interactions, membres), interface (barres, cartes, mise_en_page),
              medias (avatars), moteur (recommandation)
Utilisé par : app
"""
from __future__ import annotations

from html import escape

import numpy as np
import streamlit as st

from config.affichage import DECENNIE_LIB, FILMS_PAR_RANGEE
from donnees import interactions, membres
from interface.barres import gouts_html
from interface.cartes import grille
from interface.mise_en_page import banniere, colonnes, section, selon_ecran
from medias import avatars
from moteur.recommandation import pour_toi, similaires
from outils.texte import annee_entre_parentheses


def _melanger():
    """Bouton « Autre sélection » : passe aux 2 rangées suivantes de la sélection."""
    st.session_state["melange"] = st.session_state.get("melange", 0) + 1


def afficher(ctx):
    """Page d'accueil : bannière, puis chaque rubrique l'une sous l'autre (une rubrique vide ne s'affiche pas)."""
    ss, cat, pr, p = st.session_state, ctx.cat, ctx.profil, ctx.p
    genres = _bienvenue(ctx)
    n_ligne = selon_ecran(ctx.mobile, FILMS_PAR_RANGEE)
    perso = pour_toi(cat, pr, p, ctx.comm, n=24)
    if not perso.indices:
        st.info("Ton profil est encore vide : ajoute quelques coups de cœur depuis Explorer !")
        return
    decal = (ss.get("melange", 0) * 2 * n_ligne) % max(1, len(perso.indices))
    selection = (perso.indices[decal:] + perso.indices[:decal])[: 2 * n_ligne]
    _selection_perso(ctx, perso, selection, genres)
    connus = ctx.connus()
    _parce_que_tu_as_aime(ctx, connus, n_ligne)
    _tendances(ctx, connus, n_ligne)
    _jumeau(ctx, connus, n_ligne)
    _tes_annees(ctx, n_ligne)
    _pepites(ctx, n_ligne)
    _cinema_francais(ctx, n_ligne)
    _sagas(ctx, connus, n_ligne)


def _bienvenue(ctx) -> str:
    """Ballons au premier passage, puis bannière. Renvoie les 3 premiers genres déclarés (texte)."""
    ss, m = st.session_state, ctx.membre
    if ss.pop("bienvenue", False):
        st.balloons()
        st.toast(f"Bienvenue à bord, {m['prenom']} ! +50 XP", icon="🚀")
    genres = ", ".join(ctx.prefs.get("genres", [])[:3]) or "à découvrir"
    banniere("Bon retour à <em>88 MPH</em>,", f"{m['prenom']} {m['nom']}".strip(),
             f"Flux calibré sur tes goûts ({escape(genres)}) · Clique sur une jaquette pour ouvrir sa fiche "
             "ou réagis avec ❤️ ➕ 🤮.")
    return genres


def _selection_perso(ctx, perso, selection, genres):
    """🔥 Sélection personnelle + bouton « Autre sélection » (décale la sélection de 2 rangées)."""
    m = ctx.membre
    c1, c2 = colonnes(ctx.mobile, [4, 1], vertical_alignment="bottom")
    with c1:
        section(f"🔥 Sélection 88 MPH — pour {m['prenom']}",
                f"Basée sur tes goûts ({genres}), {len(ctx.inter['like'])} favoris ❤️, {len(ctx.seances)} séances au carnet "
                f"et {len(ctx.inter['dislike'])} film(s) 🤮 écartés.")
        st.html(gouts_html(perso.contexte.get("gouts", []), "Ton flux en ce moment :"))
    with c2:
        st.button("Autre sélection", icon=":material/refresh:", on_click=_melanger, width="stretch")
    grille(ctx.cat, selection, "perso", "reco_accueil", inter=ctx.inter, res=perso)


def _parce_que_tu_as_aime(ctx, connus, n_ligne):
    """💿 Films proches du dernier film aimé."""
    cat, pr, p = ctx.cat, ctx.profil, ctx.p
    if pr.aimes:
        dernier = pr.aimes[-1]
        sim = similaires(cat, dernier, p, ctx.comm, exclure=list(connus - {dernier}), n=n_ligne)
        section(f"💿 Parce que tu as aimé {cat.df.titre[dernier]}{annee_entre_parentheses(cat.annee[dernier])}", "film → films proches")
        grille(cat, sim.indices, "parceque", "reco_accueil", inter=ctx.inter, res=sim)


def _tendances(ctx, connus, n_ligne):
    """📈 Films les plus aimés par les membres ces 30 derniers jours (hors films déjà connus)."""
    cat = ctx.cat
    tend = ctx.comm.tendances(30)
    if connus:
        tend[list(connus)] = 0
    ordre = [int(k) for k in np.argsort(-tend)[:n_ligne] if tend[k] > 0]
    if ordre:
        section("📈 Tendances chez les membres", "les films les plus aimés ces 30 derniers jours")
        grille(cat, ordre, "tendances", "reco_accueil", inter=ctx.inter)


def _jumeau(ctx, connus, n_ligne):
    """Coups de cœur du membre aux goûts les plus proches (« jumeau ciné »)."""
    cat, pr = ctx.cat, ctx.profil
    _, voisins = ctx.comm.membre(pr.aimes, exclure_uid=ctx.uid, k=3)
    if voisins:
        jumeau = membres.membre(voisins[0][0])
        if jumeau:
            tous = [cat.position[t] for t in interactions.interactions(jumeau["id"])["like"] if t in cat.position]
            communs = len(set(tous) & set(pr.aimes))
            leurs = [k for k in tous if k not in connus][:n_ligne]
            if leurs:
                st.html(f'<div class="ft-section"><h3>{avatars.img(jumeau["avatar"], 34, rayon=9)} Les coups de cœur de '
                        f'{escape(jumeau["pseudo"])}</h3><p>Ton jumeau ciné · {communs} film{"s" if communs > 1 else ""} '
                        f'aimé{"s" if communs > 1 else ""} en commun</p></div>')
                grille(cat, leurs, "jumeau", "reco_accueil", inter=ctx.inter)


def _tes_annees(ctx, n_ligne):
    """📼 Le meilleur d'une décennie préférée (change à chaque nouveau film aimé)."""
    cat, pr, p = ctx.cat, ctx.profil, ctx.p
    decs = list(ctx.prefs.get("decennies") or [])
    if not decs and pr.aimes:
        decs = [int(cat.decennie[pr.aimes[-1]])]
    if decs:
        d = decs[len(pr.aimes) % len(decs)]
        res_d = pour_toi(cat, pr, p, ctx.comm, n=n_ligne, filtre=cat.decennie == d)
        section(f"📼 Tes années {DECENNIE_LIB.get(d, d)}", "le meilleur de ta décennie préférée")
        grille(cat, res_d.indices, f"dec{d}", "reco_accueil", inter=ctx.inter, res=res_d)


def _pepites(ctx, n_ligne):
    """💎 Films très bien notés mais peu vus en salles."""
    cat, pr, p = ctx.cat, ctx.profil, ctx.p
    pep = pour_toi(cat, pr, dict(p, popularite=-5.0, qualite=max(p["qualite"], 4.0)), ctx.comm, n=n_ligne,
                   filtre=(cat.qualite > 0.7) & (cat.pop < 0.45))
    section("💎 Pépites méconnues pour toi", "très bien notées, peu vues en salles")
    grille(cat, pep.indices, "pepites", "reco_accueil", inter=ctx.inter, res=pep)


def _cinema_francais(ctx, n_ligne):
    """🇫🇷 Rubrique française, sauf pour les membres qui ont choisi « international »."""
    cat, pr, p = ctx.cat, ctx.profil, ctx.p
    if ctx.prefs.get("origine") != "international":
        fr = pour_toi(cat, pr, dict(p, francais=5.0), ctx.comm, n=n_ligne, filtre=cat.fr)
        section("🇫🇷 Le meilleur du cinéma français", "coup de projecteur CNC")
        grille(cat, fr.indices, "francais", "reco_accueil", inter=ctx.inter, res=fr)


def _sagas(ctx, connus, n_ligne):
    """🔗 Volets non vus des sagas dont le membre a aimé un film."""
    cat, pr = ctx.cat, ctx.profil
    sagas = list(dict.fromkeys(cat.saga[k] for k in pr.aimes if cat.saga[k]))
    suite = [int(k) for s in sagas for k in np.where(cat.saga == s)[0] if k not in connus]
    if suite:
        section("🔗 Sagas à compléter", "d'autres volets des sagas que tu aimes")
        grille(cat, sorted(suite, key=lambda k: (cat.saga[k], cat.annee[k]))[:n_ligne], "sagas", "reco_accueil",
               inter=ctx.inter)
