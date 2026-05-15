# =============================================================================
# Fichier    : app.py
# Projet     : PDF Structure Inspector
# Rôle       : Fenêtre applicative — ouverture des PDF et enchaînement des
#              étapes d'extraction (flux marqué, arbre logique, Treeview).
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Application Tkinter : orchestration entre le modèle PDF et le visualiseur."""

import os
from tkinter import Button, filedialog

from processing._marked_content import read_content_stream
from processing._pdf_structtreeroot import reconstruct_tree
from processing.pdf_file import PDFObject
from ui._viewer import PDFViewer


class App:
    """Contrôle le cycle de vie de la fenêtre et le traitement d'un fichier PDF."""

    def __init__(self):
        self.viewer = PDFViewer(self)

        self.button = Button(
            self.viewer.canvas,
            text="Open PDF File",
            command=self.open_file,
        )
        self.button.pack(expand=True)

        self.default_pdf_path = os.path.join(os.path.dirname(__file__), "default.pdf")
        self.initialize_with_default_pdf()

    def initialize_with_default_pdf(self) -> None:
        """Ouvre ``default.pdf`` à la racine du projet s'il est présent."""
        if os.path.exists(self.default_pdf_path):
            self.open_pdf(self.default_pdf_path)
        else:
            print("No default PDF found. You can open a file manually.")

    def open_file(self) -> None:
        """Affiche la boîte de dialogue d'ouverture et charge le PDF choisi."""
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.open_pdf(file_path)

    def open_pdf(self, file_path) -> None:
        """Charge le document dans le visualiseur puis lance le traitement."""
        pdf = PDFObject(file_path)

        self.viewer.open_document(pdf)

        self.process(pdf)

    def read_content_stream(self, pdf_file) -> None:
        """Lit le flux de contenu avec pdfminer et remplit le dictionnaire marqué."""
        if pdf_file.tagged:
            self.viewer.pdf.marked_content_dict = read_content_stream(pdf_file)

    def reconstruct_tree(self, pdf_file) -> None:
        """Reconstruit la structure logique (PyPDF2) à partir du StructTreeRoot."""
        if pdf_file.tagged:
            self.viewer.pdf.logical_structure = reconstruct_tree(
                pdf_file, self.viewer.pdf.marked_content_dict
            )

    def create_treeview_widget(self, pdf_file) -> None:
        """Peuple le Treeview avec la structure logique reconstruite."""
        if pdf_file.tagged:
            self.viewer.populate_treeview(
                self.viewer.pdf.marked_content_dict,
                self.viewer.pdf.logical_structure,
            )

    def process(self, pdf_file) -> None:
        """Enchaîne extraction du contenu marqué, arbre logique et affichage."""
        self.read_content_stream(pdf_file)
        self.reconstruct_tree(pdf_file)
        self.create_treeview_widget(pdf_file)

    def run(self) -> None:
        """Démarre la boucle événementielle Tkinter."""
        self.viewer.mainloop()


pdf_processor = App()
