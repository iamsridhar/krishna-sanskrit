"""Replace upstream's Latin with Gentium Medium (SIL, OFL) for transliteration.

Sanskrit2020 bundles URW Palladio Latin, which is AGPL/GPL-licensed (not OFL-compatible)
and lacks the combining accents used in ISO-15919 Vedic transliteration (U+0320 anudātta
below, U+030D/U+030E svarita above, U+0325 ring below, U+0310 candrabindu). This step:

1. keeps only the Devanāgarī part of the patched font (Devanāgarī, Vedic Extensions,
   Devanāgarī Extended, joiners, dotted circle, spaces) with all its layout;
2. takes Gentium Medium's Latin (Latin, IPA, spacing modifiers, combining marks, Latin
   Extended Additional, general punctuation), with its mark/mkmk/kern and common
   typographic features, scaled so its x-height matches the Latin Sanskrit2020 used;
3. merges the two; glyph outlines and positioning of both parts are unchanged.
"""
import io

from fontTools import merge, subset
from fontTools.ttLib import TTFont
from fontTools.ttLib.scaleUpem import scale_upem

from krishnatools import upstream

DEVANAGARI = [
    *range(0x0900, 0x0980), *range(0x1CD0, 0x1D00), *range(0xA8E0, 0xA900),
    0x200C, 0x200D, 0x25CC, 0x0020, 0x00A0,
]
LATIN = [
    *range(0x0021, 0x007F), *range(0x00A1, 0x0250),   # ASCII, Latin-1, Latin Extended-A/B
    *range(0x0250, 0x0370),                            # IPA, spacing modifiers, combining marks
    *range(0x1AB0, 0x1B00), *range(0x1D00, 0x1F00),    # combining marks ext., phonetic ext., combining supp., Latin Ext. Additional
    *range(0x2000, 0x2070),                            # general punctuation (incl. U+2060 word joiner)
    *range(0x20A0, 0x20C1),                            # currency, incl. ₹
    *range(0x2C60, 0x2C80), *range(0xA720, 0xA800), *range(0xAB30, 0xAB70),  # Latin Ext. C/D/E (case pairs)
    0x2122, 0x2212,
]
LATIN_FEATURES = ['ccmp', 'locl', 'mark', 'mkmk', 'kern', 'liga', 'calt', 'case', 'frac', 'numr',
                  'dnom', 'sups', 'subs', 'ordn', 'onum', 'lnum', 'pnum', 'tnum', 'smcp', 'c2sc']
TARGET_X_HEIGHT = 961  # x-height of the Latin inside Sanskrit2020, at 2048 upem
GENTIUM_COPYRIGHT = ('Latin derived from Gentium, Copyright (c) 2003-2025 SIL Global '
                     '(https://www.sil.org/), with Reserved Font Names "Gentium" and "SIL".')


def _subset(font, unicodes, scripts, features, drop=()):
    options = subset.Options()
    options.layout_features = features
    options.layout_scripts = scripts
    options.glyph_names = True
    options.name_IDs = ['*']
    options.name_languages = ['*']
    options.notdef_outline = True
    options.hinting = False
    options.drop_tables += list(drop)
    s = subset.Subsetter(options)
    s.populate(unicodes=unicodes)
    s.subset(font)
    return font


def latin_scale():
    gentium = TTFont(upstream.path('Gentium-Medium.ttf'))
    return TARGET_X_HEIGHT / gentium['OS/2'].sxHeight


def latin_font():
    """Gentium Medium's Latin, subset and scaled to match the Devanāgarī."""
    font = TTFont(upstream.path('Gentium-Medium.ttf'))
    _subset(font, [c for c in LATIN if c not in DEVANAGARI], ['latn', 'DFLT'], LATIN_FEATURES,
            drop=['Silf', 'Glat', 'Gloc', 'Feat', 'Sill', 'Silt', 'STAT', 'DSIG', 'meta'])
    upem = font['head'].unitsPerEm
    scale_upem(font, round(upem * TARGET_X_HEIGHT / font['OS/2'].sxHeight))
    font['head'].unitsPerEm = upem  # same em, so the design is now TARGET/x-height larger
    return font


def compose(devanagari_font):
    """Devanāgarī part of `devanagari_font` merged with Gentium Latin. Returns a TTFont."""
    deva = TTFont(_to_bytes(devanagari_font))
    _subset(deva, DEVANAGARI, ['deva', 'dev2', 'DFLT'], ['*'])
    latin = latin_font()
    if latin['head'].unitsPerEm != deva['head'].unitsPerEm:
        raise ValueError('units per em differ')
    merged = merge.Merger(options=merge.Options(drop_tables=['vmtx', 'vhea'])).merge(
        [_to_bytes(deva), _to_bytes(latin)])
    _below_marks_on_vedic_anusvara(merged)
    merged['head'].fontRevision = deva['head'].fontRevision  # the merger keeps the highest (Gentium's)
    names = merged['name']
    notice = names.getDebugName(0)
    if GENTIUM_COPYRIGHT not in notice:
        names.setName(f'{notice} {GENTIUM_COPYRIGHT}', 0, 3, 1, 0x409)
    return TTFont(_to_bytes(merged))


VEDIC_ANUSVARAS = [0xA8F3, 0xA8F4]  # ꣳ ꣴ, written inside ISO-15919 transliteration


def _below_marks_on_vedic_anusvara(font):
    """ISO transliteration writes accents on ꣳ/ꣴ (ꣳ̠ occurs 11,403 times in the corpus).
    Those are Devanāgarī-Extended characters, so HarfBuzz shapes the cluster as Devanāgarī
    and Gentium's Latin-only mark lookup never sees it: the accent would sit wherever its
    outline happens to be. Add a lookup, in every script's `mark` feature, that hangs
    Gentium's below-marks under ꣳ/ꣴ exactly as Gentium hangs them under its letters."""
    import copy
    from fontTools.otlLib.builder import buildAnchor, buildCoverage
    from fontTools.ttLib.tables import otTables as ot
    from krishnatools.otl import append_lookup

    cmap, gmap = font.getBestCmap(), font.getReverseGlyphMap()
    anudatta, letter_a = cmap[0x0320], cmap[ord('a')]
    source = None
    for lookup in font['GPOS'].table.LookupList.Lookup:
        for st in lookup.SubTable:
            st = st.ExtSubTable if lookup.LookupType == 9 else st
            if getattr(st, 'MarkCoverage', None) and hasattr(st, 'BaseCoverage') \
                    and anudatta in st.MarkCoverage.glyphs and letter_a in st.BaseCoverage.glyphs:
                source = st
    if source is None:
        raise ValueError("Gentium's below-mark lookup not found")
    below = source.MarkArray.MarkRecord[source.MarkCoverage.glyphs.index(anudatta)].Class
    marks = [(g, r) for g, r in zip(source.MarkCoverage.glyphs, source.MarkArray.MarkRecord) if r.Class == below]
    a_anchor = source.BaseArray.BaseRecord[source.BaseCoverage.glyphs.index(letter_a)].BaseAnchor[below]
    a_ymin = font['glyf'][letter_a].yMin

    st = ot.MarkBasePos()
    st.Format, st.ClassCount = 1, 1
    marks.sort(key=lambda m: gmap[m[0]])
    st.MarkCoverage = buildCoverage([g for g, _ in marks], gmap)
    st.MarkArray = ot.MarkArray()
    st.MarkArray.MarkRecord = []
    for _, rec in marks:
        new = copy.deepcopy(rec)
        new.Class = 0
        st.MarkArray.MarkRecord.append(new)
    st.MarkArray.MarkCount = len(marks)
    bases = sorted((cmap[cp] for cp in VEDIC_ANUSVARAS), key=gmap.__getitem__)
    st.BaseCoverage = buildCoverage(bases, gmap)
    st.BaseArray = ot.BaseArray()
    st.BaseArray.BaseRecord = []
    glyf = font['glyf']
    for name in bases:
        g = glyf[name]
        g.recalcBounds(glyf)
        rec = ot.BaseRecord()
        # same drop below the ink as Gentium uses for 'a'
        rec.BaseAnchor = [buildAnchor(round((g.xMin + g.xMax) / 2),
                                      round(min(g.yMin, 0) + a_anchor.YCoordinate - min(a_ymin, 0)))]
        st.BaseArray.BaseRecord.append(rec)
    st.BaseArray.BaseCount = len(bases)
    lookup = ot.Lookup()
    lookup.LookupType, lookup.LookupFlag = 4, 0
    lookup.SubTable, lookup.SubTableCount = [st], 1
    append_lookup(font['GPOS'].table, lookup, 'mark')


def _to_bytes(font):
    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    return buf
