"""Génère des membres fictifs cohérents pour la démo (préférences, j'aime, notes, liste, connexions).

Usage (terminal VS Code, environnement activé) :
    python -m demo.generation              # crée 180 membres si la base est vide
    python -m demo.generation --nb 250 --reset   # remplace les membres fictifs (les vrais sont conservés)

Chaque membre appartient à une « tribu » de goûts (Nostalgiques 80s, Comédie à la française…) :
ses préférences déclarées et ses films aimés en découlent, avec du hasard. C'est ce qui donne
au filtrage collaboratif (« les membres qui te ressemblent ») un vrai signal à exploiter.
Tous les comptes fictifs utilisent le mot de passe « retro1985 » et une adresse @example.com
(domaine réservé à la documentation, aucun risque d'écrire à une vraie personne).

Utilise     : donnees (base, membres, securite, catalogue), medias/avatars, config, outils, demo/profils.
Utilisé par : app (premier lancement, base vide), vues/admin (bouton « Régénérer les membres fictifs »).
"""
from __future__ import annotations

import argparse
import json
import random
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np

from config.catalogue import CSV_NOM
from config.chemins import RACINE
from config.donnees import LIEUX
from config.reglages_moteur import DECENNIES, FORMATS_DUREE
from demo.profils import (
    AGE_PAR_DECENNIE,
    AVIS_NEGATIFS,
    AVIS_POSITIFS,
    COMPTE_DEMO,
    DEMOS,
    MDP_DEMO,
    NOMS,
    PRENOMS,
    TRIBUS,
    VIDES,
    VILLES,
)
from donnees import base, membres, securite
from donnees.catalogue import Catalogue, chemin_csv, lire_catalogue
from medias import avatars
from outils.calcul import proximite, ramener_entre_0_et_1


def _ascii(s: str) -> str:
    """Texte sans accents, en minuscules et sans espaces (pour fabriquer les adresses e-mail)."""
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower().replace(" ", "")


def _gumbel_top(rng, logits, k, interdits=()):
    """Tire k positions au hasard, d'autant plus probables que leur score est haut (astuce de Gumbel)."""
    cle = logits + rng.gumbel(size=len(logits))
    if len(interdits):
        cle[list(interdits)] = -np.inf
    return [int(j) for j in np.argsort(-cle)[:k]]


def _instant(rng, debut: datetime, fin: datetime) -> str:
    """Horodatage aléatoire entre deux dates, plutôt le soir (pic 20-22 h)."""
    jour = debut + timedelta(seconds=float(rng.uniform(0, max((fin - debut).total_seconds(), 60))))
    heure = int(np.clip(rng.normal(20.5, 2.6), 7, 23)) if rng.random() < 0.8 else int(rng.integers(8, 19))
    t = jour.replace(hour=heure, minute=int(rng.integers(0, 60)), second=int(rng.integers(0, 60)))
    return min(max(t, debut), fin).strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class _Generation:
    """Ce que partagent toutes les étapes : catalogue, deux générateurs de hasard, horloge, films cultes
    des tribus et lignes à écrire en base (accumulées puis insérées d'un coup à la fin)."""
    cat: Catalogue
    rng: np.random.Generator
    rnd: random.Random
    maintenant: datetime
    cultes: dict
    interactions: list = field(default_factory=list)
    evenements: list = field(default_factory=list)
    seances: list = field(default_factory=list)


def generer(cat: Catalogue, nb: int = 180, graine: int = 1985, reset: bool = False, progression=None) -> dict:
    """Crée `nb` membres fictifs et toute leur activité. L'ordre des étapes fixe l'ordre des tirages au
    hasard : le changer changerait la base de démo produite."""
    base.initialiser()
    if reset:
        with base.connexion() as con:
            con.execute("DELETE FROM utilisateurs WHERE est_fictif = 1")
    rng = np.random.default_rng(graine)
    rnd = random.Random(graine)
    maintenant = datetime.now().replace(microsecond=0)
    poids_tribus = np.array([t[5] for t in TRIBUS], float)
    poids_tribus /= poids_tribus.sum()
    gen = _Generation(cat, rng, rnd, maintenant, _films_cultes(cat, rng))
    profils = [_tirer_profil(gen, k, poids_tribus) for k in range(nb)]
    _rendre_adresses_uniques(profils)
    hashes = _hacher_mots_de_passe(len(profils))
    with base.connexion() as con:
        for idx, (p, h) in enumerate(zip(profils, hashes)):
            _creer_membre(con, gen, p, h)
            if progression:
                progression((idx + 1) / len(profils))
        _enregistrer(con, gen)
    return {"membres": len(profils), "interactions": len(gen.interactions), "seances": len(gen.seances),
            "evenements": len(gen.evenements)}


def _films_cultes(cat: Catalogue, rng) -> dict:
    """Films « cultes » de chaque tribu : ce qui crée un vrai signal communautaire."""
    cultes = {}
    for nom, genres, decs, origine, style, _ in TRIBUS:
        affinite = (np.isin(cat.df["genre"].to_numpy(), genres) * 2.0 + np.isin(cat.decennie, decs) * 1.2
                    + cat.pop * (1.5 if style == "cultes" else 0.5) + cat.qualite * (1.5 if style == "pepites" else 0.6)
                    + (cat.fr * 1.0 if origine == "francais" else 0))
        cultes[nom] = set(_gumbel_top(rng, affinite * 3.0, 45))
    return cultes


def _tirer_profil(gen: _Generation, k: int, poids_tribus) -> dict:
    """Identité, tribu, préférences et date d'inscription du k-ième membre (les premiers sont les comptes DEMOS)."""
    cat, rng, rnd, maintenant = gen.cat, gen.rng, gen.rnd, gen.maintenant
    demo = DEMOS[k] if k < len(DEMOS) else None
    t = demo["tribu"] if demo else int(rng.choice(len(TRIBUS), p=poids_tribus))
    nom_t, genres_t, decs_t, origine_t, style_t, _ = TRIBUS[t]
    genres = rnd.sample(genres_t, k=min(len(genres_t), rnd.randint(2, 3)))
    if rnd.random() < 0.45:
        autre = rnd.choice([g for g in cat.genres if g not in genres and g != "Court-métrage"])
        genres.append(autre)
    decennies = sorted(set(rnd.sample(decs_t, k=min(len(decs_t), rnd.randint(1, 2)))
                           + ([rnd.choice(DECENNIES)] if rnd.random() < 0.35 else [])))
    prefs = {"genres": genres, "decennies": decennies,
             "format_duree": rnd.choices(["court", "standard", "long", "indifferent"], [.22, .38, .12, .28])[0],
             "origine": origine_t if rnd.random() < 0.6 else rnd.choice(["francais", "international", "indifferent"]),
             "style": style_t if rnd.random() < 0.6 else rnd.choice(["cultes", "pepites", "indifferent"])}
    if demo:
        prenom, nom, pseudo, avatar, ville, age = (demo[c] for c in ("prenom", "nom", "pseudo", "avatar", "ville", "age"))
        email = f"{_ascii(prenom)}.{_ascii(nom)}@example.com"
        prefs = {c: demo[c] for c in ("genres", "decennies", "format_duree", "origine", "style")}
    else:
        prenom, nom = rnd.choice(PRENOMS), rnd.choice(NOMS)
        email = f"{_ascii(prenom)}.{_ascii(nom)}{rnd.randint(1, 99) if rnd.random() < .5 else ''}@example.com"
        pseudo = rnd.choice([prenom, f"{prenom}{nom[0]}", f"{prenom}_{rnd.choice(['88', '85', 'VHS', 'retro', 'cine'])}",
                             f"{_ascii(prenom).capitalize()}{rnd.randint(70, 99)}"])
        avatar = rnd.choice(list(avatars.catalogue()))
        ville = rnd.choice(VILLES)
        age = rnd.choice(AGE_PAR_DECENNIE[rnd.choice(decennies)])
    jours = 1 + 150 * rng.random() ** 1.7  # plus d'inscriptions récemment : la croissance se voit
    inscription = maintenant - timedelta(days=float(jours))
    return dict(prenom=prenom, nom=nom, pseudo=pseudo, email=email, avatar=avatar, ville=ville, age=age,
                prefs=prefs, tribu=nom_t, inscription=inscription, demo=demo)


def _rendre_adresses_uniques(profils: list) -> None:
    """Ajoute un numéro aux adresses déjà prises (en base ou dans ce lot)."""
    vus = {r["email"] for r in base.requete("SELECT email FROM utilisateurs")}
    for p in profils:
        adresse, n = p["email"], 2
        while p["email"] in vus:
            p["email"] = adresse.replace("@", f"{n}@")
            n += 1
        vus.add(p["email"])


def _hacher_mots_de_passe(nb: int) -> list:
    """Hachage des mots de passe en parallèle (PBKDF2 600 000 itérations par compte)."""
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(lambda _: securite.hacher(MDP_DEMO), range(nb)))


def _creer_membre(con, gen: _Generation, p: dict, h: str) -> None:
    """Un membre complet : compte, goûts, films aimés / rejetés / en liste, puis son activité sur le site."""
    uid, d_ins = _inserer_membre(con, gen, p, h)
    logits = _envies(gen, p)
    likes, liste, vus_seuls, dislikes = _choisir_films(gen, p, logits)
    nb_onb = gen.rnd.randint(3, 5)  # nombre de films aimés dès l'inscription
    _noter_films_aimes(gen, p, uid, d_ins, likes, nb_onb)
    _noter_films_rejetes(gen, p, uid, dislikes)
    _noter_liste_et_vus(gen, p, uid, liste, vus_seuls)
    derniere = _evenements(gen, p, uid, d_ins, likes, liste, nb_onb)
    con.execute("UPDATE utilisateurs SET derniere_connexion = ? WHERE id = ?", (derniere, uid))


def _inserer_membre(con, gen: _Generation, p: dict, h: str) -> tuple:
    """Écrit le compte et ses préférences ; renvoie (id du membre, date d'inscription en texte)."""
    rnd = gen.rnd
    d_ins = p["inscription"].strftime("%Y-%m-%d %H:%M:%S")
    cur = con.execute(
        "INSERT INTO utilisateurs(email, prenom, nom, pseudo, mdp_hash, avatar, tranche_age, ville, newsletter,"
        " consentement_rgpd, date_inscription, derniere_connexion, est_fictif, est_demo)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1,?)",
        (p["email"], p["prenom"], p["nom"], p["pseudo"], h, p["avatar"], p["age"], p["ville"],
         int(rnd.random() < .35), d_ins, d_ins, d_ins, int(bool(p["demo"]))))
    uid = cur.lastrowid
    membres.ecrire_preferences(con, uid, p["prefs"], d_ins)
    return uid, d_ins


def _envies(gen: _Generation, p: dict):
    """Goûts « réels » du membre = préférences + tribu + 2 films phares + hasard (un score par film)."""
    cat, rng, cultes = gen.cat, gen.rng, gen.cultes
    pr = p["prefs"]
    ancres = _gumbel_top(rng, np.where(np.isin(cat.df["genre"].to_numpy(), pr["genres"]), 3.0, 0)
                         + cat.pop * 2, 2) if not (p["demo"] and p["demo"].get("favoris")) \
        else [cat.position[t] for t in p["demo"]["favoris"][:2]]
    sim_ancres = ramener_entre_0_et_1(np.max([cat.sim_resume(a) for a in ancres], axis=0))
    meme_real = np.zeros(cat.n)
    for a in ancres:
        for r in cat.real[a]:
            meme_real[cat.index_real[r]] = 1
    dec_aff = np.zeros(cat.n)
    for d in pr["decennies"]:
        dec_aff = np.maximum(dec_aff, (cat.decennie == d) * 1.0 + (np.abs(cat.decennie - d) == 10) * 0.4)
    logits = (1.9 * np.isin(cat.df["genre"].to_numpy(), pr["genres"]) + 1.1 * dec_aff
              + 3.0 * np.isin(np.arange(cat.n), list(cultes[p["tribu"]]))
              + 1.3 * cat.pop + 0.9 * cat.qualite + 2.2 * sim_ancres + 0.9 * meme_real
              + {"cultes": 1.0, "pepites": -0.6}.get(pr["style"], 0) * cat.pop
              + (1.0 if pr["style"] == "pepites" else 0) * cat.qualite
              + {"francais": 0.9, "international": -0.7}.get(pr["origine"], 0) * cat.fr
              + 0.5 * proximite(cat.duree, FORMATS_DUREE.get(pr["format_duree"], (110, 60))[0], 30))
    return logits


def _choisir_films(gen: _Generation, p: dict, logits) -> tuple:
    """Tire les films aimés, mis en liste, simplement vus et rejetés ; renvoie ces 4 listes de positions."""
    cat, rng, rnd = gen.cat, gen.rng, gen.rnd
    pr = p["prefs"]
    nb_likes = int(np.clip(rng.lognormal(np.log(20), 0.55), 6, 70))
    choix = _gumbel_top(rng, logits * 1.5, nb_likes + 25)
    if p["demo"]:  # compte de démo : goûts nets (moins de hasard) et films cultes éventuels en tête
        nb_likes = 18
        favoris = [cat.position[t] for t in p["demo"].get("favoris", [])]
        choix = favoris + [j for j in _gumbel_top(rng, logits * 3.0, nb_likes + 30) if j not in favoris]
    likes, reste = choix[:nb_likes], choix[nb_likes:]
    liste = reste[: rnd.randint(2, 12)]
    vus_seuls = reste[len(liste): len(liste) + rnd.randint(0, 8)]
    rejet_logits = 1.4 * cat.pop - 1.6 * np.isin(cat.df["genre"].to_numpy(), pr["genres"]) - 0.8 * cat.qualite
    dislikes = _gumbel_top(rng, rejet_logits, rnd.randint(1, 8), interdits=choix)
    return likes, liste, vus_seuls, dislikes


def _noter_films_aimes(gen: _Generation, p: dict, uid: int, d_ins: str, likes: list, nb_onb: int) -> None:
    """J'aime, notes éventuelles, « vu » et carnet de séance pour chaque film aimé."""
    cat, rng, rnd, maintenant = gen.cat, gen.rng, gen.rnd, gen.maintenant
    lignes_inter, lignes_seances = gen.interactions, gen.seances
    for rang, j in enumerate(likes):
        quand = d_ins if rang < nb_onb else _instant(rng, p["inscription"], maintenant)
        src = "inscription" if rang < nb_onb else rnd.choice(["accueil", "fiche", "machine", "explorer", "recherche"])
        lignes_inter.append((uid, cat.df.tconst[j], "like", None, src, quand))
        note = None
        if rnd.random() < 0.45:
            note = 5.0 if cat.qualite[j] > 0.7 and rnd.random() < 0.7 else rnd.choice([4.0, 4.0, 5.0, 3.0])
            lignes_inter.append((uid, cat.df.tconst[j], "note", note, src, quand))
        lignes_inter.append((uid, cat.df.tconst[j], "vu", None, src, quand))
        if rang >= nb_onb and rnd.random() < 0.35:  # carnet de séance
            if note is None:
                note = rnd.choice([4.0, 5.0])
                lignes_inter.append((uid, cat.df.tconst[j], "note", note, "carnet", quand))
            lieu = rnd.choices(list(LIEUX), [.5, .35, .15])[0]
            lignes_seances.append((uid, cat.df.tconst[j], quand[:10], lieu, int(note), rnd.choice(AVIS_POSITIFS), quand))


def _noter_films_rejetes(gen: _Generation, p: dict, uid: int, dislikes: list) -> None:
    """Je n'aime pas, notes basses éventuelles, avis négatifs et « vu » pour chaque film rejeté."""
    cat, rng, rnd, maintenant = gen.cat, gen.rng, gen.rnd, gen.maintenant
    lignes_inter, lignes_seances = gen.interactions, gen.seances
    for j in dislikes:
        quand = _instant(rng, p["inscription"], maintenant)
        lignes_inter.append((uid, cat.df.tconst[j], "dislike", None, "accueil", quand))
        if rnd.random() < 0.5:
            note = rnd.choice([1.0, 2.0, 2.0])
            lignes_inter.append((uid, cat.df.tconst[j], "note", note, "fiche", quand))
            if rnd.random() < 0.4:
                lignes_seances.append((uid, cat.df.tconst[j], quand[:10], rnd.choice(list(LIEUX)), int(note),
                                       rnd.choice(AVIS_NEGATIFS), quand))
        lignes_inter.append((uid, cat.df.tconst[j], "vu", None, "fiche", quand))


def _noter_liste_et_vus(gen: _Generation, p: dict, uid: int, liste: list, vus_seuls: list) -> None:
    """Films ajoutés à « ma liste » et films seulement marqués vus."""
    cat, rng, rnd, maintenant = gen.cat, gen.rng, gen.rnd, gen.maintenant
    lignes_inter = gen.interactions
    for j in liste:
        lignes_inter.append((uid, cat.df.tconst[j], "liste", None, rnd.choice(["accueil", "fiche", "machine"]),
                             _instant(rng, p["inscription"], maintenant)))
    for j in vus_seuls:
        lignes_inter.append((uid, cat.df.tconst[j], "vu", None, "fiche", _instant(rng, p["inscription"], maintenant)))


def _evenements(gen: _Generation, p: dict, uid: int, d_ins: str, likes: list, liste: list, nb_onb: int) -> str:
    """Événements : inscription, connexions, recherches, fiches ouvertes. Renvoie la dernière connexion."""
    cat, rng, rnd, maintenant = gen.cat, gen.rng, gen.rnd, gen.maintenant
    lignes_evt = gen.evenements
    lignes_evt.append((uid, "inscription", json.dumps({"tribu_demo": p["tribu"]}, ensure_ascii=False), d_ins))
    jours_membre = max((maintenant - p["inscription"]).days, 1)
    derniere = d_ins
    for _ in range(int(rng.poisson(jours_membre / 3.5)) + 1):
        quand = _instant(rng, p["inscription"], maintenant)
        derniere = max(derniere, quand)
        lignes_evt.append((uid, "connexion", None, quand))
    for _ in range(int(rng.poisson(jours_membre / 6)) + 1):
        j = rnd.choice(likes + liste)
        titre = str(cat.df.titre[j])
        mots = [m for m in titre.replace(":", " ").split() if len(m) > 3 and m.lower() not in VIDES]
        saisie = rnd.choice(mots) if mots and rnd.random() < .45 else titre
        lignes_evt.append((uid, "recherche", saisie.lower()[:40], _instant(rng, p["inscription"], maintenant)))
    for j in likes[nb_onb:] + liste:
        origine = rnd.choices(["reco_accueil", "reco_machine", "recherche", "explorer"], [.5, .2, .18, .12])[0]
        lignes_evt.append((uid, "fiche", json.dumps({"tconst": cat.df.tconst[j], "origine": origine}),
                           _instant(rng, p["inscription"], maintenant)))
    return derniere


def _enregistrer(con, gen: _Generation) -> None:
    """Insère d'un coup toutes les lignes accumulées (beaucoup plus rapide que ligne par ligne)."""
    con.executemany("INSERT OR IGNORE INTO interactions(utilisateur_id, tconst, type, valeur, source, date)"
                    " VALUES(?,?,?,?,?,?)", gen.interactions)
    con.executemany("INSERT INTO evenements(utilisateur_id, type, detail, date) VALUES(?,?,?,?)", gen.evenements)
    con.executemany("INSERT OR IGNORE INTO seances(utilisateur_id, tconst, date_seance, lieu, note, avis, date)"
                    " VALUES(?,?,?,?,?,?,?)", gen.seances)



def main():
    """Commande terminal : vérifie le catalogue et la base, génère les membres et affiche le bilan."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nb", type=int, default=180, help="nombre de membres fictifs (défaut 180)")
    ap.add_argument("--reset", action="store_true", help="supprime d'abord les membres fictifs existants")
    ap.add_argument("--graine", type=int, default=1985, help="graine aléatoire (résultats reproductibles)")
    args = ap.parse_args()
    source = chemin_csv(RACINE)
    if source is None:
        raise SystemExit(f"Catalogue introuvable : place {CSV_NOM} dans le dossier data/.")
    base.initialiser()
    if base.nb_membres() and not args.reset:
        raise SystemExit("La base contient déjà des membres. Ajoute --reset pour remplacer les membres fictifs.")
    print(f"Catalogue : {source}")
    cat = lire_catalogue(source.read_bytes())
    stats = generer(cat, args.nb, args.graine, args.reset,
                    progression=lambda x: print(f"\r  Création des membres… {x:4.0%}", end="", flush=True))
    print(f"\nBase : {base.CHEMIN_BDD}\n{stats}\nCompte démo : {COMPTE_DEMO} / {MDP_DEMO}")



if __name__ == "__main__":
    main()
