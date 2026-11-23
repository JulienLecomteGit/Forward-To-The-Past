"""Lance Streamlit avec le hasard et l'horloge figés, pour que deux versions de l'app soient comparables.

- random.seed : les tirages au hasard (avatar proposé, « Au hasard »…) sont les mêmes pour les deux versions.
- Horloge (time-machine) : datetime.now(), date.today(), pd.Timestamp.now(), time.time() renvoient tous le même instant
  figé, identique pour la référence et la version refactorisée (journal, KPI « vs semaine précédente », tendances…).

Utilisé par captures.py — ne pas lancer à la main.
Usage interne : python lanceur_streamlit.py <port>   (exécuté depuis le dossier du projet)
"""
import os
import random
import sys

random.seed(1985)  # même graine pour la référence et la version refactorisée

if os.environ.get("FTTP_HORLOGE"):  # instant figé, en secondes depuis 1970, fourni par controler.py
    import time_machine

    time_machine.travel(float(os.environ["FTTP_HORLOGE"]), tick=False).start()

from streamlit.web import cli  # noqa: E402

port = sys.argv[1]
sys.argv = ["streamlit", "run", "app.py", "--server.headless=true", f"--server.port={port}",
            "--server.address=127.0.0.1", "--server.fileWatcherType=none", "--server.runOnSave=false",
            "--browser.gatherUsageStats=false"]
sys.exit(cli.main())
