"""Forward To The Past · ciné-club. Lancer avec : python -m streamlit run app.py

Point d'entrée : configuration de la page, bandeau (logo, Mobile, Admin, menu, compte), puis la page choisie.

Utilise     : demo (generation), donnees (base), etat (actions, cache, contexte, navigation),
              interface (textes, theme), medias (avatars),
              vues (accueil, admin, auth, explorer, fiche, machine, mes_films, profil)
Utilisé par : —
"""
import streamlit as st

st.set_page_config(page_title="Forward To The Past · Ciné-club 88 MPH", page_icon="🌴", layout="wide",
                   initial_sidebar_state="collapsed")

from demo.generation import generer as generer_demo  # noqa: E402
from donnees import base  # noqa: E402
from medias import avatars  # noqa: E402
from etat.actions import afficher_toasts  # noqa: E402
from etat.cache import catalogue  # noqa: E402
from etat.contexte import construire  # noqa: E402
from etat.navigation import aller, deconnecter  # noqa: E402
from interface.textes import logo_html  # noqa: E402
from interface.theme import injecter_theme, style  # noqa: E402
from vues import accueil, admin, auth, explorer, fiche, mes_films, machine, profil  # noqa: E402

PAGES = {  # clé : (libellé, icône, fonction) — ordre de la barre de navigation
    "accueil": ("Pour toi", ":material/local_fire_department:", accueil.afficher),
    "explorer": ("Explorer", ":material/search:", explorer.afficher),
    "machine": ("88 MPH", ":material/bolt:", machine.afficher),
    "mesfilms": ("Mes films", ":material/movie:", mes_films.afficher),
    "profil": ("Profil", ":material/person:", profil.afficher),
}


def etat_initial():
    """Valeurs de départ de la session : détection mobile au premier chargement, page d'accueil."""
    ss = st.session_state
    if "ua_mobile" not in ss:
        agent = st.context.headers.get("User-Agent", "") if st.context.headers else ""
        ss.ua_mobile = any(m in agent for m in ("Mobi", "Android", "iPhone", "iPad"))
        ss.mobile = ss.ua_mobile  # bascule auto au premier chargement, modifiable ensuite
    ss.setdefault("page", "accueil")


def entete(ctx):
    """Bandeau du haut : logo, interrupteur Mobile, bouton Admin, puis menu des pages et compte du membre."""
    ss = st.session_state
    with st.container(key="entete", horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
        st.html(logo_html())
        with st.container(key="droite", horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
            st.toggle("Mobile", key="mobile", help="Affichage mobile (sur ordinateur : aperçu dans un cadre de téléphone).")
            if ss.page != "admin":
                st.button("Admin", icon=":material/lock:", key="btn_admin", on_click=aller, args=("admin",))
            if ss.page == "admin":
                st.html('<span class="ft-pastille-admin">🔒 Espace admin</span>')
            elif ctx.uid:
                m = ctx.membre
                style(f".st-key-menu_membre [data-testid=\"stPopoverButton\"]::before{{content:'';width:32px;height:32px;"
                         f"border-radius:9px;background:url({avatars.data_uri(m['avatar'])}) center/cover;margin-right:.5rem}}")
                with st.container(key="menu_membre"):
                    with st.popover(m["pseudo"]):
                        st.html(f'<div class="ft-av-ligne">{avatars.img(m["avatar"], 56)}<div><b>{m["prenom"]} {m["nom"]}</b>'
                                f'<br><span class="ft-petit">{m["email"]}</span></div></div>')
                        st.button("Mon profil", icon=":material/person:", on_click=aller, args=("profil",), width="stretch")
                        st.button("Changer de profil", icon=":material/switch_account:", on_click=deconnecter,
                                  width="stretch")
    if ctx.uid and ss.page != "admin":  # l'espace admin n'affiche pas la navigation des membres
        page_nav = ss.get("page_avant", "accueil") if ss.page == "fiche" else ss.page
        with st.container(key="nav", horizontal=True):
            for cle, (lib, icone, _) in PAGES.items():
                st.button(lib, icon=icone, key=f"nav_{cle}", on_click=aller, args=(cle,),
                          type="primary" if page_nav == cle else "secondary", width="stretch")


def main():
    """Point d'entrée : thème, catalogue, base (démo créée si vide), contexte, puis la page demandée."""
    etat_initial()
    ss = st.session_state
    injecter_theme(ss.mobile, cadre=ss.mobile and not ss.ua_mobile)
    cat = catalogue()
    if cat is None:
        st.stop()
    base.initialiser()
    if base.nb_membres() == 0:
        barre = st.progress(0.0, "Première mise en route : création des membres fictifs…")
        stats = generer_demo(cat, progression=lambda x: barre.progress(x, "Création des membres fictifs…"))
        barre.empty()
        st.toast(f"Base créée : {stats['membres']} membres, {stats['interactions']} interactions", icon="🗄️")
    ctx = construire(cat)
    entete(ctx)
    afficher_toasts()
    if ss.page == "admin":
        admin.afficher(ctx)
    elif not ctx.uid:
        auth.afficher(ctx)
    elif ss.page == "fiche" and ss.get("fiche"):
        fiche.afficher(ctx)
    else:
        PAGES.get(ss.page, PAGES["accueil"])[2](ctx)
    st.html('<p class="ft-petit" style="text-align:center;margin-top:2.5rem;opacity:.7">Forward To The Past · '
            'ciné-club du projet CNC · données IMDb &amp; TMDB · affiches © TMDB · moteur de recommandation v2</p>')


main()
