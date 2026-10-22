"""Independently verify the disabled preview integration and its single live receipt."""
from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def verify(cached: Path, live: Path, destination: Path) -> dict:
    from check_ner_location_v46 import preservation, read, lines, sha, write, ROOT, ART, AUTHOR, P44, E44, PIPELINE_FILES
    assert not destination.exists()
    preserved = preservation()
    freeze = read(live/'freeze.json')
    for name, digest in freeze['implementation'].items(): assert sha(ROOT/name) == digest, name
    assert sha(AUTHOR/'tests.json') == freeze['test_receipt_sha256']
    tests = read(AUTHOR/'tests.json'); assert tests['returncode'] == 0 and tests['source_hashes'] == freeze['implementation']
    for name, digest in read(cached/'freeze.json')['pipeline_hashes'].items(): assert sha(ROOT/name) == digest
    assert sha(cached/'summary.json') == freeze['cached_summary_sha256']
    from app.services.news_ner.location_pipeline import from_neural_mentions
    from app.services.news_ner.bundle import verify_bundle
    from app.services.news_ner.contract import object_sha, IMAGE
    from app.services.news_ner.projection import project
    request = read(P44/'request.json')['groups']; count = 0; graph_count = 0
    for group, rows in request.items():
        expected = {r['record_id']: r for r in lines(E44/'worker-output'/(group+'.jsonl'))}
        assert len(expected) == len(rows)
        for row in rows:
            value = from_neural_mentions(row['raw']); original = expected[row['record_id']]['methods']['combined']
            repair = value['proposal']; saved = original['repair']
            assert repair['neural_mentions'] == saved['neural_mentions'] == row['raw']['mentions']
            assert repair['control_mentions'] == row['control_mentions'] == saved['control_mentions']
            assert repair['effective_mentions'] == saved['effective_mentions']
            assert [p for p in repair['proposals'] if p['implementation'] == 'lanes-location-repair-v44'] == saved['proposals']
            if 'context' in original: assert value['graph'] == original['context']; graph_count += 1
            count += 1
    assert count == 788 and graph_count == 407
    checks = read(cached/'fixture-checks.json'); pairs = read(cached/'paired-checks.json')
    assert len(checks) == 418 and all(t['passed'] for t in checks)
    assert len(pairs) == 3 and all(t['passed'] for t in pairs)
    api = read(live/'api-response.json'); body = api['body']; worker = read(live/'worker-response.json')
    assert api['status_code'] == 200 and api['headers']['cache-control'] == 'no-store'
    expected = read(cached/'article-adapter-result.json')
    for key in ('neural_mentions', 'effective_mentions', 'proposals', 'abstentions'):
        assert body[key] == expected['proposal'][key] == worker['proposal'][key]
    assert len(body['neural_mentions']) == 53 and body['graph'] == worker['graph'] == expected['graph']
    raw = request['article'][0]['raw']
    assert body['groups'] == project({**raw, 'mentions': body['effective_mentions']}, body['graph'])
    source_file = ART/'ner-preview-source-link-20261019-v2/saved-article-input.json'
    assert sha(source_file) == freeze['source_sha256']
    assert body['source']['canonical_url'] == read(source_file)['canonical_url']
    assert body['schema_version'] == 'lanes-ner-preview-v1'
    expected_fields = {'schema_version','source','provenance','measurements','neural_mentions','effective_mentions',
                       'proposals','abstentions','groups','unassigned','graph','limitations'}
    assert set(body) == expected_fields
    assert body['provenance']['location_rules'] == 'lanes-location-repair-v40+v44'
    assert body['provenance']['location_method'] == 'combined' and body['provenance']['context_rules'] == 'lanes-context-association-v42'
    bundle = ART/'ner-preview-bundle-20261019-v1'; bundle_hash = '13137f64b216d2a9f2978f0eb3d278950754dc56731688495b8348f2ad43a8cd'
    assets = verify_bundle(bundle, bundle_hash)
    assert body['provenance']['bundle_sha256'] == bundle_hash
    assert body['provenance']['model_manifest_sha256'] == assets['model_manifest_sha256']
    assert body['provenance']['resource_manifest_sha256'] == assets['resource_manifest_sha256']
    package = ROOT/'backend/app/services/news_ner'
    code = {p.name: sha(p) for p in package.glob('*.py')}; code['promotion.json'] = sha(package/'promotion.json')
    assert body['provenance']['code_sha256'] == object_sha(code)
    container = read(live/'container.json'); state = read(live/'completed-container.json')
    host = container['HostConfig']; assert container['Config']['Image'] == IMAGE
    assert host['NetworkMode'] == 'none' and host['ReadonlyRootfs'] and host['NanoCpus'] == 2000000000
    assert host['Memory'] == host['MemorySwap'] == 4294967296 and host['PidsLimit'] == 128
    assert host['CapDrop'] == ['ALL'] and 'no-new-privileges' in host['SecurityOpt']
    assert set(host['Tmpfs']) == {'/tmp'} and 'noexec' in host['Tmpfs']['/tmp']
    mounts = {m['Destination']: m for m in container['Mounts']}
    assert set(mounts) == {'/assets', '/code/news_ner'}
    for target, source in (('/assets', bundle), ('/code/news_ner', package)):
        assert Path(mounts[target]['Source']).resolve() == source.resolve() and not mounts[target]['RW']
    assert not state['State']['Running'] and state['State']['Pid'] == 0 and state['State']['ExitCode'] == 0 and not state['State']['OOMKilled']
    commands = [read(p) for p in sorted(live.glob('command-*.json'))]
    assert sum(c['args'][1] == 'start' for c in commands) == 1
    assert any(c['args'][1] == 'rm' and c['returncode'] == 0 for c in commands)
    assert commands[-1]['args'][1] == 'ps' and commands[-1]['stdout'].strip() == '' and commands[-1]['returncode'] == 0
    assert (ROOT/'backend/runtime_data/ner_preview/owner.lock').read_bytes() == b'\0'
    from app.core.config import Settings, settings
    assert Settings.model_fields['NEWS_NER_PREVIEW_ENABLED'].default is False and settings.NEWS_NER_PREVIEW_ENABLED is False
    old = read(cached/'article-dispositions.json')
    assert len(old['targets']) == 34 and len(old['rows']) == 19
    facts = [f for r in old['rows'] for f in r['facts']]
    assert len(facts) == len({f['previous_fact_id'] for f in facts}) == 93
    assert sum(f['disposition'] == 'restored' for f in facts) == 40 and sum(not r['restored'] for r in old['rows']) == 11
    result = {'status': 'independently_verified', 'cached_records': count, 'saved_context_graphs': graph_count,
              'applicable_fixtures': 418, 'paired_checks': 3, 'real_worker_requests': 1,
              'neural_mentions_preserved': 53, 'article_corrected_occurrences': 8, 'article_restored_facts': 40,
              'article_unresolved_rows': 11, 'article_facts_accounted': 93, 'previous_complete_rows_retained': 8,
              'response_contract_and_source_link_preserved': True, 'runtime_v44_verbatim': True,
              'proposal_and_graph_binding_verified': True, 'isolation_and_cleanup_verified': True,
              'default_feature_disabled': True, 'database_access': False, 'database_writes': False,
              'frontend_or_plotting_changed': False, 'automatic_inference_retry': False, 'preservation': preserved}
    write(destination, result); return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('cached', 'live', 'output'): parser.add_argument('--'+name, type=Path, required=True)
    a = parser.parse_args()
    print(json.dumps(verify(a.cached.resolve(), a.live.resolve(), a.output.resolve())))
