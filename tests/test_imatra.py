"""The i-matra hook must land on the final consonant of a conjunct (patch p30)."""
from krishnatools.imatra import I_GLYPHS, required_reach
from krishnatools.shaping import has_internal_virama
from patches.p30_long_i_matra import MIN_LEVEL, STEP

MAX_ERROR = 1.5 * STEP  # bins of STEP per glyph, so up to ~STEP/2 per position


def _shift(glyphs):
    for g in glyphs:
        base, _, suffix = g.name.partition('.l')
        if base in I_GLYPHS:
            return int(suffix) * STEP if suffix else 0
    return None


def _reach_errors(shaped, krishna):
    cache, out = {}, []
    for c, n, _, a in shaped:
        if '\u093F' not in c or not has_internal_virama(c):
            continue
        measured = required_reach(krishna, c, cache)
        shift = _shift(a)
        if not measured or shift is None:
            continue
        delta = measured[1]
        target = delta if delta >= (MIN_LEVEL - 0.5) * STEP else 0
        out.append((c, n, delta, shift, shift - target))
    return out


def test_i_matra_reaches_final_consonant(shaped, krishna):
    errors = _reach_errors(shaped, krishna)
    assert errors
    bad = sorted((e for e in errors if abs(e[4]) > MAX_ERROR), key=lambda e: -e[1])
    assert not bad, f'{len(bad)} clusters, {sum(e[1] for e in bad):,} tokens off by >{MAX_ERROR}: {bad[:8]}'


def test_single_consonant_i_matra_unchanged(shaped, upstream, krishna):
    changed = [c for c, _, u, a in shaped
               if '\u093F' in c and '\u094D' not in c and upstream.signature(u) != krishna.signature(a)]
    assert not changed, changed[:10]
