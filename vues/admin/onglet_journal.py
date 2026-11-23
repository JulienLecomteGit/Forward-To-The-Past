"""Espace admin › onglet 📜 Journal & base : journal d'activité filtrable, taille de la base, copie
téléchargeable, régénération des membres fictifs (démo).

Utilise     : demo (generation), donnees (base, journal), etat (actions), interface (mise_en_page), outils (texte)
Utilisé par : vues (admin)
"""
from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from demo.generation import generer as generer_demo
from donnees import base, journal
from etat.actions import annoncer
from interface.mise_en_page import section
from outils.texte import nombre_fr


def afficher(ctx, d):
    """Onglet 📜 Journal : derniers événements filtrables et régénération des membres fictifs."""
    e, m = d["evts"].copy(), d["membres"]
    pseudos = dict(zip(m.id, m.pseudo)) if len(m) else {}
    e["Membre"] = e.uid.map(lambda u: pseudos.get(u, "—") if pd.notna(u) else "—")
    types = sorted(e.type.unique())
    choix = st.multiselect("Types d'événements", types, default=types, key="j_types")
    vue = e[e.type.isin(choix)].sort_values("date", ascending=False).head(400)[["date", "Membre", "type", "detail"]]
    st.dataframe(vue.rename(columns={"date": "Date", "type": "Type", "detail": "Détail"}), hide_index=True, width="stretch", height=360)
    section("Base de données", str(base.CHEMIN_BDD))
    taille = base.CHEMIN_BDD.stat().st_size / 1e6 if base.CHEMIN_BDD.exists() else 0
    comptes = {t: base.requete(f"SELECT COUNT(*) n FROM {t}")[0]["n"] for t in ("utilisateurs", "interactions", "seances", "evenements")}
    cols = st.columns(5 if not ctx.mobile else 2)
    cols[0].metric("Taille", f"{taille:.1f} Mo")
    for c, (t, n) in zip(cols[1:], comptes.items()):
        c.metric(t.capitalize(), nombre_fr(n))
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Préparer une copie de la base (.db)", icon=":material/database:", width="stretch"):
            with base.connexion() as con:
                con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            st.session_state.copie_bdd = base.CHEMIN_BDD.read_bytes()
        if st.session_state.get("copie_bdd"):
            st.download_button("Télécharger fttp.db", icon=":material/download:", data=st.session_state.copie_bdd, file_name="fttp.db",
                               mime="application/x-sqlite3", on_click="ignore", width="stretch")
    with c2:
        with st.expander("♻️ Régénérer les membres fictifs"):
            st.caption("Remplace uniquement les membres fictifs (les vrais comptes sont conservés).")
            nb = st.number_input("Nombre de membres fictifs", 20, 1000, 180, 10)
            if st.checkbox("Je confirme", key="regen_ok") and st.button("Régénérer", type="primary"):
                barre_progres = st.progress(0.0)
                stats = generer_demo(ctx.cat, int(nb), graine=int(time.time()) % 10_000, reset=True,
                                                 progression=lambda x: barre_progres.progress(x))
                journal.journaliser(st.session_state.get("uid"), "admin_regeneration", stats)
                annoncer(f"{stats['membres']} membres fictifs recréés", "♻️")
                st.rerun()
