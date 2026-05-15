# =============================================================================
# Fichier    : bounding_boxes.py
# Projet     : PDF Structure Inspector
# Rôle       : Rectangle de surlignage sur le canvas et liaison au Treeview.
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Affichage interactif des boîtes englobantes sur l'aperçu de page."""

import tkinter as tk
from tkinter import ttk


class BoundingBox:
    """Dessine un rectangle sur le canvas et synchronise la sélection avec l'arbre."""

    def __init__(self, canvas, bbox, treeview_item, pdf_viewer):
        self.canvas = canvas
        self.bbox = bbox
        self.treeview_item = treeview_item
        self.pdf_viewer = pdf_viewer
        self.rect_id = None
        self.default_color = "#c96efa"
        self.hover_color = "#ff6f91"
        self.selected_color = "#ff4d4d"

    def draw(self) -> None:
        """Trace le rectangle sur le canvas et attache les événements souris."""
        self.rect_id = self.canvas.create_rectangle(
            self.bbox,
            outline=self.default_color,
            tags="bounding_boxes",
            width=2,
            activedash=(4, 4),
        )
        self.bind_events()

    def bind_events(self) -> None:
        """Associe survol, sortie et clic au rectangle Tkinter."""
        self.canvas.tag_bind(self.rect_id, "<Enter>", self.on_hover)
        self.canvas.tag_bind(self.rect_id, "<Leave>", self.on_leave)
        self.canvas.tag_bind(self.rect_id, "<Button-1>", self.on_click)

    def on_hover(self, event):
        """Met en évidence le contour au survol."""
        self.canvas.itemconfig(self.rect_id, outline=self.hover_color)

    def on_leave(self, event):
        """Restaure la couleur par défaut lorsque la souris quitte la zone."""
        self.canvas.itemconfig(self.rect_id, outline=self.default_color)

    def on_click(self, event):
        """Sélectionne l'entrée correspondante dans le Treeview."""
        self.canvas.itemconfig(self.rect_id, outline=self.selected_color)

        self.pdf_viewer.tree.selection_set(self.treeview_item)
        self.pdf_viewer.tree.see(self.treeview_item)
