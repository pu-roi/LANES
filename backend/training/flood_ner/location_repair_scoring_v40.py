"""Coordinator-only scoring; references never enter the repair worker."""
from __future__ import annotations

from collections import Counter
from .context_association_scoring import output_keys, reference_keys, strict_counts, span_key
from .context_scoring_v37 import qualifier_errors


def location_result(case: dict, output: dict) -> dict:
    expected = {tuple(x) for x in case['expected_mentions']}
    actual = {span_key(m) for m in output['effective_mentions']}
    return {'case_id': case['case_id'], 'family': case['family'], 'language': case['language'],
            'passed': expected == actual and output['neural_mentions'] == case['raw']['mentions'],
            'expected': sorted(expected), 'actual': sorted(actual)}


def temporal_result(case: dict, output: dict) -> dict:
    expressions = {e['id']: e for e in output['expressions']}
    roles = [f['temporal_role'] for f in output['facts'] if f['kind'] == 'time' and
             any(expressions[e]['text'] == case['clock'] for e in f['entity_ids'])]
    statuses = [f['value'] for f in output['facts'] if f['kind'] == 'status']
    status_ok = case['expected_status'] is None or case['expected_status'] in statuses
    invention = bool(output['absolute_instants'] or output['numeric_depths'])
    return {'case_id': case['case_id'], 'language': case['language'], 'time_before': case['time_before'],
            'expected_role': case['role'], 'actual_roles': roles, 'actual_statuses': statuses,
            'passed': roles == [case['role']] and status_ok and not invention,
            'onset_invented': case['forbid_onset'] and 'onset' in roles,
            'absolute_or_numeric_invention': invention, 'status_preserved': status_ok}


def recognition(reference: list, original: list, effective: list) -> dict:
    gold = {tuple(x) for x in reference}; old = {span_key(m) for m in original}; new = {span_key(m) for m in effective}
    return {'baseline': strict_counts(gold, old), 'candidate': strict_counts(gold, new),
            'gained_correct': sorted((new & gold)-old), 'lost_correct': sorted((old & gold)-new),
            'introduced_fp': sorted((new-gold)-(old-gold)), 'resolved_fp': sorted((old-gold)-new)}


def context(reference: dict, previous: dict, output: dict) -> dict:
    gold = reference_keys(reference); old = output_keys(previous); new = output_keys(output)
    return {'counts': strict_counts(gold['links'], new['links']),
            'lost_correct': sorted((gold['links'] & old['links'])-new['links']),
            'introduced_fp': sorted((new['links']-gold['links'])-(old['links']-gold['links'])),
            'gained_correct': sorted((gold['links'] & new['links'])-old['links']),
            'expression_regressions': {kind: {'new_fp': sorted((new[kind]-gold[kind])-(old[kind]-gold[kind])),
                                             'new_fn': sorted((gold[kind]-new[kind])-(gold[kind]-old[kind]))}
                                       for kind in ('DEPTH', 'TIME')},
            'qualifier_errors': qualifier_errors(output),
            'unassigned_count': len(output['unassigned'])}


def aggregate(rows: list[dict], downstream: list[dict], fixtures: list[dict],
              existing_fixtures: list[dict], times: list[dict]) -> dict:
    if len(rows) != 345 or len(downstream) != 23 or len(existing_fixtures) != 238 or len(times) != 36:
        raise ValueError('complete frozen workload required')
    totals = {name: Counter(tp=0, fp=0, fn=0) for name in ('baseline', 'candidate')}
    for row in rows:
        for name in totals:
            totals[name].update({k: row[name][k] for k in ('tp', 'fp', 'fn')})
    flags = {'fixture_failures': sum(not r['passed'] for r in fixtures),
             'existing_fixture_failures': sum(not r['passed'] for r in existing_fixtures),
             'introduced_location_fp': sum(len(r['introduced_fp']) for r in rows),
             'lost_correct_locations': sum(len(r['lost_correct']) for r in rows),
             'gained_correct_locations': sum(len(r['gained_correct']) for r in rows),
             'introduced_association_fp': sum(len(r['introduced_fp']) for r in downstream),
             'lost_correct_associations': sum(len(r['lost_correct']) for r in downstream),
             'gained_correct_associations': sum(len(r['gained_correct']) for r in downstream),
             'qualifier_failures': sum(len(r['qualifier_errors']) for r in downstream),
             'expression_regressions': sum(len(v[k]) for r in downstream for v in r['expression_regressions'].values()
                                           for k in ('new_fp', 'new_fn')),
             'temporal_failures': sum(not r['passed'] for r in times)}
    reasons = [k for k in flags if k not in ('gained_correct_locations', 'gained_correct_associations') and flags[k]]
    if not flags['gained_correct_locations']:
        reasons.append('no_supported_location_correction')
    return {'qualified_for_later_proposal': not reasons, 'blockers': reasons, 'checks': flags,
            'recognition_counts': {k: dict(v) for k, v in totals.items()},
            'association_counts': {k: sum(r['counts'][k] for r in downstream) for k in ('tp', 'fp', 'fn')},
            'training_only_exposed_silver': True, 'generalization_claim': False}
