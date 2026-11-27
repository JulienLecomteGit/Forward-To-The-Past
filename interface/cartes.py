"""Cartes film (affiche, réactions ❤️ ➕ 🤮, score, chiffres) et grilles de cartes ; ligne compacte de « Mes films ».

Un clic sur l'affiche ouvre la fiche (etat/navigation) ; un clic sur une réaction l'enregistre (etat/actions).

Utilise     : config (affichage), etat (actions, navigation), interface (textes), medias (affiches),
              moteur (explications), outils (texte)
Utilisé par : vues (accueil, explorer, fiche, machine, mes_films), vues/admin (onglet_membres)
"""
from __future__ import annotations

from html import escape

import streamlit as st

from config.affichage import REACTIONS
from etat.actions import basculer
from etat.navigation import ouvrir_fiche
from interface.textes import balise_affiche, etoiles, meta_film, note_txt, resume_court
from medias.affiches import url_affiche
from moteur.explications import pourquoi
from outils.texte import annee_txt, date_fr, format_entrees


def reactions(f: dict, inter: dict, cle_conteneur: str, prefixe: str, suffixe: str, source: str) -> None:
    """Ligne « année · genre » + boutons ❤️ ➕ 🤮 (clé des boutons : <prefixe>_<type>_<suffixe>). Carte et fiche film."""
    t = f["tconst"]
    with st.container(key=cle_conteneur, horizontal=True):
        annee = annee_txt(f["annee"])
        st.html(f'<div class="fc-meta"><span class="fc-annee">{annee}</span><span class="fc-genre">· {escape(f["genre"])}</span></div>')
        for type_, emoji, aide in REACTIONS:
            actif = t in inter.get(type_, {})
            st.button(emoji, key=f"{prefixe}_{type_}_{suffixe}", help=aide + (" ✓" if actif else ""), on_click=basculer,
                      args=(t, type_, source), type="primary" if actif else "secondary")


def carte(cat, j: int, cle: str, origine: str, inter: dict | None, score=None, raison: str = "", seance: dict | None = None,
          actions=None) -> None:
    """Carte d'un film : jaquette cliquable, note, entrées, raison de la recommandation et boutons de réaction
    (ou boutons d'action fournis par la page).
    """
    f = cat.film(j)
    t = f["tconst"]
    inter = inter or {}
    url = url_affiche(f["affiche"])
    img = balise_affiche(url, f["titre"])
    badges = ""
    if f["fr"]:
        badges += '<span class="fc-fr">🇫🇷 FR</span>'
    if t in inter.get("vu", {}):
        badges += '<span class="fc-vu">VU</span>'
    sc = f'<div class="fc-score">⚡ {score}</div>' if score is not None else ""
    with st.container(key=f"carte_{cle}"):
        st.html(f'<div class="fc-poster">{img}{sc}<div class="fc-badges">{badges}</div></div>')
        st.button(f["titre"], key=f"pst_{cle}", on_click=ouvrir_fiche, args=(t, origine))
        reactions(f, inter, f"reac_{cle}", "r", cle, origine)
        chip = ""
        if seance:
            chip = (f'<div class="fc-seance">🎟️ {date_fr(seance["date_seance"])}'
                    f' · {etoiles(seance.get("note"))} {escape(seance.get("avis") or "")}</div>')
        note = note_txt(f["note"]) or "—"
        duree = f"{int(f['duree'])} min" if f["duree"] == f["duree"] and f["duree"] else "—"
        st.html(f'<div class="fc-corps"><div class="fc-titre">{escape(f["titre"])}</div>'
                f'<div class="fc-pourquoi">{escape(raison or resume_court(f))}</div>{chip}'
                f'<div class="fc-chiffres"><span class="fc-note">⭐ {note}</span><span class="fc-bo">🎟️ {format_entrees(f["entrees"])}</span>'
                f'<span class="fc-duree">⏱️ {duree}</span></div></div>')
        if actions:
            with st.container(key=f"act_{cle}", horizontal=True):
                for libelle, icone, rappel, args, aide in actions:
                    st.button(libelle, icon=icone, key=f"a_{cle}_{libelle}", on_click=rappel, args=args, help=aide, width="stretch")


def grille(cat, indices, cle: str, origine: str, inter=None, res=None, raisons: bool = True, seances=None, actions=None) -> None:
    """Rangée de cartes ; message « Rien à afficher » si la liste est vide."""
    if not len(indices):
        st.caption("Rien à afficher ici pour l'instant.")
        return
    with st.container(key=f"grille_{cle}", horizontal=True):
        for j in indices:
            t = cat.df.tconst[j]
            raison = " · ".join(pourquoi(cat, res, j, 2)) if (res is not None and raisons) else ""
            carte(cat, j, f"{cle}_{t}", origine, inter, score=res.score_100(j) if res is not None else None,
                  raison=raison, seance=(seances or {}).get(t), actions=actions(j) if actions else None)


def ligne_film(cat, j: int, cle: str, origine: str, sous_html: str, rappel, args, aide: str) -> None:
    """Carte-ligne : un clic ouvre la fiche, la corbeille (en bas à droite) retire le film de la liste."""
    f = cat.film(j)
    url = url_affiche(f["affiche"], "w185")
    img = f'<img src="{url}" alt="" loading="lazy">'
    with st.container(key=f"lf_{cle}"):
        st.html(f'<div class="fl-ligne">{img}<div><div class="fl-titre">{escape(f["titre"])}</div>'
                f'<div class="fl-meta">{escape(meta_film(f))}</div>{sous_html}</div></div>')
        st.button(f"Ouvrir la fiche de {f['titre']}", key=f"lfo_{cle}", on_click=ouvrir_fiche, args=(f["tconst"], origine))
        st.button("Retirer", icon=":material/delete:", key=f"lfx_{cle}", on_click=rappel, args=args, help=aide)
