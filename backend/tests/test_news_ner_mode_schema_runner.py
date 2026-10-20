"""A setup failure must stop the owned fixture server too, without real Docker."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import verify_news_ner_mode_schema as runner


@pytest.mark.parametrize('fails', [False, True], ids=['success', 'setup_failure'])
def test_owned_server_cleanup_includes_setup_failure(tmp_path, monkeypatch, fails):
    state = {'container_id': 'fictional-owned-container'}
    monkeypatch.setattr(runner, 'read', lambda _: state)
    monkeypatch.setattr(runner, 'assert_owner', lambda _: {'State': {'Running': False}})
    calls = []
    monkeypatch.setattr(runner, 'docker', lambda *args: calls.append(args))
    def checks(*_args):
        if fails:
            raise RuntimeError('fictional setup failure')
        return {'status': 'tests_passed', 'returncode': 0}
    monkeypatch.setattr(runner, 'run_checks', checks)
    if fails:
        with pytest.raises(RuntimeError, match='fictional setup failure'):
            runner.test(tmp_path)
    else:
        assert runner.test(tmp_path)['returncode'] == 0
    assert calls == [('stop', '--time', '5', state['container_id'])]
    assert (tmp_path / 'private-container-stopped.json').exists()
