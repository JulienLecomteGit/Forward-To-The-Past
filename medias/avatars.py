"""Galerie d'avatars façon « Qui regarde ? » de Netflix, extensible depuis l'espace admin.

- Images : static/avatars/<cle>.jpg (servies par Streamlit) + static/avatars/mini/<cle>.jpg (72 px,
  intégrées en base64 là où une URL ne suffit pas : menu membre, tableau admin).
- Libellés, catégories, visibilité : static/avatars/avatars.json (créé au premier lancement).
- Une planche 3 × 2 déposée dans l'admin est découpée automatiquement en 6 avatars.

Utilise     : config (avatars, chemins)
Utilisé par : app, demo (generation), interface (cartes_membres), vues (accueil, auth, profil),
              vues/admin (onglet_avatars, onglet_membres, onglet_qualite, onglet_vue_ensemble)
"""
from __future__ import annotations

import base64
import io
import json
import re
import unicodedata
from functools import lru_cache

import numpy as np
from PIL import Image

from config.avatars import ANCIENS, AVATAR_DEFAUT, CATEGORIES, META_DEFAUT, URL_AVATARS
from config.chemins import DOSSIER_AVATARS

FICHIER_META = DOSSIER_AVATARS / "avatars.json"


# ------------------------------------------------------------------ métadonnées
def _lire_meta() -> dict:
    """Lit la description des avatars (libellé, catégorie) ; la recrée depuis les images si absente."""
    meta = {}
    if FICHIER_META.is_file():
        try:
            meta = json.loads(FICHIER_META.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            meta = {}
    if not meta:
        meta = {k: {"libelle": lib, "categorie": cat, "actif": True} for k, (lib, cat) in META_DEFAUT.items()}
    # toute image présente sans métadonnée est ajoutée (dépôt manuel dans le dossier)
    for p in sorted(DOSSIER_AVATARS.glob("*.jpg")):
        meta.setdefault(p.stem, {"libelle": p.stem.replace("_", " ").replace("-", " ").title(),
                                 "categorie": "Mes imports", "actif": True})
    return {k: v for k, v in meta.items() if (DOSSIER_AVATARS / f"{k}.jpg").is_file()}


_CACHE: dict = {}


def catalogue(tous: bool = False) -> dict:
    """{clé: {libelle, categorie, actif}} dans l'ordre d'affichage (actifs seulement par défaut)."""
    mtime = FICHIER_META.stat().st_mtime if FICHIER_META.is_file() else 0
    nb = len(list(DOSSIER_AVATARS.glob("*.jpg")))
    if _CACHE.get("cle") != (mtime, nb):
        _CACHE.update(cle=(mtime, nb), meta=_lire_meta())
    meta = _CACHE["meta"]
    return meta if tous else {k: v for k, v in meta.items() if v.get("actif", True)}


def enregistrer_meta(meta: dict) -> None:
    """Écrit la description des avatars et vide les caches correspondants."""
    DOSSIER_AVATARS.mkdir(parents=True, exist_ok=True)
    FICHIER_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    _CACHE.clear()
    data_uri.cache_clear()


def categories() -> list[str]:
    """Catégories d'avatars présentes, dans l'ordre prévu puis les nouvelles par ordre alphabétique."""
    vus = [v["categorie"] for v in catalogue().values()]
    return [c for c in CATEGORIES if c in vus] + sorted({c for c in vus if c not in CATEGORIES})


def par_categorie(categorie: str | None = None) -> list[str]:
    """Clés des avatars d'une catégorie (toutes si None ou « Tous »)."""
    return [k for k, v in catalogue().items() if categorie in (None, "Tous", v["categorie"])]


# ------------------------------------------------------------------ accès
def cle_valide(cle: str | None) -> str:
    """Clé d'avatar existante : convertit les anciennes clés, sinon avatar par défaut."""
    cle = ANCIENS.get(cle or "", cle or "")
    return cle if cle in catalogue(tous=True) else AVATAR_DEFAUT


def nom(cle: str) -> str:
    """Libellé lisible d'un avatar."""
    return catalogue(tous=True).get(cle_valide(cle), {}).get("libelle", "Avatar")


def url(cle: str) -> str:
    """Adresse web de l'image d'un avatar."""
    return URL_AVATARS + cle_valide(cle) + ".jpg"


@lru_cache(maxsize=None)
def data_uri(cle: str) -> str:
    """Image de l'avatar intégrée au HTML (miniature si elle existe) ; vide si illisible."""
    chemin = DOSSIER_AVATARS / "mini" / f"{cle_valide(cle)}.jpg"
    if not chemin.is_file():
        chemin = DOSSIER_AVATARS / f"{cle_valide(cle)}.jpg"
    try:
        return "data:image/jpeg;base64," + base64.b64encode(chemin.read_bytes()).decode("ascii")
    except OSError:
        return ""


def img(cle: str, taille: int = 40, classe: str = "ft-avatar", rayon: int | None = None) -> str:
    """Balise <img> carrée d'un avatar, à la taille demandée."""
    r = f"border-radius:{rayon}px;" if rayon is not None else ""
    return (f'<img class="{classe}" src="{url(cle)}" width="{taille}" height="{taille}" alt="Avatar {nom(cle)}" '
            f'style="width:{taille}px;height:{taille}px;object-fit:cover;{r}">')


# ------------------------------------------------------------------ import d'une planche 3 × 2
def _coutures(profil: np.ndarray, n: int) -> list[int]:
    """Positions des coupes : on cherche la plus forte rupture de couleur près de chaque 1/n."""
    taille = len(profil)
    coupes = [0]
    for k in range(1, n):
        cible = taille * k // n
        fen = slice(max(1, cible - taille // 25), min(taille - 1, cible + taille // 25))
        zone = profil[fen]
        coupes.append(fen.start + int(np.argmax(zone)) + 1 if len(zone) else cible)
    return coupes + [taille]


def _slug(texte: str) -> str:
    """Nom de fichier sûr à partir d'un texte (sans accents ni caractères spéciaux)."""
    s = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_") or "import"


def decouper_planche(contenu: bytes, colonnes: int = 3, lignes: int = 2) -> list[Image.Image]:
    """Découpe une planche de portraits en cases, en repérant les coutures entre images."""
    im = Image.open(io.BytesIO(contenu)).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    dx = np.abs(np.diff(a, axis=1)).sum(axis=(0, 2)).astype(float)
    dy = np.abs(np.diff(a, axis=0)).sum(axis=(1, 2)).astype(float)
    xs, ys = _coutures(dx, colonnes), _coutures(dy, lignes)
    tuiles = []
    for r in range(lignes):
        for c in range(colonnes):
            x0, x1, y0, y1 = xs[c] + 6, xs[c + 1] - 6, ys[r] + 6, ys[r + 1] - 6
            t = im.crop((x0, y0, x1, y1))
            w, h = t.size
            s = min(w, h)
            t = t.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
            tuiles.append(t.resize((320, 320), Image.LANCZOS))
    return tuiles


def importer_planche(contenu: bytes, categorie: str, libelles: list[str]) -> list[str]:
    """Découpe, enregistre les 6 avatars et les ajoute au catalogue. Retourne les nouvelles clés."""
    tuiles = decouper_planche(contenu)
    meta = catalogue(tous=True)
    base = _slug(categorie)
    cles = []
    for i, t in enumerate(tuiles, start=1):
        n, cle = i, f"{base}_{i}"
        while cle in meta or (DOSSIER_AVATARS / f"{cle}.jpg").exists():
            n += 6
            cle = f"{base}_{n}"
        (DOSSIER_AVATARS / "mini").mkdir(parents=True, exist_ok=True)
        t.save(DOSSIER_AVATARS / f"{cle}.jpg", quality=88, optimize=True)
        t.resize((72, 72), Image.LANCZOS).save(DOSSIER_AVATARS / "mini" / f"{cle}.jpg", quality=82, optimize=True)
        lib = (libelles[i - 1] if i - 1 < len(libelles) else "").strip() or f"{categorie} {i}"
        meta[cle] = {"libelle": lib, "categorie": categorie.strip() or "Mes imports", "actif": True}
        cles.append(cle)
    enregistrer_meta(meta)
    return cles


def apercu_planche(contenu: bytes) -> list[Image.Image]:
    """Aperçu du découpage d'une planche avant import (même découpage que l'import)."""
    return decouper_planche(contenu)
