"""Fresh interpreter coverage for the controlled C3b entrypoint."""
import pytest
import test_news_ner_processing_cli as probes


@pytest.mark.parametrize('failure,target,code,status',[
    ('settings','','ner_configuration_invalid',1),
    ('import','pydantic','ner_runtime_failed',1),
    ('import','app.services.news_ner_durable.assets','ner_runtime_failed',1),
    ('import','app.services.news_ner_durable.pipeline','ner_runtime_failed',1),
    ('interrupt','app.services.news_ner_durable.pipeline','ner_runtime_cancelled',130),
    ('cancel','app.services.news_ner_durable.pipeline','ner_runtime_cancelled',130),
])
def test_pipeline_cli_bootstrap_is_bounded(tmp_path,monkeypatch,failure,target,code,status):
    monkeypatch.setattr(probes,'BOOTSTRAP_PROBE',probes.BOOTSTRAP_PROBE.replace(
        'scripts.run_news_ner_processing','scripts.run_news_ner_pipeline'))
    result=probes.run_fresh_cli(tmp_path,failure,target,[
        '--bundle','unused','--bundle-sha256','0'*64,'--worker-code-sha256','0'*64])
    import json
    assert result.returncode==status
    assert result.stdout.splitlines()==[json.dumps({'error_code':code})] and result.stderr==''
