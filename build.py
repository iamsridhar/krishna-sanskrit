"""Build Krishna Sanskrit from the upstream Sanskrit2020 binary.

    python build.py                 # all patches -> build/KrishnaSanskrit-Regular.{ttf,woff2}
    python build.py --upto p00      # stop after a given patch (used by the round-trip test)
    python build.py --out some.ttf  # custom output path (no woff2)
"""
import argparse
import hashlib
from pathlib import Path

from fontTools.ttLib import TTFont

from patches import PATCHES

REPO = Path(__file__).resolve().parent
UPSTREAM = REPO / 'upstream' / 'Sanskrit2020U.otf'
UPSTREAM_SHA256 = 'dfaf4ed323c7a42d5c4bf3f62182e5db5a99f1472ab137cb3f53a05d3c2e1bd9'
DEFAULT_OUT = REPO / 'build' / 'KrishnaSanskrit-Regular.ttf'


def check_upstream():
    digest = hashlib.sha256(UPSTREAM.read_bytes()).hexdigest()
    if digest != UPSTREAM_SHA256:
        raise SystemExit(f'{UPSTREAM} changed (sha256 {digest}); update UPSTREAM_SHA256 deliberately.')


def build(out=DEFAULT_OUT, upto=None, woff2=True):
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
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    font.save(out)
    if woff2:
        font.flavor = 'woff2'
        font.save(out.with_suffix('.woff2'))
    return out, applied


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--upto')
    ap.add_argument('--out', default=str(DEFAULT_OUT))
    args = ap.parse_args()
    out, applied = build(args.out, args.upto, woff2=args.out == str(DEFAULT_OUT))
    print(f'{out} ({", ".join(applied)})')


if __name__ == '__main__':
    main()
