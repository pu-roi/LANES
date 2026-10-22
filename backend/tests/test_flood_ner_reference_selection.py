"""Reference-preserving cohort revision contracts; constructed sources only."""
from copy import deepcopy
import json
from types import SimpleNamespace

import numpy as np
import pytest

from test_flood_ner_cohort import SMALL, bundle, output, sample
from training.flood_ner import cohort as c


def pinned_bundle():
    rows,reviews,sources=bundle()
    for i,row in enumerate(rows):
        row.split=('train','dev','test')[i//2]
        row.source.event_group=reviews[i].event_group
        sources[i].event_group=reviews[i].event_group
    return rows,reviews,sources


def test_legacy_defaults_remain_identical_and_reference_round_trip(tmp_path):
    rows,reviews,sources=pinned_bundle()
    legacy=c.build_cohort(rows,reviews,sources,tmp_path,output(tmp_path,'legacy'),targets=SMALL,publisher_cap=2)
    assert 'selection_constraints' not in legacy and 'selection_solver' not in legacy
    kwargs=dict(targets=SMALL,publisher_cap=2,reference_records=deepcopy(rows),fixed_record_ids={r.record_id for r in rows},max_reference_changes=0)
    first=c.build_cohort(rows,reviews,sources,tmp_path,output(tmp_path),**kwargs)
    second=c.build_cohort(list(reversed(rows)),list(reversed(reviews)),sources,tmp_path,output(tmp_path,'replay'),**kwargs)
    assert first==second and first['selection_constraints']['actual_reference_changes']==0
    for file in output(tmp_path).iterdir():assert file.read_bytes()==(output(tmp_path,'replay')/file.name).read_bytes()


@pytest.mark.parametrize('change', ['missing','text','language','entity'])
def test_hard_fixed_record_cannot_disappear_or_change(tmp_path,change):
    rows,reviews,sources=pinned_bundle();refs=deepcopy(rows)
    if change=='missing':rows.pop(0)
    elif change=='text':rows[0].passage_start=1
    elif change=='language':rows[0].passage_language='taglish'
    else:rows[0].entities=[dict(id='bad')]
    with pytest.raises(ValueError,match='hard-fixed'):
        c.build_cohort(rows,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=2,
                       reference_records=refs,fixed_record_ids={'r000'},max_reference_changes=1)
    assert not output(tmp_path).exists()


@pytest.mark.parametrize('budget',[None,-1,True,7])
def test_malformed_reference_budget_rejected(tmp_path,budget):
    rows,reviews,sources=pinned_bundle()
    with pytest.raises(ValueError,match='reference'):
        c.build_cohort(rows,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,reference_records=rows,max_reference_changes=budget)


def test_bad_fixed_identity_duplicate_reference_and_orphan_options(tmp_path):
    rows,reviews,sources=pinned_bundle()
    for kwargs in [dict(fixed_record_ids={'missing'}),dict(max_reference_changes=0),
                   dict(reference_records=rows+rows[:1],max_reference_changes=0),
                   dict(reference_records=rows,fixed_record_ids={'missing'},max_reference_changes=0)]:
        with pytest.raises(ValueError):c.build_cohort(rows,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,**kwargs)


def test_soft_conflicting_alternatives_are_kept_until_selection(tmp_path):
    rows,reviews,sources=pinned_bundle();refs=deepcopy(rows)
    alternative=rows[0].model_copy(update={'record_id':'alternative'},deep=True)
    result=c.build_cohort(rows+[alternative],reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=2,
                          reference_records=refs,fixed_record_ids=set(),max_reference_changes=1)
    exclusions=json.loads((output(tmp_path)/'exclusion_register.json').read_text())
    assert {'record_id':'alternative','reason':'eligible_reserve_not_selected'} in exclusions
    assert result['selection_constraints']['actual_reference_changes']==0


def test_hard_fixed_shorter_record_wins_eligibility_over_duplicate(tmp_path):
    rows,reviews,sources=pinned_bundle()
    other=rows[0].model_copy(update={'record_id':'aaa-alternative'},deep=True)
    result=c.build_cohort(rows+[other],reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=2,
                          reference_records=deepcopy(rows),fixed_record_ids={'r000'},max_reference_changes=0)
    assert result['selection_constraints']['actual_reference_changes']==0
    exclusions=json.loads((output(tmp_path)/'exclusion_register.json').read_text())
    assert {'record_id':'aaa-alternative','reason':'overlapping_article_passage'} in exclusions


def test_twenty_change_limit_rejects_twenty_one_changes():
    refs=[sample(i)[0] for i in range(22)]
    extra=[sample(100+i)[0] for i in range(21)]
    for r in refs:r.split='train'
    rows=refs+extra;pilots={r.record_id for r in extra}
    args=(rows,c._groups(rows),pilots,{'train':{'english':22}},100,1)
    with pytest.raises(ValueError,match='infeasible'):
        c._assign(*args,reference_records=refs,fixed_record_ids={refs[0].record_id},max_reference_changes=20)
    result=c._assign(*args,reference_records=refs,fixed_record_ids={refs[0].record_id},max_reference_changes=21)
    assert sum(r.record_id in result for r in refs)==1
    result=c._assign(rows,c._groups(rows),{r.record_id for r in extra[:20]},
                     {'train':{'english':22}},100,1,reference_records=refs,max_reference_changes=20)
    assert sum(r.record_id in result for r in refs)==2


def test_split_movement_and_substantive_change_count_but_notes_do_not():
    row=sample(0)[0];row.split='dev';rows=[row.model_copy(deep=True)]
    args=(rows,c._groups(rows),set(),{'train':{'english':1},'dev':{'english':0}},10,1)
    with pytest.raises(ValueError,match='infeasible'):c._assign(*args,reference_records=[row],max_reference_changes=0)
    assert c._assign(*args,reference_records=[row],max_reference_changes=1)=={row.record_id:'train'}
    row.split='train';rows[0].notes.append('metadata only')
    assert c._same_reference_content(rows[0],row)
    rows[0].passage_language='taglish'
    assert not c._same_reference_content(rows[0],row)


def test_valid_time_limited_incumbent_is_not_called_optimal(monkeypatch):
    rows,_,_=pinned_bundle();original=c.milp
    def limited(*args,**kwargs):
        result=original(*args,**kwargs);result.status=1;result.success=False;result.message='constructed time limit';return result
    monkeypatch.setattr(c,'milp',limited);diagnostics={}
    result=c._assign(rows,c._groups(rows),set(),SMALL,2,3,reference_records=rows,max_reference_changes=0,diagnostics=diagnostics)
    assert len(result)==6 and diagnostics['optimality_proven'] is False and diagnostics['solver_status']==1
    with pytest.raises(ValueError,match='unresolved'):c._assign(rows,c._groups(rows),set(),SMALL,2,3)


def test_fractional_or_infeasible_incumbent_is_rejected(monkeypatch):
    rows,_,_=pinned_bundle()
    def invalid(cost,**kwargs):return SimpleNamespace(status=1,success=False,message='constructed invalid incumbent',x=np.full(len(cost),.5))
    monkeypatch.setattr(c,'milp',invalid)
    with pytest.raises(ValueError,match='unresolved'):
        c._assign(rows,c._groups(rows),set(),SMALL,2,3,reference_records=rows,max_reference_changes=0)


def test_fixed_records_in_connected_group_cannot_leak_between_splits():
    rows,_,_=pinned_bundle()
    rows[2].source.event_group=rows[0].source.event_group
    with pytest.raises(ValueError,match='infeasible'):
        c._assign(rows,c._groups(rows),set(),SMALL,2,3,reference_records=deepcopy(rows),
                  fixed_record_ids={rows[0].record_id,rows[2].record_id},max_reference_changes=2)


def test_conflicting_soft_alternatives_cannot_both_fill_slots():
    rows=[sample(i)[0] for i in range(3)]
    for row in rows:row.split='train'
    conflict=[(rows[0].record_id,rows[1].record_id)]
    with pytest.raises(ValueError,match='infeasible'):
        c._assign(rows,c._groups(rows),set(),{'train':{'english':3}},10,1,
                  reference_records=rows,max_reference_changes=3,conflicts=conflict)
    for pair in [(rows[0].record_id,'missing'),(rows[0].record_id,rows[0].record_id)]:
        with pytest.raises(ValueError,match='conflict'):
            c._assign(rows,c._groups(rows),set(),{'train':{'english':2}},10,1,
                      reference_records=rows,max_reference_changes=3,conflicts=[pair])


def test_ineligible_hard_fixed_record_is_rejected_before_assembly(tmp_path):
    rows,reviews,sources=pinned_bundle();rows[0].complete=False;rows[0].review_status='draft'
    with pytest.raises(ValueError,match='hard-fixed'):
        c.build_cohort(rows,reviews,sources,tmp_path,output(tmp_path),targets=SMALL,publisher_cap=2,
                       reference_records=deepcopy(rows),fixed_record_ids={rows[0].record_id},max_reference_changes=1)
    assert not output(tmp_path).exists()


def test_integer_incumbent_violating_counts_is_rejected(monkeypatch):
    rows,_,_=pinned_bundle()
    def invalid(cost,**kwargs):
        return SimpleNamespace(status=1,success=False,message='constructed count violation',x=np.zeros(len(cost)))
    monkeypatch.setattr(c,'milp',invalid)
    with pytest.raises(ValueError,match='unresolved'):
        c._assign(rows,c._groups(rows),set(),SMALL,2,3,reference_records=rows,max_reference_changes=0)
