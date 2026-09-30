"""The release build: production steps must not change rendering, and must deliver what
they promise (Unicode glyph names, no PUA, sane vertical metrics, faithful web subset)."""
import shutil
import subprocess

import pytest
from fontTools import agl

from krishnatools.names import _is_pua, glyph_sequences
from krishnatools.web import WEB_FILE


def test_production_steps_render_identically(clusters, krishna, release):
    diffs = [c for c in clusters if krishna.signature(krishna.shape(c)) != release.signature(release.shape(c))]
    assert not diffs, diffs[:10]


def test_glyph_names_spell_their_text(release):
    """Every glyph that renders known text has a name that decodes to that text."""
    seq = glyph_sequences(release.tt)
    wrong = [(n, seq[n], agl.toUnicode(n)) for n in release.order
             if n in seq and not _is_pua(ord(seq[n][0])) and agl.toUnicode(n) != seq[n]]
    assert not wrong, wrong[:10]


def test_no_private_use_mappings_for_real_text(release):
    seq = glyph_sequences(release.tt)
    pua = [hex(cp) for cp, g in release.tt.getBestCmap().items()
           if _is_pua(cp) and not _is_pua(ord(seq[g][0]))]
    assert not pua, pua[:10]


def test_vertical_metrics(release):
    tt = release.tt
    os2, hhea, head = tt['OS/2'], tt['hhea'], tt['head']
    assert os2.version >= 4 and os2.fsSelection & (1 << 7), 'USE_TYPO_METRICS'
    assert (os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap) == (hhea.ascent, hhea.descent, hhea.lineGap)
    assert os2.usWinAscent >= head.yMax and os2.usWinDescent >= -head.yMin, 'Windows would clip ink'


def test_every_glyph_is_hinted(release):
    """Simple glyphs carry instructions (composites are hinted through their components)."""
    glyf = release.tt['glyf']
    unhinted = [n for n in release.order
                if glyf[n].numberOfContours > 0 and not (hasattr(glyf[n], 'program') and glyf[n].program.getBytecode())]
    assert not unhinted, unhinted[:10]


def test_web_subset_renders_identically(clusters, release, release_dir):
    """Compare by glyph name: glyph IDs differ in the subset. HarfBuzz can't read WOFF2,
    so decompress it first, as a browser does."""
    from fontTools.ttLib import TTFont
    from krishnatools.shaping import Shaper
    woff2 = TTFont(release_dir / 'web' / WEB_FILE)
    woff2.flavor = None
    web = Shaper(ttfont=woff2)

    def sig(shaper, c):
        return tuple((g.name, g.x_advance, g.x_offset, g.y_offset) for g in shaper.shape(c))
    diffs = [c for c in clusters if sig(release, c) != sig(web, c)]
    assert not diffs, diffs[:10]
    assert not any(0x41 <= cp <= 0x7A for cp in web.tt.getBestCmap()), 'Latin letters should be dropped'


SAMPLE = 'समृ॑द्ध्यै अ॒द्ध्व॒र्युः ब्ज क्त्रि॑ न्ति सु॒ ऋ॒द्धिः'
# Conjuncts that must survive copy-paste (ि and reph are in visual order in any PDF).
EXPECTED = ['समृ॑द्ध्यै', 'अ॒द्ध्व॒', 'ब्ज', 'क्त्र', 'सु॒', 'ऋ॒', 'द्ध']


@pytest.mark.skipif(not shutil.which('xelatex'), reason='needs xelatex')
def test_pdf_copy_paste_is_unicode(release_dir, tmp_path):
    pymupdf = pytest.importorskip('pymupdf')
    tex = tmp_path / 't.tex'
    tex.write_text('\\documentclass{article}\\usepackage{fontspec}'
                   f'\\newfontfamily\\A{{KrishnaSanskrit-Regular.ttf}}[Path={release_dir}/, Script=Devanagari]'
                   f'\\begin{{document}}\\A {SAMPLE}\\end{{document}}', 'utf-8')
    subprocess.run(['xelatex', '-interaction=nonstopmode', tex.name], cwd=tmp_path, check=True,
                   capture_output=True)
    text = pymupdf.open(tmp_path / 't.pdf')[0].get_text()
    assert not any(_is_pua(ord(ch)) for ch in text), repr(text)
    missing = [e for e in EXPECTED if e not in text]
    assert not missing, (missing, text)
