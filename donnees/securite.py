"""Mots de passe : empreinte PBKDF2-SHA256 (600 000 itérations, sel unique — recommandation OWASP), vérification, robustesse.

Utilise     : config (donnees)
Utilisé par : demo (generation), donnees (membres), vues (auth, profil)
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets

from config.donnees import ITERATIONS


def hacher(mdp: str) -> str:
    """Empreinte PBKDF2-SHA256 salée du mot de passe (le mot de passe n'est jamais stocké)."""
    sel = secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", mdp.encode("utf-8"), sel, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${sel.hex()}${h.hex()}"


def verifier(mdp: str, stocke: str) -> bool:
    """Vrai si le mot de passe correspond à l'empreinte stockée (comparaison à temps constant)."""
    try:
        algo, it, sel, attendu = stocke.split("$")
        if algo != "pbkdf2_sha256":
            return False
        calc = hashlib.pbkdf2_hmac("sha256", mdp.encode("utf-8"), bytes.fromhex(sel), int(it))
        return hmac.compare_digest(calc.hex(), attendu)
    except (ValueError, TypeError):
        return False


def robustesse(mdp: str) -> tuple[int, str]:
    """Score 0-4 et libellé, pour la jauge à l'inscription."""
    score = sum([len(mdp) >= 8, len(mdp) >= 12, bool(re.search(r"\d", mdp)) and bool(re.search(r"[A-Za-z]", mdp)),
                 bool(re.search(r"[^A-Za-z0-9]", mdp)) or (bool(re.search(r"[a-z]", mdp)) and bool(re.search(r"[A-Z]", mdp)))])
    return score, ["Trop faible", "Faible", "Correct", "Solide", "Blindé"][score]
