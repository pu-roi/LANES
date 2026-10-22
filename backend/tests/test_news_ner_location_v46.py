"""Fictional adapter checks; no model, database or live source."""
from copy import deepcopy
import pytest

from app.services.news_ner.location_pipeline import compose, from_neural_mentions
from app.services.news_ner import location_repair_v44 as promoted
from training.flood_ner.location_repair_cases_v44 import location_cases
from training.flood_ner.location_repair_v44 import propose as frozen
from training.flood_ner.location_scoring_v45 import location_result, author_repaired_expectations, repaired_result
from training.flood_ner.context_cases_v42 import core_cases
from app.services.news_ner.context_association_v42 import extract
from app.services.news_ner.contract import object_sha


@pytest.mark.parametrize('case', location_cases(), ids=lambda c: c['case_id'])
def test_promoted_copy_and_pipeline_preserve_fictional_expectations(case):
    raw = case['raw']; before = deepcopy(raw)
    value = {k: raw[k] for k in ('record_id', 'text', 'mentions')}
    assert promoted.propose(value) == frozen(value)
    result = from_neural_mentions(raw)
    repair = result['proposal']
    row = {'record_id': raw['record_id'], 'raw': raw, 'control_mentions': repair['control_mentions']}
    assert location_result(case, row, repair, conditional=True)['passed']
    assert raw == before and result['graph']['mentions'] == repair['effective_mentions']
    for p in repair['proposals']:
        assert p['provenance_sha256'] == object_sha({k: v for k, v in p.items() if k != 'provenance_sha256'})
    assert all(a['implementation'] in repair['stage_order'] for a in repair['abstentions'])


@pytest.mark.parametrize('oracle', author_repaired_expectations(core_cases()), ids=lambda o: o['case_id'])
def test_source_authored_original_and_repaired_views_remain_separate(oracle):
    raw = next(c['raw'] for c in core_cases() if c['case_id'] == oracle['case_id'])
    value = from_neural_mentions(raw); repair = value['proposal']
    row = {'record_id': raw['record_id'], 'raw': raw, 'control_mentions': repair['control_mentions']}
    assert repaired_result(oracle, row, repair, extract(raw), value['graph'])['passed']
    assert repair['neural_mentions'] == raw['mentions']


def test_both_stages_keep_order_and_original_hashes():
    text = 'At Piña tunnel: knee-deep flooding.\nÁster cor Luntian - 8 inches, gutter deep'
    import hashlib
    raw = {'record_id': 'fictional-chain', 'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'publication': None, 'mentions': []}
    repair = compose(raw)
    implementations = [p['implementation'] for p in repair['proposals']]
    assert implementations[0] == 'lanes-location-repair-v40'
    assert implementations[1:] == ['lanes-location-repair-v44']*2
    assert all(p['origin'] == 'rule_proposal_not_neural' for p in repair['proposals'])
    assert repair['neural_mentions'] == [] and len(repair['control_mentions']) == 1


@pytest.mark.parametrize('case', location_cases(), ids=lambda c: c['case_id'])
def test_worker_and_host_use_the_same_pipeline(case):
    from app.services.news_ner.worker import extraction_from_neural_mentions
    assert extraction_from_neural_mentions(case['raw']) == from_neural_mentions(case['raw'])


@pytest.mark.parametrize('mutation', ('proposal_action', 'proposal_hash', 'proposal_origin', 'abstention_stage',
    'effective_label', 'old_location_rules', 'wrong_method', 'graph_measurement', 'graph_targets', 'graph_onset'))
def test_host_rejects_tampered_chain_and_valid_but_mismatched_graph(mutation):
    import asyncio
    from app.services.news_ner_preview_service import preview_article
    from app.services.news_ner.runtime import PreviewError
    from test_news_ner_preview import article, config, fake_runner
    text = 'Daan Piña cor Áster Road - 8 inches, gutter deep at 6 PM'
    async def altered(raw, *args):
        value = await fake_runner(raw, *args)
        if mutation == 'proposal_action': value['proposal']['proposals'][-1]['action'] = 'replace'
        elif mutation == 'proposal_hash': value['proposal']['proposals'][-1]['provenance_sha256'] = '0'*64
        elif mutation == 'proposal_origin': value['proposal']['proposals'][-1]['origin'] = 'neural'
        elif mutation == 'abstention_stage': value['proposal']['abstentions'].append({'implementation': 'unknown', 'reason': 'fake'})
        elif mutation == 'effective_label': value['proposal']['effective_mentions'][-1]['label'] = 'CITY'
        elif mutation == 'old_location_rules': value['provenance']['location_rules'] = 'lanes-location-repair-v40'
        elif mutation == 'wrong_method': value['provenance']['location_method'] = 'missing_junction'
        elif mutation == 'graph_measurement': value['graph']['facts'][0]['value'] = '9 inches'
        elif mutation == 'graph_targets': value['graph']['relations'][0]['target_entity_ids'] = ['n0']
        else:
            next(f for f in value['graph']['facts'] if f['kind'] == 'time')['temporal_role'] = 'onset'
        return value
    with pytest.raises(PreviewError, match='preview_worker_failed'):
        asyncio.run(preview_article(article(text), config(), altered))
