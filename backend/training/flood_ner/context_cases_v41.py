"""Thirty-six fictional contrasts for time predicates and collective scope."""
from __future__ import annotations

import hashlib
from .location_repair_cases_v40 import mention


def core_cases() -> list[dict]:
    cases = []
    for language in ('english', 'tagalog', 'taglish'):
        for family in ('predicate_attachment', 'competing_subjects', 'collective_locality'):
            for supported in (True, False):
                for variant in (0, 1):
                    road = 'Daan Piña'; clock = '6:31 PM'; expected = []
                    depth_scopes = None; relation_scopes = None
                    if family == 'predicate_attachment':
                        if supported and variant == 0:
                            text = {'english': f'🌧 At {clock}, flooding started on {road}.',
                                    'tagalog': f'🌧 Nang {clock}, nagsimula ang baha sa {road}.',
                                    'taglish': f'🌧 At {clock}, nagsimula ang flood sa {road}.'}[language]
                            expected = [[clock, 'onset']]
                        elif supported:
                            text = {'english': f'The flood report about {road} was issued at {clock}.',
                                    'tagalog': f'Iniulat ang baha sa {road} nang {clock}.',
                                    'taglish': f'Reported ang baha sa {road} at {clock}.'}[language]
                            expected = [[clock, 'report']]
                        elif variant == 0:
                            text = {'english': f'At {clock}, flooding had not started on {road}.',
                                    'tagalog': f'Nang {clock}, hindi nagsimula ang baha sa {road}.',
                                    'taglish': f'At {clock}, hindi nagsimula ang flood sa {road}.'}[language]
                            expected = [[clock, 'unspecified']]
                        else:
                            text = {'english': f'Forecast: flooding may have started on {road} at {clock}.',
                                    'tagalog': f'Babala: maaaring nagsimula ang baha sa {road} nang {clock}.',
                                    'taglish': f'Forecast: maaaring nagsimula ang flood sa {road} at {clock}.'}[language]
                            expected = [[clock, 'unspecified']]
                        mentions = [mention(text, road, 'ROAD')]
                    elif family == 'competing_subjects':
                        if supported and variant == 0:
                            text = {'english': f'The report at 8 PM said flooding on {road} started at 6 PM.',
                                    'tagalog': f'Iniulat nang 8 PM na nagsimula ang baha sa {road} nang 6 PM.',
                                    'taglish': f'Reported at 8 PM na nagsimula ang flood sa {road} at 6 PM.'}[language]
                            expected = [['8 PM', 'report'], ['6 PM', 'onset']]
                        elif supported:
                            text = {'english': f'Rainfall started at 5 PM before flooding was observed on {road} at 7 PM.',
                                    'tagalog': f'Nagsimula ang pag-ulan nang 5 PM bago naobserbahan ang baha sa {road} nang 7 PM.',
                                    'taglish': f'Rainfall started at 5 PM bago observed ang baha sa {road} at 7 PM.'}[language]
                            expected = [['5 PM', 'unspecified'], ['7 PM', 'observation']]
                        elif variant == 0:
                            text = {'english': f'Flooding on {road} either started or was reported at 6 PM.',
                                    'tagalog': f'Nagsimula o iniulat ang baha sa {road} nang 6 PM.',
                                    'taglish': f'Flooding sa {road} either nagsimula or reported at 6 PM.'}[language]
                            expected = [['6 PM', 'unspecified']]
                        else:
                            text = {'english': f'Classes started at 5 PM before flooding was observed on {road} at 7 PM.',
                                    'tagalog': f'Nagsimula ang classes nang 5 PM bago naobserbahan ang baha sa {road} nang 7 PM.',
                                    'taglish': f'Classes started at 5 PM bago observed ang baha sa {road} at 7 PM.'}[language]
                            expected = [['5 PM', 'unspecified'], ['7 PM', 'observation']]
                        mentions = [mention(text, road, 'ROAD')]
                    else:
                        anchor, tail = ('Purok 8', '9') if variant == 0 else ('Sitio 12', '13')
                        conjunction = 'and' if language == 'english' else 'at'
                        if supported and variant == 0:
                            text = {'english': f'At {anchor} {conjunction} {tail}, the flood reached the first floor of the houses.',
                                    'tagalog': f'Sa {anchor} {conjunction} {tail}, abot-baywang ang baha sa mga bahay.',
                                    'taglish': f'Sa {anchor} {conjunction} {tail}, the flood reached the first floor of the houses.'}[language]
                            depth_scopes = ['collective']; relation_scopes = ['collective']
                        elif supported:
                            text = {'english': f'At {anchor} {conjunction} {tail}, houses were flooded with about 10 to 20 cm of water.',
                                    'tagalog': f'Sa {anchor} {conjunction} {tail}, binaha ang mga bahay ng halos 10 hanggang 20 cm na tubig.',
                                    'taglish': f'Sa {anchor} {conjunction} {tail}, flooded ang houses with about 10 to 20 cm of water.'}[language]
                            depth_scopes = ['range']; relation_scopes = ['collective']
                        elif variant == 0:
                            text = {'english': f'{anchor} {conjunction} {tail} both had knee-deep flooding inside houses.',
                                    'tagalog': f'{anchor} {conjunction} {tail}, pareho ang abot-tuhod na baha sa mga bahay.',
                                    'taglish': f'{anchor} {conjunction} {tail} both had knee-deep na baha inside houses.'}[language]
                            depth_scopes = ['point']; relation_scopes = ['shared']
                        else:
                            text = {'english': f'At {anchor}, knee-deep flooding was observed at 6 PM. At {anchor}, waist-deep flooding was observed at 7 PM.',
                                    'tagalog': f'Sa {anchor}, abot-tuhod na baha ang naobserbahan nang 6 PM. Sa {anchor}, abot-baywang na baha ang naobserbahan nang 7 PM.',
                                    'taglish': f'Sa {anchor}, knee-deep ang flood at 6 PM. Sa {anchor}, waist-deep ang flood at 7 PM.'}[language]
                            expected = [['6 PM', 'observation'], ['7 PM', 'observation']]
                            depth_scopes = ['point', 'point']; relation_scopes = ['local', 'local']
                        if not supported and variant == 1:
                            mentions = [mention(text, anchor, 'LOCAL_AREA', i, f'n{i}') for i in (0, 1)]
                        else:
                            mentions = [mention(text, anchor, 'LOCAL_AREA'), mention(text, tail, 'LOCAL_AREA', identity='n1')]
                    raw = {'record_id': f'fictional-v41-{len(cases)}', 'text': text,
                           'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                           'publication': None, 'mentions': mentions}
                    cases.append({'case_id': f'v41-{family}-{language}-{supported}-{variant}',
                                  'family': family, 'language': language, 'supported': supported, 'variant': variant,
                                  'raw': raw, 'expected_roles': expected, 'expected_depth_scopes': depth_scopes,
                                  'expected_depth_relation_scopes': relation_scopes})
    return cases


def result(case: dict, output: dict) -> dict:
    expressions = {e['id']: e for e in output['expressions']}
    roles = [[expressions[f['entity_ids'][0]]['text'], f['temporal_role']]
             for f in output['facts'] if f['kind'] == 'time']
    depths = [f for f in output['facts'] if f['kind'] == 'depth']
    by_id = {f['id']: f for f in depths}
    scopes = [r['scope'] for r in output['relations'] if r['fact_id'] in by_id]
    depth_scopes = [f['depth_scope'] for f in depths]
    ok = roles == case['expected_roles']
    if case['expected_depth_scopes'] is not None:
        ok = ok and depth_scopes == case['expected_depth_scopes'] and scopes == case['expected_depth_relation_scopes']
    ok = ok and output['mentions'] == case['raw']['mentions'] and not output['absolute_instants'] and not output['numeric_depths']
    return {'case_id': case['case_id'], 'passed': bool(ok), 'family': case['family'], 'language': case['language'],
            'expected_roles': case['expected_roles'], 'actual_roles': roles,
            'expected_depth_scopes': case['expected_depth_scopes'], 'actual_depth_scopes': depth_scopes,
            'expected_relation_scopes': case['expected_depth_relation_scopes'], 'actual_relation_scopes': scopes}
