"""Comparaisons : golden master (JSON) et captures d'écran (pixels), avec masque du « bruit » de rendu.

Normalement appelé par controler.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from enveloppe import tolere


# ------------------------------------------------------------------ golden master
def ecarts_json(a, b, chemin: str = "", sortie: list | None = None, limite: int = 60) -> list[str]:
    """Liste lisible des différences entre deux JSON (chemin → valeur référence | valeur candidate)."""
    sortie = [] if sortie is None else sortie
    if len(sortie) >= limite:
        return sortie
    if type(a) is not type(b):
        sortie.append(f"{chemin} : type {type(a).__name__} → {type(b).__name__}")
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in b:
                sortie.append(f"{chemin}/{k} : absent de la version candidate")
            elif k not in a:
                sortie.append(f"{chemin}/{k} : en trop dans la version candidate")
            else:
                ecarts_json(a[k], b[k], f"{chemin}/{k}", sortie, limite)
    elif isinstance(a, list):
        if len(a) != len(b):
            sortie.append(f"{chemin} : {len(a)} éléments → {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            ecarts_json(x, y, f"{chemin}[{i}]", sortie, limite)
    elif a != b:
        if isinstance(a, str) and len(a) > 90:  # long texte (CSS, HTML) : montrer l'endroit exact de la différence
            i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            ligne = a.count("\n", 0, i) + 1
            sortie.append(f"{chemin} (ligne {ligne}, caractère {i}) : …{a[max(0, i - 40):i + 50]!r}… → "
                          f"…{b[max(0, i - 40):i + 50]!r}…")
        else:
            sortie.append(f"{chemin} : {str(a)[:90]!r} → {str(b)[:90]!r}")
    return sortie


def comparer_golden(ref: Path, cand: Path) -> list[str]:
    return ecarts_json(json.loads(ref.read_text(encoding="utf-8")), json.loads(cand.read_text(encoding="utf-8")))


# ------------------------------------------------------------------ captures
# Écart minuscule : signalé, non bloquant. Soit ≤ 10 pixels au total (lissage d'un coin, trait de tableau), soit
# ≤ 50 pixels d'intensité faible (≤ 10 niveaux sur 255 : dégradé d'un bouton, réduction d'une image), invisibles à l'œil.
MICRO_PX = 10
MICRO_PX_FAIBLE, MICRO_NIVEAUX = 50, 10


def _tableau(p: Path) -> np.ndarray:
    return np.asarray(Image.open(p).convert("RGB"), dtype=np.int16)


def masque_bruit(ref: Path, ref_bis: Path | None, marge: int = 3) -> np.ndarray | None:
    """Pixels qui changent entre deux captures de la MÊME version (anticrénelage, horloge…) : ignorés ensuite."""
    if ref_bis is None or not ref_bis.exists():
        return None
    a, b = _tableau(ref), _tableau(ref_bis)
    if a.shape != b.shape:
        return np.ones(a.shape[:2], bool)  # page instable en hauteur : tout est considéré comme bruit
    m = Image.fromarray(((np.abs(a - b).max(axis=2) > 0) * 255).astype(np.uint8))
    return np.asarray(m.filter(ImageFilter.MaxFilter(2 * marge + 1))) > 0


def comparer_captures(dossier_ref: Path, dossier_cand: Path, dossier_bis: Path | None, dossier_ecarts: Path) -> dict:
    """Renvoie {nom: (statut, détail)} ; statut ∈ IDENTIQUE, BRUIT, MICRO, ÉCART, TAILLE, MANQUANTE."""
    dossier_ecarts.mkdir(parents=True, exist_ok=True)
    bilan = {}
    for f_ref in sorted(dossier_ref.glob("*.png")):
        f_cand = dossier_cand / f_ref.name
        if not f_cand.exists():
            bilan[f_ref.stem] = ("MANQUANTE", "capture absente pour la version candidate")
            continue
        a, b = _tableau(f_ref), _tableau(f_cand)
        if a.shape != b.shape:
            bilan[f_ref.stem] = ("TAILLE", f"{a.shape[1]}×{a.shape[0]} px → {b.shape[1]}×{b.shape[0]} px (contenu décalé)")
            continue
        diff = np.abs(a - b).max(axis=2) > 0
        if not diff.any():
            bilan[f_ref.stem] = ("IDENTIQUE", "")
            continue
        bruit = masque_bruit(f_ref, dossier_bis / f_ref.name if dossier_bis else None)
        connu = tolere(f_ref.stem, b)  # bruit déjà observé sur la V9 (enveloppe.py) : seulement dans la plage connue
        if connu is not None:
            bruit = connu if bruit is None else (bruit | connu)
        reel = diff & ~bruit if bruit is not None else diff
        if not reel.any():
            bilan[f_ref.stem] = ("BRUIT", f"{int(diff.sum())} px, tous dans des zones instables de la référence")
            continue
        ys, xs = np.nonzero(reel)
        intensite = int(np.abs(a - b).max(axis=2)[reel].max())
        if reel.sum() <= MICRO_PX or (reel.sum() <= MICRO_PX_FAIBLE and intensite <= MICRO_NIVEAUX):
            bilan[f_ref.stem] = ("MICRO", f"{int(reel.sum())} px isolés (vers x {xs.min()}, y {ys.min()}, intensité ≤ {intensite}/255) : "
                                          "anticrénelage, invisible à l'œil — à regarder seulement si le doute persiste")
            continue
        # Image d'écart : capture candidate assombrie + pixels différents en rouge.
        vue = (b * 0.35).astype(np.uint8)
        vue[reel] = (255, 40, 40)
        Image.fromarray(vue).save(dossier_ecarts / f_ref.name)
        bilan[f_ref.stem] = ("ÉCART", f"{int(reel.sum())} px différents, zone x {xs.min()}–{xs.max()}, y {ys.min()}–{ys.max()}")
    for f_cand in sorted(dossier_cand.glob("*.png")):
        if not (dossier_ref / f_cand.name).exists():
            bilan[f_cand.stem] = ("MANQUANTE", "capture absente pour la référence")
    return bilan


def reclasser_apres_rejeu(bilan: dict, bilan_rejeu: dict) -> dict:
    """Écrans en écart rejoués : non reproduit → 🟡 BRUIT ; reproduit → l'écart d'origine reste bloquant."""
    nouveau = dict(bilan)
    for nom, (statut, detail) in bilan.items():
        if statut not in ("ÉCART", "TAILLE", "MANQUANTE"):
            continue
        statut2, detail2 = bilan_rejeu.get(nom, ("MANQUANTE", "écran non rejoué"))
        if statut2 in ("IDENTIQUE", "BRUIT", "MICRO"):
            nouveau[nom] = ("BRUIT", f"non reproduit au rejeu ({detail} ; rejeu : {statut2.lower()})")
        else:
            nouveau[nom] = (statut, f"{detail} — **reproduit au rejeu** ({detail2})")
    return nouveau
