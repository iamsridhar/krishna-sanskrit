"""p25: the rakar stroke of प्र is longer and reaches below the bowl."""


def _bounds(shaper, text):
    glyf = shaper.tt['glyf']
    name = shaper.shape(text)[0].name
    g = glyf[name]
    g.recalcBounds(glyf)
    return name, g


def test_pra_stroke_reaches_left_and_down(upstream, krishna):
    _, up = _bounds(upstream, 'प्र')
    _, kr = _bounds(krishna, 'प्र')
    assert kr.xMin <= up.xMin - 25, (up.xMin, kr.xMin)
    coords, _, _ = kr.getCoordinates(krishna.tt['glyf'])
    tip = min(coords[13:27], key=lambda p: p[0])
    assert tip[1] < 200, tip  # upstream tip sits at y≈315


def test_pra_metrics_unchanged(upstream, krishna):
    for text in ('प्र', 'प्रा', 'प्रु', 'प्र॒'):
        assert upstream.signature(upstream.shape(text)) != () and \
            [g.x_advance for g in upstream.shape(text)] == [g.x_advance for g in krishna.shape(text)]
