# Forward To The Past · V10.4 — archive complète

Tout est dans ce dossier : code, données (`data/`), images et polices (`static/`), base de démo, guide, documentation, kit de contrôle et preuves.

## Lancer l'app (Windows, terminal VS Code)
```powershell
cd C:\Users\Julie\code\Forward_To_The_Past
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py
```

## Où trouver quoi
| Besoin | Fichier |
|---|---|
| Changer l'apparence (couleur, police, taille…) | `GUIDE_PERSONNALISATION.html` (ouvrir dans Chrome) |
| Comprendre et modifier le code | `LISEZMOI_CODE.md`, `architecture.html` |
| Nouveautés de la V10 | `README.md` (en tête) et `BUGS_ET_RISQUES.md`, section E |
| Bugs et risques connus | `BUGS_ET_RISQUES.md` |
| Présentation de l'app | `README.md` |
| Contrôle de non-régression | `controle_fttp/LISEZMOI.md` |
| Rapport final et résultats des contrôles | `preuves/` |

Dépôt public : https://github.com/JulienLecomteGit/Forward-To-The-Past · App en ligne : https://forward-to-the-past.streamlit.app/
