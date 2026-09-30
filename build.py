"""Build Krishna Sanskrit from the upstream Sanskrit2020 binary.

    python build.py                 # release build -> build/KrishnaSanskrit-Regular.{ttf,woff2}
                                    #                + build/web/ (split WOFF2 subsets + CSS)
    python build.py --upto p00      # stop after a given patch (used by the round-trip test)
    python build.py --out some.ttf  # custom output path (no woff2/web files)

Source fonts are downloaded from their official releases and verified by SHA-256
(krishnatools.upstream). The release build then:
  1. applies every patch in patches/ to Sanskrit2020 (Devanāgarī fixes);
  2. replaces the bundled URW Latin with Gentium Medium Latin (krishnatools.latin);
  3. applies the final patches (vertical metrics over the merged font);
  4. production: glyph names that spell their text + no PUA cmap entries
     (krishnatools.names), so text copied out of PDFs is Unicode; then ttfautohint.
Tests use the patched font *before* steps 2-4 (working glyph names); tests/test_release.py
checks that steps 2-4 change no Devanāgarī rendering and that the Latin works.
"""
import argparse
import io
from pathlib import Path

import ttfautohint
from fontTools.ttLib import TTFont

from krishnatools import upstream
from krishnatools.latin import compose
from krishnatools.names import rename
from krishnatools.web import write_web_package
from patches import FINAL_PATCHES, PATCHES

REPO = Path(__file__).resolve().parent
UPSTREAM = upstream.UPSTREAM_DIR / 'Sanskrit2020U.otf'
DEFAULT_OUT = REPO / 'build' / 'KrishnaSanskrit-Regular.ttf'


def patched(upto=None):
    """Sanskrit2020 with the Devanāgarī patches applied (working glyph names).
    Returns (TTFont, applied ids)."""
    font = TTFont(upstream.path('Sanskrit2020U.otf'))
    applied = []
    for patch in PATCHES:
        patch.apply(font)
        applied.append(patch.ID)
        if patch.ID == upto:
            break
    else:
        if upto:
            raise SystemExit(f'Unknown patch id {upto!r}')
    return font, applied


def finish(font):
    """Gentium Latin merged in, then the final patches. Returns a new TTFont."""
    font = compose(font)
    for patch in FINAL_PATCHES:
        patch.apply(font)
    return font


def production(font):
    """Production names, no PUA, whole-font ttfautohint. Returns a new TTFont."""
    named, _, _ = rename(font)
    buf = io.BytesIO()
    named.save(buf)
    hinted = ttfautohint.ttfautohint(in_buffer=buf.getvalue(), default_script='deva',
                                     fallback_script='latn', windows_compatibility=False)
    return TTFont(io.BytesIO(hinted))


def build(out=DEFAULT_OUT, upto=None, woff2=True, release=True):
    """Write a font. `release` (full builds only) adds the production steps."""
    font, applied = patched(upto)
    if release and upto is None:
        font = production(finish(font))
        applied += ['latin'] + [p.ID for p in FINAL_PATCHES]
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    font.save(out)
    if woff2:
        font.flavor = 'woff2'
        font.save(out.with_suffix('.woff2'))
        font.flavor = None
        write_web_package(out, out.parent / 'web')
    return out, applied


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--upto')
    ap.add_argument('--out', default=str(DEFAULT_OUT))
    args = ap.parse_args()
    out, applied = build(args.out, args.upto, woff2=args.out == str(DEFAULT_OUT))
    print(f'{out} ({", ".join(applied)}{", production" if args.upto is None else ""})')


if __name__ == '__main__':
    main()
