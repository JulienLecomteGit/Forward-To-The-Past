"""Mes films : carnet de séance, favoris, à voir, pas pour moi — lignes compactes, recherche, filtre et tri.

Utilise     : config (affichage, donnees, libelles), etat (actions, navigation),
              interface (cartes, mise_en_page, textes, tuiles), outils (texte), recherche
Utilisé par : app
"""
from __future__ import annotations

from html import escape

import streamlit as st

import recherche
from config.affichage import LIGNES_PAR_PAGE_MES_FILMS
from config.donnees import LIEUX
from config.libelles import ONGLETS_MES_FILMS, TOUS_GENRES, TOUS_LIEUX, TRIS_CARNET, TRIS_LISTE
from etat.actions import basculer, retirer_seance
from etat.navigation import ouvrir_fiche
from interface.cartes import ligne_film
from interface.mise_en_page import colonnes
from interface.textes import etoiles, note_txt
from interface.tuiles import tuile
from outils.texte import date_fr, format_entrees, normaliser


def afficher(ctx):
    """Page Mes films : carnet de séance puis un onglet par liste (favoris, à voir, pas pour moi)."""
    inter, seances = ctx.inter, ctx.seances
    st.markdown("## 🎟️ Mes films")
    tabs = st.tabs([f"🎟️ Carnet de séance ({len(seances)})"] + [f"{lib} ({len(inter[t])})" for t, (lib, _, _) in ONGLETS_MES_FILMS.items()])
    with tabs[0]:
        _carnet(ctx)
    for tab, t in zip(tabs[1:], ONGLETS_MES_FILMS):
        with tab:
            _liste(ctx, t)


# ------------------------------------------------------------------ outils communs
def _cherche(cat, j: int, q: str) -> bool:
    """Vrai si le texte cherché apparaît dans le titre, le titre original, la réalisation ou le casting."""
    if not q:
        return True
    q = normaliser(q)
    f = cat.df.iloc[j]
    texte = normaliser(" ".join([f["titre"], f["original"], *f["real_noms"], *f["acteurs_noms"][:4]]))
    return q in texte


def _outils(ctx, cle: str, filtre_lab: str, filtre_opts: list, tris: dict, tconsts: list) -> tuple[str, str, str]:
    """Barre d'outils d'un onglet : recherche, filtre, tri ; renvoie (texte, filtre, tri)."""
    ss = st.session_state
    with st.container(key="mf_outils" if cle == "carnet" else f"mf_outils_{cle}"):
        c1, c2, c3 = colonnes(ctx.mobile, [2.2, 1.3, 1.6], meme_conteneur=True, vertical_alignment="top")
        with c1:
            ev = recherche.champ(ctx.cat, f"mfr_{cle}", "Titre, réalisateur, acteur…", mode="liste", valeur=ss.get(f"mfq_{cle}", ""),
                                 restreindre=tconsts, libelle="Rechercher")
        filtre = c2.selectbox(filtre_lab, filtre_opts, key=f"mff_{cle}")
        tri = c3.selectbox("Trier par", list(tris), format_func=tris.get, key=f"mft_{cle}")
    if ev and ev["type"] == "film":
        ouvrir_fiche(ev["tconst"], "mes_films")
        st.rerun()
    if ev and ev["type"] == "texte":
        ss[f"mfq_{cle}"] = ev.get("q", "")
    return ss.get(f"mfq_{cle}", "").strip(), filtre, tri


def _plus(cle: str, n: int):
    """Bouton « Afficher plus » : ajoute une page de lignes."""
    st.session_state[f"mfn_{cle}"] = n + LIGNES_PAR_PAGE_MES_FILMS


def _lignes(ctx, cle: str, lignes: list, total: int, unite: str = "film"):
    """lignes : (indice catalogue, html sous le titre, rappel corbeille, args, aide)."""
    ss = st.session_state
    n = ss.get(f"mfn_{cle}", LIGNES_PAR_PAGE_MES_FILMS)
    if not lignes:
        st.info("Aucun film ne correspond à ta recherche.")
        return
    filtre = f" sur {total}" if len(lignes) != total else ""
    st.caption(f"{len(lignes)} {unite}{'s' if len(lignes) > 1 else ''}{filtre} · clique sur un film pour ouvrir sa fiche, "
               "🗑️ pour le retirer")
    with st.container(key=f"glignes_{cle}", horizontal=True):
        for j, sous, rappel, args, aide in lignes[:n]:
            ligne_film(ctx.cat, j, f"{cle}_{ctx.cat.df.tconst[j]}", "mes_films", sous, rappel, args, aide)
    if len(lignes) > n:
        st.button(f"Afficher {min(LIGNES_PAR_PAGE_MES_FILMS, len(lignes) - n)} de plus ({len(lignes) - n} restants)", icon=":material/expand_more:",
                  key=f"mfplus_{cle}", on_click=_plus, args=(cle, n), width="stretch")


# ------------------------------------------------------------------ carnet de séance
def _carnet(ctx):
    """Onglet carnet : chiffres clés, outils, puis une ligne par séance."""
    cat, seances = ctx.cat, ctx.seances
    if not seances:
        st.info("Ton carnet est vide. Ouvre la fiche d'un film puis « Mon carnet de séance » pour noter date, lieu, note et avis.")
        return
    notes = [s["note"] for s in seances.values() if s.get("note")]
    lieux = [s["lieu"] for s in seances.values()]
    with st.container(key="gmembres_carnet", horizontal=True):
        for lab, val, det in [
                ("Séances", str(len(seances)), "dans ton carnet"),
                ("Note moyenne", f"{sum(notes) / len(notes):.1f}".replace(".", ",") if notes else "—", f"{len(notes)} notes"),
                ("Au cinéma", str(lieux.count("cinema")), "en salle"),
                ("À la maison", str(lieux.count("streaming") + lieux.count("tv")), "streaming, TV, DVD")]:
            st.html(tuile(lab, val, det))
    q, lieu, tri = _outils(ctx, "carnet", "Lieu", [TOUS_LIEUX] + list(LIEUX.values()), TRIS_CARNET, list(seances))
    code_lieu = {v: k for k, v in LIEUX.items()}.get(lieu)
    items = [(cat.position[t], s) for t, s in seances.items() if t in cat.position]
    items = [(j, s) for j, s in items if (code_lieu is None or s["lieu"] == code_lieu) and _cherche(cat, j, q)]
    cles = {"recent": lambda x: x[1]["date_seance"] or "", "ancien": lambda x: x[1]["date_seance"] or "",
            "note": lambda x: (x[1].get("note") or 0, x[1]["date_seance"] or ""),
            "titre": lambda x: normaliser(cat.df.titre[x[0]]), "annee": lambda x: cat.annee[x[0]]}
    items.sort(key=cles[tri], reverse=tri in ("recent", "note", "annee"))
    lignes = []
    for j, s in items:
        sous = (f'<div class="fl-info"><span class="ft-etoiles">{etoiles(s.get("note"))}</span>'
                f'<span>{date_fr(s["date_seance"])}</span><span class="fl-chip">{LIEUX.get(s["lieu"], "")}</span></div>'
                + (f'<div class="fl-avis">« {escape(s["avis"])} »</div>' if s.get("avis") else ""))
        lignes.append((j, sous, retirer_seance, (cat.df.tconst[j],), "Retirer du carnet"))
    _lignes(ctx, "carnet", lignes, len(seances), "séance")


# ------------------------------------------------------------------ favoris, à voir, pas pour moi
def _liste(ctx, t: str):
    """Onglet favoris / à voir / pas pour moi (t = like, liste, dislike) : outils de recherche et tri, puis les lignes."""
    cat, inter = ctx.cat, ctx.inter
    _, vide, aide = ONGLETS_MES_FILMS[t]
    dates = inter.get("_dates", {})
    films = [cat.position[c] for c in inter[t] if c in cat.position]
    if not films:
        st.info(vide)
        return
    genres = sorted({cat.df.genre[j] for j in films if cat.df.genre[j]})
    q, genre, tri = _outils(ctx, t, "Genre", [TOUS_GENRES] + genres, TRIS_LISTE, [cat.df.tconst[j] for j in films])
    choix = [j for j in films if (genre == TOUS_GENRES or cat.df.genre[j] == genre) and _cherche(cat, j, q)]
    _trier_liste(cat, choix, tri, dates)
    if t == "liste":
        minutes = int(sum(cat.duree[j] for j in choix if cat.duree[j] == cat.duree[j]))
        st.caption(f"🍿 {minutes // 60} h {minutes % 60:02d} de cinéma devant toi")
    lignes = [_ligne_liste(cat, j, dates, t, aide) for j in choix]
    _lignes(ctx, t, lignes, len(films))


def _trier_liste(cat, choix: list, tri: str, dates: dict) -> None:
    """Trie sur place : date d'ajout, titre, année, note IMDb ou durée (valeur inconnue : 0, ou 999 pour la durée)."""
    cles = {"ajout": lambda j: dates.get(cat.df.tconst[j], ""), "titre": lambda j: normaliser(cat.df.titre[j]),
            "annee": lambda j: cat.annee[j] if cat.annee[j] == cat.annee[j] else 0,
            "imdb": lambda j: cat.note[j] if cat.note[j] == cat.note[j] else 0,
            "duree": lambda j: cat.duree[j] if cat.duree[j] == cat.duree[j] else 999}
    choix.sort(key=cles[tri], reverse=tri in ("ajout", "annee", "imdb"))


def _ligne_liste(cat, j: int, dates: dict, t: str, aide: str) -> tuple:
    """Une ligne : film, sous-titre HTML (note, entrées, date d'ajout, réalisateurs), bouton pour le retirer."""
    f = cat.df.iloc[j]
    note = note_txt(f["note"]) or "—"
    ajout = date_fr(dates.get(f["tconst"], ""))
    sous = (f'<div class="fl-info"><span class="fc-note">⭐ {note}</span><span class="fc-bo">🎟️ {format_entrees(f["entrees"])}</span>'
            + (f'<span class="fl-chip">ajouté le {ajout}</span>' if ajout else "") + "</div>"
            + (f'<div class="fl-meta">Réalisé par {escape(", ".join(f["real_noms"][:2]))}</div>' if len(f["real_noms"]) else ""))
    return (j, sous, basculer, (f["tconst"], t, "mes_films"), aide)
