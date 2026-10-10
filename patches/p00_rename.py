"""Name the font Krishna Sanskrit and record everyone whose work it contains (OFL).

The copyright notice keeps Omkarananda Ashram Himalayas' copyright for the Sanskrit 2003 /
Sanskrit2020 Devanāgarī and adds this project's and IIT Bombay's (Shobhika-derived glyphs,
p15). Gentium's notice is added when its Latin is merged (krishnatools.latin). Upstream's
URW Palladio Latin is not included in Krishna Sanskrit, so its notice is not carried.
"""
ID = 'p00'
SUMMARY = 'Name the font Krishna Sanskrit, credit all sources, drop stale DSIG and Mac names.'
CHANGES_RENDERING = False

FAMILY = 'Krishna Sanskrit'
STYLE = 'Regular'
VERSION = '1.003'
POSTSCRIPT = 'KrishnaSanskrit-Regular'
PROJECT_URL = 'https://github.com/iamsridhar/krishna-sanskrit'
UPSTREAM_COPYRIGHT_PREFIX = 'Copyright 2014 Omkarananda Ashram Himalayas, Rishikesh, INDIA'
COPYRIGHT = (
    f'Copyright 2026 The Krishna Sanskrit Project Authors ({PROJECT_URL}). '
    'Devanagari based on Sanskrit2020 by advaita56 and Sanskrit 2003, '
    'Copyright 2014 Omkarananda Ashram Himalayas, Rishikesh, INDIA. '
    'Glyphs for ddha, ddhya, dbhya, dvya and ddya derived from Shobhika, '
    'Copyright (c) 2016 IIT Bombay (www.iitb.ac.in).'
)
DESCRIPTION = (
    'Krishna Sanskrit is a Devanagari font for Vedic texts: Nirnaya Sagar style letterforms '
    'from Sanskrit2020 with corrected Vedic accent placement, clearer conjuncts and i-matra '
    'hooks that reach the final consonant, plus Gentium Latin for transliteration.'
)
DESIGNERS = ('Omkarananda Ashram Himalayas (Sanskrit 2003); advaita56 (Sanskrit2020); '
             'IIT Bombay (Shobhika); SIL Global (Gentium); Krishna Sanskrit Project')
LICENSE = ('This Font Software is licensed under the SIL Open Font License, Version 1.1. '
           'This license is available with a FAQ at: https://openfontlicense.org')
LICENSE_URL = 'https://openfontlicense.org'


def apply(font):
    name = font['name']
    upstream = name.getDebugName(0) or ''
    if not upstream.startswith(UPSTREAM_COPYRIGHT_PREFIX):
        raise ValueError(f'Unexpected upstream copyright: {upstream!r}')
    records = {
        0: COPYRIGHT,
        1: FAMILY,
        2: STYLE,
        3: f'{VERSION};SRII;{POSTSCRIPT}',
        4: f'{FAMILY} {STYLE}',
        5: f'Version {VERSION}; derived from Sanskrit2020 Version 1.30 (July 27, 2022)',
        6: POSTSCRIPT,
        8: 'Krishna Sanskrit Project',
        9: DESIGNERS,
        10: DESCRIPTION,
        11: PROJECT_URL,
        13: LICENSE,
        14: LICENSE_URL,
        16: FAMILY,
        17: STYLE,
    }
    for name_id in records:
        name.removeNames(nameID=name_id)
    for name_id, value in records.items():
        name.setName(value, name_id, 3, 1, 0x409)
    name.names = [r for r in name.names if r.platformID != 1]  # modern fonts: Windows names only
    font['head'].fontRevision = float(VERSION)
    font['OS/2'].achVendID = 'SRII'
    if 'DSIG' in font:
        del font['DSIG']


def affects(cluster):
    return False
