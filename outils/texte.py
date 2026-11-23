"""Petites fonctions de texte réutilisées partout (aucune dépendance au reste du projet).

Utilise     : —
Utilisé par : donnees (catalogue), interface (cartes, jaquettes), moteur (explications),
              vues (auth, explorer, fiche, machine, mes_films, profil),
              vues/admin (onglet_journal, onglet_vue_ensemble)
"""
import unicodedata


def normaliser(s) -> str:
    """Texte comparable : minuscules, sans accents ni ponctuation (« Élan & Co » → « elan co »)."""
    s = unicodedata.normalize("NFKD", str(s or "").casefold().replace("œ", "oe").replace("æ", "ae"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join("".join(c if c.isalnum() else " " for c in s).split())


def format_entrees(n) -> str:
    """Nombre d'entrées lisible : 950 → « 950 », 12 500 → « 12 k », 1 250 000 → « 1,2 M »."""
    n = int(n or 0) if n == n else 0  # une valeur vide (NaN) compte pour 0
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} M".replace(".", ",")
    if n >= 1000:
        return f"{n // 1000} k"
    return str(n)


def date_fr(iso: str) -> str:
    """Date ISO « 2026-02-03 » → « 03/02/2026 » (texte vide si la date est absente ou incomplète)."""
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}" if iso and len(iso) >= 10 else ""


def annee_ou_vide(annee) -> str:
    """Année en texte (« 1985 »), ou chaîne vide si elle est inconnue (NaN)."""
    return str(int(annee)) if annee == annee else ""


def annee_entre_parentheses(annee) -> str:
    """« (1985) » précédé d'une espace, pour écrire « Titre (1985) » ; rien si l'année est inconnue (NaN)."""
    return f" ({int(annee)})" if annee == annee else ""


def annee_txt(annee) -> str:
    """Année d'un film en texte, ou « — » si elle est inconnue (NaN)."""
    return str(int(annee)) if annee == annee else "—"


def nombre_fr(n) -> str:
    """Nombre avec espace pour les milliers : 7356 → « 7 356 »."""
    return f"{n:,}".replace(",", " ")
