# =============================================================================
# Fichier    : paned_window.py
# Projet     : PDF Structure Inspector
# Rôle       : PanedWindow avec limite de largeur par volet (Treeview / canvas).
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Séparateur redimensionnable entre le panneau d'arbre et l'aperçu PDF."""

import tkinter as tk


class PanedWindow(tk.PanedWindow):
    """PanedWindow horizontal avec respect optionnel d'une largeur maximale."""

    def __init__(self, *args, **kwargs):
        super(PanedWindow, self).__init__(*args, **kwargs)
        self.max_width = {}
        self.bind("<B1-Motion>", self.check_width)
        self.bind("<ButtonRelease-1>", self.set_width)

    def add(self, child, max_width=None, *args, **kwargs):
        """Ajoute un volet ; ``max_width`` borne la largeur lors du glissement du sash."""
        super(PanedWindow, self).add(child, *args, **kwargs)
        self.max_width[child] = max_width

    def check_width(self, event):
        """Pendant le déplacement du sash, ramène le volet à sa largeur max si besoin."""
        for widget, width in self.max_width.items():
            if width and widget.winfo_width() >= width:
                self.paneconfig(widget, width=width)
                return "break"

    def set_width(self, event):
        """Au relâchement, ajuste légèrement la largeur pour éviter le blocage du sash."""
        for widget, width in self.max_width.items():
            if width and widget.winfo_width() >= width:
                self.paneconfig(widget, width=width - 1)
