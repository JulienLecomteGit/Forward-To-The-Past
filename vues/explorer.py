"""Explorer : recherche (titre, acteur, réalisateur), filtres et tri — dont « Pour toi ».

Utilise     : config (affichage, catalogue, libelles), donnees (journal), etat (navigation),
              interface (cartes, mise_en_page), moteur (recommandation), outils (texte), recherche
Utilisé par : app
"""
from __future__ import annotations

import numpy as np
import streamlit as st

import recherche
from config.affichage import EMOJI_GENRE, FILMS_PAR_PAGE_EXPLORER
from config.catalogue import ANNEE_MAX, ANNEE_MIN
from config.libelles import TRIS_EXPLORER
from donnees import journal
from etat.navigation import ouvrir_fiche
from interface.cartes import grille
from interface.mise_en_page import colonnes, selon_ecran
from moteur.recommandation import pour_toi
from outils.texte import nombre_fr


def afficher(ctx):
    """Page Explorer : champ de recherche, filtres, tri, puis la grille paginée (« Charger N films de plus »)."""
    ss, cat = st.session_state, ctx.cat
    st.markdown("## 🔎 Explorer le catalogue")
    q = _recherche(ctx)
    genres, tri, annees, duree, note, fr, masquer = _filtres(ctx)
    masque = _masque(ctx, genres, annees, duree, note, fr, masquer)
    base = np.array(cat.chercher(q, None), dtype=int) if q.strip() else np.arange(cat.n)
    idx = base[masque[base]] if len(base) else base
    idx, res = _trier(ctx, idx, tri, q)
    signature = (q, tuple(genres), tri, annees, duree, note, fr, masquer)
    pas = selon_ecran(ctx.mobile, FILMS_PAR_PAGE_EXPLORER)
    if ss.get("ex_sig") != signature:
        ss.ex_sig, ss.ex_limite = signature, pas
    st.caption(f"**{nombre_fr(len(idx))}** film(s)" + (" · triés par pertinence de recherche" if q.strip() and res is not None else ""))
    if not len(idx):
        st.info("Aucun film ne correspond. Élargis les filtres ou essaie le titre original.")
        return
    grille(cat, idx[: ss.ex_limite].tolist(), "explorer", "explorer", res=res, inter=ctx.inter, raisons=False)
    if len(idx) > ss.ex_limite:
        st.button(f"Charger {pas} films de plus", icon=":material/expand_more:", width="stretch",
                  on_click=lambda: ss.update(ex_limite=ss.ex_limite + pas))


def _recherche(ctx) -> str:
    """Champ de recherche : un film choisi ouvre sa fiche ; un texte libre filtre la grille. Renvoie le texte."""
    ss, cat = st.session_state, ctx.cat
    ev = recherche.champ(cat, "ex_rech", "Un titre (FR ou VO), un acteur, un réalisateur… ex. Jean Reno", mode="explorer",
                         valeur=ss.get("ex_q", ""), personnes=True)
    if ev and ev["type"] == "film":
        journal.journaliser(ctx.uid, "recherche", cat.df.titre[cat.position[ev["tconst"]]][:80] if ev["tconst"] in cat.position else "")
        ouvrir_fiche(ev["tconst"], "recherche")
        st.rerun()
    if ev and ev["type"] == "texte":
        ss.ex_q = ev.get("q", "")
    q = ss.get("ex_q", "")
    if q.strip() and ss.get("ex_q_log") != q.strip():
        journal.journaliser(ctx.uid, "recherche", q.strip()[:80])
        ss.ex_q_log = q.strip()
    return q


def _filtres(ctx) -> tuple:
    """Panneau « ⚙️ Filtres et tri » (fenêtre sur mobile, volet dépliable sur ordinateur)."""
    cat = ctx.cat
    zone = st.popover("⚙️ Filtres et tri", width="stretch") if ctx.mobile else st.expander("⚙️ Filtres et tri", expanded=False)
    with zone:
        c1, c2, c3 = colonnes(ctx.mobile, 3)
        with c1:
            genres = st.multiselect("Genres", cat.genres, key="ex_genres", placeholder="Tous",
                                    format_func=lambda g: f"{EMOJI_GENRE.get(g, '🎞️')} {g}")
            tri = st.selectbox("Trier par", TRIS_EXPLORER, key="ex_tri")
        with c2:
            annees = st.slider("Période", ANNEE_MIN, ANNEE_MAX, (ANNEE_MIN, ANNEE_MAX), key="ex_annees")
            dmin, dmax = int(np.nanmin(cat.duree)), int(np.nanmax(cat.duree))
            duree = st.slider("Durée (min)", dmin, dmax, (dmin, dmax), step=5, key="ex_duree")
        with c3:
            note = st.slider("Note IMDb minimale", 0.0, 9.0, 0.0, 0.5, key="ex_note")
            fr = st.toggle("🇫🇷 Cinéma français uniquement", key="ex_fr")
            masquer = st.toggle("🙈 Masquer ce que j'ai déjà vu", key="ex_masquer")
    return genres, tri, annees, duree, note, fr, masquer


def _masque(ctx, genres, annees, duree, note, fr, masquer):
    """Vrai pour chaque film qui passe tous les filtres (durée ou note inconnue : 100 min / 0)."""
    cat = ctx.cat
    masque = ((cat.annee >= annees[0]) & (cat.annee <= annees[1])
              & (np.nan_to_num(cat.duree, nan=100) >= duree[0]) & (np.nan_to_num(cat.duree, nan=100) <= duree[1])
              & (np.nan_to_num(cat.note, nan=0) >= note))
    if genres:
        masque &= np.isin(cat.df["genre"].to_numpy(), genres)
    if fr:
        masque &= cat.fr
    if masquer:
        masque[list(ctx.profil.vus)] = False
    return masque


def _trier(ctx, idx, tri, q) -> tuple:
    """Ordonne les films selon le tri choisi (TRIS_EXPLORER, dans l'ordre de la liste) ; renvoie (films, résultat
    « Pour toi » ou None). Avec une recherche, le tri « Pour toi » garde l'ordre de pertinence."""
    cat = ctx.cat
    res = None
    if tri == TRIS_EXPLORER[0]:
        res = pour_toi(cat, ctx.profil, ctx.p, ctx.comm, n=1)
        if not q.strip():
            idx = idx[np.argsort(-res.scores[idx], kind="stable")]
    elif tri == TRIS_EXPLORER[1]:
        idx = idx[np.argsort(-np.nan_to_num(cat.qualite[idx]), kind="stable")]
    elif tri == TRIS_EXPLORER[2]:
        idx = idx[np.argsort(-cat.entrees[idx], kind="stable")]
    elif tri == TRIS_EXPLORER[3]:
        idx = idx[np.argsort(-cat.annee[idx], kind="stable")]
    elif tri == TRIS_EXPLORER[4]:
        idx = idx[np.argsort(cat.annee[idx], kind="stable")]
    else:
        idx = idx[np.argsort(cat.df["titre"].str.lower().to_numpy()[idx], kind="stable")]
    return idx, res
