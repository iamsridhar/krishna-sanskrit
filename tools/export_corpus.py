"""Regenerate tests/data/clusters.tsv from the generated Veda HTML in the sriiyer.com repo.

    python tools/export_corpus.py [--site ~/code/sriiyerNew]
"""
import argparse
import glob
import html
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from krishnatools.corpus import segment, write_clusters  # noqa: E402

SECTIONS = ['samhita', 'brahmana', 'aranyaka', 'kathakam', 'pada', 'krama', 'ekagnikandam', 'suktani']
SPAN = re.compile(r'class="script-devanagari">(.*?)</span>', re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', default=str(Path.home() / 'code' / 'sriiyerNew'))
    args = ap.parse_args()
    counts, files = Counter(), 0
    for section in SECTIONS:
        for f in sorted(glob.glob(f'{args.site}/veda/{section}/*.html')):
            files += 1
            for m in SPAN.finditer(Path(f).read_text('utf-8')):
                counts.update(segment(html.unescape(re.sub('<[^>]+>', '', m.group(1)))))
    if not counts:
        sys.exit(f'No Devanagari found under {args.site}/veda — run the site build first.')
    write_clusters(counts, source=f'From {files} Veda HTML pages of sriiyer.com.')
    print(f'{len(counts):,} unique clusters, {sum(counts.values()):,} tokens from {files} pages')


if __name__ == '__main__':
    main()
