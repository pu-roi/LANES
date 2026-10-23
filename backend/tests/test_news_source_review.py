"""Read models distinguish a current capture from immutable run evidence."""
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services.news_source_read_service import compare_source_capture, require_current_pilot_capture, supporting_passages
from app.services.news_ner_durable.resolution import ResolutionError
from app.services.news_saved_run_service import SavedRunReadError

NOW = datetime(2026, 10, 23, tzinfo=timezone.utc)


def records(body='Publisher report: Sample Road flooded as of 2:47 p.m.'):
    article = SimpleNamespace(id=47, canonical_url='https://example.org/flood', publisher_source_id='fictional',
        title='Flood report', excerpt='', article_text=body, published_at=NOW, fetched_at=NOW)
    version = SimpleNamespace(article_id=47, created_at=NOW, input_snapshot={'article_text': body})
    return article, version


def test_superseded_input_is_not_relabelled_as_the_current_article():
    article, version = records()
    version.input_snapshot['article_text'] = 'Older index capture: Different Road waist-deep.'
    before = deepcopy(version.input_snapshot)
    review = compare_source_capture(article, version)
    assert review.state == 'different_capture'
    assert review.current_input.article_text == article.article_text
    assert review.selected_captured_at == version.created_at
    assert version.input_snapshot == before
    with pytest.raises(ResolutionError, match='pilot_source_capture_requires_review'):
        require_current_pilot_capture(SimpleNamespace(get=lambda *args: article), version)


def test_compatible_native_metadata_does_not_change_body_identity():
    article, version = records()
    version.input_snapshot.update(capture_schema='lanes-news-ner-input-v1')
    assert compare_source_capture(article, version).state == 'matching_capture'
    require_current_pilot_capture(SimpleNamespace(get=lambda *args: article), version)


@pytest.mark.parametrize('body', [None, '', '   '])
def test_missing_current_capture_is_explicit_and_blocks_pilot(body):
    article, version = records(body)
    review = compare_source_capture(article, version)
    assert review.state == 'current_unavailable' and review.current_input is None
    with pytest.raises(ResolutionError, match='requires_review'):
        require_current_pilot_capture(SimpleNamespace(get=lambda *args: article), version)


def test_source_review_cannot_cross_article_ownership():
    article, version = records()
    version.article_id = 99
    with pytest.raises(SavedRunReadError, match='article_mismatch'):
        compare_source_capture(article, version)


def test_selected_quotes_omit_intervening_chrome_without_rewriting_the_source():
    body = 'Date\nGOOGLE PROMOTION\nSample Road'
    quote = {'start': 22, 'end': len(body), 'quote': 'Sample Road'}
    group = {'normalizations': {'audit': {'place': {'evidence': [quote]},
        'time': {'evidence': [{'start': 0, 'end': 4, 'quote': 'Date'}, quote]}}}}
    assert supporting_passages(group, body) == ['Date', 'Sample Road']
    assert body == 'Date\nGOOGLE PROMOTION\nSample Road'


def test_wrong_saved_quote_cannot_be_presented_as_source_evidence():
    group = {'normalizations': {'audit': {'place': {'evidence': [
        {'start': 0, 'end': 5, 'quote': 'Other'}]}}}}
    with pytest.raises(SavedRunReadError, match='passage_mismatch'):
        supporting_passages(group, 'Road A')
