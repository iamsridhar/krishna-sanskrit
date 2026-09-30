"""Make upstream's GPOS valid for the OpenType Sanitizer (OTS).

Upstream lookup 29 gives U+1CED (Vedic sign tiryak) a NULL mark anchor. The spec requires
one, and OTS (run by browsers on web fonts, and by FontBakery) rejects the whole GPOS
table over it. HarfBuzz and other engines treat a NULL anchor as (0, 0), so writing an
explicit (0, 0) anchor keeps rendering identical.
"""
from fontTools.otlLib.builder import buildAnchor

ID = 'p05'
SUMMARY = 'Give upstream NULL mark anchors an explicit (0, 0) so GPOS passes OTS.'
CHANGES_RENDERING = False


def apply(font):
    fixed = 0
    for lookup in font['GPOS'].table.LookupList.Lookup:
        for st in lookup.SubTable:
            for array in (getattr(st, 'MarkArray', None), getattr(st, 'Mark1Array', None)):
                for rec in getattr(array, 'MarkRecord', None) or []:
                    if rec.MarkAnchor is None:
                        rec.MarkAnchor = buildAnchor(0, 0)
                        fixed += 1
    if not fixed:
        raise ValueError('No NULL mark anchors left; drop this patch')


def affects(cluster):
    return False
