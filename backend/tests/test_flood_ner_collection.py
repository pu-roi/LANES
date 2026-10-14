"""Offline historical-source integrity, review and collection boundaries."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import httpx
import pytest

from training.flood_ner.annotation.schema import SourceCapture, text_hash
from training.flood_ner.collection import (
    article_key, canonical_news_url, collect_candidates, collection_report,
    import_browser_capture, publication_date, publisher_for, same_story,
    source_entry, validate_reviewed, verify_capture_files, wikipedia_reference,
    write_reviewed_collection,
)
from training.flood_ner.sources import CaptureParser, capture_source, json_bytes
from training.flood_ner.cli import main

BODY = ('Floodwaters reached Purok 12 in Barangay Villa Luna, Cauayan, Isabela. '
        'Residents reported knee-deep water on the road at 8:30 a.m. Rescue workers '
        'said the bridge was impassable. Water later subsided, although household '
        'counts did not measure water depth. The barangay retained evacuation shelters.')


def test_expanded_collection_target_preserves_default_and_existing_register(tmp_path):
    source, entry = reviewed_source()
    assert collection_report([entry])['target'] == 100
    with pytest.raises(ValueError, match='exactly 100'):
        write_reviewed_collection([entry], [source], tmp_path/'default')
    result = write_reviewed_collection([entry], [source], tmp_path/'custom', expected_count=1)
    assert result['target'] == result['accepted_news_articles'] == 1
    before = (tmp_path/'custom/news_register.json').read_bytes()
    with pytest.raises(ValueError, match='empty'):
        write_reviewed_collection([entry], [source], tmp_path/'custom', expected_count=1)
    assert (tmp_path/'custom/news_register.json').read_bytes() == before


@pytest.mark.parametrize('count', [0, -1, True, 1.5])
def test_invalid_expanded_collection_counts_fail_without_output(tmp_path, count):
    with pytest.raises(ValueError, match='positive integer'):
        write_reviewed_collection([], [], tmp_path/'invalid', expected_count=count)
    assert not (tmp_path/'invalid').exists()


def reviewed_source(url='https://www.gmanetwork.com/news/topstories/nation/123456/flood/story/'):
    source = SourceCapture(source_id='article-1', url=url, publisher='GMA News',
        text=BODY, text_sha256=text_hash(BODY), capture_version='v1',
        published_at=datetime(2024, 11, 13, 18, tzinfo=timezone.utc),
        publication_basis='JSON-LD datePublished', article_group=url,
        reuse_terms='not verified', extraction_method='jsonld-articleBody-text-v2')
    entry = source_entry(source)
    entry.update(status='accepted', reviewer='offline reviewer', review_notes=['body/date/publisher reviewed'],
                 evidence=[{'start':0, 'end':len(BODY), 'sha256':text_hash(BODY)}])
    return source, entry


@pytest.mark.parametrize('value,expected', [
    ('2022-01-01','2022-01-01'),('2026-10-14','2026-10-14'),
    ('2024-11-13T18:00:00Z','2024-11-14'),('2026-10-14T16:00:00Z','2026-10-15'),
    ('2024-01-01T08:00:00','2024-01-01'),('2024-02-30',None),('yesterday',None),
    ('2024-02-29 junk',None),(None,None),
])
def test_publication_day_retains_unknown_zone_and_converts_known_zone(value, expected):
    result = publication_date(value)
    assert (result.isoformat() if result else None) == expected


@pytest.mark.parametrize('value,reason', [
    ('2021-12-31T12:00:00+08:00','publication_date_out_of_range'),
    ('2026-10-15T00:00:00+08:00','publication_date_out_of_range'),
    ('2022-01-01',None),('2026-10-14',None), (None,'publication_date_unconfirmed'),
])
def test_collection_date_filter(value, reason):
    source, _ = reviewed_source()
    source = source.model_copy(update={'published_at':None})
    assert source_entry(source, publication_value=value)['exclusion_reason'] == reason


def test_canonical_article_id_and_publisher_are_domain_bounded():
    a='http://www.gmanetwork.com/news/topstories/nation/123456/flood/story/?utm_source=x&fbclid=y'
    b='https://gmanetwork.com/news/balitambayan/balita/123456/renamed/story/amp'
    assert article_key(a) == article_key(b) == 'gma:123456'
    assert canonical_news_url(a).endswith('/story')
    assert canonical_news_url('https://www.philstar.com/story/amp/?output=1') == 'https://philstar.com/story'
    assert publisher_for('https://news.abs-cbn.com/report') == 'ABS-CBN News'
    assert publisher_for('https://abs-cbn.com.evil.example/report') is None
    with pytest.raises(ValueError):
        canonical_news_url('https://user:password@example.org/')


def test_percent_escape_case_aliases_preserve_real_path_distinctions():
    assert article_key('https://rmn.ph/%F0%9D%97%9C/') == article_key('https://rmn.ph/%f0%9d%97%9c/')
    assert article_key('https://rmn.ph/Report/') != article_key('https://rmn.ph/report/')
    assert article_key('https://rmn.ph/a%2Fb/') != article_key('https://rmn.ph/a/b/')


def test_publication_metadata_precedence_and_body_html_decoding(tmp_path):
    payload={'@graph':[{'@type':'NewsArticle','headline':'Flood report','datePublished':'2024-01-16T08:30:00+08:00',
                        'articleBody':'<p>Floods in Purok 9 &amp; 12.</p><p>Road closed.</p>'}]}
    html=('<html><meta property="article:published_time" content="2025-01-01">'
          '<link rel="canonical" href="https://gmanetwork.com/news/topstories/nation/123456/flood/story/">'
          '<script type="application/ld+json">'+json.dumps(payload)+'</script>'
          '<article>Polluted navigation <footer>related news</footer></article></html>')
    client=httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,text=html,headers={'content-type':'text/html'})))
    s=capture_source('https://gmanetwork.com/report','case','GMA News','english','event',client,tmp_path)
    assert s.text == 'Floods in Purok 9 & 12.\nRoad closed.'
    assert s.published_at.year == 2024
    assert s.extraction_method == 'jsonld-articleBody-html-v2'
    p=CaptureParser();p.feed(html)
    assert p.canonical_url.endswith('/story/')
    assert p.headline() == 'Flood report'


def test_meta_date_and_title_fallback():
    p=CaptureParser();p.feed('<title>Flood &amp; rain</title><meta property="article:published_time" content="2024-01-01">')
    assert p.publication_value() == ('2024-01-01','HTML meta article:published_time')
    assert p.headline() == 'Flood & rain'


def test_abs_static_shell_is_not_captured_as_article(tmp_path):
    html='<article><h1>Flood news</h1><footer>Newsletter</footer></article>'
    client=httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,text=html,headers={'content-type':'text/html'})))
    with pytest.raises(ValueError,match='no article/main'):
        capture_source('https://www.abs-cbn.com/news/report','abs','ABS-CBN News','unknown','event',client,tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_capture_failure_is_an_explicit_outcome_not_a_count(tmp_path, monkeypatch):
    import training.flood_ner.collection as module
    monkeypatch.setattr(module,'inventory_sources',lambda root:([],[]))
    def fail(*args,**kwargs):
        raise httpx.ConnectError('publisher unavailable')
    monkeypatch.setattr(module,'capture_source',fail)
    entries=collect_candidates(['https://gmanetwork.com/article'],tmp_path,tmp_path/'out')
    assert entries[0]['status'] == 'capture_failed'
    assert 'publisher unavailable' in entries[0]['exclusion_reason']
    assert collection_report(entries)['accepted_news_articles'] == 0
    assert json.loads((tmp_path/'out/candidates.json').read_text())['entries'] == entries


@pytest.mark.parametrize('changes,error', [
    ({'text_sha256':'0'*64},'missing/mismatched'),({'url':'bad'},'missing/mismatched'),
    ({'publication_date':'2025-01-01'},'publication date does not match'),
    ({'publication_basis':None},'publication date does not match'),
    ({'reviewer':None},'review and evidence required'),
    ({'evidence':[]},'review and evidence required'),
    ({'publisher':'Someone else'},'publisher identity mismatch'),
    ({'canonical_url':'bad'},'canonical article identity mismatch'),
    ({'source_category':'wikipedia_reference'},'not dated publisher news'),
    ({'admission_status':'training_admitted'},'research only'),
    ({'evidence':[{'start':-1,'end':100}]},'invalid body evidence'),
    ({'evidence':[{'start':False,'end':100}]},'invalid body evidence'),
    ({'evidence':[{'start':0,'end':100,'sha256':'0'*64}]},'body evidence hash mismatch'),
])
def test_review_rejects_unsubstantiated_records(changes,error):
    source,entry=reviewed_source();entry.update(changes)
    assert any(error in message for message in validate_reviewed([entry],{'v1':source}))


def test_versions_and_copied_stories_do_not_pad_collection():
    source,entry=reviewed_source()
    duplicate=deepcopy(entry)
    assert any('duplicate article/version' in e for e in validate_reviewed([entry,duplicate],{'v1':source}))
    other=source.model_copy(update={'source_id':'copy','capture_version':'v2','url':'https://gmanetwork.com/news/nation/999999/copy/story/'})
    copy=source_entry(other);copy.update(status='accepted',reviewer='reviewer',review_notes=['checked'],evidence=entry['evidence'])
    assert any('copied/near-identical' in e for e in validate_reviewed([entry,copy],{'v1':source,'v2':other}))
    assert same_story(BODY,BODY.upper())
    assert not same_story(BODY,'A distinct Cebu storm surge destroyed coastal homes during the night.')


def test_freeze_requires_all_100_before_writing(tmp_path):
    source,entry=reviewed_source()
    assert validate_reviewed([entry],{'v1':source}) == []
    with pytest.raises(ValueError,match='expected exactly 100'):
        write_reviewed_collection([entry],[source],tmp_path/'output')
    assert not (tmp_path/'output').exists()


def test_rendered_capture_preserves_header_and_immutable_body(tmp_path):
    snapshot=tmp_path/'input.json'
    snapshot.write_bytes(json_bytes({'url':'https://www.abs-cbn.com/news/flood', 'title':'Flood',
        'body_text':BODY,'body_html':'<p>'+BODY+'</p>',
        'headers':['Published November 14, 2024 02:00 AM PHT','Updated November 14, 2024 05:00 AM PHT'],
        'captured_at':'2026-10-14T02:00:00Z'}))
    source=import_browser_capture(snapshot,tmp_path/'captures','abs','english')
    assert source.text == BODY
    assert source.published_at.isoformat() == '2024-11-14T02:00:00+08:00'
    assert source.raw_sha256 == hashlib.sha256(snapshot.read_bytes()).hexdigest()
    assert source.admission_status == 'research_only'
    assert import_browser_capture(snapshot,tmp_path/'captures','abs','english') == source
    with pytest.raises(ValueError,match='identity conflict'):
        import_browser_capture(snapshot,tmp_path/'captures','another','english')
    payload=json.loads(snapshot.read_text());payload['headers']=['Updated November 14, 2024 05:00 AM PHT']
    snapshot.write_bytes(json_bytes(payload))
    with pytest.raises(ValueError,match='publication header not verified'):
        import_browser_capture(snapshot,tmp_path/'captures','abs','english')


def test_file_hash_and_publication_evidence_verification(tmp_path):
    source,entry=reviewed_source()
    (tmp_path/'body.txt').write_bytes(BODY.encode())
    raw=b'<meta property="article:published_time" content="2024-11-13T18:00:00+00:00">'
    (tmp_path/'raw.html').write_bytes(raw)
    entry.update(text_path='body.txt',raw_path='raw.html',raw_sha256=hashlib.sha256(raw).hexdigest(),
                 publication_evidence={'kind':'html_metadata','path':'raw.html'})
    assert verify_capture_files([entry],tmp_path) == []
    entry['publication_value']='2024-11-14'
    assert 'publication metadata mismatch' in verify_capture_files([entry],tmp_path)[0]
    entry['publication_value']='2024-11-13T18:00:00+00:00'
    (tmp_path/'body.txt').write_text('modified')
    assert 'frozen text hash mismatch' in verify_capture_files([entry],tmp_path)[0]
    entry['text_path']='../outside.txt'
    assert 'outside repository' in verify_capture_files([entry],tmp_path)[0]


def test_wikipedia_revision_license_and_support_only_boundary(tmp_path):
    def respond(request):
        if request.url.params.get('meta') == 'siteinfo':
            return httpx.Response(200,json={'query':{'rightsinfo':{'url':'https://creativecommons.org/licenses/by-sa/4.0/','text':'CC BY-SA 4.0'}}})
        assert request.url.params['rvstart'] == '2026-10-14T15:59:59Z'
        return httpx.Response(200,json={'query':{'pages':[{'title':'Tropical Storm Trami','revisions':[
            {'revid':42,'timestamp':'2026-09-01T00:00:00Z','user':'editor',
             'slots':{'main':{'content':'Reference context, with cited news links.'}}}]}]}})
    result=wikipedia_reference('Typhoon Trami (2024)','en',httpx.Client(transport=httpx.MockTransport(respond)),tmp_path)
    assert result['revision_id'] == 42
    assert result['permanent_url'].endswith('title=Tropical_Storm_Trami&oldid=42')
    assert result['news_target_count'] == 0
    assert result['training_admission'] == 'excluded_support_only'
    assert result['license']['text'] == 'CC BY-SA 4.0'
    assert text_hash((tmp_path/'en-42.wiki.txt').read_text()) == result['text_sha256']
    assert 'contributors' in result['attribution']
    metadata=(tmp_path/'en-42.json').read_bytes()
    repeated=wikipedia_reference('Typhoon Trami (2024)','en',httpx.Client(transport=httpx.MockTransport(respond)),tmp_path)
    assert repeated == result
    assert (tmp_path/'en-42.json').read_bytes() == metadata
    other=wikipedia_reference('Typhoon Trami (2024)','tl',httpx.Client(transport=httpx.MockTransport(respond)),tmp_path)
    assert other['language'] == 'tl'
    assert (tmp_path/'tl-42.json').exists() and (tmp_path/'en-42.json').read_bytes() == metadata
    (tmp_path/'en-42.wiki.txt').write_text('corrupt')
    with pytest.raises(ValueError,match='revision/content mismatch'):
        wikipedia_reference('Typhoon Trami (2024)','en',httpx.Client(transport=httpx.MockTransport(respond)),tmp_path)


@pytest.mark.parametrize('changes,error', [
    ({'canonical_url':'https://gmanetwork.com/news/nation/999999/other/story/','article_key':'gma:999999'},'canonical article identity mismatch'),
    ({'captured_at':'2030-01-01T00:00:00Z'},'captured_at does not match'),
    ({'published_at':'2024-11-14T18:00:00Z'},'published_at does not match'),
    ({'reuse_status':'allowed'},'reuse status does not match'),
    ({'capture_version':{}},'missing/mismatched'),
    ({'article_key':{}},'canonical article identity mismatch'),
    ({'evidence':[None]},'invalid body evidence'),
    ({'evidence':{'start':0,'end':1}},'review and evidence required'),
    ({'review_notes':[None]},'review and evidence required'),
    ({'reviewer':['reviewer']},'review and evidence required'),
])
def test_audit_provenance_and_malformed_review_rejections(changes,error):
    source,entry=reviewed_source();entry.update(changes)
    assert any(error in e for e in validate_reviewed([entry],{'v1':source}))


@pytest.mark.parametrize('payload',[{},[None],[42]])
def test_malformed_manifest_has_actionable_cli_error(tmp_path,capsys,payload):
    path=tmp_path/'bad.json';path.write_bytes(json_bytes(payload))
    assert main(['verify-news',str(path),'--output',str(tmp_path/'output')]) == 1
    assert 'verify-news failed:' in capsys.readouterr().err
    assert not (tmp_path/'output').exists()


def test_unknown_retrieval_timestamp_cannot_be_invented():
    source,entry=reviewed_source()
    assert source.captured_at is None
    entry['captured_at']='2026-10-14T02:00:00Z'
    assert any('captured_at does not match' in e for e in validate_reviewed([entry],{'v1':source}))


def test_evidence_cannot_borrow_another_capture_with_matching_date(tmp_path):
    source,entry=reviewed_source()
    (tmp_path/'body.txt').write_bytes(BODY.encode())
    raw=b'<meta property="article:published_time" content="2024-11-13T18:00:00+00:00">'
    (tmp_path/'raw.html').write_bytes(raw);(tmp_path/'other.html').write_bytes(raw)
    entry.update(text_path='body.txt',raw_path='raw.html',raw_sha256=hashlib.sha256(raw).hexdigest(),
                 publication_evidence={'kind':'html_metadata','path':'other.html'})
    assert any('not bound to this raw capture' in e for e in verify_capture_files([entry],tmp_path))


def test_crlf_frozen_body_survives_browser_import_and_file_verification(tmp_path):
    text=BODY.replace('. ','.\r\n')
    snapshot=tmp_path/'snapshot.json'
    snapshot.write_bytes(json_bytes({'url':'https://abs-cbn.com/news/flood','title':'Flood','body_text':text,
        'body_html':'<p>rendered text supplied separately</p>',
        'headers':['Published November 14, 2024 02:00 AM PHT'],'captured_at':'2026-10-14T02:00:00Z'}))
    source=import_browser_capture(snapshot,tmp_path/'captures','abs','english')
    assert import_browser_capture(snapshot,tmp_path/'captures','abs','english') == source
    entry=source_entry(source)
    entry.update(status='accepted',text_path=f'captures/{source.capture_version}.txt',
                 raw_path=f'captures/{source.capture_version}.dom-snapshot',
                 publication_evidence={'kind':'rendered_header','path':f'captures/{source.capture_version}.dom-snapshot'})
    assert verify_capture_files([entry],tmp_path) == []
    assert (tmp_path/entry['text_path']).read_bytes() == text.encode()


def test_legacy_body_header_must_support_its_publication_day(tmp_path):
    text='September 9, 2026 - 5:03pm\n'+BODY
    path=tmp_path/'body.txt';path.write_bytes(text.encode())
    header=text.splitlines()[0]
    entry={'source_id':'legacy','status':'accepted','text_path':'body.txt','text_sha256':text_hash(text),
           'raw_sha256':None,'publication_value':'2026-09-08',
           'publication_evidence':{'kind':'preserved_body_header','path':'body.txt','start':0,'end':len(header),'sha256':text_hash(header)}}
    assert any('does not corroborate publication day' in e for e in verify_capture_files([entry],tmp_path))
    entry['publication_value']='2026-09-09'
    assert verify_capture_files([entry],tmp_path) == []


def test_browser_capture_does_not_return_modified_metadata(tmp_path):
    snapshot=tmp_path/'snapshot.json'
    snapshot.write_bytes(json_bytes({'url':'https://abs-cbn.com/news/flood','title':'Flood','body_text':BODY,
        'headers':['Published November 14, 2024 02:00 AM PHT'],'captured_at':'2026-10-14T02:00:00Z'}))
    source=import_browser_capture(snapshot,tmp_path/'captures','abs','english')
    path=tmp_path/'captures'/f'{source.capture_version}.json'
    data=json.loads(path.read_text());data['published_at']='2024-11-15T02:00:00+08:00'
    path.write_bytes(json_bytes(data))
    with pytest.raises(ValueError,match='metadata mismatch'):
        import_browser_capture(snapshot,tmp_path/'captures','abs','english')
