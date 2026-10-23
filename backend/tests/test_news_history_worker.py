"""Cloud command status handling must agree with committed registration outcomes."""
import json
import sys

import pytest

from app.services.news_ner_durable.contracts import sha
from scripts import run_news_history_seed as worker


@pytest.mark.parametrize('result,code,status', [
    ({'database_writes_performed':True,'version_ids':[1,2]},0,'completed'),
    ({'database_writes_performed':False},0,'ready'),
    ({'status':'requires_attention','database_writes_performed':True},1,'requires_attention')])
def test_command_keeps_durable_outcome_and_returns_correct_status(tmp_path,monkeypatch,capsys,result,code,status):
    config={'fictional':True};path=tmp_path/'config.json';path.write_text(json.dumps(config),encoding='utf-8')
    monkeypatch.setattr(sys,'argv',['worker','register','--config',str(path),'--config-sha256',sha(config)])
    monkeypatch.setattr(worker,'execute',lambda *_:dict(result))
    assert worker.main()==code
    event=json.loads(capsys.readouterr().out)
    assert event['status']==status and event['stage']=='register'


def test_receipt_never_emits_source_text_or_interpretation(capsys):
    worker.emit('preview',{'status':'ready','selection':[{'text':'PRIVATE'}],
        'execution_manifest':{'article_text':'PRIVATE'},'historical_interpretations':[{'text':'PRIVATE'}],
        'outputs':[{'article_id':1,'outcome':'unresolved','geometry':{'text':'PRIVATE'},'read_projection':{'text':'PRIVATE'}}]})
    output=capsys.readouterr().out
    assert 'PRIVATE' not in output and json.loads(output)['outputs'][0]['article_id']==1
