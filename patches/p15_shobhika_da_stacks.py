"""Redraw द्ध, द्ध्य, द्भ्य, द्व्य, द्द्य from Shobhika's outlines, at Krishna's size and weight.

Upstream squeezes the lower letter of these द-stacks and fuses the ya-phala into a cramped
block. Shobhika (OFL, IIT Bombay) draws them open: a small ध-loop or lower letter flowing
into a full द bowl, with a compact ya-phala joined on. This patch takes those outlines and
fits them to Sanskrit2020:

- scale y so Shobhika's headline top (700) meets Sanskrit2020's (1325), and x so its द
  width (620) matches Sanskrit2020's द (996);
- thicken vertical stems by merging copies shifted right by up to STEM_BOOST units
  (horizontals stay thin, as in Sanskrit2020's high-contrast design);
- lay Sanskrit2020's own headline (y 1169-1325) across the full width.

The upstream glyph names are kept, so all GSUB rules still produce them. Mark anchors
are the upstream glyph's anchors scaled to the new width.
"""
import hashlib
import re
from pathlib import Path

import pathops
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from krishnatools.outline import rect, to_glyf, union

ID = 'p15'
SUMMARY = 'Redraw ddha, ddhya, dbhya, dvya, ddya from Shobhika outlines at Krishna size and weight.'

SHOBHIKA = Path(__file__).resolve().parent.parent / 'upstream' / 'Shobhika-Regular.otf'
SHOBHIKA_SHA256 = 'bde48974337ea665b930d956c26d0b3884f1bc0549769bfb7d82caa3e0af181f'
COPYRIGHT_ADDITION = ('Glyphs for ddha, ddhya, dbhya, dvya and ddya derived from Shobhika, '
                      'Copyright (c) 2016 IIT Bombay (www.iitb.ac.in).')

# upstream glyph -> Shobhika source glyph
REDRAW = {
    'upsilontonosgrek': 'DaDha.dv',   # द्ध
    'betasymbolgrek': 'DaDhaYa.dv',   # द्ध्य
    'Archaickoppagrek': 'DaBhaYa.dv',  # द्भ्य
    'Sheicopt': 'DaVaYa.dv',          # द्व्य
    'omegagrek': 'DaDaYa.dv',         # द्द्य
}
SCALE_Y = 1325 / 700
SCALE_X = 996 / 620
STEM_BOOST = 40
HEADLINE = (1169, 1325)

_AFFECTS = re.compile('द्ध|द्भ्य|द्व्य|द्द्य')


def _shobhika():
    if hashlib.sha256(SHOBHIKA.read_bytes()).hexdigest() != SHOBHIKA_SHA256:
        raise ValueError(f'{SHOBHIKA} changed; update SHOBHIKA_SHA256 deliberately')
    return TTFont(SHOBHIKA)


def fitted_glyph(shobhika, source, glyph_set):
    """Shobhika glyph scaled, stem-thickened and given Sanskrit2020's headline."""
    src = shobhika.getGlyphSet()[source]

    def placed(dx):
        path = pathops.Path()
        src.draw(TransformPen(path.getPen(), (SCALE_X, 0, 0, SCALE_Y, dx, 0)))
        return path

    advance = round(shobhika['hmtx'][source][0] * SCALE_X) + STEM_BOOST
    shape = union(placed(0), placed(STEM_BOOST / 2), placed(STEM_BOOST), rect(0, HEADLINE[0], advance, HEADLINE[1]))
    return to_glyf(shape, glyph_set), advance


def _scale_anchors(font, name, factor):
    for lookup in font['GPOS'].table.LookupList.Lookup:
        for st in lookup.SubTable:
            st = st.ExtSubTable if lookup.LookupType == 9 else st
            cov = getattr(st, 'BaseCoverage', None)
            if lookup.LookupType == 4 or (lookup.LookupType == 9 and cov):
                if name in cov.glyphs:
                    for a in st.BaseArray.BaseRecord[cov.glyphs.index(name)].BaseAnchor:
                        if a is not None:
                            a.XCoordinate = round(a.XCoordinate * factor)


def apply(font):
    shobhika = _shobhika()
    glyf, hmtx, glyph_set = font['glyf'], font['hmtx'], font.getGlyphSet()
    for name, source in REDRAW.items():
        glyph, advance = fitted_glyph(shobhika, source, glyph_set)
        glyph.recalcBounds(glyf)
        old_advance = hmtx[name][0]
        glyf[name] = glyph
        hmtx[name] = (advance, glyph.xMin)
        _scale_anchors(font, name, advance / old_advance)

    names = font['name']
    copyright_ = names.getDebugName(0)
    if COPYRIGHT_ADDITION not in copyright_:
        names.removeNames(nameID=0)
        for platform in ((3, 1, 0x409), (1, 0, 0)):
            names.setName(f'{copyright_} {COPYRIGHT_ADDITION}', 0, *platform)


def affects(cluster):
    return bool(_AFFECTS.search(cluster))
