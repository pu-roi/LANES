"""The historical host preserves the already reviewed Cloud Run resource rules."""
import pytest

from app.services import news_history_resources as resources


@pytest.mark.parametrize('quota,swap,accepted', [(104300, 0, True), (80600, None, True), (-1, 0, False)])
def test_cloud_profile_reports_actual_quota_and_requires_positive_limits(tmp_path, quota, swap, accepted):
    root = tmp_path/'cgroup'; proc = tmp_path/'proc'
    for directory in (root/'cpu', root/'memory', proc):
        directory.mkdir(parents=True, exist_ok=True)
    values = {'cpu/cpu.cfs_quota_us':quota, 'cpu/cpu.cfs_period_us':100000,
        'memory/memory.limit_in_bytes':3*1024**3, 'memory/memory.max_usage_in_bytes':2*1024**3,
        'memory/memory.memsw.limit_in_bytes':3*1024**3 if swap == 0 else 2**63-4096}
    for path, value in values.items():
        (root/path).write_text(str(value), encoding='ascii')
    (proc/'swaps').write_text('Filename Type Size Used Priority\n', encoding='ascii')
    (proc/'meminfo').write_text('SwapTotal: 0 kB\nSwapFree: 0 kB\n', encoding='ascii')
    if accepted:
        result = resources.resources(root, profile=resources.CLOUD_PROFILE, proc=proc)
        assert result['cpu_quota'] == quota
        assert result['swap_evidence']['basis'] == ('enforced_zero_limit' if swap == 0 else 'host_no_swap')
        with pytest.raises(ValueError):
            resources.resources(root, profile=resources.STRICT_PROFILE, proc=proc)
        if swap is None:
            (proc/'meminfo').write_text('SwapTotal: 100 kB\nSwapFree: 100 kB\n', encoding='ascii')
            with pytest.raises(ValueError, match='swap_evidence_required'):
                resources.resources(root, profile=resources.CLOUD_PROFILE, proc=proc)
    else:
        with pytest.raises(ValueError):
            resources.resources(root, profile=resources.CLOUD_PROFILE, proc=proc)


def test_resource_checkpoint_rejects_peak_above_headroom(monkeypatch):
    monkeypatch.setattr(resources, 'resources', lambda **_: {'peak':resources.HEADROOM_BYTES})
    with pytest.raises(ValueError, match='headroom'):
        resources.checkpoint()


@pytest.mark.asyncio
async def test_worker_resource_failure_returns_bounded_status_without_sql(monkeypatch):
    from sqlalchemy.engine import URL
    from app.services.news_historical_policy import HistoricalAuthorization
    from app.services.news_ner_durable.processing import process_native_saved_news
    monkeypatch.setenv('LANES_HISTORY_RESOURCE_PROFILE', 'cloud-run-v1')
    def fail():
        raise ValueError('cpu_limit_required')
    monkeypatch.setattr(resources, 'checkpoint', fail)
    authorization = HistoricalAuthorization(None, None, {'resource_profile':'cloud-run-v1'}, '')
    summary = await process_native_saved_news(lambda: pytest.fail('Resource failure reached SQL'),
        load_assets=lambda: pytest.fail('Resource failure reached asset loading'), environment='production',
        database_url=URL.create('postgresql+psycopg',host='example.invalid',database='fixture').render_as_string(),
        run_ids=(1,),limit=1,historical_authorization=authorization)
    assert summary.error_code == 'historical_resource_envelope_unqualified'
