# =============================================================================
# Fichier    : node.py
# Projet     : PDF Structure Inspector
# Rôle       : Nœud de base pour l'arbre de structure (parent commun).
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Classe de base des nœuds de structure (branche ou feuille)."""


class Node:
    """Représente un élément relié à une branche parente dans la hiérarchie."""

    def __init__(self, parent_tag):
        self.parent_tag = parent_tag

    def __str__(self):
        return "Node"

    def __repr__(self):
        return self.__str__()
