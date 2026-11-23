"""Accès et sécurité des écrans de connexion : nombre d'essais, durée de blocage, code admin de démonstration.

Utilise     : —
Utilisé par : vues (auth), vues/admin (connexion)
"""

ESSAIS_MAX = 5                 # essais ratés avant blocage (membre comme admin)
BLOCAGE_CONNEXION_S = 30       # attente imposée après 5 échecs de connexion membre (secondes)
BLOCAGE_ADMIN_S = 60           # attente imposée après 5 codes admin faux (secondes)
CODE_ADMIN_DEMO = "007"        # utilisé seulement si ni secrets.toml (ADMIN_MDP) ni FTTP_ADMIN_MDP ne sont définis
