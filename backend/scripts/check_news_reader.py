"""Protected canary acceptance. GET requests and read-only SQL; no providers or writes."""
from __future__ import annotations

import argparse
from datetime import timedelta
import json
from urllib.parse import urlencode, urlsplit

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import engine
from app.core.security import create_access_token
from app.services.news_native_read_context import configured_native_read_context, validate_native_reader_startup
from app.services.news_results_service import browse_news_results


def checked_url(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or not parsed.hostname.endswith('.run.app')
            or parsed.username or parsed.password or parsed.port or parsed.path not in {'', '/'}
            or parsed.query or parsed.fragment):
        raise ValueError('reader_check_url_invalid')
    return value.rstrip('/')


def identities(page: dict) -> list[dict]:
    return [{key: row[key] for key in ('key', 'run_id', 'article_id', 'article_version_id', 'claim')}
            for row in page['items']]


def get_json(client: httpx.Client, url: str, path: str) -> dict:
    response = client.get(url + path)
    if response.status_code != 200:
        raise ValueError('reader_check_http_' + str(response.status_code))
    return response.json()


def check_detail(item: dict, detail: dict) -> None:
    if (detail['item']['key'] != item['key']
            or (not detail.get('is_metadata_only', False) and not detail['captured_input'].get('article_text'))):
        raise ValueError('reader_check_detail_mismatch')


def check_reader(candidate: str, baseline: str) -> dict:
    candidate, baseline = checked_url(candidate), checked_url(baseline)
    validate_native_reader_startup(engine)
    context = configured_native_read_context()
    if context is None:
        raise ValueError('reader_check_native_context_required')
    with Session(engine) as db:
        db.execute(text('SET TRANSACTION READ ONLY'))
        db.execute(text('SET LOCAL statement_timeout=15000'))
        uid = db.scalar(text("SELECT u.id FROM users u JOIN roles r ON r.id=u.role_id "
                             "WHERE u.is_active AND r.name='Super Admin' ORDER BY u.id LIMIT 1"))
        if uid is None:
            raise ValueError('reader_check_staff_unavailable')
        expected = browse_news_results(db, page=1, page_size=12, search='', publisher=None,
            condition=None, placement=None, order='extraction_newest', processing_context=context).model_dump(mode='json')
        from app.models.report import FloodEvent
        from app.services.spatial_browse_service import history_query, history_overview, history_collection
        history_ids = [row.id for row in history_query(db, {'status_filter': 'all'})
                       .with_entities(FloodEvent.id).order_by(FloodEvent.id.desc()).limit(3)]
        expected_history = {event_id: history_overview(db, event_id) for event_id in history_ids}
        expected_collections = {
            event_id: {name: history_collection(db, event_id, name, 1).model_dump(mode='json')
                       for name in ('reports', 'zones', 'locations', 'timeline', 'news_sources')}
            for event_id in history_ids}
    token = create_access_token({'sub': str(uid)}, expires_delta=timedelta(minutes=5))
    base_path = '/api/v1/admin/news/results'
    with httpx.Client(timeout=60, follow_redirects=False, headers={'Authorization': 'Bearer ' + token}) as client:
        first = get_json(client, candidate, base_path + '?page=1&page_size=12&order=extraction_newest')
        if first['total'] != expected['total'] or identities(first) != identities(expected):
            raise ValueError('reader_check_database_selection_mismatch')
        queries = [dict(page=1, page_size=12, order='extraction_newest'),
                   dict(page=1, page_size=2), dict(page=2, page_size=2)]
        if first['items']:
            item = first['items'][0]
            queries += [dict(publisher=item['publisher_source_id']),
                        dict(search=item['claim']['raw_place_name'])]
        for query in queries:
            path = base_path + '?' + urlencode(query)
            actual, prior = get_json(client, candidate, path), get_json(client, baseline, path)
            if actual['total'] != prior['total'] or identities(actual) != identities(prior):
                raise ValueError('reader_check_serving_selection_mismatch')
        for item in first['items']:
            suffix = ('/groups/' + item['group_id'] if item.get('group_id') else '/' + str(item['claim_index']))
            detail = get_json(client, candidate, base_path + '/' + str(item['run_id']) + suffix)
            check_detail(item, detail)
        for article_id in sorted({item['article_id'] for item in first['items']}):
            detail = get_json(client, candidate, '/api/v1/admin/news/articles/' + str(article_id))
            if detail['article']['id'] != article_id:
                raise ValueError('reader_check_article_mismatch')
        get_json(client, candidate, '/api/v1/admin/news/collection?page=1&page_size=12')
        for event_id in history_ids:
            path = '/api/v1/admin/flood-events/' + str(event_id) + '/inspection'
            overview = get_json(client, candidate, path)
            for key in ('id', 'media_count', 'zone_count', 'supporting_report_count', 'location_count'):
                if overview[key] != expected_history[event_id][key]:
                    raise ValueError('reader_check_history_inspection_mismatch')
            for name, expected_collection in expected_collections[event_id].items():
                actual = get_json(client, candidate, path + '/' + name + '?page=1')
                if (actual['total'] != expected_collection['total']
                        or actual['page'] != expected_collection['page']
                        or actual['items'] != expected_collection['items']):
                    raise ValueError('reader_check_history_collection_mismatch')
        for url in (candidate, baseline):
            response = httpx.get(url + base_path, timeout=30, follow_redirects=False)
            if response.status_code not in {401, 403}:
                raise ValueError('reader_check_authentication_failed')
    return {'status': 'reader_canary_passed', 'total': first['total'],
            'selected_run_ids': sorted({item['run_id'] for item in first['items']}),
            'history_event_ids': history_ids,
            'checks': ['database_selection', 'serving_selection', 'pagination', 'filters',
                       'group_details', 'articles', 'collection', 'history_inspection',
                       'history_collections', 'authentication'],
            'database_writes': 0, 'provider_requests': 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--baseline', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(check_reader(args.candidate, args.baseline)))
    except Exception as error:
        # Avoid exception rendering: HTTP headers and DB connections are private.
        reason = str(error) if isinstance(error, ValueError) and str(error).startswith('reader_check_') else type(error).__name__
        print(json.dumps({'status': 'reader_canary_failed', 'reason': reason}))
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
