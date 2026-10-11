"""Check configuration; optionally probe free-only auditing with synthetic text.

No database access, news discovery, publication, or map/routing writes.
Default checks settings only. --probe makes one free-router/model request.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timedelta, timezone

from app.schemas.news_extraction import ExtractedClaim, NewsArticleExtractorInput
from app.services.news_claim_auditor import AUDIT_TIMEOUT_SECONDS, AuditorConfig, NewsClaimAuditor


async def check_auditor(config: AuditorConfig, *, probe: bool = False,
                        timeout_seconds: float = AUDIT_TIMEOUT_SECONDS) -> dict:
    result = dict(provider=config.provider, model=config.model,
                  database_access=False, public_data_written=False)
    error = config.error_code()
    if error:
        return dict(result, status="configuration_error", reason=error)
    if config.provider != "openrouter" or config.model != "openrouter/free":
        return dict(result, status="configuration_error", reason="free_openrouter_router_required",
                    provider_request_made=False)
    try:
        auditor = NewsClaimAuditor(config, timeout_seconds=timeout_seconds)
    except ValueError:
        return dict(result, status="configuration_error", reason="auditor_timeout_invalid",
                    provider_request_made=False)
    result["timeout_seconds"] = auditor.timeout_seconds
    if not probe:
        return dict(result, status="configuration_ok", provider_request_made=False)
    # An explicitly synthetic historical fixture: never a current source claim.
    body = ("Synthetic test article, not a real flood report. At 07:00 Philippine time on "
            "January 1, 2020, Sample Road in Pasig City was flooded knee deep.")
    start = body.index("Sample Road")
    observed = datetime(2020, 1, 1, 7, tzinfo=timezone(timedelta(hours=8)))
    claim = ExtractedClaim(raw_place_name="Sample Road", canonical_city="City of Pasig",
        canonical_road="Sample Road", place_type="street", place_char_start=start,
        place_char_end=start + len("Sample Road"), evidence_sentence=body,
        evidence_sentence_offset=(0, len(body)), condition="active", depth_raw="knee deep",
        depth_canonical="knee", event_time_raw="07:00 Philippine time on January 1, 2020",
        event_time_kind="observation", event_time_resolved=observed, is_historical=True)
    article = NewsArticleExtractorInput(article_id=0, canonical_url="https://example.org/lanes-auditor-self-test",
        publisher="LANES synthetic self-test", title="Synthetic historical fixture", article_text=body,
        published_at=observed + timedelta(hours=1), fetched_at=observed + timedelta(hours=2))
    audit = await auditor.audit(claim, article)
    return dict(result, status="valid_response" if audit.evidence is not None else "probe_failed",
                outcome=audit.outcome, reason=audit.reason_code, provider_request_made=True,
                provider_http_status=getattr(audit, "provider_http_status", None))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=AUDIT_TIMEOUT_SECONDS,
                        help="Wait 1-120 seconds for the single probe (default: 20); no persistent setting change")
    args = parser.parse_args()
    result = asyncio.run(check_auditor(AuditorConfig.from_environment(), probe=args.probe,
                                     timeout_seconds=args.timeout_seconds))
    print(json.dumps(result, indent=2))
    if result["status"] not in {"configuration_ok", "valid_response"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
