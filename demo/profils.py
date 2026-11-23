"""Données de démonstration : comptes de démo, prénoms, noms, villes, « tribus » de goûts, avis types.

Uniquement pour la démo : aucune valeur ici n'est utilisée par les vrais membres.

Utilise     : —
Utilisé par : demo (generation), vues (auth)
"""
from __future__ import annotations

MDP_DEMO = "retro1985"

COMPTE_DEMO = "marty.dubois@example.com"

PRENOMS = ["Lucas", "Emma", "Hugo", "Jade", "Louis", "Léa", "Gabriel", "Chloé", "Arthur", "Manon", "Jules", "Inès",
           "Adam", "Camille", "Raphaël", "Sarah", "Nathan", "Zoé", "Tom", "Lina", "Théo", "Alice", "Noah", "Lola",
           "Ethan", "Juliette", "Maël", "Rose", "Sacha", "Anna", "Paul", "Louise", "Yanis", "Ambre", "Karim", "Nina",
           "Mehdi", "Clara", "Antoine", "Sonia", "Kelly", "Julien", "Thomas", "Mathilde", "Nicolas", "Aïcha", "Bruno",
           "Fatou", "Olivier", "Isabelle", "Patrick", "Nathalie", "Sylvie", "Christophe", "Moussa", "Mei", "Diego",
           "Elsa", "Victor", "Margaux", "Samir", "Océane", "Bastien", "Laura", "Kevin", "Pauline", "Rémi", "Yasmine"]

NOMS = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau", "Simon",
        "Laurent", "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier", "Morel",
        "Girard", "Andre", "Mercier", "Dupont", "Lambert", "Bonnet", "François", "Martinez", "Legrand", "Garnier",
        "Faure", "Rousseau", "Blanc", "Guerin", "Muller", "Henry", "Roussel", "Nicolas", "Perrin", "Morin", "Mathieu",
        "Clement", "Gauthier", "Dumont", "Lopez", "Fontaine", "Chevalier", "Robin", "Masson", "Benali", "Nguyen",
        "Diallo", "Traoré", "Haddad", "Rossi", "Silva", "Kowalski", "Cohen", "Bouvier"]

VILLES = (["Paris"] * 14 + ["Boulogne-Billancourt", "Saint-Denis", "Montreuil", "Versailles", "Nanterre", "Créteil",
          "Vincennes", "Argenteuil", "Courbevoie", "Vitry-sur-Seine", "Lyon", "Marseille", "Lille", "Bordeaux",
          "Nantes", "Toulouse", "Nice", "Rennes", "Strasbourg", "Montpellier"])

TRIBUS = [  # nom, genres, décennies, origine, style, poids
    ("Nostalgiques 80s", ["Aventure - Action", "Science Fiction", "Comédie", "Film familial"], [1980], "indifferent", "cultes", 14),
    ("Comédie à la française", ["Comédie", "Comédie dramatique"], [1990, 2000, 2010], "francais", "cultes", 14),
    ("Frissons garantis", ["Horreur", "Thriller"], [1980, 1990, 2000], "international", "indifferent", 9),
    ("Familles & animation", ["Animation", "Film familial", "Fantasy"], [1990, 2000, 2010], "indifferent", "cultes", 11),
    ("Grands classiques", ["Drame", "Western", "Guerre", "Péplum"], [1960, 1970], "indifferent", "pepites", 8),
    ("Blockbusters", ["Aventure - Action", "Comicbook", "Science Fiction"], [2000, 2010], "international", "cultes", 13),
    ("Cœurs d'artichaut", ["Romance", "Comédie dramatique", "Musical"], [1990, 2000], "indifferent", "indifferent", 8),
    ("Polar à la française", ["Thriller", "Drame"], [1970, 1980, 1990], "francais", "indifferent", 8),
    ("Cinéphiles pointus", ["Drame", "Documentaire", "Comédie dramatique"], [1960, 1970, 2000], "indifferent", "pepites", 7),
    ("Geeks SF & fantasy", ["Science Fiction", "Fantasy", "Comicbook"], [1980, 1990, 2000, 2010], "international", "indifferent", 8),
]

AGE_PAR_DECENNIE = {  # tranches d'âge plausibles selon les décennies aimées
    1960: ["50-64 ans", "65 ans et +", "35-49 ans"], 1970: ["50-64 ans", "35-49 ans", "65 ans et +"],
    1980: ["35-49 ans", "25-34 ans", "50-64 ans"], 1990: ["25-34 ans", "35-49 ans", "18-24 ans"],
    2000: ["18-24 ans", "25-34 ans", "35-49 ans"], 2010: ["18-24 ans", "25-34 ans", "18-24 ans"],
}

VIDES = {"les", "des", "une", "dans", "pour", "avec", "sans", "sur", "the", "and", "of", "aux", "est", "qui", "que", "pas"}

DEMO_FAVORIS = ["tt0088763", "tt0089218", "tt0087363", "tt0092099", "tt0083866"]

# 8 comptes de démonstration affichés sur l'écran « Qui regarde ? » (connexion en un clic, comptes fictifs uniquement)
DEMOS = [
    dict(prenom="Marty", nom="Dubois", pseudo="Marty88", avatar="scifi_1", tribu=0, ville="Paris", age="18-24 ans",
         genres=["Science Fiction", "Aventure - Action", "Comédie"], decennies=[1980], format_duree="standard",
         origine="indifferent", style="cultes", favoris=DEMO_FAVORIS),
    dict(prenom="Lucia", nom="Fernandez", pseudo="FemmeFatale", avatar="gangsters_2", tribu=7, ville="Marseille",
         age="25-34 ans", genres=["Thriller", "Drame"], decennies=[1990, 1970], format_duree="standard",
         origine="indifferent", style="indifferent"),
    dict(prenom="Camille", nom="Laurent", pseudo="AmelieRetro", avatar="pop_1", tribu=1, ville="Paris", age="35-49 ans",
         genres=["Comédie", "Comédie dramatique"], decennies=[2000, 1990], format_duree="court", origine="francais",
         style="cultes"),
    dict(prenom="Enzo", nom="Moreau", pseudo="LElu", avatar="scifi_3", tribu=9, ville="Lyon", age="18-24 ans",
         genres=["Science Fiction", "Fantasy"], decennies=[1990, 2000], format_duree="long", origine="international",
         style="indifferent"),
    dict(prenom="Chloé", nom="Petit", pseudo="ChloeMiami", avatar="chat_miami", tribu=3, ville="Nantes", age="18-24 ans",
         genres=["Animation", "Film familial", "Fantasy"], decennies=[2000, 2010], format_duree="court",
         origine="indifferent", style="cultes"),
    dict(prenom="Henri", nom="Martin", pseudo="DocHenri", avatar="scifi_2", tribu=4, ville="Versailles",
         age="65 ans et +", genres=["Drame", "Western", "Guerre"], decennies=[1960, 1970], format_duree="long",
         origine="indifferent", style="pepites"),
    dict(prenom="Sarah", nom="Benali", pseudo="SarahFrissons", avatar="gangsters_6", tribu=2, ville="Lille",
         age="25-34 ans", genres=["Horreur", "Thriller"], decennies=[1980, 1990], format_duree="standard",
         origine="international", style="indifferent"),
    dict(prenom="Lucas", nom="Girard", pseudo="LucasSynth", avatar="pop_2", tribu=5, ville="Bordeaux", age="35-49 ans",
         genres=["Aventure - Action", "Comicbook", "Science Fiction"], decennies=[2000, 2010], format_duree="standard",
         origine="international", style="cultes"),
]

AVIS_POSITIFS = ["Culte, je ne m'en lasse pas.", "Revu avec plaisir, toujours aussi bon.", "Une claque visuelle !",
                 "Parfait pour une soirée entre amis.", "La bande originale est géniale.", "Un classique indémodable.",
                 "Je l'ai vu trois fois !", "Casting au top.", "", ""]

AVIS_NEGATIFS = ["Pas convaincu…", "Trop long à mon goût.", "Le scénario m'a perdu.", ""]
