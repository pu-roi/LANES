"""Verify cached location parity, then one default-disabled local API integration."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'backend'))
ART = ROOT/'backend/training/flood_ner/artifacts'
AUTHOR = ART/'backend-location-authoring-20261020-v46'
P44 = ART/'location-repair-prepared-20261020-v44'
E44 = ART/'location-repair-execution-20261020-v44'
P45 = ART/'location-scoring-prepared-20261020-v45'
A45 = ART/'location-scoring-analysis-20261020-v45'
PIPELINE_FILES = ['backend/app/services/news_ner/'+n for n in (
    'location_pipeline.py', 'location_repair_v44.py', 'location_repair_v40.py', 'contract.py',
    'context_association.py', 'context_association_v38.py', 'context_association_v42.py')]
TEST_FILES = ['backend/tests/'+n for n in ('test_news_ner_preview.py', 'test_news_ner_preview_api.py',
    'test_news_ner_preview_runtime.py', 'test_context_association_v41.py', 'test_location_repair_v40.py',
    'test_context_association_v42.py', 'test_news_ner_context_v42_wiring.py', 'test_news_ner_location_v46.py')]


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path: Path) -> list[dict]:
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True); stream.write('\n')


def implementation_bindings() -> dict:
    package = ROOT/'backend/app/services/news_ner'
    code = {p.relative_to(ROOT).as_posix(): sha(p) for p in package.glob('*.py')}
    for name in ['backend/app/services/news_ner/promotion.json', 'backend/app/services/news_ner_preview_service.py',
                 'backend/app/schemas/news_ner_preview.py', 'backend/app/api/v1/endpoints/admin_news_ner.py',
                 'backend/scripts/verify_ner_location_v46.py', 'backend/scripts/check_ner_location_v46.py', *TEST_FILES]:
        code[name] = sha(ROOT/name)
    return code


def preservation() -> dict:
    from training.flood_ner.context_study_v42 import preservation as original
    preserved = original()
    before = read(AUTHOR/'preserved-application.json'); changes = []
    for name, digest in before['files'].items():
        snapshot = AUTHOR/'predecessor'/name
        assert sha(snapshot) == digest
        if sha(ROOT/name) != digest:
            assert name in before['allowed_changes'], name; changes.append(name)
    for folder in ('location-repair-prepared-20261019-v40', 'context-repair-prepared-20261019-v42',
                   'location-repair-prepared-20261020-v44', 'location-scoring-prepared-20261020-v45'):
        freeze = read(ART/folder/'freeze.json')
        for name, digest in freeze['implementation'].items(): assert sha(ROOT/name) == digest, name
    # Historical manifests/scores stay exact; a planned application update does
    # not imply that predecessor promotion hashes still describe the live app.
    for binding in read(P45/'freeze.json')['inputs']:
        assert sha(ROOT/binding['path']) == binding['sha256'], binding['path']
    for folder in (P45, A45):
        for name, digest in read(folder/'final-package-manifest.json')['files'].items():
            assert sha(folder/name) == digest, name
    old = read(ART/'context-repair-verification-20261019-v42/promotion.json')['source_hashes']
    reconciled = []
    for name, digest in old.items():
        if sha(ROOT/name) == digest: continue
        assert name in before['allowed_changes'] and sha(AUTHOR/'predecessor'/name) == digest, name
        reconciled.append(name)
    boundaries = read(AUTHOR/'boundaries.json')
    for name, digest in boundaries['hash_bound'].items(): assert sha(ROOT/name) == digest
    for name, metadata in boundaries['environment_metadata_only'].items():
        state = (ROOT/name).stat(); assert state.st_size == metadata['bytes'] and state.st_mtime_ns == metadata['mtime_ns'], name
    assert sha(ROOT/'backend/app/services/news_ner/location_repair_v44.py') == sha(ROOT/'backend/training/flood_ner/location_repair_v44.py')
    return {**preserved, 'application_snapshot_files': len(before['files']), 'planned_application_changes': sorted(changes),
            'predecessor_promotion_changes_reconciled': sorted(reconciled), 'v44_v45_frozen_evidence_unchanged': True,
            'environment_and_normal_processing_unchanged': True, 'runtime_v44_verbatim': True}


def cached(destination: Path) -> dict:
    assert not destination.exists() and destination.parent.resolve() == ART.resolve()
    kept = preservation()
    from app.services.news_ner.location_pipeline import from_neural_mentions
    from app.services.news_ner.projection import project
    from training.flood_ner.location_reassessment_v45 import original_case
    from training.flood_ner.location_scoring_v45 import location_result, repaired_result
    from training.flood_ner.location_repair_scoring_v44 import article_result
    request = read(P44/'request.json')['groups']
    fixtures = {'location_fixtures': read(ART/'location-repair-prepared-20261019-v40/location-fixtures.json'),
                'new': read(P44/'new-fixtures.json'),
                'existing': read(ART/'context-association-fixed-links-20261019-v38/fixtures-final.json'),
                'temporal': read(ART/'location-repair-prepared-20261019-v40/temporal-fixtures.json'),
                'v41': read(ART/'context-repair-prepared-20261019-v41/new-fixtures.json'),
                'v42': read(ART/'context-repair-prepared-20261019-v42/new-fixtures.json')}
    oracles = {o['case_id']: o for o in read(P45/'repaired-expectations.json')}
    by_case = {}
    for group, cases in fixtures.items():
        by_case[group] = {('fictional-'+hashlib.sha256(c['case_id'].encode()).hexdigest()[:20]
                          if group == 'existing' else c['raw']['record_id']): c for c in cases}
    destination.mkdir()
    hashes = {name: sha(ROOT/name) for name in PIPELINE_FILES}
    write(destination/'freeze.json', {'pipeline_hashes': hashes, 'request_sha256': sha(P44/'request.json'),
        'v44_output_manifest_sha256': sha(E44/'output-manifest.json'), 'v45_summary_sha256': sha(A45/'summary.json'),
        'expected_raw_records': 788, 'expected_fixtures': 418, 'expected_paired_views': 3, 'neural_inference': False})
    fixture_results = []; pairs = []; total = 0; graphs = 0; article = None
    try:
        with (destination/'parity.jsonl').open('x', encoding='utf-8') as stream:
            for group, rows in request.items():
                saved = {r['record_id']: r for r in lines(E44/'worker-output'/(group+'.jsonl'))}
                assert len(saved) == len(rows)
                for row in rows:
                    raw = row['raw']; result = from_neural_mentions(raw); proposal = result['proposal']
                    expected = saved[row['record_id']]['methods']['combined']['repair']
                    for key in ('record_id', 'text_sha256', 'method', 'neural_mentions', 'control_mentions', 'effective_mentions'):
                        assert proposal[key] == expected[key], (group, key)
                    assert [p for p in proposal['proposals'] if p['implementation'] == 'lanes-location-repair-v44'] == expected['proposals']
                    assert [dict(a, implementation='lanes-location-repair-v44') for a in expected['abstentions']] == [
                        a for a in proposal['abstentions'] if a['implementation'] == 'lanes-location-repair-v44']
                    if 'context' in saved[row['record_id']]['methods']['combined']:
                        assert result['graph'] == saved[row['record_id']]['methods']['combined']['context']; graphs += 1
                    groups = project({**raw, 'mentions': proposal['effective_mentions']}, result['graph'])
                    assigned = {f['id'] for g in groups for kind in ('depth', 'time', 'status', 'access') for f in g[kind]}
                    assert assigned | {u['fact_id'] for u in result['graph']['unassigned']} == {f['id'] for f in result['graph']['facts']}
                    if group in fixtures:
                        case = by_case[group][row['record_id']]
                        if group in {'new', 'location_fixtures'}:
                            test = location_result(case, row, proposal, conditional=group == 'new')
                        elif case['case_id'] in oracles:
                            test = repaired_result(oracles[case['case_id']], row, proposal,
                                saved[row['record_id']]['control'], result['graph']); pairs.append(test)
                        else:
                            test = original_case(case, {**row, 'control_mentions': proposal['effective_mentions']}, group, result['graph'])
                        assert test['passed'], case['case_id']; fixture_results.append({'group': group, **test})
                    if group == 'article':
                        article = article_result(raw, saved[row['record_id']]['control'], result['graph'],
                            saved[row['record_id']]['methods']['combined']['repair'],
                            read(ART/'recognition-gap-assessment-20261020-v43/case-ledger.json'),
                            read(ART/'context-repair-prepared-20261019-v42/article-oracle.json'))
                        assert (article['corrected_occurrences'], article['restored_rows'], article['restored_facts'], article['remaining_unresolved_rows']) == (8, 8, 40, 11)
                        write(destination/'article-adapter-result.json', result); write(destination/'article-dispositions.json', article)
                    stream.write(json.dumps({'group': group, 'record_id': row['record_id'], 'passed': True, 'effective_mentions': len(proposal['effective_mentions'])})+'\n')
                    total += 1
        assert total == 788 and len(fixture_results) == 418 and len(pairs) == 3 and graphs == 407
        assert hashes == {name: sha(ROOT/name) for name in PIPELINE_FILES}
        write(destination/'fixture-checks.json', fixture_results); write(destination/'paired-checks.json', pairs)
        summary = {'status': 'passed', 'cached_records': total, 'saved_context_graphs_matched': graphs, 'applicable_fixtures': 418,
                   'paired_checks': 3, 'original_control_expectations_retained_from_v45': True, 'article_corrected_occurrences': 8,
                   'article_restored_facts': 40, 'article_unresolved_rows': 11, 'article_facts_accounted': 93,
                   'neural_inference': False, 'worker_wired': False, 'preservation': kept}
        write(destination/'summary.json', summary)
        return summary
    except BaseException as exc:
        write(destination/'failure.json', {'error_type': type(exc).__name__, 'worker_wired': False, 'neural_inference': False}); raise


def live(cached_package: Path, destination: Path) -> dict:
    assert not destination.exists() and destination.parent.resolve() == ART.resolve()
    assert read(cached_package/'summary.json')['status'] == 'passed'
    for name, digest in read(cached_package/'freeze.json')['pipeline_hashes'].items(): assert sha(ROOT/name) == digest
    kept = preservation()
    destination.mkdir()
    write(ART/'backend-location-v46-live.claim.json', {'attempts': 1, 'destination': destination.name})
    package = ROOT/'backend/app/services/news_ner'
    code = implementation_bindings()
    tests = read(AUTHOR/'tests.json')
    assert tests['returncode'] == 0 and tests['source_hashes'] == code
    write(destination/'freeze.json', {'implementation': code, 'cached_summary_sha256': sha(cached_package/'summary.json'),
          'source_sha256': sha(ART/'ner-preview-source-link-20261019-v2/saved-article-input.json'), 'attempts': 1,
          'test_receipt_sha256': sha(AUTHOR/'tests.json'),
          'expected_neural_mentions': 53, 'expected_restored_facts': 40, 'database_access': False})
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api import deps
        from app.api.v1.endpoints import admin_news_ner as endpoint
        from app.core.database import get_db
        from app.core.limiter import limiter
        from app.schemas.news_ner_preview import NerPreview
        from app.services.news_ner_preview_service import preview_article
        from app.services.news_ner.projection import project
        from app.services.news_ner.contract import object_sha
        from app.services.news_ner.runtime import run_local
        from app.services.news_ner import runtime as runtime_module
        source = read(ART/'ner-preview-source-link-20261019-v2/saved-article-input.json')
        article = SimpleNamespace(**source); article.published_at = datetime.fromisoformat(source['published_at'])
        bundle = ART/'ner-preview-bundle-20261019-v1'; bundle_hash = '13137f64b216d2a9f2978f0eb3d278950754dc56731688495b8348f2ad43a8cd'
        config = SimpleNamespace(ENVIRONMENT='test', NEWS_NER_PREVIEW_ENABLED=True, NEWS_NER_PREVIEW_BUNDLE=str(bundle),
            NEWS_NER_PREVIEW_BUNDLE_SHA256=bundle_hash, NEWS_NER_PREVIEW_DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe')
        count = {'reads': 0, 'workers': 0}
        command_count = 0
        original_command = runtime_module.command
        async def record_command(args: list[str], payload: bytes | None = None, timeout: float = 10) -> tuple[int, bytes, bytes]:
            nonlocal command_count
            value = await original_command(args, payload, timeout); command_count += 1
            write(destination/f'command-{command_count:02d}.json', {'args': args, 'returncode': value[0],
                  'stdout': value[1].decode('utf-8', errors='replace')[:16384] if args[1] != 'start' else None})
            if value[0] == 0 and args[1] in {'create', 'start'}:
                target = value[1].decode().strip() if args[1] == 'create' else args[-1]
                rc, output, error = await original_command([args[0], 'inspect', target])
                assert rc == 0
                state = json.loads(output)[0]
                write(destination/('container.json' if args[1] == 'create' else 'completed-container.json'), state)
                host = state['HostConfig']; mounts = {m['Destination']: m for m in state['Mounts']}
                assert host['NetworkMode'] == 'none' and host['ReadonlyRootfs']
                assert host['Memory'] == host['MemorySwap'] == 4294967296 and host['NanoCpus'] == 2000000000
                assert host['PidsLimit'] == 128 and host['CapDrop'] == ['ALL'] and 'no-new-privileges' in host['SecurityOpt']
                assert set(mounts) == {'/assets', '/code/news_ner'} and all(not m['RW'] for m in mounts.values())
                assert Path(mounts['/assets']['Source']).resolve() == bundle.resolve()
                assert Path(mounts['/code/news_ner']['Source']).resolve() == package.resolve()
                if args[1] == 'start':
                    assert not state['State']['Running'] and state['State']['Pid'] == 0 and state['State']['ExitCode'] == 0
            return value
        class ReadOnlyStore:
            def get(self, model: object, identity: int) -> object:
                assert identity == article.id; count['reads'] += 1; return article
            def __getattr__(self, name: str) -> None: raise AssertionError('database operation prohibited: '+name)
        async def runner(*args: object) -> dict:
            count['workers'] += 1; assert count['workers'] == 1
            value = await run_local(*args)
            write(destination/'worker-response.json', value); return value
        async def service(row: object) -> NerPreview: return await preview_article(row, config, runner)
        app = FastAPI(); app.state.limiter = limiter; app.include_router(endpoint.router, prefix='/api/v1/admin/news')
        app.dependency_overrides[get_db] = lambda: ReadOnlyStore()
        app.dependency_overrides[deps.get_current_active_admin] = lambda: object()
        old_service = endpoint.preview_article; old_flag = endpoint.settings.NEWS_NER_PREVIEW_ENABLED
        old_environment = endpoint.settings.ENVIRONMENT; old_limiter = limiter.enabled
        endpoint.preview_article = service; endpoint.settings.NEWS_NER_PREVIEW_ENABLED = True
        endpoint.settings.ENVIRONMENT = 'test'; limiter.enabled = False
        runtime_module.command = record_command
        try:
            with TestClient(app) as client: response = client.post(f'/api/v1/admin/news/articles/{article.id}/ner-preview')
            write(destination/'api-response.json', {'status_code': response.status_code, 'headers': dict(response.headers), 'body': response.json()})
        finally:
            endpoint.preview_article = old_service; endpoint.settings.NEWS_NER_PREVIEW_ENABLED = old_flag
            endpoint.settings.ENVIRONMENT = old_environment; limiter.enabled = old_limiter
            runtime_module.command = original_command
        assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
        value = response.json(); expected = read(cached_package/'article-adapter-result.json')
        assert value['schema_version'] == 'lanes-ner-preview-v1' and value['source']['canonical_url'] == source['canonical_url']
        assert value['neural_mentions'] == expected['proposal']['neural_mentions'] and len(value['neural_mentions']) == 53
        assert value['effective_mentions'] == expected['proposal']['effective_mentions']
        assert value['proposals'] == expected['proposal']['proposals'] and value['abstentions'] == expected['proposal']['abstentions']
        assert value['graph'] == expected['graph']
        raw = read(P44/'request.json')['groups']['article'][0]['raw']
        assert value['groups'] == project({**raw, 'mentions': expected['proposal']['effective_mentions']}, expected['graph'])
        assert value['provenance']['location_rules'] == 'lanes-location-repair-v40+v44' and value['provenance']['location_method'] == 'combined'
        assert count == {'reads': 1, 'workers': 1}
        assert all(sha(ROOT/n) == digest for n, digest in code.items())
        summary = {'status': 'passed', 'api_responses': 1, 'real_worker_requests': 1, 'neural_mentions_preserved': 53,
                   'cached_combined_graph_matched': True, 'article_corrected_occurrences': 8, 'article_restored_facts': 40,
                   'article_unresolved_rows': 11, 'default_flag_restored': not endpoint.settings.NEWS_NER_PREVIEW_ENABLED,
                   'live_container_isolation_verified': True, 'worker_completed_and_removed': True,
                   'database_access': False, 'database_writes': False, 'source_fetch': False, 'automatic_retry': False,
                   'preservation': preservation()}
        assert summary['default_flag_restored']; write(destination/'summary.json', summary); return summary
    except BaseException as exc:
        write(destination/'failure.json', {'error_type': type(exc).__name__, 'inference_retry_allowed': False}); raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('action', choices=('cached', 'live', 'preserve'))
    parser.add_argument('--output', type=Path); parser.add_argument('--cached-package', type=Path); a = parser.parse_args()
    if a.action == 'cached': result = cached(a.output.resolve())
    elif a.action == 'live': result = live(a.cached_package.resolve(), a.output.resolve())
    else: result = preservation()
    print(json.dumps(result))
