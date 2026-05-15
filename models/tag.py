# =============================================================================
# Fichier    : tag.py
# Projet     : PDF Structure Inspector
# Rôle       : Variante de nœud « balise » (peu utilisée dans le flux actuel).
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Modèle de balise générique avec liste d'enfants."""

from models.node import Node


class Tag(Node):
    """Balise nommée et hiérarchie d'enfants (hors icônes de configuration)."""

    def __init__(self, name, parent_tag=None):
        super().__init__(parent_tag)
        self.name = name
        self.parent_tag = parent_tag
        self.children = []

    def add_child(self, child):
        """Ajoute un enfant à cette balise."""
        self.children.append(child)

    def __str__(self):
        return f"🏷 {self.name}"
