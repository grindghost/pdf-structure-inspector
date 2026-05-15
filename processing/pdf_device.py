# =============================================================================
# Fichier    : pdf_device.py
# Projet     : PDF Structure Inspector
# Rôle       : Device pdfminer — capture du contenu marqué (MCID, LTChar, etc.).
# Auteur(s)  : les contributeurs du dépôt (voir README.md et historique Git).
# Licence    : MIT — voir le fichier LICENSE à la racine du projet.
# Remarque   : largement dérivé de pdfminer.six (PDFTextDevice / PDFDevice).
# =============================================================================
"""Implémentation des callbacks graphiques pdfminer vers le dictionnaire marqué."""

import io
import logging
import re
from typing import (
    BinaryIO,
    Iterable,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    TextIO,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from pdfminer.pdfcolor import PDFColorSpace

from pdfminer.psparser import PSLiteral
from pdfminer.pdffont import PDFCIDFont, PDFType1Font

from pdfminer import utils
from pdfminer.image import ImageWriter
from pdfminer.layout import LAParams, LTComponent, TextGroupElement
from pdfminer.layout import LTAnno
from pdfminer.layout import LTChar
from pdfminer.layout import LTContainer
from pdfminer.layout import LTCurve
from pdfminer.layout import LTFigure
from pdfminer.layout import LTImage
from pdfminer.layout import LTItem
from pdfminer.layout import LTLayoutContainer
from pdfminer.layout import LTLine
from pdfminer.layout import LTPage
from pdfminer.layout import LTRect
from pdfminer.layout import LTText
from pdfminer.layout import LTTextBox
from pdfminer.layout import LTTextBoxVertical
from pdfminer.layout import LTTextGroup
from pdfminer.layout import LTTextLine
from pdfminer.pdfdevice import PDFTextDevice, PDFDevice
from pdfminer.pdffont import PDFFont
from pdfminer.pdffont import PDFUnicodeNotDefined
from pdfminer.pdfinterp import PDFGraphicState, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import PDFStream
from pdfminer.utils import AnyIO, Point, Matrix, Rect, PathSegment, make_compat_str
from pdfminer.utils import apply_matrix_pt
from pdfminer.utils import bbox2str
from pdfminer.utils import enc
from pdfminer.utils import mult_matrix

PDFTextSeq = Iterable[Union[int, float, bytes]]


log = logging.getLogger(__name__)

marked_sequence = {
    "/MCID": str,
    "/Tag": str,
    "/Type": str,
    "/Lang": str,
    "/Page": int,
    "/PageHeight": 0,
    "/Name": str,
    "/Height": None,
    "/Width": None,
    "/AltText": str,
    "/Bbox": [],
    "/RawText": str,  # ...
    "/LTChar": [],  # ...
    "/LTRect": []
}


class MarkedContentExtractor(PDFDevice):
    """Device de rendu qui alimente ``marked_content_dict`` pour chaque MCID actif."""

    cur_item: LTLayoutContainer

    def __init__(
            self, rsrcmgr: "PDFResourceManager", outfp: BinaryIO, pdf_file: None, codec: str = "utf-8"
    ) -> None:
        PDFDevice.__init__(self, rsrcmgr)

        self.metadatas = pdf_file.metadatas

        self.outfp = outfp
        self.codec = codec
        self.pageno = 0

        self.current_mcid = None
        self.in_marked_sequence = False
        self.mcid_stack = []

        self.marked_content_dict = {}

    # Original render_image
    def render_image(self, name: str, stream: PDFStream) -> None:
        assert isinstance(self.cur_item, LTFigure), str(type(self.cur_item))
        item = LTImage(
            name,
            stream,
            (self.cur_item.x0, self.cur_item.y0,
             self.cur_item.x1, self.cur_item.y1),
        )
        self.cur_item.add(item)

        # if self.in_marked_sequence:
        #     if 'Artifact' not in str(self.current_mcid[1]):
        #         print(self.current_mcid, item.bbox)

    def _render_image(self, name, stream):
        if self.in_marked_sequence:

            # Get the current transformation matrix
            ctm = self.ctm

            # The width and height of the image
            width = stream.get('Width')
            height = stream.get('Height')

            self.marked_content_dict[self.current_mcid]["/Name"] = name
            self.marked_content_dict[self.current_mcid]["/Height"] = height
            self.marked_content_dict[self.current_mcid]["/Width"] = width

    def render_string(
            self,
            textstate: "PDFTextState",
            seq: PDFTextSeq,
            ncs: PDFColorSpace,
            graphicstate: "PDFGraphicState",
    ) -> None:

        assert self.ctm is not None
        matrix = utils.mult_matrix(textstate.matrix, self.ctm)
        font = textstate.font
        fontsize = textstate.fontsize
        scaling = textstate.scaling * 0.01
        charspace = textstate.charspace * scaling
        wordspace = textstate.wordspace * scaling
        rise = textstate.rise
        assert font is not None

        # Get the decoded corresponding text
        text = ""
        for obj in seq:
            if isinstance(obj, str):
                obj = utils.make_compat_bytes(obj)
            if not isinstance(obj, bytes):
                continue
            chars = font.decode(obj)

            for cid in chars:
                try:
                    char = font.to_unichr(cid)
                    text += char

                    if self.current_mcid not in self.marked_content_dict:
                        self.marked_content_dict[self.current_mcid] = marked_sequence.copy(
                        )
                        self.marked_content_dict[self.current_mcid]['/RawText'] = utils.enc(
                            text)
                    else:
                        self.marked_content_dict[self.current_mcid]['/RawText'] += utils.enc(
                            char)
                        # self.marked_content_dict[self.current_mcid]['/RawText'] = utils.enc(text)

                except PDFUnicodeNotDefined:
                    pass

        # Adjust the line matrix
        if font.is_multibyte():
            wordspace = 0
        dxscale = 0.001 * fontsize * scaling
        if font.is_vertical():
            textstate.linematrix = self.render_string_vertical(
                seq,
                matrix,
                textstate.linematrix,
                font,
                fontsize,
                scaling,
                charspace,
                wordspace,
                rise,
                dxscale,
                ncs,
                graphicstate,
            )
        else:
            textstate.linematrix = self.render_string_horizontal(
                seq,
                matrix,
                textstate.linematrix,
                font,
                fontsize,
                scaling,
                charspace,
                wordspace,
                rise,
                dxscale,
                ncs,
                graphicstate,
            )

    def render_string_horizontal(
            self,
            seq: PDFTextSeq,
            matrix: Matrix,
            pos: Point,
            font: PDFFont,
            fontsize: float,
            scaling: float,
            charspace: float,
            wordspace: float,
            rise: float,
            dxscale: float,
            ncs: PDFColorSpace,
            graphicstate: "PDFGraphicState",
    ) -> Point:
        (x, y) = pos
        needcharspace = False
        for obj in seq:
            if isinstance(obj, (int, float)):
                x -= obj * dxscale
                needcharspace = True
            else:
                for cid in font.decode(obj):
                    if needcharspace:
                        x += charspace
                    x += self.render_char(
                        utils.translate_matrix(matrix, (x, y)),
                        font,
                        fontsize,
                        scaling,
                        rise,
                        cid,
                        ncs,
                        graphicstate,
                    )
                    if cid == 32 and wordspace:
                        x += wordspace
                    needcharspace = True
        return (x, y)

    def render_char(
            self,
            matrix: Matrix,
            font: PDFFont,
            fontsize: float,
            scaling: float,
            rise: float,
            cid: int,
            ncs: PDFColorSpace,
            graphicstate: PDFGraphicState,
    ) -> float:
        try:
            text = font.to_unichr(cid)
            assert isinstance(text, str), str(type(text))
        except PDFUnicodeNotDefined:
            text = self.handle_undefined_char(font, cid)
        textwidth = font.char_width(cid)
        textdisp = font.char_disp(cid)
        item = LTChar(
            matrix,
            font,
            fontsize,
            scaling,
            rise,
            text,
            textwidth,
            textdisp,
            ncs,
            graphicstate,
        )
        if self.in_marked_sequence:
            self.marked_content_dict[self.current_mcid]['/LTChar'].append(item)
        return item.adv

    def begin_page(self, page: PDFPage, ctm: Matrix) -> None:

        # Get the page height for convenience
        self.page_height = page.mediabox[3]
        return

    def end_page(self, page: PDFPage) -> None:

        # Increment the page number
        self.pageno += 1

        # Reset the mcid to None
        self.current_mcid = None
        return

    def begin_tag(self, tag: PSLiteral, props: Optional["PDFStackT"] = None) -> None:

        # It's probable, that the properties get overriden here,
        # if the same MCID are used across multiple pages.

        _mcid = self.current_mcid[1]
        _tag = tag.name
        _text = ""  # Will override previous content if MCID already exists...

        if props != None:
            _lang = props.get('Lang', self.metadatas['/Lang'])
            if _lang is not None:
                _lang = _lang.decode('utf-8')
        else:
            _lang = self.metadatas['/Lang']

        # Will override previous content if MCID already exists...
        _ltchars = []

        _page = self.pageno
        _pageheight = self.page_height

        self.marked_content_dict[self.current_mcid] = {
            "/MCID": _mcid,
            "/Tag": _tag,
            "/Type": None,
            "/Lang": _lang,
            "/Page": _page,
            "/PageHeight": _pageheight,
            "/Name": "",
            "/Height": None,
            "/Width": None,
            "/AltText": "",
            "/Bbox": [],
            "/RawText": _text,
            "/LTChar": _ltchars,
            "/LTRect": []
        }

        return

    def end_tag(self) -> None:
        return

    def do_tag(self, tag: PSLiteral, props: Optional["PDFStackT"] = None) -> None:
        self.begin_tag(tag, props)
        return

    def paint_path(
        self,
        gstate: PDFGraphicState,
        stroke: bool,
        fill: bool,
        evenodd: bool,
        path: Sequence[PathSegment],
    ) -> None:
        if self.in_marked_sequence:
            self.marked_content_dict[self.current_mcid]['/Type'] = '✅ VECTOR'

        """Paint paths described in section 4.4 of the PDF reference manual"""
        shape = "".join(x[0] for x in path)

        if shape[:1] != "m":
            # Per PDF Reference Section 4.4.1, "path construction operators may
            # be invoked in any sequence, but the first one invoked must be m
            # or re to begin a new subpath." Since pdfminer.six already
            # converts all `re` (rectangle) operators to their equivelent
            # `mlllh` representation, paths ingested by `.paint_path(...)` that
            # do not begin with the `m` operator are invalid.
            pass

        elif shape.count("m") > 1:
            # recurse if there are multiple m's in this shape
            for m in re.finditer(r"m[^m]+", shape):
                subpath = path[m.start(0): m.end(0)]
                self.paint_path(gstate, stroke, fill, evenodd, subpath)

        else:
            # Although the 'h' command does not not literally provide a
            # point-position, its position is (by definition) equal to the
            # subpath's starting point.
            #
            # And, per Section 4.4's Table 4.9, all other path commands place
            # their point-position in their final two arguments. (Any preceding
            # arguments represent control points on Bézier curves.)
            raw_pts = [
                cast(Point, p[-2:] if p[0] != "h" else path[0][-2:]) for p in path
            ]
            pts = [apply_matrix_pt(self.ctm, pt) for pt in raw_pts]

            if shape in {"mlh", "ml"}:
                # single line segment
                #
                # Note: 'ml', in conditional above, is a frequent anomaly
                # that we want to support.
                line = LTLine(
                    gstate.linewidth,
                    pts[0],
                    pts[1],
                    stroke,
                    fill,
                    evenodd,
                    gstate.scolor,
                    gstate.ncolor,
                )
                if self.in_marked_sequence:
                    self.marked_content_dict[self.current_mcid]["/LTRect"].append(
                        line)
                    self.marked_content_dict[self.current_mcid]["/Name"] += "Path"
                # self.cur_item.add(line)

            elif shape in {"mlllh", "mllll"}:
                (x0, y0), (x1, y1), (x2, y2), (x3, y3), _ = pts

                is_closed_loop = pts[0] == pts[4]
                has_square_coordinates = (
                    x0 == x1 and y1 == y2 and x2 == x3 and y3 == y0
                ) or (y0 == y1 and x1 == x2 and y2 == y3 and x3 == x0)
                if is_closed_loop and has_square_coordinates:
                    rect = LTRect(
                        gstate.linewidth,
                        (*pts[0], *pts[2]),
                        stroke,
                        fill,
                        evenodd,
                        gstate.scolor,
                        gstate.ncolor,
                    )
                    if self.in_marked_sequence:
                        self.marked_content_dict[self.current_mcid]["/LTRect"].append(
                            rect)
                        self.marked_content_dict[self.current_mcid]["/Name"] += "Path"
                    # self.cur_item.add(rect)
                else:
                    curve = LTCurve(
                        gstate.linewidth,
                        pts,
                        stroke,
                        fill,
                        evenodd,
                        gstate.scolor,
                        gstate.ncolor,
                    )
                    if self.in_marked_sequence:
                        self.marked_content_dict[self.current_mcid]["/LTRect"].append(
                            curve)
                        self.marked_content_dict[self.current_mcid]["/Name"] += "Path"
                    # self.cur_item.add(curve)

            else:
                curve = LTCurve(
                    gstate.linewidth,
                    pts,
                    stroke,
                    fill,
                    evenodd,
                    gstate.scolor,
                    gstate.ncolor,
                )
                if self.in_marked_sequence:
                    self.marked_content_dict[self.current_mcid]["/LTRect"].append(
                        curve)
                    self.marked_content_dict[self.current_mcid]["/Name"] += "Path"
                # self.cur_item.add(curve)

    def begin_figure(self, name: str, bbox: Rect, matrix: Matrix) -> None:

        if self.in_marked_sequence:
            img = LTFigure(name, bbox, mult_matrix(matrix, self.ctm))
            self.marked_content_dict[self.current_mcid]['/Bbox'] = list(
                img.bbox)

            # ✅
            self.cur_item = LTFigure(name, bbox, mult_matrix(matrix, self.ctm))
        # self._stack.append(self.cur_item)
        # self.cur_item = LTFigure(name, bbox, mult_matrix(matrix, self.ctm))
        super().begin_figure(name, bbox, matrix)
