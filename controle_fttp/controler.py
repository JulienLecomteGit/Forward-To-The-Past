"""CONTRÔLE DE NON-RÉGRESSION — Forward To The Past.

Vérifie qu'une version refactorisée calcule et affiche EXACTEMENT la même chose que la version de référence (V9).
Les deux versions sont contrôlées dans la même exécution, sur la même machine, avec la même base de données figée :
la date du jour, les polices et l'environnement ne faussent donc pas la comparaison.

Usage (depuis le dossier controle_fttp, .venv activé) :
    python controler.py --reference ..\\Forward_To_The_Past_v9 --candidat ..\\Forward_To_The_Past_refacto

Options :
    --rapide          une seule série de captures de référence (pas de détection automatique du bruit de rendu)
    --sans-rejeu      ne pas rejouer automatiquement les écrans en écart (rejeu actif par défaut)
    --golden-seul     seulement les calculs métier (≈ 15 s), sans captures
    --captures-seules seulement les captures d'écran
    --scenarios A B   limiter les captures à certains écrans (noms dans scenarios.py)
    --sortie DOSSIER  dossier des résultats (défaut : resultats_controle)

Résultat : rapport.md dans le dossier de sortie + verdict CONFORME / NON CONFORME (code retour 0 / 1).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))

for _flux in (sys.stdout, sys.stderr):  # Windows : accents et symboles ✓ ✗ sans erreur d'encodage
    if hasattr(_flux, "reconfigure"):
        _flux.reconfigure(encoding="utf-8", errors="replace")

from captures import capturer  # noqa: E402
from comparer import comparer_captures, comparer_golden, reclasser_apres_rejeu  # noqa: E402

A_EXCLURE = shutil.ignore_patterns(".venv", "venv", "__pycache__", ".git", "*.pyc", "*.db", "*.db-wal", "*.db-shm",
                                   "recherche_*.json", "resultats_controle", "controle_fttp")


def preparer(source: Path, cible: Path) -> Path:
    """Copie propre du projet (sans environnement, cache, base ni index de recherche régénérable)."""
    if cible.exists():
        shutil.rmtree(cible)
    shutil.copytree(source, cible, ignore=A_EXCLURE)
    return cible


def golden(projet: Path, sortie: Path, base: Path, horloge: str) -> None:
    env = dict(os.environ, PYTHONHASHSEED="0", TZ="Europe/Paris", PYTHONIOENCODING="utf-8", FTTP_HORLOGE=horloge)
    r = subprocess.run([sys.executable, str(ICI / "golden.py"), str(projet), str(sortie), str(base)], env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout.strip())
    if r.returncode != 0:
        lignes = [x for x in r.stderr.strip().splitlines() if x.strip()]
        precis = next((x for x in lignes if x.startswith(("ÉLÉMENT INTROUVABLE", "→"))), None)
        message = "\n".join(x for x in lignes if x.startswith(("ÉLÉMENT INTROUVABLE", "→"))) if precis else "\n".join(lignes[-6:])
        raise RuntimeError(f"golden master impossible pour la version « {projet.name} » : {message}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reference", required=True, type=Path)
    ap.add_argument("--candidat", required=True, type=Path)
    ap.add_argument("--sortie", default=Path("resultats_controle"), type=Path)
    ap.add_argument("--rapide", action="store_true")
    ap.add_argument("--sans-rejeu", action="store_true")
    ap.add_argument("--golden-seul", action="store_true")
    ap.add_argument("--captures-seules", action="store_true")
    ap.add_argument("--scenarios", nargs="*")
    a = ap.parse_args()

    ref_src, cand_src, out = a.reference.resolve(), a.candidat.resolve(), a.sortie.resolve()
    base_src = ref_src / "data" / "fttp.db"
    for chemin, quoi in ((ref_src / "app.py", "app.py de la référence"), (cand_src / "app.py", "app.py du candidat"),
                         (base_src, "base data/fttp.db de la référence")):
        if not chemin.exists():
            print(f"✗ Introuvable : {quoi} ({chemin})")
            return 2
    debut = time.time()
    out.mkdir(parents=True, exist_ok=True)
    for ancien in ("captures_reference", "captures_reference_bis", "captures_candidat", "ecarts", "_travail",
                   "rejeu_reference", "rejeu_candidat", "ecarts_rejeu"):
        shutil.rmtree(out / ancien, ignore_errors=True)  # repartir d'un dossier de résultats propre
    for ancien in ("golden_reference.json", "golden_candidat.json", "rapport.md"):
        (out / ancien).unlink(missing_ok=True)
    travail = out / "_travail"
    base = out / "base_reference.db"
    shutil.copy(base_src, base)  # base figée, la même pour les deux versions
    print("① Préparation des copies de travail…")
    ref = preparer(ref_src, travail / "reference")
    cand = preparer(cand_src, travail / "candidat")

    horloge = str(float(int(time.time()) // 60 * 60))  # instant figé commun aux deux versions (minute entière)
    lignes_rapport, conforme = [], True
    # ---------------------------------------------------------------- golden master
    if not a.captures_seules:
        print("② Golden master (calculs métier)…")
        golden(ref, out / "golden_reference.json", base, horloge)
        try:
            golden(cand, out / "golden_candidat.json", base, horloge)
            ecarts = comparer_golden(out / "golden_reference.json", out / "golden_candidat.json")
        except RuntimeError as e:
            ecarts = [str(e)]
        conforme &= not ecarts
        lignes_rapport += ["## Calculs métier (golden master)", "",
                           "✅ **Strictement identiques** (recommandations, explications, recherches, statistiques, "
                           "base de données, CSS et HTML générés)." if not ecarts else
                           f"❌ **{len(ecarts)} écart(s)** (60 premiers affichés) :", ""]
        lignes_rapport += [f"- `{e}`" for e in ecarts] + [""]

    # ---------------------------------------------------------------- captures
    if not a.golden_seul:
        print("③ Captures de la référence…")
        echecs = capturer(ref, out / "captures_reference", base, a.scenarios, horloge)
        bis = None
        if not a.rapide:
            print("④ 2ᵉ série de référence (détection du bruit de rendu)…")
            echecs += capturer(ref, out / "captures_reference_bis", base, a.scenarios, horloge)
            bis = out / "captures_reference_bis"
        print("⑤ Captures de la version candidate…")
        echecs_cand = capturer(cand, out / "captures_candidat", base, a.scenarios, horloge)
        bilan = comparer_captures(out / "captures_reference", out / "captures_candidat", bis, out / "ecarts")
        mauvais = {k: v for k, v in bilan.items() if v[0] in ("ÉCART", "TAILLE", "MANQUANTE")}
        if mauvais and not a.sans_rejeu:
            # Règle du projet : un écart qui ne se reproduit pas est du bruit, un écart qui se reproduit est une régression.
            # On reprend donc en photo, référence ET candidat, les seuls écrans en écart, puis on les compare de nouveau.
            a_rejouer = sorted({k.split("_", 1)[1] for k in mauvais})
            print(f"⑥ Rejeu automatique de {len(a_rejouer)} écran(s) en écart : {', '.join(a_rejouer)}")
            echecs += capturer(ref, out / "rejeu_reference", base, a_rejouer, horloge)
            echecs_cand += capturer(cand, out / "rejeu_candidat", base, a_rejouer, horloge)
            bilan_rejeu = comparer_captures(out / "rejeu_reference", out / "rejeu_candidat", out / "captures_reference",
                                            out / "ecarts_rejeu")
            bilan = reclasser_apres_rejeu(bilan, bilan_rejeu)
            mauvais = {k: v for k, v in bilan.items() if v[0] in ("ÉCART", "TAILLE", "MANQUANTE")}
        conforme &= not mauvais and not echecs_cand
        icones = {"IDENTIQUE": "✅", "BRUIT": "🟡", "MICRO": "🟡", "ÉCART": "❌", "TAILLE": "❌", "MANQUANTE": "❌"}
        lignes_rapport += ["## Captures d'écran (bureau + mobile)", "",
                           f"{sum(v[0] == 'IDENTIQUE' for v in bilan.values())} identiques au pixel · "
                           f"{sum(v[0] in ('BRUIT', 'MICRO') for v in bilan.values())} avec bruit de rendu seulement · "
                           f"**{len(mauvais)} en écart**", "", "| Écran | Statut | Détail |", "|---|---|---|"]
        lignes_rapport += [f"| {k} | {icones[s]} {s} | {d} |" for k, (s, d) in sorted(bilan.items())]
        if echecs or echecs_cand:
            lignes_rapport += ["", "### Scénarios impossibles à jouer", ""] + [f"- référence : {e}" for e in echecs] + \
                              [f"- candidat : {e}" for e in echecs_cand]
        lignes_rapport += ["", "Images des écarts (pixels différents en rouge) : dossier `ecarts/`.", ""]

    verdict = "✅ CONFORME" if conforme else "❌ NON CONFORME"
    entete = [f"# Contrôle de non-régression — {verdict}", "",
              f"- Date : {datetime.now():%d/%m/%Y %H:%M} · durée {int(time.time() - debut)} s",
              f"- Référence : `{ref_src}`", f"- Candidat : `{cand_src}`", ""]
    (out / "rapport.md").write_text("\n".join(entete + lignes_rapport), encoding="utf-8")
    shutil.rmtree(travail, ignore_errors=True)
    print(f"\n{verdict} — rapport : {out / 'rapport.md'}")
    return 0 if conforme else 1


if __name__ == "__main__":
    sys.exit(main())
