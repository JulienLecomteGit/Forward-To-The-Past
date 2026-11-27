# Bugs et risques connus

> Revue faite avec Julien le 23/11/2026 : chaque point a été corrigé ou laissé **par décision**.
> Mise à jour Lot 14 (guide de personnalisation refait) : section D, points 13 à 21, **à décider**.
> Légende gravité : 🟠 Moyenne · 🟡 Faible · ⚪ Info. **[F]** = fait vérifié dans le code.

## A. Laissés volontairement (décision du 23/11/2026)

| # | Constat | Gravité | Pourquoi on le laisse | Si un jour on le traite |
|---|---|---|---|---|
| 1 | **Code admin « 007 » par défaut** quand aucun mot de passe n'est défini | 🟠 si mise en ligne | app de démonstration ; le message « mot de passe de démonstration actif » le rappelle dans l'admin | créer `.streamlit/secrets.toml` avec `ADMIN_MDP = "…"` (aucun code à changer) — **à faire avant toute mise en ligne** |
| 2 | **Blocage après 5 essais conservé dans la session** : recharger la page remet le compteur à zéro | 🟠 si mise en ligne | usage local et démonstration | compter les échecs déjà journalisés en base (`connexion_echec`, `admin_echec`) — **à faire avant toute mise en ligne** |
| 3 | **Mot de passe gardé en clair dans la session pendant l'inscription** (étapes 1 à 5) | 🟡 Faible | mémoire du serveur uniquement, jamais écrit en base, effacé à la création du compte | le transformer en empreinte dès l'étape 1 (`creer_membre` accepte déjà `mdp_hash`) |
| 8 | **Retirer une séance du carnet garde la note donnée sur la fiche** | ⚪ Choix métier | cohérent : la note de la fiche est un avis distinct de la séance | retirer aussi la note dans `donnees/carnet.py` · `retirer_seance` |
| 9 | **L'index de recherche est écrit dans `static/` au démarrage** | ⚪ Info | sans effet en local et sur Streamlit Community Cloud | le générer au déploiement si l'hébergeur interdit l'écriture |
| 12 | **Bruit de rendu du contrôle visuel** (coins arrondis, avatars, dégradés, tableaux) | ⚪ Info (contrôle) | déjà absorbé par le kit (enveloppe de la V9 + rejeu automatique) | reconstruire `enveloppe_v9.npz` si le navigateur ou les polices de la machine de contrôle changent |

## B. Corrigés au Lot 13 (23/11/2026)

| # | Constat d'origine | Correction faite | Preuve |
|---|---|---|---|
| 4 | `int(année)` sans protection : plantage si un film n'a pas d'année | nouvelles fonctions `annee_ou_vide` et `annee_entre_parentheses` (`outils/texte.py`), utilisées aux 4 endroits signalés (fiche : lien bande-annonce ; accueil : « Parce que tu as aimé » ; 88 MPH : « Tu as choisi » ; admin : aperçu) **et à un 5ᵉ trouvé en corrigeant** (`moteur/explications.py` · `_phrase_epoque`) | film sans année simulé : l'ancienne version plante sur la fiche, l'accueil et 88 MPH, la nouvelle s'affiche (sans l'année) ; avec une année, texte identique |
| 5 | Test « films cachés » : division par zéro si les films cachés d'un membre ont disparu du catalogue | ce membre est ignoré (`moteur/evaluation.py` · `evaluer`) | cas simulé : ancienne version `ZeroDivisionError`, nouvelle « OK » ; résultats du test qualité inchangés sinon |
| 6 | « Pourquoi ce film ? » : noms cités dans un ordre qui changeait d'un lancement à l'autre | les noms suivent l'ordre du générique du catalogue (`_phrase_casting`, `_phrase_realisation`) | 1 400 explications × 3 lancements : 15 instables avant, **0** après ; 24 explications du contrôle changent d'ordre de noms (ex. « Lana Wachowski » au lieu de « Lilly Wachowski »), rien d'autre |
| 7 | `format_entrees(nan)` levait une erreur | une valeur vide compte pour 0 (`outils/texte.py`) | `format_entrees(nan)` → « 0 » ; valeurs normales identiques |
| 10 | 14 styles CSS sans élément affiché (`.ft-led…`, `.ft-badge`, `.ft-badges`, `.ft-label`, `.ft-panneau`, `.ft-ligne-seance`, `.fp-resume`, `.ad-delta`, `.cv-attente`) | 25 règles retirées de 6 fichiers (dont `.cv.fixe .cv-attente` retiré d'une liste où `.cv.fixe .cv-calcul`, utilisé, est gardé) | aucune classe utilisée ailleurs (Python, HTML, JS) ; fichiers CSS : uniquement des lignes retirées ; captures comparées à la V9 (voir rapport du Lot 13) |
| 11 | En-tête de `demo/generation.py` : « Utilise » oubliait `donnees/securite` | ajouté | — |

## C. Traités pendant la consolidation (sans changer l'app)

| # audit | Constat d'origine | Ce qui a été fait |
|---|---|---|
| 8 | Données de démo, simulation admin, test qualité et étapes 2 à 5 de l'inscription non couverts par le kit | trois contrôles ajoutés au kit : `controle_demo.py`, `controle_admin.py` et `controle_ecrans.py`, joués à chaque lot |
| 9 | Code mort `pepites` et `panneau_temps`, impossible à supprimer car le kit les contrôlait | supprimé au Lot 9 avec 4 autres restes ; le kit est adapté sur 2 lignes et revalidé |
| — | Boucle d'imports cachée `ui ↔ contexte` | supprimée par le rangement en couches (vérifié : aucune remontée, aucune boucle) |
| — | 14 motifs de code répétés (libellés, colonnes mobile, dates, nombres, palette…) | factorisés aux Lots 7 et 8, textes visibles identiques |
| — | 9 fonctions de plus de 50 lignes, dont une de 166 | découpées au Lot 10 : 50 lignes au plus |

## D. Repérés au Lot 14 (guide de personnalisation, publication, mise en ligne) — à décider

| # | Constat | Gravité | Effet | Correction possible |
|---|---|---|---|---|
| 13 | **Le guide est une photographie du code** : captures, zones et numéros de ligne datent de la V9.1 | 🟠 Moyenne (maintenance) | après une modification du CSS ou du Python, des lignes peuvent être décalées et des captures périmées ; le guide ne le signale pas | régénérer le guide à chaque version (captures + vérification des 50 986 emplacements) ; à défaut, `Ctrl`+`F` sur le sélecteur indiqué dans la fiche |
| 14 | **« ★ prioritaire » est calculé, pas mesuré** : ordre de la cascade CSS (!important, précision du sélecteur, ordre des fichiers, ligne) | 🟡 Faible | cas rares où le style par défaut de Streamlit ou un `style="…"` écrit dans le Python l'emporte quand même | relever la valeur réellement affichée de chaque élément pendant les captures et la comparer |
| 15 | **115 règles CSS sur 580 n'apparaissent sur aucune capture** (animations du convecteur, mode Mobile sur ordinateur, cas d'erreur, états rares) | ⚪ Info | pas touchables dans 👆 Je pointe ; trouvables par 🔍 la recherche et 📚 la Bibliothèque | ajouter des vues photographiées (en surveillant la taille, point 16) |
| 16 | **Guide à 2,94 Mo pour une limite Drive de 3,1 Mo** | 🟡 Faible | quelques captures de plus feraient dépasser la limite | compresser davantage les images, ou livrer le guide hors Drive (GitHub, point 18) |
| 17 | **Affiches absentes des captures, polices du guide chargées depuis Google Fonts, navigateur récent requis** | ⚪ Info | captures prises sans internet (titre à la place de l'affiche) ; hors ligne, le guide s'affiche en police système ; Chrome, Edge ou Firefox récents | sans objet pour l'usage prévu |
| 18 | **Publication publique sur GitHub : licences des données du catalogue** (`data/Catalogue_CNC_VF.csv`, issu d'IMDb et de TMDB) | 🟠 si dépôt public | les jeux de données IMDb sont réservés à un usage personnel et non commercial ; TMDB demande de citer la source | publier sans le CSV (avec la méthode pour le recréer), ou le garder en citant les sources et l'usage pédagogique — **décision de Julien** |
| 19 | **Code admin « 007 » visible dans un dépôt public** (`config/acces.py`) | 🟠 si l'app est mise en ligne | quiconque lit le code connaît le code de démo | identique au point 1 : `.streamlit/secrets.toml` avec `ADMIN_MDP` avant toute mise en ligne (le fichier est déjà exclu de Git) |
| 20 | **Base des membres exclue de Git** (`data/*.db` dans `.gitignore`) | ⚪ Info (protection) | même si les 180 membres sont fictifs, la base n'est pas publiée ; elle est recréée automatiquement au lancement | à garder ainsi |

| 21 | **Premier démarrage : deux visiteurs simultanés font planter le second** (`sqlite3.IntegrityError: UNIQUE constraint failed: utilisateurs.email`). Constaté sur Streamlit Cloud le 23/11, reproduit en local (copie fraîche du dépôt, 2 visiteurs à 3 s d'écart). Déjà présent dans la V9 (`app.py` · `main` : `if nb_membres() == 0` puis création des 180 membres, sans verrou) | 🟠 si mise en ligne | pendant la création de la base (environ 1 min sur Streamlit Cloud), un 2ᵉ chargement de la page recrée les mêmes membres → erreur rouge pour ce visiteur ; la base reste correcte (180 membres) et les visiteurs suivants n'ont aucun problème | verrou partagé (`st.cache_resource` + `threading.Lock`) autour de la création, avec revérification `nb_membres() == 0` dans le verrou : le 2ᵉ visiteur attend puis voit l'accueil — **à décider** |

## E. Version 10 (27/11/2026)

### Changements
| Version | Changement | Fichiers |
|---|---|---|
| V10 | Base `data/Catalogue_CNC_VF.csv` : 7 356 films, + `overview_fr` et `source_fr`, 10 acteurs par film (au lieu de 5) | `data/`, `config/catalogue.py` |
| V10 | Synopsis affiché en français (`overview_fr`), repli automatique sur `overview` ; mention selon la source. Le moteur garde `overview` (anglais) pour le TF-IDF | `donnees/catalogue.py`, `vues/fiche.py` |
| V10 | Affiche de remplacement pour les films sans jaquette (19) et les affiches TMDB en erreur | `medias/affiches.py`, `16_divers.css`, recherche |
| V10 | En-tête Streamlit transparent aux clics : la barre de Streamlit Cloud masquait le haut du bouton Mobile, du « ? » et d'Admin | `16_divers.css` |
| V10.1 | Adresse absolue `/app/static/…` pour l'affiche : **inefficace** sur Cloud (renvoie la page HTML) | remplacée par la V10.2 |
| V10.2 | Affiche renommée `affiche_introuvable.png` (nom ASCII) | `static/`, `config/chemins.py` |
| V10.3 | Documentation à jour (README, LISEZ_D_ABORD, LISEZMOI_CODE, cette section) | documentation |

### Effet sur les recommandations (kit de contrôle, même base de membres)
Code V10 + ancienne base : aucun écart de calcul. Nouvelle base : « Pour toi » 88 % de films en commun avec la V9.1, « Films proches » 92 % ; précision@10 0,128 → 0,140, rappel@10 0,31 → 0,34. Cause : 10 acteurs par film.

### Limites connues
| # | Constat | Gravité | Effet | Correction possible |
|---|---|---|---|---|
| 22 | **Streamlit Cloud ne sert pas un fichier de `static/` dont le nom contient des espaces ou des accents** (404) | 🟠 | image invisible en ligne | nommer les fichiers de `static/` en ASCII (fait pour l'affiche) |
| 23 | **Après une fusion sur `main`, Streamlit Cloud peut garder d'anciens modules Python en mémoire** (constaté le 27/11 : CSS à jour, adresse d'affiche encore en V10.1) | 🟠 | mélange de deux versions en ligne | *Manage app* › ⋮ › **Reboot app** après chaque mise en ligne |
| 24 | **Safari (iPhone) n'affiche pas le `::after` d'une image cassée** | 🟡 | si une affiche TMDB renvoie une erreur, case sombre au lieu de l'affiche introuvable (comme en V9.1) | aucune sans JavaScript (`st.html` retire `onerror`) |
| 25 | **Le guide de personnalisation date de la V9.1** (voir point 13) : les 3 règles ajoutées en fin de `16_divers.css` n'y figurent pas | 🟡 | numéros de ligne de `16_divers.css` décalés de 5 lignes en fin de fichier | regénérer le guide |
| 26 | **Données IMDb publiées dans le dépôt public** (décision du 27/11 pour que le site en ligne fonctionne ; voir point 18) | 🟠 | usage non commercial à respecter | dépôt privé ou CSV hors dépôt |
