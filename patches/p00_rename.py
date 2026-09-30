"""Rename to Krishna Sanskrit and carry the upstream copyright forward (OFL requirements)."""

ID = 'p00'
SUMMARY = 'Rename Sanskrit2020 to Krishna Sanskrit; keep upstream copyright; drop stale DSIG.'
CHANGES_RENDERING = False

FAMILY = 'Krishna Sanskrit'
STYLE = 'Regular'
VERSION = '0.100'
POSTSCRIPT = 'KrishnaSanskrit-Regular'
UPSTREAM_COPYRIGHT_PREFIX = 'Copyright 2014 Omkarananda Ashram Himalayas'
COPYRIGHT_ADDITION = 'Copyright 2026 The Krishna Sanskrit Project Authors (https://sriiyer.com/veda).'
DESCRIPTION = (
    'Krishna Sanskrit is a Devanagari font for Vedic texts, derived from Sanskrit2020 '
    '(advaita56), which is based on Sanskrit 2003 by Omkarananda Ashram Himalayas.'
)
LICENSE = ('This Font Software is licensed under the SIL Open Font License, Version 1.1. '
           'This license is available with a FAQ at: https://openfontlicense.org')
LICENSE_URL = 'https://openfontlicense.org'


def apply(font):
    name = font['name']
    upstream = name.getDebugName(0) or ''
    if not upstream.startswith(UPSTREAM_COPYRIGHT_PREFIX):
        raise ValueError(f'Unexpected upstream copyright: {upstream!r}')
    records = {
        0: f'{upstream} {COPYRIGHT_ADDITION}',
        1: FAMILY,
        2: STYLE,
        3: f'{VERSION};SRII;{POSTSCRIPT}',
        4: f'{FAMILY} {STYLE}',
        5: f'Version {VERSION}; derived from Sanskrit2020 Version 1.30 (July 27, 2022)',
        6: POSTSCRIPT,
        10: DESCRIPTION,
        13: LICENSE,
        14: LICENSE_URL,
        16: FAMILY,
        17: STYLE,
    }
    for name_id in records:
        name.removeNames(nameID=name_id)
    for name_id, value in records.items():
        name.setName(value, name_id, 3, 1, 0x409)
        name.setName(value, name_id, 1, 0, 0)
    font['head'].fontRevision = float(VERSION)
    font['OS/2'].achVendID = 'SRII'
    if 'DSIG' in font:
        del font['DSIG']


def affects(cluster):
    return False
