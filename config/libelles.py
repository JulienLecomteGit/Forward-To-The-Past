"""Libellés et listes de choix des écrans : préférences, tris, onglets, humeurs, sauts dans le temps, étapes…

Modifier un libellé ici le modifie partout où il est affiché.

Utilise     : —
Utilisé par : vues (auth, explorer, machine, mes_films, profil), vues/admin (onglet_vue_ensemble, simulation)
"""

# Préférences du membre : code enregistré en base → libellé affiché
LIBELLES_FORMAT = {"court": "⚡ Court (≈ 1 h 30)", "standard": "🎬 Standard (≈ 1 h 50)", "long": "🍿 Long (2 h +)",
                   "indifferent": "🤷 Peu importe"}
LIBELLES_ORIGINE = {"francais": "🇫🇷 Plutôt français", "international": "🌍 Plutôt international", "indifferent": "🎲 Les deux"}
# Le libellé « pépites » diffère volontairement entre l'inscription et le profil (textes de la V9 conservés à l'identique)
LIBELLES_STYLE_INSCRIPTION = {"cultes": "🏆 Les grands succès", "pepites": "💎 Les pépites méconnues", "indifferent": "🎲 Un peu de tout"}
LIBELLES_STYLE_PROFIL = {"cultes": "🏆 Les grands succès", "pepites": "💎 Les pépites", "indifferent": "🎲 Un peu de tout"}

# Inscription : nom des 5 étapes (barre de progression)
ETAPES_INSCRIPTION = ["Identité", "Avatar", "Genres", "Époques & style", "Coups de cœur"]

# Explorer : choix du menu « Trier par » (le 1er, « Pour toi », utilise le moteur)
TRIS_EXPLORER = ["⚡ Pour toi", "⭐ Mieux notés", "🎟️ Plus d'entrées en France", "🆕 Plus récents", "📼 Plus anciens", "🔤 A → Z"]

# Mes films : tris du carnet et des listes, onglets (titre, message si vide, info-bulle de la corbeille), filtres « tous »
TRIS_CARNET = {"recent": "📅 Séance la plus récente", "ancien": "📅 Séance la plus ancienne", "note": "⭐ Mieux notés d'abord",
               "titre": "🔤 Titre A → Z", "annee": "🕰️ Année de sortie (récent → ancien)"}
TRIS_LISTE = {"ajout": "🕒 Ajout le plus récent", "titre": "🔤 Titre A → Z", "annee": "🕰️ Année de sortie (récent → ancien)",
              "imdb": "⭐ Mieux notés (IMDb)", "duree": "⏱️ Plus courts d'abord"}
ONGLETS_MES_FILMS = {"like": ("❤️ Favoris", "Aucun favori pour l'instant : clique sur ❤️ sous une affiche.", "Retirer de mes favoris"),
                     "liste": ("➕ À voir", "Rien à voir pour l'instant : clique sur ➕ sous une affiche.", "Retirer de mes films à voir"),
                     "dislike": ("🤮 Pas pour moi", "Rien ici, tu es bon public !", "Ne plus l'écarter")}
TOUS_GENRES, TOUS_LIEUX = "Tous les genres", "Tous les lieux"

# 88 MPH : humeurs du convecteur (→ genres) et sauts dans le temps proposés (année → film emblématique)
HUMEURS = {"😂 Rire": ["Comédie", "Comédie dramatique"], "😱 Frissonner": ["Horreur", "Thriller"],
           "💘 Craquer": ["Romance", "Comédie dramatique", "Musical"], "🚀 S'évader": ["Science Fiction", "Fantasy", "Aventure - Action"],
           "🤯 Réfléchir": ["Drame", "Documentaire", "Guerre"], "👨‍👩‍👧 En famille": ["Animation", "Film familial"],
           "🤠 Grand spectacle": ["Western", "Péplum", "Catastrophe", "Comicbook"]}
SAUTS_DANS_LE_TEMPS = {1964: "Goldfinger", 1977: "Star Wars", 1985: "Retour vers le futur", 1993: "Jurassic Park", 1999: "Matrix",
                       2008: "The Dark Knight", 2015: "Retour vers le futur II"}

# Admin : jours de la semaine (carte de chaleur des connexions) et scénarios de la simulation
JOURS_SEMAINE = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
SCENARIOS_SIMULATION = ["❤️ Aime 5 films", "🤮 Rejette 5 films", "🧬 Change ses genres"]
