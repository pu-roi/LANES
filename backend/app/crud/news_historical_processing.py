"""Bounded historical input inspection and capture persistence; no publication writes."""
from contextlib import contextmanager
from collections.abc import Iterator

from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.crud.news_processing import enqueue_input_snapshot
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.services.news_historical_preparation import PreparationError


@contextmanager
def readonly_historical_session(engine: Engine, confirmed_database: str) -> Iterator[Session]:
    if engine.url.get_backend_name() != 'postgresql' or not confirmed_database or engine.url.database != confirmed_database:
        raise PreparationError('historical_database_confirmation_mismatch')
    with engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection:
        connection.execute(text('SET TRANSACTION READ ONLY'))
        connection.execute(text("SET LOCAL statement_timeout = '5000'"))
        connection.execute(text("SET LOCAL lock_timeout = '5000'"))
        if (connection.scalar(text('SELECT current_database()')) != confirmed_database
                or connection.scalar(text('SHOW transaction_read_only')) != 'on'):
            raise PreparationError('historical_read_only_target_mismatch')
        try:
            with Session(bind=connection, autoflush=False) as db:
                yield db
        finally:
            connection.rollback()


def read_historical_state(db: Session, inputs: list[dict], pipeline: str) -> dict:
    inspector = inspect(db.connection())
    tables = set(inspector.get_table_names())
    revision = db.scalar(text('SELECT version_num FROM alembic_version')) if 'alembic_version' in tables else None
    state = {'revision': revision, 'tables_present': {'news_articles', 'news_article_versions',
        'news_extraction_runs', 'system_settings'} <= tables, 'sources': [], 'runs': [],
        'database': db.scalar(text('SELECT current_database()'))}
    if not state['tables_present']:
        return state
    # Match the actual named/validated check from approved revision e8a6f1c2d903,
    # including PostgreSQL's canonical expression, without altering the schema.
    expression = "((mode)::text = ANY ((ARRAY['rules_only'::character varying, 'ner_rules_v1'::character varying])::text[]))"
    state['native_mode_supported'] = bool(db.scalar(text("""
        SELECT EXISTS (SELECT 1 FROM pg_constraint
          WHERE conrelid='news_extraction_runs'::regclass
          AND conname='ck_news_extraction_runs_rules_only_mode' AND contype='c'
          AND convalidated AND conislocal AND NOT connoinherit
          AND pg_get_expr(conbin,conrelid,false)=:expression)
        """), {'expression': expression}))
    versions = db.execute(select(NewsArticleVersion, NewsArticle.canonical_url, NewsArticle.publisher_source_id)
        .join(NewsArticle, NewsArticle.id == NewsArticleVersion.article_id)
        .where(NewsArticleVersion.id.in_([i['source_version_id'] for i in inputs])))
    state['sources'] = [{'version_id': version.id, 'article_id': version.article_id,
        'input_fingerprint': version.input_fingerprint, 'input_snapshot': version.input_snapshot,
        'article_url': url, 'article_publisher': publisher} for version, url, publisher in versions]
    state['runs'] = list(db.scalars(select(NewsExtractionRun).join(NewsArticleVersion)
        .where(NewsArticleVersion.article_id.in_([i['article_id'] for i in inputs]),
            NewsArticleVersion.input_fingerprint.in_([i['native_input_fingerprint'] for i in inputs]),
            NewsExtractionRun.mode == 'ner_rules_v1', NewsExtractionRun.pipeline_version == pipeline)
        .order_by(NewsExtractionRun.id)))
    return state


def enqueue_historical_captures(db: Session, captures: tuple[dict, ...], pipeline: str) -> tuple[int, ...]:
    return tuple(enqueue_input_snapshot(db, c['article_id'], c['input_snapshot'], c['native_input_fingerprint'],
        mode='ner_rules_v1', pipeline_version=pipeline) for c in captures)


def read_historical_run_records(db: Session, run_ids: tuple[int, ...]) -> list[tuple[NewsExtractionRun, NewsArticleVersion]]:
    return list(db.execute(select(NewsExtractionRun, NewsArticleVersion)
        .join(NewsArticleVersion).where(NewsExtractionRun.id.in_(run_ids)).order_by(NewsExtractionRun.id)))
