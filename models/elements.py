# =============================================================================
# Fichier    : elements.py
# Projet     : PDF Structure Inspector
# Rôle       : Feuilles spécialisées (lien, formulaire, figure, graphique placé).
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Types de feuilles pour liens OBJR, champs, images et graphiques vectoriels."""

from configs.configurations import ICONS, LEAF_ARE_MCID
from models.node import Node

_figure_registry: list = []


def reset_figure_registry() -> None:
    """Réinitialise les indices d'images entre deux constructions d'arbre."""
    _figure_registry.clear()


class Link(Node):
    """Hyperlien avec rectangle et inversion des coordonnées pour l'affichage."""

    def __init__(self, props, parent_tag=None):
        super().__init__(parent_tag)
        self.props = props
        self.original_bbox = self.props["/Rect"].copy()

        self.height = self.props["/PageHeight"]

    @property
    def bbox(self):
        """Boîte englobante dans le repère page (origine haut-gauche)."""
        top_y = self.height - float(self.original_bbox[3])
        bottom_y = self.height - float(self.original_bbox[1])

        new_bbox = self.original_bbox.copy()
        new_bbox[1] = top_y
        new_bbox[3] = bottom_y
        return new_bbox

    def __str__(self):
        if LEAF_ARE_MCID is True:
            try:
                return f"[{str(self.props['/MCID'])}] {self.props['/Name']}"
            except Exception:
                return "[...]"
        return f"{ICONS['link']} {self.props['/Name']}"

    def __repr__(self):
        return self.__str__()


class Form(Node):
    """Champ de formulaire (OBJR) avec rectangle et conversion de coordonnées."""

    def __init__(self, props, parent_tag=None):
        super().__init__(parent_tag)
        self.props = props

        self.original_bbox = self.props["/Rect"].copy()
        self.height = self.props["/PageHeight"]

    @property
    def bbox(self):
        """Boîte du champ dans le repère page."""
        top_y = self.height - float(self.original_bbox[3])
        bottom_y = self.height - float(self.original_bbox[1])
        new_bbox = self.original_bbox.copy()
        new_bbox[1] = top_y
        new_bbox[3] = bottom_y
        return new_bbox

    def __str__(self):
        if LEAF_ARE_MCID is True:
            return f"[{str(self.props['/MCID'])}] {self.props['/Name']}"
        return f"{ICONS['leaf']} {self.props['/Name']}"

    def __repr__(self):
        return self.__str__()


class Figure(Node):
    """Figure ou image : choix de la source de bbox (texte, dessin, arbre logique)."""

    def __init__(self, props, parent_tag=None):
        super().__init__(parent_tag)
        self.props = props

        self.UpdateDimensions()

        self.idx = len(_figure_registry)
        _figure_registry.append(self)

        self.UpdateName()

    def UpdateName(self):
        """Met à jour le libellé affiché avec l'indice d'image courant."""
        self.props["/Name"] = f"Image({self.idx})"

    def UpdateDimensions(self):
        """Recalcule largeur et hauteur à partir de la bbox effective."""
        self.props["/Width"] = abs(self.bbox[2] - self.bbox[0])
        self.props["/Height"] = abs(self.bbox[3] - self.bbox[1])

    @property
    def bbox(self):
        """Priorise XObj, puis texte, dessins, puis bbox issue de l'arbre logique."""
        if self.props.get("/XObj", None) is not None:
            print("Value used as Bbox:", "/Bbox")
            return self.props["/Bbox"]

        if self.props["/BboxText"] != [0.0, 0.0, 0.0, 0.0]:
            print("Value used as Bbox:", "/BboxText")
            return self.props["/BboxText"]
        if self.props["/BboxDrawings"] != [0.0, 0.0, 0.0, 0.0]:
            print("Value used as Bbox:", "/BboxDrawings")
            return self.props["/BboxDrawings"]
        return self.props["/BboxLogicalTree"]

    def __str__(self):
        if LEAF_ARE_MCID is True:
            return (
                f"[{str(self.props['/MCID'])}] Image({self.idx}): "
                f"w:{int(self.props['/Width'])} h:{int(self.props['/Height'])}"
            )
        return (
            f"{ICONS['image']} Image({self.idx}): "
            f"w:{int(self.props['/Width'])} h:{int(self.props['/Height'])}"
        )

    def __repr__(self):
        return self.__str__()


class PlacedGraphic(Node):
    """Graphique placé : bbox dérivée des rectangles de dessin (LTRect)."""

    def __init__(self, props, parent_tag=None):
        super().__init__(parent_tag)
        self.props = props

        self.UpdateDimensions()
        self.idx = len(_figure_registry)
        _figure_registry.append(self)

    def UpdateDimensions(self):
        """Recalcule largeur et hauteur à partir de /BboxDrawings."""
        self.props["/Width"] = abs(self.bbox[2] - self.bbox[0])
        self.props["/Height"] = abs(self.bbox[3] - self.bbox[1])

    @property
    def bbox(self):
        """Boîte englobante agrégée à partir des LTRect."""
        return self.props["/BboxDrawings"]

    def __str__(self):
        if LEAF_ARE_MCID is True:
            return f"[{str(self.props['/MCID'])}] {self.props['/Name']}"
        return f"({self.props['/MCID']}) 🖼 [{self.props['/Name']}]"

    def __repr__(self):
        return self.__str__()
