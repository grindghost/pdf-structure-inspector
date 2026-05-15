# =============================================================================
# Fichier    : struture_tree_view.py
# Projet     : PDF Structure Inspector
# Rôle       : Treeview dédié à la structure logique et dictionnaires d'index.
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Widget Treeview avec cartes id → nœud (branche ou feuille)."""

from tkinter import ttk


class StructureTreeview(ttk.Treeview):
    """Treeview pour l'aperçu de la structure balisée et les références aux feuilles."""

    def __init__(self, master, *args, **kwargs):
        ttk.Treeview.__init__(self, master, *args, **kwargs)
        self.leaf_dict = {}
        self.tag_dict = {}
