from copy import deepcopy
import pytest

from training.flood_ner.location_repair_v44 import METHODS, object_sha, object_text_sha, propose
from training.flood_ner.location_repair_cases_v44 import location_cases, result
from training.flood_ner.location_repair_cases_v40 import mention


@pytest.mark.parametrize('case', location_cases(), ids=lambda c: c['case_id'])
@pytest.mark.parametrize('method', METHODS)
def test_fictional_expectations(case, method):
    before = deepcopy(case['raw'])
    raw = {k: before[k] for k in ('record_id', 'text', 'mentions')}
    output = propose(raw, method)
    assert result(case, output)['passed']
    assert before == case['raw']
    for p in output['proposals']:
        assert p['provenance_sha256'] == object_sha({k: v for k, v in p.items() if k != 'provenance_sha256'})
        assert before['text'][p['start']:p['end']] == p['text']
        e = p['evidence']; assert before['text'][e['start']:e['end']] == e['text']


@pytest.mark.parametrize('intro,join', [('At the intersection of ', ' and '), ('Sa kanto ng ', ' at '), ('Junction of ', ' and ')])
def test_explicit_intro_and_neural_control_separation(intro, join):
    text = intro+'Áster'+join+'Piña - knee-deep at 6 PM'
    neural = [mention(text, 'Piña', 'CITY')]
    control = deepcopy(neural); control[0]['label'] = 'ROAD'
    out = propose({'record_id': 'fictional-intro', 'text': text, 'mentions': control}, neural_mentions=neural)
    assert out['neural_mentions'] == neural and out['control_mentions'] == control
    assert [(m['text'], m['label']) for m in out['effective_mentions']] == [('Áster', 'ROAD'), ('Piña', 'ROAD')]


@pytest.mark.parametrize('text', ['Áster and Piña - knee-deep', 'Áster - knee-deep', 'QX cor Piña - knee-deep',
                                 '17 Áster cor Piña - knee-deep', 'Áster cor Piña company - knee-deep',
                                 'Áster cor Piña cor Luntian - knee-deep', 'Áster cor - knee-deep'])
def test_no_names_from_capitalization_depth_or_ambiguous_structure(text):
    out = propose({'record_id': 'fictional-abstain', 'text': text, 'mentions': []})
    assert not out['proposals']


def test_one_cross_junction_span_is_not_split():
    text = 'Áster cor Piña - knee-deep'
    raw = {'record_id': 'fictional-overlap', 'text': text, 'mentions': [mention(text, 'Áster cor Piña', 'ROAD')]}
    assert propose(raw)['effective_mentions'] == raw['mentions']


def test_invalid_unicode_slice_and_method_rejected():
    text = '🌧 Áster cor Piña - knee-deep'
    raw = {'record_id': 'fictional-invalid', 'text': text, 'mentions': [mention(text, 'Áster', 'ROAD')]}
    raw['mentions'][0]['start'] -= 1
    with pytest.raises(ValueError): propose(raw)
    with pytest.raises(ValueError): propose({'record_id': 'x', 'text': text, 'mentions': []}, 'unknown')


def test_source_exact_time_and_status_preserved_by_unchanged_context():
    from app.services.news_ner.context_association_v42 import extract
    text = 'As of 6 PM, the following roads are flooded:\nÁster cor Piña - 8 inches, gutter deep\nÁster Road was cleared of floodwater at 7 PM.'
    mentions = [mention(text, 'Áster Road', 'ROAD')]
    raw = {'record_id': 'fictional-times', 'text': text, 'text_sha256': object_text_sha(text), 'publication': None, 'mentions': mentions}
    before = extract(raw); after = extract({**raw, 'mentions': propose({k: raw[k] for k in ('record_id', 'text', 'mentions')})['effective_mentions']})
    sig = lambda g: [(f['value'], f['temporal_role']) for f in g['facts'] if f['kind'] == 'time']
    assert sig(before) == sig(after)
    assert any(f['kind'] == 'status' and f['value'] == 'cleared' for f in after['facts'])
    assert not after['absolute_instants']
