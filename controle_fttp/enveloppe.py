"""Enveloppe du bruit de rendu de la V9 : pour chaque pixel instable, la plage de couleurs déjà observée.

Pourquoi : deux captures de la V9 NON modifiée ne sont pas toujours identiques (coins arrondis, avatars réduits,
graphiques, tableaux). Les deux séries de référence d'une exécution ne voient pas toujours ce bruit : on mémorise donc,
sur de nombreuses séries de la V9, la plage [min, max] de chaque pixel qui a varié.

Règle de comparaison : un pixel du candidat différent de la référence est TOLÉRÉ seulement s'il reste dans la plage
observée sur la V9 pour ce pixel (élargie à ses 8 voisins). Là où la V9 a toujours été stable (textes, bordures,
couleurs), aucune tolérance : le moindre niveau d'écart est détecté.

Construction (outil, à relancer si le navigateur ou les polices changent) :
    python enveloppe.py construire SORTIE.npz DOSSIER_CAPTURES_V9 [DOSSIER_CAPTURES_V9 ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ICI = Path(__file__).resolve().parent
FICHIER = ICI / "enveloppe_v9.npz"


def _canal(a: np.ndarray, filtre) -> np.ndarray:
    return np.stack([np.asarray(Image.fromarray(a[..., c]).filter(filtre)) for c in range(3)], axis=2)


def construire(sortie: Path, dossiers: list[Path]) -> dict:
    """Parcourt toutes les séries de captures V9 et enregistre, écran par écran, la plage des pixels instables."""
    noms = sorted({p.stem for d in dossiers for p in d.glob("*.png")})
    donnees, bilan = {}, {}
    for nom in noms:
        mini = maxi = None
        for d in dossiers:
            f = d / f"{nom}.png"
            if not f.exists():
                continue
            a = np.asarray(Image.open(f).convert("RGB"))
            if mini is None:
                mini, maxi = a.copy(), a.copy()
            elif a.shape != mini.shape:
                continue  # hauteur différente : non utilisable pour une plage pixel à pixel
            else:
                np.minimum(mini, a, out=mini)
                np.maximum(maxi, a, out=maxi)
        if mini is None:
            continue
        instable = (maxi != mini).any(axis=2)
        if not instable.any():
            continue
        zone = np.asarray(Image.fromarray((instable * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
        mini_v, maxi_v = _canal(mini, ImageFilter.MinFilter(3)), _canal(maxi, ImageFilter.MaxFilter(3))
        idx = np.flatnonzero(zone).astype(np.int32)
        donnees[f"{nom}|forme"] = np.array(mini.shape, np.int32)
        donnees[f"{nom}|idx"] = idx
        donnees[f"{nom}|min"] = mini_v.reshape(-1, 3)[idx]
        donnees[f"{nom}|max"] = maxi_v.reshape(-1, 3)[idx]
        bilan[nom] = int(instable.sum())
    np.savez_compressed(sortie, **donnees)
    return bilan


_CACHE: dict = {}


def tolere(nom: str, candidat: np.ndarray) -> np.ndarray | None:
    """Masque des pixels du candidat qui restent dans la plage de bruit observée sur la V9 (None si rien de connu)."""
    if not FICHIER.exists():
        return None
    if "z" not in _CACHE:
        _CACHE["z"] = np.load(FICHIER)
    z = _CACHE["z"]
    if f"{nom}|idx" not in z.files or tuple(z[f"{nom}|forme"]) != candidat.shape:
        return None
    idx, mn, mx = z[f"{nom}|idx"], z[f"{nom}|min"].astype(np.int16), z[f"{nom}|max"].astype(np.int16)
    valeurs = candidat.reshape(-1, 3)[idx].astype(np.int16)
    dans = ((valeurs >= mn - 1) & (valeurs <= mx + 1)).all(axis=1)
    masque = np.zeros(candidat.shape[0] * candidat.shape[1], bool)
    masque[idx[dans]] = True
    return masque.reshape(candidat.shape[:2])


if __name__ == "__main__" and len(sys.argv) > 3 and sys.argv[1] == "construire":
    b = construire(Path(sys.argv[2]), [Path(x) for x in sys.argv[3:]])
    print("pixels instables par écran :", b)
