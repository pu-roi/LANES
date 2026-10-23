"""Regression for real Gemini character offsets used as quote-option references."""
from copy import deepcopy
import json

import pytest

from app.services.news_gemini_receipts import validate_batch
from app.services.news_ner_durable.gemini_resolution import (
    EVIDENCE_CONTRACT, EVIDENCE_FIELDS, INSTRUCTIONS, response_schema)
from app.services.news_ner_durable.resolution import ResolutionError, quote_options
from test_news_gemini_receipts import CONFIG, envelope
from test_news_native_resolution import answer, resolver


@pytest.mark.parametrize('profile',['normalized','compact','inline'])
@pytest.mark.parametrize('count',[1,59,256])
def test_only_article_quote_ids_are_advertised_in_every_evidence_field(profile,count):
    batch=[{'id':'n0'},{'id':'n1'}];before=deepcopy(batch)
    schema=response_schema(batch,profile,count)
    row=schema['properties']['results']['items'] if profile=='inline' else schema['$defs']['ResolvedMention']
    assert batch==before
    for field in EVIDENCE_FIELDS:
        item=row['properties'][field+'_evidence']
        assert item['items']=={'type':'integer','enum':list(range(count))}
        assert all(index not in item['items']['enum'] for index in (-1,count,318,327,347))
        if profile!='normalized':assert 'minItems' not in item and 'maxItems' not in item
    assert row['properties']['target_id']['enum']==['n0','n1']


@pytest.mark.parametrize('count',[0,257,-1,True,'59'])
def test_no_unbounded_schema_for_missing_or_invalid_quote_inventory(count):
    with pytest.raises(ResolutionError,match='native_resolution_quote_count_invalid'):
        response_schema([{'id':'n0'}],'compact',count)


def test_wire_contract_changes_processing_identity_without_changing_canonical_format():
    identity=resolver().identity
    assert identity['evidence_contract']==EVIDENCE_CONTRACT
    assert identity['response_version']=='native-gemini-resolution-v1'
    assert 'Character start/end positions' in INSTRUCTIONS


@pytest.mark.parametrize('indexes',[ [318], [327], [347], [-1], [59], [0,0] ])
def test_returned_offsets_and_duplicates_still_fail_without_repair_or_dedup(indexes):
    text='\n'.join('Source paragraph '+str(i) for i in range(59))
    options=quote_options(text)
    document={'evidence_text':text,'quote_options':[{'option_index':i,'quote':q['quote']} for i,q in enumerate(options)],
        'targets':[{'id':'n1'}]}
    packet={'contents':[{'parts':[{'text':json.dumps(document)}]}]}
    row=answer({'id':'n1','label':'ROAD'},place_evidence=indexes)
    original=deepcopy(row)
    with pytest.raises(ResolutionError,match='native_resolution_evidence_invalid') as caught:
        validate_batch(packet,json.dumps(envelope([row])).encode(),CONFIG)
    assert row==original
    assert caught.value.provider_diagnostic['errors'][0]['target_id']=='n1'
    assert caught.value.provider_diagnostic['errors'][0]['field']=='place_evidence'


def test_boundary_quote_references_pass_structural_validation_only():
    text='\n'.join('Source paragraph '+str(i) for i in range(59))
    options=quote_options(text)
    document={'evidence_text':text,'quote_options':[{'option_index':i,'quote':q['quote']} for i,q in enumerate(options)],
        'targets':[{'id':'n1'}]}
    packet={'contents':[{'parts':[{'text':json.dumps(document)}]}]}
    row=answer({'id':'n1','label':'CITY'},place_evidence=[0,58])
    parsed,_=validate_batch(packet,json.dumps(envelope([row])).encode(),CONFIG)
    assert parsed.results[0].place_evidence==(0,58)
