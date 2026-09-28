"""Patches applied, in order, to the upstream Sanskrit2020 binary.

Each patch module defines:
    ID          short identifier, e.g. "p00"
    SUMMARY     one-line description (goes into FONTLOG)
    apply(font) mutate a fontTools TTFont in place
    affects(cluster: str) -> bool
                True for every text cluster whose rendering this patch may change.
                tests/test_scope.py fails if any other cluster changes.
"""
from . import p00_rename, p10_anudatta_below_vowel

PATCHES = [p00_rename, p10_anudatta_below_vowel]
