# =============================================================================
# Fichier    : branch.py
# Projet     : PDF Structure Inspector
# Rôle       : Nœud interne de l'arbre (balise de structure PDF).
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Branche de structure : nom de balise et enfants (branches ou feuilles)."""

from configs.configurations import ICONS
from models.node import Node


class Branch(Node):
    """Balise structurante affichée dans le Treeview (ex. /P, /H1)."""

    def __init__(self, name, parent_branch=None):
        super().__init__(parent_branch)
        self.name = name
        self.parent_branch = parent_branch
        self.children = []

    def add_child(self, child):
        """Ajoute un enfant à cette branche."""
        self.children.append(child)

    def __str__(self):
        return f"{ICONS['branch']} {self.name}"
