from datetime import datetime, timezone
import hashlib
import json

import pytest
from pydantic import ValidationError

from training.flood_ner.annotation.schema import SourceCapture, AnnotationRecord, text_hash
from training.flood_ner.collection import source_entry
from training.flood_ner.preparation import CandidatePassage, propose_passage, prepare_candidates
from training.flood_ner.sources import read_jsonl


def reviewed(tmp_path, newline='\n'):
    body=newline.join(['Published January 16, 2024','Nabunturan',
        'Flooding reached Purok 9, Barangay Poblacion, while Purok 5 and Purok 6 in Barangay Magading were also affected.',
        'Several residents reported knee-deep water. Rescue workers said the bridge was closed to vehicles.',
        'Later reports described recession. These observations provide no exact onset date or per-household water measurement.'])
    raw=b'<meta property="article:published_time" content="2024-01-16T08:00:00+00:00">'
    (tmp_path/'body.txt').write_bytes(body.encode());(tmp_path/'raw.html').write_bytes(raw)
    source=SourceCapture(source_id='test-source',url='https://gmanetwork.com/news/nation/123456/report/story/',publisher='GMA News',
        text=body,text_sha256=text_hash(body),capture_version='version',raw_sha256=hashlib.sha256(raw).hexdigest(),
        published_at=datetime(2024,1,16,8,tzinfo=timezone.utc),publication_basis='HTML meta article:published_time',
        article_group='test-article',reuse_terms='not verified',extraction_method='test-source')
    start=body.index('Flooding');end=body.index(newline,start)
    cue=body.index('Purok 9')
    entry=source_entry(source)
    entry.update(status='accepted',reviewer='test-reviewer',review_notes=['test body reviewed'],language='english',
        text_path='body.txt',raw_path='raw.html',publication_evidence={'kind':'html_metadata','path':'raw.html'},
        event_group='provisional:davao-2024',syndication_group='unresolved:test',
        evidence=[{'role':'body_review_anchor','start':start,'end':end,'sha256':text_hash(body[start:end])},
                  {'role':'numbered_locality_cue','start':cue,'end':cue+7,'sha256':text_hash('Purok 9')}])
    return source,entry


@pytest.mark.parametrize('newline',['\n','\r\n'])
def test_candidate_preserves_context_and_unreviewed_state(tmp_path,newline):
    source,entry=reviewed(tmp_path,newline)
    candidate=propose_passage(entry,source)
    assert candidate.text.startswith('Nabunturan'+newline)
    assert 'Published January' not in candidate.text
    assert candidate.text == source.text[candidate.passage_start:candidate.passage_end]
    cue=candidate.case_cues[0]
    assert candidate.text[cue['start']:cue['end']] == 'Purok 9'
    assert candidate.passage_language == 'unknown' and candidate.review_status == 'proposed'
    assert candidate.admission_status == 'research_only' and candidate.proposed_event_group.startswith('provisional:')
    assert CandidatePassage.model_validate_json(candidate.model_dump_json()) == candidate
    with pytest.raises(ValidationError):
        AnnotationRecord.model_validate_json(candidate.model_dump_json())


@pytest.mark.parametrize('changes',[{'text_sha256':'0'*64},{'passage_start':1},{'admission_status':'training_admitted'},
    {'review_status':'accepted'},{'case_cues':[{'role':'test','start':0,'end':2,'sha256':'0'*64}]},
    {'article_key':'gma:9999999'},{'candidate_id':'candidate-'+'0'*20},
    {'hold_reasons':['annotation_not_started']},{'case_cues':[{'role':None,'start':0,'end':2,'sha256':text_hash('Na')}]}])
def test_candidate_rejects_corruption_or_premature_admission(tmp_path,changes):
    source,entry=reviewed(tmp_path);candidate=propose_passage(entry,source)
    data=candidate.model_dump();data.update(changes)
    with pytest.raises(ValidationError):
        CandidatePassage.model_validate(data)


def test_preparation_is_deterministic_and_metadata_excludes_full_text(tmp_path):
    source,entry=reviewed(tmp_path)
    base=tmp_path/'backend/training/flood_ner/artifacts'
    first=prepare_candidates([entry],[source],tmp_path,base/'first')
    second=prepare_candidates([entry],[source],tmp_path,base/'second')
    assert first == second
    for filename in ('candidate_passages.jsonl','candidate_register.json','group_review_queue.json','readiness.json'):
        assert (base/'first'/filename).read_bytes()==(base/'second'/filename).read_bytes()
    restored=read_jsonl(base/'first/candidate_passages.jsonl',CandidatePassage)
    assert restored[0].source.text == source.text
    metadata=json.loads((base/'first/candidate_register.json').read_text())
    assert 'text' not in metadata[0] and 'source' not in metadata[0]
    assert first['training_admitted'] == first['assigned_splits'] == first['annotated_passages'] == 0
    with pytest.raises(ValueError,match='must be empty'):
        prepare_candidates([entry],[source],tmp_path,base/'first')


def test_preparation_refuses_non_artifact_output_and_bad_sources(tmp_path):
    source,entry=reviewed(tmp_path)
    with pytest.raises(ValueError,match='ignored training artifacts'):
        prepare_candidates([entry],[source],tmp_path,tmp_path/'docs')
    assert not (tmp_path/'docs').exists()
    entry['text_sha256']='0'*64
    with pytest.raises(ValueError,match='mismatched'):
        prepare_candidates([entry],[source],tmp_path,tmp_path/'backend/training/flood_ner/artifacts/out')


def test_missing_retrieval_time_retains_a_provenance_hold(tmp_path):
    source,entry=reviewed(tmp_path)
    assert source.raw_sha256 and source.captured_at is None
    candidate=propose_passage(entry,source)
    assert 'legacy_original_html_retrieval_gap' in candidate.hold_reasons
    data=candidate.model_dump()
    data['hold_reasons'].remove('legacy_original_html_retrieval_gap')
    with pytest.raises(ValidationError,match='required review/provenance holds'):
        CandidatePassage.model_validate(data)


def test_chrome_truncation_and_omitted_case_are_diagnostics(tmp_path):
    source,entry=reviewed(tmp_path)
    body=source.text+'\nADVERTISEMENT\nLater flood status changed at Purok 12.\n'+'Another independent paragraph. '*15
    source=source.model_copy(update={'text':body,'text_sha256':text_hash(body)})
    at=body.index('Purok 12')
    entry['case_types']=['numbered_locality_cue']
    # Select a short bounded draft whose body anchor does not include the later cue.
    entry['evidence']=[entry['evidence'][0],{'role':'numbered_locality_cue','start':at,'end':at+8,'sha256':text_hash('Purok 12')}]
    candidate=propose_passage(entry,source,target_characters=100)
    assert 'truncated_article_scope_review_pending' in candidate.hold_reasons
    assert 'numbered_locality_cue_outside_window_review_pending' in candidate.hold_reasons
    full=propose_passage(entry,source,target_characters=len(body))
    assert 'publisher_chrome_review_pending' in full.hold_reasons
    assert full.review_status=='proposed' and full.passage_language=='unknown'


def test_known_source_measurement_ambiguity_survives_proposal(tmp_path):
    source,entry=reviewed(tmp_path)
    entry['case_types']=['measurement_role_ambiguity']
    note='Height in this source describes crops, not floodwater; review the measurement role.'
    entry['review_notes'].append(note)
    candidate=propose_passage(entry,source)
    assert note in candidate.source_review_notes
    assert 'measurement_role_review_pending' in candidate.hold_reasons
    assert candidate.admission_status=='research_only'
