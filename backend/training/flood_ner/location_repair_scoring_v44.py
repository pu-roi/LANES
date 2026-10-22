"""Reference-side scoring. This module is never mounted in the worker."""
from collections import Counter

from .context_association_scoring import output_keys, span_key
from .context_review_v37 import fixture_result
from .context_cases_v41 import result as result41
from .context_cases_v42 import result as result42
from .location_repair_cases_v44 import result as result44
from .location_repair_scoring_v40 import recognition, context, temporal_result, location_result
from .location_repair_v44 import METHODS


def freeze_key(value: object) -> object:
    return tuple(freeze_key(v) for v in value) if isinstance(value, list) else value


def fact_key(fact: dict, graph: dict, *, evidence: bool = True) -> tuple:
    expressions = {e['id']: e for e in graph['expressions']}
    key = (fact['kind'], fact['value'], fact['temporal_role'], fact['depth_scope'],
           tuple(span_key(expressions[i]) for i in fact['entity_ids']))
    return key + (tuple((e['start'], e['end']) for e in fact['evidence']),) if evidence else key


def article_result(raw: dict, control: dict, graph: dict, repair: dict, ledger: dict, oracle: dict) -> dict:
    """Exact saved source dispositions; no inferred or revised reference labels."""
    from app.services.news_ner.context_association_v42 import validate_output
    validate_output({**raw, 'mentions': repair['effective_mentions']}, graph)
    text = raw['text']; mentions = graph['mentions']; rels = {r['fact_id']: r for r in graph['relations']}
    baseline = {fact_key(f, control): f for f in control['facts']}
    after = {fact_key(f, graph): f for f in graph['facts']}
    lost = [k for k in baseline if k not in after]
    qualifier_losses = [k for k, f in baseline.items() if k in after and
                        not all(any(q.casefold() in a.casefold() for a in after[k]['qualifiers']) for q in f['qualifiers'])]
    before_spans = {span_key(e) for e in control['expressions']}
    span_regressions = before_spans ^ {span_key(e) for e in graph['expressions']}
    targets = []; by_target = {}
    for item in ledger['target_occurrences']:
        s = item['source_span']; assert text[s['start']:s['end']] == s['text']
        exact = [m for m in mentions if (m['start'], m['end']) == (s['start'], s['end']) and
                 m['label'] in {'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY'}]
        before = [m for m in control['mentions'] if (m['start'], m['end']) == (s['start'], s['end']) and
                  m['label'] in {'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY'}]
        value = {'target_id': item['target_id'], 'source_span': s, 'cause': item['cause'],
                 'meaning_review_retained': item['label_or_meaning_review_required'], 'complete': len(exact) == 1,
                 'corrected': not before and len(exact) == 1, 'effective_ids': [m['id'] for m in exact]}
        targets.append(value); by_target[item['target_id']] = value
    source_allowed = {(t['source_span']['start'], t['source_span']['end']) for t in ledger['target_occurrences']
                      if not t['label_or_meaning_review_required']}
    bad_proposals = [p for p in repair['proposals'] if (p['start'], p['end']) not in source_allowed]
    rows = []; accounted = []; wrong_links = []; recovered = 0
    for row in ledger['rows']:
        all_complete = all(by_target[i]['complete'] for i in row['target_ids'])
        ids = [by_target[i]['effective_ids'][0] for i in row['target_ids']] if all_complete else []
        facts = []
        for before in row['facts_preserved_unassigned']:
            key = fact_key(before, control)
            candidates = [f for f in graph['facts'] if fact_key(f, graph) == key]
            relation = rels.get(candidates[0]['id']) if len(candidates) == 1 else None
            actual = relation['target_entity_ids'] if relation else []
            supported = actual == ids and (not ids or relation['scope'] == ('collective' if len(ids) > 1 else 'local'))
            if not supported: wrong_links.append({'row_id': row['row_id'], 'fact_id': before['id'], 'actual_targets': actual, 'expected_targets': ids})
            disposition = 'restored' if ids and supported and len(candidates) == 1 else 'preserved_unassigned' if not ids and len(candidates) == 1 and not relation else 'failed'
            facts.append({'previous_fact_id': before['id'], 'kind': before['kind'], 'disposition': disposition})
            accounted.append(before['id'])
        restored = bool(ids) and all(f['disposition'] == 'restored' for f in facts)
        recovered += int(restored)
        rows.append({'row_id': row['row_id'], 'all_targets_complete': all_complete, 'restored': restored, 'facts': facts})
    assert len(accounted) == len(set(accounted)) == 93 and len(targets) == 34 and len(rows) == 19
    # Preserve all eight originally complete measured rows, checked by original
    # source fact signatures and original target identities, not recovery counts.
    complete_lost = []
    for row in oracle['measured_rows']:
        if not row['targets']: continue
        for f in control['facts']:
            r = next((r for r in control['relations'] if r['fact_id'] == f['id']), None)
            if not r or r['target_entity_ids'] != row['targets'] or not any(e['end'] == row['end'] for e in f['evidence']): continue
            candidate = after.get(fact_key(f, control)); nr = rels.get(candidate['id']) if candidate else None
            if not nr or nr['target_entity_ids'] != r['target_entity_ids'] or nr['scope'] != r['scope']: complete_lost.append(f['id'])
    unmeasured = oracle['unmeasured_junction']
    invented_depth = [f['id'] for f in graph['facts'] if f['kind'] == 'depth' and any(e['end'] == unmeasured['end'] for e in f['evidence'])]
    dateline = any(set(r['target_entity_ids']) & set(oracle['dateline_ids']) for r in graph['relations'])
    return {'targets': targets, 'rows': rows, 'corrected_occurrences': sum(t['corrected'] for t in targets),
            'restored_rows': recovered, 'restored_measured_rows': sum(r['restored'] and r['row_id'] != 'unmeasured' for r in rows),
            'restored_unmeasured_rows': sum(r['restored'] and r['row_id'] == 'unmeasured' for r in rows),
            'restored_facts': sum(f['disposition'] == 'restored' for r in rows for f in r['facts']),
            'remaining_unresolved_rows': sum(not r['restored'] for r in rows), 'facts_accounted': 93,
            'new_unsupported_proposals': bad_proposals, 'new_incorrect_links': wrong_links,
            'source_fact_losses': lost, 'qualifier_losses': qualifier_losses, 'span_regressions': sorted(span_regressions),
            'previous_complete_row_losses': complete_lost, 'invented_unmeasured_depth': invented_depth, 'dateline_error': dateline}


def score(package, execution, destination) -> dict:
    from .location_repair_study_v44 import check, read, lines, write, bound, ROOT, ART, P40, P42, E42, A43, preserved
    assert not destination.exists(); check(package)
    for b in read(execution/'output-manifest.json')['files']: assert __import__('hashlib').sha256((ROOT/b['path']).read_bytes()).hexdigest() == b['sha256']
    groups = read(package/'request.json')['groups']; outputs = {}
    for group, inputs in groups.items():
        rows = lines(execution/'worker-output'/(group+'.jsonl'))
        assert len(rows) == len(inputs) and len({r['record_id'] for r in rows}) == len(rows)
        outputs[group] = {r['record_id']: r for r in rows}
        assert set(outputs[group]) == {r['record_id'] for r in inputs}
    f40 = read(P40/'freeze.json')
    references = {r['record_id']: r for r in lines(ROOT/f40['training_references']['path'])}
    refs = read(ROOT/f40['context_references']['path'])
    fixtures = {'location_fixtures': read(P40/'location-fixtures.json'), 'existing': read(ROOT/f40['existing_fixtures']['path']),
                'temporal': read(P40/'temporal-fixtures.json'),
                'v41': read(ART/'context-repair-prepared-20261019-v41/new-fixtures.json'),
                'v42': read(P42/'new-fixtures.json'), 'new': read(package/'new-fixtures.json')}
    previous_contexts = {r['record_id']: r for r in lines(E42/'worker-output/context_rows.jsonl')}
    seven = read(ROOT/f40['seven_errors']['path'])
    assert len(seven) == 7 and len(refs) == 23
    # Check saved predecessor controls and the original view without scoring holds.
    for r in groups['contexts']:
        output = outputs['contexts'][r['record_id']]; old = previous_contexts[r['record_id']]['views']
        assert output['original'] == old['original'] and output['control'] == old['combined']
    ledger = read(A43/'case-ledger.json'); oracle = read(P42/'article-oracle.json')
    article_raw = groups['article'][0]['raw']; article = outputs['article'][article_raw['record_id']]
    article_baseline = lines(E42/'worker-output/article_rows.jsonl')[0]['output']; assert article['control'] == article_baseline
    details = {}; methods = {}
    for method in METHODS:
        training = []
        for row in groups['training']:
            rid = row['record_id']; ref = references[rid]
            assert ref['text_sha256'] == row['raw']['text_sha256'] and ref['partition'] == 'train'
            repair = outputs['training'][rid]['methods'][method]['repair']
            training.append({'record_id': rid, **recognition(ref['reference'], row['control_mentions'], repair['effective_mentions'])})
        comparisons = []
        for ref in refs:
            rid = ref['record_id']; out = outputs['contexts'][rid]
            comparisons.append({'record_id': rid, **context(ref['revised_reference'], out['control'], out['methods'][method]['context'])})
        tests = {}
        for group, cases in fixtures.items():
            tests[group] = []
            for case in cases:
                if group == 'existing':
                    import hashlib
                    rid = 'fictional-'+hashlib.sha256(case['case_id'].encode()).hexdigest()[:20]
                else: rid = case['raw']['record_id']
                result = outputs[group][rid]['methods'][method]; graph = result.get('context')
                if group == 'new': value = result44(case, result['repair'])
                elif group == 'location_fixtures': value = location_result(case, result['repair'])
                elif group == 'existing':
                    raw = next(r for r in groups[group] if r['record_id'] == rid)['raw']
                    value = fixture_result(case, {**raw, 'mentions': result['repair']['effective_mentions']}, graph,
                                           exhaustive=case['case_id'].startswith(('fictional-v36_', 'fictional-v37_', 'fictional-v38_')))
                elif group == 'temporal': value = temporal_result(case, graph)
                elif group == 'v41': value = result41(case, graph)
                else: value = result42(case, graph)
                tests[group].append(value)
        art = article_result(article_raw, article['control'], article['methods'][method]['context'],
                             article['methods'][method]['repair'], ledger, oracle)
        historic = []
        for e in seven:
            rid = e['opaque_id']; out = outputs['contexts'][rid]
            key = freeze_key(e['strict_key'])
            oldkeys = output_keys(out['control'])['links']; newkeys = output_keys(out['methods'][method]['context'])['links']
            historic.append({'error_id': e['error_id'], 'disposition': 'retained_recovery' if key in oldkeys and key in newkeys else
                             'lost_predecessor_recovery' if key in oldkeys else 'newly_recovered' if key in newkeys else 'still_unresolved'})
        checks = {'new_fixture_failures': sum(not t['passed'] for t in tests['new']),
                  'preserved_location_fixture_failures': sum(not t['passed'] for t in tests['location_fixtures']),
                  'preserved_context_temporal_failures': sum(not t['passed'] for group in ('existing', 'temporal', 'v41', 'v42') for t in tests[group]),
                  'introduced_location_fp': sum(len(r['introduced_fp']) for r in training),
                  'lost_correct_locations': sum(len(r['lost_correct']) for r in training),
                  'introduced_association_fp': sum(len(r['introduced_fp']) for r in comparisons),
                  'lost_correct_associations': sum(len(r['lost_correct']) for r in comparisons),
                  'qualifier_losses': sum(len(r['qualifier_errors']) for r in comparisons) + len(art['qualifier_losses']),
                  'expression_regressions': sum(len(v[k]) for r in comparisons for v in r['expression_regressions'].values() for k in ('new_fp', 'new_fn')) + len(art['span_regressions']),
                  'article_unsupported_proposals': len(art['new_unsupported_proposals']),
                  'article_incorrect_links': len(art['new_incorrect_links']), 'article_fact_losses': len(art['source_fact_losses']),
                  'article_previously_complete_losses': len(art['previous_complete_row_losses']),
                  'article_invented_depth': len(art['invented_unmeasured_depth']), 'article_dateline_error': int(art['dateline_error']),
                  'historic_recovery_losses': sum(r['disposition'] == 'lost_predecessor_recovery' for r in historic)}
        gains = sum(len(r['gained_correct']) for r in training) + art['corrected_occurrences']
        blockers = [k for k, v in checks.items() if v]
        if not gains: blockers.append('no_supported_real_correction')
        methods[method] = {'qualified_for_later_proposal': not blockers, 'blockers': blockers, 'checks': checks,
                           'recognition_counts': {s: {k: sum(r[s][k] for r in training) for k in ('tp', 'fp', 'fn')} for s in ('baseline', 'candidate')},
                           'gained_correct_training_locations': sum(len(r['gained_correct']) for r in training),
                           'association_counts': {k: sum(r['counts'][k] for r in comparisons) for k in ('tp', 'fp', 'fn')},
                           'fixtures': {g: {'passed': sum(t['passed'] for t in ts), 'total': len(ts)} for g, ts in tests.items()},
                           'article': {k: art[k] for k in ('corrected_occurrences', 'restored_rows', 'restored_measured_rows', 'restored_unmeasured_rows', 'restored_facts', 'remaining_unresolved_rows', 'facts_accounted')},
                           'historical_seven': dict(Counter(r['disposition'] for r in historic))}
        details[method] = {'training': training, 'contexts': comparisons, 'fixtures': tests, 'article': art, 'historical_seven': historic}
    summary = {'status': 'completed', 'methods': methods, 'raw_records': 788, 'three_holds_retained': True,
               'independent_accuracy_measurement': False, 'exposed_training_and_constructed_checks': True,
               'neural_inference': False, 'backend_promoted': False, 'no_post_result_tuning': True, 'preservation': preserved()}
    destination.mkdir(); write(destination/'summary.json', summary); write(destination/'private-details.json', details)
    write(destination/'manifest.json', {'files': [bound(p) for p in sorted(destination.iterdir()) if p.is_file()]})
    return summary
