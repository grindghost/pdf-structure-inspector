# =============================================================================
# Fichier    : structure_presenter.py
# Projet     : PDF Structure Inspector
# Rôle       : Construction du Treeview à partir de la structure logique.
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Présentateur : arbre hiérarchique et feuilles liées au dictionnaire marqué."""

from __future__ import annotations

from typing import Any, Dict, List, MutableMapping, Union

import tkinter as tk
from tkinter import ttk

from models.branch import Branch
from models.leaf import Leaf
from models.elements import Figure, Form, Link, PlacedGraphic, reset_figure_registry


def flatten_branch(tag: Branch) -> List[Union[Branch, Leaf, Figure, Form, Link, PlacedGraphic]]:
    """Aplatit récursivement une branche en liste (branches et feuilles dans l'ordre)."""
    flat_list: List[Any] = [tag]
    for child in tag.children:
        if isinstance(child, Branch):
            flat_list.extend(flatten_branch(child))
        else:
            flat_list.append(child)
    return flat_list


class StructurePresenter:
    """
    Remplit le Treeview et le dictionnaire ``leaves_on_page`` à partir du contenu marqué
    et de la structure imbriquée renvoyée par ``reconstruct_tree``.
    """

    def __init__(self) -> None:
        self._pdf: Any = None
        self._pdf_document: Any = None

    def bind_document(self, pdf: Any, pdf_document: Any) -> None:
        """Associe le modèle ``PDFObject`` et le document PyMuPDF pour la session courante."""
        self._pdf = pdf
        self._pdf_document = pdf_document

    def populate_treeview(
        self,
        tree: ttk.Treeview,
        marked_content_dict: MutableMapping[Any, Any],
        logical_structure: Any,
        leaves_on_page: MutableMapping[int, list],
        current_page: int,
    ) -> None:
        """Vide l'arbre, réinitialise les figures, puis reconstruit les nœuds."""
        if tree is not None:
            tree.tag_dict.clear()
            for i in tree.get_children():
                tree.delete(i)

        reset_figure_registry()
        self._pdf.marked_content_dict = marked_content_dict
        leaves_on_page.clear()
        self._build_tree(
            "",
            logical_structure,
            tree,
            tree.tag_dict,
            leaves_on_page,
            current_page,
        )

    def _build_tree(
        self,
        parent_id: str,
        logical_structure: Any,
        treeview: ttk.Treeview,
        tag_dict: Dict[str, Any],
        leaves_on_page: MutableMapping[int, list],
        current_page: int,
    ) -> None:
        """Parcourt la structure imbriquée et insère branches et feuilles dans le Treeview."""
        parent_branch = tag_dict.get(parent_id) if parent_id else None
        for element in logical_structure:
            if isinstance(element, dict):
                for key in element:
                    tag = Branch(key, parent_branch=parent_branch)

                    tid = treeview.insert(parent_id, "end", text=str(tag))
                    tag_dict[tid] = tag
                    if parent_branch:
                        parent_branch.children.append(tag)
                    if isinstance(element[key], list):
                        self._build_tree(
                            tid,
                            element[key],
                            treeview,
                            tag_dict,
                            leaves_on_page,
                            current_page,
                        )
            else:
                leaf = self._leaf_factory(
                    element, tag_dict[parent_id], leaves_on_page, current_page
                )
                leaf.props["/Page"] = element[0]

                leaf_id = treeview.insert(
                    parent_id, "end", text=str(leaf), tags=("leaf",)
                )
                treeview.tag_configure(
                    "leaf", background="gray96", font=("Helvetica", 10)
                )

                leaf.treeview_item = leaf_id

                tag_dict[leaf_id] = leaf
                if parent_branch:
                    parent_branch.children.append(leaf)

    def _leaf_factory(
        self,
        element: Any,
        parent_tag: Any,
        leaves_on_page: MutableMapping[int, list],
        current_page: int,
    ) -> Any:
        """Instancie la classe de feuille adaptée (figure, lien, formulaire, span…)."""
        props = self._pdf.marked_content_dict[element]
        element_type = props["/Type"]

        if element_type == "Figure":
            leaf = Figure(props, parent_tag)
        elif element_type == "PlacedGraphic":
            leaf = PlacedGraphic(props, parent_tag)
        elif element_type == "Link":
            props["/PageHeight"] = self._pdf_document[current_page].rect.height
            props["/Lang"] = self._pdf.metadatas["/Lang"]
            leaf = Link(props, parent_tag)
        elif element_type == "Form":
            props["/PageHeight"] = self._pdf_document[current_page].rect.height
            props["/Lang"] = self._pdf.metadatas["/Lang"]
            leaf = Form(props, parent_tag)
        else:
            leaf = Leaf(props, parent_tag)

        if "/Page" in props:
            page_number = props["/Page"]
            if page_number not in leaves_on_page:
                leaves_on_page[page_number] = []
            leaves_on_page[page_number].append(leaf)

        return leaf
