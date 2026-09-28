"""Serve the sriiyer.com site twice for side-by-side review, without touching its files.

    python tools/preview_site.py [--site ~/code/sriiyerNew] [--port 8800]

    http://localhost:8800/...   the site exactly as it is
    http://localhost:8801/...   the same site with Krishna Sanskrit as the Devanagari font

On the Krishna port, CSS/HTML responses are rewritten on the fly: every Devanagari
font stack that names Shobhika or Sanskrit2020 uses 'Krishna Sanskrit' instead, and
the Shobhika-specific faux-weight (-webkit-text-stroke) is dropped. JS font loaders
that fetch Sanskrit2020U.otf get the Krishna build. The font is served from build/.
"""
import argparse
import re
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUILD = REPO / 'build'
FONT_URL = '/__krishna/KrishnaSanskrit-Regular.woff2'
FONT_FACE = (
    "@font-face{font-family:'Krishna Sanskrit';"
    f"src:url('{FONT_URL}') format('woff2');font-display:block;"
    "unicode-range:U+0900-097F,U+1CD0-1CFF,U+A8E0-A8FF,U+200C-200D,U+25CC;}\n"
)
BADGE = (
    '<div style="position:fixed;z-index:99999;right:12px;bottom:12px;padding:6px 10px;'
    'font:600 12px system-ui;color:#fff;background:#7A2A17;border-radius:6px;'
    'box-shadow:0 2px 8px #0003">Preview: Krishna Sanskrit</div>'
)
FONT_FACE_BLOCK = re.compile(r'@font-face\s*\{[^}]*\}', re.S)
FAMILY_DECL = re.compile(r'((?:font-family|--veda-font-primary)\s*:\s*)([^;}]*)', re.I)
REPLACED = re.compile(r"""(['"])(?:Shobhika|Sanskrit2020|Sanskrit 2020|Sanskrit 2003)\1""")
FAUX_WEIGHT = re.compile(r'-webkit-text-stroke\s*:\s*0\.18px\s+currentColor\s*;')


def _swap_families(value):
    if not REPLACED.search(value):
        return value
    parts, seen = [], set()
    for part in (p.strip() for p in REPLACED.sub("'Krishna Sanskrit'", value).split(',')):
        if part and part not in seen:
            seen.add(part)
            parts.append(part)
    return ', '.join(parts)


def rewrite_css(text):
    """Swap font stacks everywhere except inside @font-face rules."""
    out, pos = [], 0
    for m in FONT_FACE_BLOCK.finditer(text):
        out.append(_rewrite_rules(text[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(_rewrite_rules(text[pos:]))
    return FONT_FACE + ''.join(out)


def _rewrite_rules(text):
    text = FAMILY_DECL.sub(lambda m: m.group(1) + _swap_families(m.group(2)), text)
    return FAUX_WEIGHT.sub('', text)


def rewrite_html(text):
    text = re.sub(r'(<style[^>]*>)(.*?)(</style>)',
                  lambda m: m.group(1) + rewrite_css(m.group(2)) + m.group(3), text, flags=re.S | re.I)
    text = re.sub(r'(style=")([^"]*)(")', lambda m: m.group(1) + _rewrite_rules(m.group(2)) + m.group(3), text)
    text = text.replace('</head>', f'<style>{FONT_FACE}</style></head>', 1)
    return text.replace('</body>', BADGE + '</body>', 1)


def rewrite_js(text):
    return re.sub(r'/css/fonts/Sanskrit2020U\.otf', FONT_URL, text)


class Handler(SimpleHTTPRequestHandler):
    krishna = False

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, *args):
        pass

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if self.krishna and path.startswith('/__krishna/'):
            return self._send_file(BUILD / Path(path).name)
        if not self.krishna:
            return super().do_GET()
        local = Path(self.translate_path(path))
        if local.is_dir():
            local = local / 'index.html'
        rewriters = {'.css': rewrite_css, '.html': rewrite_html, '.js': rewrite_js}
        rewrite = rewriters.get(local.suffix)
        if not rewrite or not local.is_file():
            return super().do_GET()
        body = rewrite(local.read_text('utf-8')).encode('utf-8')
        types = {'.css': 'text/css', '.html': 'text/html', '.js': 'application/javascript'}
        self.send_response(200)
        self.send_header('Content-Type', f'{types[local.suffix]}; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file):
        if not file.is_file():
            return self.send_error(404, f'{file.name} not built; run build.py')
        body = file.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'font/woff2' if file.suffix == '.woff2' else 'font/ttf')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class KrishnaHandler(Handler):
    krishna = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', default=str(Path.home() / 'code' / 'sriiyerNew'))
    ap.add_argument('--port', type=int, default=8800)
    args = ap.parse_args()
    servers = [
        ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=args.site)),
        ThreadingHTTPServer(('127.0.0.1', args.port + 1), partial(KrishnaHandler, directory=args.site)),
    ]
    for s in servers:
        threading.Thread(target=s.serve_forever, daemon=True).start()
    print(f'original: http://localhost:{args.port}/veda/samhita/Kanda_1_Prashna_1.html')
    print(f'krishna:    http://localhost:{args.port + 1}/veda/samhita/Kanda_1_Prashna_1.html', flush=True)
    threading.Event().wait()


if __name__ == '__main__':
    main()
