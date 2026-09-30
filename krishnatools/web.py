"""Web package: a Devanagari-only WOFF2 and a ready-to-use CSS snippet.

The web subset keeps every Devanagari / Vedic / Devanagari Extended character with all of
their OpenType layout (the subsetter follows GSUB closure, so every conjunct, i-matra
variant and accent form stays), and drops the Latin glyphs, which the site never uses
through this font.
"""
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

FAMILY = 'Krishna Sanskrit'
WEB_FILE = 'KrishnaSanskrit-Devanagari.woff2'
UNICODES = [
    *range(0x0900, 0x0980),   # Devanagari
    *range(0x1CD0, 0x1D00),   # Vedic Extensions
    *range(0xA8E0, 0xA900),   # Devanagari Extended
    0x200C, 0x200D,           # ZWNJ, ZWJ (conjunct control)
    0x25CC,                   # dotted circle (shown for malformed clusters)
    0x0020, 0x00A0,           # space, no-break space
]
UNICODE_RANGE = 'U+0900-097F, U+1CD0-1CFF, U+A8E0-A8FF, U+200C-200D, U+25CC'


def subset_font(src, dst):
    options = subset.Options()
    options.layout_features = ['*']
    options.layout_scripts = ['*']
    options.name_IDs = ['*']
    options.name_languages = ['*']
    options.glyph_names = True
    options.notdef_outline = True
    options.hinting = True
    options.flavor = 'woff2'
    font = TTFont(src)
    sub = subset.Subsetter(options)
    sub.populate(unicodes=UNICODES)
    sub.subset(font)
    font.flavor = 'woff2'
    font.save(dst)
    return font


def css(font):
    """@font-face with metric overrides so line boxes don't shift when the font loads."""
    upem = font['head'].unitsPerEm
    os2 = font['OS/2']
    pct = lambda v: f'{abs(v) / upem * 100:.2f}%'  # noqa: E731
    return f"""/* Krishna Sanskrit, Devanagari-only web subset. SIL Open Font License 1.1. */
@font-face {{
  font-family: '{FAMILY}';
  src: url('{WEB_FILE}') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
  ascent-override: {pct(os2.sTypoAscender)};
  descent-override: {pct(os2.sTypoDescender)};
  line-gap-override: {pct(os2.sTypoLineGap)};
  unicode-range: {UNICODE_RANGE};
}}

/* Usage: put Krishna first; the Latin fallback renders any non-Devanagari text.
   .sanskrit {{ font-family: '{FAMILY}', 'Noto Serif Devanagari', serif; }} */
"""


def write_web_package(full_font_path, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    font = subset_font(full_font_path, out_dir / WEB_FILE)
    (out_dir / 'krishna-sanskrit.css').write_text(css(font), 'utf-8')
    return out_dir / WEB_FILE
