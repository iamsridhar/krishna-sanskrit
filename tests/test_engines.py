"""CoreText (Safari/macOS) must render every corpus cluster the way HarfBuzz does, except
where upstream Sanskrit2020 already differs. macOS only, ~40 s: KRISHNA_ENGINES=1 pytest"""
import os
import shutil
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != 'darwin' or not shutil.which('swiftc') or not os.environ.get('KRISHNA_ENGINES'),
    reason='CoreText comparison needs macOS + swiftc; enable with KRISHNA_ENGINES=1')


def test_no_new_coretext_differences(clusters, krishna):
    from tools.compare_engines import compare
    import build
    listing = list(clusters)
    new = compare(krishna.path, listing) - compare(build.UPSTREAM, listing)
    assert not new, sorted(new, key=lambda c: -clusters[c])[:20]
