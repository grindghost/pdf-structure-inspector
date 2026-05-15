# =============================================================================
# Fichier    : _pdf_structtreeroot.py
# Projet     : PDF Structure Inspector
# Rôle       : Parcours PyPDF2 du StructTreeRoot et liste imbriquée pour l'UI.
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Reconstruction de l'arbre logique et enrichissement du dictionnaire marqué."""

import uuid
from dataclasses import dataclass
from typing import Any, List, Mapping, MutableMapping, Optional, Tuple, Union

import PyPDF2


@dataclass(frozen=True)
class StructureTreeRebuildContext:
    """Contexte d'une passe de parcours (pages + RoleMap), sans variable globale."""

    pages_ref_dict: Mapping[Any, Any]
    role_map_dict: Mapping[Any, Any]


def reverse_coordinates(page_height, coords):
    """Convertit une bbox PDF (origine bas-gauche) en repère haut-gauche pour l'affichage."""
    top_y = page_height - float(coords[3])
    bottom_y = page_height - float(coords[1])
    new_bbox = coords.copy()
    new_bbox[1] = top_y
    new_bbox[3] = bottom_y
    return new_bbox


def get_page_index(
    element, ctx: StructureTreeRebuildContext
) -> Optional[Union[int, Tuple[Any, Tuple]]]:
    """Résout l'indice de page et les dimensions à partir de ``/Pg`` ou des enfants ``/K``."""
    pages_ref_dict = ctx.pages_ref_dict

    page_object = element.get("/Pg", None)
    kids = element.get("/K", None)

    if page_object:
        struct_parent = page_object.get_object()["/StructParents"]
        page_idx = pages_ref_dict[struct_parent]["page"]
        page_dimension = (
            pages_ref_dict[struct_parent]["width"],
            pages_ref_dict[struct_parent]["height"],
        )
        return (page_idx, page_dimension)

    if kids:
        if isinstance(kids, list):
            for k in kids:
                if k.get_object().get("/Pg", None) is not None:
                    struct_parent = k.get_object()["/Pg"].get_object()[
                        "/StructParents"
                    ]
                    page_idx = pages_ref_dict[struct_parent]["page"]
                    page_dimension = (
                        pages_ref_dict[struct_parent]["width"],
                        pages_ref_dict[struct_parent]["height"],
                    )
                    return (page_idx, page_dimension)

        elif isinstance(kids, PyPDF2.generic.IndirectObject):
            if kids.get_object().get("/Pg", None) is not None:
                struct_parent = kids.get_object()["/Pg"].get_object()[
                    "/StructParents"
                ]
                page_idx = pages_ref_dict[struct_parent]["page"]
                page_dimension = (
                    pages_ref_dict[struct_parent]["width"],
                    pages_ref_dict[struct_parent]["height"],
                )
                return (page_idx, page_dimension)
            return None

        elif isinstance(kids, dict):
            if kids.get_object().get("/Pg", None) is not None:
                try:
                    struct_parent = kids.get_object()["/Pg"].get_object()[
                        "/StructParents"
                    ]
                    page_idx = pages_ref_dict[struct_parent]["page"]
                    page_dimension = (
                        pages_ref_dict[struct_parent]["width"],
                        pages_ref_dict[struct_parent]["height"],
                    )
                    return (page_idx, page_dimension)
                except (KeyError, AttributeError, TypeError):
                    return 0
            return None
        return None

    return None


def traverse_tree(
    element,
    marked_content_dict: MutableMapping[Any, Any],
    ctx: StructureTreeRebuildContext,
) -> List[Any]:
    """Parcourt récursivement ``/K`` et construit la liste imbriquée balise → MCID."""
    children = element.get("/K")
    if children is None:
        return []

    if isinstance(children, PyPDF2.generic.NumberObject):
        page_idx = get_page_index(element, ctx)
        return [(page_idx[0], children)]

    if isinstance(children, PyPDF2.generic.IndirectObject):
        children = [children]

    items: List[Any] = []
    form_stack: List[Any] = []

    for child in children:
        child_obj = child.get_object()

        if isinstance(child_obj, PyPDF2.generic.NumberObject):
            page_idx = get_page_index(element, ctx)
            items.append((page_idx[0], child_obj))

        elif isinstance(child_obj, dict):
            tag = child_obj.get("/S", "")

            mapped = ctx.role_map_dict.get(tag)
            if mapped is not None:
                tag = mapped

            if tag == "/Form":
                mcid = f"form_{uuid.uuid4()}"
                page_idx = get_page_index(child_obj, ctx)
                mcid_tuple = (page_idx[0], mcid)

                form_properties = child_obj["/K"]["/Obj"].get_object()

                rect = form_properties.get("/Rect", [])
                field_name = str(form_properties.get("/T", mcid))

                marked_content_dict[mcid_tuple] = dict(form_properties)
                marked_content_dict[mcid_tuple]["/MCID"] = mcid
                marked_content_dict[mcid_tuple]["/Name"] = f"{field_name} - OBJR"
                marked_content_dict[mcid_tuple]["/Rect"] = rect
                marked_content_dict[mcid_tuple]["/Type"] = "Form"
                marked_content_dict[mcid_tuple]["/PageHeight"] = page_idx[1][1]

                form = mcid_tuple
                form_stack.append(form)

            if tag == "/Figure":
                mcid = child_obj.get("/K", "")

                if isinstance(mcid, list):
                    mcid = mcid[0]
                else:
                    if not isinstance(mcid, int):
                        if mcid.get("/MCID", None) is not None:
                            mcid = mcid.get("/MCID", None)

                page_idx = get_page_index(child_obj, ctx)
                mcid_tuple = (page_idx[0], mcid)

                if child_obj.get("/A", None) is not None:
                    coords = child_obj["/A"]["/BBox"]
                    page_height = float(page_idx[1][1])
                    bbox = reverse_coordinates(page_height, coords)
                else:
                    bbox = [0.0, 0.0, 0.0, 0.0]

                alt = child_obj.get("/Alt", "")

                marked_content_dict[mcid_tuple]["/BboxLogicalTree"] = bbox
                marked_content_dict[mcid_tuple]["/AltText"] = alt

            if tag == "/Link":
                mcid = f"linkobjr_{uuid.uuid4()}"

                page_idx = get_page_index(child_obj, ctx)
                mcid_tuple = (page_idx[0], mcid)

                try:
                    rect = (
                        child_obj.get("/K", "")[0]
                        .get_object()["/Obj"]
                        .get_object()["/Rect"]
                    )
                except (KeyError, IndexError, AttributeError, TypeError):
                    rect = [0.0, 0.0, 0.0, 0.0]

                try:
                    action = (
                        child_obj.get("/K", "")[0]
                        .get_object()["/Obj"]
                        .get_object()["/A"]
                    )
                except (KeyError, IndexError, AttributeError, TypeError):
                    action = {}

                marked_content_dict[mcid_tuple] = dict(child_obj)
                marked_content_dict[mcid_tuple]["/MCID"] = mcid
                marked_content_dict[mcid_tuple]["/Tag"] = "Link"
                marked_content_dict[mcid_tuple]["/Name"] = "Link - OBJR"
                marked_content_dict[mcid_tuple]["/Type"] = "Link"
                marked_content_dict[mcid_tuple]["/Rect"] = rect
                marked_content_dict[mcid_tuple]["/Action"] = action

                marked_content_dict[mcid_tuple]["/PageHeight"] = page_idx[1][1]

                link = (page_idx[0], mcid)
                link_objr = child_obj.get("/K")

                if isinstance(link_objr, list) and link_objr:
                    link_objr.pop(0)
                tag_items = [link] + traverse_tree(
                    child_obj, marked_content_dict, ctx
                )

            else:
                tag_items = traverse_tree(child_obj, marked_content_dict, ctx)

            if tag == "/Form":
                items.append({tag: [form_stack.pop(-1)]})
            else:
                items.append({tag: tag_items})

    return items


def reconstruct_tree(pdf_file, marked_content_dict):
    """Point d'entrée : installe le contexte et lance le parcours depuis la racine."""
    ctx = StructureTreeRebuildContext(
        pages_ref_dict=pdf_file.pages_ref_dict,
        role_map_dict=pdf_file.role_map_dict,
    )
    return traverse_tree(pdf_file.struct_tree_root_obj, marked_content_dict, ctx)
