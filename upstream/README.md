# Upstream sources

Krishna Sanskrit is built from these fonts. They are **not** stored in this repository:
`krishnatools/upstream.py` downloads each from its official release on first build and
refuses to continue if its SHA-256 differs from the pinned value.

| File | Official source | Licence | SHA-256 |
|---|---|---|---|
| `Sanskrit2020U.otf` | [advaita-sharada-font on SourceForge](https://sourceforge.net/projects/advaita-sharada-font/files/Devanagari/) (Version 1.30, July 27 2022) | SIL OFL 1.1, as declared in the font's name table (IDs 13/14) | `dfaf4ed323c7a42d5c4bf3f62182e5db5a99f1472ab137cb3f53a05d3c2e1bd9` |
| `Shobhika-Regular.otf` | [Sandhi-IITBombay/Shobhika v1.05](https://github.com/Sandhi-IITBombay/Shobhika/releases/tag/v1.05) | SIL OFL 1.1 (`Shobhika-OFL.txt`) | `bde48974337ea665b930d956c26d0b3884f1bc0549769bfb7d82caa3e0af181f` |
| `Gentium-Medium.ttf` | [silnrsi/font-gentium v7.000](https://github.com/silnrsi/font-gentium/releases/tag/v7.000) | SIL OFL 1.1, Reserved Font Names "Gentium", "SIL" (`Gentium-OFL.txt`) | `658ba723e1e76345b5397fabe73456fe65147e7da1ba4aa5751b956ebaf519e4` |

What is used from each:

- **Sanskrit2020**: all Devanāgarī, Vedic Extensions and Devanāgarī Extended glyphs and
  their OpenType layout, modified by `patches/`. Its bundled URW Palladio Latin
  (AGPL/GPL-licensed) is **removed** and does not appear in Krishna Sanskrit.
- **Shobhika**: outlines of five द-stack glyphs (द्ध, द्ध्य, द्भ्य, द्व्य, द्द्य), refitted by
  `patches/p15_shobhika_da_stacks.py`.
- **Gentium Medium**: Latin, IPA, combining marks, Latin Extended Additional and
  punctuation, with their positioning, scaled to match (`krishnatools/latin.py`).
