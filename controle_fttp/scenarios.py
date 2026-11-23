"""Parcours rejoués dans le navigateur pour photographier chaque écran de Forward To The Past (V9).

Chaque scénario = une suite d'actions depuis l'écran d'accueil, base de données remise à neuf avant chaque scénario.
Les sélecteurs s'appuient sur les clés Streamlit (key=...) et les libellés : la refactorisation ne doit pas les changer.

Pour ajouter un écran : ajouter une ligne dans SCENARIOS (nom → liste d'actions).
"""
from __future__ import annotations


# ------------------------------------------------------------------ actions élémentaires
def attendre(page, ms: int = 900) -> None:
    """Attend la fin du calcul Streamlit, le chargement des polices, puis une courte stabilisation."""
    page.wait_for_selector('[data-test-script-state="notRunning"]', timeout=120_000)
    page.wait_for_timeout(ms)
    page.wait_for_selector('[data-test-script-state="notRunning"]', timeout=120_000)
    page.evaluate("document.fonts.ready")


JS_IMAGES = """async () => {
  const imgs = [...document.images];
  imgs.forEach(i => { i.loading = 'eager'; });            // les images « paresseuses » se chargent aussi
  await Promise.all(imgs.map(i => i.complete ? null : new Promise(r => { i.onload = i.onerror = r; })));
  await Promise.all(imgs.map(i => i.decode ? i.decode().catch(() => null) : null));   // décodage terminé
}"""


def images_pretes(page) -> None:
    """Attend que toutes les images (avatars, affiches locales) soient chargées ET décodées."""
    page.evaluate(JS_IMAGES)
    page.wait_for_timeout(300)


def clic(selecteur: str, force: bool = True):
    def action(page):
        page.locator(selecteur).first.click(force=force)
        attendre(page)
    return action


def bouton(texte: str):
    def action(page):
        page.get_by_role("button", name=texte, exact=False).first.click()
        attendre(page)
    return action


def onglet(rang: int):
    """Clique sur le n-ième onglet visible (0 = premier)."""
    def action(page):
        page.get_by_role("tab").nth(rang).click()
        page.wait_for_timeout(900)
    return action


def code_admin(page) -> None:
    page.get_by_label("Code d'accès").fill("007")
    page.get_by_role("button", name="Entrer", exact=True).click()
    attendre(page, 1500)


DEMO = clic('[class*="st-key-cliq_demo_"] button')         # 1er profil de démo (Marty)
NAV = {p: clic(f".st-key-nav_{p} button") for p in ("accueil", "explorer", "machine", "mesfilms", "profil")}
ADMIN = clic(".st-key-btn_admin button")
FICHE = clic('[class*="st-key-pst_"] button')               # 1re jaquette de la page

# ------------------------------------------------------------------ scénarios (nom → actions)
SCENARIOS: dict[str, list] = {
    "01_accueil_public": [],
    "02_inscription_etape1": [bouton("Créer mon compte gratuitement")],
    "03_pour_toi": [DEMO],
    "04_fiche_film": [DEMO, FICHE],
    "05_explorer": [DEMO, NAV["explorer"]],
    "06_88mph_tu_as_aime": [DEMO, NAV["machine"]],
    "07_88mph_destination": [DEMO, NAV["machine"], onglet(1)],
    "08_88mph_convecteur": [DEMO, NAV["machine"], onglet(2)],
    "09_mes_films_carnet": [DEMO, NAV["mesfilms"]],
    "10_mes_films_favoris": [DEMO, NAV["mesfilms"], onglet(1)],
    "11_mes_films_pas_pour_moi": [DEMO, NAV["mesfilms"], onglet(3)],
    "12_profil_preferences": [DEMO, NAV["profil"]],
    "13_profil_avatar": [DEMO, NAV["profil"], onglet(1)],
    "14_profil_rgpd": [DEMO, NAV["profil"], onglet(3)],
    "15_admin_code": [ADMIN],
    "16_admin_vue_ensemble": [ADMIN, code_admin],
    "17_admin_membres": [ADMIN, code_admin, onglet(1)],
    "18_admin_reglages": [ADMIN, code_admin, onglet(2)],
    "19_admin_qualite": [ADMIN, code_admin, onglet(3)],
    "20_admin_avatars": [ADMIN, code_admin, onglet(4)],
    "21_admin_journal": [ADMIN, code_admin, onglet(5)],
}

# ------------------------------------------------------------------ affichages
UA_MOBILE = ("Mozilla/5.0 (Linux; Android 15; Pixel 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/131.0.0.0 Mobile Safari/537.36")
AFFICHAGES = {
    "bureau": {"viewport": {"width": 1440, "height": 900}},
    "mobile": {"viewport": {"width": 412, "height": 915}, "user_agent": UA_MOBILE, "is_mobile": True, "has_touch": True},
}
