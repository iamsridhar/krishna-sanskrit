"""Render a before/after proof sheet (upstream Sanskrit2020 vs Krishna Sanskrit).

    python tools/proof.py --patch p10 [--top 60] [--extra 'त्रू॒ꣳ॒ ष्टुः॒'] [--png]

Clusters shown: the most frequent clusters in the patch's scope whose rendering changed,
plus any --extra clusters. Output: proofs/<patch>.html (and .png with --png).
"""
import argparse
import html
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from krishnatools.corpus import load_clusters  # noqa: E402
from krishnatools.shaping import Shaper  # noqa: E402
import build  # noqa: E402
from patches import PATCHES  # noqa: E402

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--patch', required=True)
    ap.add_argument('--top', type=int, default=60)
    ap.add_argument('--extra', default='')
    ap.add_argument('--png', action='store_true')
    args = ap.parse_args()
    patch = next(p for p in PATCHES if p.ID == args.patch)

    font_path, _ = build.build(woff2=False)
    up, aa = Shaper(build.UPSTREAM), Shaper(font_path)
    changed = [(c, n) for c, n in load_clusters().most_common()
               if patch.affects(c) and up.signature(up.shape(c)) != aa.signature(aa.shape(c))]
    rows = changed[:args.top] + [(c, 0) for c in args.extra.split()]

    cells = ''.join(
        f'<div class="cell"><span class="up">{html.escape(c)}</span><span class="aa">{html.escape(c)}</span>'
        f'<div class="meta">{n:,}×</div></div>' if n else
        f'<div class="cell extra"><span class="up">{html.escape(c)}</span><span class="aa">{html.escape(c)}</span>'
        f'<div class="meta">extra</div></div>'
        for c, n in rows)
    page = f"""<!doctype html><meta charset="utf-8"><title>{patch.ID} proof</title><style>
@font-face{{font-family:Up;src:url({build.UPSTREAM.as_uri()})}}
@font-face{{font-family:Aa;src:url({font_path.resolve().as_uri()})}}
body{{font:13px system-ui;background:#fbf8f1;margin:16px;width:1400px}}
#g{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}}
.cell{{background:#fff;border:1px solid #e3dccb;border-radius:6px;padding:4px 8px 2px;display:flex;justify-content:space-around;flex-wrap:wrap;line-height:1.6}}
.extra{{border-color:#b3261e}} .up{{font-family:Up;font-size:48px;color:#999}} .aa{{font-family:Aa;font-size:48px}}
.meta{{width:100%;text-align:center;color:#888;font-size:11px}}
</style><h3>{patch.ID}: {html.escape(patch.SUMMARY)}</h3>
<p>{len(changed):,} corpus clusters changed. Each cell: <span style="color:#999">upstream Sanskrit2020</span> → <b>Krishna Sanskrit</b>.</p>
<div id="g">{cells}</div>"""
    out = REPO / 'proofs' / f'{patch.ID}.html'
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, 'utf-8')
    print(out)
    if args.png:
        png = out.with_suffix('.png')
        height = 160 + 128 * ((len(rows) + 5) // 6)
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--allow-file-access-from-files',
                        f'--window-size=1440,{height}', f'--screenshot={png}', out.as_uri()],
                       check=True, capture_output=True)
        print(png)


if __name__ == '__main__':
    main()
