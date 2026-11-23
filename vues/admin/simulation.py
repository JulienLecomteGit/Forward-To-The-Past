"""Espace admin › simulation sans rien enregistrer : on rejoue la sélection « Pour toi » d'un membre après
une action fictive (aime 5 films, en rejette 5, change ses genres) et on mesure l'effet.

Utilise     : config (affichage, libelles), donnees (base, interactions, membres),
              interface (barres, jaquettes, mise_en_page, tuiles), moteur (communaute, profil_membre, recommandation),
              vues/admin (comparaison)
Utilisé par : vues/admin (onglet_qualite)
"""
from __future__ import annotations

from html import escape

import streamlit as st

from config.affichage import AMBRE, JAQUETTES_PAR_RANGEE_ADMIN, ROSE, TURQUOISE
from config.libelles import SCENARIOS_SIMULATION
from donnees import base, interactions, membres
from interface.barres import gouts_html
from interface.jaquettes import jaquettes
from interface.mise_en_page import colonnes, section, selon_ecran
from interface.tuiles import tuile_score
from moteur.communaute import Communaute
from moteur.profil_membre import profil_membre
from moteur.recommandation import pour_toi
from vues.admin.comparaison import comparer_classements


def _simuler(ctx, uid: int, scenario: str, genre: str, genres: list) -> dict:
    """Rejoue les recommandations d'un membre après une action fictive (rien n'est écrit en base)."""
    cat, p = ctx.cat, ctx.p
    prefs, inter = membres.preferences(uid), interactions.interactions(uid)
    pr0 = profil_membre(cat, prefs, inter, uid)
    r0 = pour_toi(cat, pr0, p, ctx.comm, n=8)
    inter2 = {k: dict(v) for k, v in inter.items()}
    inter2.setdefault("_dates", {})
    prefs2, comm2, films, vise = dict(prefs), ctx.comm, [], genre
    connus = set(pr0.aimes) | set(pr0.detestes) | pr0.vus | pr0.liste
    if scenario == SCENARIOS_SIMULATION[0]:
        films = [int(j) for j in cat.par_popularite if cat.df.genre[j] == genre and j not in connus and j not in r0.indices][:5]
        for j in films:
            inter2["like"][cat.df.tconst[j]] = None
            inter2["_dates"][cat.df.tconst[j]] = "9999"  # plus récent que tout
        comm2 = Communaute(cat, interactions.toutes_interactions() + [(uid, cat.df.tconst[j], "like", None, base.maintenant()) for j in films])
    elif scenario == SCENARIOS_SIMULATION[1]:
        gouts = r0.contexte.get("gouts") or [(cat.df.genre[r0.indices[0]], 1)]
        vise = gouts[0][0]
        large = pour_toi(cat, pr0, p, ctx.comm, n=30).indices
        films = [j for j in large if cat.df.genre[j] == vise][:5]
        for j in films:
            inter2["dislike"][cat.df.tconst[j]] = None
            inter2["_dates"][cat.df.tconst[j]] = "9999"
    else:
        prefs2["genres"] = list(genres)
        vise = genres[0] if genres else genre
    pr1 = profil_membre(cat, prefs2, inter2, uid)
    r1 = pour_toi(cat, pr1, p, comm2, n=8)
    part = lambda idx, g: sum(cat.df.genre[j] == g for j in idx) / max(len(idx), 1)  # noqa: E731
    jumeaux_touches, nb_jumeaux = 0, 0
    if comm2 is not ctx.comm:
        _, voisins = ctx.comm.membre(pr0.aimes, exclure_uid=uid, k=10)
        for v, _s in voisins:
            prv = profil_membre(cat, membres.preferences(v), interactions.interactions(v), v)
            a = pour_toi(cat, prv, p, ctx.comm, n=10).indices
            b = pour_toi(cat, prv, p, comm2, n=10).indices
            nb_jumeaux += 1
            jumeaux_touches += int(set(a) != set(b))
    return {"avant": r0.indices, "apres": r1.indices, "films": films, "vise": vise,
            "g0": r0.contexte.get("gouts", []), "g1": r1.contexte.get("gouts", []),
            "part0": part(r0.indices, vise), "part1": part(r1.indices, vise),
            "changes": len(set(r1.indices) - set(r0.indices)), "jumeaux": (jumeaux_touches, nb_jumeaux),
            "communaute": comm2 is not ctx.comm}


def afficher(ctx):
    """Simulation : choix d'un membre et d'une action, puis sélection avant / après, sans rien enregistrer."""
    ss, cat = st.session_state, ctx.cat
    n_aff = selon_ecran(ctx.mobile, JAQUETTES_PAR_RANGEE_ADMIN)
    section("🕹️ Le membre a-t-il vraiment la main ?", "simulation sans rien enregistrer : on rejoue sa sélection « Pour toi » après une action")
    with st.container(key="adcarte_influence"):
        liste_membres = membres.liste_pour_selection()
        noms = {r["id"]: f"{r['pseudo']} ({r['prenom']})" for r in liste_membres}
        c1, c2, c3 = colonnes(ctx.mobile, [1, 2, 1.2], meme_conteneur=True)
        uid = c1.selectbox("Membre", list(noms), key="inf_uid", format_func=lambda u: noms.get(u, str(u)))
        scenario = c2.segmented_control("Action simulée", SCENARIOS_SIMULATION, default=SCENARIOS_SIMULATION[0], key="inf_scen") or SCENARIOS_SIMULATION[0]
        genre, genres = "Horreur", []
        if scenario == SCENARIOS_SIMULATION[0]:
            genre = c3.selectbox("Genre des 5 films aimés", cat.genres, index=cat.genres.index("Horreur") if "Horreur" in cat.genres else 0, key="inf_genre")
        elif scenario == SCENARIOS_SIMULATION[1]:
            c3.caption("Il rejette 5 films de son genre n°1 actuel.")
        else:
            genres = c3.multiselect("Ses nouveaux genres", cat.genres, default=[g for g in ("Horreur", "Thriller") if g in cat.genres],
                                    max_selections=5, key="inf_genres")
        cle = (uid, scenario, genre, tuple(genres), interactions.version_communaute(), tuple(sorted(ctx.p.items())))
        if st.button("Simuler", icon=":material/play_arrow:", type="primary", key="inf_go"):
            with st.spinner("Simulation…"):
                ss.inf_res = (cle, _simuler(ctx, uid, scenario, genre, genres))
        if not ss.get("inf_res") or ss.inf_res[0] != cle:
            st.caption("Choisis un membre et une action, puis lance la simulation.")
            return
        r = ss.inf_res[1]
        if r["films"]:
            st.html(f'<div class="fj-label">Films {"aimés" if scenario == SCENARIOS_SIMULATION[0] else "rejetés"} dans la simulation</div>'
                    + jaquettes(cat, r["films"], {j: ("❤️" if scenario == SCENARIOS_SIMULATION[0] else "🤮", "") for j in r["films"]}, col=n_aff))
        marques, classes, bilan = comparer_classements(r["avant"], r["apres"])
        st.html('<div class="fj-label">Sa sélection avant</div>' + gouts_html(r["g0"], "Goûts compris :")
                + jaquettes(cat, r["avant"], col=n_aff))
        st.html('<div class="fj-label">Sa sélection après</div>' + gouts_html(r["g1"], "Goûts compris :")
                + jaquettes(cat, r["apres"], marques, classes, col=n_aff))
        t_j, n_j = r["jumeaux"]
        effet = (f"{t_j} / {n_j}" if r["communaute"] else "0")
        detail = ("de ses jumeaux ciné voient leur top 10 changer" if r["communaute"]
                  else "un « pas pour moi » ou un changement de genres ne touche que ses propres recommandations")
        with st.container(key="qtuiles_inf", horizontal=True):
            for titre, val, det, c in (("Films changés", f"{r['changes']} / {len(r['apres'])}", "dans sa sélection de 8", ROSE),
                                       (f"Part « {r['vise']} »", f"{r['part0']:.0%} → {r['part1']:.0%}", "dans sa sélection", AMBRE),
                                       ("Effet sur les autres", effet, detail, TURQUOISE)):
                st.html(tuile_score(c, titre, val, f'<div class="ft-petit">{escape(det)}</div>'))
