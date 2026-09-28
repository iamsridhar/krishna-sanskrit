"""Helpers for adding glyphs to an existing font's OpenType Layout tables."""
import copy

from fontTools.otlLib.builder import buildCoverage
from fontTools.ttLib.tables import otTables as ot


def append_glyph(font, name, glyph, advance, like):
    """Add a glyf glyph at the end of the glyph order (existing coverages stay sorted)."""
    font['glyf'].glyphs[name] = glyph
    font['hmtx'][name] = (advance, font['hmtx'][like][1])
    classes = font['GDEF'].table.GlyphClassDef.classDefs
    if like in classes:
        classes[name] = classes[like]
    order = list(font.getGlyphOrder()) + [name]
    font.setGlyphOrder(order)
    font['glyf'].glyphOrder = order


def clone_into_gpos(font, base, variant, map_x=lambda x: x):
    """Put `variant` everywhere `base` is in GPOS; anchor x coordinates go through map_x.

    Supports the structures Sanskrit2020 uses: chain-context format 3 coverages,
    mark-to-base bases and mark-to-mark mark2s. Anything else raises, so a new use of the
    glyph can't be silently dropped.
    """
    def anchor(a):
        if a is None:
            return None
        b = copy.deepcopy(a)
        b.XCoordinate = map_x(b.XCoordinate)
        return b

    for lookup in font['GPOS'].table.LookupList.Lookup:
        for st in lookup.SubTable:
            t = lookup.LookupType
            if t == 8 and st.Format == 3:
                for cov in st.BacktrackCoverage + st.InputCoverage + st.LookAheadCoverage:
                    if base in cov.glyphs:
                        cov.glyphs.append(variant)
            elif t == 4:
                if base in st.BaseCoverage.glyphs:
                    rec = st.BaseArray.BaseRecord[st.BaseCoverage.glyphs.index(base)]
                    new = ot.BaseRecord()
                    new.BaseAnchor = [anchor(a) for a in rec.BaseAnchor]
                    st.BaseCoverage.glyphs.append(variant)
                    st.BaseArray.BaseRecord.append(new)
                    st.BaseArray.BaseCount = len(st.BaseArray.BaseRecord)
                if base in st.MarkCoverage.glyphs:
                    raise NotImplementedError(f'{base} as mark in MarkBasePos')
            elif t == 6:
                if base in st.Mark2Coverage.glyphs:
                    rec = st.Mark2Array.Mark2Record[st.Mark2Coverage.glyphs.index(base)]
                    new = ot.Mark2Record()
                    new.Mark2Anchor = [anchor(a) for a in rec.Mark2Anchor]
                    st.Mark2Coverage.glyphs.append(variant)
                    st.Mark2Array.Mark2Record.append(new)
                    st.Mark2Array.MarkCount = len(st.Mark2Array.Mark2Record)
                if base in st.Mark1Coverage.glyphs:
                    raise NotImplementedError(f'{base} as mark1 in MarkMarkPos')
            else:
                glyphs = set()
                for attr in ('Coverage', 'MarkCoverage', 'BaseCoverage', 'LigatureCoverage'):
                    cov = getattr(st, attr, None)
                    if cov:
                        glyphs |= set(cov.glyphs)
                for attr in ('ClassDef1', 'ClassDef2'):
                    cd = getattr(st, attr, None)
                    if cd:
                        glyphs |= set(cd.classDefs)
                if base in glyphs:
                    raise NotImplementedError(f'{base} in GPOS lookup type {t} format {st.Format}')


def append_lookup(table, lookup, feature=None):
    """Append a lookup; if `feature` is given, register it in every record with that tag."""
    table.LookupList.Lookup.append(lookup)
    table.LookupList.LookupCount = len(table.LookupList.Lookup)
    index = table.LookupList.LookupCount - 1
    if feature:
        registered = 0
        for fr in table.FeatureList.FeatureRecord:
            if fr.FeatureTag == feature:
                fr.Feature.LookupListIndex.append(index)
                fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
                registered += 1
        if not registered:
            raise ValueError(f'No {feature} feature to register lookup {index} in')
    return index


def add_mark_filtering_set(font, glyphs):
    """Append a GDEF mark glyph set (upgrading GDEF to 1.2) and return its index."""
    gdef = font['GDEF'].table
    if gdef.Version < 0x00010002 or getattr(gdef, 'MarkGlyphSetsDef', None) is None:
        gdef.Version = 0x00010002
        gdef.MarkGlyphSetsDef = ot.MarkGlyphSetsDef()
        gdef.MarkGlyphSetsDef.MarkSetTableFormat = 1
        gdef.MarkGlyphSetsDef.Coverage = []
    sets = gdef.MarkGlyphSetsDef
    sets.Coverage.append(buildCoverage(glyphs, font.getReverseGlyphMap()))
    sets.MarkSetCount = len(sets.Coverage)
    return sets.MarkSetCount - 1
