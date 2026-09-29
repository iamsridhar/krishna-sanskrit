# Krishna Sanskrit

A Devanāgarī font for Vedic texts: the traditional, high-contrast letterforms of
[Sanskrit2020](https://sourceforge.net/projects/advaita-sharada-font/files/Devanagari/),
with corrected Vedic accent placement and (planned) improved conjunct forms.

Working name. Not yet released. See **Licensing status** before publishing anything.

## How it is built

The font is not redrawn from scratch. `build.py` loads the upstream Sanskrit2020 binary
(`upstream/Sanskrit2020U.otf`, pinned by SHA-256) and applies small, reviewable patches
from `patches/` in order:

| Patch | What it does |
|---|---|
| `p00_rename` | Renames to Krishna Sanskrit, keeps upstream copyright, drops the stale DSIG. Renders identically to upstream. |
| `p10_anudatta_below_vowel` | Hangs anudātta (U+0952) under u/ū/ṛ/ṝ/ḷ/ḹ vowel signs and virama instead of overlapping them. |
| `p15_shobhika_da_stacks` | Redraws द्ध, द्ध्य, द्भ्य, द्व्य, द्द्य from Shobhika's outlines (open stack, compact joined ya-phala), scaled to Krishna, stems thickened, Krishna's headline. |
| `p20_conjunct_decompose` | Splits cramped fused conjuncts into upstream component glyphs: ब्ज क्त्र क्च च्छ्र ञ्छ्र न्त्र्य → half form + letter; द्ध्व द्ध्म द्ध्र द्घ्र द्र्व → द् + rest; leftover below-ra (र्र्ष) → र्. |
| `p30_long_i_matra` | Adds 23 longer i-mātrā (ि) hooks, made by stretching the flat top of the upstream arc (also for the ि+anusvāra/candrabindu/reph forms), and picks one per conjunct so the hook lands on the final consonant as it does on a single consonant. Single consonants keep the upstream ि. |

Each patch declares, via `affects(cluster)`, which text clusters it is allowed to change.
The test suite fails if anything else changes.

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/python build.py                 # -> build/KrishnaSanskrit-Regular.ttf + .woff2
venv/bin/python -m pytest -q             # regression suite (~2 s)
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
- `test_engines.py` (macOS, opt-in with `KRISHNA_ENGINES=1`): CoreText (Safari, macOS/iOS
  apps) shapes every corpus cluster exactly like HarfBuzz, apart from differences upstream
  already has.

## Reviewing on the real site

```bash
venv/bin/python tools/preview_site.py      # needs a built ~/code/sriiyerNew
```

Serves the site on two ports without modifying it: `:8800` as-is, `:8801` with every
Shobhika/Sanskrit2020 Devanāgarī font stack switched to Krishna Sanskrit (and the Shobhika
faux-weight removed). Compare e.g. `/veda/samhita/Kanda_1_Prashna_1.html` on both.
`tools/compare_engines.py` prints the CoreText vs HarfBuzz report in detail.

## Renderer notes

- HarfBuzz (Chrome, Firefox, Android, XeTeX/LuaTeX) and CoreText (Safari, macOS/iOS) are
  verified. DirectWrite (Windows/Word) is not yet tested.
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
- **Latin glyphs** are URW Palladio. Their licence is unconfirmed. Before release, either
  confirm it or replace the Latin with an OFL font (e.g. PT Serif or TeX Gyre Pagella).
- **Shobhika** (`upstream/Shobhika-Regular.otf`, OFL, © IIT Bombay) supplies the outlines for
  five द-stack glyphs (p15). IIT Bombay's copyright is in `OFL.txt` and name ID 0.
- Output fonts are OFL-1.1 (`OFL.txt`). They may be bundled and redistributed freely but
  not sold on their own, and must keep all copyright notices.
