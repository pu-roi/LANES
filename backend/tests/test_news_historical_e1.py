"""Remaining E1 policy/date/placement checks; fictional sources, no inference."""
from copy import deepcopy
from datetime import timedelta
import json
from types import SimpleNamespace

import pytest
from sqlalchemy.engine import URL

from app.services import news_historical_processing as service
from app.services.news_historical_policy import expected_target_policy, load_target_policy
from app.services.news_historical_interpretation import historical_time, interpret_historical
from app.services.news_historical_preparation import PreparationError, save_private_package
from app.services.news_ner_durable.contracts import NativeInput, RunEvidence, sha
from historical_processing_fixtures import fictional_documents
from test_news_ner_durable import trusted, NOW, BODY, make_case


def origin_package(trusted, tmp_path, engine, text=BODY):
    docs = fictional_documents(trusted, text)
    identity = service.database_identity(engine)
    docs['inventory.json']['database_identity_sha256'] = identity
    docs['manifest.json']['database_identity_sha256'] = identity
    docs['receipt.json']['manifest_sha256'] = sha(docs['manifest.json'])
    docs['receipt.json']['document_sha256'] = {name: sha(value) for name, value in docs.items() if name != 'receipt.json'}
    path = tmp_path/'origin'
    save_private_package(path, docs)
    return service.load_historical_package(path/'manifest.json', sha(docs['manifest.json']))


def target():
    return SimpleNamespace(url=URL.create('postgresql+psycopg', host='cloud.invalid', database='lanes'))


def authorization(package, trusted, engine, tmp_path, changed=None, expected=None):
    value = expected_target_policy(package, trusted, engine)
    if changed:
        changed(value)
    path = tmp_path/'policy.json'
    path.write_text(json.dumps(value), encoding='utf-8')
    return load_target_policy(path, expected or sha(value), package, trusted, engine)


def test_policy_authenticates_origin_workload_assets_and_current_code(trusted, tmp_path):
    engine = target(); package = origin_package(trusted, tmp_path, engine)
    auth = authorization(package, trusted, engine, tmp_path)
    execution, blockers = service.execution_manifest(package, trusted, sha(trusted.manifest), engine, 'production', auth)
    assert not blockers and execution['target_policy_sha256'] == auth.policy_sha256
    assert execution['processing_policy'] == 'pinned_origin_processing_only_no_publication'
    assert auth.policy['publication_allowed'] is False
    assert 'cloud.invalid' not in json.dumps(execution) and 'cloud.invalid' not in json.dumps(auth.policy)
    assert 'historical_cloud_processing_not_qualified' in service.execution_manifest(
        package, trusted, sha(trusted.manifest), engine, 'production')[1]


@pytest.mark.parametrize('field', ['parent_manifest_sha256', 'dataset_id', 'demonstration_session_id',
    'confirmed_database', 'target_database_identity_sha256', 'inputs', 'assets_sha256',
    'pipeline_version', 'application_sha256', 'operations', 'publication_allowed'])
def test_rehashed_policy_with_changed_binding_is_rejected(trusted, tmp_path, field):
    engine = target(); package = origin_package(trusted, tmp_path, engine)
    with pytest.raises(PreparationError, match='historical_target_policy_binding_mismatch'):
        authorization(package, trusted, engine, tmp_path, lambda p: p.update({field: 'tampered'}))


def test_wrong_policy_hash_and_loaded_mutation_and_connection_override_rejected(trusted, tmp_path):
    engine = target(); package = origin_package(trusted, tmp_path, engine)
    with pytest.raises(PreparationError, match='historical_target_policy_hash_mismatch'):
        authorization(package, trusted, engine, tmp_path, expected='0'*64)
    auth = authorization(package, trusted, engine, tmp_path)
    auth.policy['operations'].append('publish')
    with pytest.raises(PreparationError, match='historical_target_policy_changed'):
        auth.validate(engine)
    auth = authorization(package, trusted, engine, tmp_path)
    with pytest.raises(PreparationError, match='historical_target_connection_invalid'):
        auth.validate(SimpleNamespace(url=engine.url.update_query_dict({'host': 'other'})))
    with pytest.raises(PreparationError, match='historical_target_origin_required'):
        auth.validate(SimpleNamespace(url=engine.url.set(database='other')))


@pytest.mark.parametrize('change', [lambda p: p.update(publication_allowed=0),
    lambda p: p['inputs'][0].update(article_id=101.0)])
def test_policy_binding_uses_canonical_types_not_python_numeric_equality(trusted, tmp_path, change):
    engine = target(); package = origin_package(trusted, tmp_path, engine)
    with pytest.raises(PreparationError, match='historical_target_policy_binding_mismatch'):
        authorization(package, trusted, engine, tmp_path, change)


def clock_case(text, publication=None, uncertainty=False):
    source = NativeInput(canonical_url='https://example.org/fictional', publisher='fictional', title='Fictional',
        article_text=text, published_at=NOW, publication_evidence=publication or {'basis': 'legacy_unknown'})
    evidence = {'start': 0, 'end': len(text), 'text': text}
    fact = {'id': 'f1', 'kind': 'time', 'temporal_role': 'observation', 'evidence': [evidence],
        'uncertainty': ['ambiguous'] if uncertainty else [], 'value': text, 'entity_ids': ['t1']}
    graph = {'expressions': [{'id': 't1', **evidence}]}
    return source, graph, [fact]


@pytest.mark.parametrize('text,precision,date', [
    ('On September 24, 2026 at 10 AM PHT, flooding was observed.', 'instant', '2026-09-24'),
    ('On September 24, 2026 flooding was observed.', 'date', '2026-09-24'),
    ('On September 24, 2026 at 10 AM flooding was observed.', 'date', '2026-09-24'),
    ('Today at 10 AM PHT flooding was observed.', 'unknown', None),
    ('At 10 AM PHT flooding was observed.', 'unknown', None),
    ('On September 9, 2026 and September 24, 2026 flooding was observed.', 'unknown', None),
    ('On September 31, 2026 flooding was observed.', 'unknown', None),
])
def test_historical_time_precision_and_no_invented_dates(text, precision, date):
    result = historical_time(*clock_case(text))
    assert result['precision'] == precision and result['occurrence_date'] == date
    assert bool(result['observed_at']) == (precision == 'instant')


def test_relative_date_requires_authenticated_publication_and_report_role_is_not_observation():
    publication = {'raw': NOW.isoformat(), 'basis': 'publisher_feed', 'timezone_known': True}
    source, graph, facts = clock_case('Yesterday at 10 AM PHT flooding was observed.', publication)
    assert historical_time(source, graph, facts)['occurrence_date'] == '2026-10-19'
    facts[0]['temporal_role'] = 'report'
    assert historical_time(source, graph, facts)['precision'] == 'unknown'


def test_bad_offset_uncertainty_and_conflicting_clocks_are_not_exact():
    source, graph, facts = clock_case('On September 24, 2026 at 10 AM PHT and 11 AM PHT flooding occurred.')
    assert historical_time(source, graph, facts)['precision'] == 'date'
    facts[0]['uncertainty'] = ['ambiguous']
    assert historical_time(source, graph, facts)['precision'] == 'unknown'
    facts[0]['evidence'][0]['start'] = 1
    with pytest.raises(PreparationError, match='historical_time_evidence_invalid'):
        historical_time(source, graph, facts)


def prepared_case(trusted, tmp_path, text=BODY, labels=None):
    engine = target(); package = origin_package(trusted, tmp_path, engine, text)
    capture = package.captures[0]
    run, version, _, inference, _ = make_case(trusted, text, labels=labels)
    version.article_id = capture['article_id']; version.input_snapshot = capture['input_snapshot']
    version.input_fingerprint = capture['native_input_fingerprint']
    from app.services.news_ner_durable.adapter import build_native_result
    from app.services.news_ner.location_pipeline import from_neural_mentions
    context = RunEvidence.from_records(run, version)
    inference = {**inference, **from_neural_mentions({**context.source().runtime_request(context.input_fingerprint),
        'mentions': inference['proposal']['neural_mentions']})}
    run.result = build_native_result(context, inference, trusted, extracted_at=NOW).model_dump(mode='json', by_alias=True)
    execution, _ = service.execution_manifest(package, trusted, sha(trusted.manifest), engine, 'production')
    return run, version, package, execution


def test_interpretation_reuses_verified_source_and_preview_without_mutating_result(trusted, tmp_path):
    run, version, package, execution = prepared_case(trusted, tmp_path)
    before = deepcopy(run.result)
    calls = []
    preview = SimpleNamespace(preview=lambda claim: calls.append(claim) or SimpleNamespace(
        model_dump=lambda **_: {'status': 'unresolved', 'reason': 'fictional_geometry_not_qualified'}))
    receipt = interpret_historical(run, version, trusted, package, execution, now=NOW+timedelta(days=3), placement_service=preview)
    assert receipt['status'] == 'qualified' and len(calls) == 1
    assert receipt['groups'][0]['disposition'] == 'active_demo'
    assert receipt['groups'][0]['placement']['status'] == 'unresolved'
    assert receipt['groups'][0]['geometry_acceptance'] == 'pending_e2'
    assert run.result == before and receipt['result_sha256'] == sha(before)
    assert receipt['publication_evidence']['basis'] == 'legacy_unknown'
    # Real-time admission remains a review; historical interpretation is separate.
    assert receipt['groups'][0]['source_check']['outcome'] == 'review'
    output = tmp_path/'receipts'
    service.save_attempt(output, {'historical_interpretations': [receipt]}, 'first')
    service.save_attempt(output, {'historical_interpretations': [receipt]}, 'second')
    assert len(list(output.glob('interpretation-*.json'))) == 1
    # Future evidence must not be admitted by the historical-age exception.
    future = interpret_historical(run, version, trusted, package, execution, now=NOW-timedelta(days=3), placement_service=preview)
    assert future['status'] == 'unresolved' and len(calls) == 1


@pytest.mark.parametrize('text', [
    'Fictional Crescent in Pasig City was flooded knee-deep.',
    'Tomorrow Fictional Crescent in Pasig City may be flooded knee-deep.',
    'On October 20, 2026 at 10 AM PHT, Fictional Crescent in Pasig City was not flooded.',
    'On October 20, 2026 at 10 AM PHT, flooding on Fictional Crescent in Pasig City has subsided.',
    'Photo: On October 20, 2026 at 10 AM PHT, Fictional Crescent in Pasig City was flooded knee-deep.',
])
def test_unsupported_evidence_does_not_reach_placement(trusted, tmp_path, text):
    run, version, package, execution = prepared_case(trusted, tmp_path, text)
    provider = SimpleNamespace(preview=lambda _: pytest.fail('Unsupported evidence reached geometry'))
    before = deepcopy(run.result)
    receipt = interpret_historical(run, version, trusted, package, execution, now=NOW, placement_service=provider)
    assert receipt['status'] == 'unresolved' and run.result == before


def test_real_existing_placement_service_retains_unresolved_geometry(trusted, tmp_path):
    # Actual OSM resolver and NOAH preview, supplied synthetic spatial assets.
    from test_news_placement_preview import service as spatial_service
    provider = spatial_service(tmp_path, city='City of Pasig')
    run, version, package, execution = prepared_case(trusted, tmp_path)
    receipt = interpret_historical(run, version, trusted, package, execution, now=NOW,
                                   placement_service=provider)
    assert receipt['status'] == 'qualified'
    group = receipt['groups'][0]
    assert group['placement']['status'] in {'unresolved', 'ambiguous'}
    assert group['geometry_acceptance'] == 'pending_e2'


def test_collective_groups_keep_native_targets_without_individual_claims(trusted, tmp_path):
    text = 'On October 20, 2026 at 10 AM PHT, Fictional Crescent and Imaginary Avenue in Pasig City were flooded knee-deep.'
    run, version, package, execution = prepared_case(trusted, tmp_path, text,
        [('Fictional Crescent', 'ROAD'), ('Imaginary Avenue', 'ROAD'), ('Pasig City', 'CITY')])
    receipt = interpret_historical(run, version, trusted, package, execution, now=NOW,
        placement_service=SimpleNamespace(preview=lambda _: pytest.fail('Collective group split into a scalar')))
    assert receipt['status'] == 'unresolved'
    assert any(len(g['target_entity_ids']) > 1 for g in receipt['groups'])
    assert all(g['claim_index'] is None for g in receipt['groups'])


def test_date_only_and_separate_observations_remain_distinct(trusted, tmp_path):
    text = ('On October 19, 2026 Fictional Crescent in Pasig City was flooded knee-deep. '
            'On October 20, 2026 Fictional Crescent in Pasig City was flooded knee-deep.')
    run, version, package, execution = prepared_case(trusted, tmp_path, text)
    receipt = interpret_historical(run, version, trusted, package, execution, now=NOW,
        placement_service=SimpleNamespace(preview=lambda _: SimpleNamespace(model_dump=lambda **_: {'status': 'unresolved'})))
    dates = {g['time']['occurrence_date'] for g in receipt['groups']}
    assert dates == {'2026-10-19', '2026-10-20'}
    assert all(g['time']['observed_at'] is None for g in receipt['groups'])


def test_tampered_saved_result_rejected_before_historical_context(trusted, tmp_path):
    run, version, package, execution = prepared_case(trusted, tmp_path)
    run.result['claims'][0]['depth_raw'] = 'invented-depth'
    from app.services.news_ner_durable.contracts import NerEvidenceError
    with pytest.raises(NerEvidenceError, match='ner_result_contract_invalid'):
        interpret_historical(run, version, trusted, package, execution, now=NOW)
