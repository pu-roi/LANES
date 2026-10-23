"""Read-only E0 inventory. No ORM mutation, queue claim or inference imports."""
from __future__ import annotations

import hashlib
from sqlalchemy import text, bindparam
from sqlalchemy.engine import Engine

from app.services.news_historical_preparation import SOURCES, PreparationError
from app.services.news_ner_durable.contracts import sha


def read_preparation_inventory(engine: Engine, confirmed_database: str, *, version_ids: tuple[int, ...] | None = None) -> dict:
    if not confirmed_database or engine.url.database != confirmed_database:
        raise PreparationError("database_confirmation_mismatch")
    from app.services.news_historical_processing import database_identity
    with engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        connection.execute(text("SET LOCAL statement_timeout = '10000'"))
        connection.execute(text("SET LOCAL lock_timeout = '5000'"))
        if (connection.execute(text("SELECT current_database()")).scalar_one() != confirmed_database
                or connection.execute(text("SHOW transaction_read_only")).scalar_one() != "on"):
            raise PreparationError("read_only_database_mismatch")
        selected = version_ids if version_ids is not None else tuple(s.version_id for s in SOURCES)
        if not selected or len(selected) > 1000 or len(set(selected)) != len(selected) or any(type(i) is not int or i <= 0 for i in selected):
            raise PreparationError('historical_version_selection_invalid')
        sources = [dict(row) for row in connection.execute(text("""
            SELECT article_id,id AS version_id,input_fingerprint,input_snapshot
            FROM news_article_versions WHERE id IN :ids ORDER BY id
            """).bindparams(bindparam('ids', expanding=True)), {'ids': selected}).mappings()]
        feeds = [dict(row) for row in connection.execute(text("""
            SELECT article_id,source_id,raw_metadata FROM news_article_feed_entries
            WHERE article_id IN :ids ORDER BY id
            """).bindparams(bindparam('ids', expanding=True)), {'ids': [r['article_id'] for r in sources]}).mappings()]
        history = [] if version_ids is not None else [dict(row) for row in connection.execute(text("""
            SELECT v.article_id,r.id AS run_id,r.mode,s.claim_ordinal,
                   r.result->'claims'->s.claim_ordinal AS claim,
                   s.case_id,d.id AS decision_id,z.id AS zone_id,z.event_id,z.is_active,
                   e.status AS event_status,ST_IsValid(z.geometry) AS geometry_valid,
                   ST_SRID(z.geometry) AS geometry_srid,encode(ST_AsEWKB(z.geometry),'hex') AS geometry_hex
            FROM news_article_versions v JOIN news_extraction_runs r ON r.article_version_id=v.id
            JOIN news_claim_sources s ON s.extraction_run_id=r.id
            JOIN news_claim_evaluations ev ON ev.claim_source_id=s.id
            JOIN news_claim_decisions d ON d.evaluation_id=ev.id
            JOIN news_claim_zone_links l ON l.decision_id=d.id
            JOIN flood_avoidance_zones z ON z.id=l.zone_id JOIN flood_events e ON e.id=z.event_id
            WHERE z.id IN (59,60,61,62,63) ORDER BY z.id,d.id
            """)).mappings()]
        for row in history:
            row["geometry_sha256"] = hashlib.sha256(bytes.fromhex(row.pop("geometry_hex"))).hexdigest()
        modes = [dict(row) for row in connection.execute(text("""
            SELECT mode,status,count(*) AS count FROM news_extraction_runs GROUP BY mode,status ORDER BY mode,status
            """)).mappings()]
        connection.rollback()
    return {"schema": "lanes-historical-e0-inventory-v1", "read_only": True,
            "database_identity_sha256": database_identity(engine), "sources": sources, "feeds": feeds,
            "history": history, "processing_modes_at_preparation": modes}
