# =============================================================================
# Fichier    : main.py
# Projet     : PDF Structure Inspector
# Rôle       : Point d'entrée — lance la boucle principale de l'application.
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
#
# Dépendances typiques (voir requirements.txt) :
#   - Python 3.10+
#   - PyMuPDF, PyPDF2, pdfminer.six, Pillow

from app import pdf_processor

if __name__ == "__main__":
    pdf_processor.run()
