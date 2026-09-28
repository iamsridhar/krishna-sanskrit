"""Split cramped precomposed conjuncts back into Sanskrit2020's own component glyphs.

Upstream fuses these clusters into single glyphs that squeeze every letter into one
akshara width. Shobhika's structure is clearer: stack the first two letters and join a
full-size ya to them (द्ध + य), or write the cluster linearly with a half form (ब्‌ + ज).
This patch reproduces that structure without drawing anything: a final multiple-
substitution lookup rewrites each fused glyph into the upstream glyphs it is made of.
Because the result is made of real upstream glyphs, marks (u-sign, accents, anusvara,
reph) attach through their existing anchors.

For the stack + ya forms, the stack is replaced by a joining copy (`<stack>.yj`): the same
outline with a narrower advance, measured so the ya's left bowl meets the stack with
JOIN_OVERLAP units of overlap. A copy is needed because द्धय (no virama) produces the same
stack + ya glyphs and must stay apart.
"""
import copy
import re

from fontTools.otlLib.builder import buildMultipleSubstSubtable
from fontTools.ttLib.tables import otTables as ot

from krishnatools.geometry import min_gap
from krishnatools.otl import append_glyph, append_lookup, clone_into_gpos

ID = 'p20'
SUMMARY = 'Split cramped conjunct ligatures (ddhya, dbhya, dvya, ddya, bja, ktra, kca, cchra, ...) into component glyphs.'

HALF_NA, HALF_BA, HALF_KA, HALF_CA, HALF_NYA = 'glyph219', 'glyph222', 'glyph200', 'glyph205', 'glyph209'
YA, JA, CA, TRA, CHRA = 'uni092F', 'uni091C', 'uni091A', 'signavagrahadeva.1', 'ladeva.1'
STACK_DDHA, STACK_DBHA, STACK_DVA, STACK_DDA = 'upsilontonosgrek', 'kaisymbolgrek', 'sampigrek', 'psigrek'
YA_STACKS = [STACK_DDHA, STACK_DBHA, STACK_DVA, STACK_DDA]
JOIN_OVERLAP = 20


def joined(stack):
    return f'{stack}.yj'


# fused upstream glyph -> (conjunct it renders, replacement glyph sequence)
DECOMPOSE = {
    'betasymbolgrek': ('द्ध्य', [joined(STACK_DDHA), YA]),
    'Archaickoppagrek': ('द्भ्य', [joined(STACK_DBHA), YA]),
    'Sheicopt': ('द्व्य', [joined(STACK_DVA), YA]),
    'omegagrek': ('द्द्य', [joined(STACK_DDA), YA]),
    'Zhecyrl': ('न्द्ध्य', [HALF_NA, joined(STACK_DDHA), YA]),
    'Encyrl': ('न्द्व्य', [HALF_NA, joined(STACK_DVA), YA]),
    'izhitsadoublegravecyrl': ('ब्ज', [HALF_BA, JA]),
    'lretroflexhook': ('क्त्र', [HALF_KA, TRA]),
    'hturned': ('क्च', [HALF_KA, CA]),
    'raisedcolonmod': ('च्छ्र', [HALF_CA, CHRA]),
    'palatalizedhookbelowcomb': ('ञ्छ्र', [HALF_NYA, CHRA]),
    # Below-base ra left over when no rakar ligature applies (र्र्ष, भ्र्रा): show र +
    # virama instead of a detached hook, as Shobhika does.
    'glyph89': ('र्र', ['uni0930', 'uni094D']),
}
# psts is the last presentation feature. HarfBuzz runs all presentation lookups in one
# pass in lookup order, but CoreText runs them feature by feature, so registering here
# keeps this lookup after upstream's pres/psts ligatures in both engines.
FEATURE = 'psts'

_AFFECTS = re.compile('|'.join(sorted({seq for seq, _ in DECOMPOSE.values()}, key=len, reverse=True)))
_EXPLICIT_VIRAMA = re.compile('र्र')


def join_tightening(font, stack):
    """Units to remove from the stack's advance so ya's ink overlaps it by JOIN_OVERLAP."""
    gap, _ = min_gap(font, stack, YA)
    return max(0, round(gap + JOIN_OVERLAP))


def _add_joining_stacks(font):
    glyf, hmtx = font['glyf'], font['hmtx']
    for stack in YA_STACKS:
        advance = hmtx[stack][0] - join_tightening(font, stack)
        append_glyph(font, joined(stack), copy.deepcopy(glyf[stack]), advance, like=stack)
        clone_into_gpos(font, stack, joined(stack))


def apply(font):
    _add_joining_stacks(font)
    glyphs = set(font.getGlyphOrder())
    mapping = {}
    for src, (_, seq) in DECOMPOSE.items():
        missing = [g for g in [src, *seq] if g not in glyphs]
        if missing:
            raise ValueError(f'{src}: unknown glyphs {missing}')
        mapping[src] = seq

    lookup = ot.Lookup()
    lookup.LookupType = 2
    lookup.LookupFlag = 0
    lookup.SubTable = [buildMultipleSubstSubtable(mapping)]
    lookup.SubTableCount = 1
    append_lookup(font['GSUB'].table, lookup, FEATURE)


def affects(cluster):
    return bool(_AFFECTS.search(cluster))


def intentional_virama(cluster):
    """Clusters where this patch deliberately shows a visible virama."""
    return bool(_EXPLICIT_VIRAMA.search(cluster))
