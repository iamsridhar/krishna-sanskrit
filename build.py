"""Build Krishna Sanskrit from the upstream Sanskrit2020 binary.

    python build.py                 # release build -> build/KrishnaSanskrit-Regular.{ttf,woff2}
                                    #                + build/web/ (Devanagari-only WOFF2 + CSS)
    python build.py --upto p00      # stop after a given patch (used by the round-trip test)
    python build.py --out some.ttf  # custom output path (no woff2/web files)

The release build runs every patch, then the production steps:
  1. production glyph names + no PUA cmap entries (krishnatools.names), so text copied
     out of PDFs is real Unicode;
  2. ttfautohint over the whole font, so every glyph is hinted the same way.
Tests use the patched font *before* these steps (glyph names are the working names);
tests/test_release.py checks that the production steps change no shaping.
"""
import argparse
import hashlib
import io
from pathlib import Path

import ttfautohint
from fontTools.ttLib import TTFont

from krishnatools.names import rename
from krishnatools.web import write_web_package
from patches import PATCHES

REPO = Path(__file__).resolve().parent
UPSTREAM = REPO / 'upstream' / 'Sanskrit2020U.otf'
UPSTREAM_SHA256 = 'dfaf4ed323c7a42d5c4bf3f62182e5db5a99f1472ab137cb3f53a05d3c2e1bd9'
DEFAULT_OUT = REPO / 'build' / 'KrishnaSanskrit-Regular.ttf'


def check_upstream():
    digest = hashlib.sha256(UPSTREAM.read_bytes()).hexdigest()
    if digest != UPSTREAM_SHA256:
        raise SystemExit(f'{UPSTREAM} changed (sha256 {digest}); update UPSTREAM_SHA256 deliberately.')


def patched(upto=None):
    """Upstream with patches applied (working glyph names). Returns (TTFont, applied ids)."""
    check_upstream()
    font = TTFont(UPSTREAM)
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
        font = production(font)
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
