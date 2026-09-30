"""Web package: the WOFF2 plus a ready-to-use CSS snippet.

One file, not per-script subsets: Vedic transliteration puts Latin combining accents on
Devanāgarī-Extended letters (ꣳ̠), and a mark can only attach to a base in the same font
file, so splitting the font would detach those accents.
"""
import shutil
from pathlib import Path

from fontTools.ttLib import TTFont

FAMILY = 'Krishna Sanskrit'
WOFF2 = 'KrishnaSanskrit-Regular.woff2'
CSS_FILE = 'krishna-sanskrit.css'
UNICODE_RANGE = ('U+0000-036F, U+0900-097F, U+1AB0-1AFF, U+1CD0-1CFF, U+1D00-1EFF, U+2000-206F, '
                 'U+20A0-20C0, U+2122, U+2212, U+25CC, U+2C60-2C7F, U+A720-A7FF, U+A8E0-A8FF, U+AB30-AB6F')


def css(font, prefix=''):
    """@font-face with metric overrides so line boxes don't shift when the font loads."""
    upem = font['head'].unitsPerEm
    os2 = font['OS/2']
    pct = lambda v: f'{abs(v) / upem * 100:.2f}%'  # noqa: E731
    return f"""/* Krishna Sanskrit: Devanagari with Vedic accents, and Gentium Latin for transliteration.
   SIL Open Font License 1.1. https://github.com/iamsridhar/krishna-sanskrit */
@font-face {{
  font-family: '{FAMILY}';
  src: url('{prefix}{WOFF2}') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
  ascent-override: {pct(os2.sTypoAscender)};
  descent-override: {pct(os2.sTypoDescender)};
  line-gap-override: {pct(os2.sTypoLineGap)};
  unicode-range: {UNICODE_RANGE};
}}

/* Usage: .sanskrit {{ font-family: '{FAMILY}', serif; }} */
"""


def write_web_package(full_font_path, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    woff2 = Path(full_font_path).with_suffix('.woff2')
    shutil.copyfile(woff2, out_dir / WOFF2)
    (out_dir / CSS_FILE).write_text(css(TTFont(woff2)), 'utf-8')
    return out_dir
