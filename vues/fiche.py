"""Fiche film en pleine page (style V8) : affiche, réactions, infos, carnet de séance, « pourquoi », films proches.

Utilise     : config (affichage, catalogue, donnees, reglages_moteur), donnees (journal), etat (actions, navigation),
              interface (cartes, mise_en_page, textes), medias (affiches), moteur (recommandation), outils (texte)
Utilisé par : app
"""
from __future__ import annotations

from datetime import date
from html import escape
from urllib.parse import quote_plus

import streamlit as st

from config.affichage import EMOJI_GENRE
from config.catalogue import LANGUES
from config.donnees import LIEUX
from config.reglages_moteur import LIBELLES
from donnees import journal
from etat.actions import enregistrer_seance, retirer_seance
from etat.navigation import retour
from interface.cartes import grille, reactions
from interface.mise_en_page import colonnes, section
from interface.textes import balise_affiche, etoiles, note_txt, origine_txt
from medias.affiches import url_affiche
from moteur.recommandation import pour_toi, similaires
from outils.texte import annee_ou_vide, date_fr, nombre_fr

# Mention sous le synopsis selon sa source (colonne source_fr du catalogue) ; à défaut : version originale
SOURCES_SYNOPSIS = {"TMDB": "Synopsis en français (TMDB)", "TRADUCTION": "Synopsis traduit du résumé TMDB"}


def afficher(ctx):
    """Fiche d'un film : retour, affiche + réactions, infos + carnet, « Pourquoi ce film ? », films similaires."""
    ss, cat = st.session_state, ctx.cat
    tconst = ss.get("fiche")
    j = cat.position.get(tconst)
    st.button("Retour", icon=":material/arrow_back:", on_click=retour, key="fiche_retour", type="primary")
    if j is None:
        st.error("Film introuvable dans le catalogue.")
        return
    f = cat.film(j)
    inter, seance = ctx.inter, ctx.seances.get(tconst)
    if ss.get("fiche_log") != tconst:
        journal.journaliser(ctx.uid, "fiche", {"tconst": tconst, "origine": ss.get("fiche_origine", "")})
        ss.fiche_log = tconst
    source = ss.get("fiche_origine", "fiche")

    gauche, droite = colonnes(ctx.mobile, [1, 2.3], gap="large")
    with gauche:
        url = url_affiche(f["affiche"], "w500")
        img = balise_affiche(url, f["titre"], paresseuse=False)
        st.html(f'<div class="ff-poster">{img}</div>')
        reactions(f, inter, f"reac_fiche_{tconst}", "f", tconst, source)
    with droite:
        _infos(f, tconst)
        _carnet(ctx, tconst, seance)

    _pourquoi(ctx, j)

    st.divider()
    section(f"⚡ Films similaires à {f['titre']}", "selon le moteur de recommandation")
    sim = similaires(cat, j, ctx.p, ctx.comm, n=4)
    grille(cat, sim.indices, f"sim_{tconst}", "reco_fiche", inter=inter, res=sim, seances=ctx.seances)


def _infos(f, tconst):
    """Titre, ligne d'infos (année, genre, durée, note, entrées, origine), saga, équipe, synopsis et liens."""
    st.html(f'<h1 class="ff-titre">🎬 {escape(f["titre"])}</h1>'
            + (f'<p class="ft-petit" style="margin:.3rem 0 0">Titre original : <i>{escape(f["original"])}</i></p>'
               if f["original"] and f["original"] != f["titre"] else ""))
    votes = nombre_fr(int(f['votes']))
    meta = [f"📅 {int(f['annee'])}" if f["annee"] == f["annee"] else "", f"{EMOJI_GENRE.get(f['genre'], '🎭')} {escape(f['genre'])}",
            f"⏱️ {int(f['duree'])} min" if f["duree"] == f["duree"] and f["duree"] else "",
            f"⭐ {note_txt(f['note'])}/10 ({votes} votes)" if note_txt(f["note"]) else "",
            f"🎟️ {nombre_fr(int(f['entrees']))} entrées France",
            f"🌍 {escape(origine_txt(f))} · {LANGUES.get(f['langue'], f['langue'])}"]
    st.html('<div class="ff-meta">' + "".join(f"<span>{x}</span>" for x in meta if x) + "</div>"
            + (f'<p class="ff-ligne">🔗 <b>Saga :</b> {escape(f["saga"])}</p>' if f["saga"] else "")
            + (f'<p class="ff-ligne">🎥 <b>Réalisation :</b> {escape(", ".join(f["real_noms"]))}</p>' if f["real_noms"] else "")
            + (f'<p class="ff-ligne">🌟 <b>Casting principal :</b> {escape(", ".join(f["acteurs_noms"][:5]))}</p>'
               if f["acteurs_noms"] else ""))
    st.markdown("### 📖 Synopsis")
    source = SOURCES_SYNOPSIS.get(f.get("source_fr", ""), "Résumé en version originale (TMDB)")
    st.html(f'<p class="ff-synopsis">{escape(f.get("resume_fr") or f["resume"] or "Résumé indisponible.")}</p>'
            f'<p class="ft-petit" style="margin-top:-.4rem">{source}</p>')
    with st.container(horizontal=True):
        st.link_button("Bande-annonce", icon=":material/play_circle:", url="https://www.youtube.com/results?search_query="
                       + quote_plus(" ".join(x for x in (f["titre"], annee_ou_vide(f["annee"]), "bande annonce") if x)))
        st.link_button("IMDb", f"https://www.imdb.com/title/{tconst}/", icon=":material/open_in_new:")
        if f.get("tmdb_id"):
            st.link_button("TMDB", f"https://www.themoviedb.org/movie/{int(f['tmdb_id'])}", icon=":material/open_in_new:")


def _pourquoi(ctx, j):
    """Volet « Pourquoi ce film pour toi ? » : une jauge par critère qui a pesé (contribution > 0,05)."""
    res = pour_toi(ctx.cat, ctx.profil, ctx.p, ctx.comm, n=1)
    contrib = {k: v for k, v in res.contributions(j).items() if v > 0.05}
    with st.expander(f"Pourquoi ce film pour toi ? · score {res.score_100(j)}/100", icon=":material/psychology:"):
        if contrib:
            maxi = max(contrib.values())
            st.html("".join(
                f'<div style="display:grid;grid-template-columns:220px 1fr 48px;gap:10px;align-items:center;margin:5px 0">'
                f'<span class="ft-petit">{LIBELLES.get(k, k)}</span><div class="ft-jauge"><i style="width:{100 * v / maxi:.0f}%"></i></div>'
                f'<span class="ft-petit">{v:.1f}</span></div>' for k, v in sorted(contrib.items(), key=lambda x: -x[1])))
            st.caption("Chaque barre = poids réglé par l'admin × ressemblance (0 à 1). Leur total donne le score.")
        else:
            st.caption("Ce film ne colle pas vraiment à ton profil : une bonne occasion de sortir de ta zone de confort !")


def _carnet(ctx, tconst, seance):
    """Séance déjà notée (s'il y en a une) et formulaire du carnet : date, lieu, note, avis."""
    cle = f"carnet_{tconst}"
    ss = st.session_state
    if seance:
        st.html(f'<div class="fc-seance" style="white-space:normal;font-size:.85rem;margin-top:.8rem">🎟️ Vu le '
                f'{date_fr(seance["date_seance"])} · '
                f'{LIEUX.get(seance["lieu"], "")} · <span class="ft-etoiles">{etoiles(seance.get("note"))}</span>'
                + (f'<br><i>« {escape(seance["avis"])} »</i>' if seance.get("avis") else "") + "</div>")
    with st.expander("Mon carnet de séance (date, lieu, note & avis)" if not seance else "Modifier ma séance",
                     icon=":material/confirmation_number:", expanded=False):
        ss.setdefault(f"{cle}_date", date.fromisoformat(seance["date_seance"]) if seance else date.today())
        ss.setdefault(f"{cle}_lieu", seance["lieu"] if seance else "cinema")
        if seance and seance.get("note") and f"{cle}_note" not in ss:
            ss[f"{cle}_note"] = int(seance["note"]) - 1
        ss.setdefault(f"{cle}_avis", seance.get("avis", "") if seance else "")
        c1, c2 = st.columns(2)
        c1.date_input("Date", key=f"{cle}_date", max_value=date.today(), format="DD/MM/YYYY")
        c2.segmented_control("Où ?", list(LIEUX), format_func=LIEUX.get, key=f"{cle}_lieu")
        st.caption("Ta note")
        st.feedback("stars", key=f"{cle}_note")
        st.text_area("Ton avis (facultatif)", key=f"{cle}_avis", max_chars=500, height=80,
                     placeholder="Ce que tu en as pensé, avec qui tu l'as vu…")
        b1, b2 = st.columns(2)
        b1.button("Enregistrer la séance", icon=":material/save:", type="primary", width="stretch",
                  on_click=enregistrer_seance, args=(tconst, cle))
        if seance:
            b2.button("Retirer du carnet", icon=":material/delete:", width="stretch", on_click=retirer_seance,
                      args=(tconst,))
