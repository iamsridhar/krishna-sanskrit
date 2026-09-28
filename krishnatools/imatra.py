"""How far a pre-base i-matra has to reach across a conjunct.

Sanskrit2020's single i-matra is designed to reach the stem of one consonant. Before a
conjunct its hook should reach the *final* consonant the same way, so the extra reach
needed is the width of everything in front of the final consonant:

    delta = advance(base glyph run after the i-matra) - advance(final consonant alone)
"""
import re

I_GLYPHS = ['uni093F', 'ziM', 'ziMM', 'rzi', 'rziM', 'rziMM']  # i, i+anusvara, i+candrabindu, reph+i...
_STRIP = re.compile('[\u0900-\u0903\u0951-\u0954\u1CD0-\u1CFF\uA8E0-\uA8FF\u0300-\u036F]')
_FINAL = re.compile('[\u0915-\u0939]\u093C?(?:\u094D\u0930)?$')
CONSONANTS = [chr(c) for c in range(0x0915, 0x093A)]
# Spacing signs that follow the consonant cluster but are not part of what the hook spans.
YOGAVAHAS = [0x0903, 0xA8F3, 0xA8F4, 0x1CF2, 0x1CF3, 0x1CF5, 0x1CF6, 0x093D, 0x0964, 0x0965]
# HarfBuzz renders ZWJ/ZWNJ as a zero-width space glyph and skips it in GSUB contexts.
IGNORABLE = ['space']


def final_consonant(cluster):
    """Text of the consonant the i-matra hook should land on (keeps a trailing rakar)."""
    core = _STRIP.sub('', cluster.split('\u093F')[0])
    m = _FINAL.search(core)
    return m.group(0) if m else None


def base_run(shaper, glyphs):
    """The consonant glyphs the i-matra spans: after it, up to the first mark or yogavaha."""
    stop = getattr(shaper, '_yogavaha_glyphs', None)
    if stop is None:
        cmap = shaper.tt.getBestCmap()
        stop = shaper._yogavaha_glyphs = {cmap[c] for c in YOGAVAHAS if c in cmap}
    out = []
    for g in glyphs:
        if g.name in I_GLYPHS or g.name.split('.')[0] in I_GLYPHS or g.name in IGNORABLE:
            continue
        if g.name in shaper.marks or g.name in stop:
            if out:
                break
            continue
        out.append(g)
    return out


def required_reach(shaper, cluster, cache=None):
    """(base run, delta) for a cluster containing an i-matra, or None."""
    final = final_consonant(cluster)
    if not final:
        return None
    cache = {} if cache is None else cache
    if final not in cache:
        cache[final] = sum(g.x_advance for g in shaper.shape(final) if g.name not in shaper.marks)
    run = base_run(shaper, shaper.shape(cluster))
    if not run:
        return None
    return run, sum(g.x_advance for g in run) - cache[final]


def attested_pairs(corpus):
    """Consonant pairs that occur adjacent inside a conjunct somewhere in the corpus."""
    from .corpus import conjuncts
    pairs = set()
    for c in conjuncts(corpus):
        cs = re.findall('[\u0915-\u0939]', c)
        pairs |= set(zip(cs, cs[1:]))
    return pairs


def attested_chains(corpus, length):
    """Every `length`-consonant cluster whose adjacent pairs are all attested."""
    nxt = {}
    for a, b in attested_pairs(corpus):
        nxt.setdefault(a, set()).add(b)
    chains = [[a] for a in sorted(nxt)]
    for _ in range(length - 1):
        chains = [c + [b] for c in chains for b in sorted(nxt.get(c[-1], ()))]
    return ['\u094D'.join(c) for c in chains]


def candidate_clusters(corpus):
    """Clusters to learn i-matra reach from: corpus conjuncts with an i-matra, every
    generated 2- and 3-consonant cluster, and every 4-consonant cluster built from
    consonant pairs attested in the corpus (~37k)."""
    out = [c for c in corpus if '\u093F' in c and '\u094D' in c]
    for a in CONSONANTS:
        for b in CONSONANTS:
            out.append(f'{a}\u094D{b}\u093F')
            out.extend(f'{a}\u094D{b}\u094D{c}\u093F' for c in CONSONANTS)
    out.extend(f'{c}\u093F' for c in attested_chains(corpus, 4))
    return out
