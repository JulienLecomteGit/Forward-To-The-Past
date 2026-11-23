# 🌴 Forward To The Past · ciné-club (v3 — design V8 + moteur complet)

Application Streamlit du Projet 2 (appel à projets CNC) : ciné-club rétro 80s avec **inscription façon Spotify/Netflix**, **moteur de recommandation personnalisé**, **carnet de séance**, **version mobile** et **espace admin** pour piloter le moteur.

---

## ⚡ Lignes de commande (terminal VS Code : Terminal › Nouveau terminal)

```powershell
# 1. Se placer dans le dossier du projet
cd "C:\chemin\vers\Forward_To_The_Past"

# 2. Créer l'environnement virtuel (une seule fois)
py -3.12 -m venv .venv

# 3. Activer l'environnement (à chaque nouveau terminal)
.\.venv\Scripts\Activate.ps1

# 4. Installer les librairies (une seule fois)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 5. Lancer l'app → http://localhost:8501   (Ctrl+C pour arrêter)
python -m streamlit run app.py
```

| Option | Commande |
|---|---|
| Activation bloquée par Windows | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (une seule fois), puis refaire l'étape 3 |
| Tester sur le téléphone (même Wi-Fi) | `python -m streamlit run app.py --server.address 0.0.0.0` puis `http://IP-DU-PC:8501` sur le téléphone (`ipconfig` donne l'IP) |
| Port 8501 déjà pris | `python -m streamlit run app.py --server.port 8502` |
| Recréer les membres fictifs | `python -m demo.generation --nb 180 --reset` |
| Base neuve | supprimer `data/fttp.db` puis relancer l'app (recréée automatiquement) |

Dans VS Code, `Ctrl+Maj+P` › **Python: Select Interpreter** › `.venv`.

---

## 🔑 Comptes

| Accès | Identifiants |
|---|---|
| « Qui passe la séance ce soir ? » | 8 profils de démo en **1 clic** sur l'écran d'accueil (Marty, Lucia, Camille, Enzo, Chloé, Henri, Sarah, Lucas) |
| Compte démo (formulaire) | `marty.dubois@example.com` · `retro1985` |
| 180 membres fictifs | adresse visible dans l'admin (`…@example.com`) · mot de passe `retro1985` |
| Vrais comptes | créés via « Créer mon compte » : **e-mail + mot de passe obligatoires** (pas d'accès en 1 clic) |
| Espace admin | code **`007`** (bouton 🔒 Admin) |

> Pour une vraie mise en ligne : copier `.streamlit/secrets.toml.exemple` en `.streamlit/secrets.toml` et remplacer `ADMIN_MDP`. Le code « 007 » n'est qu'une valeur de démonstration.

---

## 🧭 Écrans

| Écran | Contenu |
|---|---|
| **Accueil public** | Bannière DeLorean, « Qui passe la séance ce soir ? » (profils démo), connexion, création de compte |
| **Inscription (5 étapes)** | Identité + consentement RGPD → avatar (24, par catégorie, façon Netflix) → genres (façon Spotify) → décennies, durée, origine, style → 3 coups de cœur minimum |
| **Pour toi** | Bannière « Bon retour à 88 MPH, Prénom Nom » · Sélection 88 MPH avec « Ton flux en ce moment » (goûts compris par le moteur, en %) · Parce que tu as aimé… · Tendances · Coups de cœur de ton jumeau ciné · Tes années · Pépites · Cinéma français · Sagas — cartes avec réactions ❤️ ➕ 🤮 |
| **Explorer** | **Recherche prédictive** (vignette + année dès la 1re lettre, films et personnes) titre FR/VO, acteur ou réalisateur ; filtres genre, période, durée, note, cinéma français ; tri « Pour toi » |
| **88 MPH** | *Tu as aimé… ?* (moteur + graphique de décision) · *Destination année* (7 années cultes en cartes, « Au hasard », curseur) · **Convecteur temporel** : humeur → animation façon DeLorean (compteur et jauge 0 → 88 MPH, convecteur temporel détaillé, destination tapée sur les **Time Circuits** rouge/vert/ambre, convecteur qui s'emballe, 0 → 88 MPH, 1,21 gigowatts, onde de choc, flash, traînées de feu ; à l'arrivée PRESENT TIME passe à la date du film) puis **jaquette du film qui se matérialise — cliquable pour ouvrir la fiche** |
| **Fiche film (pleine page)** | Affiche + réactions, synopsis, saga/réalisation/casting, bande-annonce/IMDb/TMDB, **carnet de séance** (date, lieu, note ★, avis), « Pourquoi ce film pour toi ? », films proches, bouton Retour |
| **Mes films** | Carnet de séance (compteurs), Favoris, À voir, Pas pour moi en **lignes compactes** : clic = fiche, 🗑️ = retirer · recherche prédictive limitée à la liste (titre, réalisateur, acteur), filtre (lieu ou genre), **tri** (date, note, titre, année, durée) · 20 lignes puis « Afficher plus » |
| **Profil** | Avatar, niveau & XP, **Mon Rewind**, **jumeaux ciné** (cartes avatar), **9 badges avec progression**, **Mes préférences** (ADN ciné : choix + ce que le moteur utilise en ce moment ; genres et décennies en grille alignée), avatar, infos, **export JSON / suppression (RGPD)** |
| **Admin (007)** | Espace séparé (sans la navigation membre) : vue d'ensemble (KPI + graphiques) · membres (e-mails masqués) · **recette du moteur + réglages en cartes, aperçu avant/après en jaquettes** · **qualité du moteur** (test, exemple concret, simulation « le membre a-t-il la main ? ») · **🖼️ Avatars** · journal & base |
| **📱 Mobile** | Détection automatique + bouton de bascule (cadre téléphone sur ordinateur). Barre de navigation en bas, grilles en 2 colonnes |

---

## 🧠 Le moteur de recommandation

Chaque critère donne une note entre 0 et 1 ; l'admin règle son **poids** (0 à 10). Score = somme des poids × notes, ramenée sur 100.

| Réglage admin (vulgarisé) | Ce qui est calculé |
|---|---|
| 🎭 Même genre | Genre identique (mode film) ou affinité du membre pour le genre (déclarée + aimée) |
| 📅 Même époque · ↔️ écart toléré | Proximité d'année ou affinité par décennie |
| ⏳ Durée similaire | Proximité de durée / format préféré |
| 📖 Histoire qui se ressemble | Similarité des résumés **TF-IDF** (scikit-learn), cosinus |
| 🌟 Acteurs en commun | Acteurs partagés, stars omniprésentes pondérées à la baisse (IDF) |
| 🎬 Même réalisateur | Réalisateurs partagés |
| 👥 Goûts des membres | **Filtrage collaboratif** : membres aux j'aime proches (cosinus) |
| 🧬 Préférences / ❤️ Ce que le membre a aimé | Dosage entre goûts déclarés et comportement réel : j'aime, notes 4-5★ (5★ pèsent 1,5×), séances, « À voir » (signal faible) et « Pas pour moi » (retire du poids au genre rejeté) |
| ⚡ Réactivité aux dernières actions | Les actions récentes pèsent plus : le poids est divisé par 2 toutes les « 40 / réglage » actions (réglage 5 → toutes les 8 actions ; 0 = pas d'effet) |
| 🎯 Respect de toutes ses envies | **Calibrage** (méthode « calibrated recommendations », Netflix) : la sélection reprend les proportions des goûts du membre (ex. 48 % comédie, 32 % action, 21 % SF) au lieu de ne montrer que le genre dominant |
| ⭐ Bonnes notes | Note IMDb pondérée par le nombre de votes |
| 🎟️ Pépites ↔ Succès en salles | Bonus/malus selon les entrées France |
| 🇫🇷 Coup de pouce cinéma français | Bonus aux films (co)produits en France |
| 🌈 Diversité | Re-classement **MMR** |
| 🔗 Saga · 🙈 Déjà vus · 🚫 Note minimale · 🔢 Nombre | Règles d'affichage |

**Preuve que les réglages comptent** : l'onglet *Qualité du moteur* cache 20 % des films aimés de 80 membres et mesure si le moteur les retrouve (taux de réussite, précision, rappel, couverture), comparé à « les plus populaires » et « au hasard », avec un exemple concret en jaquettes. Données fictives → résultats indicatifs.

**Le membre a-t-il la main ?** (onglet *Qualité du moteur*, simulation sans écriture en base) — mesures sur Marty, réglages d'usine :

| Action du membre | Effet sur sa sélection |
|---|---|
| ❤️ 5 films d'horreur aimés | 4 films sur 8 changent · horreur 0 % → 21 % des 24 films proposés |
| 🤮 5 comédies rejetées | comédie 50 % → 29 % |
| 🧬 Genres passés à Horreur + Thriller | 4 films sur 8 changent · horreur 0 % → 25 %, thriller 0 % → 25 % |

Effet sur les **autres** membres : un membre seul ne change pas les recommandations des autres (0 sur 179 dans le test) ; l'effet est **collectif** : 20 membres qui aiment un même film le placent n° 6 des « Tendances », 40 membres → n° 1. Les « Pas pour moi » et les préférences ne touchent que le membre lui-même.

---

## 🗄️ Base de données (`data/fttp.db`, SQLite)

Créée automatiquement au premier lancement : 180 membres fictifs (dont 8 profils démo), ≈ 14 000 interactions, ≈ 1 300 séances, ≈ 9 400 événements.

| Table | Contenu |
|---|---|
| `utilisateurs` | e-mail, prénom, nom, pseudo, **hash du mot de passe**, avatar, tranche d'âge, ville, newsletter, consentement, dates, fictif, `est_demo` |
| `preferences` | genres, décennies, durée, origine, style (inscription, modifiables) |
| `interactions` | like · dislike · liste · vu · note (1-5), source, date |
| `seances` | carnet : film, date de séance, lieu (cinéma / streaming / TV-DVD), note, avis |
| `evenements` | connexions, recherches, fiches ouvertes (et depuis quelle reco), actions admin |
| `parametres` | réglages du moteur enregistrés par l'admin |

---

## 🖼️ Avatars

- 24 avatars dans `static/avatars/` (+ `mini/` pour l'en-tête) décrits dans `static/avatars/avatars.json` (libellé, catégorie, visible).
- **Ajouter des avatars** : Admin › 🖼️ Avatars › déposer une planche 3 × 2 (JPG/PNG) → découpage automatique → nommer → Importer. Libellés, catégories et visibilité se modifient dans le tableau.

---

## 🎨 Style et polices

- Boutons et onglets style **GTA VI × Retour vers le futur** : biseautés, italique majuscule, dégradé « coucher de soleil » pour l'action principale.
- Phrase de la bannière en **Kanit Black Italic** avec le dégradé du logo.
- Polices libres (licence OFL) **intégrées au projet** dans `static/polices/` : Kanit, Plus Jakarta Sans, Orbitron, Share Tech Mono, **DSEG7 / DSEG14** (afficheurs LED à segments des Time Circuits). L'app garde son apparence **même sans internet** (soutenance hors ligne). Licences dans `static/polices/licences/`.

## 🔎 Recherche prédictive

Composant maison sans dépendance (`composants/recherche/index.html`) : au premier lancement, le catalogue est exporté dans `static/recherche_<empreinte>.json` (≈ 1 Mo, recréé automatiquement si le CSV change) ; le navigateur filtre ensuite à chaque lettre, sans recharger la page. Flèches ↑ ↓ pour naviguer, Entrée pour choisir, Échap pour fermer. Utilisé dans Explorer, 88 MPH (« Tu as aimé… ? »), Mes films et l'aperçu admin.

## 🔐 Sécurité & RGPD

- Mots de passe : **PBKDF2-SHA256, 600 000 itérations, sel unique** ; temps de réponse identique si l'e-mail n'existe pas.
- Anti-force brute : blocage 30 s après 5 échecs (membres) et 60 s (admin) ; tentatives admin journalisées.
- Connexion en 1 clic **réservée aux 8 profils de démo** (`est_demo = 1`).
- Consentement explicite, inscription dès 15 ans ; **export JSON** (carnet inclus) et **suppression du compte** depuis le profil.
- Admin : e-mails masqués par défaut, export/suppression d'un membre, journal des actions.
- Adresses fictives en `@example.com` ; `.gitignore` exclut `.venv`, `secrets.toml` et la base des membres.

---

## 📁 Structure

```
Forward_To_The_Past/
├── app.py                  # point d'entrée : thème, en-tête, navigation, routage
├── config/                 # réglages et libellés (moteur, catalogue, affichage, base, avatars, chemins) — aucun calcul
├── outils/                 # petites fonctions pures : texte (normaliser, format_entrees), calcul
├── donnees/                # SQLite par sujet (base, securite, membres, interactions, carnet, journal, reglages) + catalogue CSV
├── medias/                 # avatars (galerie, import de planches) et affiches (locales ou TMDB)
├── demo/                   # membres fictifs + 8 profils démo (CLI : python -m demo.generation) — retirable
├── moteur/                 # communauté, profil membre, recommandation (film→films, membre→films), sélection, explications, évaluation
├── etat/                   # cache, contexte de la page, actions des boutons, navigation, XP & badges
├── interface/              # thème (style/*.css + theme.py) et composants : cartes, tuiles, jaquettes, barres, Time Circuits, graphes
├── recherche/              # recherche prédictive : composant (__init__.py) + index JSON (index.py)
├── composants/recherche/   # composant HTML/JS de la recherche prédictive
├── vues/                   # un fichier par écran : auth, accueil, explorer, machine, fiche, mes_films, profil
│   └── admin/              # espace admin : un fichier par onglet (+ connexion, chargement, comparaison, simulation)
├── data/                   # dataset_catalogue_Final_enrichi.csv + fttp.db
├── static/                 # logo, bannière, avatars/ (+ mini/, avatars.json), 39 affiches locales
├── .streamlit/             # config.toml (thème, fichiers statiques) + secrets.toml.exemple
├── .vscode/settings.json   # interpréteur .venv
├── LISEZMOI_CODE.md        # comprendre et modifier le code : « je veux modifier… → fichier », glossaire, règles
├── GUIDE_PERSONNALISATION.html  # guide interactif : toucher un élément sur la capture → page, fichier:ligne, ligne à coller
├── architecture.html       # schéma interactif des dossiers, des flux de données et du trajet d'un clic ❤️
├── BUGS_ET_RISQUES.md      # points connus, signalés et non corrigés
├── controle_correspondance.json  # où se trouve chaque élément de la V9 (utilisé par le kit de contrôle)
├── controle_fttp/          # kit de contrôle de non-régression (voir controle_fttp/LISEZMOI.md)
└── requirements.txt        # librairies (Streamlit 1.50, pandas, scikit-learn, plotly, Pillow…)
```

> **Pour modifier le code** : commencer par `LISEZMOI_CODE.md` (et `architecture.html` dans un navigateur).
> **Pour changer l'apparence** (couleur, police, taille, alignement, contour…) : ouvrir `GUIDE_PERSONNALISATION.html` dans un navigateur.

## 🛠️ Dépannage

| Symptôme | Solution |
|---|---|
| Affiches grises avec titre | Pas d'accès à `image.tmdb.org` : les 39 affiches locales restent affichées, les autres montrent un visuel de remplacement |
| Polices absentes | Vérifier que le dossier `static/polices/` est présent (polices servies localement) |
| Catalogue introuvable | Placer `dataset_catalogue_Final_enrichi.csv` dans `data/` |
| Erreur après mise à jour | Supprimer `data/fttp.db` puis relancer (la base est recréée) |

## 📚 Sources des données et usage

- **Catalogue** (`data/dataset_catalogue_Final_enrichi.csv`) construit à partir de :
  - **IMDb Non-Commercial Datasets** (titres, notes, votes, casting, réalisation) — https://developer.imdb.com/non-commercial-datasets/ — information courtesy of IMDb (https://www.imdb.com), usage personnel et non commercial ;
  - **TMDB** (affiches, synopsis, langues, pays) — *This product uses the TMDB API but is not endorsed or certified by TMDB* — https://www.themoviedb.org ;
  - entrées en salles en France issues des données publiques du CNC.
- **Usage pédagogique et non commercial** : projet du bootcamp Data Analyst (ciné-club « Forward To The Past », appel à projets CNC). Aucune exploitation commerciale du catalogue ni de l'app.
- **Membres** : la base `data/fttp.db` n'est pas publiée (`.gitignore`) ; elle est recréée au lancement avec des membres de démonstration fictifs.
- **Code admin de démonstration** : « 007 » tant que `.streamlit/secrets.toml` n'existe pas. Avant toute mise en ligne, créer ce fichier avec `ADMIN_MDP = "…"` (voir `BUGS_ET_RISQUES.md`, points 1 et 19).

## ✅ Contrôle de non-régression

Le dossier `controle_fttp/` contient le kit qui prouve qu'une version modifiée calcule et affiche exactement la même chose que la référence. Le copier à côté du projet, puis suivre `controle_fttp/LISEZMOI.md`.
