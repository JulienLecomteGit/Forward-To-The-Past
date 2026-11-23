"""Réglages du moteur de recommandation : valeurs d'usine, curseurs de l'admin, profils prêts à l'emploi.

Utilise     : —
Utilisé par : demo (generation), etat (cache), moteur (profil_membre, recommandation),
              vues (auth, fiche, machine, profil), vues/admin (onglet_qualite, onglet_reglages)
"""

# Valeurs d'usine (l'admin peut les modifier : elles sont alors enregistrées en base, table « parametres »)
PARAMS_DEFAUT = {
    "genre": 6.0, "epoque": 3.0, "tolerance": 15, "duree": 1.0, "casting": 3.0, "realisation": 3.0,
    "histoire": 4.0, "communaute": 3.0, "qualite": 2.0, "popularite": 0.0, "francais": 0.0,
    "declare": 5.0, "historique": 5.0, "recence": 5.0, "calibrage": 5.0, "diversite": 3.0, "saga": True, "note_min": 0.0,
    "nb_reco": 10, "masquer_vus": True,
}

# clé, libellé, explication vulgarisée, min, max, pas, groupe
REGLAGES = [
    ("genre", "🎭 Même genre", "Plus c'est haut, plus on reste dans le genre aimé (comédie → comédie).", 0, 10, .5, "Ressemblance"),
    ("epoque", "📅 Même époque", "Favorise les films sortis à peu près à la même période.", 0, 10, .5, "Ressemblance"),
    ("tolerance", "↔️ Écart d'années toléré", "Au-delà de cet écart, deux films ne sont plus « de la même époque ».", 2, 40, 1, "Ressemblance"),
    ("duree", "⏳ Durée similaire", "Un film de 1 h 30 appelle un film de 1 h 30.", 0, 10, .5, "Ressemblance"),
    ("histoire", "📖 Histoire qui se ressemble", "Compare les mots-clés des résumés (voyage dans le temps, braquage…).", 0, 10, .5, "Ressemblance"),
    ("casting", "🌟 Acteurs en commun", "Retrouver ses acteurs préférés. Les stars omniprésentes comptent un peu moins.", 0, 10, .5, "Équipe du film"),
    ("realisation", "🎬 Même réalisateur", "Un réalisateur aimé = ses autres films remontent.", 0, 10, .5, "Équipe du film"),
    ("communaute", "👥 Goûts des membres", "« Ceux qui ont aimé ça ont aussi aimé… » (comme Spotify ou Netflix).", 0, 10, .5, "Communauté"),
    ("declare", "🧬 Préférences de l'inscription", "Poids des goûts cochés à l'inscription (genres, décennies).", 0, 10, .5, "Profil membre"),
    ("historique", "❤️ Ce que le membre a aimé depuis", "Poids des j'aime, notes, séances et « Pas pour moi » laissés dans l'app.", 0, 10, .5, "Profil membre"),
    ("recence", "⚡ Réactivité aux dernières actions", "Plus c'est haut, plus les derniers j'aime / « Pas pour moi » pèsent lourd face aux anciens "
     "(0 = tous les j'aime comptent pareil).", 0, 10, .5, "Profil membre"),
    ("calibrage", "🎯 Respect de toutes ses envies", "La sélection reprend les proportions de ses goûts (ex. 50 % comédie, 30 % horreur) "
     "au lieu de ne montrer que son genre dominant — méthode « calibrated recommendations » de Netflix.", 0, 10, .5, "Profil membre"),
    ("qualite", "⭐ Bonnes notes du public", "Pousse les films bien notés (note IMDb pondérée par le nombre de votes).", 0, 10, .5, "Ligne éditoriale"),
    ("popularite", "🎟️ Pépites ↔ Succès en salles", "À gauche : films méconnus. À droite : gros succès au box-office France.", -5, 5, .5, "Ligne éditoriale"),
    ("francais", "🇫🇷 Coup de pouce cinéma français", "Bonus aux films (co)produits en France — cohérent avec la mission CNC.", 0, 5, .5, "Ligne éditoriale"),
    ("diversite", "🌈 Diversité des propositions", "Évite de proposer 10 films quasi identiques entre eux.", 0, 10, .5, "Affichage"),
    ("note_min", "🚫 Note minimale", "Les films sous cette note IMDb ne sont jamais proposés.", 0.0, 8.0, .5, "Affichage"),
    ("nb_reco", "🔢 Films par recommandation", "Nombre de films affichés dans chaque sélection.", 5, 20, 1, "Affichage"),
]
INTERRUPTEURS = [
    ("saga", "🔗 Toujours proposer un autre volet de la saga", "Si le film fait partie d'une saga, un autre épisode est garanti."),
    ("masquer_vus", "🙈 Masquer les films déjà vus", "Ne repropose pas un film marqué « déjà vu »."),
]
PRESETS = {
    "⚖️ Équilibré": {},
    "🍿 Grand public": {"popularite": 4.0, "qualite": 3.0, "diversite": 2.0, "histoire": 3.0},
    "🎓 Cinéphile": {"popularite": -4.0, "qualite": 6.0, "histoire": 6.0, "realisation": 6.0, "note_min": 6.5},
    "🌟 Fan de stars": {"casting": 8.0, "realisation": 6.0, "genre": 4.0},
    "🇫🇷 Spécial CNC": {"francais": 5.0, "qualite": 3.0, "popularite": 1.0},
    "🎲 Explorateur": {"diversite": 9.0, "communaute": 6.0, "genre": 3.0, "epoque": 1.0, "tolerance": 30},
}
COMPOSANTES = ("genre", "epoque", "duree", "histoire", "casting", "realisation", "communaute", "qualite",
               "popularite", "francais")
LIBELLES = {k: lib for k, lib, *_ in REGLAGES}

# Mode « Pour toi » : force d'un rejet, durées visées par format, décennies proposées
FORCE_REJET = 1.0  # un « pas pour moi » efface l’équivalent d’un j’aime récent du même genre
FORMATS_DUREE = {"court": (90, 25), "standard": (110, 25), "long": (145, 40)}
DECENNIES = list(range(1960, 2020, 10))

# Admin › Réglages du moteur : les curseurs sont rangés en 5 cartes (dans cet ordre)
CARTES_REGLAGES = {  # carte d'affichage : (icône, sous-titre, groupes de curseurs ci-dessus)
    "Profil membre": ("🧬", "Comment le moteur écoute chaque membre", ("Profil membre",)),
    "Ressemblance": ("🧩", "Ce qui rend deux films proches", ("Ressemblance",)),
    "Équipe & communauté": ("👥", "Acteurs, réalisateurs et goûts des autres membres", ("Équipe du film", "Communauté")),
    "Ligne éditoriale": ("🎟️", "La couleur du ciné-club", ("Ligne éditoriale",)),
    "Affichage": ("🖥️", "Règles de présentation des sélections", ("Affichage",)),
}
