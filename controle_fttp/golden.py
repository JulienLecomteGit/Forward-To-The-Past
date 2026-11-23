"""Golden master métier : exécute les fonctions de calcul de l'app et enregistre tous leurs résultats en JSON.

Deux versions qui donnent le même JSON calculent exactement la même chose (tolérance : 9 décimales).
Usage : python golden.py <dossier_projet> <sortie.json> <base_reference.db>
Normalement appelé par controler.py (une fois pour la référence, une fois pour la version refactorisée).
"""
from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
import math
import os
import shutil
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np

# L'ordre des ensembles Python (set) change à chaque lancement sauf si PYTHONHASHSEED est fixé :
# certaines explications « Pourquoi ce film » en dépendent. On se relance donc avec une graine fixe.
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import subprocess
    sys.exit(subprocess.call([sys.executable, *sys.argv]))

for _flux in (sys.stdout, sys.stderr):  # Windows : accents sans erreur d'encodage
    if hasattr(_flux, "reconfigure"):
        _flux.reconfigure(encoding="utf-8", errors="replace")

if os.environ.get("FTTP_HORLOGE"):  # même instant figé que les captures (datetime, pandas, time)
    import time_machine

    time_machine.travel(float(os.environ["FTTP_HORLOGE"]), tick=False).start()

ICI = Path(__file__).resolve().parent
PROJET = Path(sys.argv[1]).resolve()
SORTIE = Path(sys.argv[2]).resolve()
BASE_REF = Path(sys.argv[3]).resolve()

# Base de travail : copie neuve, désignée à l'app par la variable FTTP_BDD (lue par bdd.py au démarrage).
TMP = Path(tempfile.mkdtemp())
shutil.copy(BASE_REF, TMP / "fttp.db")
os.environ["FTTP_BDD"] = str(TMP / "fttp.db")
os.chdir(PROJET)
sys.path.insert(0, str(PROJET))
warnings.filterwarnings("ignore")
import logging  # noqa: E402

logging.disable(logging.CRITICAL)  # messages « No runtime found » de Streamlit hors serveur

# ------------------------------------------------------------------ correspondance des emplacements
CARTE = {k: v for k, v in json.loads((ICI / "correspondance_defaut.json").read_text(encoding="utf-8")).items()
         if not k.startswith("_")}
perso = PROJET / "controle_correspondance.json"
if perso.exists():
    CARTE.update({k: v for k, v in json.loads(perso.read_text(encoding="utf-8")).items() if not k.startswith("_")})


def obtenir(nom: str):
    cible = CARTE[nom]
    if cible.startswith("fichier:"):
        return (PROJET / cible[len("fichier:"):]).read_text(encoding="utf-8")
    module, _, attr = cible.partition(":")
    try:
        objet = importlib.import_module(module)
        for morceau in attr.split("."):
            objet = getattr(objet, morceau)
    except (ImportError, AttributeError) as e:
        print(f"ÉLÉMENT INTROUVABLE : « {nom} » n'est plus à « {cible} » ({e}).\n"
              f"→ Indiquer son nouvel emplacement dans controle_correspondance.json à la racine du projet, "
              f'par exemple : {{"{nom}": "nouveau_module:{attr.split(".")[-1]}"}}', file=sys.stderr)
        sys.exit(3)
    return objet


# ------------------------------------------------------------------ mise en forme JSON stable
def norm(x, profondeur=0):
    if isinstance(x, (bool, np.bool_)) or x is None or isinstance(x, str):
        return bool(x) if isinstance(x, np.bool_) else x
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        x = float(x)
        return "NaN" if math.isnan(x) else ("Inf" if math.isinf(x) else round(x, 9))
    if isinstance(x, np.ndarray):
        if x.size > 300:  # gros tableau : empreinte + somme, pour garder un JSON lisible
            arr = np.nan_to_num(x.astype(float), nan=-9e9).round(9) if x.dtype.kind in "fiub" else x.astype(str)
            return {"_tableau": list(x.shape), "empreinte": hashlib.sha256(arr.tobytes() if arr.dtype.kind == "f" else
                    "|".join(arr.ravel()).encode()).hexdigest()[:16],
                    "somme": norm(float(np.nansum(x))) if x.dtype.kind in "fiub" else None}
        return [norm(v, profondeur + 1) for v in x.tolist()]
    if isinstance(x, dict):
        return {str(k): norm(v, profondeur + 1) for k, v in x.items()}
    if isinstance(x, (set, frozenset)):
        return sorted((norm(v, profondeur + 1) for v in x), key=str)
    if isinstance(x, (list, tuple)):
        return [norm(v, profondeur + 1) for v in x]
    if dataclasses.is_dataclass(x):
        return {f.name: norm(getattr(x, f.name), profondeur + 1) for f in dataclasses.fields(x)}
    if hasattr(x, "keys"):  # sqlite3.Row
        return {k: norm(x[k], profondeur + 1) for k in x.keys()}
    return repr(x)


# Valeurs qui changent à chaque exécution (date du jour, sel aléatoire du mot de passe) : exclues de la comparaison.
HORODATAGES = {"date", "maj", "derniere_connexion", "date_inscription", "export_le", "cree_le", "_dates", "mdp_hash"}


def sans_horodatage(x):
    """Retire les dates « maintenant » écrites pendant le test (elles changent à chaque exécution)."""
    if isinstance(x, dict):
        return {k: sans_horodatage(v) for k, v in x.items() if k not in HORODATAGES}
    if isinstance(x, list):
        return [sans_horodatage(v) for v in x]
    return x


def resultat(res, cat, pourquoi, nb_pourquoi=5):
    return {
        "indices": [int(j) for j in res.indices],
        "tconst": [cat.df.tconst[int(j)] for j in res.indices],
        "score_100": [res.score_100(int(j)) for j in res.indices],
        "scores": norm(np.asarray(res.scores)),
        "scores_retenus": [norm(float(res.scores[int(j)])) for j in res.indices],
        "contributions": [norm(res.contributions(int(j))) for j in res.indices[:nb_pourquoi]],
        "poids": norm(res.poids), "mode": res.mode, "source": norm(res.source), "contexte": norm(res.contexte),
        "pourquoi": [pourquoi(cat, res, int(j), 3) for j in res.indices[:nb_pourquoi]],
    }


G: dict = {}

# ------------------------------------------------------------------ 1. Catalogue
CSV = PROJET / "data" / obtenir("CSV_NOM")
cat = obtenir("lire_catalogue")(CSV.read_bytes())
G["catalogue"] = {
    "n": cat.n, "genres": cat.genres, "colonnes": list(cat.df.columns),
    "df": hashlib.sha256(cat.df.astype(str).to_csv(index=False).encode()).hexdigest(),
    "tableaux": {k: norm(getattr(cat, k)) for k in ("annee", "duree", "decennie", "genre_code", "note", "votes", "entrees",
                                                     "fr", "pop", "qualite") if hasattr(cat, k)},
    "film_exemple": norm(cat.film(cat.position["tt0088763"])),
}
G["recherche_catalogue"] = {q: [int(j) for j in cat.chercher(q, 60)] for q in
                            ["retour vers le futur", "Matrix", "spielberg", "Jean Dujardin", "amelie", "le", "zzzz", "", "Bébel"]}

# ------------------------------------------------------------------ 2. Paramètres et constantes métier
PARAMS = obtenir("PARAMS_DEFAUT")
PRESETS = obtenir("PRESETS")
G["parametres"] = {k: norm(obtenir(k)) for k in ("PARAMS_DEFAUT", "PRESETS", "REGLAGES", "INTERRUPTEURS", "LIBELLES",
                                                   "MESSAGES", "NIVEAUX", "EMOJI_GENRE")}
JEUX = {"defaut": dict(PARAMS), **{nom: {**PARAMS, **reg} for nom, reg in PRESETS.items()}}

# ------------------------------------------------------------------ 3. Base de données (lecture) et communauté
obtenir("bdd_initialiser")()
G["bdd_lecture"] = {"nb_membres": obtenir("bdd_nb_membres")(), "demos": norm(obtenir("bdd_membres_demo")()),
                    "parametres_moteur": norm(obtenir("bdd_lire_parametres")(PARAMS))}
lignes = obtenir("bdd_toutes_interactions")()
comm = obtenir("Communaute")(cat, lignes)
G["communaute"] = {"uids": comm.uids[:50], "nb_film": norm(comm.nb_film), "nb_user": norm(comm.nb_user),
                   "tendances_30j": norm(comm.tendances(30)), "item_retour_futur": norm(comm.item(cat.position["tt0088763"]))}

# ------------------------------------------------------------------ 4. Recommandations membre → films
pourquoi = obtenir("pourquoi")
demos = [d["id"] for d in obtenir("bdd_membres_demo")()]
membres_test = demos + [u for u in comm.uids if u % 23 == 0][:6]
G["pour_toi"], G["gamification"] = {}, {}
Ctx, xp, niveau, badges = obtenir("Ctx"), obtenir("xp"), obtenir("niveau"), obtenir("badges")
for uid in membres_test:
    prefs = obtenir("bdd_preferences")(uid)
    inter = obtenir("bdd_interactions")(uid)
    pr = obtenir("profil_membre")(cat, prefs, inter, uid)
    G["pour_toi"][f"profil_{uid}"] = norm(pr)
    for nom, p in JEUX.items():
        G["pour_toi"][f"{uid}|{nom}"] = resultat(obtenir("pour_toi")(cat, pr, p, comm, n=24), cat, pourquoi)
    ctx = Ctx(cat=cat, comm=comm, p=dict(PARAMS), mobile=False, uid=uid, membre=obtenir("bdd_membre")(uid), prefs=prefs,
              inter=inter, profil=pr, seances=obtenir("bdd_seances")(uid))
    pts = xp(ctx, 12)
    G["gamification"][str(uid)] = {"xp": pts, "niveau": norm(niveau(pts)), "badges": norm(badges(ctx)),
                                   "connus": norm(ctx.connus()), "nb": ctx.nb}

# ------------------------------------------------------------------ 5. Recommandations film → films
G["similaires"] = {}
films_test = ["tt0088763", "tt0133093", "tt0211915", "tt0081505", "tt0092099", "tt0108052"] + \
             [cat.df.tconst[j] for j in range(0, cat.n, max(1, cat.n // 8))]
for t in films_test:
    if t not in cat.position:
        continue
    for nom, p in JEUX.items():
        G["similaires"][f"{t}|{nom}"] = resultat(obtenir("similaires")(cat, cat.position[t], p, comm), cat, pourquoi)

# ------------------------------------------------------------------ 6. Évaluation hors-ligne (onglet Qualité du moteur)
prefs_tous = {u: obtenir("bdd_preferences")(u) for u in comm.uids}
G["evaluer"] = norm(obtenir("evaluer")(cat, lignes, prefs_tous, dict(PARAMS), nb_max=25))

# ------------------------------------------------------------------ 7. Apparence : CSS et morceaux HTML générés
f0 = cat.film(cat.position["tt0088763"])
G["apparence"] = {
    "CSS": obtenir("CSS"), "CSS_MOBILE": obtenir("CSS_MOBILE"), "CSS_CADRE": obtenir("CSS_CADRE"),
    "logo": obtenir("logo_html")(), "meta_film": obtenir("meta_film")(f0),
    "note_txt": [obtenir("note_txt")(v) for v in (None, float("nan"), 7.25, 8.0)],
    "origine_txt": obtenir("origine_txt")(f0), "etoiles": [obtenir("etoiles")(n) for n in (0, 3, 5, None)],
    "url_affiche": [obtenir("url_affiche")(f0["affiche"]), obtenir("url_affiche")(f0["affiche"], "w500"),
                    obtenir("url_affiche")("")],
    "carte_membre": [obtenir("carte_membre_html")("a01", "Marty <b>", "marty", "SF", "x", c) for c in (False, True)],
    "tuile": obtenir("tuile")("Titre", "42", "détail"),
    "tuile_kpi": [obtenir("tuile_kpi")("Membres", "180", "+3", ton, "aide") for ton in ("neutre", "bon", "mauvais")],
    "jaquettes": obtenir("jaquettes")(cat, list(range(0, 40, 5)), {0: "✓"}, {5: "ok"}, 4),
    "barre": [obtenir("barre")([("SF", 0.5), ("Comédie", 0.3), ("Drame", 0.2)], leg, pc) for leg in (True, False) for pc in (True, False)],
    "gouts": [obtenir("gouts_html")([("SF", 0.48), ("Action", 0.32)]), obtenir("gouts_html")([])],
    "circuits": [obtenir("circuits_temps")([
        {"couleur": "r", "plaque": "DESTINATION TIME", "apres": obtenir("moment")(1955, 11, 5, 6, 0), "saisie": tape},
        {"couleur": "v", "plaque": "PRESENT TIME", "avant": obtenir("moment")(1985, 10, 26, 1, 21),
         "apres": obtenir("moment")(1955, 11, 5, 6, 0)},
        {"couleur": "a", "plaque": "LAST TIME DEPARTED", "avant": obtenir("moment")(2015, 10, 21, 16, 29),
         "apres": obtenir("moment")(1985, 10, 26, 13, 21)}], tape) for tape in (False, True)],
    "format_entrees": [obtenir("format_entrees")(n) for n in (0, 950, 12_500, 1_250_000, 19_000_000, None)],
    "normaliser": [obtenir("normaliser")(s) for s in ("Retour vers le Futur", "Élan & Co", "", None)],
    "composant_recherche": hashlib.sha256(obtenir("composant_recherche").encode()).hexdigest(),
    "avatars_json": json.loads(obtenir("avatars_json")),
}
nom_index = obtenir("index_recherche")(cat)
G["apparence"]["index_recherche"] = {"nom": nom_index, "contenu": hashlib.sha256(
    (PROJET / "static" / nom_index).read_bytes()).hexdigest()}

# ------------------------------------------------------------------ 8. Base de données (écriture) : scénario complet d'un membre
mdp = "Retro-1985!"
uid = obtenir("bdd_creer_membre")("test.controle@example.com", "Test", "Contrôle", "testeur", mdp, "a01", "25-34 ans",
                                  "Paris", True, {"genres": ["Comédie", "Science Fiction"], "decennies": [1980, 1990],
                                                  "format_duree": "court", "origine": "francais", "style": "pepites"},
                                  coups_de_coeur=["tt0088763", "tt0133093"], date="2026-01-01 10:00:00")
etapes = {"basculer": [obtenir("bdd_basculer")(uid, "tt0211915", t, "test") for t in ("like", "liste", "dislike", "like", "vu")]}
obtenir("bdd_noter")(uid, "tt0081505", 4.0, "test")
obtenir("bdd_noter")(uid, "tt0092099", None, "test")
obtenir("bdd_enregistrer_seance")(uid, "tt0108052", "2026-02-03", "cinema", 5, "  Superbe !  ")
obtenir("bdd_enregistrer_seance")(uid, "tt0092099", "2026-02-04", "streaming", None, "")
obtenir("bdd_retirer_seance")(uid, "tt0092099")
auth = obtenir("bdd_authentifier")("TEST.controle@example.com ", mdp)
etapes.update({
    "membre": norm(obtenir("bdd_membre")(uid)), "preferences": norm(obtenir("bdd_preferences")(uid)),
    "interactions": norm(obtenir("bdd_interactions")(uid)), "seances": norm(obtenir("bdd_seances")(uid)),
    "export": norm(obtenir("bdd_export_membre")(uid)), "email_existe": [obtenir("bdd_email_existe")(e) for e in
                                                                         ("test.controle@example.com", "inconnu@example.com")],
    "authentifier_ok": norm(auth) if not isinstance(auth, (int, type(None))) else auth,
    "authentifier_ko": norm(obtenir("bdd_authentifier")("test.controle@example.com", "mauvais")),
    "robustesse": [norm(obtenir("bdd_robustesse")(m)) for m in ("", "abc", "abcdefgh", "Abcdefgh1", "Retro-1985!xyz")],
    "hachage_verifie": obtenir("bdd_verifier")(mdp, obtenir("bdd_hacher")(mdp)),
    "hachage_refuse": obtenir("bdd_verifier")("autre", obtenir("bdd_hacher")(mdp)),
})
G["bdd_ecriture"] = sans_horodatage(norm(etapes))

SORTIE.write_text(json.dumps(norm(G), ensure_ascii=False, sort_keys=True, indent=1), encoding="utf-8")
shutil.rmtree(TMP, ignore_errors=True)
print(f"  ✓ golden master : {len(G['pour_toi'])} entrées « Pour toi », {len(G['similaires'])} « films proches », "
      f"{len(G['recherche_catalogue'])} recherches, scénario base de données complet")
