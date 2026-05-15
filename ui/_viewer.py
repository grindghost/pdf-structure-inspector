# =============================================================================
# Fichier    : _viewer.py
# Projet     : PDF Structure Inspector
# Rôle       : Fenêtre principale Tkinter — arbre, canvas PDF, miniatures.
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Visualiseur : composition des modules page, miniatures et présentateur d'arbre."""

import tkinter as tk

import fitz

from configs.configurations import DEFAULT_APP_TITLE

from models.branch import Branch
from models.bounding_boxes import BoundingBox

from ui.page_renderer import page_pixmap_size, render_page_to_photoimage
from ui.structure_presenter import StructurePresenter, flatten_branch
from ui.thumbnail_strip import ThumbnailStrip
from ui.widgets.struture_tree_view import StructureTreeview
from ui.widgets.paned_window import PanedWindow


class Store:
    """Utilitaire de débogage : affiche l'état courant (sélection, page)."""

    def __init__(self, ui):
        self.ui = ui

    def update(self) -> None:
        """Imprime la sélection du Treeview et la page active dans la console."""
        print()
        print("*************")
        print("🥊 APP. STATES:")

        selected_item = self.ui.tree.selection()[0]
        print("   ▢ Treeview selected item:", selected_item)
        print(
            "   ▢ Tag name of the parent:",
            self.ui.tree.tag_dict[selected_item],
        )
        print("   ▢ Current page:", self.ui.current_page)
        print("*************")
        print()


class PDFViewer(tk.Tk):
    """Fenêtre racine : document PyMuPDF, surlignage et navigation."""

    def __init__(self, parent):
        tk.Tk.__init__(self)

        self.resizable(False, False)

        self.store = Store(self)

        self.pdf = None
        self.pdf_document = None
        self.parent = parent

        self.title(DEFAULT_APP_TITLE)

        self.thumbnail_visible = False

        self.bounding_boxes = []

        self.leaves_on_page = {}

        self._structure = StructurePresenter()

        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_frame, width=140, bg="gray92")
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.sidebar = tk.Frame(left_frame, width=50, bg="gray92")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(0)

        self.toggle_thumbnails_button = tk.Button(
            self.sidebar,
            text="☰",
            command=self.toggle_thumbnail_panel,
            state=tk.DISABLED,
        )
        self.toggle_thumbnails_button.pack(padx=10, pady=10)

        self.paned_window = PanedWindow(
            main_frame, orient=tk.HORIZONTAL, borderwidth=0, showhandle=True
        )
        self.paned_window.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        treeview_frame = tk.Frame(self.paned_window, width=200)
        treeview_frame.pack_propagate(0)
        self.paned_window.add(treeview_frame)
        self.paned_window.paneconfig(treeview_frame, minsize=50)

        self.tree = StructureTreeview(
            treeview_frame, show="tree", padding=(15, 10, 1, 15)
        )
        self.tree.column("# 0", anchor=tk.CENTER, stretch=tk.YES, width=10)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.pack_propagate(0)

        treeview_scrollbar = tk.Scrollbar(
            treeview_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        treeview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        self.tree.configure(yscrollcommand=treeview_scrollbar.set)

        self.canvas = tk.Canvas(self.paned_window, bg="gray70", bd=5)
        self.paned_window.add(self.canvas)

        self.thumbs = ThumbnailStrip(left_frame, self)
        self.thumbs.panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.thumbs.panel.pack_forget()

        self.tree.bind("<<TreeviewSelect>>", self.on_treeview_selection)

        self.bind("<Command-o>", lambda evt=None: self.parent.open_file())
        self.bind("<Command-O>", lambda evt=None: self.parent.open_file())

        self.footer = tk.Frame(self, bg="lightgray", height=0)
        self.footer.pack(side="bottom", fill="x")

        self.center_window()

    def on_sash_move(self, event) -> None:
        """Recalcule la taille de la fenêtre lorsque le séparateur panneau est déplacé."""
        self.update_window_size()

    def toggle_thumbnail_panel(self) -> None:
        """Affiche ou masque la colonne de miniatures et ajuste la géométrie."""
        if self.thumbnail_visible:
            self.thumbs.panel.pack_forget()
            self.thumbnail_visible = False
        else:
            self.thumbs.panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.thumbs.populate()
            self.thumbs.highlight_current_page_only()
            self.thumbnail_visible = True

        self.update_idletasks()
        self.update_window_size()

    def update_window_size(self) -> None:
        """Adapte la largeur / hauteur de la fenêtre au contenu (arbre + page + bande)."""
        if self.pdf_document is None:
            return
        pw, ph = page_pixmap_size(self.pdf_document, self.current_page, dpi=72)

        total_width = self.tree.winfo_width() + pw + 75
        if self.thumbnail_visible:
            total_width += self.thumbs.panel.winfo_width()

        total_height = ph
        footer_height = self.footer.winfo_height() if self.footer.winfo_ismapped() else 0
        total_height += footer_height

        self.geometry(f"{total_width}x{total_height}")

    def populate_treeview(self, marked_content_dict, logical_structure) -> None:
        """Délègue au présentateur le remplissage du Treeview et ``leaves_on_page``."""
        self._structure.populate_treeview(
            self.tree,
            marked_content_dict,
            logical_structure,
            self.leaves_on_page,
            self.current_page,
        )

    def open_document(self, pdf_object) -> None:
        """Ouvre le PDF avec PyMuPDF, configure le titre et prépare miniatures + arbre."""
        self.pdf = pdf_object

        self.pdf_document = fitz.open(self.pdf.file_path)
        self.pdf_document.zoom = 2
        self.current_page = 0
        self.pages = self.pdf_document.page_count

        self.pdf.zoom = 2
        self.pdf.pages_count = self.pages

        self._structure.bind_document(self.pdf, self.pdf_document)

        if self.pdf.metadatas.get("Title", None) is not None:
            if isinstance(self.pdf.metadatas["Title"], bytes):
                title = self.pdf.metadatas["Title"].decode("latin-1")
            else:
                title = str(self.pdf.metadatas["Title"])

            self.title(title)
        else:
            self.title("Untitled document")

        self.parent.button.pack_forget()
        self.after(500, lambda: self.display_pdf(center=True))

        self.toggle_thumbnails_button.config(state=tk.NORMAL)

        self.tree.bind("<Configure>", self.on_sash_move)

        self.leaves_on_page = {}

        self.thumbs.populate()

    def display_pdf(self, center=False) -> None:
        """Affiche la page courante, redimensionne la fenêtre et trace les boîtes si besoin."""
        try:
            self.bounding_boxes = []

            w, h, img = render_page_to_photoimage(
                self.pdf_document, self.current_page, dpi=72
            )

            self.canvas.config(width=w, height=h)

            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.img = img

            total_width = w + self.tree.winfo_width() + 50
            total_height = h
            self.geometry(f"{total_width}x{total_height}")

            if center:
                self.center_window()

            if len(self.tree.selection()) == 0:
                for leaf in self.leaves_on_page.get(self.current_page, []):
                    bbox = leaf.bbox
                    bounding_box = BoundingBox(
                        self.canvas, bbox, leaf.treeview_item, self
                    )
                    bounding_box.draw()
                    self.bounding_boxes.append(bounding_box)

            self.update_window_size()

        except RuntimeError as e:
            print(f"Error loading PDF page: {e}")

    def highlight_items(self, leafs_list) -> None:
        """Surligne les feuilles de la page courante (y compris bbox de dessin si utile)."""
        self.canvas.delete("bounding_boxes")

        self.bounding_boxes = []

        for leaf in leafs_list:
            if leaf.props["/Page"] == self.current_page:
                bbox = leaf.bbox

                bounding_box = BoundingBox(
                    self.canvas, bbox, leaf.treeview_item, self
                )
                bounding_box.draw()

                self.bounding_boxes.append(bounding_box)

                if leaf.props.get("/BboxDrawings", None) is not None:
                    if leaf.props["/Type"] != "Span":
                        drawings_bbox = leaf.props["/BboxDrawings"]
                        drawing_box = BoundingBox(
                            self.canvas, drawings_bbox, leaf.treeview_item, self
                        )
                        drawing_box.draw()
                        self.bounding_boxes.append(drawing_box)

    def on_treeview_selection(self, event) -> None:
        """Réagit à la sélection dans l'arbre : page, miniature et rectangles."""
        if len(self.tree.selection()) == 0:
            return

        selected_item = self.tree.selection()[0]
        item = self.tree.tag_dict[selected_item]
        if isinstance(item, Branch):
            flat_list = flatten_branch(item)
        else:
            flat_list = [item]

        leafs_list = []
        for el in flat_list:
            if not isinstance(el, Branch):
                leafs_list.append(el)

        if leafs_list:
            page_number = leafs_list[0].props["/Page"]
            self.go_to_page(page_number)

            self.thumbs.sync_thumbnail_for_page(page_number)

            self.highlight_items(leafs_list)

    def center_window(self) -> None:
        """Centre la fenêtre sur l'écran (après calcul de sa taille)."""
        self.update()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

    def go_to_page(self, page_idx) -> None:
        """Change l'indice de page affichée et rafraîchit le canvas."""
        self.current_page = page_idx
        self.display_pdf()
