"""Vérification ponctuelle des écrans publics (inscription 1→5, fiche avec séance, carnet) (parties interactives non jouées par le kit) : AppTest de Streamlit.

Pour chaque version : ouvre l'espace admin, clique « Lancer le test » (qualité), « Simuler » (3 scénarios), sélectionne le
mode « Un film » de l'aperçu, puis exporte TOUT le contenu affiché (textes, HTML, graphiques, tableaux, libellés).
Usage (depuis controle_fttp, .venv activé) :
    python controle_ecrans.py ..\\Forward_To_The_Past_v9 ..\\Forward_To_The_Past_refacto ..\\Forward_To_The_Past_v9\\data\\fttp.db
Durée ≈ 2 min. Verdict : ✅ IDENTIQUE / ❌ DIFFÉRENT, écran par écran (ordinateur et mobile).
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CODE = r'''
import json, os, random, re, sys, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
import time_machine
time_machine.travel(float(os.environ["FTTP_HORLOGE"]), tick=False).start()
random.seed(1985)
from google.protobuf.json_format import MessageToDict
from streamlit.testing.v1 import AppTest
from streamlit.testing.v1 import element_tree as et
# Contournement d'un bug de l'outil de test Streamlit 1.50 (boutons de choix : options = objets, pas des textes)
def _indices(self):
    valeurs = self.value if isinstance(self.value, (list, tuple)) else ([] if self.value is None else [self.value])
    if self.format_func is None:  # étoiles (st.feedback) : la valeur est déjà l'indice
        return [int(v) for v in valeurs]
    contenus = [o.content for o in self.options]
    sortie = []
    for v in valeurs:
        f = self.format_func(v)
        sortie.append(contenus.index(f.content if hasattr(f, "content") else str(f)))
    return sortie
et.ButtonGroup.indices = property(_indices)

IGNORE = {"uuid", "id", "formId", "deltaPath", "fragmentId", "scriptRunId", "key"}
import base64, pyarrow as pa
def tableau(b64):
    t = pa.ipc.open_stream(base64.b64decode(b64)).read_all().to_pandas()
    return {"colonnes": [str(c) for c in t.columns], "lignes": t.astype(str).values.tolist()}
def nettoie(x):
    if isinstance(x, dict):
        return {k: (tableau(v) if k == "data" and isinstance(v, str) and v.startswith("/////") else nettoie(v))
                for k, v in x.items() if k not in IGNORE}
    if isinstance(x, list):
        return [nettoie(v) for v in x]
    if isinstance(x, str):  # identifiant aléatoire des tableaux mis en forme par pandas (Styler) : sans effet visible
        return re.sub(r"T_[0-9a-f]{5,}", "T_x", x)
    return x
def contenu(at):
    out = []
    def visite(n):
        p = getattr(n, "proto", None)
        if p is not None and hasattr(p, "DESCRIPTOR"):
            out.append(nettoie(MessageToDict(p)))
        for c in getattr(n, "children", {}).values() if isinstance(getattr(n, "children", None), dict) else []:
            visite(c)
    visite(at._tree)
    return out

etapes = {}
import sqlite3
con = sqlite3.connect(os.environ["FTTP_BDD"])
uid = con.execute("SELECT id FROM utilisateurs WHERE est_demo = 1 ORDER BY id LIMIT 1").fetchone()[0]
film_carnet = con.execute("SELECT tconst FROM seances WHERE utilisateur_id = ? ORDER BY id LIMIT 1", (uid,)).fetchone()[0]
con.close()
base_ins = {"etape": 0, "avatar": "scifi_1", "genres": ["Comédie", "Drame", "Horreur"], "decennies": [1980, 1990],
            "format_duree": "court", "origine": "francais", "style": "pepites", "coeurs": ["tt0088763"], "page_films": 0,
            "prenom": "Test", "pseudo": "Testeur", "email": "t@example.com", "tranche_age": "25-34 ans", "nom": "Contrôle",
            "ville": "Paris", "mdp": "Retro-1985!", "newsletter": True, "rgpd": True}
for mobile in (False, True):
    for e in range(5):
        at = AppTest.from_file("app.py", default_timeout=600)
        at.session_state["mobile"] = mobile; at.session_state["ua_mobile"] = mobile
        at.session_state["inscription"] = dict(base_ins, etape=e)
        at.run(); etapes[f"inscription étape {e + 1}" + (" (mobile)" if mobile else "")] = contenu(at)
    at = AppTest.from_file("app.py", default_timeout=600)
    at.session_state["mobile"] = mobile; at.session_state["ua_mobile"] = mobile
    at.session_state["uid"] = uid; at.session_state["page"] = "fiche"; at.session_state["fiche"] = film_carnet
    at.session_state["page_avant"] = "mesfilms"; at.session_state["fiche_origine"] = "mes_films"
    at.run(); etapes["fiche d'un film du carnet" + (" (mobile)" if mobile else "")] = contenu(at)
    at.session_state["page"] = "mesfilms"; at.session_state.fiche = None
    at.run(); etapes["mes films (carnet)" + (" (mobile)" if mobile else "")] = contenu(at)
erreurs = [str(e.value)[:200] for e in at.exception]
print(json.dumps({"etapes": etapes, "exceptions": erreurs}, ensure_ascii=False, sort_keys=True, default=str))
'''


def executer(projet: Path, base: Path, horloge: str) -> dict:
    tmp = Path(tempfile.gettempdir()) / "fttp_controle_admin" / "fttp.db"  # chemin FIXE (affiché dans l'admin)
    tmp.parent.mkdir(exist_ok=True)
    for suffixe in ("-wal", "-shm"):
        Path(str(tmp) + suffixe).unlink(missing_ok=True)
    tmp.write_bytes(base.read_bytes())
    env = dict(os.environ, PYTHONHASHSEED="0", TZ="Europe/Paris", FTTP_BDD=str(tmp), FTTP_HORLOGE=horloge, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", CODE], cwd=projet, env=env, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit(r.stderr[-3000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


ref, cand, base = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
h = str(float(int(time.time()) // 60 * 60))
A, B = executer(ref, base, h), executer(cand, base, h)
print("exceptions référence :", A["exceptions"] or "aucune", "| candidat :", B["exceptions"] or "aucune")
ok = True
for etape in A["etapes"]:
    a, b = A["etapes"][etape], B["etapes"].get(etape)
    same = a == b
    ok &= same
    print(f"  {'✅' if same else '❌'} {etape:32} {len(a)} éléments affichés" + ("" if same else f" (candidat : {len(b or [])})"))
    if not same and b is not None:
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                if isinstance(x.get("data"), dict):
                    for la, lb in zip(x["data"]["lignes"], y["data"]["lignes"]):
                        if la != lb: print("     ligne réf.:", la, "\n     ligne cand:", lb)
                else:
                    print("     1er écart, élément", i, ":", json.dumps(x, ensure_ascii=False)[:300], "\n     ≠", json.dumps(y, ensure_ascii=False)[:300])
                break
print("✅ IDENTIQUE" if ok and A["exceptions"] == B["exceptions"] else "❌ DIFFÉRENT")
