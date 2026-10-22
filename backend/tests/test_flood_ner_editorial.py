from datetime import datetime, timezone
import json

import pytest
from pydantic import ValidationError

from training.flood_ner.annotation.schema import AnnotationRecord, SourceCapture, text_hash
from training.flood_ner.cli import main
from training.flood_ner.editorial import EditorialReview, build_editorial_queue, validate_review
from training.flood_ner.preparation import propose_passage


def packet(newline='\n'):
    text = newline.join(['Published metadata', 'Malabon City',
                         'Sitio 6 is flooded as of 8 a.m.', 'ADVERTISEMENT',
                         'Water later receded. Purok 12 remains flooded.'])
    source = SourceCapture(source_id='editorial-fixture', url='https://gmanetwork.com/news/topstories/metro/123456/report/story/',
        publisher='GMA News', text=text, text_sha256=text_hash(text), capture_version='editorial-version',
        article_group='editorial-article', origin='constructed_fixture', raw_sha256='a'*64,
        captured_at=datetime(2026,10,14,tzinfo=timezone.utc), reuse_terms='Test fixture only',
        extraction_method='constructed fixture')
    start=text.index('Malabon');ad=text.index('ADVERTISEMENT');ad_end=ad+len('ADVERTISEMENT')
    candidate=propose_passage({'article_key':'gma:123456','language':'english',
        'evidence':[{'role':'body_review_anchor','start':start,'end':ad,'sha256':text_hash(text[start:ad])}]},source)
    def span(a,b,**extras):
        return {'start':a,'end':b,'sha256':text_hash(text[a:b]),'reason':'Reviewed fixture range',**extras}
    review=EditorialReview(candidate_id=candidate.candidate_id,source_id=source.source_id,
        capture_version=source.capture_version,source_text_sha256=source.text_sha256,
        reviewer='Test AI reviewer',review_kind='ai_assisted',reviewed_at=datetime(2026,10,14,tzinfo=timezone.utc),
        review_revision='test-v1',notes=['No human or training qualification'],
        selections=[span(start,ad-len(newline),language='english',language_reason='English syntax'),
                    span(ad_end+len(newline),len(text),language='english',language_reason='English syntax')],
        exclusions=[span(0,start,kind='publisher_metadata'),span(ad,ad_end,kind='publisher_interface')])
    return candidate,review,source


@pytest.mark.parametrize('newline',['\n','\r\n'])
def test_editorial_slices_preserve_raw_text_and_do_not_join_context(tmp_path,newline):
    candidate,review,source=packet(newline)
    report=build_editorial_queue([candidate],[review],[source],tmp_path,
        tmp_path/'backend/training/flood_ner/artifacts/out')
    rows=[json.loads(line) for line in (tmp_path/'backend/training/flood_ner/artifacts/out/context_blocks.jsonl').read_text().splitlines()]
    assert len(rows)==2 and report['source_articles']==1
    for row in rows:
        assert row['text']==source.text[row['passage_start']:row['passage_end']]
        assert row['text_sha256']==text_hash(row['text']) and 'ADVERTISEMENT' not in row['text']
        assert row['context_source_sha256']==source.text_sha256 and row['sibling_block_ids']
        assert row['admission_status']=='research_only'
        assert {'cross_block_context_review_pending','research_team_manual_review_pending',
                'reuse_assessment_pending','event_syndication_review_pending','annotation_not_started'} <= set(row['hold_reasons'])
        with pytest.raises(ValidationError):
            AnnotationRecord.model_validate_json(json.dumps(row))
    assert report['training_admitted']==report['annotated_passages']==report['assigned_splits']==0
    assert EditorialReview.model_validate_json(review.model_dump_json())==review


@pytest.mark.parametrize('field,value',[
    ('source_id','forged'),('capture_version','forged'),('source_text_sha256','0'*64),
    ('candidate_id','candidate-'+'0'*20)])
def test_editorial_rejects_wrong_original_identity(field,value):
    candidate,review,_=packet()
    data=review.model_dump();data[field]=value
    with pytest.raises(ValueError,match='identity'):
        validate_review(candidate,EditorialReview.model_validate(data))


@pytest.mark.parametrize('problem',['overlap','unaccounted','bad_hash','out_of_bounds','whitespace'])
def test_editorial_rejects_lost_or_corrupt_source_ranges(problem):
    candidate,review,_=packet()
    data=review.model_dump()
    if problem=='overlap':
        data['exclusions'].append(data['exclusions'][0])
    elif problem=='unaccounted':
        data['exclusions'].pop(0)
    elif problem=='bad_hash':
        data['selections'][0]['sha256']='0'*64
    elif problem=='out_of_bounds':
        data['selections'][0]['end']=100000
    else:
        a=candidate.source.text.index('\n')
        data['selections'][0].update(start=a,end=a+1,sha256=text_hash('\n'))
    with pytest.raises(ValueError):
        validate_review(candidate,EditorialReview.model_validate(data))


def test_editorial_does_not_force_regional_or_tagalog_text_into_paper_scope(tmp_path):
    candidate,review,source=packet();data=review.model_dump()
    data['selections'][0]['language']='unknown';data['selections'][1]['language']='tagalog'
    report=build_editorial_queue([candidate],[EditorialReview.model_validate(data)],[source],tmp_path,
        tmp_path/'backend/training/flood_ner/artifacts/out')
    assert report['paper_language_compatible_blocks']==0
    assert report['hold_reasons']['unsupported_or_unresolved_language_review_pending']==1
    assert report['hold_reasons']['outside_paper_english_taglish_scope']==1


def test_editorial_rejects_duplicate_review_and_forged_capture(tmp_path):
    candidate,review,source=packet()
    out=tmp_path/'backend/training/flood_ner/artifacts/out'
    with pytest.raises(ValueError,match='unique'):
        build_editorial_queue([candidate,candidate],[review,review],[source],tmp_path,out)
    altered=source.model_copy(update={'publisher':'forged publisher'})
    with pytest.raises(ValueError,match='inventoried'):
        build_editorial_queue([candidate],[review],[altered],tmp_path,out)
    assert not out.exists()


def test_editorial_rejects_missing_reviews_and_nonignored_destinations(tmp_path):
    candidate,review,source=packet()
    with pytest.raises(ValueError,match='each original'):
        build_editorial_queue([candidate],[],[source],tmp_path,tmp_path/'out')
    with pytest.raises(ValueError,match='ignored'):
        build_editorial_queue([candidate],[review],[source],tmp_path,tmp_path/'out')


def test_editorial_outputs_are_deterministic_and_cannot_overwrite(tmp_path):
    candidate,review,source=packet()
    base=tmp_path/'backend/training/flood_ner/artifacts'
    build_editorial_queue([candidate],[review],[source],tmp_path,base/'first')
    build_editorial_queue([candidate],[review],[source],tmp_path,base/'second')
    assert {p.name:p.read_bytes() for p in (base/'first').iterdir()} == {
        p.name:p.read_bytes() for p in (base/'second').iterdir()}
    with pytest.raises(ValueError,match='empty'):
        build_editorial_queue([candidate],[review],[source],tmp_path,base/'first')


def test_editorial_metadata_rejects_naive_times_blank_reasons_and_false_admission():
    _,review,_=packet()
    for changes in [{'reviewed_at':datetime(2026,10,14)},{'reviewer':' '},
                    {'notes':[' ']},{'admission_status':'training_admitted'}]:
        with pytest.raises(ValueError):
            EditorialReview.model_validate(review.model_dump()|changes)


def test_editorial_cli_reports_inventory_failure(tmp_path,monkeypatch,capsys):
    monkeypatch.setattr('training.flood_ner.cli.inventory_sources',lambda root:([],['missing capture']))
    assert main(['review-passages',str(tmp_path/'candidates'),str(tmp_path/'reviews'),
                 '--output',str(tmp_path/'out')])==1
    assert 'source inventory has unresolved integrity issues' in capsys.readouterr().err


def test_editorial_excluded_widget_cues_remain_auditable(tmp_path):
    candidate,review,source=packet()
    start=candidate.text.index('ADVERTISEMENT')
    candidate=candidate.model_copy(update={'case_cues':[{'role':'research_cue',
        'start':start,'end':start+13,'sha256':text_hash('ADVERTISEMENT')}]})
    output=tmp_path/'backend/training/flood_ner/artifacts/out'
    build_editorial_queue([candidate],[review],[source],tmp_path,output)
    cues=json.loads((output/'cue_dispositions.json').read_text())
    assert len(cues)==1 and cues[0]['disposition']=='explicitly_excluded'
    assert cues[0]['exclusion_kind']=='publisher_interface'
    assert cues[0]['source_version']==source.capture_version
    assert cues[0]['sha256']==text_hash(source.text[cues[0]['start']:cues[0]['end']])
