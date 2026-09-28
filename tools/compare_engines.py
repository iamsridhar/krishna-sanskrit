"""Compare CoreText (Safari/macOS) shaping with HarfBuzz (Chrome/Firefox/XeTeX) over the corpus.

    python tools/compare_engines.py

Reports, for upstream Sanskrit2020 and for the Krishna build, how many corpus clusters the
two engines render differently, and whether any clusters changed by Krishna's patches
differ between engines (the important number: it should be 0 beyond upstream's own).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from krishnatools.corpus import load_clusters  # noqa: E402
from krishnatools.shaping import Shaper  # noqa: E402
import build  # noqa: E402
from patches import PATCHES  # noqa: E402

BIN = REPO / 'build' / 'coretext_shape'
TOLERANCE = 2  # font units; CoreText rounds positions


def coretext(font, clusters):
    if not BIN.exists() or BIN.stat().st_mtime < (REPO / 'tools' / 'coretext_shape.swift').stat().st_mtime:
        subprocess.run(['swiftc', '-O', str(REPO / 'tools' / 'coretext_shape.swift'), '-o', str(BIN)], check=True)
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as fh:
        fh.write('\n'.join(clusters))
    out = subprocess.run([str(BIN), str(font), fh.name], check=True, capture_output=True, text=True).stdout
    Path(fh.name).unlink()
    rows = []
    for line in out.split('\n')[:len(clusters)]:
        rows.append([tuple(t.rstrip('!').split(':')) + (t.endswith('!'),) for t in line.split()])
    return rows


def harfbuzz(shaper, cluster):
    x, out = 0, []
    for info in shaper.shape(cluster):
        out.append((info.gid, x + info.x_offset, info.y_offset, info.name))
        x += info.x_advance
    return out


def same(hb_glyphs, ct_glyphs, ignorable):
    hb_glyphs = [g for g in hb_glyphs if g[0] not in ignorable]
    ct_glyphs = [g for g in ct_glyphs if int(g[0]) not in ignorable]
    if any(g[3] for g in ct_glyphs) or len(hb_glyphs) != len(ct_glyphs):
        return False
    return all(h[0] == int(c[0]) and abs(h[1] - int(c[1])) <= TOLERANCE and abs(h[2] - int(c[2])) <= TOLERANCE
               for h, c in zip(hb_glyphs, ct_glyphs))


def compare(font, clusters):
    shaper = Shaper(font)
    ignorable = {shaper.tt.getReverseGlyphMap()[g] for g in ('space',) if g in shaper.tt.getReverseGlyphMap()}
    ct = coretext(font, clusters)
    return {c for c, row in zip(clusters, ct) if not same(harfbuzz(shaper, c), row, ignorable)}


def main():
    counts = load_clusters()
    clusters = list(counts)
    font, _ = build.build(woff2=False)
    up_diff = compare(build.UPSTREAM, clusters)
    aa_diff = compare(font, clusters)
    changed = [c for c in clusters if any(p.affects(c) for p in PATCHES)]
    tok = lambda s: sum(counts[c] for c in s)
    print(f'{len(clusters):,} clusters, {sum(counts.values()):,} tokens')
    print(f'upstream: CoreText != HarfBuzz for {len(up_diff):,} clusters ({tok(up_diff):,} tokens)')
    print(f'krishna:    CoreText != HarfBuzz for {len(aa_diff):,} clusters ({tok(aa_diff):,} tokens)')
    new = sorted(aa_diff - up_diff, key=lambda c: -counts[c])
    print(f'new engine differences introduced by Krishna: {len(new):,} clusters ({tok(new):,} tokens)')
    for c in new[:25]:
        print(f'  {c}\t{counts[c]}')
    fixed = up_diff - aa_diff
    print(f'engine differences Krishna removed: {len(fixed):,}')
    print(f'patched clusters that differ between engines: {len(set(changed) & aa_diff):,} of {len(changed):,}')
    return 1 if new else 0


if __name__ == '__main__':
    sys.exit(main())
