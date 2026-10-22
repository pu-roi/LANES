"""Verify saved v44 evidence without extraction, inference or database access."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'backend'))


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def verify(package: Path, execution: Path, analysis: Path, destination: Path) -> dict:
    from training.flood_ner.location_repair_study_v44 import check, WORKER
    check(package)
    assert not destination.exists()
    for b in read(execution/'output-manifest.json')['files']:
        assert hashlib.sha256((ROOT/b['path']).read_bytes()).hexdigest() == b['sha256']
    for b in read(analysis/'manifest.json')['files']:
        assert hashlib.sha256((ROOT/b['path']).read_bytes()).hexdigest() == b['sha256']
    request = read(package/'request.json')['groups']; total = proposals = graphs = 0
    for group, rows in request.items():
        saved = [json.loads(line) for line in (execution/'worker-output'/(group+'.jsonl')).read_text(encoding='utf-8').splitlines()]
        assert len(saved) == len(rows) and {r['record_id'] for r in saved} == {r['record_id'] for r in rows}
        by_id = {r['record_id']: r for r in saved}; assert len(by_id) == len(rows)
        for row in rows:
            raw = row['raw']; text = raw['text']; out = by_id[row['record_id']]
            assert hashlib.sha256(text.encode()).hexdigest() == raw['text_sha256']
            for method, item in out['methods'].items():
                repair = item['repair']
                assert repair['method'] == method and repair['record_id'] == row['record_id']
                assert repair['neural_mentions'] == raw['mentions'] and repair['control_mentions'] == row['control_mentions']
                assert repair['text_sha256'] == raw['text_sha256']
                changes = {p['original_mention_id']: p for p in repair['proposals'] if p['original_mention_id']}
                assert len(changes) == sum(bool(p['original_mention_id']) for p in repair['proposals'])
                expected = []
                for m in row['control_mentions']:
                    p = changes.get(m['id'])
                    expected.append(m if p is None else {'id': m['id'], **{k: p[k] for k in ('start', 'end', 'text', 'label', 'provenance_sha256')}})
                for p in repair['proposals']:
                    assert p['origin'] == 'rule_proposal_not_neural' and p['implementation'] == 'lanes-location-repair-v44'
                    assert text[p['start']:p['end']] == p['text']
                    e = p['evidence']; assert text[e['start']:e['end']] == e['text']
                    assert e['start'] <= p['start'] < p['end'] <= e['end']
                    content = {k: v for k, v in p.items() if k != 'provenance_sha256'}
                    digest = hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
                    assert digest == p['provenance_sha256']
                    if p['action'] == 'add':
                        assert p['original_mention_id'] is None
                        expected.append({'id': 'v44-'+digest[:24], **{k: p[k] for k in ('start', 'end', 'text', 'label', 'provenance_sha256')}})
                    else: assert p['original_mention_id'] in {m['id'] for m in row['control_mentions']}
                expected.sort(key=lambda m: (m['start'], m['end']))
                assert expected == repair['effective_mentions']
                assert len({m['id'] for m in expected}) == len(expected)
                stop = 0
                for m in expected:
                    assert stop <= m['start'] < m['end'] and text[m['start']:m['end']] == m['text']; stop = m['end']
                proposals += len(repair['proposals'])
                if 'context' in item:
                    graph = item['context']; assert graph['mentions'] == expected and graph['text_sha256'] == raw['text_sha256']
                    for e in graph['expressions']: assert text[e['start']:e['end']] == e['text']
                    for f in graph['facts']:
                        for e in f['evidence']: assert text[e['start']:e['end']] == e['text']
                    assert not graph['absolute_instants'] and not graph['numeric_depths']; graphs += 1
            total += 1
    assert total == 788
    summary = read(analysis/'summary.json'); details = read(analysis/'private-details.json')
    f40 = read(ROOT/'backend/training/flood_ner/artifacts/location-repair-prepared-20261019-v40/freeze.json')
    refs = {r['record_id']: r for r in [json.loads(s) for s in (ROOT/f40['training_references']['path']).read_text(encoding='utf-8').splitlines()]}
    training_outputs = {r['record_id']: r for r in [json.loads(s) for s in (execution/'worker-output/training.jsonl').read_text(encoding='utf-8').splitlines()]}
    key = lambda m: (m['start'], m['end'], m['label'])
    for method, result in summary['methods'].items():
        totals = {'baseline': Counter(tp=0, fp=0, fn=0), 'candidate': Counter(tp=0, fp=0, fn=0)}
        fps = lost = 0
        for row in request['training']:
            rid = row['record_id']; gold = {tuple(s) for s in refs[rid]['reference']}
            before = {key(m) for m in row['control_mentions']}
            after = {key(m) for m in training_outputs[rid]['methods'][method]['repair']['effective_mentions']}
            for name, mentions in (('baseline', before), ('candidate', after)):
                totals[name].update(tp=len(gold & mentions), fp=len(mentions-gold), fn=len(gold-mentions))
            fps += len((after-gold)-(before-gold)); lost += len((before & gold)-after)
        assert {k: dict(v) for k, v in totals.items()} == result['recognition_counts']
        assert fps == result['checks']['introduced_location_fp'] and lost == result['checks']['lost_correct_locations']
        art = details[method]['article']
        assert len(art['targets']) == 34 and len(art['rows']) == 19
        ids = [f['previous_fact_id'] for r in art['rows'] for f in r['facts']]
        assert len(ids) == len(set(ids)) == 93 and len(details[method]['historical_seven']) == 7
        assert result['article']['restored_facts'] == sum(f['disposition'] == 'restored' for r in art['rows'] for f in r['facts'])
        for group, ts in details[method]['fixtures'].items():
            assert result['fixtures'][group] == {'passed': sum(t['passed'] for t in ts), 'total': len(ts)}
        assert result['qualified_for_later_proposal'] == (not result['blockers'])
    container = json.loads(read(execution/'container.json')['stdout'])[0]; host = container['HostConfig']
    assert host['NetworkMode'] == 'none' and host['ReadonlyRootfs'] and host['NanoCpus'] == 2000000000
    assert host['Memory'] == host['MemorySwap'] == 4294967296
    mounts = {m['Destination']: m for m in container['Mounts']}
    expected_mounts = {'/code/'+n: ROOT/p for n, p in WORKER.items()}
    expected_mounts.update({'/input': execution/'input', '/output': execution/'worker-output'})
    assert set(mounts) == set(expected_mounts)
    for target, source in expected_mounts.items():
        assert Path(mounts[target]['Source']).resolve() == source.resolve()
        assert mounts[target]['RW'] == (target == '/output')
    state = json.loads(read(execution/'completed-state.json')['stdout'])[0]['State']
    assert not state['Running'] and state['Pid'] == 0 and state['ExitCode'] == 0 and not state['OOMKilled']
    result = {'status': 'independently_verified', 'raw_records': total, 'candidate_context_graphs': graphs,
              'proposal_records': proposals, 'training_counts_recomputed': True, 'source_offsets_provenance_verified': True,
              'article_occurrences_per_method': 34, 'article_rows_per_method': 19, 'article_facts_per_method': 93,
              'historical_misses_per_method': 7, 'preservation': summary['preservation'],
              'isolation_verified': True, 'worker_stopped': True, 'three_holds_retained': True,
              'freeze_sha256': hashlib.sha256((package/'freeze.json').read_bytes()).hexdigest(),
              'extraction_or_inference_rerun': False, 'backend_promoted': False}
    with destination.open('x', encoding='utf-8') as stream: json.dump(result, stream, indent=2); stream.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('package', 'execution', 'analysis', 'output'): parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.package.resolve(), args.execution.resolve(), args.analysis.resolve(), args.output.resolve())))
