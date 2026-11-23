"""Démonstration : 180 membres fictifs et 8 comptes de démo, pour que l'app soit vivante dès le premier lancement.

Ce dossier n'a pas vocation à rester en production. Il est relié au reste de l'app en 3 points seulement :
  1. app.py            : base vide au premier lancement → demo.generation.generer() ;
  2. vues/admin        : onglet « Journal & base » › « Régénérer les membres fictifs » → generer(reset=True) ;
  3. vues/auth         : rappel « Démo : marty.dubois@example.com · mot de passe retro1985 » (demo/profils.py).
Les comptes de démo en 1 clic (« Qui passe la séance ce soir ? ») sont des membres marqués est_demo = 1 en base
(donnees/membres.py : membres_demo, connecter_demo).

Commande : python -m demo.generation --help

Utilise     : config, donnees, medias, outils
Utilisé par : app, vues
"""
