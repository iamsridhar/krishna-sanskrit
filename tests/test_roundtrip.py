"""The build pipeline itself must not change rendering: rename-only == upstream."""


def test_rename_only_build_renders_identically(clusters, upstream, renamed):
    diffs = [c for c in clusters if upstream.signature(upstream.shape(c)) != renamed.signature(renamed.shape(c))]
    assert not diffs, f'{len(diffs)} clusters render differently after rename only, e.g. {diffs[:10]}'


def test_rename_only_keeps_glyphs_and_cmap(upstream, renamed):
    assert upstream.order == renamed.order
    assert upstream.tt.getBestCmap() == renamed.tt.getBestCmap()
    for name in upstream.order:
        assert upstream._ink_bbox(name) == renamed._ink_bbox(name), name


def test_names(renamed):
    names = renamed.tt['name']
    assert names.getDebugName(1) == 'Krishna Sanskrit'
    assert names.getDebugName(6) == 'KrishnaSanskrit-Regular'
    assert 'Omkarananda Ashram Himalayas' in names.getDebugName(0)
    assert 'URW' in names.getDebugName(0)
    assert 'Sanskrit2020' in names.getDebugName(10)
    assert 'Open Font License' in names.getDebugName(13)
    assert not any('Sanskrit 2020' in (r.toUnicode()) for r in names.names if r.nameID in (1, 4, 6, 16))
