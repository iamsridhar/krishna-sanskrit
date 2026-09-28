"""Devanagari cluster segmentation and the committed test corpus."""
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLUSTERS_TSV = REPO / 'tests' / 'data' / 'clusters.tsv'

C = '[\u0915-\u0939\u0958-\u095F\u0978-\u097F]'
N = '\u093C?'
H = '\u094D'
V = '[\u0904-\u0914\u0960\u0961\u0972-\u0977]'
MARK_CHARS = (
    '\u0900-\u0903\u093A-\u094C\u094E\u094F\u0951-\u0957\u0962\u0963'
    '\u1CD0-\u1CFF\uA8E0-\uA8FF\u0300-\u036F\u200D'
)
MARKS = f'[{MARK_CHARS}]*'
CLUSTER = re.compile(f'(?:(?:{C}{N}{H}\u200D?)*{C}{N}(?:{H}(?!{C}))?|{V}){MARKS}')
CONSONANT_STACK = re.compile(f'(?:{C}{N}{H})+{C}{N}')


def segment(text):
    return CLUSTER.findall(text)


def load_clusters(path=CLUSTERS_TSV):
    counts = Counter()
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            if line.startswith('#') or not line.strip():
                continue
            cluster, n = line.rstrip('\n').split('\t')
            counts[cluster] = int(n)
    return counts


def write_clusters(counts, path=CLUSTERS_TSV, source=''):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(f'# cluster<TAB>count; {len(counts)} unique, {sum(counts.values())} tokens. {source}\n')
        for cluster, n in counts.most_common():
            fh.write(f'{cluster}\t{n}\n')


def conjuncts(counts):
    out = Counter()
    for cluster, n in counts.items():
        m = CONSONANT_STACK.match(cluster)
        if m:
            out[m.group(0)] += n
    return out
