"""Read-only trace of saved articles, displayed claims and current extraction."""
from __future__ import annotations

import json
import argparse
from pathlib import Path

from sqlalchemy import func, literal, select, text

from app.core.database import SessionLocal
from app.crud.news_processing import current_pipeline_version
from app.crud.news_results import list_result_rows, readable_claim
from app.crud.news_collection import list_collection
from app.models.news import NewsArticle, NewsArticleVersion, NewsExtractionRun
from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.services.news_presentation_service import claim_reading_reason


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compare-local-rules", action="store_true",
        help="Compare pure local rules/CSV extraction; never calls the hybrid auditor or HTTP.")
    parser.add_argument("--summary-only", action="store_true", help="Print totals without article text or titles.")
    parser.add_argument("--validate-policy", action="store_true", help="Read-only PostgreSQL positive/negative predicate checks using synthetic literals.")
    parser.add_argument("--replay-result", type=Path,
        help="Compare historical replay claims with the real PostgreSQL predicate using read-only literals.")
    args = parser.parse_args()
    with SessionLocal() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        if args.replay_result:
            payload = json.loads(args.replay_result.read_text(encoding="utf-8"))
            readable = road_count = 0
            for raw_claim in payload["claims"]:
                claim = ExtractedClaim.model_validate(raw_claim)
                fields = claim.model_dump()
                fields["uncertainty_reasons"] = json.dumps(fields["uncertainty_reasons"])
                # Production's JSON ->> accessor returns text, including for
                # booleans. Literal checks must preserve that SQL type.
                for field in ("flood_mentioned", "is_negated", "is_forecast", "is_historical"):
                    fields[field] = "true" if fields[field] else "false"
                actual = bool(db.scalar(select(readable_claim(lambda field: literal(fields.get(field))))))
                if actual != (claim_reading_reason(claim) is None):
                    raise AssertionError("Replay claim differs between PostgreSQL and the detail reader")
                readable += actual
                road_count += actual and claim.place_type == "street"
            print(json.dumps({"postgres_replay_claim_checks": len(payload["claims"]),
                              "readable_claims": readable, "readable_road_sites": road_count, "passed": True}))
        if args.validate_policy:
            checks = [
                ("Binaha ang Maybunga sa Pasig City.", "1381400000", "City of Pasig", True),
                ("A basin helps prevent flooding, but streets are flooded in Pasig City.", None, "City of Pasig", True),
                ("Knee-deep flooding was observed in Manila.", "1380600000", "City of Manila", True),
                ("The school is regularly flooded during heavy rain.", "1381300000", "Quezon City", False),
                ("A basin helps mitigate localized flooding.", "1381300000", "Quezon City", False),
                ("Drainage at UP-PGH in Manila will help address flooding.", "1380600000", "City of Manila", False),
                ("Residents waded through waist-deep waters in Bangkok.", None, None, False),
                ("The interior ministry said residents were flooded.", "0504119009", "San Jacinto", False),
                ("Officials in Pasig City discussed flooding and drainage.", "1381400000", "City of Pasig", False),
                ("Pasig City will be flooded with knee-deep water.", "1381400000", "City of Pasig", False),
                ("A flood drill in Manila simulated knee-deep floodwater.", "1380600000", "City of Manila", False),
                ("Madalas binabaha ang Maybunga sa Pasig City.", "1381400000", "City of Pasig", False),
                ("Flooding affected roads in Pasig City.", "1381400000", "City of Pasig", True),
                ("Flooded roads in Manila stranded commuters.", "1380600000", "City of Manila", True),
                ("Floodwaters hit roads in Pasig City.", "1381400000", "City of Pasig", True),
                ("Flooding along East Avenue corner EDSA cleared by 3:20 p.m.", "1381300000", "Quezon City", True),
                ("Floodwaters receded in affected areas of Quezon City.", "1381300000", "Quezon City", True),
                ("Flooding on East Avenue in Quezon City might subside by 3:20 p.m.", "1381300000", "Quezon City", False),
                ("Flood-control works on East Avenue were cleared for construction.", "1381300000", "Quezon City", False),
            ]
            for sentence, code, city, expected in checks:
                fields = {"raw_place_name": "Test site", "evidence_sentence": sentence,
                          "canonical_city": city, "psgc_code": code, "condition": "active"}
                actual = bool(db.scalar(select(readable_claim(lambda field: literal(fields.get(field))))))
                if actual != expected:
                    raise AssertionError("Database evidence predicate disagrees with the expected policy")
            print(json.dumps({"postgres_policy_checks": len(checks), "passed": True}))
        articles = list(db.scalars(select(NewsArticle).order_by(NewsArticle.id).limit(100)))
        rows, total, _, _ = list_result_rows(db, page=1, page_size=100, search="", publisher=None,
            condition=None, placement=None, order="extraction_newest")
        _, attention_total, _, collection_counts, _ = list_collection(db, page=1, page_size=12,
            search="", publisher=None, status="attention")
        print(json.dumps({"runtime_pipeline": current_pipeline_version(), "articles": len(articles),
                          "displayed_claims": total,
                          "collection_counts": collection_counts, "attention_articles": attention_total,
                          "current_version_runs": dict(db.execute(select(NewsExtractionRun.status, func.count()).where(
                              NewsExtractionRun.pipeline_version == current_pipeline_version()).group_by(NewsExtractionRun.status)).all()),
                          "all_extraction_runs": db.scalar(select(func.count()).select_from(NewsExtractionRun)),
                          "source_versions": db.scalar(select(func.count()).select_from(NewsArticleVersion)),
                          "migration_head": db.scalar(text("SELECT version_num FROM alembic_version"))}, default=str))
        if args.summary_only:
            db.rollback()
            return
        by_article: dict[int, list] = {}
        for row in rows:
            claim = row["claim"] if isinstance(row["claim"], dict) else json.loads(row["claim"])
            by_article.setdefault(row["article_id"], []).append({
                "run": row["run_id"], "index": row["claim_index"],
                "place": claim.get("raw_place_name"), "city": claim.get("canonical_city"),
                "psgc": claim.get("psgc_code"), "condition": claim.get("condition"),
                "depth": claim.get("depth_raw"), "sentence": claim.get("evidence_sentence", "")[:240],
            })
        for article in articles:
            latest = db.execute(select(NewsExtractionRun).join(NewsArticleVersion).where(
                NewsArticleVersion.article_id == article.id).order_by(
                    NewsExtractionRun.created_at.desc(), NewsExtractionRun.id.desc()).limit(1)).scalar_one_or_none()
            comparison = None
            if args.compare_local_rules and article.article_text and not article.article_error:
                # This parser uses local regex/CSV references only. No hybrid
                # service, HTTP client, external AI or persistence is invoked.
                from app.services.taglish_extraction_service import extract_taglish_flood_facts
                fresh = extract_taglish_flood_facts(NewsArticleExtractorInput(
                    article_id=article.id, canonical_url=article.canonical_url,
                    publisher=article.publisher_source_id, title=article.title, excerpt=article.excerpt or "",
                    article_text=article.article_text, published_at=article.published_at))
                comparison = [{"place": c.raw_place_name, "city": c.canonical_city,
                    "condition": c.condition, "sentence": c.evidence_sentence[:240]} for c in fresh.claims]
            print(json.dumps({"article": article.id, "title": article.title,
                "published": article.published_at, "url": article.canonical_url,
                "body_chars": len(article.article_text or ""), "body_error": bool(article.article_error),
                "latest_run": latest.id if latest else None,
                "saved_pipeline": latest.pipeline_version if latest else None,
                "saved_extractor": latest.result.get("extractor_version") if latest and latest.result else None,
                "displayed": by_article.get(article.id, []), "fresh_local_rules": comparison}, default=str, ensure_ascii=False))
        db.rollback()


if __name__ == "__main__":
    main()
