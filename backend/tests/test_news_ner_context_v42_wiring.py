"""Promoted backend wiring using fictional cached mentions only."""
import asyncio
import pytest

from app.services.news_ner.worker import CONTEXT_IMPLEMENTATION,context_from_effective_mentions
from app.services.news_ner.runtime import PreviewError
from app.services.news_ner_preview_service import preview_article
from training.flood_ner.context_cases_v42 import core_cases,result
from test_news_ner_preview import article,config,fake_runner


@pytest.mark.parametrize('case',core_cases(),ids=lambda c:c['case_id'])
def test_worker_pure_context_boundary(case):
    assert CONTEXT_IMPLEMENTATION=='lanes-context-association-v42'
    assert result(case,context_from_effective_mentions(case['raw']))['passed']


def test_host_rejects_predecessor_context_provenance():
    async def stale(raw,*args):
        value=await fake_runner(raw,*args)
        value['provenance']['context_rules']='lanes-context-association-v41'
        return value
    with pytest.raises(PreviewError,match='preview_worker_failed'):
        asyncio.run(preview_article(article(),config(),stale))
