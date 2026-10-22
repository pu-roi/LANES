"""Fictional software oracles; not admitted NER corpus records."""
from __future__ import annotations

import hashlib

LANGUAGES = ('english', 'tagalog', 'taglish')


def mention(text: str, phrase: str, label: str, occurrence: int = 0, identity: str = 'n0') -> dict:
    offset = -1
    for _ in range(occurrence+1):
        offset = text.index(phrase, offset+1)
    return {'id': identity, 'start': offset, 'end': offset+len(phrase), 'text': phrase,
            'label': label, 'provenance_sha256': 'c'*64}


def location_cases() -> list[dict]:
    cases = []
    for language in LANGUAGES:
        for family in ('transport_asset', 'shared_locality', 'explicit_road'):
            for supported in (True, False):
                for variant in (0, 1):
                    name = 'Piña Áster' if variant == 0 else 'Luntian'
                    contrast = 'supported' if supported else 'counterexample'
                    if family == 'transport_asset':
                        asset = name + (' tunnel' if variant == 0 else ' bridge')
                        if supported:
                            text = {'english': f'🌧 At {asset}: knee-deep flooding at 6 PM.',
                                    'tagalog': f'🌧 Sa {asset}: abot-tuhod ang baha nang 6 PM.',
                                    'taglish': f'🌧 Sa {asset}: knee-deep ang flood at 6 PM.'}[language]
                            original = []; expected = [(text.index(asset), text.index(asset)+len(asset), 'LANDMARK')]
                        elif variant == 0:
                            text = {'english': f'{asset} company reported rainfall at 6 PM.',
                                    'tagalog': f'Ang kompanyang {asset} ay nag-ulat ng pag-ulan nang 6 PM.',
                                    'taglish': f'{asset} company nag-report ng ulan at 6 PM.'}[language]
                            original = []; expected = []
                        else:
                            text = {'english': f'At {asset}: flooding. At {asset}: depth unreported.',
                                    'tagalog': f'Sa {asset}: baha. Sa {asset}: walang ulat ng lalim.',
                                    'taglish': f'Sa {asset}: flooded. Sa {asset}: no depth report.'}[language]
                            # An overlapping shorter neural name cannot be enlarged.
                            original = [mention(text, name, 'CITY', i, f'n{i}') for i in (0, 1)]
                            expected = [(m['start'], m['end'], m['label']) for m in original]
                    elif family == 'shared_locality':
                        anchor = 'Purok 8' if variant == 0 else 'Sitio 12'
                        tail = '9' if variant == 0 else '13'
                        conjunction = 'and' if language == 'english' else 'at'
                        text = {'english': f'At {anchor} {conjunction} {tail}, houses were flooded waist-deep.',
                                'tagalog': f'Sa {anchor} {conjunction} {tail}, abot-baywang ang baha sa mga bahay.',
                                'taglish': f'Sa {anchor} {conjunction} {tail}, waist-deep ang flood sa houses.'}[language]
                        original = [mention(text, anchor, 'LOCAL_AREA'), mention(text, tail, 'ROAD', identity='n1')]
                        if not supported:
                            if variant == 0:
                                text = {'english': f'At {anchor}, {tail} residents reported flooding.',
                                        'tagalog': f'Sa {anchor}, {tail} pamilya ang nag-ulat ng baha.',
                                        'taglish': f'Sa {anchor}, {tail} residents ang nag-report ng flood.'}[language]
                                original = [mention(text, anchor, 'LOCAL_AREA'), mention(text, tail, 'ROAD', identity='n1')]
                            else:
                                original[0]['label'] = 'ROAD'
                        expected = [(m['start'], m['end'], 'LOCAL_AREA' if supported else m['label']) for m in original]
                    else:
                        road = name + (' Road' if variant == 0 else ' Street')
                        text = {'english': f'At {road}: flooding at 6 PM; later 20 cm at 7 PM.',
                                'tagalog': f'Sa {road}: baha nang 6 PM; kalaunan 20 cm nang 7 PM.',
                                'taglish': f'Sa {road}: flooded at 6 PM; later 20 cm at 7 PM.'}[language]
                        original = [mention(text, road, 'LANDMARK')]
                        if not supported:
                            if variant == 0:
                                text = {'english': f'At {road} company, officials reported flooding elsewhere.',
                                        'tagalog': f'Ang kompanyang {road} ay nag-ulat ng baha sa ibang lugar.',
                                        'taglish': f'At {road} company, nag-report ng flood sa ibang lugar.'}[language]
                                original = [mention(text, road, 'LANDMARK')]
                            else:
                                text = {'english': f'At Upper {road}: flooding.',
                                        'tagalog': f'Sa Upper {road}: baha.',
                                        'taglish': f'Sa Upper {road}: flooded.'}[language]
                                original = [mention(text, road, 'LANDMARK')]
                        expected = [(m['start'], m['end'], 'ROAD' if supported else m['label']) for m in original]
                    cases.append({'case_id': f'v40-location-{family}-{language}-{contrast}-{variant}',
                                  'family': family, 'language': language, 'supported': supported,
                                  'variant': variant, 'raw': {'record_id': f'fictional-{len(cases)}', 'text': text, 'mentions': original},
                                  'expected_mentions': expected})
    return cases


def temporal_cases() -> list[dict]:
    cases = []
    for language in LANGUAGES:
        for role in ('onset', 'observation', 'report', 'recession', 'clearance', 'unspecified'):
            for before in (True, False):
                road = 'Piña Road'; clock = '6:31 PM' if role == 'onset' else '6 PM'
                pairs = {
                    'english': {
                        'onset': (f'At {clock}, flooding started on {road}.', f'Flooding on {road} started at {clock}.'),
                        'observation': (f'At {clock}, flooding was observed on {road}.', f'Flooding was observed on {road} at {clock}.'),
                        'report': (f'At {clock}, the flood report about {road} was issued.', f'The flood report about {road} was issued at {clock}.'),
                        'recession': (f'At {clock}, floodwater on {road} subsided.', f'Floodwater on {road} subsided at {clock}.'),
                        'clearance': (f'At {clock}, {road} was cleared of floodwater.', f'{road} was cleared of floodwater at {clock}.'),
                        'unspecified': (f'At {clock}, rainfall started near {road}; no flood observation was supplied.', f'Rainfall started near {road} at {clock}; no flood observation was supplied.')},
                    'tagalog': {
                        'onset': (f'Nang {clock}, nagsimula ang baha sa {road}.', f'Nagsimula ang baha sa {road} nang {clock}.'),
                        'observation': (f'Nang {clock}, naobserbahan ang baha sa {road}.', f'Naobserbahan ang baha sa {road} nang {clock}.'),
                        'report': (f'Nang {clock}, iniulat ang baha sa {road}.', f'Iniulat ang baha sa {road} nang {clock}.'),
                        'recession': (f'Nang {clock}, humupa ang baha sa {road}.', f'Humupa ang baha sa {road} nang {clock}.'),
                        'clearance': (f'Nang {clock}, tuyo na ang {road} at wala nang baha.', f'Tuyo na ang {road} at wala nang baha nang {clock}.'),
                        'unspecified': (f'Nang {clock}, nagsimula ang pag-ulan sa {road}; walang ulat ng baha.', f'Nagsimula ang pag-ulan sa {road} nang {clock}; walang ulat ng baha.')},
                    'taglish': {
                        'onset': (f'At {clock}, nagsimula ang flood sa {road}.', f'Nagsimula ang flood sa {road} at {clock}.'),
                        'observation': (f'At {clock}, observed ang baha sa {road}.', f'Observed ang baha sa {road} at {clock}.'),
                        'report': (f'At {clock}, reported ang baha sa {road}.', f'Reported ang baha sa {road} at {clock}.'),
                        'recession': (f'At {clock}, subsided ang baha sa {road}.', f'Subsided ang baha sa {road} at {clock}.'),
                        'clearance': (f'At {clock}, tuyo na ang {road}; cleared of floodwater.', f'Tuyo na ang {road}; cleared of floodwater at {clock}.'),
                        'unspecified': (f'At {clock}, rainfall started sa {road}; no flood observation was supplied.', f'Rainfall started sa {road} at {clock}; no flood observation was supplied.')}}
                text = pairs[language][role][0 if before else 1]
                raw = {'record_id': f'temporal-{len(cases)}', 'text': text,
                       'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                       'publication': {'value': '2026-01-01T20:00:00+08:00', 'basis': 'fictional publication; never a flood clock'},
                       'mentions': [mention(text, road, 'ROAD')]}
                cases.append({'case_id': f'v40-time-{role}-{language}-'+('before' if before else 'after'),
                              'language': language, 'role': role, 'clock': clock, 'time_before': before,
                              'raw': raw, 'expected_status': {'recession': 'subsided', 'clearance': 'cleared'}.get(role),
                              'forbid_onset': role != 'onset', 'absolute_instants': []})
    return cases
