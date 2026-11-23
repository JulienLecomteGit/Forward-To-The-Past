# Kit de contrôle de non-régression — Forward To The Past (V9)

**À quoi ça sert :** prouver qu'une version refactorisée de l'app **calcule et affiche exactement la même chose** que la V9.
Le kit compare les deux versions **dans la même exécution, sur la même machine, avec la même base figée**, le même hasard
(graine fixe) et la même horloge (« maintenant » figé). La date du jour, les polices et l'environnement ne faussent donc
jamais la comparaison.

| Contrôle | Ce qui est vérifié | Durée |
|---|---|---|
| **Golden master** (calculs) | « Pour toi » de 14 membres × 7 réglages, « films proches » de 15 films × 7 réglages, explications « Pourquoi ce film », recherche, communauté et tendances, évaluation du moteur, XP / niveaux / badges, scénario complet en base (inscription, ❤️ ➕ 🤮, notes, carnet, export RGPD, connexion), CSS et morceaux HTML générés | ≈ 15 s |
| **Captures** (visuel) | 21 écrans × bureau (1440 px) + mobile (Pixel, 412 px) = **42 captures** comparées pixel par pixel | ≈ 15 min |

---

## 1. Installation (une seule fois, Windows, terminal VS Code)

Organisation conseillée (3 dossiers côte à côte) :
```
FTTP\
├── Forward_To_The_Past_v9\        ← RÉFÉRENCE : ne jamais la modifier
├── Forward_To_The_Past_refacto\   ← version refactorisée à contrôler
└── controle_fttp\                 ← ce kit
```
```powershell
cd "C:\chemin\vers\FTTP\Forward_To_The_Past_v9"
.\.venv\Scripts\Activate.ps1                                   # le .venv de l'app (README de l'app)
python -m pip install -r ..\controle_fttp\requirements-controle.txt
python -m playwright install chromium                          # navigateur de capture (≈ 150 Mo, une fois)
```

## 2. Lancer un contrôle

```powershell
cd "C:\chemin\vers\FTTP\controle_fttp"
python controler.py --reference ..\Forward_To_The_Past_v9 --candidat ..\Forward_To_The_Past_refacto
```

| Option | Effet |
|---|---|
| `--golden-seul` | calculs seulement (≈ 15 s) : idéal après chaque petit lot |
| `--captures-seules` | captures seulement |
| `--sans-rejeu` | ne pas rejouer automatiquement les écrans en écart (par défaut, chaque écran en ❌ est re-photographié, référence et candidat : non reproduit → 🟡 BRUIT, reproduit → ❌ reste bloquant) |
| `--rapide` | une seule série de référence (≈ 10 min), sans détection automatique du bruit |
| `--scenarios 03_pour_toi 05_explorer` | limiter les captures à quelques écrans |
| `--sortie DOSSIER` | dossier des résultats (défaut `resultats_controle`) |

**Contrôle complémentaire — données de démo** (non couvertes par `controler.py`, ≈ 30 s) :
`python controle_demo.py --reference ..\Forward_To_The_Past_v9 --candidat ..\Forward_To_The_Past_refacto`
→ génère la base de démo avec les deux versions (graine et horloge figées) et compare les tables (seules les empreintes de mots de passe, salées au hasard, sont exclues).

## 3. Lire le résultat

`resultats_controle\rapport.md` (ouvrir dans VS Code puis `Ctrl+Maj+V` pour l'aperçu) :

| Statut | Signification | Action |
|---|---|---|
| ✅ CONFORME | Calculs identiques **et** aucune capture en écart | Lot validé |
| ✅ IDENTIQUE | Capture identique au pixel | — |
| 🟡 BRUIT | Différences uniquement là où la V9 elle-même varie : entre les 2 captures de référence de l'exécution, ou dans la plage de couleurs déjà observée sur 16 séries de la V9 (`enveloppe_v9.npz`) | Aucune |
| 🟡 MICRO | ≤ 10 pixels au total, ou ≤ 50 pixels d'intensité ≤ 10/255 (lissage d'un coin, dégradé d'un bouton) : invisible à l'œil, non bloquant | Coup d'œil si doute |
| ❌ ÉCART | Pixels différents hors bruit → image rouge dans `ecarts\` | Corriger |
| ❌ TAILLE | Hauteur de page différente : contenu ajouté, supprimé ou décalé | Corriger |
| ❌ écart golden | Le chemin indique quoi (ex. `/pour_toi/115|defaut/indices`) | Corriger |

---

## 4. Règles pour la version refactorisée (sinon le kit ne peut pas comparer)

1. **Clés Streamlit et libellés inchangés** (`key="nav_explorer"`, « Créer mon compte gratuitement »…) : les parcours s'appuient dessus, et le CSS aussi.
2. **Variable `FTTP_BDD` conservée** (emplacement de la base, lu par `bdd.py`) : le kit l'utilise pour travailler sur une copie.
3. **Signatures des fonctions inchangées** (mêmes paramètres, mêmes noms de paramètres).
4. **Fonction déplacée → `controle_correspondance.json`** à la racine du projet refactorisé, avec les seuls éléments déplacés :
   ```json
   { "pour_toi": "moteur.recommandation:pour_toi",
     "CSS": "fichier:interface/style/theme.css" }
   ```
   La liste complète des éléments contrôlés et de leurs emplacements V9 est dans `correspondance_defaut.json`.
   Le préfixe `fichier:` permet de déplacer le CSS dans un fichier `.css` : le contenu doit rester **identique au caractère près**.
5. Ne pas déplacer `static/` ni `composants/recherche/` : les URL `app/static/...` (polices, avatars) et le composant de recherche en dépendent.

## 5. Limites (à vérifier à la main, 5 minutes)

Le kit coupe internet pendant les captures, donc les affiches TMDB distantes ne sont pas comparées (les 39 affiches locales le sont).
Il ne joue pas non plus : les étapes 2 à 5 de l'inscription, la saisie dans la recherche prédictive, l'animation du convecteur
temporel une fois lancée, les survols de souris et le cadre « Mobile » sur ordinateur. Checklist manuelle :

- [ ] Inscription complète (5 étapes) jusqu'à « Créer mon compte »
- [ ] Recherche prédictive : taper « ret » dans Explorer, ↑ ↓ Entrée
- [ ] 88 MPH › Convecteur : choisir une humeur, lancer, ouvrir la fiche du film
- [ ] Bascule « Mobile » sur ordinateur (cadre de téléphone)
- [ ] Une réaction ❤️ sur une carte, puis vérifier « Mes films › Favoris »

## 6. Fichiers du kit

| Fichier | Rôle |
|---|---|
| `controler.py` | **la seule commande à lancer** : prépare, compare, écrit le rapport |
| `golden.py` | exécute les fonctions de calcul de l'app et enregistre leurs résultats (JSON) |
| `captures.py` | démarre l'app et photographie chaque écran avec Playwright |
| `scenarios.py` | la liste des parcours (ajouter un écran = ajouter une ligne) |
| `comparer.py` | compare les JSON et les images, calcule le masque de bruit |
| `controle_ecrans.py` | contrôle complémentaire des écrans non photographiés : inscription étapes 1 → 5, fiche d'un film du carnet, Mes films › carnet, en ordinateur et en mobile (≈ 2 min) |
| `controle_admin.py` | contrôle complémentaire de l'admin : clique « Lancer le test », « Simuler » (3 scénarios), mode « Un film », filtre « membres réels » et compare tout ce qui s'affiche (≈ 3 min) |
| `controle_demo.py` | contrôle complémentaire : base de démo générée par les deux versions, comparée table par table |
| `enveloppe.py` + `enveloppe_v9.npz` | plage de couleurs de chaque pixel instable de la V9 (bruit de rendu connu). À reconstruire si le navigateur ou les polices changent : `python enveloppe.py construire enveloppe_v9.npz <dossiers de captures V9>` |
| `lanceur_streamlit.py` | démarre Streamlit avec le hasard et l'horloge figés |
| `correspondance_defaut.json` | emplacement V9 de chaque élément contrôlé |
