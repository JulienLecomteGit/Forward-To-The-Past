"""Espace admin › onglet 👥 Membres : tableau filtrable, export CSV, fiche détaillée d'un membre
(goûts, recommandations actuelles, export RGPD, suppression).

Utilise     : config (affichage, donnees), donnees (interactions, journal, membres), etat (actions),
              interface (cartes, mise_en_page), medias (avatars), moteur (profil_membre, recommandation)
Utilisé par : vues (admin)
"""
from __future__ import annotations

import json
from html import escape

import pandas as pd
import streamlit as st

from config.affichage import DECENNIE_LIB, EMOJI_GENRE
from config.donnees import TYPES_INTERACTION
from donnees import interactions, journal, membres
from etat.actions import annoncer
from interface.cartes import grille
from interface.mise_en_page import colonnes
from medias import avatars
from moteur.profil_membre import profil_membre
from moteur.recommandation import pour_toi


def _masquer(email: str) -> str:
    """Adresse e-mail masquée (« ma•••@domaine.fr ») pour la minimisation RGPD."""
    nom, _, dom = email.partition("@")
    return (nom[:2] + "•••" if len(nom) > 2 else "•••") + "@" + dom


def afficher(ctx, d):
    """Onglet complet : filtres, tableau des membres (une ligne cliquable par membre), export, puis le détail."""
    m, i = d["membres"].copy(), d["inter"]
    if not len(m):
        st.info("Aucun membre.")
        return
    c1, c2, c3 = colonnes(ctx.mobile, [2, 1, 1])
    q = c1.text_input("Rechercher un membre", placeholder="pseudo, prénom, nom, ville…", key="adm_q")
    type_m = c2.segmented_control("Membres", ["Tous", "Réels", "Fictifs"], default="Tous", key="adm_type")
    complets = c3.toggle("Afficher les e-mails complets", key="adm_mails",
                         help="Par défaut les adresses sont masquées (principe de minimisation RGPD).")
    m = _filtrer(_avec_compteurs(m, i), q, type_m)
    vue = _tableau(m, complets)
    if not len(vue):
        st.info("Aucun membre ne correspond. Les membres « réels » apparaissent dès qu'un compte est créé via « Créer mon compte ».")
        return
    st.caption(f"{len(vue)} membre(s) · clique une ligne pour voir le détail")
    sel = st.dataframe(vue, hide_index=True, width="stretch", height=420, on_select="rerun", selection_mode="single-row", key="adm_table",
                       column_config={"Avatar": st.column_config.ImageColumn(width="small"),
                                      "Inscription": st.column_config.DatetimeColumn(format="DD/MM/YYYY"),
                                      "Dernière connexion": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                                      "J'aime": st.column_config.ProgressColumn(min_value=0, max_value=max(int(vue["J'aime"].max()) if len(vue) else 0, 1), format="%d")})
    st.download_button("Exporter la liste (CSV)", icon=":material/download:", data=vue.drop(columns="Avatar").to_csv(index=False, sep=";").encode("utf-8-sig"),
                       file_name="membres_fttp.csv", mime="text/csv", on_click="ignore")
    lignes = sel.selection.rows if sel and sel.selection else []
    if lignes:
        _detail_membre(ctx, m.iloc[lignes[0]])


def _avec_compteurs(m, i):
    """Ajoute à chaque membre son nombre d'interactions par type (like, liste, note…), 0 si aucune."""
    compte = i.pivot_table(index="uid", columns="type", values="tconst", aggfunc="count", fill_value=0)
    for t in TYPES_INTERACTION:
        if t not in compte:
            compte[t] = 0
    return m.merge(compte, left_on="id", right_index=True, how="left").fillna({t: 0 for t in TYPES_INTERACTION})


def _filtrer(m, q, type_m):
    """Recherche texte (pseudo, prénom, nom, ville, e-mail) + réels / fictifs ; les plus récents en premier."""
    if q:
        mask = m[["pseudo", "prenom", "nom", "ville", "email"]].astype(str).apply(lambda s: s.str.contains(q, case=False)).any(axis=1)
        m = m[mask]
    if type_m == "Réels":
        m = m[m.est_fictif == 0]
    elif type_m == "Fictifs":
        m = m[m.est_fictif == 1]
    return m.sort_values("date_inscription", ascending=False)


def _tableau(m, complets: bool):
    """Colonnes affichées et exportées (e-mails masqués sauf si l'admin demande les adresses complètes)."""
    return pd.DataFrame({
        "Avatar": m.avatar.map(avatars.url), "Pseudo": m.pseudo, "Prénom": m.prenom, "Nom": m.nom,
        "E-mail": m.email if complets else m.email.map(_masquer), "Âge": m.tranche_age, "Ville": m.ville,
        "Inscription": m.date_inscription, "Dernière connexion": m.derniere_connexion,
        "J'aime": m.like.astype(int), "Liste": m.liste.astype(int), "Notes": m.note.astype(int),
        "Fictif": m.est_fictif.astype(bool)})


def _detail_membre(ctx, r):
    """Encadré du membre sélectionné : identité, goûts, recommandations actuelles, export RGPD, suppression."""
    ss = st.session_state
    uid = int(r.id)
    with st.container(border=True):
        prefs = membres.preferences(uid)
        st.html(f'<div class="ft-av-ligne">{avatars.img(r.avatar, 64)}<div><h3 style="margin:0">{escape(r.pseudo)}</h3>'
                f'<span class="ft-petit">{escape(r.prenom)} {escape(r.nom)} · {escape(r.tranche_age or "")} · {escape(r.ville or "")}'
                f' · {"fictif" if r.est_fictif else "réel"}</span></div></div>')
        st.html('<div class="ft-chips" style="margin:.6rem 0">' + "".join(
            f'<span class="ft-chip">{EMOJI_GENRE.get(g, "")} {escape(g)}</span>' for g in prefs["genres"]) + "".join(
            f'<span class="ft-chip cyan">{DECENNIE_LIB.get(dd, dd)}</span>' for dd in prefs["decennies"])
            + f'<span class="ft-chip rose">{prefs["style"]} · {prefs["origine"]} · {prefs["format_duree"]}</span></div>')
        inter = interactions.interactions(uid)
        pr = profil_membre(ctx.cat, prefs, inter, uid)
        res = pour_toi(ctx.cat, pr, ctx.p, ctx.comm, n=4)
        st.markdown("**Ce que le moteur lui recommande actuellement :**")
        grille(ctx.cat, res.indices, f"adm_{uid}", "admin", inter=inter, res=res)
        c1, c2 = st.columns(2)
        c1.download_button("Exporter ses données (RGPD)", icon=":material/folder_zip:", data=json.dumps(membres.export_membre(uid), ensure_ascii=False, indent=2),
                           file_name=f"membre_{uid}.json", mime="application/json", on_click="ignore", width="stretch")
        if c2.checkbox("Je confirme la suppression", key=f"adm_conf_{uid}"):
            if c2.button("Supprimer ce membre", icon=":material/delete:", type="primary", width="stretch"):
                membres.supprimer_membre(uid)
                journal.journaliser(ss.get("uid"), "admin_suppression", {"membre": uid})
                annoncer("Membre supprimé", "🗑️")
                st.rerun()
