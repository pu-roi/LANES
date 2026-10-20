"""Forty fictional context acceptance cases, never admitted corpus members."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from typing import Any

from .context_acceptance import exact_occurrence
from .annotation.schema import AnnotationRecord


def make_case(family: str, language: str, contrast: str, text: str,
              entities: list[tuple[str, str, str, int]], facts: list[dict],
              links: list[tuple[str, list[str], str]], forbidden: list[str], reason: str) -> dict:
    case_id = f'fictional-{family}-{language}-{contrast}'
    evidence = {'start': 0, 'end': len(text), 'text': text}
    values = [{'id': id, 'label': label, **exact_occurrence(text, phrase, occurrence)}
              for id, phrase, label, occurrence in entities]
    by_id = {e['id']: e for e in values}
    fs = []
    for supplied in facts:
        f = deepcopy(supplied)
        f['evidence'] = [deepcopy(evidence)]
        if f['kind'] in {'depth', 'time'}:
            f['value'] = by_id[f['entity_ids'][0]]['text']
        fs.append(f)
    relations = [{'id': f'link-{i}', 'fact_id': fact_id, 'target_entity_ids': targets,
                  'scope': scope, 'evidence': [deepcopy(evidence)]}
                 for i, (fact_id, targets, scope) in enumerate(links)]
    source = {'source_id': case_id, 'url': 'https://example.invalid/' + case_id,
              'publisher': 'Fictional acceptance author', 'origin': 'constructed_fixture',
              'text': text, 'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
              'capture_version': 'context-acceptance-v33', 'article_group': case_id,
              'reuse_terms': 'constructed software fixture only', 'extraction_method': 'authored fixture'}
    record = AnnotationRecord.model_validate_json(__import__('json').dumps({
        'record_id': case_id, 'source': source, 'text': text, 'text_sha256': source['text_sha256'],
        'passage_start': 0, 'passage_end': len(text), 'passage_language': language,
        'entities': values, 'facts': fs, 'relations': relations, 'annotation_profile': 'context-rich-v1',
        'annotation_revision': 'context-acceptance-v33', 'quality': 'constructed',
        'complete': True, 'review_status': 'accepted', 'reviewer': 'fictional fixture author', 'split': None,
    })).model_dump(mode='json')
    linked = {r['fact_id'] for r in record['relations']}
    return {'case_id': case_id, 'family': family, 'language': language, 'contrast': contrast,
            'record': record, 'expected': {'relations': deepcopy(record['relations']),
                'unassigned_fact_ids': sorted(f['id'] for f in record['facts'] if f['id'] not in linked),
                'must_not_infer': forbidden, 'absolute_instants': []}, 'reason': reason}


def entity(id: str, phrase: str, label: str = 'ROAD', occurrence: int = 0) -> tuple:
    return id, phrase, label, occurrence


def depth(id: str, entity_id: str, scope: str = 'point', qualifiers: list[str] | None = None) -> dict:
    return {'id': id, 'kind': 'depth', 'entity_ids': [entity_id], 'depth_scope': scope,
            'qualifiers': qualifiers or []}


def time(id: str, entity_id: str, role: str) -> dict:
    return {'id': id, 'kind': 'time', 'entity_ids': [entity_id], 'temporal_role': role}


def status(id: str, value: str) -> dict:
    return {'id': id, 'kind': 'status', 'value': value}


def core_cases() -> list[dict[str, Any]]:
    cases = []
    for language in ('english', 'taglish'):
        en = language == 'english'
        def add(family: str, contrast: str, english: str, taglish: str, es: list, fs: list,
                links: list, forbidden: list[str], reason: str) -> None:
            cases.append(make_case(family, language, contrast, english if en else taglish,
                                   es, fs, links, forbidden, reason))
        add('row_measurements', 'supported',
            '🌧 Flood report\nAster Road: 10 cm.\nPiña Court: 20 cm.',
            '🌧 Baha report\nAster Road: 10 cm.\nPiña Court: 20 cm.',
            [entity('p1','Aster Road'),entity('p2','Piña Court','LOCAL_AREA'),entity('d1','10 cm','DEPTH'),entity('d2','20 cm','DEPTH')],
            [depth('f1','d1'),depth('f2','d2')],[('f1',['p1'],'local'),('f2',['p2'],'local')],
            ['Do not transfer 20 cm to p1 or 10 cm to p2.'], 'Each explicit row retains its measurement and LOCAL_AREA label.')
        add('row_measurements', 'counterexample',
            'Aster Road: 10 cm of floodwater.\nAster Road: depth not recorded.',
            'Aster Road: 10 cm ang baha.\nAster Road: walang recorded depth.',
            [entity('p1','Aster Road'),entity('p2','Aster Road',occurrence=1),entity('d1','10 cm','DEPTH')],
            [depth('f1','d1')],[('f1',['p1'],'local')],['Do not copy the first row measurement to the second occurrence.'],
            'Repeated names refer to separately evidenced rows, not first-occurrence relocation.')
        add('separate_depth_shared_time','supported',
            'As of 2 PM, Aster Road had knee-deep flooding and Piña Road had waist-deep flooding.',
            'As of 2 PM, knee-deep ang baha sa Aster Road at waist-deep sa Piña Road.',
            [entity('p1','Aster Road'),entity('p2','Piña Road'),entity('d1','knee-deep','DEPTH'),entity('d2','waist-deep','DEPTH'),entity('t','2 PM','TIME')],
            [depth('f1','d1'),depth('f2','d2'),time('ft','t','observation')],
            [('f1',['p1'],'local'),('f2',['p2'],'local'),('ft',['p1','p2'],'shared')],
            ['A shared time does not make the two depths interchangeable.'], 'The sentence explicitly scopes one clock across two distinct measurements.')
        add('separate_depth_shared_time','counterexample',
            'At 2 PM, Aster Road had knee-deep flooding. Meanwhile, Piña Road had waist-deep flooding at 3 PM.',
            'At 2 PM, knee-deep ang baha sa Aster Road. Samantala, waist-deep sa Piña Road at 3 PM.',
            [entity('p1','Aster Road'),entity('p2','Piña Road'),entity('d1','knee-deep','DEPTH'),entity('d2','waist-deep','DEPTH'),entity('t1','2 PM','TIME'),entity('t2','3 PM','TIME')],
            [depth('f1','d1'),depth('f2','d2'),time('ft1','t1','observation'),time('ft2','t2','observation')],
            [('f1',['p1'],'local'),('f2',['p2'],'local'),('ft1',['p1'],'local'),('ft2',['p2'],'local')],
            ['Do not carry the first clock past the explicit scope change.'], 'Both observations have their own explicit clock.')
        add('shared_depth','supported',
            'Aster Road and Piña Road both have knee-deep flooding.',
            'Parehong may knee-deep na baha sa Aster Road at Piña Road.',
            [entity('p1','Aster Road'),entity('p2','Piña Road'),entity('d','knee-deep','DEPTH')],
            [depth('f','d')],[('f',['p1','p2'],'shared')],['Do not invent exact meters or observation time.'],
            'Both explicitly supports the same verbal gauge for both named roads.')
        add('shared_depth','counterexample',
            'Aster Road and Piña Road were flooded. One had knee-deep water; the report did not say which.',
            'Binaha ang Aster Road at Piña Road. May knee-deep na tubig sa isa; walang sinabi kung alin.',
            [entity('p1','Aster Road'),entity('p2','Piña Road'),entity('d','knee-deep','DEPTH')],
            [depth('f','d')],[],['Do not assign the unidentified measurement to either or both roads.'],
            'The depth is recognized but its applicable location remains unassigned.')
        add('ranges_qualifiers','supported',
            'Aster Road had up to 20 cm of floodwater. Piña Road had about knee-deep water.',
            'May up to 20 cm na baha sa Aster Road; about knee-deep naman sa Piña Road.',
            [entity('p1','Aster Road'),entity('p2','Piña Road'),entity('d1','up to 20 cm','DEPTH'),entity('d2','about knee-deep','DEPTH')],
            [depth('f1','d1','maximum',['upper bound']),depth('f2','d2','point',['approximate verbal gauge'])],
            [('f1',['p1'],'local'),('f2',['p2'],'local')],['Do not replace an upper bound or approximation with an exact point value.'],
            'Qualifiers stay inside the source span and in fact semantics.')
        add('ranges_qualifiers','counterexample',
            'Flood depths across Aster Road and Piña Road ranged from 10 to 20 cm; individual depths were not given.',
            'Ang flood depths sa Aster Road at Piña Road ay 10 to 20 cm; walang individual measurement.',
            [entity('p1','Aster Road'),entity('p2','Piña Road'),entity('d','10 to 20 cm','DEPTH')],
            [depth('f','d','range',['collective range; individual depth unknown'])],[('f',['p1','p2'],'collective')],
            ['Do not assign 20 cm, 10 cm, or a midpoint to every road.'], 'A collective range is not one shared scalar.')
        add('scope_boundaries','supported',
            'Aster Road in Barangay Luntian, Bay City, Verde Province had knee-deep flooding. Piña School was used as a shelter; no school flood was reported.',
            'Knee-deep ang baha sa Aster Road sa Barangay Luntian, Bay City, Verde Province. Shelter ang Piña School; walang report na binaha ang school.',
            [entity('p1','Aster Road'),entity('b','Barangay Luntian','BARANGAY'),entity('c','Bay City','CITY'),entity('v','Verde Province','PROVINCE'),entity('p2','Piña School','LANDMARK'),entity('d','knee-deep'if en else'Knee-deep','DEPTH')],
            [depth('f','d')],[('f',['p1'],'local')],['Do not spread the road depth to the shelter or its parent administrative areas.'],
            'Administrative mentions and the evacuation destination remain separate location mentions.')
        add('scope_boundaries','counterexample',
            'Aster Road was mentioned. Piña Road was mentioned. Nearby, water was knee-deep, but the site was not identified.',
            'Nabanggit ang Aster Road. Nabanggit ang Piña Road. Nearby, knee-deep ang tubig pero hindi tinukoy ang site.',
            [entity('p1','Aster Road'),entity('p2','Piña Road'),entity('d','knee-deep','DEPTH')],
            [depth('f','d')],[],['Do not resolve nearby to the closest or most recently mentioned road.'],
            'A missing antecedent is explicit unresolved scope.')
        add('forecast','supported',
            'Forecasters warn Aster Road may have knee-deep flooding tomorrow; no current observation is supplied.',
            'May forecast na maaaring knee-deep ang baha sa Aster Road tomorrow; walang current observation.',
            [entity('p','Aster Road'),entity('d','knee-deep','DEPTH'),entity('t','tomorrow','TIME')],
            [depth('f','d','point',['predicted only']),time('ft','t','unspecified'),status('s','forecast')],
            [('f',['p'],'local'),('ft',['p'],'local'),('s',['p'],'local')],
            ['Do not classify the forecast as observed active flooding or resolve an absolute date.'], 'Forecast evidence stays prospective.')
        add('forecast','counterexample',
            'A forecast predicts knee-deep flooding on Aster Road tomorrow. Piña Road is not flooded now.',
            'Forecast ang knee-deep na baha sa Aster Road tomorrow. Hindi binabaha ang Piña Road now.',
            [entity('p1','Aster Road'),entity('p2','Piña Road'),entity('d','knee-deep','DEPTH'),entity('t1','tomorrow','TIME'),entity('t2','now','TIME')],
            [depth('f','d','point',['predicted only']),time('ft1','t1','unspecified'),time('ft2','t2','observation'),status('s1','forecast'),status('s2','negated')],
            [('f',['p1'],'local'),('ft1',['p1'],'local'),('ft2',['p2'],'local'),('s1',['p1'],'local'),('s2',['p2'],'local')],
            ['Do not let a forecast or its depth override the other road absence observation.'], 'Forecast and negation have distinct targets.')
        add('negation','supported',
            'Aster Road is not flooded at 2 PM.', 'Hindi binabaha ang Aster Road at 2 PM.',
            [entity('p','Aster Road'),entity('t','2 PM','TIME')],[status('s','negated'),time('ft','t','observation')],
            [('s',['p'],'local'),('ft',['p'],'local')],['Do not infer zero measured depth or a flood-clearance time from absence alone.'],
            'An absence observation is not a measured zero or a transition from a prior flood.')
        add('negation','counterexample',
            'No residents were injured, but Aster Road had knee-deep flooding.',
            'Walang residents na nasaktan, pero knee-deep ang baha sa Aster Road.',
            [entity('p','Aster Road'),entity('d','knee-deep','DEPTH')],[depth('f','d'),status('s','active')],
            [('f',['p'],'local'),('s',['p'],'local')],['Do not treat negated injuries as negated flooding.'], 'Negation scope is the casualty statement only.')
        add('historical_update','supported',
            'Last year Aster Road had knee-deep flooding. Today Piña Road has waist-deep flooding.',
            'Last year ay knee-deep ang baha sa Aster Road. Today ay waist-deep sa Piña Road.',
            [entity('p1','Aster Road'),entity('p2','Piña Road'),entity('d1','knee-deep','DEPTH'),entity('d2','waist-deep','DEPTH'),entity('t1','Last year','TIME'),entity('t2','Today','TIME')],
            [depth('f1','d1'),depth('f2','d2'),time('ft1','t1','observation'),time('ft2','t2','observation'),status('s1','historical'),status('s2','active')],
            [('f1',['p1'],'local'),('f2',['p2'],'local'),('ft1',['p1'],'local'),('ft2',['p2'],'local'),('s1',['p1'],'local'),('s2',['p2'],'local')],
            ['Do not activate an old observation or transfer its depth into the current report.'], 'Historical and current sites remain separate.')
        add('historical_update','counterexample',
            'Yesterday Aster Road had knee-deep flooding. Today Aster Road has gutter-deep flooding.',
            'Yesterday ay knee-deep ang baha sa Aster Road. Today ay gutter-deep sa Aster Road.',
            [entity('p1','Aster Road'),entity('p2','Aster Road',occurrence=1),entity('d1','knee-deep','DEPTH'),entity('d2','gutter-deep','DEPTH'),entity('t1','Yesterday','TIME'),entity('t2','Today','TIME')],
            [depth('f1','d1'),depth('f2','d2'),time('ft1','t1','observation'),time('ft2','t2','observation'),status('s1','historical'),status('s2','active')],
            [('f1',['p1'],'local'),('f2',['p2'],'local'),('ft1',['p1'],'local'),('ft2',['p2'],'local'),('s1',['p1'],'local'),('s2',['p2'],'local')],
            ['Do not merge repeated same-name occurrences or discard the historical evidence.'], 'Different observation versions are preserved without geographic inference.')
        add('observation_onset','supported',
            'Flooding on Aster Road began at 1 PM and was observed at 2 PM.',
            'Nagsimula ang baha sa Aster Road at 1 PM at na-observe at 2 PM.',
            [entity('p','Aster Road'),entity('t1','1 PM','TIME'),entity('t2','2 PM','TIME')],
            [time('ft1','t1','onset'),time('ft2','t2','observation')],
            [('ft1',['p'],'local'),('ft2',['p'],'local')],['Do not replace the onset with the later observation clock.'], 'Explicit onset and observation remain distinct roles.')
        add('observation_onset','counterexample',
            'Flooding on Aster Road was observed at 2 PM. Its start time was unknown.',
            'Na-observe ang baha sa Aster Road at 2 PM. Unknown ang start time.',
            [entity('p','Aster Road'),entity('t','2 PM','TIME')],[time('ft','t','observation')],[('ft',['p'],'local')],
            ['Do not infer onset from observation or publication time.'], 'Only an observation time is supported.')
        add('recession_clearance','supported',
            'At 1 PM water on Aster Road was receding. At 2 PM the road was explicitly reported dry and cleared of floodwater.',
            'At 1 PM ay receding ang baha sa Aster Road. At 2 PM ay reported dry at cleared of floodwater na ang kalsada.',
            [entity('p','Aster Road'),entity('t1','1 PM','TIME'),entity('t2','2 PM','TIME')],
            [time('ft1','t1','recession'),time('ft2','t2','clearance'),status('s1','receding'),status('s2','cleared')],
            [('ft1',['p'],'local'),('ft2',['p'],'local'),('s1',['p'],'local'),('s2',['p'],'local')],
            ['Do not erase the prior observation or treat 1 PM as clearance.'], 'Explicit dry/cleared wording supports the later clearance only.')
        add('recession_clearance','counterexample',
            'At 2 PM water on Aster Road was receding but remained gutter-deep.',
            'At 2 PM ay receding ang baha sa Aster Road pero gutter-deep pa rin.',
            [entity('p','Aster Road'),entity('t','2 PM','TIME'),entity('d','gutter-deep','DEPTH')],
            [time('ft','t','recession'),depth('f','d'),status('s','receding')],
            [('ft',['p'],'local'),('f',['p'],'local'),('s',['p'],'local')],
            ['Do not infer dry, cleared, zero depth, or a clearance time from recession.'], 'Residual water remains explicitly present.')
    return cases
