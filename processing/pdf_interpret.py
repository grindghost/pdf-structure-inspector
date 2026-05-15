# =============================================================================
# Fichier    : pdf_interpret.py
# Projet     : PDF Structure Inspector
# Rôle       : Interpréteur PDF personnalisé — séquences BDC/EMC et XObject.
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# Remarque   : dérivé de pdfminer.six (PDFPageInterpreter) avec extensions MCID.
# =============================================================================
"""Gestion des opérateurs PDF marqués et des XObject (formulaires, images)."""

from typing import cast

from pdfminer.pdfinterp import PDFInterpreterError, PDFPageInterpreter
from pdfminer.pdftypes import PDFStream, dict_value, list_value, stream_value
from pdfminer.psparser import LIT, PSLiteral, PSStackType, literal_name
from pdfminer.utils import MATRIX_IDENTITY, Matrix, Rect, mult_matrix

try:
    from pdfminer import settings
except ImportError:

    class _Settings:
        STRICT = False

    settings = _Settings()

LITERAL_FORM = LIT("Form")
LITERAL_IMAGE = LIT("Image")

PDFStackT = PSStackType[PDFStream]


class CustomPDFInterpreter(PDFPageInterpreter):
    """Interpréteur qui trace les blocs marqués (BDC/EMC) et enrichit les images."""

    def __init__(self, rsrcmgr, device):
        super().__init__(rsrcmgr, device)
        self.artifacts = 0

    def do_BDC(self, tag: PDFStackT, props: PDFStackT) -> None:
        """Début de contenu marqué : MCID réel ou pseudo-MCID pour artefacts."""
        if isinstance(props, dict):
            if "MCID" in props:
                self.device.in_marked_sequence = True
                self.device.current_mcid = (self.device.pageno, props["MCID"])
                self.device.mcid_stack.append(self.device.current_mcid)
                self.device.begin_tag(cast(PSLiteral, tag), props)
            else:
                self.device.in_marked_sequence = True
                self.artifacts += 1
                self.device.current_mcid = (
                    self.device.pageno,
                    f"{tag.name} {self.artifacts}",
                )
                self.device.mcid_stack.append(self.device.current_mcid)
                self.device.begin_tag(cast(PSLiteral, tag), props)

    def do_EMC(self) -> None:
        """Fin de contenu marqué : dépile la pile de MCID et notifie le device."""
        if self.device.in_marked_sequence:
            self.device.mcid_stack.pop()
            if len(self.device.mcid_stack) > 0:
                self.device.current_mcid = self.device.mcid_stack[-1]
            else:
                self.device.in_marked_sequence = False
        self.device.end_tag()

    def do_Do(self, xobjid_arg: PDFStackT) -> None:
        """Invoque l'XObject nommé (formulaire ou image) et met à jour le device."""
        xobjid = cast(str, literal_name(xobjid_arg))
        try:
            xobj = stream_value(self.xobjmap[xobjid])
        except KeyError:
            if settings.STRICT:
                raise PDFInterpreterError("Undefined xobject id: %r" % xobjid)
            return
        subtype = xobj.get("Subtype")
        if subtype is LITERAL_FORM and "BBox" in xobj:
            interpreter = self.dup()
            bbox = cast(Rect, list_value(xobj["BBox"]))
            matrix = cast(Matrix, list_value(xobj.get("Matrix", MATRIX_IDENTITY)))
            xobjres = xobj.get("Resources")
            if xobjres:
                resources = dict_value(xobjres)
            else:
                resources = self.resources.copy()

            self.device.begin_figure(xobjid, bbox, matrix)
            interpreter.render_contents(
                resources, [xobj], ctm=mult_matrix(matrix, self.ctm)
            )
            self.device.end_figure(xobjid)
        elif subtype is LITERAL_IMAGE and "Width" in xobj and "Height" in xobj:
            self.device.begin_figure(xobjid, (0, 0, 1, 1), MATRIX_IDENTITY)
            self.device.render_image(xobjid, xobj)

            if self.device.in_marked_sequence:
                self.device.marked_content_dict[self.device.current_mcid][
                    "/Type"
                ] = "Image"
                self.device.marked_content_dict[self.device.current_mcid][
                    "/XObj"
                ] = True
            self.device.end_figure(xobjid)
        return
