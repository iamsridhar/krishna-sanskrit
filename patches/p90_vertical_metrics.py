"""Vertical metrics: consistent line spacing everywhere, and no clipping on Windows.

Upstream's metrics disagree across tables (OS/2 typo line gap 101 vs hhea 51) and its
Windows clipping box (usWin 2200/1000) is smaller than the ink of stacked Vedic marks
(the corpus reaches 2367 above and -1176 below), so some Windows apps clip them. This
patch follows the Google Fonts vertical-metrics guidance:

- line spacing = typo metrics = hhea metrics (upstream's 2200 / -1000 / 51), and the
  USE_TYPO_METRICS flag (OS/2 v4) so Windows uses the same values as macOS;
- usWinAscent / usWinDescent cover the font's full bounding box (they only clip).
"""
ID = 'p90'
SUMMARY = 'Consistent line spacing (USE_TYPO_METRICS, typo = hhea) and a Windows clip box covering all ink.'
CHANGES_RENDERING = False  # metrics only; no glyph or position changes

USE_TYPO_METRICS = 1 << 7


def font_bbox(font):
    glyf = font['glyf']
    y_min = y_max = 0
    for name in font.getGlyphOrder():
        g = glyf[name]
        g.recalcBounds(glyf)
        if g.numberOfContours:
            y_min, y_max = min(y_min, g.yMin), max(y_max, g.yMax)
    return y_min, y_max


def apply(font):
    os2, hhea = font['OS/2'], font['hhea']
    os2.version = max(os2.version, 4)
    os2.fsSelection |= USE_TYPO_METRICS
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = hhea.ascent, hhea.descent, hhea.lineGap
    y_min, y_max = font_bbox(font)
    os2.usWinAscent = max(os2.usWinAscent, y_max)
    os2.usWinDescent = max(os2.usWinDescent, -y_min)


def affects(cluster):
    return False
