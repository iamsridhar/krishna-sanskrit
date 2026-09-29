"""Split cramped precomposed conjuncts back into Sanskrit2020's own component glyphs.

Upstream fuses these clusters into single glyphs that squeeze every letter into one
akshara width. Written linearly with a half form (ब्‌ + ज) or with an explicit द्, as
Shobhika and the reviewer prefer, they read clearly. This patch does that without drawing
anything: a final multiple-substitution lookup rewrites each fused glyph into the upstream
glyphs it is made of, so marks (u-sign, accents, anusvara, reph) attach through their
existing anchors. (The द-stacks with ya are redrawn instead, by p15.)
"""
import re

from fontTools.otlLib.builder import buildMultipleSubstSubtable
from fontTools.ttLib.tables import otTables as ot

from krishnatools.otl import append_lookup

ID = 'p20'
SUMMARY = ('Split cramped conjunct ligatures into component glyphs (bja, ktra, kca, cchra, ntrya, '
           '...; ddhva, ddhma, ddhra, dghra, drva as da + virama).')

HALF_NA, HALF_BA, HALF_KA, HALF_CA, HALF_NYA = 'glyph219', 'glyph222', 'glyph200', 'glyph205', 'glyph209'
DA_VIRAMA = 'glyph217'  # द with a visible virama; upstream's द-half form
JA, CA, TRA, CHRA = 'uni091C', 'uni091A', 'signavagrahadeva.1', 'ladeva.1'
DDHYA, DVYA = 'betasymbolgrek', 'Sheicopt'  # redrawn by p15


# fused upstream glyph -> (conjunct it renders, replacement glyph sequence)
DECOMPOSE = {
    'Zhecyrl': ('न्द्ध्य', [HALF_NA, DDHYA]),
    'Encyrl': ('न्द्व्य', [HALF_NA, DVYA]),
    'izhitsadoublegravecyrl': ('ब्ज', [HALF_BA, JA]),
    'lretroflexhook': ('क्त्र', [HALF_KA, TRA]),
    'hturned': ('क्च', [HALF_KA, CA]),
    'Yicyrl': ('न्त्र्य', [HALF_NA, 'glyph930']),  # glyph930 = upstream त्र्य
    # द-stacks with a complex lower letter: written द् + rest, like upstream's own द्ध्न.
    'Upsilonacutehooksymbolgrek': ('द्ध्व', [DA_VIRAMA, 'gangiacopt']),
    'Kaisymbolgrek': ('द्ध्म', [DA_VIRAMA, 'Horicopt']),
    'thetasymbolgrek': ('द्ध्र', [DA_VIRAMA, 'vowelsigniideva.1']),
    'upsilongrek.1': ('द्घ्र', [DA_VIRAMA, 'yadeva.1']),
    'Sampigrek': ('द्र्व', [DA_VIRAMA, 'uni0935', 'rephaabove']),
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


def apply(font):
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
