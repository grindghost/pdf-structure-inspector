# Feuille de route — PDF Structure Inspector

Document de référence pour la préparation à la publication sur GitHub et les évolutions du MVP (application Python/Tkinter d’analyse de PDF balisés pour l’accessibilité).

---

## Objectif de ce document

- Garder une **vision partagée** de l’état du projet et des **prochaines étapes**.
- Prioriser le travail sans **big bang** : préserver un MVP fonctionnel à chaque itération.
- Servir de **point d’entrée** pour un contributeur externe (après README et dépendances).

---

## État d’avancement (refactors démarrés)

- [x] **Étape 1 (partielle)** : `README.md`, `requirements.txt`, `LICENSE` (MIT), scripts obsolètes déplacés vers `processing/_archive/`, `processing/README.md`.
- [x] **Étape 2** : titre fenêtre corrigé, `leaves_on_page` via `.get`, hauteurs bbox image / dessins (`y1 - y0`) dans `_marked_content.py`.
- [x] **Étape 3** : plus de variables globales `pages_ref_dict` / `role_map_dict` dans `_pdf_structtreeroot.py` — contexte `StructureTreeRebuildContext`.
- [x] **Important** : imports explicites dans `ui/_viewer.py` ; `figures_list` remplacé par `_figure_registry` + `reset_figure_registry()` dans `models/elements.py`.
- [x] **Étapes 4–6** : `ui/page_renderer.py` (pixmap → PhotoImage), `ui/thumbnail_strip.py` (miniatures), `ui/structure_presenter.py` (arbre + `flatten_branch`) ; `PDFViewer` allégé.
- [ ] **Étape 7** : tests automatisés, typage poussé, packaging `pip install -e .` (au besoin).

---

## Diagnostic synthétique

### Points forts

- Découpage **haut niveau** lisible : `main.py` → `app.py` → `processing/` (extraction PDF), `models/` (objets d’affichage / logique de présentation), `ui/` (Tkinter), `configs/`.
- Le flux principal est identifiable : chargement PDF → contenu marqué (pdfminer) → arbre logique (PyPDF2 / `StructTreeRoot`) → Treeview + surlignage (PyMuPDF).

### Points de friction

- **`ui/_viewer.py`** concentre trop de responsabilités (fenêtre principale, rendu page, miniatures, arbre, navigation, surlignage).
- **`processing/_pdf_structtreeroot.py`** mélange parcours de structure PDF, enrichissement du dictionnaire de contenu marqué et construction de la structure imbriquée (le contexte `StructureTreeRebuildContext` évite les variables globales de module).
- Les scripts hors pipeline ont été déplacés vers **`processing/_archive/`** (voir `_archive/README.md`).
- Quelques **fragilités** restantes : exceptions larges dans certains chemins, `print` dans le chemin nominal pour `PDFObject`, logique page/MCID répétitive.

---

## Vérifications demandées (synthèse)

| Question | Synthèse |
|----------|------------|
| 1. Organisation fichiers/dossiers | Plutôt claire ; confusion possible à cause des **doublons / scripts** dans `processing/`. |
| 2. Séparation modules/classes | Oui : surtout **éclater `PDFViewer`**, clarifier la reconstruction d’arbre, **retirer les globals** côté struct tree. |
| 3. Mélange PDF / données / Tkinter | **Partiellement** séparé ; le viewer reste fortement couplé à la logique métier et aux structures « props PDF ». |
| 4. Fonctions/classes trop longues | Principalement **`PDFViewer`** et **`traverse_tree`** ; `pdf_device.py` est volumineux mais cohérent avec un device pdfminer personnalisé. |
| 5. Noms explicites | Globalement corrects ; quelques **typos** (`struture_tree_view`, `metadatas`, etc.) et incohérences mineures. |
| 6. Fragile / répétitif | Globals, `except:` larges, prints dans le chemin nominal pour `PDFObject`, logique page/MCID répétitive. |
| 7. Compréhensibilité externe | Bonne **avec** README, dépendances et nettoyage des fichiers non utilisés ; moyenne **sans**. |
| 8. Avant GitHub | Voir priorités **critiques** ci-dessous. |

---

## Recommandations par priorité

### Critique (publication / clarté immédiate)

1. **Fichier de dépendances** — `requirements.txt` ou `pyproject.toml` avec versions alignées sur l’environnement réel (aujourd’hui partiellement documenté dans `main.py`).
2. **README** — Objectif, installation, commande de lancement, versions Python, limites connues du MVP ; capture d’écran optionnelle.
3. **Licence** — Fichier `LICENSE` si le dépôt est public et ouvert aux contributions.
4. **Hygiène du dépôt** — Statut explicite des dossiers/fichiers auxiliaires (`prompts/`, `samples/`) ; **déplacer, archiver ou documenter** les scripts `processing/` non branchés à l’app pour éviter les modifications sur le mauvais fichier.
5. **Bugs / robustesse évidents** (à traiter tôt) :
   - Titre fenêtre : `str(title=...)` dans `ui/_viewer.py` est invalide ; utiliser `str(...)` ou décoder proprement.
   - Pages sans feuilles : accès à `leaves_on_page[self.current_page]` peut lever une exception ; prévoir `.get` ou initialisation par page.
   - Vérifier les calculs de hauteur du type `height = y1 - x1` dans `processing/_marked_content.py` (souvent attendu : `y1 - y0`).

### Important (maintenabilité / contributions)

1. **Supprimer ou encapsuler les globals** dans `processing/_pdf_structtreeroot.py` — contexte explicite (classe ou paramètres) pour `pages_ref_dict` et `role_map_dict`.
2. **`figures_list` global** dans `models/elements.py` — remplacer par un registre contrôlé (compteur ou liste passée au moment de la construction des `Figure` / `PlacedGraphic`).
3. **Réduire `PDFViewer`** — extraire au minimum : rendu de page (PyMuPDF), panneau miniatures, logique « sélection Treeview → feuilles → surlignage ».
4. **Exceptions** — éviter `except:` nu ; journaliser derrière un flag de debug cohérent avec `configs/configurations.py`.
5. **Imports** — remplacer `from models.elements import *` par des imports nommés dans `ui/_viewer.py`.

### Amélioration future (sans urgence)

1. Typage progressif (TypedDict / structures pour les props « style PDF »).
2. Tests ciblés sur la reconstruction d’arbre et la résolution page/MCID (petits PDFs de fixture).
3. Renommages (fichier treeview, `metadata`, cohérence `leaf` / `leaves`).
4. CI légère (lint, `compileall`, ou un test minimal).

---

## Plan de refactorisation progressive

Principe : **petites étapes**, une vérification manuelle (ou test) après chaque étape : ouverture d’un PDF de référence, arbre, surlignage, miniatures.

### Étape 1 — Hygiène dépôt (peu de risque fonctionnel)

- Ajouter README, dépendances, licence.
- Décider du sort des fichiers `processing/` non utilisés par l’application : suppression, dossier `archive/` ou `experiments/`, ou note explicite en tête de fichier.
- Clarifier `prompts/` et `samples/` (garder, déplacer vers `docs/`, ou ignorer dans `.gitignore` selon intention).

### Étape 2 — Correctifs robustesse à faible risque

- Correction titre fenêtre (`ui/_viewer.py`).
- Garde-fous sur `leaves_on_page` par page.
- Relecture / correction des dimensions dans `_marked_content.py` si un bug visuel est confirmé.

### Étape 3 — Retirer les globals de reconstruction d’arbre

- Refactor local à `processing/_pdf_structtreeroot.py` : par exemple classe ou `dataclass` « contexte de reconstruction » ; conserver la signature publique `reconstruct_tree(pdf_file, marked_content_dict)` pour limiter les changements dans `app.py`.

### Étape 4 — Extraire le rendu de page depuis `PDFViewer` *(réalisé : `ui/page_renderer.py`)*

- Module dédié : chargement page, pixmap, conversion `PhotoImage` ; le viewer orchestre le canvas.

### Étape 5 — Extraire miniatures et défilement *(réalisé : `ui/thumbnail_strip.py`)*

- Classe `ThumbnailStrip` : panneau, scroll, population, synchro avec la page courante.

### Étape 6 — Extraire la logique d’arbre / présentation *(réalisé : `ui/structure_presenter.py`)*

- `StructurePresenter` + `flatten_branch` ; le viewer conserve sélection et surlignage.

### Étape 7 — Qualité long terme

- Typage, tests de non-régression, packaging installable (`pip install -e .`) si le projet grandit.

---

## Pistes techniques (rappel)

- Registre figures : `models/elements.py` (`reset_figure_registry`, `_figure_registry`).
- Couplage UI : `StructurePresenter` met à jour `pdf.marked_content_dict` ; le viewer conserve la navigation et le surlignage.

---

## Prochaine action suggérée

Enchaîner **Étape 1** puis **Étape 2** avant ou juste après la première publication ; enchaîner **Étape 3** dès qu’un contributeur touche à la reconstruction d’arbre, pour éviter les effets de bord entre ouvertures de fichiers.

---

*Document généré à partir d’une revue de structure et de code du dépôt ; à mettre à jour au fil des refactors (cocher les étapes, ajuster les chemins de fichiers si renommés).*
