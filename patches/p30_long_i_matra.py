"""Longer i-matra (ि) hooks that reach the final consonant of a conjunct.

Upstream has a single i-matra, sized for one consonant, so before a conjunct the hook
stops over the first half-form (क्त्रि reads like कि + त्र). This patch:

1. Makes stretched copies of the six i-matra glyphs (plain, +anusvara, +candrabindu,
   and the reph-merged forms) in steps of STEP units. The outline is split at SPLIT_X,
   on the flat top of the arc: everything right of it (arc end, tip, and any anusvara,
   candrabindu or reph contour) moves right; the stem and left curve do not.
2. Chooses a length per conjunct so the hook lands on the final consonant the way it
   lands on that consonant alone (krishnatools.imatra.required_reach). Rules are learned
   from the corpus plus every generated 2- and 3-consonant cluster, and generalise by
   width class: every glyph before the last contributes its advance, the last glyph its
   width beyond its final consonant.
3. Adds each variant to every GPOS table its original is in (anchors right of SPLIT_X
   shifted with the outline), so accents keep their upstream behaviour.

Clusters needing less than MIN_LEVEL steps keep the upstream i-matra, so the i-matra
before a single consonant never changes.
"""
import copy
from collections import defaultdict
from statistics import median

from fontTools.otlLib.builder import buildCoverage, buildSingleSubstSubtable
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables import ttProgram

from krishnatools.corpus import load_clusters
from krishnatools.imatra import I_GLYPHS, candidate_clusters, required_reach
from krishnatools.shaping import Shaper, has_internal_virama

ID = 'p30'
SUMMARY = 'Longer i-matra hooks that reach the final consonant of conjuncts.'

STEP = 120
MIN_LEVEL = 2
MAX_LEVEL = 24
SPLIT_X = 530
MAIN_CONTOURS = 2  # the i-matra itself; later contours (bindu, reph) move rigidly
# Last presentation feature: CoreText applies features one at a time, so this keeps the
# lookup after upstream's psts ligature that merges the i-matra with anusvara/reph.
FEATURE = 'psts'
USE_MARK_FILTERING_SET = 0x0010
# ZWJ is this glyph while GSUB runs (both engines only show it as `space` afterwards).
# HarfBuzz skips it when matching contexts; CoreText does not, so multi-glyph rules
# get extra copies with it in each possible position.
ZWJ_GLYPH = 'uni200D'


def variant_name(base, level):
    return f'{base}.l{level:02d}'


def _stretch_x(x, shift):
    return x + shift if x > SPLIT_X else x


def _stretched_glyph(glyf, name, shift):
    g = copy.deepcopy(glyf[name])
    if g.isComposite():
        raise ValueError(f'{name} is composite')
    coords = g.coordinates
    start = 0
    for contour, end in enumerate(g.endPtsOfContours):
        for i in range(start, end + 1):
            x, y = coords[i]
            coords[i] = (x + shift if contour >= MAIN_CONTOURS else _stretch_x(x, shift), y)
        start = end + 1
    g.program = ttProgram.Program()  # upstream hints don't fit the stretched outline
    g.program.fromBytecode(b'')
    g.recalcBounds(glyf)
    return g


def _levels_and_rules(font):
    """Learn (lookahead coverages -> level) rules from shaping candidate clusters."""
    shaper = Shaper(ttfont=font)
    hmtx = font['hmtx']
    cache, ext_samples, runs = {}, defaultdict(list), {}
    for cluster in candidate_clusters(load_clusters()):
        measured = required_reach(shaper, cluster, cache)
        if not measured:
            continue
        run, delta = measured
        names = tuple(g.name for g in run)
        last = names[-1]
        ext_samples[last].append(sum(g.x_advance for g in run[-1:]) - (sum(g.x_advance for g in run) - delta))
        runs[names] = delta
    ext = {g: median(v) for g, v in ext_samples.items()}

    def bin_(units):
        return round(units / STEP)

    rules = defaultdict(lambda: defaultdict(set))  # signature -> position -> glyphs
    levels = {}
    for names, _ in runs.items():
        prefix_bins = tuple(bin_(hmtx[g][0]) for g in names[:-1])
        last_bin = bin_(ext[names[-1]])
        level = min(sum(prefix_bins) + last_bin, MAX_LEVEL)
        signature = prefix_bins + (last_bin,)
        levels[signature] = level
        for pos, g in enumerate(names):
            rules[signature][pos].add(g)
    return rules, levels


def _add_variant_to_gpos(font, base, variant, shift):
    """Put `variant` everywhere `base` is in GPOS, with anchors shifted like the outline."""
    def anchor(a):
        if a is None:
            return None
        b = copy.deepcopy(a)
        b.XCoordinate = _stretch_x(b.XCoordinate, shift)
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
                if base in glyphs:
                    raise NotImplementedError(f'{base} in GPOS lookup type {t} format {st.Format}')


def _append_lookup(table, lookup):
    table.LookupList.Lookup.append(lookup)
    table.LookupList.LookupCount = len(table.LookupList.Lookup)
    return table.LookupList.LookupCount - 1


def _mark_filtering_set(font, glyphs):
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


def apply(font):
    rules, levels = _levels_and_rules(font)
    used = sorted({lv for lv in levels.values() if lv >= MIN_LEVEL})

    # 1. variant glyphs, appended to the glyph order so existing coverages stay sorted
    glyf, hmtx = font['glyf'], font['hmtx']
    classes = font['GDEF'].table.GlyphClassDef.classDefs
    order = list(font.getGlyphOrder())
    for level in used:
        for base in I_GLYPHS:
            name = variant_name(base, level)
            glyf.glyphs[name] = _stretched_glyph(glyf, base, level * STEP)
            hmtx[name] = hmtx[base]
            classes[name] = classes[base]
            order.append(name)
    font.setGlyphOrder(order)
    glyf.glyphOrder = order
    for level in used:
        for base in I_GLYPHS:
            _add_variant_to_gpos(font, base, variant_name(base, level), level * STEP)

    # 2. one single-substitution lookup per length, referenced from a chaining lookup
    gsub = font['GSUB'].table
    gmap = font.getReverseGlyphMap()
    subst_index = {}
    for level in used:
        lk = ot.Lookup()
        lk.LookupType, lk.LookupFlag = 1, 0
        lk.SubTable = [buildSingleSubstSubtable({b: variant_name(b, level) for b in I_GLYPHS})]
        lk.SubTableCount = 1
        subst_index[level] = _append_lookup(gsub, lk)

    contexts = []  # (lookahead glyph sets, level)
    for signature, level in levels.items():
        # A matching subtable ends the lookup, so short multi-glyph runs still need an
        # (action-less) rule; otherwise a shorter rule could match their first glyph.
        if level < MIN_LEVEL and len(signature) == 1:
            continue
        sets = [sorted(rules[signature][p]) for p in range(len(signature))]
        contexts.append((sets, level))
        for j in range(len(sets) - 1):
            contexts.append((sets[:j + 1] + [[ZWJ_GLYPH]] + sets[j + 1:], level))

    subtables = []
    for sets, level in sorted(contexts, key=lambda c: -len(c[0])):  # longest context first
        st = ot.ChainContextSubst()
        st.Format = 3
        st.BacktrackCoverage = []
        st.InputCoverage = [buildCoverage(I_GLYPHS, gmap)]
        st.LookAheadCoverage = [buildCoverage(glyphs, gmap) for glyphs in sets]
        st.BacktrackGlyphCount, st.InputGlyphCount = 0, 1
        st.LookAheadGlyphCount = len(st.LookAheadCoverage)
        st.SubstLookupRecord = []
        if level >= MIN_LEVEL:
            rec = ot.SubstLookupRecord()
            rec.SequenceIndex, rec.LookupListIndex = 0, subst_index[level]
            st.SubstLookupRecord = [rec]
        st.SubstCount = len(st.SubstLookupRecord)
        subtables.append(st)

    chain = ot.Lookup()
    chain.LookupType = 6
    chain.LookupFlag = USE_MARK_FILTERING_SET
    chain.MarkFilteringSet = _mark_filtering_set(font, I_GLYPHS)
    chain.SubTable = subtables
    chain.SubTableCount = len(subtables)
    index = _append_lookup(gsub, chain)
    registered = 0
    for fr in gsub.FeatureList.FeatureRecord:
        if fr.FeatureTag == FEATURE:
            fr.Feature.LookupListIndex.append(index)
            fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
            registered += 1
    if not registered:
        raise ValueError(f'No {FEATURE} feature for the i-matra lookup')


def affects(cluster):
    return '\u093F' in cluster and has_internal_virama(cluster)
