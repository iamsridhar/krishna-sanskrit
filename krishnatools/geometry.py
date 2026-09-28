"""Ink geometry measured from outlines (point-in-outline sampling)."""
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.pointInsidePen import PointInsidePen


def _inside(glyph_set, name, x, y):
    pen = PointInsidePen(glyph_set, (x, y))
    glyph_set[name].draw(pen)
    return pen.getResult()


def ink_edge(glyph_set, name, y, side, step=4):
    """Rightmost ('right') or leftmost ('left') inked x on row y, or None."""
    pen = BoundsPen(glyph_set)
    glyph_set[name].draw(pen)
    if not pen.bounds:
        return None
    x0, _, x1, _ = pen.bounds
    xs = range(int(x1), int(x0) - 1, -step) if side == 'right' else range(int(x0), int(x1) + 1, step)
    return next((x for x in xs if _inside(glyph_set, name, x, y)), None)


def min_gap(font, left, right, y_range=(80, 1150), row_step=20):
    """Smallest horizontal gap between `left` ink and `right` ink set after it at `left`'s
    advance, over rows in y_range (below the headline). Returns (gap, y)."""
    glyph_set = font.getGlyphSet()
    advance = font['hmtx'][left][0]
    best = None
    for y in range(y_range[0], y_range[1], row_step):
        r = ink_edge(glyph_set, left, y, 'right')
        l = ink_edge(glyph_set, right, y, 'left')
        if r is None or l is None:
            continue
        gap = l + advance - r
        if best is None or gap < best[0]:
            best = (gap, y)
    return best
