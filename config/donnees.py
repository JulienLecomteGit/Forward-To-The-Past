"""Constantes de la base de données : sécurité des mots de passe, types d'interactions, tranches d'âge, lieux.

Utilise     : —
Utilisé par : demo (generation), donnees (interactions, securite), vues (auth, fiche, mes_films, profil),
              vues/admin (onglet_membres, onglet_vue_ensemble)
"""
import re

# Hachage PBKDF2-SHA256 : 600 000 itérations (recommandation OWASP) ; types d'avis ; tranches d'âge ; e-mail valide
ITERATIONS = 600_000
TYPES_INTERACTION = ("like", "dislike", "liste", "vu", "note")
TRANCHES_AGE = ("15-17 ans", "18-24 ans", "25-34 ans", "35-49 ans", "50-64 ans", "65 ans et +")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")

# Lieux possibles d'une séance du carnet : code enregistré → libellé affiché
LIEUX = {"cinema": "🎟️ Au cinéma", "streaming": "📺 En streaming", "tv": "📼 TV / DVD"}
