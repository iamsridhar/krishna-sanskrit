# Upstream sources

| File | Source | SHA-256 |
|---|---|---|
| `Sanskrit2020U.otf` | https://sourceforge.net/projects/advaita-sharada-font/files/Devanagari/ (Version 1.30, July 27 2022), as shipped in sriiyer.com `css/fonts/` | `dfaf4ed323c7a42d5c4bf3f62182e5db5a99f1472ab137cb3f53a05d3c2e1bd9` |
| `Shobhika-Regular.otf` | https://github.com/Sandhi-IITBombay/Shobhika (v1.05); licence in `Shobhika-OFL.txt` | `bde48974337ea665b930d956c26d0b3884f1bc0549769bfb7d82caa3e0af181f` |

`build.py` refuses to run if `Sanskrit2020U.otf` does not match its pinned hash.
Never edit these files; all changes go through `patches/`.
