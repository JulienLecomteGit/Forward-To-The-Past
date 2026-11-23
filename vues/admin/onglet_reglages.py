"""Espace admin › onglet 🎛️ Réglages du moteur : recette du moteur, profils prêts à l'emploi, curseurs
rangés en cartes, brouillon / enregistrement, et aperçu en direct (réglages enregistrés vs brouillon).

Utilise     : config (affichage, reglages_moteur), donnees (interactions, journal, membres, reglages),
              etat (actions, cache), interface (barres, jaquettes, mise_en_page),
              moteur (profil_membre, recommandation), recherche, vues/admin (comparaison)
Utilisé par : vues (admin), vues/admin (onglet_qualite)
"""
from __future__ import annotations

from html import escape

import streamlit as st

import recherche
from config.affichage import JAQUETTES_PAR_RANGEE_ADMIN
from config.reglages_moteur import (
    CARTES_REGLAGES,
    COMPOSANTES,
    INTERRUPTEURS,
    LIBELLES,
    PARAMS_DEFAUT,
    PRESETS,
    REGLAGES,
)
from donnees import interactions, journal, membres, reglages
from etat.actions import annoncer
from etat.cache import parametres
from interface.barres import barre, gouts_html
from interface.jaquettes import jaquettes
from interface.mise_en_page import colonnes, section, selon_ecran
from moteur.profil_membre import profil_membre
from moteur.recommandation import pour_toi, similaires
from outils.texte import annee_entre_parentheses
from vues.admin.comparaison import bilan_html, comparer_classements


def _cles():
    """Noms de tous les réglages (curseurs puis interrupteurs)."""
    return [r[0] for r in REGLAGES] + [r[0] for r in INTERRUPTEURS]


def _charger(valeurs: dict):
    """Place des valeurs dans les curseurs et interrupteurs de l'onglet."""
    for k in _cles():
        st.session_state[f"reg_{k}"] = valeurs[k]


def _appliquer_preset():
    """Charge le préréglage choisi (par-dessus les valeurs par défaut)."""
    nom = st.session_state.get("reg_preset")
    if nom:
        _charger(dict(PARAMS_DEFAUT, **PRESETS[nom]))


def lire_brouillon() -> dict:
    """Réglages en cours de modification (pas encore enregistrés)."""
    return {k: st.session_state.get(f"reg_{k}", PARAMS_DEFAUT[k]) for k in _cles()}


def _recette(p: dict) -> list[tuple[str, float]]:
    """Part de chaque critère dans le score d'un film (poids des composantes)."""
    def nom(k):
        """Nom court d'un critère pour la phrase de la recette."""
        if k == "popularite":
            return "Pépites" if float(p[k]) < 0 else "Succès en salles"
        return LIBELLES[k].split(" ", 1)[1]
    # tous les critères, même à 0 : chaque critère garde ainsi la même couleur d'une barre à l'autre
    return [(nom(k), abs(float(p[k]))) for k in COMPOSANTES]


def _titre_carte(icone: str, titre: str, sous: str) -> str:
    """En-tête d'une carte de réglages (icône, titre, sous-titre)."""
    return f'<div class="ad-titre"><span class="ic">{icone}</span><div><b>{escape(titre)}</b><p>{escape(sous)}</p></div></div>'


def afficher(ctx):
    """Onglet 🎛️ Réglages : recette en un clic, cartes de réglages, enregistrement, aperçu."""
    ss = st.session_state
    enregistres = parametres()
    if f"reg_{_cles()[0]}" not in ss:
        _charger(enregistres)
    brouillon = lire_brouillon()
    modifs = {k: (enregistres[k], v) for k, v in brouillon.items() if v != enregistres[k]}
    with st.container(key="adcarte_recette"):
        st.html(_titre_carte("🎛️", "La recette du moteur", f"Ce qui compte dans le score d'un film · s'applique à tous les membres dès "
                             f"l'enregistrement · dernière modification : {reglages.date_parametres() or 'jamais (valeurs d’usine)'}"))
        st.html('<div class="fj-label">Réglages enregistrés</div>' + barre(_recette(enregistres)))
        if modifs:
            st.html('<div class="fj-label">Ton brouillon <span>(pas encore appliqué)</span></div>' + barre(_recette(brouillon)))
        st.pills("Profils prêts à l'emploi", list(PRESETS), key="reg_preset", on_change=_appliquer_preset,
                 help="Charge un jeu de réglages dans le brouillon. Rien n'est appliqué tant que tu ne cliques pas sur Enregistrer.")
    par_groupe = {}
    for r in REGLAGES:
        par_groupe.setdefault(r[6], []).append(r)
    with st.container(key="regcartes", horizontal=True):
        for n, (titre, (icone, sous, groupes)) in enumerate(CARTES_REGLAGES.items()):
            with st.container(key=f"adcarte_reg{n}"):
                st.html(_titre_carte(icone, titre, sous))
                for groupe in groupes:
                    for cle, lib, aide, mini, maxi, pas, _ in par_groupe.get(groupe, []):
                        flottant = isinstance(pas, float)
                        kw = dict(min_value=float(mini), max_value=float(maxi), step=float(pas), format="%.1f") if flottant else \
                            dict(min_value=int(mini), max_value=int(maxi), step=int(pas))
                        ss[f"reg_{cle}"] = float(ss[f"reg_{cle}"]) if flottant else int(ss[f"reg_{cle}"])
                        st.slider(lib, key=f"reg_{cle}", help=aide, **kw)
                if titre == "Affichage":
                    for cle, lib, aide in INTERRUPTEURS:
                        st.toggle(lib, key=f"reg_{cle}", help=aide)
    brouillon = lire_brouillon()
    modifs = {k: (enregistres[k], v) for k, v in brouillon.items() if v != enregistres[k]}
    c1, c2, c3 = colonnes(ctx.mobile, 3)
    if c1.button(f"Enregistrer et appliquer ({len(modifs)} modif.)", icon=":material/save:", type="primary", width="stretch", disabled=not modifs):
        reglages.ecrire_parametres(brouillon)
        journal.journaliser(ss.get("uid"), "admin_reglages", {k: b for k, (a, b) in modifs.items()})
        annoncer("Réglages enregistrés : toutes les recommandations sont recalculées", "🎛️")
        st.rerun()
    c2.button("Annuler les modifications", icon=":material/undo:", width="stretch", on_click=_charger, args=(enregistres,), disabled=not modifs)
    c3.button("Valeurs d'usine", icon=":material/restart_alt:", width="stretch", on_click=_charger, args=(dict(PARAMS_DEFAUT),))
    if modifs:
        st.caption("Modifié : " + " · ".join(f"{LIBELLES.get(k, k)} {a} → {b}" for k, (a, b) in modifs.items()))
    _apercu(ctx, enregistres, brouillon)


def _apercu(ctx, avant: dict, apres: dict):
    """Aperçu en direct : même demande avec les réglages enregistrés et le brouillon, côte à côte."""
    cat = ctx.cat
    n_aff = selon_ecran(ctx.mobile, JAQUETTES_PAR_RANGEE_ADMIN)
    section("👀 Aperçu en direct", "même demande, réglages enregistrés vs brouillon — rien n'est appliqué aux membres")
    with st.container(key="adcarte_apercu"):
        c1, c2 = colonnes(ctx.mobile, [1, 2])
        mode = c1.segmented_control("Tester sur", ["👤 Un membre", "🎬 Un film"], default="👤 Un membre", key="ap_mode")
        if mode == "🎬 Un film":
            ss = st.session_state
            if ss.get("ap_film_t") not in cat.position:
                ss.ap_film_t = cat.df.tconst[recherche.premier(cat, "Retour vers le futur") or 0]
            with c2:
                ev = recherche.champ(cat, "ap_rech", "Tape un titre…", mode="film", valeur=cat.df.titre[cat.position[ss.ap_film_t]],
                                     libelle="Film de départ")
            if ev and ev["type"] == "film":
                ss.ap_film_t = ev["tconst"]
            depart = cat.position[ss.ap_film_t]
            r_av = similaires(cat, depart, avant, ctx.comm, n=n_aff)
            r_ap = similaires(cat, depart, apres, ctx.comm, n=n_aff)
            st.html(f'<div class="fj-label">Film de départ <span>{escape(cat.df.titre[depart])}{annee_entre_parentheses(cat.annee[depart])}'
                    f' · {escape(cat.df.genre[depart])}</span></div>')
        else:
            liste_membres = membres.liste_pour_selection()
            noms = {r["id"]: f"{r['pseudo']} ({r['prenom']})" for r in liste_membres}
            uid = c2.selectbox("Membre", list(noms), key="ap_uid", format_func=lambda u: noms.get(u, str(u)))
            pr = profil_membre(cat, membres.preferences(uid), interactions.interactions(uid), uid)
            r_av = pour_toi(cat, pr, avant, ctx.comm, n=n_aff)
            r_ap = pour_toi(cat, pr, apres, ctx.comm, n=n_aff)
        marques, classes, bilan = comparer_classements(r_av.indices, r_ap.indices)
        st.html('<div class="fj-label">Avec les réglages enregistrés</div>'
                + gouts_html(r_av.contexte.get("gouts", []), "Goûts pris en compte :")
                + jaquettes(cat, r_av.indices, col=n_aff))
        if avant == apres:
            st.caption("👆 Bouge un curseur ou choisis un profil prêt à l'emploi : une seconde rangée montrera aussitôt "
                       "les films qui entrent (🆕), montent (↑) ou descendent (↓).")
            return
        st.html('<div class="fj-label">Avec ton brouillon</div>'
                + gouts_html(r_ap.contexte.get("gouts", []), "Goûts pris en compte :")
                + jaquettes(cat, r_ap.indices, marques, classes, col=n_aff) + bilan_html(bilan))
