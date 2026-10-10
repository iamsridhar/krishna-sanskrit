"""p40: anunāsika before y, v, l (य्ँय व्ँव ल्ँल) renders as the joined conjunct.

The sequence spans two syllables, so the per-cluster corpus tests can't see it; these
check real words from the Taittirīya texts (3,341 occurrences), in HarfBuzz and, with
KRISHNA_ENGINES=1 on macOS, CoreText.
"""
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

WORDS = [
    'र॒जव॒व्ँवा', 'यव्ँवा', 'पा॒पव॑य्ँया', 'ताल्ँलो॒क',     # + vowel sign
    'व्ँवा॑', 'य्ँयो॒', 'व्ँवृ', 'व्ँवै', 'व्ँव॒',          # accents, below vowel, ai
    'व्ँवि', 'य्ँयि', 'ल्ँलि', 'व्ँविं', 'य्ँयिँ', 'व्ँवि॑',  # i-matra (and its merged forms)
]
# The second consonant starts a further conjunct: the font fuses that syllable, so p40
# leaves the sequence alone (it shows the half form + candrabindu as before).
UNTOUCHED = ['व्ँव्र॒', 'व्ँव्या', 'व्ँव्य॑']


def _names(shaper, text):
    return [g.name for g in shaper.shape(text)]


@pytest.mark.parametrize('word', WORDS)
def test_joined_conjunct_without_visible_virama(krishna, word):
    names = _names(krishna, word)
    assert any('.cb' in n for n in names), names
    assert krishna.virama not in [g.gid for g in krishna.shape(word)], names
    assert 'uni0901' not in names, names  # the candrabindu is drawn inside the conjunct glyph


@pytest.mark.parametrize('word', ['व्ँवि', 'य्ँयि', 'ल्ँलि'])
def test_i_matra_matches_plain_conjunct(krishna, word):
    """व्ँवि uses the same i-matra as व्वि, then the conjunct."""
    plain = word.replace('ँ', '')
    assert _names(krishna, word)[0] == _names(krishna, plain)[0]


@pytest.mark.parametrize('word', ['व्ँवि', 'य्ँयि', 'ल्ँलि', 'व्ँविं', 'व्ँवि॑'])
def test_i_matra_candrabindu_clears_the_arc(krishna, word):
    """With ि the candrabindu is lifted so it sits above the i-matra arc, not inside it."""
    glyf = krishna.tt['glyf']
    imatra, conj = _names(krishna, word)[:2]
    assert conj.endswith('.cb.i'), conj
    for n in (imatra, conj, 'uni0901'):
        glyf[n].recalcBounds(glyf)
    cb_height = glyf['uni0901'].yMax - glyf['uni0901'].yMin
    arc_top = glyf[_names(krishna, word.replace('ं', ''))[0]].yMax
    assert glyf[conj].yMax - cb_height >= arc_top - 1


@pytest.mark.parametrize('word', ['र॒जव॒व्ँवा', 'व्ँवी', 'व्ँवै'])
def test_candrabindu_at_headline_without_i_matra(krishna, word):
    assert any(n.endswith('.cb') for n in _names(krishna, word))


@pytest.mark.parametrize('word', UNTOUCHED)
def test_further_conjuncts_untouched(upstream, krishna, word):
    assert not any('.cb' in n for n in _names(krishna, word))


@pytest.mark.skipif(sys.platform != 'darwin' or not shutil.which('swiftc') or not os.environ.get('KRISHNA_ENGINES'),
                    reason='CoreText comparison needs macOS + swiftc; enable with KRISHNA_ENGINES=1')
def test_coretext_matches_harfbuzz(krishna):
    from tools.compare_engines import BIN, REPO
    if not BIN.exists():
        subprocess.run(['swiftc', '-O', str(REPO / 'tools' / 'coretext_shape.swift'), '-o', str(BIN)], check=True)
    words = WORDS + UNTOUCHED
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as fh:
        fh.write('\n'.join(words))
    out = subprocess.run([str(BIN), krishna.path, fh.name], check=True, capture_output=True, text=True).stdout
    os.unlink(fh.name)
    for word, line in zip(words, out.split('\n')):
        ct = [krishna.order[int(t.split(':')[0])] for t in line.split()]
        assert ct == _names(krishna, word), (word, ct, _names(krishna, word))
