"""Galerie d'avatars d'origine : catégories, libellés, avatar par défaut, anciennes clés des versions précédentes.

Utilise     : —
Utilisé par : donnees (base), medias (avatars)
"""

URL_AVATARS = "app/static/avatars/"  # adresse web des images (static/ servi par Streamlit)
CATEGORIES = ["Sci-Fi & 80s", "Gangsters & Action", "Cinéma culte", "Mascottes & Vice"]

META_DEFAUT = {  # clé : (libellé, catégorie) — 24 avatars d'origine (version V8)
    "scifi_1": ("Gilet rouge", "Sci-Fi & 80s"), "scifi_2": ("Savant fou", "Sci-Fi & 80s"),
    "scifi_3": ("Manteau noir", "Sci-Fi & 80s"), "scifi_4": ("Rousse cosmique", "Sci-Fi & 80s"),
    "scifi_5": ("Cyborg", "Sci-Fi & 80s"), "scifi_6": ("Astronaute", "Sci-Fi & 80s"),
    "robot_retro": ("Droïde synthwave", "Sci-Fi & 80s"), "cosmonaute_vice": ("Cosmonaute", "Sci-Fi & 80s"),
    "gangsters_1": ("Play-boy 70s", "Gangsters & Action"), "gangsters_2": ("Frange noire", "Gangsters & Action"),
    "gangsters_3": ("Pilote de nuit", "Gangsters & Action"), "gangsters_4": ("L'Aventurier", "Gangsters & Action"),
    "gangsters_5": ("Smoking", "Gangsters & Action"), "gangsters_6": ("Katana", "Gangsters & Action"),
    "pop_5": ("Le Solitaire", "Gangsters & Action"), "aventuriere_action": ("Aventurière", "Gangsters & Action"),
    "pop_1": ("La Parisienne", "Cinéma culte"), "pop_2": ("L'Agent", "Cinéma culte"),
    "pop_3": ("Le Boxeur", "Cinéma culte"), "pop_6": ("Le Détective", "Cinéma culte"),
    "realisateur_70s": ("Réalisateur 70s", "Cinéma culte"), "pop_4": ("Doberman cool", "Mascottes & Vice"),
    "chat_miami": ("Chat Miami", "Mascottes & Vice"), "aviatrice_vice": ("Aviatrice", "Mascottes & Vice"),
}
AVATAR_DEFAUT = "scifi_1"

# Anciennes clés (versions précédentes de l'app) → clés actuelles : les bases existantes restent valides.
ANCIENS = {
    "gilet-rouge": "scifi_1", "savant": "scifi_2", "manteau-noir": "scifi_3", "rousse": "scifi_4", "cyborg": "scifi_5",
    "astronaute": "scifi_6", "parisienne": "pop_1", "agent": "pop_2", "boxeur": "pop_3", "doberman": "pop_4",
    "solitaire": "pop_5", "detective": "pop_6", "playboy": "gangsters_1", "frange-noire": "gangsters_2",
    "pilote-nuit": "gangsters_3", "aventurier": "gangsters_4", "smoking": "gangsters_5", "katana": "gangsters_6",
    "neon-rider": "scifi_1", "vice-sunset": "gangsters_2", "doc-volt": "scifi_2", "arcade-kid": "pop_3",
    "palm-beach": "gangsters_3", "flamingo": "pop_1", "synthwave": "scifi_3", "cassette": "pop_6", "turbo": "scifi_5",
    "miami-nights": "gangsters_6", "hoverboard": "pop_4", "chrome": "scifi_6", "laser": "scifi_4",
    "retrowave": "gangsters_4", "outrun": "gangsters_5", "moonlight": "pop_5",
}
