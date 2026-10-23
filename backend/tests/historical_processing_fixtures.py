"""Fictional E0 packages for command tests, with no model/publisher access."""
from copy import deepcopy

from app.services.news_historical_preparation import SourceSpec, build_preparation, text_sha
from app.services.news_ner_durable.contracts import sha
from test_news_ner_durable import BODY, NOW


def fictional_documents(trusted, text=BODY):
    snapshots, specs, history, candidates = [], [], [], []
    for index in range(2):
        article_id, version_id, zone_id = 101 + index, 201 + index, 301 + index
        snapshot = {'canonical_url': f'https://example.org/historical-{index}', 'publisher': 'fictional',
            'title': 'Fictional historical source', 'excerpt': '', 'published_at': NOW.isoformat(),
            'article_text': text}
        specs.append(SourceSpec(article_id, version_id, sha(snapshot), text_sha(text), snapshot['canonical_url'],
            snapshot['publisher'], snapshot['published_at']))
        snapshots.append({'article_id': article_id, 'version_id': version_id,
            'input_fingerprint': sha(snapshot), 'input_snapshot': snapshot})
        claim = {'canonical_road': 'Fictional Crescent', 'canonical_city': 'City of Pasig',
            'evidence_sentence': text, 'condition': 'active', 'depth_raw': 'knee-deep'}
        history.append({'article_id': article_id, 'run_id': 401+index, 'claim_ordinal': 0,
            'zone_id': zone_id, 'event_id': 501+index, 'mode': 'rules_only', 'is_active': False,
            'event_status': 'ended', 'geometry_valid': True, 'geometry_srid': 4326,
            'geometry_sha256': '5'*64, 'claim': claim})
        candidates.append((article_id, 401+index, 0, zone_id, 'primary' if index == 0 else 'historical',
            'active_demo' if index == 0 else 'historical_archive', 'Fictional Crescent', 'City of Pasig'))
    # Model/reference identities stay fixed. Parent projection digests are
    # explicitly fictional predecessors, exercising the E1.1/E1.2 identity delta.
    original = deepcopy(trusted.manifest)
    original['projection']['code_sha256'] = 'a'*64
    original['source_check']['code_sha256'] = 'a'*64
    assets = {'manifest': original, 'manifest_sha256': sha(original),
        'pipeline_version': 'ner-v1:'+sha(original), 'preparation_code_sha256': '6'*64}
    return build_preparation({'read_only': True, 'database_identity_sha256': '3'*64,
        'sources': snapshots, 'feeds': [], 'history': history}, assets, specs=tuple(specs), candidates=tuple(candidates))
