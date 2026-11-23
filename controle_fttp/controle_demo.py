"""CONTRÔLE COMPLÉMENTAIRE — données de démonstration (non couvertes par controler.py).

Génère la base de démo (180 membres fictifs + 8 comptes de démo) avec la référence et avec le candidat, dans les mêmes
conditions (graine 1985, horloge figée, ordre des ensembles figé), puis compare les deux bases table par table.
Seule l'empreinte des mots de passe est exclue (sel aléatoire, différent à chaque hachage par conception).

Usage (depuis le dossier controle_fttp, .venv activé) :
    python controle_demo.py --reference ..\\Forward_To_The_Past_v9 --candidat ..\\Forward_To_The_Past_refacto
Durée : ≈ 2 min (hachage PBKDF2 de 188 mots de passe par version). Verdict : CONFORME / NON CONFORME (code 0 / 1).

Emplacements lus dans controle_correspondance.json du candidat (sinon emplacements V9) :
    "demo_generer": "demo.generation:generer", "lire_catalogue": "donnees.catalogue:lire_catalogue"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

for _flux in (sys.stdout, sys.stderr):
    if hasattr(_flux, "reconfigure"):
        _flux.reconfigure(encoding="utf-8", errors="replace")

DEFAUT = {"demo_generer": "donnees_fictives:generer", "lire_catalogue": "moteur:lire_catalogue", "CSV_NOM": "moteur:CSV_NOM"}
TABLES = {"utilisateurs": "id", "preferences": "utilisateur_id", "interactions": "id", "evenements": "id", "seances": "id"}

# Code exécuté DANS le dossier du projet (sous-processus) : génère la base puis l'exporte en JSON.
GENERER = r'''
import importlib, json, os, sqlite3, sys, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
import time_machine
time_machine.travel(float(os.environ["FTTP_HORLOGE"]), tick=False).start()
sys.path.insert(0, os.getcwd())
carte = json.loads(os.environ["CARTE"])
def obtenir(nom):
    m, _, a = carte[nom].partition(":")
    return getattr(importlib.import_module(m), a)
csv = open(os.path.join("data", obtenir("CSV_NOM")), "rb").read()
cat = obtenir("lire_catalogue")(csv)
stats = obtenir("demo_generer")(cat)
con = sqlite3.connect(os.environ["FTTP_BDD"]); con.row_factory = sqlite3.Row
sortie = {"stats": stats}
for table, cle in json.loads(os.environ["TABLES"]).items():
    lignes = [dict(r) for r in con.execute(f"SELECT * FROM {table} ORDER BY {cle}")]
    for l in lignes:
        l.pop("mdp_hash", None)
    sortie[table] = lignes
print(json.dumps(sortie, ensure_ascii=False, sort_keys=True, default=str))
'''


def generer(projet: Path, horloge: str) -> dict:
    carte = dict(DEFAUT)
    perso = projet / "controle_correspondance.json"
    if perso.exists():
        carte.update({k: v for k, v in json.loads(perso.read_text(encoding="utf-8")).items() if k in DEFAUT})
    base = Path(tempfile.mkdtemp()) / "demo.db"
    env = dict(os.environ, PYTHONHASHSEED="0", TZ="Europe/Paris", PYTHONIOENCODING="utf-8", FTTP_HORLOGE=horloge,
               FTTP_BDD=str(base), CARTE=json.dumps(carte), TABLES=json.dumps(TABLES))
    r = subprocess.run([sys.executable, "-c", GENERER], cwd=projet, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"génération impossible pour « {projet.name} » :\n" + "\n".join(r.stderr.strip().splitlines()[-8:]))
    return json.loads(r.stdout.strip().splitlines()[-1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reference", required=True, type=Path)
    ap.add_argument("--candidat", required=True, type=Path)
    a = ap.parse_args()
    horloge = str(float(int(time.time()) // 60 * 60))
    print("① Base de démo générée par la référence…")
    ref = generer(a.reference.resolve(), horloge)
    print("② Base de démo générée par le candidat…")
    cand = generer(a.candidat.resolve(), horloge)
    ecarts = []
    for cle in ["stats", *TABLES]:
        if ref[cle] != cand[cle]:
            n = sum(x != y for x, y in zip(ref[cle], cand[cle])) if isinstance(ref[cle], list) else 1
            ecarts.append(f"{cle} : {n} ligne(s) différente(s) (réf. {len(ref[cle])} lignes, cand. {len(cand[cle])} lignes)")
    resume = ", ".join(f"{t} {len(ref[t])}" for t in TABLES)
    empreinte = hashlib.sha256(json.dumps(ref, sort_keys=True, default=str).encode()).hexdigest()[:16]
    print(f"   lignes : {resume} · empreinte {empreinte}")
    if ecarts:
        print("❌ NON CONFORME —", " ; ".join(ecarts))
        return 1
    print("✅ CONFORME — base de démo strictement identique (hors empreintes de mots de passe)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
