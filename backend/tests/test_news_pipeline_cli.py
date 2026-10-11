"""No live discovery, provider request or configured database is used."""
from datetime import date
import json
import sys

import httpx
import pytest

from app.services.news_sources import NewsSource
from scripts import run_news_discovery as discovery, run_news_pipeline as pipeline_cli

SOURCE = NewsSource("fixture","Fixture",("example.org",),("https://example.org/feed",),date(2026,10,5),True)


@pytest.mark.parametrize("args",[
    ["--probe","--pipeline"],["--discover","--pipeline","--dry-run"],
    ["--discover","--pipeline","--process"],["--extract-saved","--pipeline","--dry-run"],
    ["--process-saved","--pipeline","--limit","201"],
])
def test_invalid_pipeline_cli_never_opens_storage_or_network(args,monkeypatch):
    monkeypatch.setattr(discovery,"SessionLocal",lambda: pytest.fail("Invalid mode opened storage"))
    monkeypatch.setattr(discovery.httpx,"Client",lambda **kwargs: pytest.fail("Invalid mode opened network"))
    monkeypatch.setattr(sys,"argv",["collector",*args])
    with pytest.raises(SystemExit) as caught: discovery.main()
    assert caught.value.code == 2


@pytest.mark.parametrize("status",[304,503])
def test_discovery_always_runs_pipeline_for_saved_evidence_even_without_new_feed_content(monkeypatch,capsys,status):
    from app.services.news_feed_service import FeedProbe
    from types import SimpleNamespace
    calls=[]
    def capture(*args,**kwargs):
        return SimpleNamespace(candidates=[],notices=[],probes=[FeedProbe(
            source_id=SOURCE.id,publisher=SOURCE.publisher,feed_url=SOURCE.feed_urls[0],
            status="unchanged" if status == 304 else "http_error",http_status=status,
            entry_count=0,publisher_link_count=0,newest_published_at=None)])
    async def run(factory,**kwargs):
        assert kwargs["unbound_only"] and kwargs["sources"] == (SOURCE,)
        calls.append("pipeline")
        return {"publication":{"expired":1},"footprints":{"catalog_status":"not_configured"}}
    class EmptySession:
        def __enter__(self): return self
        def __exit__(self,*args): pass
    monkeypatch.setattr(discovery,"SessionLocal",EmptySession)
    monkeypatch.setattr(discovery,"load_news_sources",lambda _: (SOURCE,))
    monkeypatch.setattr(discovery,"discover_news",capture)
    monkeypatch.setattr(discovery,"run_news_pipeline",run)
    real=httpx.Client
    monkeypatch.setattr(discovery.httpx,"Client",lambda **kwargs: real(transport=httpx.MockTransport(lambda _:pytest.fail("Unexpected fetch"))))
    monkeypatch.setattr(sys,"argv",["collector","--discover","--pipeline","--limit","2"])
    assert discovery.main() == (0 if status == 304 else 1)
    assert calls == ["pipeline"] and json.loads(capsys.readouterr().out)["pipeline"]["publication"]["expired"] == 1


def test_saved_pipeline_mode_preserves_stage_errors_without_network(monkeypatch,capsys):
    async def run(factory,**kwargs):
        assert kwargs["limit"] == 2 and kwargs["unbound_only"]
        return {"footprints":{"skipped":[{"reason_code":"invalid_operational_footprint_catalog"}]}}
    monkeypatch.setattr(discovery,"load_news_sources",lambda _: (SOURCE,))
    monkeypatch.setattr(discovery,"run_news_pipeline",run)
    monkeypatch.setattr(discovery.httpx,"Client",lambda **kwargs:pytest.fail("Saved mode opened HTTP"))
    monkeypatch.setattr(sys,"argv",["collector","--process-saved","--pipeline","--limit","2"])
    assert discovery.main() == 1
    assert json.loads(capsys.readouterr().out)["footprints"]["skipped"][0]["reason_code"] == "invalid_operational_footprint_catalog"


@pytest.mark.asyncio
async def test_saved_worker_carries_both_cursors_and_reports_activation_failure(monkeypatch,capsys):
    async def run(factory,**kwargs):
        assert kwargs["seed_cursor"] == 7 and kwargs["footprint_cursor"] == 11 and kwargs["unbound_only"]
        return {"next_seed_cursor":8,"next_footprint_cursor":12,
                "footprints":{"skipped":[{"case_id":1,"reason_code":"stale_case_revision"}]}}
    monkeypatch.setattr(pipeline_cli,"run_news_pipeline",run)
    assert await pipeline_cli.worker(2,7,None,11) == 1
    assert json.loads(capsys.readouterr().out)["next_footprint_cursor"] == 12
