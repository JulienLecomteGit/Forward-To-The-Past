"""Catalogue de films : recherche du fichier CSV, contrôle et nettoyage des colonnes, index (genres, personnes, résumés TF-IDF) et recherche par titre ou par nom.

Utilise     : config (catalogue), outils (calcul, texte)
Utilisé par : demo (generation), etat (cache, contexte),
              moteur (communaute, evaluation, explications, profil_membre, recommandation, selection)
"""
from __future__ import annotations

import io
import math
import os
import re
import string
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from config.catalogue import CSV_NOM, DANS_PROJET, DOSSIER_PROJET, REQUIS
from outils.calcul import rang_percentile
from outils.texte import normaliser


def chemin_csv(dossier: Path, explicite: str = "") -> Path | None:
    """Chemin explicite (FTTP_CATALOGUE), puis dossier data/ du projet, puis Drive officiel."""
    indique = explicite or os.environ.get("FTTP_CATALOGUE", "")
    if indique:
        path = Path(indique).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"CSV introuvable au chemin configuré : {path}")
        return path
    dossier = dossier.resolve()
    candidats = [dossier / "data" / CSV_NOM, dossier / CSV_NOM]
    candidats += [parent / DANS_PROJET for parent in (dossier, *dossier.parents)]
    racines = [Path("/content/drive/MyDrive"), Path.home() / "Mon Drive", Path.home() / "My Drive"]
    if os.name == "nt":
        racines += [Path(f"{lettre}:/") / nom for lettre in string.ascii_uppercase for nom in ("Mon Drive", "My Drive")]
    candidats += [root / DOSSIER_PROJET / DANS_PROJET for root in racines]
    return next((path for path in candidats if path.is_file()), None)


def _liste(s) -> tuple[str, ...]:
    """Découpe une cellule « a|b|c » du CSV en tuple de valeurs propres (vide si absent)."""
    if not isinstance(s, str) or not s.strip():
        return ()
    return tuple(v.strip() for v in s.split("|") if v.strip())


class Catalogue:
    """Le catalogue en mémoire : le tableau des films et, pour le moteur, des colonnes prêtes au calcul
    (années, durées, popularité, index des acteurs et réalisateurs, résumés vectorisés…).
    Un film est désigné par sa position j (0 à n − 1) ; `position[tconst]` donne j.
    """
    def __init__(self, df: pd.DataFrame):
        """Prépare toutes les colonnes et index à partir du tableau lu dans le CSV."""
        df = df.sort_values("tconst", kind="stable").reset_index(drop=True)
        self.df = df
        self.n = len(df)
        self.position = {t: i for i, t in enumerate(df["tconst"])}
        self.annee = df["annee"].to_numpy(float)
        self.duree = df["duree"].to_numpy(float)
        self.decennie = (df["annee"] // 10 * 10).fillna(0).astype(int).to_numpy()
        self.genres = sorted(g for g in df["genre"].unique() if g)
        code = {g: k for k, g in enumerate(self.genres)}
        self.genre_code = df["genre"].map(code).fillna(-1).astype(int).to_numpy()
        self.note = df["note"].to_numpy(float)
        self.votes = df["votes"].fillna(0).to_numpy(float)
        self.entrees = df["entrees"].fillna(0).to_numpy(float)
        self.fr = df["fr"].to_numpy(bool)
        self.saga = np.array([normaliser(s) for s in df["saga"]], dtype=object)
        self.pop = rang_percentile(np.log1p(self.entrees))
        # Note pondérée façon IMDb : une note sur 50 votes pèse moins qu'une note sur 50 000.
        c, m = np.nanmean(self.note), np.nanpercentile(self.votes, 60)
        wr = (self.votes / (self.votes + m)) * np.nan_to_num(self.note, nan=c) + (m / (self.votes + m)) * c
        self.qualite = rang_percentile(wr)
        self.acteurs = list(df["acteurs_ids"])
        self.real = list(df["real_ids"])
        self.noms: dict[str, str] = {}
        for ids, noms in zip(list(df["acteurs_ids"]) + list(df["real_ids"]),
                             list(df["acteurs_noms"]) + list(df["real_noms"])):
            if len(ids) == len(noms):
                for p, nom in zip(ids, noms):
                    self.noms.setdefault(p, nom)
        self.index_acteurs, self.tailles_acteurs = self._index(self.acteurs)
        self.index_real, self.tailles_real = self._index(self.real)
        self.poids_acteur = {p: math.log((self.n + 1) / (len(ix) + 1)) / math.log((self.n + 1) / 2)
                             for p, ix in self.index_acteurs.items()}
        # Résumés → TF-IDF (mots-clés pondérés), vecteurs normalisés : cosinus = produit scalaire.
        self.vectoriseur = TfidfVectorizer(stop_words="english", min_df=2, max_df=0.35, sublinear_tf=True,
                                           token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]{2,}\b")
        self.tfidf = self.vectoriseur.fit_transform(df["resume"].fillna("")).tocsr().astype(np.float32)
        self.vocab = self.vectoriseur.get_feature_names_out()
        # Recherche : titres FR / originaux + noms des personnes
        self.alias = [{normaliser(t) for t in (a, b) if normaliser(t)} for a, b in zip(df["titre"], df["original"])]
        self.index_titres = defaultdict(set)
        for i, al in enumerate(self.alias):
            for t in al:
                self.index_titres[t].add(i)
        self.index_personnes = defaultdict(set)
        for i, ids in enumerate(zip(self.acteurs, self.real)):
            for p in ids[0] + ids[1]:
                if p in self.noms:
                    self.index_personnes[normaliser(self.noms[p])].add(i)
        self.par_popularite = np.argsort(-self.votes, kind="stable")

    def _index(self, roles):
        """Index personne → positions de ses films, et nombre de personnes par film."""
        index = defaultdict(list)
        for i, r in enumerate(roles):
            for p in r:
                index[p].append(i)
        return {p: np.asarray(ix) for p, ix in index.items()}, np.array([len(r) for r in roles])

    # -------------------------------------------------------------- accès
    def film(self, i: int) -> dict:
        """Toutes les informations du film j, sous forme de dictionnaire."""
        return self.df.iloc[int(i)].to_dict()

    def chercher(self, texte: str, limite: int | None = 60) -> list[int]:
        """Positions des films dont le titre correspond au texte : titre exact, puis début de titre, puis contenu ;
        à égalité, les plus populaires d'abord.
        """
        q = normaliser(texte)
        if not q:
            return []
        rang = {int(i): r for r, i in enumerate(self.par_popularite)}
        exact = self.index_titres.get(q, set())
        debut = {i for i, al in enumerate(self.alias) if i not in exact and any(a.startswith(q) for a in al)}
        contient = {i for i, al in enumerate(self.alias)
                    if i not in exact and i not in debut and any(q in a for a in al)}
        personnes = set()
        if len(q) >= 3:
            for nom, films in self.index_personnes.items():
                if q in nom:
                    personnes |= films
        personnes -= exact | debut | contient
        res = []
        for groupe in (exact, debut, contient, personnes):
            res += sorted(groupe, key=lambda i: rang[i])
        return res[:limite] if limite else res

    def sim_resume(self, i: int) -> np.ndarray:
        """Ressemblance (0 à 1) entre le résumé du film i et celui de chaque film."""
        return np.asarray((self.tfidf @ self.tfidf[i].T).todense()).ravel()

    def termes_communs(self, i: int, j: int, k: int = 2) -> list[str]:
        """Les k mots les plus marquants communs aux résumés des films i et j."""
        prod = self.tfidf[i].multiply(self.tfidf[j]).tocoo()
        if prod.nnz == 0:
            return []
        ordre = np.argsort(-prod.data)[:k]
        return [str(self.vocab[prod.col[o]]) for o in ordre]


def lire_catalogue(contenu: bytes) -> Catalogue:
    """Lit et contrôle le CSV (colonnes, clés IMDb) puis construit le Catalogue."""
    df = pd.read_csv(io.BytesIO(contenu), encoding="utf-8-sig", dtype={"tconst": str}, keep_default_na=True)
    absentes = set(REQUIS) - set(df.columns)
    if absentes:
        raise ValueError("Colonnes manquantes dans le CSV : " + ", ".join(sorted(absentes)))
    if df["tconst"].duplicated().any() or not df["tconst"].str.fullmatch(r"tt[0-9]{7,}").all():
        raise ValueError("Clés IMDb (tconst) vides, mal formées ou dupliquées.")
    if len(df) < 2:
        raise ValueError("Le catalogue doit contenir au moins deux films.")
    genre = df["genre_source"].fillna("").str.strip().replace({"Aventure - action": "Aventure - Action"})
    ids_valides = lambda s: tuple(dict.fromkeys(p for p in _liste(s) if re.fullmatch(r"nm[0-9]{7,}", p)))  # noqa: E731
    sortie = pd.DataFrame({
        "tconst": df["tconst"],
        "tmdb_id": pd.to_numeric(df.get("tmdb_id", pd.Series([0] * len(df))), errors="coerce").fillna(0).astype(int),
        "titre": df["titre_affiche"].fillna(df["originalTitle"]).fillna("").astype(str),
        "original": df["originalTitle"].fillna("").astype(str),
        "annee": pd.to_numeric(df["startYear"], errors="coerce"),
        "duree": pd.to_numeric(df["runtimeMinutes"], errors="coerce").where(lambda s: s > 0),
        "genre": genre,
        "langue": df["original_language"].fillna("").astype(str),
        "origine": df["origine_production"].fillna("Origine inconnue").astype(str),
        "pays": df.get("production_countries", pd.Series([""] * len(df))).fillna("").astype(str),
        "fr": df["film_francais"].astype(str).str.lower().isin(["true", "1", "vrai"]),
        "entrees": pd.to_numeric(df["entrees_france"], errors="coerce").fillna(0),
        "saga": df["saga"].fillna("").astype(str),
        "note": pd.to_numeric(df["averageRating"], errors="coerce"),
        "votes": pd.to_numeric(df["numVotes"], errors="coerce").fillna(0),
        "resume": df["overview"].fillna("").astype(str),
        "affiche": df["poster_path"].fillna("").astype(str),
        "acteurs_ids": df["acteurs_nconst"].map(ids_valides),
        "acteurs_noms": df["acteurs_principaux"].map(_liste),
        "real_ids": df["realisateurs_nconst"].map(ids_valides),
        "real_noms": df["realisateurs"].map(_liste),
    })
    return Catalogue(sortie)
