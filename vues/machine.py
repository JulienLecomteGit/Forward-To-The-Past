"""Machine à remonter le temps : « Tu as aimé… ? », destination année, convecteur temporel.

Utilise     : config (affichage, catalogue, libelles, reglages_moteur), etat (actions, navigation),
              interface (cartes, cartes_membres, graphes, mise_en_page, textes, theme, time_circuits),
              medias (affiches), moteur (explications, recommandation), outils (texte), recherche
Utilisé par : app
"""
from __future__ import annotations

import random
from datetime import datetime
from html import escape

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import recherche
from config.affichage import ANNEE_DE_DEPART, COULEURS_CRITERES, DERNIER_DEPART_DU_FILM, TIRAGE_CONVECTEUR
from config.catalogue import ANNEE_MAX, ANNEE_MIN
from config.libelles import HUMEURS, SAUTS_DANS_LE_TEMPS
from config.reglages_moteur import COMPOSANTES, LIBELLES
from etat.actions import annoncer
from etat.navigation import ouvrir_fiche
from interface.cartes import grille
from interface.cartes_membres import carte_membre_cliquable
from interface.graphes import CONFIG, theme
from interface.mise_en_page import section
from interface.textes import balise_affiche, meta_film, note_txt
from interface.theme import style
from interface.time_circuits import circuits_temps, moment
from medias.affiches import url_affiche
from moteur.explications import pourquoi
from moteur.recommandation import pour_toi, similaires
from outils.texte import annee_entre_parentheses, format_entrees


def afficher(ctx):
    """Page 88 MPH : 3 onglets (Tu as aimé… ?, Destination année, Convecteur temporel)."""
    st.markdown("## ⚡ La machine à remonter le temps")
    t1, t2, t3 = st.tabs(["🔁 Tu as aimé… ?", "🕰️ Destination année", "⚡ Convecteur temporel"])
    with t1:
        _tu_as_aime(ctx)
    with t2:
        _destination(ctx)
    with t3:
        _convecteur(ctx)


def _suggestion(ctx, titre):
    """Remplit le champ avec le film suggéré (bouton d'exemple)."""
    j = recherche.premier(ctx.cat, titre)
    if j is not None:
        st.session_state.mc_film = ctx.cat.df.tconst[j]


def _tu_as_aime(ctx):
    """Onglet « Tu as aimé… ? » : un film choisi → les films proches, avec leur décomposition."""
    cat, ss = ctx.cat, st.session_state
    if "mc_film" not in ss and ctx.profil and ctx.profil.aimes:  # démarre sur le dernier film aimé : la page n'est jamais vide
        ss.mc_film = cat.df.tconst[ctx.profil.aimes[-1]]
    actuel = ss.get("mc_film")
    titre = cat.df.titre[cat.position[actuel]] if actuel in cat.position else ""
    ev = recherche.champ(cat, "mc_rech", "Quel film as-tu aimé ? Tape les premières lettres… ex. Retour vers le futur",
                         mode="film", valeur=titre)
    if ev and ev["type"] == "film":
        ss.mc_film = actuel = ev["tconst"]
    if actuel not in cat.position:
        st.caption("Idées de départ :")
        with st.container(horizontal=True):
            for t in ("Retour vers le futur", "Le Fabuleux Destin d'Amélie Poulain", "Matrix", "Les Visiteurs", "Shining", "Top Gun"):
                st.button(t, key=f"sug_{t}", on_click=_suggestion, args=(ctx, t))
        return
    i = cat.position[actuel]
    masquer = st.toggle("🙈 Masquer les films que j'ai déjà vus", value=True, key="mc_masquer")
    exclure = list(ctx.connus()) if masquer else []
    res = similaires(cat, i, ctx.p, ctx.comm, exclure=[k for k in exclure if k != i])
    f = cat.film(i)
    st.caption(f"Tu as choisi **{f['titre']}**{annee_entre_parentheses(f['annee'])} — voici tes {len(res.indices)} films à découvrir :")
    grille(cat, res.indices, "machine", "reco_machine", res=res, inter=ctx.inter, raisons=True)
    with st.expander("🧠 Comment le moteur a décidé (décomposition des scores)"):
        _graphe_decomposition(cat, res)


def _graphe_decomposition(cat, res):
    """Barres empilées : part de chaque critère dans le score de chaque film proposé."""
    noms = [cat.df.titre[j][:32] for j in res.indices][::-1]
    fig = go.Figure()
    for k, c in zip(COMPOSANTES, COULEURS_CRITERES):
        vals = [max(res.contributions(j)[k], 0) for j in res.indices][::-1]
        if sum(vals) > 0:
            fig.add_bar(y=noms, x=vals, name=LIBELLES.get(k, k), orientation="h", marker_color=c)
    fig.update_layout(barmode="stack", height=170 + 36 * len(noms), xaxis_title="points de score")
    st.plotly_chart(theme(fig), theme=None, config=CONFIG)
    st.caption("Chaque couleur = un critère réglable dans l'espace admin. Modifier un poids change la longueur des barres… et le classement.")


def _sauter(annee):
    """Choisit l'année de destination et l'annonce."""
    ss = st.session_state
    ss.mc_annee = annee
    annoncer(f"1,21 gigowatt ! Arrivée en {annee} ⚡", "🕰️")




def _sauter_hasard():
    """Saut vers une année tirée au hasard dans le catalogue."""
    _sauter(random.randint(ANNEE_MIN, ANNEE_MAX))


def _destination(ctx):
    """Onglet « Destination année » : choix de l'année, films du membre et box-office de l'époque."""
    cat, ss = ctx.cat, st.session_state
    ss.setdefault("mc_annee", ANNEE_DE_DEPART)
    st.caption("Choisis une année : le moteur sélectionne tes films de cette année-là et le box-office France de l'époque.")
    with st.container(key="gmembres_annees", horizontal=True):
        for a, film in SAUTS_DANS_LE_TEMPS.items():
            carte_membre_cliquable(f"saut_{a}", f'<div class="fd-carte{" actif" if ss.mc_annee == a else ""}"><div class="fd-annee">{a}</div>'
                                      f'<div class="fd-film">{film}</div></div>', f"Aller en {a}", _sauter, (a,))
        carte_membre_cliquable("saut_alea", '<div class="fd-carte hasard"><div class="fd-annee">🎲</div><div class="fd-film">Au hasard</div></div>',
                                  "Saut aléatoire", _sauter_hasard, ())
    st.slider("Ou règle l'année de destination", ANNEE_MIN, ANNEE_MAX, key="mc_annee")
    y = ss.mc_annee
    filtre = cat.annee == y
    n = 4
    res = pour_toi(cat, ctx.profil, dict(ctx.p, masquer_vus=False), ctx.comm, n=2 * n, filtre=filtre)
    section(f"🎯 Tes films de {y}", "choisis selon ton profil")
    grille(cat, res.indices, f"annee{y}", "reco_machine", inter=ctx.inter, res=res)
    top = np.where(filtre)[0]
    top = top[np.argsort(-cat.entrees[top])][:n]
    section(f"🎟️ Ce que la France allait voir en {y}", "box-office France de l'année")
    grille(cat, top.tolist(), f"box{y}", "reco_machine", inter=ctx.inter)


def _moment_film(annee: int, maintenant: datetime) -> dict:
    """Date de l'affichage transposée dans l'année du film (29 février ramené au 28)."""
    jour = min(maintenant.day, 28) if maintenant.month == 2 else maintenant.day
    return moment(annee, maintenant.month, jour, maintenant.hour, maintenant.minute)


def _lancer(ctx, genres):
    """Tire un film parmi les meilleures recommandations (filtrées par l'humeur) et prépare l'animation."""
    ss, cat = st.session_state, ctx.cat
    res = pour_toi(cat, ctx.profil, ctx.p, ctx.comm, n=TIRAGE_CONVECTEUR,
                          filtre=np.isin(cat.df["genre"].to_numpy(), genres) if genres else None)
    if not res.indices:
        return
    j = random.choice(res.indices)
    maintenant = datetime.now()
    annee = int(cat.annee[j]) if cat.annee[j] == cat.annee[j] else maintenant.year
    ss.roue = j
    ss.cv_circuits = {  # comme dans le film : on part d'aujourd'hui ; le dernier départ connu est le 26 octobre 1985, 1 h 21
        "dest": _moment_film(annee, maintenant),
        "depart": moment(maintenant.year, maintenant.month, maintenant.day, maintenant.hour, maintenant.minute),
        "precedent": (ss.get("cv_circuits") or {}).get("depart") or moment(*DERNIER_DEPART_DU_FILM),
    }
    ss.cv_anim = True
    ss.cv_n = ss.get("cv_n", 0) + 1


def _flux_html() -> str:
    """Convecteur temporel (« flux capacitor ») : boîtier vissé, vitre, trois tubes en Y avec capots et nœud lumineux."""
    bras = "".join(f'<i class="cv-bras b{k}"><span class="cv-tube"><b></b></span><span class="cv-bague"></span>'
                   f'<span class="cv-capot"></span><span class="cv-fil"></span></i>' for k in (1, 2, 3))
    return (f'<div class="cv-boite" role="img" aria-label="Convecteur temporel"><div class="cv-vitre">{bras}'
            f'<span class="cv-noeud"></span><span class="cv-onde"></span></div><div class="cv-plaque">CONVECTEUR TEMPOREL</div></div>')


def _panneau_convecteur(circuits: dict, anim: bool, n: int, film: dict) -> str:
    """Panneau Time Circuits (3 afficheurs) avec la jaquette et le titre du film tiré."""
    led = circuits_temps([
        {"couleur": "r", "plaque": "DESTINATION TIME", "apres": circuits["dest"], "saisie": anim},
        {"couleur": "v", "plaque": "PRESENT TIME", "avant": circuits["depart"], "apres": circuits["dest"]},
        {"couleur": "a", "plaque": "LAST TIME DEPARTED", "avant": circuits["precedent"], "apres": circuits["depart"]},
    ], tape=anim)
    reals = ", ".join(film["real_noms"][:1])
    url = url_affiche(film["affiche"], "w342")
    img = balise_affiche(url, film["titre"], paresseuse=False)
    billet = (f'<div class="cv-billet"><div class="cv-affiche">{img}<div class="cv-mystere"><span>?</span></div></div>'
              f'<div class="cv-pile"><div class="cv-calcul"><div class="cv-sur">CALCUL DE LA TRAJECTOIRE…</div>'
              f'<div class="cv-barres"><i></i><i></i><i></i><i></i><i></i></div></div>'
              f'<div class="cv-arrivee"><div class="cv-sur">DESTINATION ATTEINTE</div><div class="cv-titre">{escape(film["titre"])}</div>'
              f'<div class="cv-sous">{escape(meta_film(film))}{" · " + escape(reals) if reals else ""}</div>'
              f'<div class="cv-note">⭐ {note_txt(film["note"]) or "—"} · 🎟️ {format_entrees(film["entrees"])} entrées</div>'
              f'<div class="cv-ouvrir"><span>▶ Ouvrir la fiche</span></div></div></div></div>')
    haut = ('<div class="cv-haut"><div class="cv-vitesse"><span class="cv-mph"></span><small>MPH</small></div>'
            '<div class="cv-jauge"><i></i><span style="left:0">0</span><span style="left:50%">44</span><span style="left:100%">88</span></div>'
            '<div class="cv-giga">⚡ 1,21 GIGOWATTS</div></div>')
    # le numéro de tirage rend le HTML unique : l'animation repart à chaque lancement
    return (f'<div class="cv {"anim" if anim else "fixe"}" data-tirage="{n}">{haut}<div class="cv-bas">'
            f'<div class="cv-flux">{_flux_html()}</div>{led}{billet}</div>'
            f'<div class="cv-lignes"></div><div class="cv-flash"></div><div class="cv-feu"><i></i><i></i></div></div>')


def _convecteur(ctx):
    """Onglet « Convecteur temporel » : humeur, bouton de lancement, panneau et fiche du film tiré."""
    ss, cat = st.session_state, ctx.cat
    st.caption("Pas d'idée pour ce soir ? Choisis une humeur et lance le convecteur : à 88 MPH, il t'envoie vers un film "
               f"tiré au sort parmi tes {TIRAGE_CONVECTEUR} meilleures recos.")
    humeur = st.pills("Ton humeur", list(HUMEURS), key="mc_humeur", label_visibility="collapsed")
    genres = HUMEURS.get(humeur, [])
    st.button("Lancer le convecteur temporel", icon=":material/bolt:", type="primary", on_click=_lancer, args=(ctx, genres),
              width="stretch")
    if ss.get("roue") is None or not ss.get("cv_circuits"):
        return
    j = ss.roue
    anim = ss.pop("cv_anim", False)
    n = ss.get("cv_n", 0)
    annee = int(ss.cv_circuits["dest"]["a"])
    film = cat.film(j)
    with st.container(key="cv_zone"):  # bouton invisible posé sur la jaquette et le titre : un clic ouvre la fiche
        st.html(_panneau_convecteur(ss.cv_circuits, anim, n, film))
        st.button(f"Ouvrir la fiche de {film['titre']}", key="cv_ouvrir", on_click=ouvrir_fiche, args=(film["tconst"], "reco_machine"))
    if anim:  # le résultat n'apparaît qu'après l'arrivée à 88 MPH (nom d'animation unique par tirage)
        style(f"@keyframes cv-res-{n}{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:none}}}}"
                 f".st-key-cv_resultat{{animation:cv-res-{n} .7s ease 3.3s both}}"
                 f"@media (prefers-reduced-motion:reduce){{.st-key-cv_resultat{{animation:none}}}}")
    with st.container(key="cv_resultat"):
        res = pour_toi(cat, ctx.profil, ctx.p, ctx.comm, n=1)
        section(f"⚡ Destination {annee} : {cat.df.titre[j]}", " · ".join(pourquoi(cat, res, j, 3)))
        suite = similaires(cat, j, ctx.p, ctx.comm, exclure=list(ctx.connus()), n=3)
        grille(cat, [j] + suite.indices, "roue", "reco_machine", inter=ctx.inter, res=res)
        st.caption("Le premier film est ta destination ; les trois suivants prolongent la soirée.")
