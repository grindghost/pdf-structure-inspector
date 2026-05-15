# =============================================================================
# Fichier    : thumbnail_strip.py
# Projet     : PDF Structure Inspector
# Rôle       : Bande latérale de miniatures avec défilement et surbrillance.
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Miniatures des pages PDF et synchronisation avec la navigation principale."""

from __future__ import annotations

from typing import Any, List, Optional

import tkinter as tk
from PIL import ImageTk

from ui.page_renderer import render_page_thumbnail_pil


class ThumbnailStrip:
    """
    Panneau de miniatures et défilement vertical.

    L'objet *hôte* (``PDFViewer``) doit exposer : ``pdf_document``, ``pages``,
    ``current_page``, ``tree``, et la méthode ``go_to_page(page_idx)``.
    """

    THUMB_WIDTH = 100

    def __init__(self, master: tk.Widget, host: Any) -> None:
        self._host = host
        self._selected_thumbnail: Optional[tk.Widget] = None
        self._thumbnail_images: List[ImageTk.PhotoImage] = []

        self.panel = tk.Frame(master, bg="white", width=114)

        self.canvas = tk.Canvas(
            self.panel,
            bg="white",
            bd=0,
            highlightthickness=0,
            relief="ridge",
            width=114,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(
            self.panel, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.frame = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window((0, 0), window=self.frame, anchor=tk.NW)

    def populate(self) -> None:
        """Reconstruit les vignettes à partir du document ouvert sur l'hôte."""
        self.frame.update_idletasks()
        self._thumbnail_images.clear()
        for widget in self.frame.winfo_children():
            widget.destroy()

        doc = self._host.pdf_document
        n_pages = self._host.pages
        fixed_w = self.THUMB_WIDTH

        for i in range(n_pages):
            ow, oh, pil_img = render_page_thumbnail_pil(doc, i, dpi=12)
            aspect = oh / ow
            fixed_h = int(fixed_w * aspect)
            pil_resized = pil_img.resize((fixed_w, fixed_h))
            img = ImageTk.PhotoImage(pil_resized)
            self._thumbnail_images.append(img)

            self.panel.config(width=fixed_w + 20)

            thumb_lbl = tk.Label(
                self.frame,
                image=img,
                borderwidth=1,
                relief="flat",
                bg="gray82",
            )
            thumb_lbl.pack(pady=(5, 0), padx=5)

            tk.Label(
                self.frame,
                text=f"Page {i + 1}",
                bg="yellow",
                font=("Helvetica", 8),
            ).pack()

            thumb_lbl.bind(
                "<Button-1>",
                lambda e, page=i, lbl=thumb_lbl: self._on_thumb_press(
                    page, lbl, clear_tree=True
                ),
            )

        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def _reset_thumb_style(self) -> None:
        """Rétablit le style visuel de la miniature précédemment sélectionnée."""
        if self._selected_thumbnail and self._selected_thumbnail.winfo_exists():
            self._selected_thumbnail.config(
                borderwidth=1, relief="flat", bg="gray82"
            )

    def _apply_thumb_style(self, thumb_label: tk.Widget) -> None:
        """Applique le style « sélectionné » à une étiquette miniature."""
        thumb_label.config(borderwidth=2, relief="solid", bg="gray12")
        self._selected_thumbnail = thumb_label

    def _on_thumb_press(
        self, page_idx: int, thumb_label: tk.Widget, clear_tree: bool
    ) -> None:
        """Clic sur une miniature : optionnellement désélectionne l'arbre puis change de page."""
        self._reset_thumb_style()
        self._apply_thumb_style(thumb_label)
        if clear_tree and len(self._host.tree.selection()) > 0:
            self._host.tree.selection_remove(self._host.tree.selection()[0])
        self._host.go_to_page(page_idx)

    def sync_thumbnail_for_page(self, page_idx: int) -> None:
        """Après ``go_to_page`` : surligne la miniature et fait défiler le panneau."""
        children = self.frame.winfo_children()
        thumb_index = page_idx * 2
        if thumb_index < len(children):
            thumb_label = children[thumb_index]
            self._reset_thumb_style()
            self._apply_thumb_style(thumb_label)
            self.scroll_into_view(page_idx)

    def highlight_current_page_only(self) -> None:
        """Met en avant la miniature de ``host.current_page`` sans rappeler ``go_to_page``."""
        children = self.frame.winfo_children()
        thumb_index = self._host.current_page * 2
        if thumb_index < len(children):
            self._reset_thumb_style()
            self._apply_thumb_style(children[thumb_index])

    def scroll_into_view(self, page_idx: int) -> None:
        """Fait défiler le canvas vertical pour garder la miniature de la page visible."""
        children = self.frame.winfo_children()
        thumb_index = page_idx * 2
        if thumb_index >= len(children):
            return
        thumb_widget = children[thumb_index]
        self.canvas.update_idletasks()
        widget_y_root = thumb_widget.winfo_rooty()
        scrollable_y_root = self.frame.winfo_rooty()
        pos = widget_y_root - scrollable_y_root
        scrollable_height = self.frame.winfo_height()
        offset = 0.1
        self.canvas.yview_moveto(pos / scrollable_height - offset)
