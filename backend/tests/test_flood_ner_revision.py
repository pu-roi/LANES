"""Hard collection quotas and explicit historical/tokenizer identities."""
from copy import deepcopy
from datetime import date, datetime, timezone
import json

import pytest

from test_flood_ner_cohort import bundle, SMALL, output
from training.flood_ner.annotation.schema import Entity, text_hash
from training.flood_ner.budget import collection_budget
from training.flood_ner.cohort import _assign, _groups, build_cohort
from training.flood_ner.collection import source_entry, validate_reviewed, verify_capture_files
from training.flood_ner.sources import json_bytes
from training.flood_ner.export import TOKENIZER_NAME, CANDIDATE_TOKENIZER_NAME, corpus_tokenizer, export_corpus
from training.flood_ner.policy import CoveragePolicy, Support, policy_report
from training.flood_ner.qualification import load_frozen_cohort
from training.flood_ner.window import LEGACY_WINDOW, REVISION_WINDOW, PublicationWindow


def tiny_policy():
    one = Support(spans=1, passages=1, articles=1)
    return CoveragePolicy(minimum_publishers=3, publisher_min_per_language=1, publisher_max_total=2,
                          publisher_max_per_language=1, article_max=1, group_max=1,
                          groups_min_per_partition=1, train=one.model_copy(), holdout=one.model_copy(),
                          road_train=one.model_copy(), road_holdout=one.model_copy())


def labeled_bundle():
    records, reviews, sources = bundle()
    for r, review, source in zip(records, reviews, sources):
        names = [('ROAD','Alpha Road'),('LANDMARK','Beta School'),('LOCAL_AREA','Purok 03-A'),
                 ('BARANGAY','Barangay Delta'),('CITY','Echo City'),('PROVINCE','Foxtrot')]
        text = f'Report {r.record_id}: ' + ', '.join(name for _, name in names) + '.'
        source.text = text; source.text_sha256 = text_hash(text)
        source.event_group = 'original-event-'+r.record_id
        r.text = text; r.text_sha256 = text_hash(text); r.passage_end = len(text)
        r.entities = [Entity(id=f'e{i}', label=label, start=text.index(name), end=text.index(name)+len(name), text=name)
                      for i,(label,name) in enumerate(names)]
        review.text_sha256 = source.text_sha256
        review.evidence[0].end = len(text); review.evidence[0].sha256 = source.text_sha256
    return records,reviews,sources


@pytest.mark.parametrize('value,inside', [('2016-12-31',False),('2017-01-01',True),('2021-12-31',True),
                                      ('2026-10-14',True),('2026-10-15',False)])
def test_historical_inclusive_boundaries(value,inside):
    assert REVISION_WINDOW.contains(date.fromisoformat(value)) is inside
    assert LEGACY_WINDOW.as_list() == ['2022-01-01','2026-10-14']


@pytest.mark.parametrize('values', [['2026-10-14','2017-01-01'], ['unknown','2026-10-14'], ['2017-01-01'], None])
def test_invalid_windows_fail(values):
    with pytest.raises(ValueError): PublicationWindow.parse(values)


def test_source_window_explicit_without_changing_legacy():
    source = bundle()[2][0]
    source.published_at = datetime(2017,1,1,tzinfo=timezone.utc)
    source.text = 'A complete article containing enough evidence. '*12
    source.text_sha256 = text_hash(source.text)
    assert source_entry(source)['exclusion_reason'] == 'publication_date_out_of_range'
    assert source_entry(source,window=REVISION_WINDOW)['status'] == 'review_pending'
    source.published_at = None
    row = source_entry(source,publication_value='2017-01-01',window=REVISION_WINDOW)
    assert row['published_at'] is None and row['publication_date'] == '2017-01-01'


def test_policy_defaults_are_user_contract():
    policy = CoveragePolicy()
    assert (policy.publisher_min_per_language,policy.publisher_max_total,policy.publisher_max_per_language)==(25,160,100)
    assert (policy.article_max,policy.group_max,policy.groups_min_per_partition)==(8,80,5)
    assert policy.support('train','ROAD').model_dump()=={'spans':60,'passages':30,'articles':10}
    assert policy.support('dev','ROAD').model_dump()=={'spans':20,'passages':10,'articles':5}
    assert policy.support('train','LOCAL_AREA').model_dump()=={'spans':20,'passages':10,'articles':5}
    assert policy.support('test','CITY').model_dump()=={'spans':10,'passages':5,'articles':3}


def test_policy_selection_deterministic_and_saved_v3(tmp_path):
    records,reviews,sources = labeled_bundle()
    kwargs=dict(targets=SMALL,policy=tiny_policy(),window=REVISION_WINDOW,tokenizer=CANDIDATE_TOKENIZER_NAME,pilot_ids={'r000'})
    before = deepcopy([r.model_dump() for r in records])
    first=build_cohort(records,reviews,sources,tmp_path,output(tmp_path),**kwargs)
    second=build_cohort(records[::-1],reviews[::-1],sources,tmp_path,output(tmp_path,'replay'),**kwargs)
    assert first == second and first['policy_checks']['passed'] and first['counts']==SMALL
    assert [r.model_dump() for r in records] == before
    selected,nlp,manifest=load_frozen_cohort(output(tmp_path))
    assert next(r for r in selected if r.record_id=='r000').split=='train'
    assert manifest['tokenizer']==CANDIDATE_TOKENIZER_NAME and manifest['publication_window']==REVISION_WINDOW.as_list()
    assert (output(tmp_path)/'tokenizer.bin').read_bytes()==corpus_tokenizer(CANDIDATE_TOKENIZER_NAME).tokenizer.to_bytes()
    for path in output(tmp_path).iterdir(): assert path.read_bytes()==(output(tmp_path,'replay')/path.name).read_bytes()
    with pytest.raises(ValueError,match='research-only'):
        export_corpus(selected,output(tmp_path,'export'),annotation_profile='location-only-v1',tokenizer=CANDIDATE_TOKENIZER_NAME)


@pytest.mark.parametrize('field,value', [('publisher_min_per_language',2),('publisher_max_total',1),
                                      ('minimum_publishers',4),('groups_min_per_partition',3)])
def test_solver_enforces_publisher_and_group_quotas(field,value):
    records,_,_=labeled_bundle(); policy=tiny_policy(); setattr(policy,field,value)
    with pytest.raises(ValueError,match='infeasible'):
        _assign(records,_groups(records),set(),SMALL,200,3,policy)


@pytest.mark.parametrize('metric', ['spans','passages','articles'])
def test_solver_enforces_each_label_support_metric(metric):
    records,_,_=labeled_bundle(); policy=tiny_policy()
    setattr(policy.train,metric,2)
    with pytest.raises(ValueError,match='infeasible'):
        _assign(records,_groups(records),set(),SMALL,200,3,policy)


def test_group_cap_and_conservative_dependencies_not_relaxed():
    records,_,_=labeled_bundle()
    records[1].source.event_group=records[0].source.event_group='uncertain-conservative-dependency'
    with pytest.raises(ValueError,match='infeasible'):
        _assign(records,_groups(records),set(),SMALL,200,3,tiny_policy())


def test_direct_solver_control_and_article_cap():
    records,_,_=labeled_bundle();policy=tiny_policy()
    assert len(_assign(records,_groups(records),set(),SMALL,200,3,policy))==6
    records[1].source.url=records[0].source.url
    policy.group_max=2
    with pytest.raises(ValueError,match='infeasible'):
        _assign(records,_groups(records),set(),SMALL,200,3,policy)
    policy.article_max=2
    assert len(_assign(records,_groups(records),set(),SMALL,200,3,policy))==6


def test_publisher_per_language_cap_and_road_override():
    records,_,_=labeled_bundle();policy=tiny_policy()
    policy.road_train.spans=2
    with pytest.raises(ValueError,match='infeasible'):
        _assign(records,_groups(records),set(),SMALL,200,3,policy)
    policy=tiny_policy();policy.publisher_max_total=4;policy.group_max=2
    extra=[]
    for r in records:
        s=r.source.model_copy(update={'url':r.source.url+'/extra','article_group':r.source.article_group+'-extra','event_group':r.source.event_group+'-extra'})
        extra.append(r.model_copy(update={'record_id':r.record_id+'-extra','source':s}))
    targets={s:{'english':2,'taglish':2} for s in SMALL}
    with pytest.raises(ValueError,match='infeasible'):
        _assign(records+extra,_groups(records+extra),set(),targets,200,3,policy)
    policy.publisher_max_per_language=2
    assert len(_assign(records+extra,_groups(records+extra),set(),targets,200,3,policy))==12


def test_distinct_articles_cannot_be_faked_by_many_spans():
    records,_,_=labeled_bundle()
    for r in records: r.split='train'
    for r in records[::2]: r.source.url=records[0].source.url
    policy=tiny_policy();policy.train.articles=2
    report=policy_report(records,_groups(records),policy)
    assert any(f.get('metric')=='articles' and f.get('language')=='english' for f in report['failures'])


def test_infeasibility_delivers_pool_without_partition_claim(tmp_path):
    records,reviews,sources=labeled_bundle()
    result=build_cohort(records,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,policy=CoveragePolicy(),
                        tokenizer=CANDIDATE_TOKENIZER_NAME,window=REVISION_WINDOW,report_infeasible=True)
    assert result['revision_complete'] is False and result['selected_samples']==0
    assert (output(tmp_path)/'reviewed_pool.jsonl').is_file()
    assert not (output(tmp_path)/'partition_manifest.json').exists()
    assert result['coverage']['failures']


def test_budget_counts_canonical_articles_not_tracking_versions():
    baseline=['https://rmn.ph/old/']
    urls=['https://rmn.ph/new/?utm_source=x','https://rmn.ph/new/','https://rmn.ph/old/']
    result=collection_budget(urls,baseline,['https://rmn.ph/new/'],candidate_limit=1,article_limit=1)
    assert result['additional_candidate_urls']==result['additional_admitted_articles']==1
    with pytest.raises(ValueError,match='budget exceeded'):
        collection_budget(urls+['https://rmn.ph/extra/'],baseline,[],candidate_limit=1)
    with pytest.raises(ValueError,match='bind'):
        collection_budget(urls,baseline,['https://rmn.ph/unreviewed/'])


@pytest.mark.parametrize('text,name', [('CITY-Alpha Road','CITY'),('-Bonifacio Street','Bonifacio Street'),
                                     ('Purok 2—baha','Purok 2'),('Block 006-A.','Block 006-A'),
                                     ('Phase IV, Lot 03-B','Phase IV'),('Cebu.—FRJ GMA News','Cebu'),
                                     ('Kalaw/ Maria Orosa','Kalaw'),('Mag-11th Avenue;','11th Avenue'),
                                     ('EDSA/A. De Jesus','EDSA')])
def test_v3_address_boundaries_preserve_unicode_text(text,name):
    doc=corpus_tokenizer(CANDIDATE_TOKENIZER_NAME).make_doc(text)
    start=text.index(name)
    assert doc.text==text and doc.char_span(start,start+len(name),alignment_mode='strict') is not None
    assert TOKENIZER_NAME=='lanes.xx.address-v2'


def test_date_only_capture_is_bound_without_invented_instant(tmp_path):
    import hashlib
    records,reviews,sources=labeled_bundle()
    record,review,source=records[0],reviews[0],sources[0]
    source.published_at=None;source.publication_basis='HTML meta article:published_time'
    raw=b'<meta property="article:published_time" content="2017-01-01"><article>Complete body</article>'
    source.raw_sha256=hashlib.sha256(raw).hexdigest()
    (tmp_path/'raw.html').write_bytes(raw)
    (tmp_path/'text.txt').write_text(source.text,encoding='utf-8')
    entry=source_entry(source,publication_value='2017-01-01',window=REVISION_WINDOW)
    entry.update(status='accepted',reviewer='fixture review',review_notes=['Exact frozen body reviewed'],
                 evidence=[dict(start=0,end=len(source.text),sha256=source.text_sha256)],text_path='text.txt',raw_path='raw.html',
                 publication_evidence={'kind':'html_metadata','path':'raw.html'})
    assert validate_reviewed([entry],{source.capture_version:source},window=REVISION_WINDOW)==[]
    assert verify_capture_files([entry],tmp_path)==[]
    assert validate_reviewed([entry],{source.capture_version:source})
    review.publication_date='2017-01-01'
    result=build_cohort([record],[review],[source],tmp_path,output(tmp_path),window=REVISION_WINDOW,
                        news_entries=[entry],report_infeasible=True)
    assert result['reviewed_pool']==1 and source.published_at is None
    with pytest.raises(ValueError,match='corroborated'):
        build_cohort([record],[review],[source],tmp_path,output(tmp_path,'no-date-evidence'),window=REVISION_WINDOW)
    # Conflicting metadata cannot be accepted merely because one value is first.
    raw=b'<meta property="article:published_time" content="2017-01-01"><meta name="pubdate" content="2017-01-02">'
    (tmp_path/'raw.html').write_bytes(raw); entry['raw_sha256']=hashlib.sha256(raw).hexdigest()
    assert any('conflicting' in e for e in verify_capture_files([entry],tmp_path))


def test_bad_provenance_does_not_become_an_infeasibility_pool(tmp_path):
    records,reviews,sources=labeled_bundle();reviews[0].text_sha256='0'*64
    with pytest.raises(ValueError,match='bind uniquely'):
        build_cohort(records,reviews,sources,tmp_path,output(tmp_path),policy=CoveragePolicy(),report_infeasible=True)
    assert not output(tmp_path).exists()


def test_malformed_publisher_script_repair_preserves_original_capture(tmp_path):
    import httpx,hashlib
    from training.flood_ner.sources import capture_source,reextract_capture
    body='<p>Original beginning.</p><script async src="widgets.js"><\\script><p>After the embed, Sitio Doña Juana was flooded.</p>'
    html='<script type="application/ld+json">'+json.dumps({'@type':'NewsArticle','headline':'Flood',
           'datePublished':'2018-07-16','articleBody':body})+'</script>'
    with httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,text=html,headers={'content-type':'text/html'}))) as client:
        old=capture_source('https://gmanetwork.com/news/example/123456/flood','test','GMA News','unknown','review-needed:test',client,tmp_path)
        assert 'Sitio Doña Juana' not in old.text
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.iterdir()}
        new=reextract_capture(tmp_path/(old.capture_version+'.json'),tmp_path)
        direct=capture_source(old.url,'test','GMA News','unknown','review-needed:test',client,tmp_path,repair_embedded_markup=True)
    assert new.text==direct.text=='Original beginning.\nAfter the embed, Sitio Doña Juana was flooded.'
    assert new.raw_sha256==old.raw_sha256 and new.captured_at==old.captured_at
    assert new.capture_version!=old.capture_version and new.published_at is None
    assert all(hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()==sha for name,sha in before.items())
    assert reextract_capture(tmp_path/(old.capture_version+'.json'),tmp_path)==new
    # A newly expanded body cannot inherit an earlier version's training admission.
    qualified=old.model_copy(update={'reuse_status':'allowed','admission_status':'training_admitted',
                                     'reuse_terms':'explicit test-fixture grant'})
    original=tmp_path/'qualified.json';original.write_bytes(json_bytes(qualified.model_dump(mode='json')))
    original.with_suffix('.html').write_bytes((tmp_path/(old.capture_version+'.html')).read_bytes())
    original.with_suffix('.txt').write_bytes(old.text.encode('utf-8'))
    expanded=reextract_capture(original,tmp_path/'expanded')
    assert expanded.admission_status=='research_only' and qualified.admission_status=='training_admitted'


def test_rendered_date_only_and_conflicting_headers(tmp_path):
    from training.flood_ner.collection import rendered_publication,import_browser_capture
    header='June 3, 2026 - 12:00am'
    assert rendered_publication([header],'Philstar')==(header,'2026-06-03')
    with pytest.raises(ValueError,match='conflicting'):
        rendered_publication([header,'June 4, 2026 - 12:00am'],'Philstar')
    with pytest.raises(ValueError,match='conflicting'):
        rendered_publication(['Published June 3, 2026 01:00 AM PHT','Published June 3, 2026 02:00 AM PHT'],'ABS-CBN News')
    snapshot={'url':'https://philstar.com/article/2026/06/03/example','title':'Report',
              'body_text':'Floodwater entered the road, and residents moved to safety. '*10,
              'headers':[header],'captured_at':'2026-10-14T12:00:00Z'}
    path=tmp_path/'snapshot.json';path.write_bytes(json_bytes(snapshot))
    source=import_browser_capture(path,tmp_path/'capture','fixture')
    assert source.published_at is None and source.publication_basis==header


def test_cli_budget_refuses_301_before_capture(tmp_path,capsys):
    from training.flood_ner.cli import main
    urls=tmp_path/'urls.json';ledger=tmp_path/'ledger.json';baseline=tmp_path/'baseline.json'
    urls.write_bytes(json_bytes([f'https://rmn.ph/article-{i}' for i in range(301)]))
    ledger.write_bytes(json_bytes([]));baseline.write_bytes(json_bytes([]))
    assert main(['collect-news',str(urls),'--candidate-ledger',str(ledger),'--baseline-inventory',str(baseline),
                 '--output',str(tmp_path/'no-write')])==1
    assert 'budget exceeded' in capsys.readouterr().err and not (tmp_path/'no-write').exists()
    assert json.loads(ledger.read_text())==[]


def test_cli_explicit_window_and_tokenizer_validation(tmp_path,capsys):
    from training.flood_ner.cli import main
    from training.flood_ner.sources import write_jsonl
    records,_,sources=labeled_bundle()
    sources[0].published_at=datetime(2017,1,1,tzinfo=timezone.utc)
    path=tmp_path/'records.jsonl';write_jsonl(path,records)
    assert main(['validate',str(path),'--publication-start','2017-01-01','--tokenizer',CANDIDATE_TOKENIZER_NAME])==0
    assert json.loads(capsys.readouterr().out)['valid']
    assert main(['validate',str(path),'--publication-start','2022-01-01'])==1
    assert not json.loads(capsys.readouterr().out)['valid']
