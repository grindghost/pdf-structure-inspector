# Traitement PDF

Modules utilisés par l’app (`app.py`) :

| Module | Rôle |
|--------|------|
| `pdf_file.py` | `PDFObject` — ouverture PyPDF2, métadonnées, `StructTreeRoot`, pages, RoleMap. |
| `_marked_content.py` | Lecture du flux de contenu (pdfminer) → dictionnaire de contenu marqué. |
| `_pdf_structtreeroot.py` | Reconstruction de l’arbre logique à partir de `StructTreeRoot` + MCID. |
| `pdf_device.py` | Device pdfminer personnalisé pour extraire le contenu marqué. |
| `pdf_interpret.py` | Interpréteur PDF associé au device. |

Le dossier `_archive/` contient d’anciens scripts **non branchés** à l’application (voir `_archive/README.md`).

L’affichage (PyMuPDF, Treeview, miniatures) est dans le paquet **`ui/`** à la racine du projet (voir `README.md`).
