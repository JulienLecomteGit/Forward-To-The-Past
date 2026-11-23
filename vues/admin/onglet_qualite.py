"""Espace admin › onglet 🧪 Qualité du moteur : test hors-ligne (on cache 20 % des films aimés), scores,
graphique, exemple concret pour un membre, puis simulation « le membre a-t-il la main ? ».

Utilise     : config (affichage, reglages_moteur), donnees (base, interactions, membres), etat (cache),
              interface (graphes, jaquettes, mise_en_page, tuiles), medias (avatars), moteur (evaluation),
              vues/admin (onglet_reglages, simulation)
Utilisé par : vues (admin)
"""
from __future__ import annotations

from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config.affichage import AMBRE, COULEURS_METHODES, GRIS_LILAS, JAQUETTES_PAR_RANGEE_ADMIN, ROSE, TURQUOISE
from config.reglages_moteur import PARAMS_DEFAUT
from donnees import base, interactions, membres
from etat.cache import parametres
from interface.graphes import CONFIG, theme
from interface.jaquettes import jaquettes
from interface.mise_en_page import colonnes, section, selon_ecran
from interface.tuiles import tuile_score
from medias import avatars
from moteur.evaluation import evaluer
from vues.admin import simulation
from vues.admin.onglet_reglages import lire_brouillon


def afficher(ctx):
    """Onglet 🧪 Qualité : explication en 3 étapes, test du moteur, résultats et exemple concret."""
    ss = st.session_state
    cat = ctx.cat
    section("🧪 Le moteur est-il bon ?", "on le teste comme en data science : sur des films que le moteur n'a pas le droit de voir")
    with st.container(key="qetapes", horizontal=True):
        for num, titre, texte in (("ÉTAPE 1", "🙈 On cache", "20 % des films aimés de chaque membre testé sont retirés de son profil."),
                                  ("ÉTAPE 2", "🤖 On recommande", "Le moteur calcule sa sélection sans connaître ces films cachés."),
                                  ("ÉTAPE 3", "✅ On compte", "Un film caché qui réapparaît dans la sélection = le moteur a deviné juste."),
                                  ("COMPARAISON", "⚖️ On compare", "Même exercice avec « les plus populaires » et « au hasard ».")):
            st.html(f'<div class="ad-etape"><div class="num">{num}</div><h4>{titre}</h4><p>{texte}</p></div>')
    with st.container(key="adcarte_qualite"):
        c1, c2, c3 = colonnes(ctx.mobile, [1, 1, 1.2], meme_conteneur=True, vertical_alignment="bottom")
        k = c1.slider("Taille de la sélection (k)", 5, 20, 10, key="q_k")
        nb = c2.slider("Membres testés", 20, 180, 80, step=10, key="q_nb")
        if c3.button("Lancer le test : enregistrés vs brouillon", icon=":material/science:", type="primary", width="stretch"):
            with st.spinner("Évaluation en cours… le convecteur temporel chauffe 🔁"):
                lignes = interactions.toutes_interactions()
                prefs = {r["utilisateur_id"]: membres.preferences(r["utilisateur_id"]) for r in base.requete("SELECT utilisateur_id FROM preferences")}
                a, exemples = evaluer(cat, lignes, prefs, parametres(), k=k, nb_max=nb, details=True)
                b = evaluer(cat, lignes, prefs, dict(PARAMS_DEFAUT, **lire_brouillon()), k=k, nb_max=nb)
                a.loc[a.Méthode.str.startswith("Moteur"), "Méthode"] = "Moteur · réglages enregistrés"
                b = b[b.Méthode.str.startswith("Moteur")].assign(Méthode="Moteur · brouillon")
                ss.q_res = pd.concat([a.iloc[:1], b, a.iloc[1:]], ignore_index=True)
                ss.q_ex = exemples
    res = ss.get("q_res")
    if res is not None:
        col_t = [c for c in res.columns if c.startswith("Taux")][0]
        col_p = [c for c in res.columns if c.startswith("Précision")][0]
        col_r = [c for c in res.columns if c.startswith("Rappel")][0]
        with st.container(key="qtuiles", horizontal=True):
            for _, r in res.iterrows():
                st.html(tuile_score(COULEURS_METHODES.get(r.Méthode, GRIS_LILAS), r.Méthode, f"{r[col_t]:.0%}",
                                    '<div class="ft-petit">des membres : au moins 1 film caché retrouvé</div>',
                                    f'<div class="ft-petit" style="margin-top:.35rem">précision {r[col_p]:.0%} · rappel {r[col_r]:.0%} · '
                                    f'{r["Genres différents / sélection"]:.1f} genres / sélection</div>'))
        fig = go.Figure()
        for nom_c, couleur in ((col_p, ROSE), (col_r, TURQUOISE), ("Couverture catalogue", AMBRE)):
            fig.add_bar(x=res.Méthode, y=res[nom_c], name=nom_c.split(" @")[0], marker_color=couleur,
                        text=[f"{v:.0%}" for v in res[nom_c]], textposition="outside", cliponaxis=False)
        fig.update_layout(title="Précision, rappel et couverture du catalogue", barmode="group", bargap=.25, yaxis_tickformat=".0%")
        st.plotly_chart(theme(fig, 360), theme=None, config=CONFIG)
        with st.expander("Tableau détaillé et définitions"):
            fmt = {c: "{:.1%}" for c in res.columns if c.startswith(("Taux", "Précision", "Rappel", "Couverture"))}
            fmt.update({"Genres différents / sélection": "{:.1f}", "Popularité moyenne (0-1)": "{:.2f}"})
            st.dataframe(res.style.format(fmt), hide_index=True, width="stretch")
            st.caption("Taux de réussite = part des membres pour qui au moins un film caché est retrouvé · Précision = part de la "
                       "sélection qui était un film caché · Rappel = part des films cachés retrouvés · Couverture = part du catalogue "
                       "proposée au moins une fois. Données fictives : résultats indicatifs, à refaire avec de vrais membres.")
        _exemple(ctx, ss.get("q_ex") or [])
    simulation.afficher(ctx)


def _exemple(ctx, exemples: list):
    """Un membre testé où le moteur a retrouvé le plus de films cachés, montré en détail."""
    cat = ctx.cat
    if not exemples:
        return
    ex = max(exemples, key=lambda e: (len(set(e["reco"]) & set(e["caches"])), -e["uid"]))
    m = membres.membre(ex["uid"])
    if not m:
        return
    trouves = set(ex["reco"]) & set(ex["caches"])
    n_aff = selon_ecran(ctx.mobile, JAQUETTES_PAR_RANGEE_ADMIN)
    section("🔎 Exemple concret", "ce que le test a vraiment fait pour un membre")
    with st.container(key="adcarte_exemple"):
        st.html(f'<div class="ft-av-ligne">{avatars.img(m["avatar"], 52, rayon=12)}<div><b>{escape(m["pseudo"])}</b><br>'
                f'<span class="ft-petit">{escape(m["prenom"])} · {len(trouves)} film(s) caché(s) retrouvé(s) sur {len(ex["caches"])}</span></div></div>')
        st.html('<div class="fj-label">Ses derniers coups de cœur <span>(connus du moteur)</span></div>'
                + jaquettes(cat, ex["aimes"][-n_aff:], col=n_aff))
        caches = sorted(ex["caches"], key=lambda j: j not in trouves)[:n_aff]
        st.html('<div class="fj-label">Films cachés au moteur <span>✅ = retrouvé</span></div>'
                + jaquettes(cat, caches, {j: ("✅", "ok") for j in trouves}, {j: ("ok" if j in trouves else "terne") for j in caches}, col=n_aff))
        st.html(f'<div class="fj-label">Sélection du moteur <span>top {len(ex["reco"])}</span></div>'
                + jaquettes(cat, ex["reco"][:2 * n_aff], {j: ("✅", "ok") for j in trouves}, {j: "ok" for j in trouves}, col=n_aff))
