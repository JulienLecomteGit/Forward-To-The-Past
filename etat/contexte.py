"""Contexte d'une exécution de page (Ctx) : catalogue, communauté, réglages, affichage mobile, et le membre connecté
(fiche, préférences, avis, profil moteur, carnet). Construit une fois au début de chaque affichage.

Utilise     : donnees (carnet, catalogue, interactions, membres), etat (cache), moteur (communaute, profil_membre)
Utilisé par : app, etat (gamification)
"""
from __future__ import annotations

from dataclasses import dataclass, field

import streamlit as st

from donnees import carnet, interactions, membres
from donnees.catalogue import Catalogue
from etat.cache import communaute, parametres
from moteur.communaute import Communaute
from moteur.profil_membre import Profil, profil_membre


@dataclass
class Ctx:
    """Tout ce dont une page a besoin, construit une fois par affichage : catalogue, communauté, réglages,
    mode mobile et, si quelqu'un est connecté, le membre, ses préférences, ses interactions et son profil.
    """
    cat: Catalogue
    comm: Communaute
    p: dict
    mobile: bool
    uid: int | None = None
    membre: dict | None = None
    prefs: dict = field(default_factory=dict)
    inter: dict = field(default_factory=dict)
    profil: Profil | None = None
    seances: dict = field(default_factory=dict)

    @property
    def nb(self) -> int:
        """Nombre de films par sélection choisi par l'admin."""
        return int(self.p["nb_reco"])

    def connus(self) -> set:
        """Positions des films que le membre connaît déjà (aimés, rejetés, vus ou dans sa liste)."""
        pr = self.profil
        return set(pr.aimes) | set(pr.detestes) | pr.vus | pr.liste if pr else set()


def construire(cat) -> Ctx:
    """Construit le contexte de la page ; déconnecte si le compte a été supprimé entre-temps."""
    ctx = Ctx(cat, communaute(cat), parametres(), bool(st.session_state.get("mobile")))
    uid = st.session_state.get("uid")
    if uid:
        m = membres.membre(uid)
        if m is None:  # compte supprimé entre-temps
            st.session_state.pop("uid", None)
            return ctx
        ctx.uid, ctx.membre = uid, m
        ctx.prefs = membres.preferences(uid)
        ctx.inter = interactions.interactions(uid)
        ctx.profil = profil_membre(cat, ctx.prefs, ctx.inter, uid)
        ctx.seances = carnet.seances(uid)
    return ctx
