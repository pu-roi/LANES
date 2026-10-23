"""Counting and execution must agree across JSONB/Pydantic object ordering."""
import json
from unittest.mock import patch

from app.services.news_ner_durable.gemini_resolution import GeminiResolver
from app.services.news_ner_durable.contracts import sha
from app.services.news_source_repair_resolver import SourceRepairResolver


def test_embedded_document_is_canonical_without_reordering_passages_or_targets():
    resolver = object.__new__(SourceRepairResolver)
    original = {'targets':[{'id':'n6','label':'ROAD'}], 'evidence_text':'Tañong — gutter deep',
        'quote_options':[{'quote':'second', 'option_index':1}, {'quote':'first', 'option_index':0}]}
    reordered = {'quote_options':[{'option_index':1,'quote':'second'}, {'option_index':0,'quote':'first'}],
        'evidence_text':original['evidence_text'], 'targets':[{'label':'ROAD','id':'n6'}]}
    hashes = []
    for document in (original,reordered):
        packet = {'payload':{'contents':[{'parts':[{'text':json.dumps(document)}]}]}, 'context':{'parent_run_id':382}}
        with patch.object(GeminiResolver,'request_packets',return_value=[packet]):
            result = resolver.request_packets(None,None,parent_run_id=382,parent_result_sha256='a'*64)[0]
        assert json.loads(result['payload']['contents'][0]['parts'][0]['text']) == original
        hashes.append(sha(result['payload']))
    assert hashes[0] == hashes[1]
