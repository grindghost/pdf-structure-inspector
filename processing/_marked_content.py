# =============================================================================
# Fichier    : _marked_content.py
# Projet     : PDF Structure Inspector
# Rôle       : Lecture du flux de contenu (pdfminer) et enrichissement des MCID.
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# =============================================================================
"""Extraction du contenu marqué page par page et post-traitement (texte, bbox)."""

import io

from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

from configs.configurations import PRINT_DEBUG

from processing.pdf_device import MarkedContentExtractor
from processing.pdf_interpret import CustomPDFInterpreter


def AssignType(marked_content_dict):
    """Attribue un type logique (Figure, PlacedGraphic, Span) à chaque entrée."""
    for key, val in marked_content_dict.items():

        if val["/Type"] == "Image":
            marked_content_dict[key]["/Type"] = "Figure"
            continue

        if val["/Tag"] == "Figure":
            marked_content_dict[key]["/Type"] = "Figure"

        elif val["/Tag"] == "PlacedGraphic":
            marked_content_dict[key]["/Type"] = "PlacedGraphic"

        else:
            marked_content_dict[key]["/Type"] = "Span"


def CreateDecodedTexts(marked_content_dict):
    """Concatène le texte des ``LTChar`` dans ``/Text`` et supprime ``/RawText``."""
    for key, val in marked_content_dict.items():

        marked_content_dict[key]["/Text"] = str(
            "".join([char.get_text() for char in val["/LTChar"]])
        )

        del marked_content_dict[key]["/RawText"]


def CreateTextBoundingBoxes(marked_content_dict):
    """Calcule ``/BboxText`` et ``/BboxChars`` (repère page, origine haut-gauche)."""
    for key, val in marked_content_dict.items():

        try:
            x0 = min(list(bbx.bbox)[0] for bbx in val["/LTChar"]) - 4
            y0 = val["/PageHeight"] - min(
                list(bbx.bbox)[1] for bbx in val["/LTChar"]
            ) + 4
            x1 = max(list(bbx.bbox)[2] for bbx in val["/LTChar"]) + 4
            y1 = val["/PageHeight"] - max(
                list(bbx.bbox)[3] for bbx in val["/LTChar"]
            ) - 4

        except Exception:
            x0 = 0.0
            y0 = 0.0
            x1 = 0.0
            y1 = 0.0

        marked_content_dict[key]["/BboxText"] = [x0, y0, x1, y1]

        marked_content_dict[key]["/BboxChars"] = [list(bb.bbox) for bb in val["/LTChar"]]

        for i in marked_content_dict[key]["/BboxChars"]:
            i[0] = i[0]
            i[1] = val["/PageHeight"] - i[1]
            i[2] = i[2]
            i[3] = val["/PageHeight"] - i[3]


def CreateImageBoundingBoxes(marked_content_dict):
    """Normalise ``/Bbox`` des images et remplit largeur / hauteur."""
    for key, val in marked_content_dict.items():

        try:
            x0 = val["/Bbox"][0]
            y0 = val["/PageHeight"] - val["/Bbox"][1]
            x1 = val["/Bbox"][2]
            y1 = val["/PageHeight"] - val["/Bbox"][3]

            width = x1 - x0
            height = y1 - y0

            marked_content_dict[key]["/Bbox"] = [x0, y0, x1, y1]
            marked_content_dict[key]["/Width"] = width
            marked_content_dict[key]["/Height"] = height

        except Exception:
            marked_content_dict[key]["/Bbox"] = []


def CreateDrawingsBoundingBoxes(marked_content_dict):
    """Agrège les ``LTRect`` en une boîte ``/BboxDrawings``."""
    for key, val in marked_content_dict.items():

        try:
            x0 = min(list(bbx.bbox)[0] for bbx in val["/LTRect"]) - 4
            y0 = val["/PageHeight"] - min(
                list(bbx.bbox)[1] for bbx in val["/LTRect"]
            ) + 4
            x1 = max(list(bbx.bbox)[2] for bbx in val["/LTRect"]) + 4
            y1 = val["/PageHeight"] - max(
                list(bbx.bbox)[3] for bbx in val["/LTRect"]
            ) - 4

        except Exception:
            x0 = 0.0
            y0 = 0.0
            x1 = 0.0
            y1 = 0.0

        width = x1 - x0
        height = y1 - y0

        marked_content_dict[key]["/BboxDrawings"] = [x0, y0, x1, y1]
        marked_content_dict[key]["/Width"] = width
        marked_content_dict[key]["/Height"] = height


def RemoveLTObj(marked_content_dict):
    """Supprime les références lourdes aux objets layout (LTChar, LTRect, etc.)."""
    for key, val in marked_content_dict.items():

        del marked_content_dict[key]["/LTChar"]

        del marked_content_dict[key]["/BboxChars"]

        del marked_content_dict[key]["/LTRect"]


def read_content_stream(pdf_file):
    """Interprète tout le fichier avec pdfminer et retourne le dictionnaire marqué."""
    rsrcmgr = PDFResourceManager()

    outfp = io.StringIO()
    device = MarkedContentExtractor(rsrcmgr, outfp, pdf_file)

    interpreter = CustomPDFInterpreter(rsrcmgr, device)

    with open(pdf_file.file_path, "rb") as fp:
        for page in PDFPage.get_pages(fp):
            interpreter.process_page(page)

    AssignType(device.marked_content_dict)

    CreateDecodedTexts(device.marked_content_dict)

    CreateTextBoundingBoxes(device.marked_content_dict)

    CreateImageBoundingBoxes(device.marked_content_dict)

    CreateDrawingsBoundingBoxes(device.marked_content_dict)

    RemoveLTObj(device.marked_content_dict)

    if PRINT_DEBUG is True:

        for key, val in device.marked_content_dict.items():
            print(key, val)
            print("------------------")
            print()
            print()

    marked_content_dict = device.marked_content_dict.copy()
    return marked_content_dict
