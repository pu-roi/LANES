"""Constructed correction cases: immutable text/splits and explicit context links."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json

import pytest

from training.flood_ner.annotation.schema import AnnotationRecord, Entity, Fact, Relation, Span, SourceCapture, text_hash
from training.flood_ner.export import CANDIDATE_TOKENIZER_NAME, corpus_tokenizer
from training.flood_ner.revision import EntityCorrection, apply_corrections, record_hash, revise_contexts, write_cohort_revision
from training.flood_ner.sources import json_bytes, write_jsonl
from training.flood_ner.qualification import load_frozen_cohort


def fixture():
    text = 'Sa Ilocos Sur, EDSA-Balintawak receded. Unit 31-A. Ilocos Sur.'
    source = SourceCapture(source_id='constructed', url='https://example.org/constructed', publisher='Fixture',
        origin='constructed_fixture', text=text, text_sha256=text_hash(text), capture_version='fixture',
        article_group='fixture', event_group='fixture', syndication_group='fixture', reuse_terms='test only',
        extraction_method='constructed regression')
    a = text.index('EDSA'); b = text.index('Unit'); c = text.rindex('Ilocos Sur')
    entities = [Entity(id='road', start=a, end=a+15, text='EDSA-Balintawak', label='ROAD'),
                Entity(id='unit', start=b, end=b+9, text='Unit 31-A', label='LOCAL_AREA'),
                Entity(id='province2', start=c, end=c+10, text='Ilocos Sur', label='PROVINCE')]
    record = AnnotationRecord(record_id='r', source=source, text=text, text_sha256=text_hash(text),
        passage_start=0, passage_end=len(text), entities=entities, annotation_profile='location-only-v1',
        passage_language='taglish', annotation_revision='fixture-v1', quality='constructed', complete=True,
        teacher='constructed AI fixture', reviewer='constructed AI fixture', review_status='accepted', split='train')
    after = [Entity(id='province1', start=3, end=13, text='Ilocos Sur', label='PROVINCE'),
             Entity(id='road', start=a, end=a+4, text='EDSA', label='ROAD'),
             Entity(id='local', start=a+5, end=a+15, text='Balintawak', label='LOCAL_AREA'), *entities[1:]]
    patch = EntityCorrection(record_id='r', original_record_sha256=record_hash(record), passage_sha256=record.text_sha256,
        before_entities=deepcopy(entities), after_entities=deepcopy(after), revision='fixture-v2', reviewer='fixture AI reviewer',
        reviewed_at=datetime(2026,10,15,tzinfo=timezone.utc), reason='Repeated province and road/local-area boundary review.',
        context_target_qualifiers={'road':'EDSA target refers only to the source-mentioned Balintawak segment.'})
    nlp = corpus_tokenizer(CANDIDATE_TOKENIZER_NAME)
    return record, patch, nlp


def test_reviewed_correction_preserves_every_field_except_reviewed_labels_and_provenance():
    record, patch, nlp = fixture(); before = record_hash(record)
    revised = apply_corrections([record], [patch], nlp)[0]
    assert record_hash(record) == before
    assert revised.source == record.source and revised.text == record.text and revised.split == record.split
    assert revised.text_sha256 == record.text_sha256 and revised.record_id == record.record_id
    assert [e.text for e in revised.entities if e.label=='PROVINCE'] == ['Ilocos Sur','Ilocos Sur']
    assert [(e.text,e.label) for e in revised.entities if e.id in {'road','local'}] == [('EDSA','ROAD'),('Balintawak','LOCAL_AREA')]
    assert revised.entities[-2] == record.entities[-2]  # Unit 31-A remains intact.
    assert revised.quality=='constructed' and revised.annotation_revision=='fixture-v2'
    assert apply_corrections([record],[patch],nlp)==[revised]


@pytest.mark.parametrize('mutation',['record_hash','passage_hash','before','missing','duplicate','malformed','same_revision','no_change','bad_target'])
def test_changed_inputs_or_unqualified_corrections_are_rejected(mutation):
    record,patch,nlp=fixture(); patches=[patch]
    if mutation=='record_hash':patch.original_record_sha256='0'*64
    elif mutation=='passage_hash':patch.passage_sha256='0'*64
    elif mutation=='before':patch.before_entities.pop()
    elif mutation=='missing':patch.record_id='absent'
    elif mutation=='duplicate':patches.append(patch)
    elif mutation=='malformed':patch.after_entities[0].end+=1
    elif mutation=='same_revision':patch.revision=record.annotation_revision
    elif mutation=='no_change':patch.after_entities=deepcopy(record.entities)
    else:patch.context_target_qualifiers={'missing':'no such entity'}
    with pytest.raises(ValueError):apply_corrections([record],patches,nlp)


def context_for(record):
    context=record.model_copy(deep=True);context.annotation_profile='context-rich-v1'
    evidence=Span(start=0,end=len(record.text),text=record.text)
    context.facts=[Fact(id='active',kind='status',value='active',evidence=[evidence]),
                   Fact(id='receding',kind='status',value='receding',evidence=[evidence])]
    context.relations=[Relation(id='base',fact_id='active',target_entity_ids=['road'],scope='local',evidence=[evidence]),
                       Relation(id='later',fact_id='receding',target_entity_ids=['road'],scope='local',evidence=[evidence],overrides_relation_id='base')]
    return context


def test_context_preserves_targets_overrides_and_does_not_flood_new_locality():
    record,patch,nlp=fixture(); original=context_for(record);old=record_hash(original)
    revised=apply_corrections([record],[patch],nlp)
    context=revise_contexts([record],revised,[original],[patch],nlp)[0]
    assert record_hash(original)==old and context.relations==original.relations
    assert context.entities==revised[0].entities and context.relations[1].overrides_relation_id=='base'
    assert all(r.target_entity_ids==['road'] for r in context.relations)
    assert all(f.qualifiers==[patch.context_target_qualifiers['road']] for f in context.facts)


@pytest.mark.parametrize('mutation',['source','passage_bounds','language','places','split','wrong_revision','dangling_target'])
def test_context_rebind_rejects_changed_pair_or_unreviewed_inputs(mutation):
    record,patch,nlp=fixture();context=context_for(record);revised=apply_corrections([record],[patch],nlp)
    if mutation=='source':context.source=context.source.model_copy(update={'title':'changed'})
    elif mutation=='passage_bounds':context.passage_start=1
    elif mutation=='language':context.passage_language='english'
    elif mutation=='places':context.entities.pop()
    elif mutation=='split':context.split='dev'
    elif mutation=='wrong_revision':revised[0].notes.append('unreviewed edit')
    else:context.relations[0].target_entity_ids=['missing']
    with pytest.raises(ValueError):revise_contexts([record],revised,[context],[patch],nlp)


def test_review_provenance_cannot_be_blank_or_timezone_unknown():
    _,patch,_=fixture();data=patch.model_dump(mode='json')
    for changes in [{'reason':' '},{'reviewer':' '},{'reviewed_at':'2026-10-15T00:00:00'}]:
        with pytest.raises(ValueError):EntityCorrection.model_validate_json(json.dumps(data|changes))


def test_revision_rejects_overwrite_and_paths_outside_artifacts(tmp_path):
    _,patch,_=fixture();output=tmp_path/'backend/training/flood_ner/artifacts/existing';output.mkdir(parents=True)
    for target in [output,tmp_path/'outside']:
        with pytest.raises(ValueError,match='destination'):write_cohort_revision(tmp_path,[patch],target,tmp_path)


def test_frozen_revision_replays_without_reselection_and_keeps_parent_hashes(tmp_path):
    record,patch,nlp=fixture()
    base=tmp_path/'backend/training/flood_ner/artifacts';parent=base/'original';parent.mkdir(parents=True)
    write_jsonl(parent/'grouped_annotations.jsonl',[record])
    (parent/'tokenizer.bin').write_bytes(nlp.tokenizer.to_bytes())
    (parent/'annotation_schema.json').write_bytes(json_bytes(AnnotationRecord.model_json_schema()))
    (parent/'selection_register.json').write_bytes(json_bytes([{'record_id':record.record_id,'entities':len(record.entities)}]))
    (parent/'coverage.json').write_bytes(json_bytes({'entity_labels':{},'empty_entity_records':0}))
    manifest={'tokenizer':CANDIDATE_TOKENIZER_NAME,'tokenizer_sha256':hashlib.sha256((parent/'tokenizer.bin').read_bytes()).hexdigest(),
              'annotation_schema_sha256':hashlib.sha256((parent/'annotation_schema.json').read_bytes()).hexdigest(),
              'counts':{'train':{'taglish':1},'dev':{},'test':{}},'total':1,
              'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in parent.iterdir()}}
    (parent/'partition_manifest.json').write_bytes(json_bytes(manifest))
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in parent.iterdir()}
    a=write_cohort_revision(parent,[patch],base/'revised-a',tmp_path)
    b=write_cohort_revision(parent,[patch],base/'revised-b',tmp_path)
    assert a==b and a['counts']==manifest['counts'] and a['tokenizer_sha256']==manifest['tokenizer_sha256']
    rows,_,_=load_frozen_cohort(base/'revised-a')
    assert rows[0].entities==patch.after_entities and rows[0].split==record.split
    assert before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in parent.iterdir()}
    assert all((base/'revised-a'/p.name).read_bytes()==p.read_bytes() for p in (base/'revised-b').iterdir())
    patch.original_record_sha256='0'*64
    with pytest.raises(ValueError,match='input hash'):write_cohort_revision(parent,[patch],base/'invalid',tmp_path)
    assert not (base/'invalid').exists()
