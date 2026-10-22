"""Independent saved-evidence checks for v45; no worker or extraction execution."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'backend'))


def verify(package: Path, analysis: Path, destination: Path) -> dict:
    from training.flood_ner.location_reanalysis_v45 import (check, read, lines, write, ART, P44, E44, A44,
        NoNeuralDatabase, forbid_extraction, forbid_external_actions, sha)
    check(package); assert not destination.exists()
    for b in read(analysis/'manifest.json')['files']: assert sha(ROOT/b['path']) == b['sha256']
    prior = sys.getprofile(); guard = NoNeuralDatabase(); sys.meta_path.insert(0, guard)
    sys.addaudithook(forbid_external_actions); sys.setprofile(forbid_extraction)
    try:
        spec = importlib.util.spec_from_file_location('saved_v44_verifier', ROOT/'backend/scripts/verify_location_v44.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        old_receipt = module.verify(P44, E44, A44, analysis/'v44-evidence-reverification.json')
        request = read(P44/'request.json')['groups']; summary = read(analysis/'summary.json')
        details = read(analysis/'private-details.json'); controls = read(analysis/'control-checks.json')
        assert sum(len(ts) for ts in controls.values()) == 418
        assert all(t['passed'] for ts in controls.values() for t in ts)
        for group, ts in controls.items():
            assert summary['control_checks'][group] == {'passed': sum(t['passed'] for t in ts), 'total': len(ts)}
        outputs = {g: {r['record_id']: r for r in lines(E44/'worker-output'/(g+'.jsonl'))} for g in request}
        f40 = read(ART/'location-repair-prepared-20261019-v40/freeze.json')
        refs = {r['record_id']: r for r in lines(ROOT/f40['training_references']['path'])}
        context_refs = read(ROOT/f40['context_references']['path'])
        cases = read(P44/'new-fixtures.json'); oracles = {o['case_id']: o for o in read(package/'repaired-expectations.json')}
        assert len(oracles) == 3
        from training.flood_ner.context_association_scoring import output_keys, reference_keys
        for method, result in summary['methods'].items():
            totals = {'baseline': Counter(tp=0, fp=0, fn=0), 'candidate': Counter(tp=0, fp=0, fn=0)}
            new_fp = lost = 0
            for row in request['training']:
                rid = row['record_id']; gold = {tuple(s) for s in refs[rid]['reference']}
                before = {(m['start'], m['end'], m['label']) for m in row['control_mentions']}
                after = {(m['start'], m['end'], m['label']) for m in outputs['training'][rid]['methods'][method]['repair']['effective_mentions']}
                for name, mentions in (('baseline', before), ('candidate', after)):
                    totals[name].update(tp=len(gold & mentions), fp=len(mentions-gold), fn=len(gold-mentions))
                new_fp += len((after-gold)-(before-gold)); lost += len((before & gold)-after)
            assert {k: dict(v) for k, v in totals.items()} == result['recognition_counts']
            assert new_fp == result['checks']['introduced_location_fp'] and lost == result['checks']['lost_correct_locations']
            totals = Counter(tp=0, fp=0, fn=0); new_fp = lost = 0
            for ref in context_refs:
                output = outputs['contexts'][ref['record_id']]
                gold = reference_keys(ref['revised_reference'])['links']
                before = output_keys(output['control'])['links']; after = output_keys(output['methods'][method]['context'])['links']
                totals.update(tp=len(gold & after), fp=len(after-gold), fn=len(gold-after))
                new_fp += len((after-gold)-(before-gold)); lost += len((before & gold)-after)
            assert dict(totals) == result['association_counts']
            assert new_fp == result['checks']['introduced_association_fp'] and lost == result['checks']['lost_supported_associations']
            for case in cases:
                saved = outputs['new'][case['raw']['record_id']]['methods'][method]['repair']
                expected = case['expected_mentions'] if method in (case['family'], 'combined') else [
                    (m['start'], m['end'], m['label']) for m in case['raw']['mentions']]
                actual = [(m['start'], m['end'], m['label']) for m in saved['effective_mentions']]
                assert sorted(tuple(s) for s in expected) == sorted(actual)
            assert result['candidate_fixtures']['new'] == {'passed': 36, 'total': 36}
            enabled = 0
            for identity, oracle in oracles.items():
                saved = outputs['v42'][identity]; control = saved['control']
                assert not control['relations'] and all(f['kind'] == 'depth' for f in control['facts'])
                if method not in (oracle['family_enabled'], 'combined'):
                    assert saved['methods'][method]['context'] == control
                    continue
                enabled += 1; graph = saved['methods'][method]['context']
                wanted = sorted((s['start'], s['end'], s['label']) for s in oracle['target_spans'])
                assert sorted((m['start'], m['end'], m['label']) for m in graph['mentions']) == wanted
                mentions = {m['id']: m for m in graph['mentions']}; rel = {r['fact_id']: r for r in graph['relations']}
                expr = {e['id']: e for e in graph['expressions']}
                wanted_depth = sorted((s['start'], s['end'], s['text']) for s in oracle['depth_spans'])
                actual_depth = []
                for f in graph['facts']:
                    assert f['kind'] == 'depth' and f['temporal_role'] is None
                    actual_depth += [(expr[i]['start'], expr[i]['end'], expr[i]['text']) for i in f['entity_ids']]
                    assert f['value'] == expr[f['entity_ids'][0]]['text']
                    r = rel[f['id']]; assert r['scope'] == 'collective'
                    assert sorted((mentions[i]['start'], mentions[i]['end'], mentions[i]['label']) for i in r['target_entity_ids']) == wanted
                assert sorted(actual_depth) == wanted_depth and graph['expressions'] == control['expressions']
            assert result['paired_view_checks'] == {'passed': 3, 'total': 3}
            assert enabled == (3 if method == 'combined' else 1)
            for group, ts in details[method]['candidate_fixtures'].items():
                assert result['candidate_fixtures'][group] == {'passed': sum(t['passed'] for t in ts), 'total': len(ts)}
            assert sum(len(ts) for ts in details[method]['candidate_fixtures'].values()) == 418
            art = details[method]['article']; old = read(A44/'private-details.json')[method]['article']
            assert art == old
            assert len(art['targets']) == 34 and len(art['rows']) == 19
            facts = [f for r in art['rows'] for f in r['facts']]
            assert len(facts) == len({f['previous_fact_id'] for f in facts}) == 93
            assert result['article']['restored_facts'] == sum(f['disposition'] == 'restored' for f in facts)
            assert len(details[method]['historical_seven']) == 7
            blockers = [k for k, v in result['checks'].items() if v]
            gained = sum(len(r['gained_correct']) for r in details[method]['training']) + art['corrected_occurrences']
            if not gained: blockers.append('no_supported_real_correction')
            assert result['blockers'] == blockers and result['qualified_for_later_proposal'] == (not blockers)
            if method == 'junction_type': assert not gained and not result['qualified_for_later_proposal']
        execution = read(analysis/'execution-receipt.json')
        assert execution['extraction_calls'] == 0 and not execution['worker_started'] and not execution['inference']
        check(package)
        result = {'status': 'independently_verified', 'saved_raw_records': 788, 'training_records': 345,
                  'context_records': 24, 'eligible_context_references': 23, 'fictional_cases': 418,
                  'original_control_checks': 418, 'candidate_checks_per_method': 418, 'paired_view_checks_per_method': 3,
                  'article_occurrences_per_method': 34, 'article_rows_per_method': 19, 'article_facts_per_method': 93,
                  'historical_misses_per_method': 7, 'training_and_association_counts_recomputed': True,
                  'historical_v44_source_offsets_provenance_isolation_reverified': True,
                  'preservation': old_receipt['preservation'], 'original_v44_unchanged': True,
                  'extraction_calls': 0, 'inference': False, 'worker_rerun': False, 'backend_promoted': False,
                  'freeze_sha256': sha(package/'freeze.json')}
        write(destination, result)
        return result
    finally:
        sys.setprofile(prior); sys.meta_path.remove(guard)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('package', 'analysis', 'output'): parser.add_argument('--'+name, type=Path, required=True)
    a = parser.parse_args()
    print(json.dumps(verify(a.package.resolve(), a.analysis.resolve(), a.output.resolve())))
