"""Archive authority, mixed saved readers and citizen overlap regression checks."""
from copy import deepcopy
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app import models
from app.services.news_ner_durable.contracts import sha
from app.services.news_historical_preparation import PreparationError
from app.services.news_history_authority import ArchiveAuthority, expected_authority
from test_news_historical_outputs import prepared
from test_news_historical_processing_postgres import isolation, c3b_db, trusted, SOURCES, NOW


def test_authority_is_bound_to_operation_selection_target_and_code():
    from sqlalchemy.engine import URL
    target = SimpleNamespace(url=URL.create('postgresql+psycopg', host='shared.example', database='fixture'))
    policy = expected_authority(target, 'register_captures', 'a'*64)
    authority = ArchiveAuthority(policy, sha(policy))
    authority.validate(target, 'register_captures', 'a'*64)
    for operation, digest in [('save_archives', 'a'*64), ('register_captures', 'b'*64)]:
        with pytest.raises(PreparationError):
            authority.validate(target, operation, digest)
    changed = deepcopy(policy); changed['active_output_allowed'] = True
    with pytest.raises(PreparationError):
        ArchiveAuthority(changed, sha(changed)).validate(target, 'register_captures', 'a'*64)


def test_mixed_reader_preserves_legacy_and_suppresses_pending_native_fallback(prepared):
    from app.models.news import NewsArticleVersion, NewsExtractionRun
    from app.services.news_results_service import browse_news_results
    from app.services.news_native_read_context import SavedNativeReadContext
    from app.services.news_historical_processing import database_identity
    h = prepared
    # Persist the derived projection exactly as a fresh historical worker does.
    from app.services.news_ner_durable.read_projection import build_read_projection
    from app.services.news_ner_durable.adapter import verify_saved_result
    from app.services.news_ner_durable.contracts import RunEvidence
    with h.factory() as db, db.begin():
        run = db.get(NewsExtractionRun, h.ids[0]); version = db.get(NewsArticleVersion, run.article_version_id)
        result = verify_saved_result(RunEvidence.from_records(run, version), run.result, h.trusted)
        result.read_projection = build_read_projection(RunEvidence.from_records(run, version).source(), result, h.trusted.catalog)
        run.result = result.model_dump(mode='json', by_alias=True)
        second = db.get(NewsExtractionRun, h.ids[1]); second.status = 'pending'; second.result = None; second.completed_at = None
    context = SavedNativeReadContext(h.trusted.pipeline_version, database_identity(h.engine))
    args = dict(page=1, page_size=50, search='', publisher=None, condition=None, placement=None, order='extraction_newest')
    with h.factory() as db:
        page = browse_news_results(db, processing_context=context, **args)
        assert page.items and all(i.article_id != 102 for i in page.items)
        assert any(i.processing_method == 'ner_rules_v1' for i in page.items)
        assert page.total == len(page.items)


@pytest.mark.parametrize('variant', ['exact', 'active', 'date_only', 'unknown_observation', 'different_geometry'])
def test_citizen_archive_overlap_requires_exact_ended_evidence(prepared, variant):
    from geoalchemy2.shape import from_shape
    from shapely.geometry import shape
    from app.models.audit import AuditLog
    from app.services.news_history_incident_matching import citizen_archive_match
    from app.services.news_historical_outputs import qualify_outputs
    from app.services.news_historical_interpretation import historical_placement_claim
    from app.services.news_ner_durable.adapter import verify_saved_result
    from app.services.news_ner_durable.contracts import RunEvidence
    h = prepared
    with h.factory() as db, db.begin():
        output = next(o for o in qualify_outputs(db, h.package, h.trusted, h.options['policy'],
            sources=SOURCES, now=NOW, placement_service=h.options['placement_service']) if o['disposition'] == 'historical_archive')
        run = db.get(models.NewsExtractionRun, output['run_id']); version = db.get(models.NewsArticleVersion, run.article_version_id)
        result = verify_saved_result(RunEvidence.from_records(run, version), run.result, h.trusted)
        claim, _ = historical_placement_claim(result, output['group_id'])
        geometry = shape(output['geometry'])
        event = models.FloodEvent(status=models.FloodEventStatus.ACTIVE if variant == 'active' else models.FloodEventStatus.ENDED,
            verified_at=NOW, first_reported_at=NOW, ended_at=None if variant == 'active' else NOW,
            peak_severity=models.ReportSeverity.MEDIUM)
        db.add(event); db.flush()
        zone = models.FloodAvoidanceZone(event_id=event.id, is_active=variant == 'active',
            geometry=from_shape(geometry.buffer(.000001) if variant == 'different_geometry' else geometry, srid=4326))
        db.add(zone); db.flush()
        report = models.FloodReport(event_id=event.id, zone_id=zone.id, source=models.ReportSource.USER_REPORT,
            status=models.ReportStatus.APPROVED, severity=models.ReportSeverity.MEDIUM,
            raw_text='Fictional observed flood', city=claim.canonical_city,
            human_readable_location=claim.canonical_road or claim.raw_place_name)
        db.add(report); db.flush()
        observed = None if variant == 'unknown_observation' else output['interpretation']['time']['observed_at']
        db.add(AuditLog(action_type='CITIZEN_OBSERVATION', target_table='flood_reports', target_id=report.id,
            metadata_json={'observed_at': observed, 'road_validated': True})); db.flush()
        if variant == 'date_only':
            output['interpretation']['time'].update(precision='date', observed_at=None)
        before = (event.status, event.verified_at, event.ended_at, zone.is_active, report.raw_text)
        if variant == 'exact':
            match = citizen_archive_match(db, output, claim, lock=True)
            assert match[0].id == event.id and match[1].id == zone.id
        else:
            with pytest.raises(PreparationError, match='historical_existing_match_unresolved'):
                citizen_archive_match(db, output, claim, lock=True)
        assert before == (event.status, event.verified_at, event.ended_at, zone.is_active, report.raw_text)


def test_native_selection_keeps_legacy_only_articles_and_existing_collection_states(prepared):
    from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
    from app.services.news_results_service import browse_news_results
    from app.services.news_collection_service import browse_news_collection
    from app.services.news_native_read_context import SavedNativeReadContext
    from app.services.news_historical_processing import database_identity
    from app.services.news_ner_durable.read_projection import build_read_projection
    from app.services.news_ner_durable.adapter import verify_saved_result
    from app.services.news_ner_durable.contracts import RunEvidence
    h = prepared
    with h.factory() as db, db.begin():
        run = db.get(NewsExtractionRun, h.ids[0]); version = db.get(NewsArticleVersion, run.article_version_id)
        result = verify_saved_result(RunEvidence.from_records(run, version), run.result, h.trusted)
        result.read_projection = build_read_projection(RunEvidence.from_records(run, version).source(), result, h.trusted.catalog)
        run.result = result.model_dump(mode='json', by_alias=True)
        db.get(NewsArticle, 101).review_state = 'local_update'
        legacy = deepcopy(h.package.documents['inventory.json']['sources'][0]['input_snapshot'])
        legacy['canonical_url'] = 'https://example.org/legacy-only'
        article = NewsArticle(canonical_url=legacy['canonical_url'], title='Legacy only', article_text=legacy['article_text'],
            publisher_source_id='fictional', excerpt='', content_fingerprint=sha(legacy))
        db.add(article); db.flush()
        version = NewsArticleVersion(article_id=article.id, input_snapshot=legacy, input_fingerprint=sha(legacy))
        db.add(version); db.flush()
        claim = deepcopy(h.package.documents['inventory.json']['history'][0]['claim'])
        claim['raw_place_name'] = claim['canonical_road']
        claim['place_char_start'] = legacy['article_text'].index(claim['raw_place_name'])
        claim['place_char_end'] = claim['place_char_start'] + len(claim['raw_place_name'])
        claim['evidence_sentence_offset'] = [0, len(legacy['article_text'])]
        from app.schemas.news_extraction import ExtractedClaim
        claim = ExtractedClaim.model_validate(claim).model_dump(mode='json')
        db.add(NewsExtractionRun(article_version_id=version.id, pipeline_version='legacy-fictional', mode='rules_only',
            status='completed', completed_at=NOW, result={'claims':[claim], 'errors':[], 'is_metadata_only':False,
                'extracted_at':NOW.isoformat()}))
        legacy_id = article.id
    context = SavedNativeReadContext(h.trusted.pipeline_version, database_identity(h.engine))
    with h.factory() as db:
        page = browse_news_results(db, page=1, page_size=50, search='', publisher=None, condition=None,
            placement=None, order='extraction_newest', processing_context=context)
        assert any(i.article_id == legacy_id and i.processing_method == 'rules_only' for i in page.items)
        assert any(i.article_id == 101 and i.processing_method == 'ner_rules_v1' for i in page.items)
        collection = browse_news_collection(db, page=1, page_size=50, search='', publisher=None,
            status='all', processing_context=context)
        native = next(i for i in collection.items if i.id == 101)
        assert native.collection_status != 'excluded' and native.location_count > 0
        assert next(i for i in collection.items if i.id == legacy_id).processing_status == 'completed'


def test_shared_authority_rejects_active_package_and_allows_archive_repeats(prepared, monkeypatch):
    from app.services import news_historical_outputs as outputs
    from app.services.news_historical_preparation import build_preparation, SourceSpec, text_sha
    from app.services.news_historical_processing import HistoricalPackage
    h = prepared
    authority = ArchiveAuthority(expected_authority(h.engine, 'save_archives', sha(h.options['policy']),
        sha(h.trusted.manifest)), '')
    authority = ArchiveAuthority(authority.policy, sha(authority.policy))
    with pytest.raises(PreparationError, match='archive_only'):
        outputs.historical_outputs(h.engine, h.package, h.trusted, apply=True,
            authorization=authority, **h.options)
    inventory = deepcopy(h.package.documents['inventory.json']); inventory['history'] = []
    specs = tuple(SourceSpec(r['article_id'],r['version_id'],r['input_fingerprint'],
        text_sha(r['input_snapshot']['article_text']), r['input_snapshot']['canonical_url'],
        r['input_snapshot']['publisher'],r['input_snapshot']['published_at']) for r in inventory['sources'])
    documents = build_preparation(inventory, h.package.manifest['assets'], specs=specs, candidates=(), dataset_id='shared-archive-fixture')
    package = HistoricalPackage(sha(documents['manifest.json']), documents)
    policy = outputs.expected_output_policy(package, h.trusted, h.engine)
    authority_policy = expected_authority(h.engine, 'save_archives', sha(policy), sha(h.trusted.manifest))
    authorization = ArchiveAuthority(authority_policy, sha(authority_policy))
    monkeypatch.setattr(outputs, 'disposable_target', lambda *_: False)
    options = {**h.options, 'policy':policy, 'policy_sha256':sha(policy), 'authorization':authorization}
    first = outputs.historical_outputs(h.engine, package, h.trusted, apply=True, **options)
    second = outputs.historical_outputs(h.engine, package, h.trusted, apply=True, **options)
    assert first['outputs'] == second['outputs']
    assert all(o['disposition'] == 'historical_archive' for o in first['outputs'])
    with h.factory() as db:
        assert not any(db.scalars(select(models.FloodAvoidanceZone.is_active).where(
            models.FloodAvoidanceZone.id.in_([z for o in first['outputs'] for z in o['zone_ids']]))))


def test_cloud_sql_socket_is_pinned_and_other_query_overrides_are_rejected():
    from sqlalchemy.engine import URL
    from app.services.news_historical_processing import database_identity
    from app.services.news_history_authority import valid_shared_connection
    one = SimpleNamespace(url=URL.create('postgresql+psycopg', database='fixture', query={'host':'/cloudsql/project:region:one'}))
    two = SimpleNamespace(url=one.url.set(query={'host':'/cloudsql/project:region:two'}))
    assert valid_shared_connection(one) and database_identity(one) != database_identity(two)
    assert not valid_shared_connection(SimpleNamespace(url=one.url.set(query={'options':'unsafe'})))
