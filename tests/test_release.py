"""The release build: the Latin merge and production steps must not change Devanāgarī
rendering, the Gentium Latin must render the ISO transliteration exactly as Gentium does,
and the build must deliver what it promises (Unicode glyph names, no PUA, sane vertical
metrics, sanitizer-clean files, faithful web subsets, Unicode text in PDFs)."""
import shutil
import subprocess
import unicodedata

import pytest
from fontTools import agl
from fontTools.ttLib import TTFont

from krishnatools import upstream
from krishnatools.corpus import ISO_CLUSTERS_TSV, load_clusters
from krishnatools.latin import latin_scale
from krishnatools.names import _is_pua, glyph_sequences
from krishnatools.shaping import Shaper
from krishnatools.web import CSS_FILE, WOFF2


def _transliteration(cluster):
    """Latin clusters proper: the ISO JSON also holds a few stray Devanagari signs and
    C1 control codes (mis-encoded quotes) that no font can render meaningfully."""
    return not cluster[0].isspace() and not any(
        '\u0900' <= ch <= '\u0DFF' or unicodedata.category(ch) == 'Cc' for ch in cluster)


@pytest.fixture(scope='session')
def iso_clusters():
    return [c for c in load_clusters(ISO_CLUSTERS_TSV) if _transliteration(c)]


def _woff2(path):
    """HarfBuzz can't read WOFF2; decompress first, as a browser does."""
    font = TTFont(path)
    font.flavor = None
    return Shaper(ttfont=font)


def test_devanagari_renders_identically_after_latin_merge_and_production(clusters, krishna, release):
    diffs = [c for c in clusters
             if krishna.outline_signature(krishna.shape(c)) != release.outline_signature(release.shape(c))]
    assert not diffs, diffs[:10]


def test_iso_transliteration_has_every_glyph(iso_clusters, release):
    bad = [c for c in iso_clusters if {'missing', 'dotted'} & release.issues(c)]
    assert not bad, bad[:10]


def test_iso_accents_placed_exactly_as_gentium(iso_clusters, release):
    """Every letter + combining-accent cluster is positioned as Gentium Medium positions it
    (scaled to Krishna Sanskrit's x-height)."""
    gentium, k = Shaper(upstream.path('Gentium-Medium.ttf')), latin_scale()
    in_gentium = set(gentium.tt.getBestCmap())
    off = []
    for c in iso_clusters:
        if not all(ord(ch) in in_gentium for ch in c):
            continue  # e.g. ꣳ̠: Devanagari-Extended base, see test_accents_centred_on_vedic_anusvara
        ours, theirs = release.shape(c), gentium.shape(c)
        if len(ours) != len(theirs) or any(
                abs(a.x_offset - b.x_offset * k) > 3 or abs(a.y_offset - b.y_offset * k) > 3
                or abs(a.x_advance - b.x_advance * k) > 3 for a, b in zip(ours, theirs)):
            off.append(c)
    assert not off, off[:10]


def test_credits_every_source(release):
    notice = release.tt['name'].getDebugName(0)
    for holder in ('Krishna Sanskrit Project', 'Omkarananda Ashram Himalayas', 'IIT Bombay', 'SIL Global'):
        assert holder in notice
    assert 'URW' not in notice
    cmap = release.tt.getBestCmap()
    assert ord('a') in cmap and 0x0320 in cmap and 0x0915 in cmap


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
    assert hhea.lineGap == 0
    assert os2.usWinAscent >= head.yMax and os2.usWinDescent >= -head.yMin, 'Windows would clip ink'


@pytest.mark.parametrize('path', ['KrishnaSanskrit-Regular.ttf', 'KrishnaSanskrit-Regular.woff2', f'web/{WOFF2}'])
def test_passes_opentype_sanitizer(release_dir, tmp_path, path):
    """OTS is what browsers run on web fonts; it must accept every file we ship."""
    ots = pytest.importorskip('ots')
    result = ots.sanitize(str(release_dir / path), str(tmp_path / 'out'), capture_output=True)
    assert result.returncode == 0, (result.stdout + result.stderr).decode()[:500]


def test_every_glyph_is_hinted(release):
    """Simple glyphs carry instructions (composites are hinted through their components)."""
    glyf = release.tt['glyf']
    unhinted = [n for n in release.order
                if glyf[n].numberOfContours > 0 and not (hasattr(glyf[n], 'program') and glyf[n].program.getBytecode())]
    assert not unhinted, unhinted[:10]


def test_web_package(release_dir):
    web = release_dir / 'web'
    assert (web / WOFF2).read_bytes() == (release_dir / WOFF2).read_bytes()
    css = (web / CSS_FILE).read_text()
    assert WOFF2 in css and 'unicode-range' in css and "'Krishna Sanskrit'" in css


def test_accents_centred_on_vedic_anusvara(release):
    """ꣳ̠ / ꣴ̠ (13,000+ in the ISO corpus): the accent hangs centred below the sign."""
    for text in ('ꣳ̠', 'ꣴ̠', 'saꣳ̠'):
        base, mark = release.shape(text)[-2:]
        assert mark.bbox and base.bbox
        centre = lambda b: (b[0] + b[2]) / 2  # noqa: E731
        assert abs(centre(mark.bbox) - centre(base.bbox)) < 60, text
        assert mark.bbox[3] < max(base.bbox[1], 0), text


SAMPLE = 'समृ॑द्ध्यै अ॒द्ध्व॒र्युः ब्ज क्त्रि॑ न्ति सु॒ ऋ॒द्धिः — śrēṣṭha̍tamāya̠ r̥̍ṣi̠bhyaḥ'
# Must survive copy-paste (ि and reph are in visual order in any PDF).
EXPECTED = ['समृ॑द्ध्यै', 'अ॒द्ध्व॒', 'ब्ज', 'क्त्र', 'सु॒', 'ऋ॒', 'द्ध', 'śrēṣṭha', 'r̥']


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
