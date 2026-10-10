"""Anunāsika before y, v, l written as the joined conjunct (य्ँय, व्ँव, ल्ँल).

A nasalised ṁ before y, v or l is written C + virama + candrabindu + C (यव्ँवा, पापव॑य्ँया):
the candrabindu belongs to the first consonant, where it is pronounced. Because the
candrabindu sits between the virama and the next consonant, the conjunct cannot form,
so upstream shows a visible virama, the candrabindu, and the full letter (व् ँ वा).

This patch shows the joined conjunct (व्व, य्य, ल्ल) with the candrabindu over its first
part, keeping the text unchanged (search, copy-paste and corrections still see व्ँव):

1. A composite glyph per conjunct: the upstream conjunct ligature + the candrabindu,
   placed over the half form as it sits over the full letter.
2. A ligature (C, virama, candrabindu, C) -> that glyph.
3. With an i-matra the shaper has already moved ि in front of the second consonant
   (C ् ँ ि C), so: the first C becomes the i-matra the font uses for the plain conjunct
   (C्Cि, via p30), and (् ँ ि C) becomes a second composite (conjunct.cb.i) whose
   candrabindu is lifted so its bottom sits at the top of that i-matra's arc — at
   headline height it would sit inside the arc (व्ँवि).

The two consonants are in different syllables, so the lookups go in 'rlig', a global
feature HarfBuzz applies across syllable boundaries (the presentation features are
per-syllable there); CoreText gives the same result (tests/test_anunasika.py).
Clusters, the unit of the corpus tests, never contain the sequence, so affects() is
False and the coverage lives in tests/test_anunasika.py.
"""
import io

import uharfbuzz as hb
from fontTools.otlLib.builder import buildCoverage, buildLigatureSubstSubtable, buildSingleSubstSubtable
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent

from krishnatools.otl import append_glyph, append_lookup, clone_into_gpos

ID = 'p40'
SUMMARY = ('Anunasika before y, v, l (य्ँय व्ँव ल्ँल) as the joined conjunct with the candrabindu '
           'over its first part, instead of a visible virama.')
CHANGES_RENDERING = False  # per-cluster corpus can't see it; see tests/test_anunasika.py

VIRAMA, CANDRABINDU = 'uni094D', 'uni0901'
CONSONANTS = {'य': 'uni092F', 'व': 'uni0935', 'ल': 'uni0932'}
I_MARKS = ['', 'ं', 'ँ']  # ि alone, with anusvara, with candrabindu (one glyph each)
FEATURE = 'rlig'


class _Shaper:
    def __init__(self, font):
        buf = io.BytesIO()
        font.save(buf)
        self.font = hb.Font(hb.Face(hb.Blob(buf.getvalue())))
        self.order = font.getGlyphOrder()

    def __call__(self, text):
        b = hb.Buffer()
        b.add_str(text)
        b.guess_segment_properties()
        hb.shape(self.font, b, {})
        return [(self.order[i.codepoint], p.x_offset) for i, p in zip(b.glyph_infos, b.glyph_positions)]


def _lookup(kind, subtables):
    lk = ot.Lookup()
    lk.LookupType = kind
    lk.LookupFlag = 0
    lk.SubTable = subtables
    lk.SubTableCount = len(subtables)
    return lk


def _chain(font, backtrack, inputs, lookahead, nested_index):
    rev = font.getReverseGlyphMap()
    st = ot.ChainContextSubst()
    st.Format = 3
    st.BacktrackCoverage = [buildCoverage(g, rev) for g in reversed(backtrack)]
    st.BacktrackGlyphCount = len(backtrack)
    st.InputCoverage = [buildCoverage(g, rev) for g in inputs]
    st.InputGlyphCount = len(inputs)
    st.LookAheadCoverage = [buildCoverage(g, rev) for g in lookahead]
    st.LookAheadGlyphCount = len(lookahead)
    rec = ot.SubstLookupRecord()
    rec.SequenceIndex = 0
    rec.LookupListIndex = nested_index
    st.SubstLookupRecord = [rec]
    st.SubstCount = 1
    return st


def _register(table, index):
    """Register lookup `index` under FEATURE for Devanāgarī (creating the feature if needed)."""
    records = table.FeatureList.FeatureRecord
    feature_index = next((i for i, fr in enumerate(records) if fr.FeatureTag == FEATURE), None)
    if feature_index is None:
        fr = ot.FeatureRecord()
        fr.FeatureTag = FEATURE
        fr.Feature = ot.Feature()
        fr.Feature.FeatureParams = None
        fr.Feature.LookupListIndex = []
        fr.Feature.LookupCount = 0
        records.append(fr)
        table.FeatureList.FeatureCount = len(records)
        feature_index = len(records) - 1
        for sr in table.ScriptList.ScriptRecord:
            if sr.ScriptTag != 'deva':
                continue
            for ls in [sr.Script.DefaultLangSys] + [r.LangSys for r in sr.Script.LangSysRecord]:
                if ls is not None and feature_index not in ls.FeatureIndex:
                    ls.FeatureIndex.append(feature_index)
                    ls.FeatureCount = len(ls.FeatureIndex)
    feature = records[feature_index].Feature
    feature.LookupListIndex.append(index)
    feature.LookupCount = len(feature.LookupListIndex)


def apply(font):
    shape = _Shaper(font)
    glyf, hmtx = font['glyf'], font['hmtx']
    gsub = font['GSUB'].table
    plan = []  # (consonant glyph, conjunct.cb glyph, conjunct.cb.i glyph, {short i-matra: long i-matra})
    for letter, cons in CONSONANTS.items():
        (conjunct, _), = shape(letter + '्' + letter)          # upstream ligature, e.g. व्व
        half = shape(letter + '्\u200d')[0][0]                 # half form
        cb_offset = shape(letter + 'ँ')[1][1]                  # candrabindu offset on the full letter
        imatra = {}
        for mark in I_MARKS:
            short = shape(letter + 'ि' + mark)[0][0]
            long_ = shape(letter + '्' + letter + 'ि' + mark)[0][0]
            imatra[short] = long_
        arc = imatra[shape(letter + 'ि')[0][0]]
        glyf[arc].recalcBounds(glyf)
        glyf[CANDRABINDU].recalcBounds(glyf)
        lift = glyf[arc].yMax - glyf[CANDRABINDU].yMin
        names = []
        for name, dy in ((conjunct + '.cb', 0), (conjunct + '.cb.i', lift)):
            g = Glyph()
            g.numberOfContours = -1
            g.components = []
            for comp_name, x, y in ((conjunct, 0, 0), (CANDRABINDU, hmtx[half][0] + cb_offset, dy)):
                c = GlyphComponent()
                c.glyphName, c.x, c.y, c.flags = comp_name, x, y, 0x4  # ROUND_XY_TO_GRID
                g.components.append(c)
            append_glyph(font, name, g, hmtx[conjunct][0], conjunct)
            glyf[name].recalcBounds(glyf)
            clone_into_gpos(font, conjunct, name)
            names.append(name)
        plan.append((cons, names[0], names[1], imatra))

    # 1. C ् ँ C -> conjunct.cb
    append_lookup(gsub, _lookup(4, [buildLigatureSubstSubtable(
        {(cons, VIRAMA, CANDRABINDU, cons): name for cons, name, _, _ in plan})]))
    _register(gsub, gsub.LookupList.LookupCount - 1)

    # 2. (i-matra case) first C -> the conjunct's i-matra, when followed by ् ँ ि C
    nested_i = []
    for cons, _, _, imatra in plan:
        for short, long_ in imatra.items():
            append_lookup(gsub, _lookup(1, [buildSingleSubstSubtable({cons: long_})]))
            nested_i.append((cons, short, gsub.LookupList.LookupCount - 1))
    chain_i = [_chain(font, [], [[cons]], [[VIRAMA], [CANDRABINDU], [short], [cons]], index)
               for cons, short, index in nested_i]
    append_lookup(gsub, _lookup(6, chain_i))
    _register(gsub, gsub.LookupList.LookupCount - 1)

    # 3. (i-matra case) ् ँ ि C -> conjunct.cb.i, after that i-matra
    ligatures = {}
    for cons, _, name_i, imatra in plan:
        for short in imatra:
            ligatures[(VIRAMA, CANDRABINDU, short, cons)] = name_i
    append_lookup(gsub, _lookup(4, [buildLigatureSubstSubtable(ligatures)]))
    nested_lig = gsub.LookupList.LookupCount - 1
    chain_l = [_chain(font, [sorted(set(imatra.values()))], [[VIRAMA], [CANDRABINDU], sorted(imatra), [cons]], [],
                      nested_lig)
               for cons, _, _, imatra in plan]
    append_lookup(gsub, _lookup(6, chain_l))
    _register(gsub, gsub.LookupList.LookupCount - 1)


def affects(cluster):
    return False
