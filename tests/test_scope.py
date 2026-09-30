"""Every rendering change must be claimed by some patch's affects() predicate."""
from patches import PATCHES


def test_only_declared_clusters_change(shaped, upstream, krishna):
    unexpected = [
        (c, n) for c, n, u, a in shaped
        if upstream.signature(u) != krishna.signature(a) and not any(p.affects(c) for p in PATCHES)
    ]
    unexpected.sort(key=lambda x: -x[1])
    assert not unexpected, f'{len(unexpected)} undeclared changes, e.g. {unexpected[:10]}'


def test_each_patch_changes_something(shaped, upstream, krishna):
    for patch in PATCHES:
        if not getattr(patch, 'CHANGES_RENDERING', True):
            continue
        changed = sum(1 for c, _, u, a in shaped if patch.affects(c) and upstream.signature(u) != krishna.signature(a))
        assert changed, f'{patch.ID} declares a scope but changed nothing'
