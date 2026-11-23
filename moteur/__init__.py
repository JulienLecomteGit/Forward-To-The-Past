"""Moteur de recommandation 2.0 du ciné-club Forward To The Past.

Deux modes :
- « Tu as aimé X ? » (film → films proches) : genre, époque, durée, casting, réalisation,
  résumé (TF-IDF), goûts de la communauté ;
- « Pour toi » (membre → films) : préférences déclarées à l'inscription + historique
  (j'aime, notes, pas pour moi) + membres aux goûts proches (filtrage collaboratif).

Chaque composante vaut entre 0 et 1 ; les réglages admin sont des poids (0 à 10) qui
modifient réellement le classement. Une étape de diversité (MMR) évite 10 clones.

Fichiers :
  communaute.py      filtrage collaboratif (« ceux qui ont aimé ça ont aussi aimé… »)
  profil_membre.py   profil du membre (goûts déclarés + signaux récents)
  recommandation.py  les deux modes : similaires (film → films) et pour_toi (membre → films)
  selection.py       classement final : diversité, calibrage, saga
  explications.py    « Pourquoi ce film ? »
  evaluation.py      test de qualité hors-ligne (admin)
Les réglages (poids, valeurs d'usine) sont dans config/reglages_moteur.py.

Utilise     : config, donnees, outils
Utilisé par : etat, interface, vues
"""
