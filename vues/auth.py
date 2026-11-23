"""Accueil public, connexion et inscription en 5 étapes (façon Spotify + Netflix).

Utilise     : config (acces, affichage, catalogue, donnees, libelles, reglages_moteur), demo (profils),
              donnees (membres, securite), interface (cartes_membres, mise_en_page, textes),
              medias (affiches, avatars), moteur (profil_membre, recommandation), outils (texte)
Utilisé par : app
"""
from __future__ import annotations

import json
import random
import time
from html import escape

import streamlit as st

from config.acces import BLOCAGE_CONNEXION_S, ESSAIS_MAX
from config.affichage import DECENNIE_LIB, EMOJI_GENRE, FILMS_PAR_PAGE_INSCRIPTION
from config.catalogue import ANNEE_MAX, ANNEE_MIN
from config.donnees import EMAIL_RE, TRANCHES_AGE
from config.libelles import ETAPES_INSCRIPTION, LIBELLES_FORMAT, LIBELLES_ORIGINE, LIBELLES_STYLE_INSCRIPTION
from config.reglages_moteur import DECENNIES, PARAMS_DEFAUT
from demo.profils import COMPTE_DEMO, MDP_DEMO
from donnees import membres, securite
from interface.cartes_membres import carte_membre_cliquable, carte_membre_html, grille_avatars
from interface.mise_en_page import banniere, colonnes, section, selon_ecran
from interface.textes import balise_affiche, meta_film
from medias import avatars
from medias.affiches import url_affiche
from moteur.profil_membre import Profil
from moteur.recommandation import pour_toi
from outils.texte import nombre_fr


def afficher(ctx):
    """Accueil public : bannière, comptes de démo, connexion et inscription (ou l'assistant en cours)."""
    if st.session_state.get("inscription") is not None:
        assistant(ctx)
        return
    banniere("Quel film va lancer le <em>convecteur</em>&nbsp;?", "",
                f"Ciné-club rétro-futuriste · {nombre_fr(ctx.cat.n)} films de {ANNEE_MIN} à {ANNEE_MAX}"
                + " · recommandations sur mesure, carnet de séance et box-office France.")
    g, d = colonnes(ctx.mobile, [2.15, 1], gap="large")
    with g:
        _qui_regarde(ctx)
    with d:
        _connexion(ctx)


def _entrer_demo(uid):
    """Connecte directement un compte de démonstration."""
    ss = st.session_state
    if membres.connecter_demo(uid):
        ss.uid, ss.page = uid, "accueil"


def _qui_regarde(ctx):
    """« Qui passe la séance ce soir ? » : avatars cliquables des comptes de démo."""
    section("🎬 Qui passe la séance ce soir ?", "Comptes de démonstration : clique sur un avatar pour entrer directement.")
    demos = membres.membres_demo()
    if not demos:
        st.caption("Aucun compte de démonstration dans la base.")
        return
    with st.container(key="gmembres_demo", horizontal=True):
        for m in demos:
            genres = ", ".join(json.loads(m["genres"] or "[]")[:2])
            carte_membre_cliquable(f"demo_{m['id']}", carte_membre_html(m["avatar"], f"{m['prenom']} {m['nom']}", m["pseudo"], genres),
                                      f"Entrer en tant que {m['prenom']}", _entrer_demo, (m["id"],))


def _connexion(ctx):
    """Formulaire de connexion, avec blocage temporaire après trop d'essais."""
    ss = st.session_state
    section("🔐 Ton compte", "Connexion par e-mail et mot de passe.")
    with st.container(key="panneau_connexion", border=True):
        bloque = ss.get("login_bloque_jusqu", 0) - time.time()
        with st.form("connexion", border=False):
            email = st.text_input("Adresse e-mail", key="login_email", placeholder="toi@exemple.fr")
            mdp = st.text_input("Mot de passe", type="password", key="login_mdp")
            ok = st.form_submit_button("Se connecter", icon=":material/login:", type="primary", width="stretch", disabled=bloque > 0)
        if bloque > 0:
            st.warning(f"Trop d'essais. Réessaie dans {int(bloque) + 1} s.")
        elif ok:
            _connecter(email, mdp)
        st.button("Créer mon compte gratuitement", icon=":material/person_add:", width="stretch", on_click=_demarrer_inscription)
        st.caption(f"Démo : {COMPTE_DEMO} · mot de passe {MDP_DEMO} "
                   "(identique pour tous les membres fictifs).")


def _connecter(email, mdp):
    """Vérifie les identifiants ; compte les échecs et bloque au-delà du maximum."""
    ss = st.session_state
    uid = membres.authentifier(email or "", mdp or "")
    if uid:
        ss.uid, ss.page, ss.login_essais = uid, "accueil", 0
        ss.pop("login_mdp", None)
        st.rerun()
    ss.login_essais = ss.get("login_essais", 0) + 1
    if ss.login_essais >= ESSAIS_MAX:
        ss.login_bloque_jusqu, ss.login_essais = time.time() + BLOCAGE_CONNEXION_S, 0
    st.error("E-mail ou mot de passe incorrect.")


def _demarrer_inscription():
    """Démarre l'assistant d'inscription à zéro (avatar tiré au hasard)."""
    for k in [k for k in st.session_state if str(k).startswith("i_")]:
        del st.session_state[k]
    st.session_state.inscription = {"etape": 0, "avatar": random.choice(list(avatars.catalogue())), "genres": [],
                                    "decennies": [], "format_duree": "indifferent", "origine": "indifferent",
                                    "style": "indifferent", "coeurs": [], "page_films": 0}


# ------------------------------------------------------------------ assistant d'inscription
def assistant(ctx):
    """Assistant d'inscription : barre d'étapes puis l'étape en cours (5 étapes)."""
    ins = st.session_state.inscription
    e = ins["etape"]
    st.html('<div class="ft-etapes">' + "".join(f'<div class="{"ok" if i <= e else ""}"></div>' for i in range(len(ETAPES_INSCRIPTION)))
            + f'</div><p class="ft-surtitre">Étape {e + 1} / {len(ETAPES_INSCRIPTION)} · {ETAPES_INSCRIPTION[e]}</p>')
    [_etape_identite, _etape_avatar, _etape_genres, _etape_epoques, _etape_coeurs][e](ctx, ins)
    if ins.get("erreur"):
        st.error(ins.pop("erreur"))


def _nav(ins, suivant_label="Suivant", valider=None, dernier=False, disabled=False):
    """Boutons du bas d'une étape : Annuler / Retour à gauche, Suivant (ou Créer) à droite."""
    c1, _, c2 = st.columns([1, 2, 1.2])
    with c1:
        if ins["etape"] == 0:
            st.button("Annuler", icon=":material/close:", on_click=lambda: st.session_state.pop("inscription", None), width="stretch")
        else:
            st.button("Retour", icon=":material/arrow_back:", on_click=_etape, args=(-1,), width="stretch")
    with c2:
        if not dernier:
            st.button(suivant_label, icon=":material/arrow_forward:", type="primary", width="stretch", on_click=valider or _etape, args=() if valider else (1,),
                      disabled=disabled)


def _etape(delta):
    """Avance (+1) ou recule (−1) d'une étape."""
    st.session_state.inscription["etape"] += delta


def _etape_identite(ctx, ins):
    """Étape 1 : identité, e-mail, âge, mot de passe et consentements."""
    st.markdown("## Qui embarque dans la DeLorean ? 🚗💨")
    st.caption("Inscription réservée aux 15 ans et plus (âge du consentement numérique en France).")
    c1, c2 = colonnes(ctx.mobile, 2)
    with c1:
        st.text_input("Prénom *", value=ins.get("prenom", ""), key="i_prenom", max_chars=40)
        st.text_input("Pseudo (affiché aux autres membres)", value=ins.get("pseudo", ""), key="i_pseudo", max_chars=24,
                      placeholder="Laisse vide pour utiliser ton prénom")
        st.text_input("Adresse e-mail *", value=ins.get("email", ""), key="i_email", placeholder="toi@exemple.fr")
        st.selectbox("Tranche d'âge *", TRANCHES_AGE, index=TRANCHES_AGE.index(ins["tranche_age"]) if ins.get("tranche_age") else None,
                     key="i_age", placeholder="Choisis")
    with c2:
        st.text_input("Nom", value=ins.get("nom", ""), key="i_nom", max_chars=40)
        st.text_input("Ville", value=ins.get("ville", ""), key="i_ville", max_chars=60, placeholder="Paris")
        mdp = st.text_input("Mot de passe * (8 caractères min.)", type="password", value=ins.get("mdp", ""), key="i_mdp")
        st.text_input("Confirme le mot de passe *", type="password", value=ins.get("mdp", ""), key="i_mdp2")
        score, lib = securite.robustesse(mdp or "")
        st.html(f'<div class="ft-jauge"><i style="width:{max(score, .3) * 25}%"></i></div>'
                f'<span class="ft-petit">Robustesse : {lib}</span>')
    st.checkbox("📨 Je veux recevoir la newsletter du ciné-club", value=ins.get("newsletter", False), key="i_news")
    st.checkbox("🔐 J'accepte que mes préférences et mes avis soient utilisés pour me recommander des films. "
                "Je peux exporter ou supprimer mes données à tout moment depuis mon profil (RGPD). *",
                value=ins.get("rgpd", False), key="i_rgpd")
    _nav(ins, valider=_valider_identite)


def _valider_identite():
    """Contrôle l'étape 1 ; mémorise les champs et passe à la suite, ou affiche ce qui manque."""
    ss, ins = st.session_state, st.session_state.inscription
    v = {k: ss.get(f"i_{k}") for k in ("prenom", "pseudo", "email", "age", "nom", "ville", "mdp", "mdp2", "news", "rgpd")}
    email = (v["email"] or "").strip().lower()
    erreurs = []
    if not (v["prenom"] or "").strip():
        erreurs.append("le prénom")
    if not EMAIL_RE.match(email):
        erreurs.append("une adresse e-mail valide")
    elif membres.email_existe(email):
        ins["erreur"] = "Cette adresse e-mail a déjà un compte. Connecte-toi plutôt !"
        return
    if not v["age"]:
        erreurs.append("la tranche d'âge")
    if len(v["mdp"] or "") < 8 or securite.robustesse(v["mdp"])[0] < 2:
        erreurs.append("un mot de passe d'au moins 8 caractères mêlant lettres et chiffres")
    elif v["mdp"] != v["mdp2"]:
        erreurs.append("deux mots de passe identiques")
    if not v["rgpd"]:
        erreurs.append("ton accord sur l'utilisation des données")
    ins.update(prenom=(v["prenom"] or "").strip(), pseudo=(v["pseudo"] or "").strip(), email=email, tranche_age=v["age"],
               nom=(v["nom"] or "").strip(), ville=(v["ville"] or "").strip(), mdp=v["mdp"] or "", newsletter=bool(v["news"]),
               rgpd=bool(v["rgpd"]))
    if erreurs:
        ins["erreur"] = "Il manque : " + ", ".join(erreurs) + "."
        return
    ins["etape"] = 1


def _choisir_avatar(cle):
    """Retient l'avatar cliqué."""
    st.session_state.inscription["avatar"] = cle


def _etape_avatar(ctx, ins):
    """Étape 2 : choix de l'avatar par catégorie."""
    st.markdown("## Choisis ton avatar")
    pseudo = ins.get("pseudo") or ins.get("prenom", "")
    st.html(f'<div class="ft-av-ligne" style="margin-bottom:1rem">{avatars.img(ins["avatar"], 96, rayon=16)}<div>'
            f'<p class="ft-surtitre" style="margin:0">Qui regarde ?</p><h3 style="margin:0">{escape(pseudo)}</h3>'
            f'<span class="ft-petit">{avatars.nom(ins["avatar"])}</span></div></div>')
    cat_av = st.pills("Catégorie", ["Tous"] + avatars.categories(), default="Tous", key="i_cat_av", label_visibility="collapsed")
    grille_avatars("ins", ins["avatar"], _choisir_avatar, cat_av or "Tous")
    _nav(ins)


def _etape_genres(ctx, ins):
    """Étape 3 : au moins 3 genres préférés."""
    st.markdown("## Quels genres te font vibrer ? 🎛️")
    st.caption("Choisis-en au moins 3 — comme pour les artistes sur Spotify. Ils seront enregistrés et réutilisés.")
    options = [g for g in ctx.cat.genres if g != "Court-métrage"]
    # Valeur initiale posée via session_state (pas de « default » qui change à chaque clic : le widget serait recréé).
    st.session_state.setdefault("i_genres", list(ins["genres"]))
    choix = st.pills("Genres", options, selection_mode="multi", key="i_genres",
                     format_func=lambda g: f"{EMOJI_GENRE.get(g, '🎞️')} {g}", label_visibility="collapsed")
    ins["genres"] = list(choix)
    st.progress(min(len(choix) / 3, 1.0), f"{len(choix)} genre(s) choisi(s)" + (" ✅" if len(choix) >= 3 else " · encore un effort"))
    _nav(ins, disabled=len(choix) < 3)


def _etape_epoques(ctx, ins):
    """Étape 4 : décennies, format de durée, origine et style."""
    st.markdown("## Ton époque et ton style ⏳")
    st.markdown("**Tes décennies préférées** (au moins une)")
    ss = st.session_state
    ss.setdefault("i_dec", list(ins["decennies"]))
    for cle, champ in (("i_format", "format_duree"), ("i_origine", "origine"), ("i_style", "style")):
        ss.setdefault(cle, ins[champ])
    dec = st.pills("Décennies", DECENNIES, selection_mode="multi", key="i_dec",
                   format_func=lambda d: DECENNIE_LIB[d], label_visibility="collapsed")
    ins["decennies"] = list(dec)
    c1, c2, c3 = colonnes(ctx.mobile, 3)
    with c1:
        ins["format_duree"] = st.segmented_control("Durée idéale", list(LIBELLES_FORMAT), format_func=LIBELLES_FORMAT.get,
                                                   key="i_format") or "indifferent"
    with c2:
        ins["origine"] = st.segmented_control("Origine", list(LIBELLES_ORIGINE), format_func=LIBELLES_ORIGINE.get,
                                              key="i_origine") or "indifferent"
    with c3:
        ins["style"] = st.segmented_control("Plutôt…", list(LIBELLES_STYLE_INSCRIPTION), format_func=LIBELLES_STYLE_INSCRIPTION.get,
                                            key="i_style") or "indifferent"
    _nav(ins, disabled=not dec)


def _basculer_coeur(tconst):
    """Ajoute ou retire un film des coups de cœur de l'inscription."""
    c = st.session_state.inscription["coeurs"]
    c.remove(tconst) if tconst in c else c.append(tconst)


def _candidats(cat, ins) -> list[int]:
    """72 films à proposer, calculés à partir des choix des étapes 3 et 4."""
    pr = Profil(ins["genres"], ins["decennies"], ins["format_duree"], ins["origine"], ins["style"])
    p = dict(PARAMS_DEFAUT, popularite=5.0, qualite=1.0, diversite=6.0, masquer_vus=False)
    return pour_toi(cat, pr, p, None, n=72).indices


def _etape_coeurs(ctx, ins):
    """Étape 5 : au moins 3 coups de cœur parmi les films proposés ou recherchés."""
    cat = ctx.cat
    st.markdown("## Tes coups de cœur ❤️")
    st.caption("Sélectionne au moins 3 films que tu adores : le moteur s'en sert dès ta première visite.")
    cands = _candidats(cat, ins)
    taille = selon_ecran(ctx.mobile, FILMS_PAR_PAGE_INSCRIPTION)
    page = ins["page_films"] % max(1, len(cands) // taille)
    q = st.text_input("Ajouter un film précis", placeholder="Ex. Retour vers le futur, Amélie, Matrix…", key="i_cherche")
    montres = cat.chercher(q, 6) if q.strip() else []
    montres += [j for j in cands[page * taille:(page + 1) * taille] if j not in montres]
    deja = [cat.position[t] for t in ins["coeurs"] if cat.position.get(t) not in montres]
    with st.container(key="grille_onb", horizontal=True):
        for j in deja + montres:
            f = cat.film(j)
            choisi = f["tconst"] in ins["coeurs"]
            url = url_affiche(f["affiche"])
            img = balise_affiche(url, f["titre"]) if url else ""
            with st.container(key=f"carte_ob_{f['tconst']}"):
                st.html(f'<div class="fc-poster">{img}{"<div class=ft-coche></div>" if choisi else ""}</div>'
                        f'<div class="fc-corps"><div class="fc-titre">{escape(f["titre"])}</div>'
                        f'<div class="ft-petit">{escape(meta_film(f))}</div></div>')
                st.button(f["titre"], key=f"pst_ob_{f['tconst']}", on_click=_basculer_coeur, args=(f["tconst"],))
    n = len(ins["coeurs"])
    st.progress(min(n / 3, 1.0), f"{n} coup(s) de cœur" + (" ✅" if n >= 3 else ""))
    c1, c2, c3 = st.columns([1, 1.2, 1.4])
    with c1:
        st.button("Retour", icon=":material/arrow_back:", on_click=_etape, args=(-1,), width="stretch")
    with c2:
        st.button("Autres films", icon=":material/refresh:", width="stretch", on_click=lambda: ins.update(page_films=ins["page_films"] + 1))
    with c3:
        if st.button("Créer mon compte", icon=":material/rocket_launch:", type="primary", width="stretch", disabled=n < 3):
            _creer(ins)


def _creer(ins):
    """Crée le compte, connecte le membre et lance l'accueil (ballons de bienvenue)."""
    ss = st.session_state
    if membres.email_existe(ins["email"]):
        ins["erreur"] = "Cette adresse e-mail a déjà un compte."
        return
    uid = membres.creer_membre(ins["email"], ins["prenom"], ins.get("nom", ""), ins.get("pseudo") or ins["prenom"], ins["mdp"],
                           ins["avatar"], ins["tranche_age"], ins.get("ville", ""), ins.get("newsletter", False),
                           {k: ins[k] for k in ("genres", "decennies", "format_duree", "origine", "style")},
                           coups_de_coeur=ins["coeurs"])
    ss.pop("inscription", None)
    ss.uid, ss.page, ss.bienvenue = uid, "accueil", True
    st.rerun()
