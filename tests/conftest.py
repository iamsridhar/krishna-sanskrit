import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from krishnatools.corpus import load_clusters  # noqa: E402
from krishnatools.shaping import Shaper  # noqa: E402
import build  # noqa: E402


@pytest.fixture(scope='session')
def clusters():
    return load_clusters()


@pytest.fixture(scope='session')
def upstream():
    return Shaper(build.UPSTREAM)


@pytest.fixture(scope='session')
def renamed(tmp_path_factory):
    out, _ = build.build(tmp_path_factory.mktemp('p00') / 'renamed.ttf', upto='p00', woff2=False)
    return Shaper(out)


@pytest.fixture(scope='session')
def krishna(tmp_path_factory):
    """All patches, working glyph names (before the release/production steps)."""
    out, _ = build.build(tmp_path_factory.mktemp('full') / 'KrishnaSanskrit-Regular.ttf', woff2=False, release=False)
    return Shaper(out)


@pytest.fixture(scope='session')
def release_dir(tmp_path_factory):
    """Full release build: production names, no PUA, ttfautohint, WOFF2, web subset."""
    out, _ = build.build(tmp_path_factory.mktemp('release') / 'KrishnaSanskrit-Regular.ttf')
    return out.parent


@pytest.fixture(scope='session')
def release(release_dir):
    return Shaper(release_dir / 'KrishnaSanskrit-Regular.ttf')


@pytest.fixture(scope='session')
def shaped(clusters, upstream, krishna):
    """(cluster, count, upstream glyphs, krishna glyphs) for the whole corpus, shaped once."""
    return [(c, n, upstream.shape(c), krishna.shape(c)) for c, n in clusters.items()]
