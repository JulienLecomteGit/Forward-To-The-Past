# Forward To The Past — rapport final (version V9.1 + guide)

> 23/11/2026 · Version finale = **Lot 14** : V9 consolidée (Lots 1 à 12) + corrections validées (Lot 13, V9.1) + nouveau guide de personnalisation (Lot 14).
> Publiée sur GitHub (public) : https://github.com/JulienLecomteGit/Forward-To-The-Past
> **[F]** fait vérifié (mesuré ou exécuté) · **[H]** hypothèse · **[R]** recommandation.

## 0. Ce qui a changé depuis la consolidation (soirée du 23/11)

| Lot | Changement | Verdicts réels du kit | Lecture |
|---|---|---|---|
| 13 · V9.1 | 6 corrections décidées avec Julien (bugs 4, 5, 6, 7, 10, 11 de `BUGS_ET_RISQUES.md`) | Golden : ❌ 26 écarts · Captures : 41 identiques + 1 🟡 bruit, **0 écart** · Démo : ✅ CONFORME · Admin et écrans non capturés : ❌ au bloc `<style>`, puis ✅ **IDENTIQUE** (8/8 et 15/15) relancés avec l'ancien CSS | les 26 écarts sont **tous attendus** : 2 = CSS allégé de 25 règles inutilisées ; 24 = ordre des noms rendu stable dans « Pourquoi ce film » (ex. « Lilly Wachowski » → « Lana Wachowski »). Recommandations, scores, recherches, base : identiques **[F]** |
| 14 | `GUIDE_PERSONNALISATION.html` refait (👆 toucher l'élément sur la capture → page, fichier:ligne, ligne à coller) ; `BUGS_ET_RISQUES.md` section D (points 13 à 20) ; 1 ligne de `LISEZMOI_CODE.md` et du README | Golden : ✅ CONFORME · Démo : ✅ CONFORME · Guide : 50 986 emplacements vérifiés, 0 échec · Test d'usage : 0 erreur JavaScript | aucun fichier de l'app modifié (3 fichiers de documentation) **[F]** |

`BUGS_ET_RISQUES.md` à jour : A = laissés par décision (1, 2, 3, 8, 9, 12) · B = corrigés au Lot 13 (4, 5, 6, 7, 10, 11) · C = traités pendant la consolidation · D = repérés au Lot 14, **à décider** (13 à 20).

---

# Rappel : consolidation V9 → version consolidée (Lots 1 à 12, comportement identique à la V9)

> 23/11/2026 · Référence : V9 (jamais modifiée : 0 fichier changé depuis l'audit, vérifié) · Candidat : version finale (Lot 12 + correction d'un chiffre du schéma HTML).
> **[F]** fait vérifié (mesuré ou exécuté) · **[H]** hypothèse · **[R]** recommandation.

## 1. Verdict

**✅ CONFORME. L'app consolidée calcule et affiche exactement la même chose que la V9.** **[F]**

```
Contrôle complet (kit v3.5) : ✅ CONFORME
  Calculs métier : ✅ Strictement identiques (recommandations, explications, recherches, statistiques,
                   base de données, CSS et HTML générés)
  Captures : 39 identiques au pixel · 3 avec bruit de rendu seulement · 0 en écart
  | bureau_03_pour_toi           | 🟡 BRUIT | 30 px, tous dans des zones instables de la référence |
  | bureau_16_admin_vue_ensemble | 🟡 BRUIT | 1 px, tous dans des zones instables de la référence |
  | mobile_16_admin_vue_ensemble | 🟡 BRUIT | non reproduit au rejeu (79 px différents ; rejeu : bruit) |
Base de démo        : ✅ CONFORME — base de démo strictement identique (hors empreintes de mots de passe)
Admin interactif    : ✅ IDENTIQUE
Écrans non capturés : ✅ IDENTIQUE
Table de correspondance : 61 entrées, toutes résolues dans la version finale
data/ · static/ · composants/ · .streamlit/ · requirements.txt : identiques à la V9 (0 différence)
```
Le rapport brut du kit est joint : `rapport.md`.

## 2. Avant / après (mêmes outils, mêmes règles de mesure) **[F]**

| Indicateur | V9 | Version finale | Lecture |
|---|---|---|---|
| Fichiers Python | 18 | **75** | un fichier = un rôle |
| Lignes Python | 5 042 (dont 736 de CSS dans `ui.py`) | **5 851** (sans CSS) + 730 lignes de CSS dans 18 fichiers `.css` | + 809 lignes au total = **+ 756 lignes de descriptions** (en-têtes et docstrings) + 341 lignes vides de séparation + 471 lignes de code (imports en tête des 75 fichiers, signatures des étapes découpées) − 736 lignes de CSS sorties en `.css` − 23 commentaires. Code seul : 3 554 → 4 025 lignes (+ 13 %) |
| Plus gros fichier | `ui.py` : 1 049 l. | `demo/generation.py` : 349 l. | ÷ 3 |
| Fichiers > 300 lignes | 5 | **2** (`demo/generation.py` 349, `vues/auth.py` 316) | voir § 5 |
| Fonction la plus longue | 166 l. | **51 l.** (50 de code + 1 de description) | ÷ 3,3 |
| Fonctions > 50 lignes | 9 | **2 à 51 lignes**, à cause de la ligne de description | 0 au-delà de 50 lignes de code |
| Complexité moyenne (radon) | B (5,81) | **A (4,40)** | − 24 % |
| Fonctions « difficiles » (notes D, E, F) | 14 (9 D, 4 E, 1 F) | **1 D** (`profil_membre`, 21 lignes, lisible de haut en bas) | |
| Fonctions et classes décrites | 47 / 233 | **317 / 317** | |
| Fichiers avec en-tête rôle / utilise / utilisé par | 0 / 18 | **75 / 75** | calculé à partir des imports réels |
| Imports cachés dans une fonction | 3 (`ui → contexte`, `ui → moteur`, `bdd → avatars`) | **0** | |
| Boucles d'imports | 0 (évitées grâce aux 3 imports cachés) | **0**, avec des imports tous en tête de fichier | |
| Remontées entre couches | — | **0** (sens `vues → interface → etat → moteur → donnees → config`) | vérifié à chaque lot |
| Code inutilisé (pyflakes) | 3 variables mortes | **0** | |
| Code inutilisé (vulture ≥ 80 %) | 1 | 1, **faux positif documenté** (`version`, clé de cache) | |
| Blocs de 3 lignes copiés-collés | 2 | 1 (deux lignes de colonnes identiques dans le schéma SQL : normal) | 14 motifs répétés factorisés |
| Dépendances (`requirements.txt`) | — | **identiques** | aucune ajoutée |

Note : l'audit de la Phase 1 parlait d'une « dépendance circulaire masquée » `ui ↔ contexte`. La mesure exacte montre qu'il n'y avait **pas de vraie boucle** : `ui.py` importait `contexte` *dans une fonction* pour en éviter une. La version finale n'a plus besoin de cette astuce.

## 3. Ce qui a été fait, lot par lot (un seul type de changement par lot)

| Lot | Changement | Verdict complet |
|---|---|---|
| 1 | CSS sorti de `ui.py`, tel quel, en 16 fichiers par zone + mobile + cadre | ✅ (1 écran de bruit, confirmé au rejeu) |
| 2 | `config/` (réglages, libellés) et `outils/` (petites fonctions) | ✅ |
| 3 | `donnees/` (base par sujet), `medias/`, `demo/` séparé | ✅ (1 écran de bruit, confirmé au rejeu) · démo ✅ |
| 4 | `moteur/` en 6 fichiers | ✅ |
| 5 | `interface/`, `etat/`, `recherche/` | ✅ (2 écrans de bruit, identiques au rejeu) |
| 6 | `vues/admin/` : un fichier par onglet | ✅ |
| 7 | 14 motifs répétés factorisés | ✅ |
| 8 | valeurs et textes réutilisés des écrans → `config/` | ✅ |
| 9 | code mort supprimé (6 éléments) | ✅ |
| 10 | fonctions de plus de 50 lignes découpées en étapes nommées | ✅ |
| 11 | en-têtes et descriptions (preuve : code exécuté identique) | ✅ |
| 12 | `LISEZMOI_CODE.md`, `architecture.html`, `BUGS_ET_RISQUES.md` | ✅ (code identique octet par octet) |
| Recette | contrôle complet + 3 contrôles complémentaires | ✅ |

**Le kit de contrôle a été renforcé en cours de route** (v1 → v3.5), sans jamais contourner la graine, l'horloge figée ou le mode hors ligne :
- connaissance du bruit de rendu de la V9 (enveloppe tirée de 27 séries) ;
- rejeu automatique d'un écran en écart : un écart non reproduit = bruit, un écart reproduit = régression ;
- 3 contrôles complémentaires pour ce que les captures ne couvraient pas : démo, admin interactif, écrans d'inscription et de carnet.

Un piège métier (un réglage du moteur modifié volontairement) est toujours détecté : 60 écarts de calcul.

## 4. Contraintes du brief **[F]**

| Contrainte | Respect |
|---|---|
| Visuel et métier strictement identiques | ✅ verdicts ci-dessus, à chaque lot et à la recette |
| V9 jamais modifiée · archives V8 non utilisées | ✅ 0 fichier V9 modifié · dossier d'archives jamais lu (un dépôt au mauvais endroit au tout début, déplacé aussitôt) |
| CSS final identique caractère pour caractère | ✅ contrôlé par le golden à chaque lot (y compris les styles `.ft-led` devenus inutiles, gardés selon ta décision) |
| Clés de widgets, libellés de boutons et d'onglets, `FTTP_BDD`, `static/`, `composants/recherche/`, décorateurs `st.cache_*`, signatures publiques | ✅ inchangés |
| Aucun dossier `pages/` · aucune boucle d'imports · aucune dépendance ajoutée | ✅ |
| Éléments déplacés listés dans `controle_correspondance.json` | ✅ 61 entrées, toutes résolues |
| Noms et en-têtes en français · fichiers ≤ ~300 l. · fonctions ≤ ~50 l. | ✅ avec les 4 exceptions mineures du § 5 |
| Bugs signalés, jamais corrigés sans accord | ✅ pendant la consolidation : 0 corrigé · ensuite 6 corrigés **sur décision** (Lot 13) |
| Verdicts réels du kit à chaque livraison | ✅ |

## 5. Écarts mineurs et choix assumés

| Écart | Pourquoi | Recommandation |
|---|---|---|
| `donnees/catalogue.py · Catalogue.__init__` et `vues/admin/onglet_qualite.py · afficher` : 51 lignes | 50 lignes de code + 1 ligne de description | aucune **[R]** |
| `demo/generation.py` : 349 lignes | 14 étapes nommées, chacune courte ; dossier retirable | aucune, ou séparer les étapes « activité » dans un second fichier **[R]** |
| `vues/auth.py` : 316 lignes | 5 étapes d'inscription + connexion + accueil public | séparer `vues/inscription.py` si l'inscription évolue **[R]** |
| En-tête de `demo/generation.py` non mis à jour | son texte s'affiche dans `--help` (texte visible) | risque n° 11 du tableau |
| `architecture.html` non publié en page web privée | refus d'une règle de sécurité automatique, non contourné | ouvrir le fichier depuis le zip ou la conversation |

## 6. Livraison (consolidation, remplacée par le § 8)

| Fichier | Contenu |
|---|---|
| `FTTP_V9_consolide_code.zip` | le projet complet **sans `data/` ni `static/`** (identiques à la V9, limite Drive de 3,1 Mo par fichier) : code, `controle_correspondance.json`, `LISEZMOI_CODE.md`, `architecture.html`, `BUGS_ET_RISQUES.md`, README, `.streamlit/`, `composants/` |
| `rapport.md` | rapport brut du kit (contrôle complet final) |
| `Final_controle_demo.txt` · `Final_controle_admin.txt` · `Final_controle_ecrans.txt` | contrôles complémentaires |
| `Rapport_final_avant_apres.md` | ce document |

**Remettre l'app en état de marche** : dézipper, puis copier les dossiers `data/` et `static/` de la V9 dans `Forward_To_The_Past/`. Ils sont strictement identiques, donc rien d'autre à faire. Lancer ensuite `python -m streamlit run app.py`.

## 7. Suites recommandées **[R]**

1. **Avant toute mise en ligne** : risque n° 1 (définir `ADMIN_MDP`) et n° 2 (blocage des essais en base).
2. **Avant de changer de CSV** : risques n° 4 et 5 (garde sur l'année, test qualité).
3. **Pour chaque future modification** : `LISEZMOI_CODE.md` § 5 pour trouver le fichier, puis `controler.py --golden-seul`. Une modification volontaire du visuel fait apparaître un écart : c'est normal, et la nouvelle version devient la référence.

## 8. Livraison finale (dossier Drive « Final », mis à jour le 23/11)

| Fichier | Contenu |
|---|---|
| `FTTP_V9_1_final_1_code.zip` | code V9.1 + guide + documentation (sans `data/` ni `static/`) |
| `FTTP_V9_1_final_2_data.zip` | `data/` : catalogue CSV + base de démo `fttp.db` (identiques à la V9) |
| `FTTP_V9_1_final_3_static_affiches.zip` | `static/affiches/` (identique à la V9) |
| `FTTP_V9_1_final_4_static_reste.zip` | le reste de `static/` : avatars, polices, bannière, image de partage, index de recherche (identique à la V9) |
| `GUIDE_PERSONNALISATION.html` | guide interactif (ouvrir dans Chrome) |
| `BUGS_ET_RISQUES.md` · `LISEZMOI_CODE.md` · `architecture.html` | documentation à jour |
| `Final_V9_vers_V9_1_rapport_kit.md` · `Final_V9_vers_V9_1_controle_*.txt` | contrôles du Lot 13 contre la V9 d'origine (bruts, et admin/écrans relancés avec l'ancien CSS) |
| `Final_V9_1_vers_Lot14_rapport_golden.md` · `Final_V9_1_vers_Lot14_controle_demo.txt` · `Final_verification_guide.txt` | contrôles du Lot 14 |
| `Rapport_final_avant_apres.md` | ce document |

**Projet complet** : dézipper les 4 archives **au même endroit** (elles partagent le dossier `Forward_To_The_Past/`), puis lancer `python -m streamlit run app.py`. Découpage par dossier à cause de la limite Drive de 3,1 Mo par fichier ; aucun fichier n'est coupé. Vérifié : les 4 archives remontées = projet identique, `data/` et `static/` identiques à la V9, l'app démarre sans erreur. Autre voie : GitHub › Code › Download ZIP (sans `fttp.db`, recréée au lancement).

