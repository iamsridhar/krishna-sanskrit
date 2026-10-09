"""Patches applied, in order, to the upstream Sanskrit2020 binary.

Each patch module defines:
    ID          short identifier, e.g. "p00"
    SUMMARY     one-line description (goes into FONTLOG)
    apply(font) mutate a fontTools TTFont in place
    affects(cluster: str) -> bool
                True for every text cluster whose rendering this patch may change.
                tests/test_scope.py fails if any other cluster changes.
"""
from . import (p00_rename, p05_ots_null_anchors, p10_anudatta_below_vowel, p15_shobhika_da_stacks, p20_conjunct_decompose,
               p30_long_i_matra, p40_anunasika_conjunct, p90_vertical_metrics, p95_composite_hygiene)

# Devanāgarī patches, applied to Sanskrit2020 before the Latin is replaced.
PATCHES = [p00_rename, p05_ots_null_anchors, p10_anudatta_below_vowel, p15_shobhika_da_stacks, p20_conjunct_decompose,
           p30_long_i_matra, p40_anunasika_conjunct, p95_composite_hygiene]
# Applied to the finished font, after the Gentium Latin is merged (see build.finish).
FINAL_PATCHES = [p90_vertical_metrics]
