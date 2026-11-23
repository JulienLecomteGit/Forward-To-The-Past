"""Messages (toasts) affichés après une réaction ❤️ ➕ 🤮 ou « déjà vu » : (type, ajouté ?) → (icône, texte).

Utilise     : —
Utilisé par : etat (actions)
"""

MESSAGES = {
    ("like", True): ("❤️", "Ajouté à tes coups de cœur · +5 XP"),
    ("like", False): ("💔", "Retiré de tes coups de cœur"),
    ("dislike", True): ("🤮", "Compris, on t’en proposera moins comme ça"),
    ("dislike", False): ("↩️", "Avis retiré"),
    ("liste", False): ("🗑️", "Retiré de tes films à voir"),
    ("vu", True): ("✅", "Marqué comme déjà vu · +2 XP"),
    ("liste", True): ("➕", "Ajouté à tes films à voir · +3 XP"),
    ("vu", False): ("↩️", "Plus marqué comme vu"),
}
