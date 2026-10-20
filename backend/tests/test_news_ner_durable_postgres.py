"""Persist C2 fictional envelopes only in the owned opt-in PostGIS queue database."""
from copy import deepcopy

import pytest
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import DBAPIError

from app.crud.news_evaluation import validate_run
from app.crud.news_processing import claim_due_run, finish_owned_run
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.schemas.news_extraction import NewsArticleExtractorInput
from app.services.news_ner.location_pipeline import from_neural_mentions
from app.services.news_ner_durable.adapter import build_native_result, verify_saved_result
from app.services.news_ner_durable.contracts import NerEvidenceError, RunEvidence, capture_native_input
from app.services.news_ner_durable.source_check import check_native_source
from test_news_ner_durable import BODY, NOW, make_case, trusted
from test_news_processing_postgres import postgres_queue, seed


@pytest.mark.parametrize('prefix',['','  🌧️\n'])
def test_native_jsonb_roundtrip_preserves_inputs_proof_and_legacy_history(postgres_queue,trusted,prefix):
    seed(postgres_queue)
    with postgres_queue() as db,db.begin():
        row=db.scalar(select(NewsArticle));old=db.scalar(select(NewsArticleVersion))
        old_id,old_snapshot=old.id,deepcopy(old.input_snapshot)
        row.article_text=prefix+BODY;row.published_at=NOW
        source=NewsArticleExtractorInput(article_id=row.id,canonical_url=row.canonical_url,publisher=row.publisher_source_id,
            title=row.title,excerpt=row.excerpt,article_text=row.article_text,published_at=row.published_at)
        snapshot,fingerprint=capture_native_input(source)
        version=NewsArticleVersion(article_id=row.id,input_fingerprint=fingerprint,input_snapshot=snapshot)
        db.add(version);db.flush()
        run=NewsExtractionRun(article_version_id=version.id,pipeline_version=trusted.pipeline_version,mode='ner_rules_v1',status='pending',attempt_count=0)
        db.add(run);db.flush();run_id,version_id=run.id,version.id
        claim=claim_due_run(db,NOW,mode='ner_rules_v1',pipeline_version=trusted.pipeline_version)
        assert claim.run_id==run_id
        context=RunEvidence.from_records(run,version)
        _,_,_,fictional,_=make_case(trusted,row.article_text)
        raw={**context.source().runtime_request(fingerprint),'mentions':fictional['proposal']['neural_mentions']}
        native=from_neural_mentions(raw)
        result=build_native_result(context,{**native,'provenance':trusted.provenance,'measurements':fictional['measurements']},trusted,extracted_at=NOW)
        assert finish_owned_run(db,claim,NOW,result=result.model_dump(mode='json',by_alias=True))
    with postgres_queue() as db:
        run=db.get(NewsExtractionRun,run_id);version=db.get(NewsArticleVersion,version_id)
        verified=verify_saved_result(RunEvidence.from_records(run,version),run.result,trusted)
        assert verified.claims[0].confidence_score is None
        assert version.input_snapshot['article_text']==prefix+BODY
        assert version.input_snapshot['publication_evidence']['timezone_known'] is False
        assert check_native_source(run,version,run.result,0,trusted,now=NOW).outcome=='verified'
        assert db.get(NewsArticleVersion,old_id).input_snapshot==old_snapshot
        assert db.scalar(select(func.count()).select_from(NewsArticleVersion))==2
        with pytest.raises(ValueError,match='extraction_not_completed'):validate_run(run,version)
        altered=deepcopy(run.result);altered['claims'][0]['condition']='rising'
        with pytest.raises(NerEvidenceError,match='ner_result_contract_invalid'):
            check_native_source(run,version,altered,0,trusted,now=NOW)
        for table in ('news_claim_sources','news_claim_decisions','flood_avoidance_zones'):
            assert db.scalar(text('SELECT count(*) FROM '+table))==0
    with pytest.raises(DBAPIError,match='immutable'):
        with postgres_queue() as db,db.begin():
            db.execute(update(NewsArticleVersion).where(NewsArticleVersion.id==version_id).values(input_snapshot={'changed':'source'}))
