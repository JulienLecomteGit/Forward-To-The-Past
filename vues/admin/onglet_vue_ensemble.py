"""Espace admin › onglet 📊 Vue d'ensemble : 6 indicateurs clés et 9 graphiques sur les membres.

Utilise     : config (affichage, donnees, libelles), interface (graphes, mise_en_page, tuiles), medias (avatars),
              outils (texte), vues/admin (chargement)
Utilisé par : vues (admin)
"""
from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.affichage import CONTOUR_PARTS, DEGRADE_CHALEUR, ROSE, ROSE_PALE, TURQUOISE, VIOLET
from config.donnees import TRANCHES_AGE
from config.libelles import JOURS_SEMAINE
from interface.graphes import CONFIG, NEON, theme
from interface.mise_en_page import colonnes, section
from interface.tuiles import tuile_kpi
from medias import avatars
from outils.texte import nombre_fr
from vues.admin import chargement


def afficher(ctx, d0):
    """Onglet complet : interrupteur « membres fictifs », 6 indicateurs puis les graphiques, rangée par rangée."""
    cat = ctx.cat
    fictifs = st.toggle("Inclure les membres fictifs (données de démo)", value=True, key="adm_fictifs")
    d = chargement.filtrer(d0, fictifs)
    m, i, e = d["membres"], d["inter"], d["evts"]
    if not len(m):
        st.info("Aucun membre réel pour l'instant : inscris-toi pour voir apparaître tes premières statistiques !")
        return
    cnx = e[e.type == "connexion"]
    likes = i[i.type == "like"]
    fiches = _fiches_ouvertes(e)
    _indicateurs(m, i, cnx, likes, fiches, d["seances"])

    g, dr = colonnes(ctx.mobile, 2, gap="large")
    with g:
        _graphe_croissance(m)
    with dr:
        _graphe_connexions(cnx)

    g, dr = colonnes(ctx.mobile, 2, gap="large")
    with g:
        _graphe_genres(cat, d, likes)
    with dr:
        _graphe_top_films(cat, likes)

    c1, c2, c3 = colonnes(ctx.mobile, 3, gap="large")
    with c1:
        _graphe_ages(m)
    with c2:
        _graphe_origines(fiches)
    with c3:
        _graphe_villes(m)

    c1, c2 = colonnes(ctx.mobile, [1.2, 1])
    with c1:
        _avatars_preferes(m)
    with c2:
        _top_recherches(e)


def _tracer(fig, hauteur):
    """Affiche un graphique avec le thème néon, à la hauteur demandée."""
    st.plotly_chart(theme(fig, hauteur), theme=None, config=CONFIG)


def _fiches_ouvertes(e):
    """Événements « fiche ouverte » avec une colonne origine (reco_accueil, recherche…)."""
    fiches = e[e.type == "fiche"].copy()
    fiches["origine"] = fiches.detail.map(lambda s: json.loads(s).get("origine", "") if isinstance(s, str) and s.startswith("{") else "")
    return fiches


def _indicateurs(m, i, cnx, likes, fiches, seances):
    """Les 6 tuiles du haut, avec leur évolution sur 7 jours."""
    now = pd.Timestamp.now()
    s7, s14 = now - pd.Timedelta(days=7), now - pd.Timedelta(days=14)
    actifs7, actifs_prec = cnx[cnx.date >= s7].uid.nunique(), cnx[(cnx.date >= s14) & (cnx.date < s7)].uid.nunique()
    nouv7 = (m.date_inscription >= s7).sum()
    taux_reco = fiches.origine.str.startswith("reco").mean() if len(fiches) else 0
    notes = i[i.type == "note"].valeur
    sea7 = int((pd.to_datetime(seances.date_seance, errors="coerce") >= s7.normalize()).sum()) if len(seances) else 0
    ton = lambda v: "hausse" if v > 0 else ("baisse" if v < 0 else "neutre")  # noqa: E731
    kpis = [("👥 Membres", nombre_fr(len(m)), f"+{nouv7} en 7 j", ton(nouv7), "Membres inscrits (nouveaux sur 7 jours)"),
            ("🔥 Actifs 7 j", nombre_fr(actifs7), f"{actifs7 - actifs_prec:+d} vs sem. préc.", ton(actifs7 - actifs_prec),
             "Membres connectés au moins une fois ces 7 derniers jours"),
            ("❤️ J'aime", nombre_fr(len(likes)), f"+{int((likes.date >= s7).sum())} en 7 j", ton(int((likes.date >= s7).sum())), "Coups de cœur donnés"),
            ("🎟️ Séances", nombre_fr(len(seances)), f"+{sea7} en 7 j", ton(sea7), "Séances notées dans les carnets des membres"),
            ("⭐ Note moyenne", f"{notes.mean():.2f}".replace(".", ",") if len(notes) else "—", f"sur {nombre_fr(len(notes))} notes", "neutre",
             "Moyenne des notes laissées par les membres"),
            ("🎯 Via une reco", f"{taux_reco:.0%}".replace("%", " %"), f"de {nombre_fr(len(fiches))} fiches ouvertes", "neutre",
             "Part des fiches ouvertes depuis une recommandation")]
    with st.container(key="gmembres_kpi", horizontal=True):
        for lab, val, sous, tn, aide in kpis:
            st.html(tuile_kpi(lab, val, sous, tn, aide))


def _graphe_croissance(m):
    """Croissance : barres hebdomadaires + total cumulé."""
    ins = m.set_index("date_inscription").sort_index().assign(n=1).n.resample("W-MON", label="left", closed="left").sum()
    fig = go.Figure()
    fig.add_bar(x=ins.index, y=ins.values, name="Nouveaux membres (semaine)", marker_color=VIOLET,
                hovertemplate="Semaine du %{x|%d/%m} : %{y} inscrits<extra></extra>")
    fig.add_scatter(x=ins.index, y=ins.cumsum(), name="Total des membres", yaxis="y2", mode="lines+markers",
                    line=dict(color=ROSE, width=3), marker=dict(size=5),
                    hovertemplate="Total au %{x|%d/%m} : %{y}<extra></extra>")
    fig.update_layout(title="Croissance des inscriptions",
                      yaxis=dict(title="par semaine"), xaxis=dict(tickformat="%b %Y"),
                      yaxis2=dict(title="total", overlaying="y", side="right", showgrid=False, automargin=True,
                                  tickfont=dict(size=12, color=ROSE_PALE), title_font=dict(size=12, color=ROSE_PALE)))
    _tracer(fig, 360)


def _graphe_connexions(cnx):
    """Activité : carte de chaleur heure × jour des connexions."""
    if len(cnx):
        heures = list(range(7, 24))
        h = (cnx.assign(j=cnx.date.dt.dayofweek, h=cnx.date.dt.hour)
             .pivot_table(index="j", columns="h", values="uid", aggfunc="count", fill_value=0)
             .reindex(index=range(7), columns=heures, fill_value=0))
        fig = go.Figure(go.Heatmap(z=h.values, x=[f"{k}h" for k in heures], y=JOURS_SEMAINE, xgap=2, ygap=2,
                                   colorscale=DEGRADE_CHALEUR,
                                   showscale=False, hovertemplate="%{y} à %{x} : %{z} connexions<extra></extra>"))
        fig.update_layout(title="Quand les membres se connectent")
        fig.update_yaxes(autorange="reversed", showgrid=False)
        fig.update_xaxes(showgrid=False, dtick=2)
        _tracer(fig, 360)


def _graphe_genres(cat, d, likes):
    """Genres déclarés à l'inscription vs réellement aimés."""
    decl = pd.Series([x for s in d["prefs"].genres for x in json.loads(s)]).value_counts(normalize=True)
    pos = likes.tconst.map(cat.position).dropna().astype(int)
    reel = pd.Series(cat.df.genre.to_numpy()[pos]).value_counts(normalize=True)
    comp = (pd.DataFrame({"Déclarés": decl, "Aimés": reel}).fillna(0).sort_values("Aimés").tail(12))
    fig = go.Figure()
    fig.add_bar(y=comp.index, x=comp["Déclarés"], name="Déclarés à l'inscription", orientation="h", marker_color=TURQUOISE,
                hovertemplate="%{y} : %{x:.0%} des genres déclarés<extra></extra>")
    fig.add_bar(y=comp.index, x=comp["Aimés"], name="Réellement aimés", orientation="h", marker_color=ROSE,
                hovertemplate="%{y} : %{x:.0%} des j'aime<extra></extra>")
    fig.update_layout(title="Genres : ce qu'ils déclarent vs ce qu'ils aiment", barmode="group", bargap=.3,
                      xaxis_tickformat=".0%")
    _tracer(fig, 540)


def _graphe_top_films(cat, likes):
    """Top 10 des films les plus aimés (titres coupés à 32 caractères)."""
    top = likes.tconst.value_counts().head(10)
    noms = [(cat.df.titre[cat.position[t]] if t in cat.position else t) for t in top.index]
    noms = [n if len(n) <= 32 else n[:31] + "…" for n in noms]
    fig = go.Figure(go.Bar(y=noms[::-1], x=top.values[::-1], orientation="h", marker_color=ROSE,
                           text=top.values[::-1], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y} : %{x} j'aime<extra></extra>"))
    fig.update_layout(title="Top 10 des films les plus aimés", xaxis=dict(showgrid=False, showticklabels=False))
    _tracer(fig, 540)


def _graphe_ages(m):
    """Barres du nombre de membres par tranche d'âge."""
    ages = m.tranche_age.value_counts().reindex(TRANCHES_AGE, fill_value=0)
    fig = go.Figure(go.Bar(x=[a.replace(" ans", "") for a in ages.index], y=ages.values, marker_color=VIOLET,
                           text=ages.values, textposition="outside", cliponaxis=False,
                           hovertemplate="%{x} ans : %{y} membres<extra></extra>"))
    fig.update_layout(title="Tranches d'âge", yaxis=dict(showticklabels=False, showgrid=False), xaxis_title="ans")
    _tracer(fig, 340)


def _graphe_origines(fiches):
    """D'où viennent les fiches ouvertes (anneau)."""
    o = fiches.origine.replace({"reco_accueil": "Reco accueil", "reco_machine": "Machine", "reco_fiche": "Reco fiche",
                                "recherche": "Recherche", "explorer": "Explorer", "ma_liste": "Ma liste", "": "Autre"}).value_counts()
    fig = go.Figure(go.Pie(labels=o.index, values=o.values, hole=.6, sort=True, textinfo="percent", textposition="inside",
                           insidetextorientation="horizontal", marker=dict(colors=NEON, line=dict(color=CONTOUR_PARTS, width=2)),
                           hovertemplate="%{label} : %{value} fiches (%{percent})<extra></extra>"))
    fig.update_layout(title="D'où viennent les fiches ouvertes", uniformtext=dict(minsize=11, mode="hide"),
                      legend=dict(orientation="h", y=-0.05))
    _tracer(fig, 340)


def _graphe_villes(m):
    """Les 8 villes qui comptent le plus de membres."""
    villes = m.ville.replace("", "Non renseignée").value_counts().head(8)
    fig = go.Figure(go.Bar(y=villes.index[::-1], x=villes.values[::-1], orientation="h", marker_color=TURQUOISE,
                           text=villes.values[::-1], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y} : %{x} membres<extra></extra>"))
    fig.update_layout(title="Top villes", xaxis=dict(showgrid=False, showticklabels=False))
    _tracer(fig, 340)


def _avatars_preferes(m):
    """Avatars choisis par les membres, du plus au moins populaire."""
    section("Avatars préférés", "le panel le plus populaire")
    av = m.avatar.value_counts()
    st.html('<div style="display:flex;flex-wrap:wrap;gap:10px">' + "".join(
        f'<div style="text-align:center">{avatars.img(k, 58)}<div class="ft-petit">{n}</div></div>' for k, n in av.items()) + "</div>")


def _top_recherches(e):
    """Les 10 recherches les plus tapées."""
    section("Top recherches", "ce que les membres tapent")
    r = e[e.type == "recherche"].detail.str.strip().str.lower().value_counts().head(10)
    st.dataframe(r.rename_axis("Recherche").rename("Nombre").to_frame(), width="stretch", height=300)
