"""Preview contract, frozen-copy parity and isolated API/lifecycle checks."""
import asyncio
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.news_ner import context_association_v41 as runtime
from app.services.news_ner import location_repair_v40 as proposals
from app.services.news_ner.contract import IMAGE, object_sha
from app.services.news_ner.projection import project
from app.services.news_ner.runtime import PreviewError, container_args, lease
from app.services.news_ner_preview_service import preview_article
from app.services.news_ner.worker import context_from_effective_mentions
from app.services.news_ner.location_pipeline import compose, LOCATION_RULES, LOCATION_METHOD
from training.flood_ner import context_association_v41 as frozen
from training.flood_ner.context_cases_v41 import core_cases
from training.flood_ner.location_repair_cases_v40 import temporal_cases, location_cases
from training.flood_ner.context_acceptance_cases import core_cases as original
from training.flood_ner.context_association_cases_v35 import core_cases as v35
from training.flood_ner.context_cases_v36 import core_cases as v36
from training.flood_ner.context_cases_v37 import core_cases as v37
from training.flood_ner.context_cases_v38 import core_cases as v38
from training.flood_ner import location_repair_v40 as frozen_proposals
from test_flood_ner_context_association_v37 import raw_case


@pytest.mark.parametrize('raw', [c['raw'] for c in core_cases() + temporal_cases()] +
    [raw_case(c) for c in original() + v35() + v36() + v37() + v38()])
def test_context_promotion_matches_frozen(raw):
    saved = deepcopy(raw)
    output = runtime.extract(raw)
    assert output == frozen.extract(raw)
    assert raw == saved
    groups = project(raw, output)
    assert sorted(r for g in groups for r in g['relation_ids']) == sorted(r['id'] for r in output['relations'])
    assigned = {f['id'] for g in groups for kind in ('depth', 'time', 'status', 'access') for f in g[kind]}
    assert assigned | {x['fact_id'] for x in output['unassigned']} == {f['id'] for f in output['facts']}


@pytest.mark.parametrize('case', location_cases())
def test_proposal_promotion_matches_frozen(case):
    for method in frozen_proposals.METHODS:
        assert proposals.propose(case['raw'], method) == frozen_proposals.propose(case['raw'], method)


def article(text='At 6 PM, Daan Piña had knee-deep flooding.', published=None):
    return SimpleNamespace(id=7, canonical_url='https://example.invalid/fictional', publisher_source_id='fictional',
        article_text=text, article_error=None, published_at=published)


def config(**changes):
    return SimpleNamespace(ENVIRONMENT='test', NEWS_NER_PREVIEW_ENABLED=True,
        NEWS_NER_PREVIEW_BUNDLE='unused', NEWS_NER_PREVIEW_BUNDLE_SHA256='a'*64,
        NEWS_NER_PREVIEW_DOCKER='docker', **changes)


async def fake_runner(raw, *_args):
    text = raw['text']
    name = 'Daan Piña'
    start = text.index(name)
    mention = {'id': 'n0', 'start': start, 'end': start+len(name), 'text': name, 'label': 'ROAD', 'provenance_sha256': 'b'*64}
    proposal = compose({'record_id': raw['record_id'], 'text': text, 'mentions': [mention]})
    return {'proposal': proposal, 'graph': context_from_effective_mentions({**raw, 'mentions': proposal['effective_mentions']}),
        'measurements': {'cold_seconds': 1.0, 'extraction_seconds': 0.1, 'peak_worker_rss_bytes': 1000000},
        'provenance': {'bundle_sha256': 'a'*64, 'image': IMAGE, 'model': 'v19-control-seed-0',
            'location_rules': LOCATION_RULES, 'location_method': LOCATION_METHOD, 'context_rules': 'lanes-context-association-v42'}}


def test_grouped_response_and_unknown_publication_timezone():
    source = article(published=datetime(2026, 10, 19, 20))
    result = asyncio.run(preview_article(source, config(), fake_runner))
    assert result.source.canonical_url == source.canonical_url
    assert result.source.text_sha256 == hashlib.sha256(source.article_text.encode()).hexdigest()
    assert not result.source.publication_timezone_known
    assert 'publication_timezone_unknown' in result.limitations
    assert any(f.temporal_role == 'observation' for g in result.groups for f in g.time)
    assert not result.graph.absolute_instants
    assert result.source.input_sha256 != result.source.text_sha256


@pytest.mark.parametrize('text,role', [
    ('At 6 PM, flooding started on Daan Piña.', 'onset'),
    ('The flood on Daan Piña subsided at 6 PM.', 'recession'),
    ('Daan Piña was dry at 6 PM.', 'clearance'),
])
def test_semantic_roles_survive_projection(text, role):
    result = asyncio.run(preview_article(article(text), config(), fake_runner))
    assert any(f.temporal_role == role for f in result.graph.facts if f.kind == 'time')
    assert result.graph.facts  # Subsided/cleared evidence is retained.


@pytest.mark.parametrize('mutation,status,code', [
    ({'article_text': None}, 409, 'article_body_unavailable'),
    ({'article_text': ' '}, 409, 'article_body_unavailable'),
    ({'article_error': 'failed'}, 409, 'article_body_unavailable'),
    ({'article_text': 'x'*100001}, 413, 'article_too_large'),
])
def test_body_failures_do_not_invoke_inference(mutation, status, code):
    saved = article()
    for k,v in mutation.items(): setattr(saved,k,v)
    async def forbidden(*args): raise AssertionError('inference forbidden')
    with pytest.raises(PreviewError) as error:
        asyncio.run(preview_article(saved, config(), forbidden))
    assert (error.value.status, error.value.code) == (status, code)


def test_disabled_and_production_fail_closed():
    cfg=config()
    for attr,value,code in [('NEWS_NER_PREVIEW_ENABLED', False, 'preview_disabled'), ('ENVIRONMENT', 'production', 'preview_environment_unavailable')]:
        setattr(cfg, attr, value)
        with pytest.raises(PreviewError) as error:
            asyncio.run(preview_article(article(), cfg, fake_runner))
        assert error.value.code == code
        cfg=config()


def test_stale_source_and_proposal_output_are_rejected():
    async def stale(raw,*args):
        result=await fake_runner(raw,*args)
        result['graph']['text_sha256']='0'*64
        return result
    with pytest.raises(PreviewError,match='preview_worker_failed'):
        asyncio.run(preview_article(article(),config(),stale))


def test_container_controls_have_no_broad_mounts():
    args=container_args('docker','lanes-ner-preview-fixed',Path('/private/bundle'),Path('/private/code'))
    assert args.count('--mount')==2
    assert '--network' in args and args[args.index('--network')+1]=='none'
    for value in ('--read-only','--cap-drop=ALL','--pull=never','4g','128','--security-opt=no-new-privileges'):
        assert value in args
    assert not any('docker.sock' in s or '.env' in s for s in args)
    assert IMAGE in args


def test_lease_contention_and_poisoned_owner(tmp_path):
    path=tmp_path/'lease'
    with lease(path,'owner') as stream:
        with pytest.raises(PreviewError) as error:
            with lease(path,'other'): pass
        assert error.value.code=='preview_busy'
        stream.seek(0);stream.truncate();stream.write(b'\0');stream.flush()
    with lease(path,'next'): pass
    with pytest.raises(PreviewError,match='preview_cleanup_unavailable'):
        with lease(path,'again'): pass


def test_promotion_manifest_only_changes_validator_import():
    root=Path(__file__).resolve().parents[2]
    package=root/'backend/app/services/news_ner'
    for name,binding in json.loads((package/'promotion.json').read_text()).items():
        source=(root/binding['source']).read_bytes()
        assert hashlib.sha256(source).hexdigest()==binding['source_sha256']
        assert hashlib.sha256((package/name).read_bytes()).hexdigest()==binding['runtime_sha256']
        assert (package/name).read_bytes().decode('utf-8')==source.decode('utf-8').replace('from .context_acceptance import validate_raw_input','from .contract import validate_raw_input')
