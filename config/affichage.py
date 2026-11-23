"""Constantes d'affichage partagées : emoji des genres, libellés des décennies, boutons de réaction, couleurs.

Utilise     : —
Utilisé par : interface (barres, cartes, graphes, textes, time_circuits),
              vues (accueil, auth, explorer, fiche, machine, mes_films, profil),
              vues/admin (onglet_membres, onglet_qualite, onglet_reglages, onglet_vue_ensemble, simulation)
"""

# Emoji affiché devant chaque genre, libellé court des décennies, boutons ❤️ ➕ 🤮 (type, emoji, info-bulle)
EMOJI_GENRE = {"Animation": "🧸", "Aventure - Action": "💥", "Catastrophe": "🌋", "Comicbook": "🦸", "Comédie": "😂",
               "Comédie dramatique": "🎭", "Court-métrage": "⏱️", "Documentaire": "🎥", "Drame": "💔", "Fantasy": "🐉",
               "Film familial": "👨‍👩‍👧", "Guerre": "🪖", "Horreur": "👻", "Musical": "🎤", "Péplum": "🏛️",
               "Romance": "💘", "Science Fiction": "🚀", "Thriller": "🔪", "Western": "🤠"}
DECENNIE_LIB = {1960: "60s", 1970: "70s", 1980: "80s", 1990: "90s", 2000: "2000s", 2010: "2010s"}
REACTIONS = (("like", "❤️", "J'aime"), ("liste", "➕", "À voir plus tard"), ("dislike", "🤮", "Pas pour moi"))

# Couleurs néon de l'app (graphiques, barres de répartition), dans l'ordre des critères
ROSE, TURQUOISE, AMBRE, VIOLET = "#DA4B84", "#7AD6CE", "#EBC374", "#8B5CF6"  # couleurs de la marque
ROSE_PALE, GRIS_LILAS = "#FFA8CF", "#C7BBD8"
PALETTE_NEON = [ROSE, TURQUOISE, AMBRE, VIOLET, "#F29E6B", "#5FD39A", "#E88FB1", "#A5B4FC"]
COULEURS_BARRES = PALETTE_NEON + [GRIS_LILAS, "#F6D365"]  # barres de répartition (10 critères)
COULEURS_CRITERES = PALETTE_NEON + ["#E5E7EB", "#14B8A6"]  # graphique « comment le moteur a décidé » (88 MPH)

# Mois au format des Time Circuits de la DeLorean (en anglais, comme dans le film)
MOIS_EN = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# Admin : couleur de chaque méthode du test de qualité, dégradé de la carte de chaleur, contour des parts du camembert
COULEURS_METHODES = {"Moteur · réglages enregistrés": ROSE, "Moteur · brouillon": AMBRE,
                     "Les plus populaires": TURQUOISE, "Au hasard": VIOLET}
DEGRADE_CHALEUR = [[0, "#1A1040"], [.35, "#6D28D9"], [.7, ROSE], [1, AMBRE]]
CONTOUR_PARTS = "#0D0724"

# Nombre d'éléments affichés selon l'écran : (ordinateur, mobile) — lire avec interface/mise_en_page.selon_ecran
FILMS_PAR_RANGEE = (4, 2)               # Pour toi : cartes par rangée (chaque sélection = 2 rangées)
FILMS_PAR_PAGE_EXPLORER = (24, 12)      # Explorer : cartes avant « Charger … films de plus »
FILMS_PAR_PAGE_INSCRIPTION = (18, 12)   # Inscription › coups de cœur : affiches proposées par page
JAQUETTES_PAR_RANGEE_ADMIN = (8, 4)     # Admin : jaquettes par rangée (aperçus, exemple, simulation)
LIGNES_PAR_PAGE_MES_FILMS = 20          # Mes films : lignes avant « Afficher … de plus »

# 88 MPH : année affichée au départ, dernier départ connu dans le film (26 oct. 1985, 1 h 21),
# nombre de meilleures recos parmi lesquelles le convecteur tire un film au sort
ANNEE_DE_DEPART = 1985
DERNIER_DEPART_DU_FILM = (1985, 10, 26, 1, 21)  # (année, mois, jour, heure, minute)
TIRAGE_CONVECTEUR = 30
