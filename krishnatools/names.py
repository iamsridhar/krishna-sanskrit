"""Production glyph names that encode what each glyph spells.

PDF viewers (and search engines, screen readers) recover text from a PDF through each
glyph's name when the glyph has no direct cmap entry. Upstream names most conjunct glyphs
after unrelated Greek/Cyrillic/Latin characters (द्ध्य is `betasymbolgrek`), so copying
text out of a PDF yields garbage. Here every glyph gets an Adobe Glyph List name for the
Unicode sequence it renders (`uni0926094D0927094D092F`), derived from the cmap and the
GSUB rules that produce it.
"""
import io
import re

from fontTools import agl
from fontTools.ttLib import TTFont

KEEP = {'.notdef', '.null', 'nonmarkingreturn'}


def _lookups(gsub):
    for index, lookup in enumerate(gsub.LookupList.Lookup):
        for st in lookup.SubTable:
            if lookup.LookupType == 7:
                yield index, st.ExtensionLookupType, st.ExtSubTable
            else:
                yield index, lookup.LookupType, st


# The shaper reorders ra + virama to (र, ्) before below-base forms are made, but the glyph
# it becomes (the rakar stroke) stands for ्र.
BELOW_BASE_RA_FEATURES = {'blwf', 'rkrf', 'pstf'}
RA_VIRAMA = ('uni0930', 'uni094D')


def _is_pua(cp):
    return 0xE000 <= cp <= 0xF8FF or cp >= 0xF0000


def glyph_sequences(font):
    """glyph name -> the Unicode string it renders.

    Real (non-PUA) cmap entries first, then GSUB single/alternate/ligature closure, and
    only then upstream's Private Use Area code points for glyphs nothing else reaches.
    """
    cmap = font.getBestCmap()
    seq = {}
    for cp, glyph in sorted(cmap.items()):
        if not _is_pua(cp):
            seq.setdefault(glyph, chr(cp))
    gsub = font['GSUB'].table
    features = {}
    for fr in gsub.FeatureList.FeatureRecord:
        for i in fr.Feature.LookupListIndex:
            features.setdefault(i, set()).add(fr.FeatureTag)
    subtables = list(_lookups(gsub))
    changed = True
    while changed:
        changed = False
        for index, kind, st in subtables:
            pairs = []
            if kind == 1:
                pairs = [(out, seq.get(src)) for src, out in st.mapping.items()]
            elif kind == 3:
                pairs = [(out, seq.get(src)) for src, outs in st.alternates.items() for out in outs]
            elif kind == 4:
                below_ra = bool(features.get(index, set()) & BELOW_BASE_RA_FEATURES)
                for first, ligs in st.ligatures.items():
                    for lig in ligs:
                        comps = [first, *lig.Component]
                        if below_ra and tuple(comps) == RA_VIRAMA:
                            pairs.append((lig.LigGlyph, '\u094D\u0930'))
                            continue
                        parts = [seq.get(g) for g in comps]
                        pairs.append((lig.LigGlyph, ''.join(parts) if all(parts) else None))
            for out, text in pairs:
                if text and out not in seq:
                    seq[out] = text
                    changed = True
    for cp, glyph in sorted(cmap.items()):
        if _is_pua(cp):
            seq.setdefault(glyph, chr(cp))
    return seq


def strip_pua(font, seq=None):
    """Drop Private Use Area cmap entries for glyphs that have a real Unicode sequence.

    PDF writers map glyphs back to text through the cmap first, so a PUA entry makes a
    conjunct copy out as U+E145 instead of द्ध्य. Returns the number of code points removed.
    """
    seq = seq or glyph_sequences(font)
    removed = set()
    for table in font['cmap'].tables:
        for cp in [cp for cp, g in table.cmap.items() if _is_pua(cp) and not _is_pua(ord(seq.get(g, chr(cp))[0]))]:
            del table.cmap[cp]
            removed.add(cp)
    return len(removed)


def _agl_name(text):
    if all(ord(c) <= 0xFFFF for c in text):
        return 'uni' + ''.join(f'{ord(c):04X}' for c in text)
    return '_'.join(f'uni{ord(c):04X}' if ord(c) <= 0xFFFF else f'u{ord(c):05X}' for c in text)


_VALID_NAME = re.compile(r'[A-Za-z_.][A-Za-z0-9_.]{0,62}')


def production_names(font):
    """Old name -> new name for every glyph whose name doesn't already decode correctly
    (or isn't a valid post-table name, e.g. `.notdef#1` from merging fonts)."""
    seq = glyph_sequences(font)
    order = font.getGlyphOrder()
    taken, mapping = set(order), {}
    for gid, name in enumerate(order):
        if name in KEEP:
            continue
        base, dot, suffix = name.partition('.')
        text = seq.get(name) or seq.get(base)
        valid = bool(_VALID_NAME.fullmatch(name))
        if valid and text and agl.toUnicode(name) == text:
            continue
        suffix_ok = bool(dot and _VALID_NAME.fullmatch('.' + suffix))
        if text:
            new = _agl_name(text) + ('.' + suffix if suffix_ok else '')
            if not _VALID_NAME.fullmatch(new):
                new = f'_g{gid}'  # sequence too long for a 63-character name
        elif agl.toUnicode(name) or not valid:
            new = f'_g{gid}'  # unreachable glyph whose name would decode wrongly, or invalid
        else:
            continue
        candidate, n = new, 1
        while candidate in taken:
            n += 1
            candidate = f'{new}.alt{n}' if not dot else f'{new}{n}'
        taken.discard(name)
        taken.add(candidate)
        mapping[name] = candidate
    return mapping


def rename(font):
    """Return (new TTFont, mapping, PUA code points removed) with production names.

    PUA cmap entries are stripped on the source font first (while it still uses the old
    names); glyph IDs, and so every table that refers to glyphs by ID, are unchanged.
    """
    seq = glyph_sequences(font)
    removed = strip_pua(font, seq)
    mapping = production_names(font)
    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    out = TTFont(buf)
    out['post']  # decompile with the old order, recompiled with the new one on save
    out.setGlyphOrder([mapping.get(n, n) for n in out.getGlyphOrder()])
    out['post'].formatType = 2.0
    result = io.BytesIO()
    out.save(result, reorderTables=False)
    result.seek(0)
    return TTFont(result), mapping, removed
