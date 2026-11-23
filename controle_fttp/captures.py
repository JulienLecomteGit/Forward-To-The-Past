"""Photographie tous les écrans d'une version de l'app (bureau + mobile).

Usage : python captures.py <dossier_projet> <dossier_sortie> <base_reference.db> [nom_scenario ...]
Normalement appelé par controler.py.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from scenarios import AFFICHAGES, SCENARIOS, attendre, images_pretes

ICI = Path(__file__).resolve().parent

for _flux in (sys.stdout, sys.stderr):  # Windows : accents et symboles ✓ ✗ sans erreur d'encodage
    if hasattr(_flux, "reconfigure"):
        _flux.reconfigure(encoding="utf-8", errors="replace")
# Hauteur totale de la page (zone principale Streamlit), pour une capture pleine page.
JS_HAUTEUR = ("Math.max(document.querySelector('[data-testid=stMain]')?.scrollHeight || 0, "
              "document.body.scrollHeight)")


def port_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def remettre_base(base_ref: Path, base: Path) -> None:
    """Remet la base de travail dans son état d'origine (l'app ouvre et ferme une connexion à chaque opération)."""
    for suffixe in ("-wal", "-shm"):
        Path(str(base) + suffixe).unlink(missing_ok=True)
    shutil.copy(base_ref, base)


def demarrer_app(projet: Path, base: Path, horloge: str = ""):
    """Démarre l'app (base désignée par la variable FTTP_BDD) et renvoie (processus, port)."""
    port = port_libre()
    env = dict(os.environ, FTTP_BDD=str(base), PYTHONHASHSEED="0", TZ="Europe/Paris",
               FTTP_HORLOGE=horloge)
    proc = subprocess.Popen([sys.executable, str(ICI / "lanceur_streamlit.py"), str(port)], cwd=projet, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(300):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close()
            return proc, port
        except OSError:
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("L'application n'a pas démarré en 60 s.")


def capturer(projet: Path, sortie: Path, base_ref: Path, filtre: list[str] | None = None, horloge: str = "") -> list[str]:
    """Un seul serveur par série (catalogue chargé une fois) ; base remise à neuf avant chaque scénario."""
    sortie.mkdir(parents=True, exist_ok=True)
    echecs = []
    with sync_playwright() as pw:
        # Chemin FIXE (affiché dans Admin › Journal & base) : identique pour la référence et le candidat.
        dossier_base = Path(tempfile.gettempdir()) / "fttp_controle"
        dossier_base.mkdir(exist_ok=True)
        base = dossier_base / "fttp.db"
        remettre_base(base_ref, base)
        proc, port = demarrer_app(projet, base, horloge)
        base_url = f"http://127.0.0.1:{port}"
        navigateur = pw.chromium.launch()
        try:
            # Chauffe : premier chargement (catalogue, moteur, index de recherche) hors chronomètre et hors capture.
            chauffe = navigateur.new_page()
            chauffe.goto(base_url + "/")
            attendre(chauffe, 1000)
            chauffe.close()
            for affichage, options in AFFICHAGES.items():
                for nom, actions in SCENARIOS.items():
                    if filtre and nom not in filtre:
                        continue
                    remettre_base(base_ref, base)
                    try:
                        ctx = navigateur.new_context(device_scale_factor=1, locale="fr-FR", timezone_id="Europe/Paris",
                                                     reduced_motion="reduce", **options)
                        # Coupe internet (affiches TMDB…) : les deux versions sont photographiées dans les mêmes conditions.
                        ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith((base_url, "data:", "blob:"))
                                  else r.abort())
                        page = ctx.new_page()
                        page.goto(base_url + "/")
                        attendre(page, 1500)
                        for action in actions:
                            action(page)
                        attendre(page, 1200)
                        hauteur = page.evaluate(JS_HAUTEUR)
                        page.set_viewport_size({"width": options["viewport"]["width"], "height": min(int(hauteur) + 40, 16000)})
                        attendre(page, 800)
                        images_pretes(page)
                        page.screenshot(path=str(sortie / f"{affichage}_{nom}.png"), animations="disabled", caret="hide")
                        print(f"  ✓ {affichage:6} {nom}", flush=True)
                    except Exception as e:  # noqa: BLE001 — on continue, l'échec est listé dans le rapport
                        echecs.append(f"{affichage}_{nom} : {str(e).splitlines()[0][:160]}")
                        print(f"  ✗ {affichage:6} {nom} → {echecs[-1]}", flush=True)
                    finally:
                        try:
                            ctx.close()
                        except Exception:  # noqa: BLE001
                            pass
        finally:
            navigateur.close()
            proc.terminate()
            try:
                proc.wait(10)
            except subprocess.TimeoutExpired:
                proc.kill()
    return echecs


if __name__ == "__main__":
    echecs = capturer(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), sys.argv[4:] or None)
    sys.exit(1 if echecs else 0)
