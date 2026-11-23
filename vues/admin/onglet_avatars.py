"""Espace admin › onglet 🖼️ Avatars : import d'une planche 3 × 2 découpée automatiquement, renommer, classer,
masquer.

Utilise     : donnees (journal), etat (actions), medias (avatars)
Utilisé par : vues (admin)
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from donnees import journal
from etat.actions import annoncer
from medias import avatars


def afficher(ctx):
    """Onglet 🖼️ Avatars : import d'une planche découpée automatiquement, galerie, renommage."""
    st.markdown("#### Galerie d'avatars")
    st.caption("Dépose une planche de 6 portraits (3 colonnes × 2 lignes, .jpg ou .png) : elle est découpée automatiquement "
               "et les avatars apparaissent aussitôt à l'inscription et dans les profils.")
    fichier = st.file_uploader("Planche d'avatars 3 × 2", type=["jpg", "jpeg", "png"], key="adm_planche")
    if fichier is not None:
        contenu = fichier.getvalue()
        try:
            tuiles = avatars.apercu_planche(contenu)
        except Exception as e:  # image illisible
            st.error(f"Image illisible : {e}")
            tuiles = []
        if tuiles:
            st.caption("Aperçu du découpage :")
            cols = st.columns(6)
            for c, t in zip(cols, tuiles):
                c.image(t, width="stretch")
            c1, c2 = st.columns([1, 2])
            categorie = c1.text_input("Catégorie", value="Mes imports", key="adm_pl_cat")
            noms = c2.text_input("Noms des 6 avatars (séparés par des virgules, facultatif)", key="adm_pl_noms",
                                 placeholder="Ex. Pilote, Rockeuse, Robot, Surfeur, Magicienne, Chat")
            if st.button("Ajouter ces 6 avatars", icon=":material/add_photo_alternate:", type="primary"):
                cles = avatars.importer_planche(contenu, categorie, [n for n in noms.split(",")])
                journal.journaliser(st.session_state.get("uid"), "admin_avatars", {"ajouts": cles})
                annoncer(f"{len(cles)} avatars ajoutés", "🖼️")
                st.rerun()
    st.markdown("#### Renommer, classer ou masquer")
    meta = avatars.catalogue(tous=True)
    tableau = pd.DataFrame([{"Aperçu": avatars.url(k), "Clé": k, "Libellé": v["libelle"], "Catégorie": v["categorie"],
                             "Visible": bool(v.get("actif", True))} for k, v in meta.items()])
    edite = st.data_editor(tableau, hide_index=True, width="stretch", key="adm_av_table", disabled=["Aperçu", "Clé"],
                           column_config={"Aperçu": st.column_config.ImageColumn(width="small"),
                                          "Visible": st.column_config.CheckboxColumn(help="Décoché : l'avatar n'est plus proposé "
                                                                                          "(les membres qui l'ont le gardent)")})
    if st.button("Enregistrer la galerie", icon=":material/save:"):
        avatars.enregistrer_meta({r["Clé"]: {"libelle": r["Libellé"].strip() or r["Clé"], "categorie": r["Catégorie"].strip() or "Mes imports",
                                             "actif": bool(r["Visible"])} for r in edite.to_dict("records")})
        annoncer("Galerie d'avatars enregistrée", "🖼️")
        st.rerun()
