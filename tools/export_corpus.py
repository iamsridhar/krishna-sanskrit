"""Regenerate the test corpora from the sriiyer.com repo (after its site build):

- tests/data/clusters.tsv: every Devanagari cluster in the generated Veda HTML;
- tests/data/iso_clusters.tsv: every non-ASCII Latin cluster (letter + combining accents)
  in the ISO-15919 transliteration JSON.

    python tools/export_corpus.py [--site ~/code/sriiyerNew]
"""
import argparse
import glob
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from krishnatools.corpus import ISO_CLUSTERS_TSV, latin_clusters, segment, write_clusters  # noqa: E402

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

    iso, jsons = Counter(), 0
    for f in sorted(glob.glob(f'{args.site}/content/veda/*/iso/*.json')):
        jsons += 1
        stack = [json.loads(Path(f).read_text('utf-8'))]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, str):
                iso.update(latin_clusters(node))
    write_clusters(iso, path=ISO_CLUSTERS_TSV, source=f'Latin clusters from {jsons} ISO-15919 JSON files.')
    print(f'{len(iso):,} unique ISO clusters, {sum(iso.values()):,} tokens from {jsons} files')


if __name__ == '__main__':
    main()
