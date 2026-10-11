"""A longer, more visible rakar stroke in प्र.

Upstream's प्र ends its slanted ra-stroke just left of the stem and high on the
letter, so in running text it reads as a stub. The tip of the stroke (outline
points 13-26 of the first contour) is pulled down and to the left, tapering to
nothing at the joint, so the stroke is about a third longer and reaches below
the bowl, as in Noto Sans and Shobhika. Only the outline changes: same glyph,
advance and anchors, so marks (u-signs, accents, anusvara) attach as before.
प्र्य is a separate glyph and is unchanged.
"""
ID = 'p25'
SUMMARY = 'Longer, more visible rakar stroke in प्र.'
# An outline edit: glyph IDs and positions are unchanged, so the per-cluster
# signature tests can't see it; covered by tests/test_rakar.py.
CHANGES_RENDERING = False

GLYPH = 'vowelsignuucombdeva.1'  # upstream प्र
EXPECTED = [(484, 364), (317, 258), (282, 236), (252, 236), (214, 236), (171, 258), (108, 290),
            (59, 315), (58, 346), (57, 378), (104, 395), (218, 436), (319, 472), (374, 512)]
FIRST, DX, DY = 13, -90, -230   # full shift at the tip
X_START, SPAN = 420, 360        # taper: no shift at x >= X_START, full shift at X_START - SPAN


def apply(font):
    glyf = font['glyf']
    glyph = glyf[GLYPH]
    coords, _, _ = glyph.getCoordinates(glyf)
    found = [tuple(coords[i]) for i in range(FIRST, FIRST + len(EXPECTED))]
    if found != EXPECTED:
        raise ValueError(f'{GLYPH}: unexpected outline {found}')
    for i in range(FIRST, FIRST + len(EXPECTED)):
        x, y = coords[i]
        t = max(0.0, min(1.0, (X_START - x) / SPAN))
        coords[i] = (round(x + DX * t), round(y + DY * t))
    glyph.coordinates = coords
    glyph.recalcBounds(glyf)


def affects(cluster):
    return False
