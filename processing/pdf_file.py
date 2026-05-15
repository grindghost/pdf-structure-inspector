# =============================================================================
# Fichier    : pdf_file.py
# Projet     : PDF Structure Inspector
# Rôle       : Chargement PyPDF2 / pdfminer — métadonnées, StructTreeRoot, pages.
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Modèle « document ouvert » : racine de structure, pages et RoleMap."""

import pprint

import PyPDF2
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser

from configs.configurations import PRINT_DEBUG


class PDFObject:
    """Regroupe les objets PDF utiles à l'inspection (balisage, pages, rôles)."""

    def __init__(self, file_path=None, *args, **kwargs):
        print("New PDF object instantiated.")

        self.tagged = False

        self.file_path = file_path
        self.pdf_reader = PyPDF2.PdfReader(self.file_path, strict=False)
        self.metadatas = self.get_metadatas(self.file_path)

        self.struct_tree_root_obj = self.get_root(self.pdf_reader)

        self.pages_ref_dict = self.get_pages_references(
            self.pdf_reader, self.struct_tree_root_obj
        )

        self.role_map_dict = self.get_role_map(
            self.pdf_reader, self.struct_tree_root_obj
        )

        self.marked_content_dict = {}

        self.logical_structure = {}

    def get_metadatas(self, file_path):
        """Lit les métadonnées du catalogue (pdfminer) et complète ``/Lang``."""
        with open(file_path, "rb") as file:
            parser = PDFParser(file)
            doc = PDFDocument(parser)
            metadata = doc.info[0]

            if "/Lang" in metadata:
                metadata["/Lang"] = metadata["/Lang"]
            else:
                if "Lang" in doc.catalog:
                    lang = doc.catalog["Lang"]
                    metadata["/Lang"] = lang
                else:
                    metadata["/Lang"] = None

            print("Metadatas:")
            print("----------------------------")
            pp = pprint.PrettyPrinter(indent=2)
            pp.pprint(metadata)
            print()

        return metadata

    def get_root(self, pdf_reader):
        """Retourne l'objet ``/StructTreeRoot`` résolu ou ``{}`` si le PDF n'est pas balisé."""
        catalog = pdf_reader.trailer["/Root"].get_object()

        struct_tree_root = catalog.get("/StructTreeRoot", None)

        if struct_tree_root is not None:
            self.tagged = True

            struct_tree_root_obj = struct_tree_root.get_object()

            print("StructTreeRoot:")
            print("----------------------------")
            pp = pprint.PrettyPrinter(indent=2)
            pp.pprint(struct_tree_root_obj)
            print()

            return struct_tree_root_obj

        self.tagged = False
        return {}

    def get_pages_references(self, pdf_reader, struct_tree_root_obj):
        """Associe chaque ``/StructParents`` de page à l'indice de page et aux dimensions."""
        if self.tagged is False:
            return {}

        pages_ref_dict = {}

        parent_tree = struct_tree_root_obj.get("/ParentTree", None)

        if parent_tree:
            parent_tree = parent_tree.get_object()
        else:
            return {}

        for i in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[i]

            width = page.mediabox[2]
            height = page.mediabox[3]

            struct_parents_id = page.get("/StructParents")

            if struct_parents_id is not None and parent_tree:
                pages_ref_dict[struct_parents_id] = {
                    "page": i,
                    "width": width,
                    "height": height,
                }
        print("Pages StructParend ID, and dimensions:")
        print("----------------------------")
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint(pages_ref_dict)
        print()

        return pages_ref_dict

    def get_role_map(self, pdf_reader, struct_tree_root_obj):
        """Retourne le dictionnaire ``/RoleMap`` ou ``{}`` s'il est absent."""
        if self.tagged is False:
            return {}

        role_map = struct_tree_root_obj.get("/RoleMap", None)

        if role_map:
            role_map_dict = role_map.get_object()

            print("Role mapping:")
            print("----------------------------")
            pp = pprint.PrettyPrinter(indent=2)
            pp.pprint(role_map_dict)
            print()
            return role_map_dict

        print("No role mapping:")
        print("----------------------------")
        pp = pprint.PrettyPrinter(indent=2)
        pp.pprint({})
        print()

        return {}
