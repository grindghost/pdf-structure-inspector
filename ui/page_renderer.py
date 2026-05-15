# =============================================================================
# Fichier    : page_renderer.py
# Projet     : PDF Structure Inspector
# Rôle       : Conversion PyMuPDF → tailles et images pour Tkinter (Pillow).
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Rendu des pages PDF en pixmaps puis PhotoImage / PIL (sans logique de fenêtre)."""

from __future__ import annotations

from typing import Tuple

import fitz
from PIL import Image, ImageTk


def page_pixmap_size(doc: fitz.Document, page_index: int, dpi: int = 72) -> Tuple[int, int]:
    """Retourne la largeur et la hauteur en pixels d'une page au DPI demandé."""
    page = doc.load_page(page_index)
    pm = page.get_pixmap(alpha=False, dpi=dpi)
    return pm.width, pm.height


def render_page_to_photoimage(
    doc: fitz.Document, page_index: int, dpi: int = 72
) -> Tuple[int, int, ImageTk.PhotoImage]:
    """
    Rend une page en ``PhotoImage``.

    L'appelant doit conserver une référence à l'image (attribut sur le widget)
    pour éviter le ramasse-miettes Tkinter.

    Retourne ``(largeur, hauteur, image)``.
    """
    page = doc.load_page(page_index)
    pm = page.get_pixmap(alpha=False, dpi=dpi)
    w, h = pm.width, pm.height
    img = ImageTk.PhotoImage(Image.frombytes("RGB", [w, h], pm.samples))
    return w, h, img


def render_page_thumbnail_pil(
    doc: fitz.Document, page_index: int, dpi: int = 12
) -> Tuple[int, int, Image.Image]:
    """Produit une image PIL basse définition pour la bande de miniatures."""
    page = doc.load_page(page_index)
    pm = page.get_pixmap(alpha=False, dpi=dpi)
    w, h = pm.width, pm.height
    pil_image = Image.frombytes("RGB", [w, h], pm.samples)
    return w, h, pil_image
