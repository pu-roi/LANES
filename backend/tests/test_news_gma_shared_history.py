"""Shared source severity never becomes an individual measurement or live zone."""
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import re

import httpx
import pytest

from app.crud.news_publication import NewsPublicationError
from app.services.news_gma_shared_history import (GROUPS, SESSION, VERSION, SharedHistoryAuthority,
    depth_policy, shared_depth_attributes, evaluation_identity)
from app.services.news_ner_durable.contracts import sha
from app.services.news_ner_durable.scoped_resolution import source_layout, CONTRACT
from app.services.news_ner_durable.resolution import quote_options, ResolutionError


@pytest.fixture(autouse=True)
def no_provider(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail('Historical-only checks attempted an external request')
    monkeypatch.setattr(httpx.Client, 'send', forbidden)
    monkeypatch.setattr(httpx.AsyncClient, 'send', forbidden)


def fixture(heading='Waist-deep (37 inches)'):
    text = ('Flooded roads on September 9, 2026\nThe following roads were flooded.\n'
        'Quezon City (as of 8:55 AM)\n' + heading + '\n- Don Jose Street\n- Palali Street\n'
        'Tire-deep (26 inches)\n- Banawe Street\n- Tabayoc Street\n- Ubay Street')
    mentions = []
    for name, target, label in [('Quezon City', 'n0', 'CITY'), ('Don Jose Street', 'n13', 'ROAD'),
            ('Palali Street', 'n14', 'ROAD'), ('Banawe Street', 'n16', 'ROAD'),
            ('Tabayoc Street', 'n17', 'ROAD'), ('Ubay Street', 'n18', 'ROAD')]:
        match = re.search(name, text)
        value = {'id': target, 'label': label, 'text': name, 'start': match.start(), 'end': match.end()}
        mentions.append(SimpleNamespace(label=label, model_dump=lambda mode, v=value: deepcopy(v)))
    candidates = [m.model_dump(mode='json') for m in mentions]
    layout = source_layout(text, candidates); rows = []; claims = []; groups = []
    for index, group_id in enumerate(GROUPS):
        target = group_id.removeprefix('resolved-')
        nav = next(n for n in layout['targets'] if n['target_id'] == target)
        raw = 'Waist-deep (37 inches)' if index < 2 else '26 inches'
        rows.append({'target_id': target, 'verdict': 'observed', 'city': 'Quezon City', 'barangay': None,
            'place_evidence': [], 'status': 'active', 'historical': False, 'contradictory': False,
            'status_evidence': [], 'time_role': 'observation', 'date_text': 'September 9, 2026',
            'clock_text': '8:55 AM', 'contemporaneous': True, 'time_evidence': [], 'depth_text': raw,
            'depth_scope': 'shared', 'depth_evidence': [nav['list_context']['depth_heading'], *nav['target_passages']],
            'access': 'unknown', 'access_evidence': [], 'road_section': None, 'section_evidence': []})
        claims.append(SimpleNamespace(depth_raw=raw, depth_canonical=None, road_passability='unknown'))
        groups.append({'group_id': group_id, 'target_entity_ids': [target], 'claim_index': index,
            'disposition': 'historical_archive', 'source_check': {'evidence': {'depth': {'raw': raw, 'canonical': None}}}})
    payload = {'results': rows, 'row_outcomes': [{'target_id': r['target_id'], 'outcome': 'accepted', 'issues': []} for r in rows],
        'identity': {'evidence_contract': CONTRACT}, 'source_layout_sha256': sha(layout)}
    result = SimpleNamespace(native=SimpleNamespace(graph=SimpleNamespace(mentions=mentions)),
        provenance={'llm_resolution': payload}, claims=claims)
    context = SimpleNamespace(source=lambda: SimpleNamespace(article_text=text), input_fingerprint=sha(text))
    return result, groups, context


@pytest.mark.parametrize('index', range(5))
def test_shared_heading_supplies_only_high_category(index):
    result, groups, context = fixture()
    attributes, proof = shared_depth_attributes(result, groups[index], context=context)
    assert attributes == {'severity_override': 'high', 'depth_override': None, 'passable_vehicles_override': None}
    assert proof['scope'] == 'shared' and proof['individual_depth'] is None
    assert not proof['passability_inferred']
    assert proof['selected_member_target_ids'] == (['n13', 'n14'] if index < 2 else ['n16', 'n17', 'n18'])
    assert all(e['quote'] == context.source().article_text[e['start']:e['end']] for e in proof['evidence'])
    assert all(c.depth_canonical is None for c in result.claims)


@pytest.mark.parametrize('case', ['active', 'unknown_group', 'wrong_target', 'unsupported', 'conflict',
    'missing_heading', 'wrong_heading', 'missing_road', 'duplicate', 'negative', 'out_of_range',
    'scalar', 'access', 'audit', 'layout', 'individual_scope', 'wrong_measurement'])
def test_ineligible_or_tampered_evidence_is_rejected(case):
    result, groups, context = fixture(); group = groups[0]; row = result.provenance['llm_resolution']['results'][0]
    if case == 'active': group['disposition'] = 'active_demo'
    if case == 'unknown_group': group['group_id'] = 'resolved-n99'
    if case == 'wrong_target': group['target_entity_ids'] = ['n14']
    if case == 'unsupported': result.provenance['llm_resolution']['row_outcomes'][0]['outcome'] = 'unresolved'
    if case == 'conflict': row['contradictory'] = True
    if case == 'missing_heading': row['depth_evidence'] = row['depth_evidence'][1:]
    if case == 'wrong_heading': row['depth_evidence'][0] = result.provenance['llm_resolution']['results'][2]['depth_evidence'][0]
    if case == 'missing_road': row['depth_evidence'] = row['depth_evidence'][:1]
    if case == 'duplicate': row['depth_evidence'].append(row['depth_evidence'][0])
    if case == 'negative': row['depth_evidence'][0] = -1
    if case == 'out_of_range': row['depth_evidence'][0] = len(quote_options(context.source().article_text))
    if case == 'scalar': result.claims[0].depth_canonical = 'waist'
    if case == 'access': row['access'] = 'impassable_all'
    if case == 'audit': group['source_check']['evidence']['depth']['canonical'] = 'waist'
    if case == 'layout': result.provenance['llm_resolution']['source_layout_sha256'] = '0' * 64
    if case == 'individual_scope': row['depth_scope'] = 'individual'
    if case == 'wrong_measurement': row['depth_text'] = '26 inches'
    with pytest.raises(NewsPublicationError): shared_depth_attributes(result, group, context=context)


@pytest.mark.parametrize('heading', ['Waist-deep (about 37 inches)', 'Waist-deep (up to 37 inches)',
    'Waist-deep (37 to 45 inches)', 'Waist-deep (38 inches)', 'Waist-deep (37 inches or 26 inches)'])
def test_approximate_ranged_conflicting_or_unmapped_heading_stays_unresolved(heading):
    result, groups, context = fixture(heading)
    row = result.provenance['llm_resolution']['results'][0]
    row['depth_text'] = heading
    result.claims[0].depth_raw = heading; groups[0]['source_check']['evidence']['depth']['raw'] = heading
    with pytest.raises(NewsPublicationError): shared_depth_attributes(result, groups[0], context=context)


@pytest.mark.parametrize('operation', ['ner', 'resolve', 'count', 'archive', 'outputs', 'activate'])
def test_new_authority_cannot_enable_other_operations(operation):
    p = {'schema_version': VERSION, 'session_id': SESSION, 'historical_depth_policy': depth_policy(),
        'allowed_operations': [operation]}
    with pytest.raises(ResolutionError, match='authority_invalid'):
        SharedHistoryAuthority(p, sha(p), None).validate(None)


def test_new_evaluation_identity_preserves_original_unresolved_policy():
    authority = SharedHistoryAuthority({'saved_result_sha256': '1'*64}, '', None)
    new = evaluation_identity(authority, GROUPS[0])
    old = sha({'schema': 'gma-review-archive-v1', 'session': SESSION, 'run_id': 380,
        'group_id': GROUPS[0], 'result': '1'*64})
    assert new != old and new == evaluation_identity(authority, GROUPS[0])


def test_operational_gate_still_rejects_shared_depth():
    from app.services.news_publication_service import _operational_zone_attributes
    claim = SimpleNamespace(depth_canonical=None)
    audit = SimpleNamespace(evidence=SimpleNamespace(depth=SimpleNamespace(confirmed=True)))
    with pytest.raises(NewsPublicationError, match='operational_depth_not_verified'):
        _operational_zone_attributes(claim, audit)


def test_intent_storage_failure_prevents_database_connection():
    from scripts import run_news_gma_shared_history as worker
    release = {'resolver': {}, 'shared_history_policy': depth_policy()}
    ledger = {'status': 'stopped', 'attempts': [{'status': 'completed'} for _ in range(36)]}
    authority = {'schema_version': VERSION, 'release_sha256': sha(release), 'resolver': {},
        'receipts_prefix': 'private-prefix', 'historical_depth_policy': depth_policy(),
        'budget_object': 'budget', 'ledger_baseline_sha256': sha(ledger)}
    args = SimpleNamespace(mode='gma-shared-archive', run_id=[380], authority_object='authority', authority_sha256=sha(authority))
    class Store:
        def __init__(self, _bucket, key): self.key = key
        def read(self): return (authority if self.key == 'authority' else ledger), 'generation'
    with patch.object(worker, 'GCSLedgerStore', Store), patch.object(worker, 'GCSReceiptStore') as journal, \
            patch.object(worker, 'create_engine') as connection, \
            patch('app.services.news_gma_scoped_budget.effective_commitment', return_value=731_469_600), \
            patch.dict('os.environ', {'LANES_NEWS_RECEIPTS_PREFIX': 'private-prefix'}):
        journal.return_value.put.side_effect = ResolutionError('private_storage_unavailable')
        with pytest.raises(ResolutionError, match='private_storage_unavailable'): worker.run_shared_history(args, release)
        connection.assert_not_called()


@pytest.mark.parametrize('run_ids,mode', [([375], 'gma-shared-archive'), ([380, 375], 'gma-shared-preview'),
    ([380], 'gma-scoped-resolve'), ([380], 'pilot-apply')])
def test_archive_command_rejects_other_runs_and_dispatch_modes(run_ids, mode):
    from scripts.run_news_gma_shared_history import run_shared_history
    with pytest.raises(ResolutionError, match='command_invalid'):
        run_shared_history(SimpleNamespace(mode=mode, run_id=run_ids), {})


@pytest.mark.asyncio
async def test_restore_endpoint_rejects_ended_history_before_writing():
    from fastapi import HTTPException
    from unittest.mock import MagicMock
    from app.api.v1.endpoints.admin import restore_zone
    from app.models.report import FloodEventStatus
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(
        flood_event=SimpleNamespace(status=FloodEventStatus.ENDED))
    with pytest.raises(HTTPException) as failure:
        await restore_zone(123, SimpleNamespace(), db, SimpleNamespace())
    assert failure.value.status_code == 409
    db.commit.assert_not_called()


def test_zone_editor_cannot_reopen_ended_history():
    from unittest.mock import MagicMock
    from app.models.report import FloodEventStatus
    from app.schemas.report import FloodAvoidanceZoneUpdate
    from app.services import zone_editor_service as editor
    from app.services.flood_followup_service import FollowupError
    db = MagicMock()
    zone = SimpleNamespace(flood_event=SimpleNamespace(status=FloodEventStatus.ENDED))
    with patch.object(editor, 'require_staff_permission'), patch.object(editor.store, 'zone', return_value=zone):
        with pytest.raises(FollowupError) as failure:
            editor.save_zone(db, 123, SimpleNamespace(), FloodAvoidanceZoneUpdate(is_active=True))
    assert failure.value.status_code == 409
    db.flush.assert_not_called()
    db.commit.assert_not_called()
