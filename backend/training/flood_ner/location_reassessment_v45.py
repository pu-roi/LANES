"""Reference-side v45 reassessment of authenticated v44 outputs only."""
from collections import Counter
import hashlib

from .location_scoring_v45 import (METHODS, REPAIRED, canonical_spans, mention_spans, original_integrity,
                                   location_result, repaired_result, protected_facts)
from .location_reanalysis_v45 import read, lines, write, ROOT, ART, P44, E44
from .location_repair_scoring_v44 import article_result, freeze_key
from .location_repair_scoring_v40 import recognition, context, temporal_result
from .context_review_v37 import fixture_result
from .context_cases_v41 import result as result41
from .context_cases_v42 import result as result42


def projected_times(graph: dict) -> tuple:
    expr = {e['id']: e for e in graph['expressions']}
    return tuple(sorted((tuple((expr[i]['start'], expr[i]['end'], expr[i]['text']) for i in f['entity_ids']),
                         f['value'], f['temporal_role'], tuple(f['qualifiers'])) for f in graph['facts'] if f['kind'] == 'time'))


def original_case(case: dict, row: dict, group: str, graph: dict | None) -> dict:
    if group == 'location_fixtures':
        expected = canonical_spans(case['expected_mentions'], text=row['raw']['text'])
        actual = mention_spans(row['control_mentions'], row['raw']['text'])
        return {'case_id': case['case_id'], 'passed': expected == actual, 'view': 'saved_v40_control'}
    if group == 'new':
        return {'case_id': case['case_id'], 'passed': row['raw'] == case['raw'] and row['control_mentions'] == case['raw']['mentions'],
                'view': 'original_integrity_only_no_repair_expected'}
    if group == 'existing':
        return fixture_result(case, {**row['raw'], 'mentions': row['control_mentions']}, graph,
                              exhaustive=case['case_id'].startswith(('fictional-v36_', 'fictional-v37_', 'fictional-v38_')))
    if group == 'temporal': return temporal_result(case, graph)
    if group == 'v41': return result41(case, graph)
    return result42(case, graph)


def assess(package, destination) -> dict:
    groups = read(P44/'request.json')['groups']; outputs = {}; raw_by_group = {}
    counts = {'training': 345, 'contexts': 24, 'article': 1, 'location_fixtures': 36,
              'existing': 238, 'temporal': 36, 'v41': 36, 'v42': 36, 'new': 36}
    assert set(groups) == set(counts)
    for group, rows in groups.items():
        saved = lines(E44/'worker-output'/(group+'.jsonl'))
        assert len(rows) == len(saved) == counts[group]
        raw_by_group[group] = {r['record_id']: r for r in rows}; outputs[group] = {r['record_id']: r for r in saved}
        assert len(raw_by_group[group]) == len(outputs[group]) == counts[group] and raw_by_group[group].keys() == outputs[group].keys()
    p40 = ART/'location-repair-prepared-20261019-v40'; p42 = ART/'context-repair-prepared-20261019-v42'
    f40 = read(p40/'freeze.json')
    references = {r['record_id']: r for r in lines(ROOT/f40['training_references']['path'])}
    refs = read(ROOT/f40['context_references']['path']); assert len(refs) == 23
    assert set(raw_by_group['training']) == set(references)
    fixtures = {'location_fixtures': read(p40/'location-fixtures.json'), 'existing': read(ROOT/f40['existing_fixtures']['path']),
                'temporal': read(p40/'temporal-fixtures.json'),
                'v41': read(ART/'context-repair-prepared-20261019-v41/new-fixtures.json'),
                'v42': read(p42/'new-fixtures.json'), 'new': read(P44/'new-fixtures.json')}
    oracles = {o['case_id']: o for o in read(package/'repaired-expectations.json')}; assert set(oracles) == set(REPAIRED)
    def identity(case: dict, group: str) -> str:
        return 'fictional-'+hashlib.sha256(case['case_id'].encode()).hexdigest()[:20] if group == 'existing' else case['raw']['record_id']
    controls = {}
    for group, cases in fixtures.items():
        assert len(cases) == counts[group] and len({identity(c, group) for c in cases}) == len(cases)
        controls[group] = [original_case(c, raw_by_group[group][identity(c, group)], group,
                          outputs[group][identity(c, group)].get('control')) for c in cases]
    assert sum(map(len, controls.values())) == 418
    # Historical graphs are controls, never regenerated or inferred here.
    previous = {r['record_id']: r for r in lines(ART/'context-repair-execution-20261019-v42/worker-output/context_rows.jsonl')}
    for rid, out in outputs['contexts'].items():
        assert out['original'] == previous[rid]['views']['original'] and out['control'] == previous[rid]['views']['combined']
    ledger = read(ART/'recognition-gap-assessment-20261020-v43/case-ledger.json'); article_oracle = read(p42/'article-oracle.json')
    article_row = groups['article'][0]; article = outputs['article'][article_row['record_id']]
    assert article['control'] == lines(ART/'context-repair-execution-20261019-v42/worker-output/article_rows.jsonl')[0]['output']
    seven = read(ROOT/f40['seven_errors']['path']); assert len(seven) == 7
    methods = {}; details = {}
    for method in METHODS:
        integrity = []; times = []; expressions = []; fact_losses = []
        for group, rows in groups.items():
            for row in rows:
                out = outputs[group][row['record_id']]; item = out['methods'][method]; repair = item['repair']
                if repair['method'] != method: raise ValueError('method binding mismatch')
                integrity.append(original_integrity(row, repair))
                if 'context' in item:
                    graph = item['context']
                    if graph['mentions'] != repair['effective_mentions']: raise ValueError('effective mention/graph mismatch')
                    times.append(projected_times(graph) == projected_times(out['control']))
                    expressions.append(graph['expressions'] == out['control']['expressions'])
                    fact_losses.append(sum((protected_facts(out['control']) - protected_facts(graph)).values()))
        training = []
        for row in groups['training']:
            rid = row['record_id']; ref = references[rid]
            assert ref['text_sha256'] == row['raw']['text_sha256'] and ref['partition'] == 'train'
            canonical_spans(ref['reference'], text=row['raw']['text'])
            r = outputs['training'][rid]['methods'][method]['repair']
            training.append({'record_id': rid, **recognition(ref['reference'], row['control_mentions'], r['effective_mentions'])})
        comparisons = [{'record_id': r['record_id'], **context(r['revised_reference'], outputs['contexts'][r['record_id']]['control'],
                        outputs['contexts'][r['record_id']]['methods'][method]['context'])} for r in refs]
        tests = {}; paired = []
        for group, cases in fixtures.items():
            tests[group] = []
            for case in cases:
                rid = identity(case, group); row = raw_by_group[group][rid]; item = outputs[group][rid]['methods'][method]
                repair = item['repair']; graph = item.get('context')
                if group in {'new', 'location_fixtures'}:
                    value = location_result(case, row, repair, conditional=group == 'new')
                elif group == 'v42' and case['case_id'] in oracles and method in (REPAIRED[case['case_id']], 'combined'):
                    value = repaired_result(oracles[case['case_id']], row, repair, outputs[group][rid]['control'], graph)
                    paired.append(value)
                else:
                    value = original_case(case, {**row, 'control_mentions': repair['effective_mentions']}, group, graph)
                    if group == 'v42' and case['case_id'] in oracles:
                        paired.append({'case_id': case['case_id'], 'passed': value['passed'], 'view': 'original_expectation_family_disabled'})
                tests[group].append(value)
        assert len(paired) == 3
        art = article_result(article_row['raw'], article['control'], article['methods'][method]['context'],
                             article['methods'][method]['repair'], ledger, article_oracle)
        historic = []
        from .context_association_scoring import output_keys
        for e in seven:
            out = outputs['contexts'][e['opaque_id']]; key = freeze_key(e['strict_key'])
            before = key in output_keys(out['control'])['links']; after = key in output_keys(out['methods'][method]['context'])['links']
            historic.append({'error_id': e['error_id'], 'disposition': 'retained_recovery' if before and after else
                             'lost_predecessor_recovery' if before else 'newly_recovered' if after else 'still_unresolved'})
        checks = {'control_expectation_failures': sum(not t['passed'] for ts in controls.values() for t in ts),
                  'candidate_fixture_failures': sum(not t['passed'] for ts in tests.values() for t in ts),
                  'paired_view_failures': sum(not t['passed'] for t in paired), 'original_mention_failures': sum(not v for v in integrity),
                  'temporal_role_losses': sum(not v for v in times), 'saved_expression_changes': sum(not v for v in expressions),
                  'protected_fact_losses': sum(fact_losses),
                  'introduced_location_fp': sum(len(r['introduced_fp']) for r in training),
                  'lost_correct_locations': sum(len(r['lost_correct']) for r in training),
                  'introduced_association_fp': sum(len(r['introduced_fp']) for r in comparisons),
                  'lost_supported_associations': sum(len(r['lost_correct']) for r in comparisons),
                  'qualifier_losses': sum(len(r['qualifier_errors']) for r in comparisons) + len(art['qualifier_losses']),
                  'span_regressions': sum(len(v[k]) for r in comparisons for v in r['expression_regressions'].values() for k in ('new_fp', 'new_fn')) + len(art['span_regressions']),
                  'article_unsupported_proposals': len(art['new_unsupported_proposals']), 'article_incorrect_links': len(art['new_incorrect_links']),
                  'article_fact_losses': len(art['source_fact_losses']), 'previous_complete_row_losses': len(art['previous_complete_row_losses']),
                  'invented_unmeasured_depth': len(art['invented_unmeasured_depth']), 'dateline_error': int(art['dateline_error']),
                  'historic_recovery_losses': sum(r['disposition'] == 'lost_predecessor_recovery' for r in historic)}
        gains = sum(len(r['gained_correct']) for r in training) + art['corrected_occurrences']
        blockers = [k for k, v in checks.items() if v]
        if not gains: blockers.append('no_supported_real_correction')
        methods[method] = {'qualified_for_later_proposal': not blockers, 'blockers': blockers, 'checks': checks,
                           'recognition_counts': {s: {k: sum(r[s][k] for r in training) for k in ('tp', 'fp', 'fn')} for s in ('baseline', 'candidate')},
                           'association_counts': {k: sum(r['counts'][k] for r in comparisons) for k in ('tp', 'fp', 'fn')},
                           'candidate_fixtures': {g: {'passed': sum(t['passed'] for t in ts), 'total': len(ts)} for g, ts in tests.items()},
                           'paired_view_checks': {'passed': sum(t['passed'] for t in paired), 'total': 3},
                           'original_mention_checks': {'passed': sum(integrity), 'total': len(integrity)},
                           'article': {k: art[k] for k in ('corrected_occurrences', 'restored_rows', 'restored_facts', 'remaining_unresolved_rows', 'facts_accounted')},
                           'historical_seven': dict(Counter(r['disposition'] for r in historic))}
        details[method] = {'training': training, 'contexts': comparisons, 'candidate_fixtures': tests, 'paired_views': paired,
                           'article': art, 'historical_seven': historic}
    summary = {'status': 'scoring_reassessment_completed', 'methods': methods,
               'control_checks': {g: {'passed': sum(t['passed'] for t in ts), 'total': len(ts)} for g, ts in controls.items()},
               'saved_raw_records': 788, 'fictional_cases': 418, 'repaired_view_expectations': 3, 'eligible_context_references': 23,
               'three_holds_retained': True, 'extraction_calls': 0, 'inference': False, 'worker_rerun': False,
               'historical_v44_unchanged': True, 'supersedes_scoring_interpretation_only': True, 'backend_promoted': False,
               'already_exposed_evidence_not_independent_accuracy': True}
    write(destination/'summary.json', summary); write(destination/'private-details.json', details)
    write(destination/'control-checks.json', controls)
    return summary
