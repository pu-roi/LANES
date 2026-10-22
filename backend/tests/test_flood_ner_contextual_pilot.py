"""Context is paired evidence, never extra NER samples or fabricated chronology."""
from copy import deepcopy

import pytest

from training.flood_ner.annotation.schema import AnnotationRecord, text_hash
from training.flood_ner.contextual_pilot import ContextReview, CATEGORIES, validate_contextual_pilot
from training.flood_ner.export import CANDIDATE_TOKENIZER_NAME, corpus_tokenizer


def pilot():
    locations=[]; contexts=[]; reviews=[]
    for i in range(40):
        text = (f'Report {i}: Main Road and Side Road had 10–20 inches of water. '
                'Main Road instead had 5 inches. The water later subsided. The clock was not reported.')
        def span(value):
            start=text.index(value)
            return {'start':start,'end':start+len(value),'text':value}
        evidence=[{'start':0,'end':len(text),'text':text}]
        data={'record_id':f'context-{i}', 'source':{'source_id':f'fixture-{i}', 'url':f'https://gmanetwork.com/news/example/{i}',
              'publisher':'GMA News','text':text,'text_sha256':text_hash(text),'capture_version':text_hash(text),
              'article_group':f'article-{i}','event_group':f'event-{i}','syndication_group':f'copy-{i}',
              'origin':'constructed_fixture','extraction_method':'test','reuse_terms':'constructed regression fixture'},
              'passage_start':0,'passage_end':len(text),'text':text,'text_sha256':text_hash(text),
              'passage_language':'english' if i<20 else 'taglish', 'annotation_profile':'location-only-v1',
              'quality':'constructed','annotation_revision':'fixture-v1','review_status':'accepted','reviewer':'fixture reviewer',
              'complete':True,'split':'train','entities':[{'id':'road1','label':'ROAD',**span('Main Road')},
                                                      {'id':'road2','label':'ROAD',**span('Side Road')}]}
        location=AnnotationRecord.model_validate(data);locations.append(location)
        data=deepcopy(data);data['annotation_profile']='context-rich-v1'
        data['entities'] += [{'id':'range','label':'DEPTH',**span('10–20 inches')},{'id':'local','label':'DEPTH',**span('5 inches')}]
        data['facts']=[{'id':'shared-depth','kind':'depth','depth_scope':'range','entity_ids':['range'],'value':'10–20 inches','evidence':evidence,
                        'qualifiers':['collective range; no exact per-road depth']},
                       {'id':'override-depth','kind':'depth','depth_scope':'point','entity_ids':['local'],'value':'5 inches','evidence':evidence},
                       {'id':'recession','kind':'status','value':'subsided','evidence':[span('later subsided')],
                        'uncertainty':['relative transition only; no observation clock stated']}]
        data['relations']=[{'id':'shared','fact_id':'shared-depth','target_entity_ids':['road1','road2'],'scope':'shared','evidence':evidence},
                           {'id':'exception','fact_id':'override-depth','target_entity_ids':['road1'],'scope':'local','evidence':evidence,
                            'overrides_relation_id':'shared'}]
        contexts.append(AnnotationRecord.model_validate(data))
        reviews.append(ContextReview.model_validate({'record_id':data['record_id'],'passage_sha256':data['text_sha256'],
                        'reviewer':'fixture reviewer','categories':[{'category':c,'evidence':evidence,'rationale':'Explicit constructed regression evidence'} for c in CATEGORIES]}))
    return locations,contexts,reviews


def report(rows):
    return validate_contextual_pilot(*rows,corpus_tokenizer(CANDIDATE_TOKENIZER_NAME))


def test_forty_paired_records_unknown_clock_and_context_scope():
    rows=pilot();result=report(rows)
    assert result['complete'] and result['additional_location_samples']==0 and result['records']==40
    assert all(not any(f.kind=='time' for f in r.facts) for r in rows[1])
    assert all(sum(v.values())==40 for v in result['category_support'].values())


@pytest.mark.parametrize('mutation,reason', [
    ('holdout','training'),('wrong_hash','hash'),('moved_passage','passage'),('missing_review','source-bound'),
    ('same_language','20 English'),('missing_category','four examples'),('bad_evidence','unchanged'),
    ('removed_override','exception category'),('fabricated_time','depth/time'),('address_depth','evidence entity reference'),
])
def test_contextual_pilot_rejects_unqualified_pairing(mutation,reason):
    locations,contexts,reviews=pilot()
    if mutation=='holdout': locations[0].split=contexts[0].split='dev'
    if mutation=='wrong_hash': reviews[0].passage_sha256='0'*64
    if mutation=='moved_passage': contexts[0].passage_start=1
    if mutation=='missing_review': reviews.pop()
    if mutation=='same_language': contexts[0].passage_language='taglish'
    if mutation=='missing_category':
        for r in reviews: r.categories=[c for c in r.categories if c.category!='temporal_transitions']
    if mutation=='bad_evidence': reviews[0].categories[0].evidence[0].text='fabricated text'
    if mutation=='removed_override': contexts[0].relations[1].overrides_relation_id=None
    if mutation=='fabricated_time': contexts[0].facts[0].value='10:00 AM'
    if mutation=='address_depth':
        from training.flood_ner.annotation.schema import Fact
        contexts[0].facts.append(Fact(id='fabricated-depth',kind='depth',entity_ids=['road1'],depth_scope='point',evidence=contexts[0].facts[0].evidence))
    assert any(reason in e for e in report((locations,contexts,reviews))['errors'])


def test_one_article_per_language_cannot_pass_diversity():
    locations,contexts,reviews=pilot()
    for l,c in zip(locations,contexts): l.source.url=c.source.url='https://gmanetwork.com/news/example/one'
    assert any('five articles' in e for e in report((locations,contexts,reviews))['errors'])


def test_duplicate_categories_do_not_inflate_support():
    rows=pilot();rows[2][0].categories.append(rows[2][0].categories[0].model_copy(deep=True))
    assert any('duplicate categories' in e for e in report(rows)['errors'])


def test_pilot_rejects_access_polarity_contradicting_exact_source_phrase():
    from training.flood_ner.annotation.context_review import reviewed_access_fact
    from training.flood_ner.annotation.schema import Span
    locations,contexts,reviews=pilot()
    suffix=' Main Road: Not passable to light vehicles.'
    for r in (locations[0],contexts[0]):
        r.text+=suffix
        r.text_sha256=r.source.text_sha256=text_hash(r.text)
        r.source.text=r.text
        r.passage_end=len(r.text)
    reviews[0].passage_sha256=contexts[0].text_sha256
    text=contexts[0].text;start=text.index('Not passable')
    fact=reviewed_access_fact('access',Span(start=start,end=len(text)-1,text=text[start:-1]))
    fact.value='passable_unspecified'
    contexts[0].facts.append(fact)
    assert any('access value contradicts' in e for e in report((locations,contexts,reviews))['errors'])
    fact.value='light_vehicle_closed'
    assert report((locations,contexts,reviews))['complete']


def test_pilot_rejects_flood_onset_role_disclaimed_by_rainfall_qualifier():
    from training.flood_ner.annotation.schema import Entity, Fact, Span
    rows=pilot();record=rows[1][0]
    start=record.text.index('later');evidence=Span(start=start,end=start+5,text='later')
    record.entities.append(Entity(id='relative-time',label='TIME',**evidence.model_dump()))
    fact=Fact(id='rainfall-time',kind='time',value='later',entity_ids=['relative-time'],
              temporal_role='onset',evidence=[evidence],qualifiers=['Rainfall onset, not flood onset.'])
    record.facts.append(fact)
    assert any('flood temporal role contradicts' in e for e in report(rows)['errors'])
    fact.temporal_role='unspecified'
    assert report(rows)['complete']
