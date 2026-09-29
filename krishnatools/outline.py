"""Outline booleans (clip, union, translate) on glyf glyphs via skia-pathops."""
import pathops
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen


def path_of(glyph_set, name, dx=0, dy=0):
    path = pathops.Path()
    glyph_set[name].draw(TransformPen(path.getPen(), (1, 0, 0, 1, dx, dy)))
    return path


def rect(x0, y0, x1, y1):
    path = pathops.Path()
    pen = path.getPen()
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()
    return path


def intersect(a, b):
    return pathops.op(a, b, pathops.PathOp.INTERSECTION)


def union(*paths):
    out = paths[0]
    for p in paths[1:]:
        out = pathops.op(out, p, pathops.PathOp.UNION)
    return out


def to_glyf(path, glyph_set):
    """Compile a pathops path to a TrueType glyph (cubics converted to quadratics)."""
    pen = TTGlyphPen(glyph_set)
    path.draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=False))
    return pen.glyph()
