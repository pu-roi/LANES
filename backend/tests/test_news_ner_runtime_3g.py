"""Resource-profile guard checks; no Docker, model, storage or cloud execution."""
import json
from pathlib import Path
import sys

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[1] / 'scripts')]
import qualify_news_ner_runtime_3g as followup


def test_container_uses_new_memory_without_increasing_cpu_or_exposing_oracles(tmp_path):
    args = followup.container_args(tmp_path, 'fictional-check', 'frozen-image')
    assert args[args.index('--memory') + 1] == str(3 * 1024**3)
    assert args[args.index('--memory-swap') + 1] == str(3 * 1024**3)
    assert args[args.index('--cpus') + 1] == '1'
    assert args[args.index('--network') + 1] == 'none'
    assert '--read-only' in args and '--init' in args
    assert not any('expected-predictions' in value for value in args)
    assert followup.original.LIMITS['memory'] == 1024**3


@pytest.mark.parametrize('field,value', [('memory', 2 * 1024**3), ('memory_swap', -1), ('cpus', 2), ('headroom', 3 * 1024**3)])
def test_reject_changed_frozen_resource_profile(tmp_path, monkeypatch, field, value):
    monkeypatch.setattr(followup, 'preserved_previous', lambda: {})
    limits = {**followup.LIMITS, field: value}
    followup.original.write(tmp_path / 'freeze.json', {'limits': limits, 'previous': {}, 'bindings': {}})
    with pytest.raises(ValueError, match='frozen_profile_changed'):
        followup.check_freeze(tmp_path, followup.digest(tmp_path / 'freeze.json'))


def test_reject_changed_source_after_freeze(tmp_path, monkeypatch):
    monkeypatch.setattr(followup, 'preserved_previous', lambda: {})
    monkeypatch.setattr(followup, 'ROOT', tmp_path)
    (tmp_path / 'source.py').write_text('changed')
    followup.original.write(tmp_path / 'freeze.json', {'limits': followup.LIMITS, 'previous': {},
                                                    'bindings': {'source.py': '0' * 64}})
    with pytest.raises(ValueError, match='frozen_file_changed'):
        followup.check_freeze(tmp_path, followup.digest(tmp_path / 'freeze.json'))
