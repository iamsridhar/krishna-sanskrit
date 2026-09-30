"""HarfBuzz shaping plus ink-geometry helpers used by tests and proofs."""
import io
import re
from dataclasses import dataclass
from functools import lru_cache

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

VIRAMA = 0x094D
DOTTED_CIRCLE = 0x25CC
ANUDATTA = 'uni0952'
MIN_CLEARANCE = 40


@dataclass(frozen=True)
class Glyph:
    gid: int
    name: str
    cluster: int
    x_advance: int
    x_offset: int
    y_offset: int
    bbox: tuple | None  # ink bbox in cluster coordinates


class Shaper:
    def __init__(self, path=None, ttfont=None):
        if ttfont is not None:
            buf = io.BytesIO()
            ttfont.save(buf)
            data = buf.getvalue()
            self.path = None
            self.hb_font = hb.Font(hb.Face(hb.Blob(data)))
            self.tt = TTFont(io.BytesIO(data))
        else:
            self.path = str(path)
            self.hb_font = hb.Font(hb.Face(hb.Blob.from_file_path(self.path)))
            self.tt = TTFont(self.path)
        self.glyph_set = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        cmap = self.tt.getBestCmap()
        self.virama = cmap.get(VIRAMA)
        self.dotted = cmap.get(DOTTED_CIRCLE)
        classes = self.tt['GDEF'].table.GlyphClassDef.classDefs
        self.marks = {g for g, c in classes.items() if c == 3}
        self._bbox = lru_cache(maxsize=None)(self._ink_bbox)
        self._outline_hashes = {}

    def _ink_bbox(self, name):
        pen = BoundsPen(self.glyph_set)
        self.glyph_set[name].draw(pen)
        return pen.bounds

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb_font, buf, {})
        out, x = [], 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            name = self.order[info.codepoint]
            b = self._bbox(name)
            if b:
                ox, oy = x + pos.x_offset, pos.y_offset
                b = (b[0] + ox, b[1] + oy, b[2] + ox, b[3] + oy)
            out.append(Glyph(info.codepoint, name, info.cluster, pos.x_advance,
                             pos.x_offset, pos.y_offset, b))
            x += pos.x_advance
        return out

    @staticmethod
    def signature(glyphs):
        """Everything a renderer sees; equal signatures mean identical rendering."""
        return tuple((g.gid, g.x_advance, g.x_offset, g.y_offset) for g in glyphs)

    def outline_signature(self, glyphs):
        """Like signature(), but by outline instead of glyph ID, so fonts whose glyph
        order or names differ (subsets, merges, renames) can be compared."""
        glyf = self.tt['glyf']
        out = []
        for g in glyphs:
            if g.name not in self._outline_hashes:
                coords, ends, _ = glyf[g.name].getCoordinates(glyf)
                self._outline_hashes[g.name] = hash((tuple(map(tuple, coords)), tuple(ends)))
            out.append((self._outline_hashes[g.name], g.x_advance, g.x_offset, g.y_offset))
        return tuple(out)

    def issues(self, text, glyphs=None):
        glyphs = glyphs or self.shape(text)
        names = [g.name for g in glyphs]
        found = set()
        if '.notdef' in names:
            found.add('missing')
        if self.dotted and self.dotted in names:
            found.add('dotted')
        if self.virama and self.virama in names[:-1] and has_internal_virama(text):
            found.add('unformed')
        if anudatta_mark_collisions(self, glyphs):
            found.add('anudatta-collision')
        return found


def has_internal_virama(text):
    """Virama (optionally + ZWJ) followed by another consonant, i.e. part of a conjunct."""
    return bool(_INTERNAL_VIRAMA.search(text))


_INTERNAL_VIRAMA = re.compile('\u094D\u200D?[\u0915-\u0939]')


def anudatta_mark_collisions(shaper, glyphs, min_clearance=MIN_CLEARANCE):
    """Anudatta ink closer than min_clearance below another mark it overlaps horizontally."""
    hits = []
    for a in glyphs:
        if a.name != ANUDATTA or not a.bbox:
            continue
        for g in glyphs:
            if g is a or not g.bbox or g.name == ANUDATTA or g.name not in shaper.marks:
                continue
            if min(a.bbox[2], g.bbox[2]) - max(a.bbox[0], g.bbox[0]) <= 0:
                continue
            if g.bbox[3] < a.bbox[1]:
                continue  # g lies entirely below the anudatta
            clearance = g.bbox[1] - a.bbox[3]
            if clearance < min_clearance:
                hits.append((g.name, round(clearance)))
    return hits
