# =============================================================================
# Fichier    : leaf.py
# Projet     : PDF Structure Inspector
# Rôle       : Feuille de texte (Span) liée au contenu marqué et aux boîtes.
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Feuille d'affichage pour le texte issu du dictionnaire de contenu marqué."""

from configs.configurations import LEAF_ARE_MCID
from models.node import Node


class Leaf(Node):
    """Élément terminal associé à un bloc de texte (/BboxText, /Text, etc.)."""

    def __init__(self, props, parent_tag=None):
        super().__init__(parent_tag)
        self.props = props
        self.parent_tag = parent_tag

        self.UpdateDimensions()

    def UpdateDimensions(self):
        """Recalcule largeur et hauteur à partir de la boîte englobante."""
        self.props["/Width"] = abs(self.bbox[2] - self.bbox[0])
        self.props["/Height"] = abs(self.bbox[3] - self.bbox[1])

    @property
    def bbox(self):
        """Boîte du texte dans le repère page (coordonnées déjà harmonisées)."""
        return self.props["/BboxText"]

    def __str__(self):
        if LEAF_ARE_MCID is True:
            return f"[{str(self.props['/MCID'])}] {self.props['/Text']}"
        return f"📦 {self.props['/Text']}"

    def __repr__(self):
        return self.__str__()
