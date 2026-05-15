# PDF Structure Inspector

Application **Python / Tkinter** pour inspecter la structure logique d’un **PDF balisé** (accessibilité) : arbre issu de `/StructTreeRoot`, association aux MCID, aperçu des pages avec surlignage des éléments sélectionnés.

## Prérequis

- **Python 3.10+** (développement testé autour de 3.10)
- Un environnement virtuel recommandé

## Installation

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

Optionnel : placer un fichier `default.pdf` à la racine du projet pour ouverture automatique au démarrage.

## Fonctionnement général

Les PDF accessibles (ou « PDF balisés ») contiennent une structure logique (`/StructTreeRoot`) qui décrit l’organisation sémantique du document : titres, paragraphes, figures, tableaux, etc.

Ce projet tente de reconstruire et visualiser cette structure logique de manière similaire au panneau des balises d’Acrobat, tout en reliant chaque élément structurel à sa position visuelle réelle dans les pages du PDF.

À haut niveau, l’application fonctionne en plusieurs étapes :

---

### 1. Analyse initiale du PDF

Lorsqu’un PDF est ouvert, l’application vérifie d’abord si le document contient un objet `/StructTreeRoot`.

Si le document est balisé, le parseur extrait :

- les métadonnées du document ;
- les informations de langue ;
- le `/RoleMap` ;
- les références de pages ;
- la hiérarchie de la structure logique ;
- les identifiants de contenu balisé (`MCID`) ;
- les relations entre les balises et le contenu.

---

### 2. Lecture du content stream

L’application analyse ensuite les content streams du PDF afin d’extraire les sections de contenu associées aux valeurs `/MCID`.

Chaque bloc de contenu détecté est temporairement stocké dans une structure de dictionnaire interne.

À cette étape, le parseur connaît notamment :
- quel contenu appartient à quel MCID ;
- le texte brut extrait ;
- certaines informations de bas niveau liées à la structure PDF.

Cependant, la structure logique seule ne fournit pas toujours des coordonnées exploitables ni des informations de positionnement visuel suffisantes.

---

### 3. Réconciliation entre structure logique et layout visuel

Le principal défi du projet consiste à réconcilier :

- la structure logique/balisée du PDF ;
- le rendu visuel réel des pages.

Pour y parvenir, l’application combine des informations provenant :
- de l’arbre de structure logique ;
- des content streams ;
- d’analyses de layout effectuées avec `pdfminer.six` ;
- des informations de rendu fournies par `PyMuPDF (fitz)`.

Le parseur tente de faire correspondre le contenu balisé extrait avec les objets de layout correspondants (`LTChar`, lignes de texte, groupes de texte, etc.) afin de reconstruire :
- les bounding boxes ;
- les dimensions ;
- les positions sur la page ;
- les régions visuelles associées aux éléments balisés.

Les bounding boxes sont reconstruites en agrégeant les coordonnées des objets de layout au niveau caractère.

Ce processus permet d’associer les balises sémantiques du PDF (`H1`, `P`, `Figure`, etc.) aux régions réellement affichées dans la page.

---

### 4. Modèle de données interne

Les informations extraites sont regroupées dans un objet interne personnalisé nommé `PDFObject`.

Les principales structures actuellement utilisées sont :

- `self.metadatas`
- `self.role_maps`
- `self.page_references`
- `self.marked_content_dict`
- `self.structure`

`self.marked_content_dict` agit comme la principale source de données consolidées et regroupe notamment :
- les références MCID ;
- les noms des balises ;
- le texte extrait ;
- les numéros de page ;
- les dimensions ;
- les bounding boxes ;
- les informations de langue ;
- les textes alternatifs ;
- les données de positionnement visuel.

`self.structure` représente quant à lui la hiérarchie logique imbriquée du document.

---

### 5. Couche d’affichage / interface utilisateur

L’interface Tkinter utilise :
- la hiérarchie logique reconstruite ;
- le dictionnaire consolidé de contenu balisé ;
- les pages PDF rendues avec PyMuPDF.

L’application génère dynamiquement un `Treeview` navigable représentant la structure balisée du document.

Lorsqu’une balise est sélectionnée :
- la page correspondante est affichée ;
- des rectangles sont dessinés autour du contenu visuel associé ;
- les éléments imbriqués peuvent être parcourus récursivement et mis en évidence.

Cela permet de créer un pont visuel entre la structure sémantique d’accessibilité et le rendu réel du document.

---

## État actuel du projet

Le projet est actuellement un MVP expérimental.

Le parseur a été testé sur un grand nombre de PDF réels et fonctionne étonnamment bien avec plusieurs types de documents balisés, même si le format PDF demeure extrêmement variable selon les outils de génération et les workflows d’accessibilité utilisés.

Le projet nécessite encore :
- du nettoyage et du refactoring ;
- une meilleure séparation entre la logique de parsing et l’interface utilisateur ;
- des outils de navigation plus avancés ;
- une meilleure gestion des cas limites ;
- davantage de tests et de documentation.

Les contributions, idées et retours sont les bienvenus.

## Structure utile du dépôt

| Élément | Description |
|---------|-------------|
| `main.py` / `app.py` | Point d’entrée et orchestration. |
| `processing/` | Extraction PDF et arbre logique (voir `processing/README.md`). |
| `processing/_archive/` | Anciens scripts **non** utilisés par l’app. |
| `ui/` | Interface Tkinter (`_viewer.py` fenêtre principale ; `page_renderer.py` rendu PyMuPDF ; `thumbnail_strip.py` miniatures ; `structure_presenter.py` arbre Treeview). |
| `models/` | Objets d’affichage (branches, feuilles, boîtes englobantes). |
| `configs/` | Constantes d’affichage et debug. |
| `samples/`, `prompts/` | Fichiers d’exemple / notes de travail (hors pipeline principal). |

## Limites (MVP)

- Comportement et prise en charge des PDF réels **variables** selon générateur et complexité du balisage.
- Voir `FEUILLE_DE_ROUTE.md` pour les évolutions et refactors prévus.

## Licence

Voir le fichier `LICENSE` (MIT).
