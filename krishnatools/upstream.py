"""Third-party source fonts, fetched from their official releases and pinned by SHA-256.

They are not committed to this repository: the build downloads them into upstream/ on
first use and refuses to run if a file's hash ever differs.
"""
import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

UPSTREAM_DIR = Path(__file__).resolve().parent.parent / 'upstream'

SOURCES = {
    'Sanskrit2020U.otf': {
        'url': 'https://sourceforge.net/projects/advaita-sharada-font/files/Devanagari/Sanskrit2020U.otf/download',
        'sha256': 'dfaf4ed323c7a42d5c4bf3f62182e5db5a99f1472ab137cb3f53a05d3c2e1bd9',
    },
    'Shobhika-Regular.otf': {
        'url': 'https://github.com/Sandhi-IITBombay/Shobhika/releases/download/v1.05/Shobhika-1.05.zip',
        'member': 'Shobhika-1.05/Shobhika-Regular.otf',
        'sha256': 'bde48974337ea665b930d956c26d0b3884f1bc0549769bfb7d82caa3e0af181f',
    },
    'Gentium-Medium.ttf': {
        'url': 'https://github.com/silnrsi/font-gentium/releases/download/v7.000/Gentium-7.000.zip',
        'member': 'Gentium-7.000/Gentium-Medium.ttf',
        'sha256': '658ba723e1e76345b5397fabe73456fe65147e7da1ba4aa5751b956ebaf519e4',
    },
}


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def path(name):
    """Local path of a verified source font, downloading it first if needed."""
    src = SOURCES[name]
    dest = UPSTREAM_DIR / name
    if dest.exists() and _sha256(dest.read_bytes()) == src['sha256']:
        return dest
    request = urllib.request.Request(src['url'], headers={'User-Agent': 'krishna-sanskrit-build'})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    if 'member' in src:
        data = zipfile.ZipFile(io.BytesIO(data)).read(src['member'])
    digest = _sha256(data)
    if digest != src['sha256']:
        raise SystemExit(f'{name} from {src["url"]} has sha256 {digest}, expected {src["sha256"]}')
    UPSTREAM_DIR.mkdir(exist_ok=True)
    dest.write_bytes(data)
    return dest


def fetch_all():
    return {name: path(name) for name in SOURCES}


if __name__ == '__main__':
    for name, p in fetch_all().items():
        print(f'{name}: {p}')
