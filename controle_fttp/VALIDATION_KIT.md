# Validation du kit (22-23/11/2026, Streamlit 1.50.0, Python 3.13, Chromium 157)

Un kit de contrôle ne vaut que s'il (1) reste silencieux sur une version identique et (2) détecte les vraies régressions.

| # | Test | Attendu | Résultat |
|---|---|---|---|
| 1 | V9 contre une copie identique (contrôle complet : golden + 42 captures × 3 séries) | CONFORME | ✅ CONFORME : calculs identiques, 40 captures identiques au pixel, 2 micro-différences d'anticrénelage (6 px et 2 px) classées non bloquantes |
| 2 | Piège métier : poids « Même genre » 6,0 → 6,5 | NON CONFORME | ✅ détecté : 60+ écarts (paramètres, contributions, classements) |
| 3 | Piège visuel : couleur du titre des cartes modifiée | NON CONFORME | ✅ détecté : CSS (ligne 146, caractère exact) + 4/4 écrans en écart |
| 4 | Refactorisation légitime : 2 fonctions déplacées dans de nouveaux modules + `controle_correspondance.json` | CONFORME | ✅ CONFORME |
| 5 | Même refactorisation SANS fichier de correspondance | Message clair | ✅ « ÉLÉMENT INTROUVABLE : « pepites » n'est plus à « moteur:pepites » → indiquer son nouvel emplacement… » |

Sources d'instabilité neutralisées pendant la mise au point : ordre des ensembles Python (PYTHONHASHSEED), hasard
(random.seed), horloge (time-machine : KPI « vs semaine précédente », journal, tendances), chemin de la base affiché
dans l'admin, images non décodées au moment de la capture, affiches TMDB (internet coupé pendant les captures).

---

# Kit v3 (23/11/2026) — tolérance au bruit de rendu connu de la V9

**Problème constaté** : la V9 non modifiée, photographiée plusieurs fois, ne donne pas toujours les mêmes pixels
(coins arrondis des cartes, avatars réduits de l'admin, dégradé des onglets, tableaux). Le kit v1 ne voyait ce bruit
que si ses 2 séries de référence tombaient sur des rendus différents : un contrôle V9 contre V9 a ainsi été
**NON CONFORME** (bureau_16 : 18 770 px ; mobile_16 : 29 px).

**Ajouts** (aucun autre changement) :
1. `enveloppe.py` + `enveloppe_v9.npz` : plage [min, max] de chaque pixel instable, observée sur 16 séries de la V9.
   Un pixel candidat différent n'est toléré que s'il reste dans cette plage (élargie à ses voisins, ±1 niveau).
   Là où la V9 est toujours stable, **aucune tolérance**.
2. 🟡 MICRO étendu : ≤ 50 px **et** intensité ≤ 10/255 (en plus de la règle ≤ 10 px).

⚠️ L'enveloppe a été construite dans l'environnement de Claude (Linux, Chromium 157). Sur un autre PC elle n'a
presque pas d'effet : la reconstruire avec `python enveloppe.py construire …` sur 3 à 4 contrôles V9 contre V9.

| # | Test | Attendu | Résultat |
|---|---|---|---|
| 6 | Validation croisée : enveloppe construite SANS l'autotest en échec, appliquée à cet autotest | CONFORME | ✅ CONFORME (bureau_16 → 🟡 BRUIT, mobile_16 → 🟡 MICRO 29 px / 9 niveaux) |
| 7 | Piège visuel : rayon des coins des cartes 14 px → 15 px (zone même du bruit toléré) | NON CONFORME | ✅ détecté : 20 250 px (bureau) + 9 217 px (mobile) |
| 8 | Piège visuel : couleur du titre des cartes décalée de 2 niveaux (#FAF5EE → #FAF5EC), captures seules | NON CONFORME | ✅ détecté : 4 écrans, 9 176 à 32 378 px |
| 9 | Piège métier : poids « Même genre » 6,0 → 6,5 | NON CONFORME | ✅ détecté : 60 écarts golden |
| 10 | Autotest V9 vs V9 complet, captures neuves (non utilisées pour l'enveloppe) | CONFORME | ✅ CONFORME : 40 identiques, 2 🟡 BRUIT, 0 écart |
| 11 | Contrôle démo : V9 contre copie V9 | CONFORME | ✅ CONFORME : 180 membres, 14 264 interactions, 9 445 événements, 1 298 séances identiques (≈ 30 s) |
| 12 | Piège démo : un avis type modifié d'un caractère (« Casting au top. » → « … top ! ») | NON CONFORME | ✅ détecté : 112 séances différentes |
| 13 | Enveloppe enrichie : 16 → 27 séries de la V9 non modifiée (captures du 23/11 après-midi) ; pièges 7 et 8 rejoués | NON CONFORME | ✅ toujours détectés (20 250 / 9 217 px ; 4 écrans couleur) |
| 14 | Autotest V9 vs V9 complet avec l'enveloppe enrichie, captures neuves | CONFORME | ✅ CONFORME : 39 identiques, 3 🟡 BRUIT, 0 écart |
| 15 | Rejeu automatique (v3.3) — piège coins : l'écart doit être reproduit et rester bloquant | NON CONFORME | ✅ ❌ « reproduit au rejeu » (20 237 px bureau, 9 217 px mobile) |
| 16 | Rejeu automatique — logique de reclassement testée sur cas fictifs (non reproduit / reproduit / taille) | — | ✅ non reproduit → 🟡 BRUIT ; reproduit → ❌ |
| 17 | `controle_admin.py` : V9 contre copie V9 (7 étapes interactives) | IDENTIQUE | ✅ IDENTIQUE (après neutralisation de l'identifiant aléatoire des tableaux pandas) |
| 18 | `controle_admin.py` : piège (« sélection de 8 » → « sélection de 8 films ») | DIFFÉRENT | ✅ détecté (5 étapes en écart) |
| 19 | `controle_ecrans.py` : V9 contre copie V9 (14 écrans : inscription 1 → 5, fiche avec séance, carnet ; ordinateur + mobile) | IDENTIQUE | ✅ IDENTIQUE |
| 20 | `controle_ecrans.py` : piège (« 🍿 Long (2 h +) » → « (2h+) », inscription étape 4) | DIFFÉRENT | ✅ détecté (étape 4, ordinateur et mobile) |
| 21 | Kit v3.5 : code mort `pepites` et `panneau_temps` retiré du golden (2 lignes) et de `correspondance_defaut.json` (2 entrées) — V9 contre copie | CONFORME | ✅ CONFORME |
| 22 | Kit v3.5 : piège métier (genre 6,0 → 6,5) | NON CONFORME | ✅ détecté (60 écarts) |
