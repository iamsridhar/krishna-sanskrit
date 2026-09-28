"""Hang anudatta below the u, uu, vocalic r/rr, vocalic l/ll vowel signs and virama.

Upstream positions U+0952 against the base consonant only, so after a below-base
vowel sign (नु॒ भू॒ मृ॒) the two marks overlap. Upstream lookup 35 already stacks the
Vedic Extensions below-accents (U+1CD5-1CDF) under these vowel signs but omits
U+0952, and its anchors are tuned to those glyphs. This patch adds a separate
mark-to-mark lookup, with anchors derived from each glyph's ink, that places the
anudatta centred under the vowel sign with a fixed gap. A mark filtering set lets it
see past above-base marks (reph, anusvara, svarita) that sit between the two.
"""
import re

from fontTools.otlLib.builder import buildAnchor, buildCoverage
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib.tables import otTables as ot

ID = 'p10'
SUMMARY = 'Stack anudatta (U+0952) beneath u/uu/r/rr/l/ll vowel signs and virama instead of overlapping them.'

ANUDATTA = 'uni0952'
BELOW_VOWELS = ['uni0941', 'uni0942', 'uni0943', 'uni0944', 'uni0962', 'uni0963', 'uni094D']
GAP = 100  # font units (2048 upem) between vowel-sign ink and anudatta ink
FEATURE = 'blwm'
USE_MARK_FILTERING_SET = 0x0010

_BELOW_VOWEL_CHARS = '\u0941\u0942\u0943\u0944\u0962\u0963\u094D'
_ABOVE_MARKS = '\u0900-\u0903\u0951\u1CDA\uA8F3\u0300-\u036F'
# Above-base marks (reph, anusvara, svarita...) may sit between the vowel sign and the
# anudatta; the lookup's mark filtering set skips them, so the scope must too.
_AFFECTS = re.compile(f'[{_BELOW_VOWEL_CHARS}][{_ABOVE_MARKS}]*\u0952')


def _ink(font, name):
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    return pen.bounds


def build_subtable(font):
    glyph_map = font.getReverseGlyphMap()
    ax0, _, ax1, atop = _ink(font, ANUDATTA)

    st = ot.MarkMarkPos()
    st.Format = 1
    st.ClassCount = 1
    st.Mark1Coverage = buildCoverage([ANUDATTA], glyph_map)
    st.Mark1Array = ot.Mark1Array()
    rec = ot.MarkRecord()
    rec.Class = 0
    rec.MarkAnchor = buildAnchor(round((ax0 + ax1) / 2), round(atop))
    st.Mark1Array.MarkRecord = [rec]
    st.Mark1Array.MarkCount = 1

    mark2 = sorted(BELOW_VOWELS, key=glyph_map.__getitem__)
    st.Mark2Coverage = buildCoverage(mark2, glyph_map)
    st.Mark2Array = ot.Mark2Array()
    st.Mark2Array.Mark2Record = []
    for name in mark2:
        x0, y0, x1, _ = _ink(font, name)
        r = ot.Mark2Record()
        r.Mark2Anchor = [buildAnchor(round((x0 + x1) / 2), round(y0 - GAP))]
        st.Mark2Array.Mark2Record.append(r)
    st.Mark2Array.MarkCount = len(mark2)
    return st


def add_mark_filtering_set(font, glyphs):
    """Append a GDEF mark glyph set (upgrading GDEF to 1.2) and return its index."""
    gdef = font['GDEF'].table
    if gdef.Version < 0x00010002:
        gdef.Version = 0x00010002
    if getattr(gdef, 'MarkGlyphSetsDef', None) is None:
        gdef.MarkGlyphSetsDef = ot.MarkGlyphSetsDef()
        gdef.MarkGlyphSetsDef.MarkSetTableFormat = 1
        gdef.MarkGlyphSetsDef.Coverage = []
    sets = gdef.MarkGlyphSetsDef
    sets.Coverage.append(buildCoverage(glyphs, font.getReverseGlyphMap()))
    sets.MarkSetCount = len(sets.Coverage)
    return sets.MarkSetCount - 1


def apply(font):
    gpos = font['GPOS'].table
    lookup = ot.Lookup()
    lookup.LookupType = 6
    lookup.LookupFlag = USE_MARK_FILTERING_SET
    lookup.MarkFilteringSet = add_mark_filtering_set(font, BELOW_VOWELS + [ANUDATTA])
    lookup.SubTable = [build_subtable(font)]
    lookup.SubTableCount = 1
    gpos.LookupList.Lookup.append(lookup)
    gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup)
    index = gpos.LookupList.LookupCount - 1

    registered = 0
    for fr in gpos.FeatureList.FeatureRecord:
        if fr.FeatureTag == FEATURE:
            fr.Feature.LookupListIndex.append(index)
            fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
            registered += 1
    if not registered:
        raise ValueError(f'No {FEATURE} feature to register the anudatta lookup in')


def affects(cluster):
    return bool(_AFFECTS.search(cluster))
