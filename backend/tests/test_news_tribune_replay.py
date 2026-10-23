"""Cross-street context must not hide independent/conflicting observations."""
from copy import deepcopy
from types import SimpleNamespace
import pytest
from app.services.news_tribune_replay import crossing_context, source_context, ZeroProviderBudget
from app.services.news_ner_durable.resolution import ResolutionError


def source_rows():
    facts=dict(verdict='observed',city='Mandaluyong',barangay=None,status='active',date_text='Thursday',
        clock_text='4:34 p.m.',time_role='observation',depth_text='10 inches',depth_scope='individual',
        access='passable_all',historical=False,contradictory=False,
        road_section='Boni Avenue at the corner of F. Ortigas Street',place_evidence=(1,),
        status_evidence=(1,),time_evidence=(0,1),depth_evidence=(1,),access_evidence=(1,),section_evidence=(1,))
    from app.services.news_ner_durable.resolution import ResolvedMention
    rows=[ResolvedMention(target_id=key,contemporaneous=True,**facts) for key in ('owner','crossing')]
    targets=[dict(id='owner',text='Boni Avenue',label='ROAD'),dict(id='crossing',text='F. Ortigas Street',label='ROAD')]
    semantic=dict(row_outcomes=[dict(target_id=key,outcome='accepted',issues=[]) for key in ('owner','crossing')])
    return rows,targets,semantic


def test_exact_crossing_retains_original_response_and_owner():
    rows,targets,semantic=source_rows()
    before=[r.model_dump() for r in rows]
    effective,proof=crossing_context(rows,targets,semantic)
    assert [r.verdict for r in effective]==['observed','unsupported']
    assert [r.model_dump() for r in rows]==before
    assert proof[0]['owner_target_id']=='owner'
    assert effective[1].depth_text==rows[1].depth_text


@pytest.mark.parametrize('change',[
    {'clock_text':'5 PM'},{'status':'subsided'},{'depth_text':'8 inches'},
    {'city':'Manila'},{'access':'unknown'},{'road_section':'F. Ortigas Street was also flooded'},
    {'status_evidence':(2,)},
])
def test_independent_facts_or_evidence_are_not_suppressed(change):
    rows,targets,semantic=source_rows()
    rows[1]=rows[1].model_copy(update=change)
    effective,proof=crossing_context(rows,targets,semantic)
    assert effective==rows and proof==[]


def test_unresolved_owner_cannot_hide_crossing_observation():
    rows,targets,semantic=source_rows()
    semantic['row_outcomes'][0].update(outcome='unresolved',issues=[dict(code='missing_date')])
    assert crossing_context(rows,targets,semantic)==(rows,[])


def test_replay_budget_always_forbids_provider_dispatch():
    with pytest.raises(ResolutionError,match='provider_forbidden'):
        ZeroProviderBudget().reserve('model',{}, {})
    assert ZeroProviderBudget().stop('receipt_storage_failed') is None


def context_case(monkeypatch):
    import hashlib
    from app.services.news_ner_durable.resolution import quote_options
    body = ('Flooding affected roads on Thursday afternoon.\n'
            'As of 4:34 p.m., Boni Avenue had flooding.\n'
            'In Manila, Quirino Avenue near Guazon Street had flooding; '
            'Gov. Pascual Avenue in Sitio 6, Malabon City was also flooded.')
    monkeypatch.setattr('app.services.news_tribune_pilot.BODY', hashlib.sha256(body.encode()).hexdigest())
    rows, _, _ = source_rows()
    row = rows[0].model_copy(update=dict(target_id='road', city='Malabon City', barangay='Sitio 6',
        clock_text=None, time_evidence=(), place_evidence=(2,), status_evidence=(2,),
        road_section='Gov. Pascual Avenue in Sitio 6'))
    start = body.index('Gov. Pascual Avenue')
    document = dict(evidence_text=body, targets=[dict(id='road', text='Gov. Pascual Avenue',
        label='ROAD', start=start, end=start+len('Gov. Pascual Avenue'))])
    semantic = dict(row_outcomes=[dict(target_id='road', outcome='unresolved', issues=[
        dict(field='time_evidence',code='native_resolution_date_evidence_missing'),
        dict(field='barangay',code='native_resolution_barangay_unresolved')])])
    return row, document, semantic


def test_reviewed_context_restores_date_citation_without_borrowing_boni_clock(monkeypatch):
    row, document, semantic = context_case(monkeypatch)
    original = row.model_dump()
    effective, proof, reviewed = source_context([row], document, semantic)
    result = effective[0]
    assert result.time_evidence == (0, 2) and result.clock_text is None
    assert result.date_text == 'Thursday' and result.contemporaneous is False
    assert result.barangay is None and result.road_section.endswith('in Sitio 6')
    assert result.status == 'active' and result.depth_text == row.depth_text
    assert reviewed['row_outcomes'][0]['issues'] == []
    assert row.model_dump() == original and semantic['row_outcomes'][0]['issues']
    assert proof[0]['clock_transferred'] is False


def test_context_adoption_rejects_other_article_or_later_update(monkeypatch):
    row, document, semantic = context_case(monkeypatch)
    document['evidence_text'] += '\nLater update: Friday at 6 PM.'
    with pytest.raises(ResolutionError, match='context_source_changed'):
        source_context([row], document, semantic)


def test_date_repair_does_not_clear_other_verification_failures(monkeypatch):
    row, document, semantic = context_case(monkeypatch)
    semantic['row_outcomes'][0]['issues'].append(dict(field='access', code='unsupported_access'))
    _, _, reviewed = source_context([row], document, semantic)
    assert reviewed['row_outcomes'][0]['outcome'] == 'unresolved'
    assert reviewed['row_outcomes'][0]['issues'] == [dict(field='access', code='unsupported_access')]


def test_inline_sitio_and_city_qualifiers_are_context_without_clearing_independent_city(monkeypatch):
    row, document, semantic = context_case(monkeypatch)
    body = document['evidence_text']
    for name, label in [('Sitio 6','LOCAL_AREA'), ('Malabon City','CITY')]:
        start = body.index(name)
        target = dict(id='road', text=name, label=label, start=start, end=start+len(name))
        result, _, _ = source_context([row], {**document,'targets':[target]}, semantic)
        assert result[0].verdict == 'unsupported'
        assert result[0].barangay == 'Sitio 6'  # Original fields retained as context.
    city = dict(id='road',text='Quezon City',label='CITY',start=0,end=11)
    result, _, _ = source_context([row.model_copy(update={'status':'subsided'})],
        {**document,'targets':[city]}, semantic)
    assert result[0].verdict == 'observed' and result[0].status == 'subsided'


def test_worker_failure_diagnostics_do_not_log_exception_text_or_locals(monkeypatch, capsys):
    import json
    from scripts import run_news_verified_cloud as worker
    secret = 'private-error-payload-that-must-never-appear'
    monkeypatch.setattr('sys.argv', ['worker', 'tribune-finalize'])
    monkeypatch.setenv('LANES_NEWS_VERIFIED_RELEASE', '/fixture/release.json')
    monkeypatch.setenv('LANES_NEWS_VERIFIED_RELEASE_SHA256', 'fixture')
    monkeypatch.setattr('app.services.news_history_resources.checkpoint', lambda: {})
    monkeypatch.setattr('app.services.news_verified_cloud.release_file', lambda *_: {})
    def fail(*_):
        raise AttributeError(secret)
    monkeypatch.setattr('scripts.run_news_tribune_pilot.run_tribune', fail)
    assert worker.main() == 1
    output = capsys.readouterr().out
    assert secret not in output
    receipt = json.loads(output)
    assert receipt['error_type'] == 'AttributeError' and receipt['error_frames'][-1]['function'] == 'fail'
    assert all(set(frame) == {'file','function','line'} for frame in receipt['error_frames'])


@pytest.mark.parametrize('change', [dict(date_text=None), dict(clock_text='6 PM'),
    dict(status='subsided'), dict(time_evidence=(1,)), dict(place_evidence=(1,))])
def test_context_does_not_replace_conflicting_missing_or_existing_time(monkeypatch, change):
    row, document, semantic = context_case(monkeypatch)
    row = row.model_copy(update=change)
    effective, _, _ = source_context([row], document, semantic)
    assert effective[0].time_evidence == row.time_evidence
    assert effective[0].clock_text == row.clock_text
