"""Composite-glyph hygiene flagged by FontBakery (no visual change).

- Upstream's U+0957 places the same component (U+0956) twice at the same spot; drop the
  exact duplicate (overlapping identical ink looks the same).
- Upstream's U+0977 uses U+0957, itself a composite. Some rasterizers and converters
  handle nested components poorly; flatten to one level.
"""
from fontTools.ttLib.tables._g_l_y_f import GlyphComponent

ID = 'p95'
SUMMARY = 'Remove a duplicate component and flatten nested composites (no visual change).'
CHANGES_RENDERING = False


def _key(c):
    return (c.glyphName, c.x, c.y, getattr(c, 'transform', None) and tuple(map(tuple, c.transform)))


def _flattened(glyf, comp):
    child = glyf[comp.glyphName]
    if not child.isComposite():
        return [comp]
    if getattr(comp, 'transform', None) is not None:
        raise NotImplementedError(f'transformed nested component {comp.glyphName}')
    out = []
    for sub in child.components:
        for leaf in _flattened(glyf, sub):
            new = GlyphComponent()
            new.glyphName, new.x, new.y = leaf.glyphName, leaf.x + comp.x, leaf.y + comp.y
            new.flags = leaf.flags
            if getattr(leaf, 'transform', None) is not None:
                new.transform = leaf.transform
            out.append(new)
    return out


def apply(font):
    glyf = font['glyf']
    for name in font.getGlyphOrder():
        g = glyf[name]
        if not g.isComposite():
            continue
        comps, seen = [], set()
        for comp in g.components:
            for leaf in _flattened(glyf, comp):
                if _key(leaf) not in seen:
                    seen.add(_key(leaf))
                    comps.append(leaf)
        if len(comps) != len(g.components) or any(a is not b for a, b in zip(comps, g.components)):
            g.components = comps
            g.recalcBounds(glyf)


def affects(cluster):
    return False
