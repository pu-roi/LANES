"""Offline reviewed sample selection, exact stratification and admission boundaries."""
from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from training.flood_ner.annotation.schema import AnnotationRecord, SourceCapture, text_hash
from training.flood_ner.cohort import GroupReview, build_cohort
from training.flood_ner.export import export_corpus

SMALL = {s: {'english': 1, 'taglish': 1} for s in ('train', 'dev', 'test')}


def sample(number, language='english', publisher=0, group=None):
    domain, name = [('gmanetwork.com','GMA News'),('pna.gov.ph','Philippine News Agency'),('rmn.ph','RMN Networks')][publisher]
    text = f'Flood report {number} at Street {number}.'
    source = SourceCapture(source_id=f's{number}',url=f'https://{domain}/article/{number}',publisher=name,
        text=text,text_sha256=text_hash(text),capture_version=f'v{number}',language='unknown',
        article_group=f'original-a{number}',event_group='review-needed:original',reuse_terms='unknown',
        published_at=datetime(2024,1,2,tzinfo=timezone.utc),extraction_method='test-fixture')
    record = AnnotationRecord(record_id=f'r{number:03}',source=source,passage_start=0,passage_end=len(text),
        text=text,text_sha256=text_hash(text),passage_language=language,annotation_profile='location-only-v1',
        annotation_revision='test-v1',teacher='fixture teacher',reviewer='fixture reviewer',review_status='accepted',complete=True)
    review = GroupReview(source_id=source.source_id,capture_version=source.capture_version,
        text_sha256=source.text_sha256,publication_date='2024-01-02',article_group=f'a{number}',
        event_group=group or f'e{number}',syndication_group=f'unsyndicated-{number}',reviewer='fixture reviewer',
        review_revision='groups-v1',notes=['Explicit test group decision'],
        evidence=[dict(start=0,end=len(text),sha256=text_hash(text),reason='fixture group evidence')])
    return record,review,source


def bundle():
    rows=[sample(i, 'english' if i%2==0 else 'taglish',i//2) for i in range(6)]
    return ([r[0] for r in rows],[r[1] for r in rows],[r[2] for r in rows])


def output(tmp_path, name='v1'):
    return tmp_path/'backend/training/flood_ner/artifacts'/name


def test_exact_deterministic_round_trip_source_overlay_and_pilot_pin(tmp_path):
    records,reviews,sources=bundle()
    before=deepcopy([r.model_dump() for r in records])
    first=build_cohort(records,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=2,pilot_ids={'r000'})
    second=build_cohort(list(reversed(records)),list(reversed(reviews)),sources,tmp_path,output(tmp_path,'v2'),targets=SMALL,publisher_cap=2,pilot_ids={'r000'})
    assert first==second and first['counts']==SMALL and first['total']==6
    for p in output(tmp_path).iterdir(): assert p.read_bytes()==(output(tmp_path,'v2')/p.name).read_bytes()
    register=json.loads((output(tmp_path)/'selection_register.json').read_text())
    assert next(r for r in register if r['record_id']=='r000')['split']=='train'
    assert [r.model_dump() for r in records]==before
    assert first['training_admitted']==0 and 'source_not_training_admitted' in first['export_holds']
    from training.flood_ner.sources import read_jsonl
    selected=read_jsonl(output(tmp_path)/'grouped_annotations.jsonl',AnnotationRecord)
    with pytest.raises(ValueError,match='research-only'):
        export_corpus(selected,output(tmp_path,'forbidden-export'),annotation_profile='location-only-v1')
    assert not output(tmp_path,'forbidden-export').exists()


def test_connected_event_group_cannot_be_split_to_hit_exact_counts(tmp_path):
    records,reviews,sources=bundle()
    for review in reviews: review.event_group='one-shared-event'
    with pytest.raises(ValueError,match='infeasible'):
        build_cohort(records,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=2)
    assert not output(tmp_path).exists()


@pytest.mark.parametrize('field,value', [('text_sha256','0'*64),('source_id','wrong'),('event_group','provisional:x'),
                                      ('publication_date','2021-12-31')])
def test_forged_or_unreviewed_group_evidence_rejected(tmp_path,field,value):
    records,reviews,sources=bundle()
    setattr(reviews[0],field,value)
    with pytest.raises(ValueError): build_cohort(records,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=2)


def test_unknown_article_language_does_not_override_reviewed_passage_language(tmp_path):
    records,reviews,sources=bundle()
    assert all(s.language=='unknown' for s in sources)
    assert build_cohort(records,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=2)['total']==6


def test_corrupt_annotation_and_external_output_fail_without_writes(tmp_path):
    records,reviews,sources=bundle()
    with pytest.raises(ValueError,match='ignored'):
        build_cohort(records,reviews,sources,tmp_path,tmp_path/'outside',targets=SMALL)
    records[0].text='corrupt'
    with pytest.raises(ValueError,match='offsets|hash'):
        build_cohort(records,reviews,sources,tmp_path,output(tmp_path),targets=SMALL)


def test_duplicates_unresolved_and_overlapping_passages_do_not_pad_count(tmp_path):
    records,reviews,sources=bundle()
    unresolved=records[0].model_copy(update={'record_id':'unresolved','complete':False,'review_status':'unresolved'})
    duplicate=records[1].model_copy(update={'record_id':'duplicate'})
    result=build_cohort(records+[unresolved,duplicate],reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=2,
                        pilot_ids={'r001'})
    exclusions=json.loads((output(tmp_path)/'exclusion_register.json').read_text())
    assert result['total']==6
    assert any('incomplete_or_unresolved' in e['reason'] for e in exclusions)
    assert any('overlapping_article_passage' in e['reason'] for e in exclusions)


def test_missing_pilot_or_publisher_balance_is_not_silently_relaxed(tmp_path):
    records,reviews,sources=bundle()
    with pytest.raises(ValueError,match='pilot'):
        build_cohort(records,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,pilot_ids={'missing'})
    with pytest.raises(ValueError,match='infeasible'):
        build_cohort(records,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=1)


def test_frozen_output_not_overwritten(tmp_path):
    records,reviews,sources=bundle()
    build_cohort(records,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=2)
    with pytest.raises(ValueError,match='empty'):
        build_cohort(records,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=2)


def test_corrupt_raw_provenance_register_prevents_cli_cohort(tmp_path,monkeypatch,capsys):
    from training.flood_ner import cli
    records,reviews,sources=bundle()
    monkeypatch.setattr(cli,'inventory_sources',lambda root:(sources,[]))
    register=tmp_path/'register.json'
    register.write_text(json.dumps([{'status':'accepted','source_id':'forged','capture_version':'missing'}]))
    result=cli.main(['build-cohort',str(tmp_path/'unused.jsonl'),'--group-reviews',str(tmp_path/'unused-reviews.json'),
        '--news-register',str(register),'--pilot-records',str(tmp_path/'unused-pilot.json'),'--output',str(output(tmp_path))])
    assert result==1 and 'missing/mismatched captured source' in capsys.readouterr().err
    assert not output(tmp_path).exists()


@pytest.mark.parametrize('field', ['event_group','reviewer','review_revision'])
def test_blank_group_reviews_cannot_claim_review_completion(field):
    review=sample(0)[1].model_dump()
    review[field]='  '
    with pytest.raises(ValueError,match='not be blank'): GroupReview.model_validate(review)
