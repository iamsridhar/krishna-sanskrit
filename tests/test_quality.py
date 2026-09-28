"""Quality gates over the whole corpus. Krishna must never be worse than upstream."""
from krishnatools.shaping import anudatta_mark_collisions


def test_no_new_missing_glyphs_or_dotted_circles(shaped, upstream, krishna):
    """Dotted circles from malformed input text (e.g. an accent before an anusvara) also
    appear upstream; those are text bugs, not font bugs. Krishna must add none."""
    flags = {'missing', 'dotted'}
    bad = [(c, sorted(krishna.issues(c, a) & flags)) for c, _, u, a in shaped
           if krishna.issues(c, a) & flags - upstream.issues(c, u)]
    assert not bad, bad[:10]


def test_conjunct_formation_not_worse_than_upstream(shaped, upstream, krishna):
    regressions = [c for c, _, u, a in shaped
                   if 'unformed' in krishna.issues(c, a) and 'unformed' not in upstream.issues(c, u)]
    assert not regressions, regressions[:10]


KNOWN_RESIDUAL = {
    # Anudatta after visarga is moved back under the preceding akshara by upstream
    # contextual positioning, landing on the u-sign. 4 tokens.
    'ष्टुः॒',
    # Anudatta on ꣳ/ꣴ after uu: the uu tail reaches under the next base. 11 tokens.
    'त्रू॒ꣳ॒', 'जू॒ꣴ॒', 'तू॒ꣳ॒',
    # ङ्कु is a precomposed ligature (glyph570), not base + u-sign. 2 tokens.
    'ङ्कुं॒', 'ङ्कुः॒',
}


def test_anudatta_clears_below_vowel_signs(shaped, krishna):
    hits = [(c, n, anudatta_mark_collisions(krishna, a)) for c, n, _, a in shaped
            if c not in KNOWN_RESIDUAL and anudatta_mark_collisions(krishna, a)]
    hits.sort(key=lambda h: -h[1])
    assert not hits, f'{len(hits)} clusters, {sum(h[1] for h in hits):,} tokens, e.g. {hits[:8]}'


def test_upstream_baseline_is_really_broken(shaped, upstream):
    """Guards the collision check itself: it must detect the known upstream defect."""
    tokens = sum(n for c, n, u, _ in shaped if anudatta_mark_collisions(upstream, u))
    assert tokens > 10_000
