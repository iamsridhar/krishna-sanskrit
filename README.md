# Krishna Sanskrit

A Devanāgarī font for Vedic texts: the traditional, high-contrast letterforms of
[Sanskrit2020](https://sourceforge.net/projects/advaita-sharada-font/files/Devanagari/),
with corrected Vedic accent placement, clearer conjuncts, i-mātrā hooks that reach the
final consonant, and a modern release build (Unicode glyph names, sanitizer-clean, hinted,
consistent vertical metrics, a Devanāgarī-only web subset).

Working name. Not yet released. See **Licensing status** before publishing anything.

## How it is built

The font is not redrawn from scratch. `build.py` loads the upstream Sanskrit2020 binary
(`upstream/Sanskrit2020U.otf`, pinned by SHA-256) and applies small, reviewable patches
from `patches/` in order:

| Patch | What it does |
|---|---|
| `p00_rename` | Renames to Krishna Sanskrit, keeps upstream copyright, drops the stale DSIG and legacy Mac name records. Renders identically to upstream. |
| `p05_ots_null_anchors` | Gives upstream's NULL mark anchor (U+1CED) an explicit (0,0), so GPOS passes the OpenType Sanitizer. No visual change. |
| `p10_anudatta_below_vowel` | Hangs anudātta (U+0952) under u/ū/ṛ/ṝ/ḷ/ḹ vowel signs and virama instead of overlapping them. |
| `p15_shobhika_da_stacks` | Redraws द्ध, द्ध्य, द्भ्य, द्व्य, द्द्य from Shobhika's outlines (open stack, compact joined ya-phala), scaled to Krishna, stems thickened, Krishna's headline. |
| `p20_conjunct_decompose` | Splits cramped fused conjuncts into upstream component glyphs: ब्ज क्त्र क्च च्छ्र ञ्छ्र न्त्र्य → half form + letter; द्ध्व द्ध्म द्ध्र द्घ्र द्र्व → द् + rest; leftover below-ra (र्र्ष) → र्. |
| `p30_long_i_matra` | Adds 23 longer i-mātrā (ि) hooks, made by stretching the flat top of the upstream arc (also for the ि+anusvāra/candrabindu/reph forms), and picks one per conjunct so the hook lands on the final consonant as it does on a single consonant. Single consonants keep the upstream ि. |
| `p90_vertical_metrics` | USE_TYPO_METRICS, typo = hhea with the line gap folded in (same total line height), usWin covering the full bounding box so Windows doesn't clip Vedic stacks. |
| `p95_composite_hygiene` | Removes a duplicate component (U+0957) and flattens a nested composite (U+0977). No visual change. |

After the patches, the release build (`build.py` without `--upto`) runs the production
steps: every glyph gets an Adobe Glyph List name for the text it renders
(`uni0926094D0927094D092F` for द्ध्य) and upstream's Private Use Area cmap entries for
those glyphs are removed, so **text copied out of PDFs is real Unicode**; then
ttfautohint hints every glyph consistently.

Each patch declares, via `affects(cluster)`, which text clusters it is allowed to change.
The test suite fails if anything else changes.

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/python build.py                 # -> build/KrishnaSanskrit-Regular.{ttf,woff2}, build/web/
venv/bin/python -m pytest -q             # regression + release suite (~20 s)
venv/bin/python tools/proof.py --patch p10 --png   # before/after proof in proofs/
```

## Tests

`tests/data/clusters.tsv` holds every unique Devanāgarī cluster (with frequency) from the
sriiyer.com Veda corpus: Saṃhitā, Pada, Krama, Brāhmaṇa, Āraṇyaka, Kāṭhakam, Ekāgnikāṇḍam,
Sūktāni. Regenerate it with `tools/export_corpus.py` after the site build.

- `test_roundtrip.py`: the rename-only build shapes every cluster exactly like upstream
  (same glyphs, advances and offsets under HarfBuzz), with identical glyph set and cmap.
- `test_scope.py`: every rendering change is claimed by some patch.
- `test_quality.py`: no new missing glyphs or dotted circles, no conjunct regressions,
  and no anudātta collisions outside a short, documented list of known residuals.
- `test_imatra.py`: every conjunct's i-mātrā hook lands within 1.5 steps (180 units) of
  its final consonant, and the i-mātrā before a single consonant is unchanged.
- `test_release.py`: the production steps change no shaping; glyph names decode to their
  text; no PUA mappings for real text; vertical metrics; every glyph hinted; OTS accepts
  the TTF, WOFF2 and web subset; the web subset shapes identically; text copied out of an
  XeLaTeX PDF is Unicode (needs xelatex).
- `test_engines.py` (macOS, opt-in with `KRISHNA_ENGINES=1`): CoreText (Safari, macOS/iOS
  apps) shapes every corpus cluster exactly like HarfBuzz, apart from differences upstream
  already has.

## Continuous integration

`.github/workflows/build.yml` builds, runs the tests (with XeLaTeX), runs FontBakery's
universal profile (fails on any FAIL; 8 known WARNs are upstream GDEF classes, outline
overlaps and file size), and uploads `KrishnaSanskrit.zip` (TTF, WOFF2, web subset, OFL,
FONTLOG). Pushing a `v*` tag publishes the zip as a GitHub Release. A macOS job checks
CoreText agreement.

## Using the font

**Web.** Serve `build/web/KrishnaSanskrit-Devanagari.woff2` (Devanāgarī, Vedic Extensions,
Devanāgarī Extended only; no Latin) with `build/web/krishna-sanskrit.css`, which sets
`unicode-range`, `font-display` and ascent/descent overrides so lines don't shift while
the font loads:

```css
@import url('krishna-sanskrit.css');
.sanskrit { font-family: 'Krishna Sanskrit', 'Noto Serif Devanagari', serif; }
```

Use real weights only: there is no bold yet, so avoid `font-weight: bold` and
`-webkit-text-stroke` faux-bolding on Devanāgarī.

**LaTeX (XeLaTeX / LuaLaTeX).**

```latex
\usepackage{fontspec}
\newfontfamily\sanskritfont{KrishnaSanskrit-Regular.ttf}[Path=fonts/, Script=Devanagari]
```

Digits with anudātta (२॒) render correctly without any workaround.

**Desktop.** Install `KrishnaSanskrit-Regular.ttf`. Typing needs a Devanāgarī keyboard with
Vedic accents (e.g. the Sanskrit2020 KbdEdit layout or an ITRANS/Baraha input method).

## Reviewing on the real site

```bash
venv/bin/python tools/preview_site.py      # needs a built ~/code/sriiyerNew
```

Serves the site on two ports without modifying it: `:8800` as-is, `:8801` with every
Shobhika/Sanskrit2020 Devanāgarī font stack switched to Krishna Sanskrit (and the Shobhika
faux-weight removed). Compare e.g. `/veda/samhita/Kanda_1_Prashna_1.html` on both.
`tools/compare_engines.py` prints the CoreText vs HarfBuzz report in detail.

## Renderer notes

- HarfBuzz (every browser except Safari, on every OS, plus Android and XeTeX/LuaTeX) and
  CoreText (Safari, every iOS browser, macOS apps) are verified. DirectWrite shaping
  (desktop Windows apps such as Word) is not yet tested.
- New lookups are registered in `psts`, the last presentation feature: HarfBuzz applies
  all presentation lookups in lookup order, but CoreText applies them feature by feature.
- CoreText does not skip ZWJ when matching contexts, so the i-mātrā rules include
  explicit ZWJ variants.

## Adding a patch

1. Create `patches/pNN_short_name.py` with `ID`, `SUMMARY`, `apply(font)`, `affects(cluster)`.
2. Register it in `patches/__init__.py`.
3. Add a quality test for what it fixes, run `pytest`, then review `tools/proof.py --patch pNN --png`.
4. Add an entry to `FONTLOG.txt`.

## Licensing status

- **Sanskrit2020** declares the SIL Open Font License in its name table (IDs 13/14) and
  reserves no font name. Confirmation has been requested from Omkarananda Ashram and
  advaita56. **Do not publish until they reply.**
- **Latin glyphs** are URW Palladio. Their licence is unconfirmed. The web subset drops
  them. For the full font, either confirm it or replace the Latin with an OFL font
  (e.g. Gentium Plus, Noto Serif, PT Serif; TeX Gyre Pagella is GUST-licensed, not OFL).
- **Shobhika** (`upstream/Shobhika-Regular.otf`, OFL, © IIT Bombay) supplies the outlines for
  five द-stack glyphs (p15). IIT Bombay's copyright is in `OFL.txt` and name ID 0.
- Output fonts are OFL-1.1 (`OFL.txt`). They may be bundled and redistributed freely but
  not sold on their own, and must keep all copyright notices.
