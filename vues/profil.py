"""Profil : en-tête avec grand avatar, Mon Rewind, jumeaux ciné, badges, préférences, avatar, infos, RGPD.

Utilise     : config (affichage, donnees, libelles, reglages_moteur), donnees (base, interactions, membres, securite),
              etat (actions, gamification, navigation), interface (barres, cartes_membres, mise_en_page, tuiles),
              medias (avatars), moteur (profil_membre), outils (texte)
Utilisé par : app
"""
from __future__ import annotations

import json
from collections import Counter
from html import escape

import numpy as np
import streamlit as st

from config.affichage import DECENNIE_LIB, EMOJI_GENRE
from config.donnees import TRANCHES_AGE
from config.libelles import LIBELLES_FORMAT, LIBELLES_ORIGINE, LIBELLES_STYLE_PROFIL
from config.reglages_moteur import DECENNIES
from donnees import base, interactions, membres, securite
from etat.actions import annoncer
from etat.gamification import badges, niveau, xp
from etat.navigation import deconnecter
from interface.barres import barre
from interface.cartes_membres import carte_membre_html, grille_avatars
from interface.mise_en_page import colonnes, section
from interface.tuiles import tuile
from medias import avatars
from moteur.profil_membre import gouts
from outils.texte import date_fr


def afficher(ctx):
    """Page Profil : en-tête (niveau, XP), Mon Rewind, jumeaux ciné, badges, puis 4 onglets de réglages."""
    aimes = np.array(ctx.profil.aimes, dtype=int)
    _entete(ctx)
    _rewind(ctx, aimes)
    _jumeaux(ctx, aimes)

    section("🏅 Badges", "débloque-les en explorant le catalogue")
    st.html(_badges_html(badges(ctx)))

    st.write("")
    t1, t2, t3, t4 = st.tabs(["🧬 Mes préférences", "🖼️ Mon avatar", "👤 Mes infos", "🔐 Mes données (RGPD)"])
    with t1:
        _preferences(ctx)
    with t2:
        _avatar(ctx)
    with t3:
        _infos(ctx)
    with t4:
        _rgpd(ctx)


def _entete(ctx):
    """Grand avatar, niveau, pseudo, identité et jauge d'XP vers le niveau suivant."""
    m = ctx.membre
    nb_cnx = base.requete("SELECT COUNT(*) n FROM evenements WHERE utilisateur_id=? AND type LIKE 'connexion%'", (ctx.uid,))[0]["n"]
    points = xp(ctx, nb_cnx) + 5 * len(ctx.seances)
    num, titre, prog, reste = niveau(points)
    st.html(f"""<div class="fp-entete"><img src="{avatars.url(m['avatar'])}" alt="Avatar">
<div style="flex:1;min-width:240px"><div class="fp-niveau">Niveau {num} · {escape(titre)}</div><h2>{escape(m['pseudo'])}</h2>
<div class="ft-petit">{escape(m['prenom'])} {escape(m['nom'])} · {escape(m['email'])} · membre depuis le {date_fr(m['date_inscription'])}</div>
<div style="margin-top:.9rem;display:flex;gap:.8rem;align-items:center"><div class="ft-jauge" style="flex:1"><i style="width:{prog * 100:.0f}%"></i></div>
<span class="ft-badge-xp">⚡ {points} XP</span></div>
<div class="ft-petit" style="margin-top:.35rem">{f"Encore {reste} XP pour le niveau suivant" if reste else "Niveau maximum atteint !"}</div></div></div>""")


def _rewind(ctx, aimes):
    """🎞️ Mon Rewind : 6 tuiles tirées des films aimés (genre, décennie, réalisateur, acteur, heures, note)."""
    cat = ctx.cat
    section("🎞️ Mon Rewind", "ton année ciné en un coup d'œil")
    if len(aimes):
        g = Counter(cat.df.genre.to_numpy()[aimes]).most_common(1)[0]
        d = Counter(cat.decennie[aimes]).most_common(1)[0]
        reals = Counter(p for j in aimes for p in cat.real[j]).most_common(1)
        acts = Counter(p for j in aimes for p in cat.acteurs[j]).most_common(1)
        heures = int(np.nansum(cat.duree[aimes]) // 60)
        notes = [v for v in ctx.inter["note"].values() if v]
        tuiles = [tuile("Genre n°1", f"{EMOJI_GENRE.get(g[0], '🎞️')}", f"{g[0]} · {g[1]} films"),
                  tuile("Ta décennie", DECENNIE_LIB.get(int(d[0]), str(d[0])), f"{d[1]} films aimés"),
                  tuile("Réalisateur fétiche", f"{reals[0][1]} films" if reals else "—", cat.noms.get(reals[0][0], "") if reals else ""),
                  tuile("Acteur fétiche", f"{acts[0][1]} films" if acts else "—", cat.noms.get(acts[0][0], "") if acts else ""),
                  tuile("Heures aimées", f"{heures} h", f"{len(aimes)} films · {int(cat.fr[aimes].mean() * 100)} % français"),
                  tuile("Ta note moyenne", f"{np.mean(notes):.1f}".replace(".", ",") if notes else "—", f"{len(notes)} notes")]
        with st.container(key="gmembres_rewind", horizontal=True):
            for t in tuiles:
                st.html(t)
    else:
        st.caption("Aime quelques films pour débloquer ton Rewind.")


def _jumeaux(ctx, aimes):
    """👯 Les 4 membres aux goûts les plus proches, avec le nombre de films aimés en commun."""
    cat, pr = ctx.cat, ctx.profil
    _, voisins = ctx.comm.membre(pr.aimes, exclure_uid=ctx.uid, k=4)
    if voisins:
        section("👯 Tes jumeaux ciné", "les membres dont les goûts ressemblent le plus aux tiens")
        mes = {cat.df.tconst[j] for j in aimes}
        with st.container(key="gmembres_jumeaux", horizontal=True):
            for vid, _ in voisins:
                v = membres.membre(vid)
                if not v:
                    continue
                communs = len(set(interactions.interactions(vid)["like"]) & mes)
                genres = ", ".join(membres.preferences(vid)["genres"][:2])
                st.html(carte_membre_html(v["avatar"], v["pseudo"], f"{v['prenom']} · {v.get('ville') or ''}".strip(" ·"),
                                          genres, f"❤️ {communs} film{'s' if communs > 1 else ''} en commun"))


def _badges_html(badges: list[dict]) -> str:
    """Compteur de badges et grille des badges (débloqués ou avec leur progression)."""
    gagnes = sum(b["ok"] for b in badges)
    cartes = []
    for b in badges:
        if b["ok"]:
            pied = '<div class="fb-ok">✓ Débloqué</div>'
        else:
            pct = 100 * b["valeur"] / b["objectif"]
            pied = (f'<div class="fb-prog"><div class="ft-jauge"><i style="width:{pct:.0f}%"></i></div>'
                    f'<span>{b["valeur"]}/{b["objectif"]}</span></div>')
        cartes.append(f'<div class="fb-carte {"ok" if b["ok"] else "off"}"><div class="fb-medaille">{b["icone"]}</div>'
                      f'<div class="fb-texte"><div class="fb-titre">{escape(b["titre"])}</div>'
                      f'<div class="fb-cond">{escape(b["condition"])}</div>{pied}</div></div>')
    return (f'<div class="fb-tete"><b>{gagnes} / {len(badges)}</b> badges débloqués'
            f'<div class="ft-jauge"><i style="width:{100 * gagnes / len(badges):.0f}%"></i></div></div>'
            f'<div class="fb-grille">{"".join(cartes)}</div>')


# ------------------------------------------------------------------ préférences
def _init_prefs(p: dict):
    """Remplit les choix de l'onglet avec les préférences du membre (une fois par membre connecté)."""
    ss = st.session_state
    if ss.get("pf_uid") != ss.get("uid"):  # nouveau membre connecté : on recharge ses choix
        for k in [k for k in ss if str(k).startswith("pf_")]:
            del ss[k]
        ss.pf_uid = ss.get("uid")
    ss.setdefault("pf_genres", list(p["genres"]))
    ss.setdefault("pf_dec", [int(d) for d in p["decennies"]])
    ss.setdefault("pf_format", p["format_duree"])
    ss.setdefault("pf_origine", p["origine"])
    ss.setdefault("pf_style", p["style"])


def _adn_html(ctx, ss) -> str:
    """ADN ciné : choix en cours (aperçu immédiat) + ce que le moteur utilise réellement en ce moment."""
    puces = lambda items, cls="": "".join(f'<span class="ft-chip {cls}">{x}</span>' for x in items) or '<span class="fa-vide">—</span>'  # noqa: E731
    genres = puces([f"{EMOJI_GENRE.get(g, '🎞️')} {escape(g)}" for g in ss.pf_genres or []])
    decs = puces([DECENNIE_LIB.get(d, str(d)) for d in sorted(ss.pf_dec or [])], "teal")
    duree = puces([LIBELLES_FORMAT.get(ss.pf_format or "indifferent", "")], "rose")
    ligne = puces([LIBELLES_ORIGINE.get(ss.pf_origine or "indifferent", ""), LIBELLES_STYLE_PROFIL.get(ss.pf_style or "indifferent", "")], "rose")
    repartition = gouts(ctx.cat, ctx.profil, ctx.p)
    parts = sorted(((ctx.cat.genres[k], float(v)) for k, v in enumerate(repartition) if v >= 0.04), key=lambda x: -x[1])
    wd, wh = float(ctx.p["declare"]), float(ctx.p["historique"])
    dosage = f"{100 * wd / ((wd + wh) or 1):.0f} % tes choix · {100 * wh / ((wd + wh) or 1):.0f} % tes réactions ❤️ ➕ 🤮 🎟️"
    moteur_html = (f'<div class="fa-moteur"><div class="fa-lab">Ce que le moteur utilise en ce moment <span>{dosage}</span></div>'
                   f'{barre([(f"{EMOJI_GENRE.get(g, chr(127902))} {g}", v) for g, v in parts])}</div>' if parts else "")
    return (f'<div class="fa-tete"><div><p class="fp-bloc-titre">🧬 Ton ADN ciné</p><p class="fp-bloc-aide" style="margin:0">'
            f'Tes choix ci-dessous pèsent directement sur tes recommandations — tes réactions dans l\'app les affinent.</p></div></div>'
            f'<div class="fa-grille"><div class="fa-bloc"><div class="fa-lab">🎭 Genres</div><div class="fa-val">{genres}</div></div>'
            f'<div class="fa-bloc"><div class="fa-lab">📅 Époques</div><div class="fa-val">{decs}</div></div>'
            f'<div class="fa-bloc"><div class="fa-lab">⏱️ Format</div><div class="fa-val">{duree}</div></div>'
            f'<div class="fa-bloc"><div class="fa-lab">🎯 Ligne</div><div class="fa-val">{ligne}</div></div></div>{moteur_html}'
            f'<div class="fp-separateur" style="margin-top:1rem"></div>')


def _sauver_prefs():
    """Enregistre les préférences si au moins 3 genres et une décennie sont choisis."""
    ss = st.session_state
    if len(ss.pf_genres or []) < 3 or not ss.pf_dec:
        annoncer("Choisis au moins 3 genres et une décennie.", "⚠️")
        return
    membres.enregistrer_preferences(ss.uid, {"genres": ss.pf_genres, "decennies": ss.pf_dec, "format_duree": ss.pf_format or "indifferent",
                                         "origine": ss.pf_origine or "indifferent", "style": ss.pf_style or "indifferent"})
    annoncer("Préférences enregistrées : tes recommandations sont recalculées", "🧬")


def _preferences(ctx):
    """Onglet 🧬 Mes préférences : ADN ciné, genres, décennies, format, origine, style."""
    ss = st.session_state
    _init_prefs(ctx.prefs)
    with st.container(key="prefs"):
        st.html(_adn_html(ctx, ss))
        st.html('<p class="fp-bloc-titre">🎭 Genres préférés</p><p class="fp-bloc-aide">3 minimum — plus tu en choisis, plus '
                'les propositions sont variées.</p>')
        st.pills("Genres", [g for g in ctx.cat.genres if g != "Court-métrage"], selection_mode="multi", key="pf_genres",
                 format_func=lambda g: f"{EMOJI_GENRE.get(g, '')} {g}", label_visibility="collapsed")
        st.html('<p class="fp-bloc-titre">📅 Décennies</p><p class="fp-bloc-aide">Les décennies voisines comptent à moitié.</p>')
        st.pills("Décennies", DECENNIES, selection_mode="multi", key="pf_dec",
                 format_func=lambda d: DECENNIE_LIB[d], label_visibility="collapsed")
        cols = colonnes(ctx.mobile, 3)
        blocs = [("pf_format", "⏱️ Durée idéale", "Favorise les films de cette longueur.", LIBELLES_FORMAT),
                 ("pf_origine", "🌍 Origine", "Coup de pouce (ou non) au cinéma français.", LIBELLES_ORIGINE),
                 ("pf_style", "🏆 Plutôt…", "Grands succès en salles ou films méconnus.", LIBELLES_STYLE_PROFIL)]
        for col, (cle, titre, aide, options) in zip(cols, blocs):
            with col:
                with st.container(key=f"pcarte_{cle}"):
                    st.html(f'<p class="fp-bloc-titre">{titre}</p><p class="fp-bloc-aide">{aide}</p>')
                    st.segmented_control(titre, list(options), format_func=options.get, key=cle, label_visibility="collapsed")
        modifie = (sorted(ss.pf_genres or []) != sorted(ctx.prefs["genres"]) or sorted(ss.pf_dec or []) != sorted(ctx.prefs["decennies"])
                   or ss.pf_format != ctx.prefs["format_duree"] or ss.pf_origine != ctx.prefs["origine"] or ss.pf_style != ctx.prefs["style"])
        c1, c2 = st.columns([3, 1.3], vertical_alignment="center")
        c1.caption("✏️ Modifications non enregistrées" if modifie else "✅ À jour")
        c2.button("Enregistrer mes préférences", icon=":material/save:", type="primary", width="stretch",
                  on_click=_sauver_prefs, disabled=not modifie)


# ------------------------------------------------------------------ avatar, infos, RGPD
def _changer_avatar(cle):
    """Enregistre le nouvel avatar et l'annonce."""
    membres.modifier_membre(st.session_state.uid, avatar=cle)
    annoncer(f"Nouvel avatar : {avatars.nom(cle)}", "🖼️")


def _avatar(ctx):
    """Onglet 🖼️ Mon avatar : grille d'avatars par catégorie."""
    cat_av = st.pills("Catégorie", ["Tous"] + avatars.categories(), default="Tous", key="prof_cat_av", label_visibility="collapsed")
    grille_avatars("prof", ctx.membre["avatar"], _changer_avatar, cat_av or "Tous")


def _infos(ctx):
    """Onglet 👤 Mes infos : identité, newsletter et changement de mot de passe."""
    m = ctx.membre
    with st.form("infos"):
        c1, c2 = st.columns(2)
        pseudo = c1.text_input("Pseudo", m["pseudo"], max_chars=24)
        prenom = c2.text_input("Prénom", m["prenom"], max_chars=40)
        nom = c1.text_input("Nom", m["nom"], max_chars=40)
        ville = c2.text_input("Ville", m["ville"] or "", max_chars=60)
        age = c1.selectbox("Tranche d'âge", TRANCHES_AGE,
                           index=TRANCHES_AGE.index(m["tranche_age"]) if m["tranche_age"] in TRANCHES_AGE else 0)
        news = c2.checkbox("Newsletter", bool(m["newsletter"]))
        if st.form_submit_button("Enregistrer", icon=":material/save:", type="primary"):
            membres.modifier_membre(ctx.uid, pseudo=pseudo.strip() or prenom, prenom=prenom.strip() or m["prenom"], nom=nom.strip(),
                                ville=ville.strip(), tranche_age=age, newsletter=int(news))
            annoncer("Infos mises à jour", "✅")
            st.rerun()
    with st.form("mdp", clear_on_submit=True):
        st.markdown("**Changer de mot de passe**")
        a = st.text_input("Mot de passe actuel", type="password")
        n1 = st.text_input("Nouveau mot de passe", type="password")
        n2 = st.text_input("Confirmation", type="password")
        if st.form_submit_button("Changer le mot de passe", icon=":material/key:"):
            if n1 != n2 or len(n1) < 8 or securite.robustesse(n1)[0] < 2:
                st.error("Nouveau mot de passe trop faible ou différent de la confirmation.")
            elif not membres.changer_mdp(ctx.uid, a, n1):
                st.error("Mot de passe actuel incorrect.")
            else:
                st.success("Mot de passe changé.")


def _rgpd(ctx):
    """Onglet 🔐 Mes données : ce qui est stocké, export JSON et suppression du compte."""
    st.markdown("Tes données t'appartiennent. Ce qui est stocké : identité, préférences, avis (j'aime, notes, liste), "
                "carnet de séance et journal d'activité. Ton mot de passe n'est jamais stocké en clair (empreinte PBKDF2-SHA256).")
    donnees = json.dumps(membres.export_membre(ctx.uid), ensure_ascii=False, indent=2)
    st.download_button("Télécharger toutes mes données (JSON)", data=donnees, icon=":material/download:",
                       file_name=f"mes_donnees_fttp_{ctx.uid}.json", mime="application/json", on_click="ignore")
    with st.expander("Supprimer mon compte", icon=":material/delete:"):
        st.warning("Suppression définitive : profil, préférences, avis, carnet et liste. Action irréversible.")
        conf = st.text_input("Tape SUPPRIMER pour confirmer", key="conf_suppr")
        if st.button("Supprimer définitivement mon compte", disabled=conf != "SUPPRIMER", type="primary"):
            membres.supprimer_membre(ctx.uid)
            deconnecter()
            st.rerun()
