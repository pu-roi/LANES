"""Rendered publisher dates retain days without fabricating timezone instants."""
import pytest

from training.flood_ner.collection import rendered_publication


def versioned_captures(root):
    from datetime import datetime, timezone
    from training.flood_ner.annotation.schema import SourceCapture, text_hash
    from training.flood_ner.sources import json_bytes
    captures = root / 'backend/training/flood_ner/artifacts/captures'
    captures.mkdir(parents=True)
    text = 'Floodwater affected Barangay Alpha in Cebu City. ' * 12
    original = SourceCapture(source_id='same-source', url='https://rmn.ph/flood/',
        publisher='RMN Networks', text=text, text_sha256=text_hash(text),
        capture_version='original-version', article_group='same-article',
        published_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        captured_at=datetime(2026, 10, 14, tzinfo=timezone.utc),
        reuse_terms='not verified', extraction_method='captured-test-html')
    newer = original.model_copy(update={'capture_version': 'newer-version',
        'captured_at': datetime(2026, 10, 15, tzinfo=timezone.utc)})
    for source in (original, newer):
        (captures / (source.capture_version + '.json')).write_bytes(json_bytes(source.model_dump(mode='json')))
    return original, newer, captures


def test_inventory_preserves_same_text_versions_and_original_timestamps(tmp_path):
    from training.flood_ner.sources import inventory_sources
    original, newer, _ = versioned_captures(tmp_path)
    sources, errors = inventory_sources(tmp_path)
    assert not errors
    assert {s.capture_version: s for s in sources} == {
        original.capture_version: original, newer.capture_version: newer}


def test_collection_capture_paths_bind_versions_not_visible_text(tmp_path):
    from training.flood_ner.collection import collect_candidates
    original, newer, captures = versioned_captures(tmp_path)
    entries = collect_candidates([], tmp_path, tmp_path / 'collection')
    assert len(entries) == 2
    for entry in entries:
        expected = captures / (entry['capture_version'] + '.json')
        assert (tmp_path / entry['capture_path']).resolve() == expected.resolve()
    assert {e['captured_at'] for e in entries} == {
        original.captured_at.isoformat(), newer.captured_at.isoformat()}


def test_identical_capture_versions_do_not_count_as_two_reviewed_articles(tmp_path):
    from training.flood_ner.collection import source_entry, validate_reviewed
    original, newer, _ = versioned_captures(tmp_path)
    entries = [source_entry(s) | {'status': 'accepted', 'reviewer': 'AI test',
        'review_notes': ['body reviewed'], 'evidence': [{'start': 0, 'end': len(s.text),
                                                     'sha256': s.text_sha256}]}
               for s in (original, newer)]
    errors = validate_reviewed(entries, {s.capture_version: s for s in (original, newer)})
    assert any('duplicate' in error or 'repeated' in error for error in errors)


@pytest.mark.parametrize('status,expected', [(1, 'remains unresolved'), (2, 'is infeasible')])
def test_selection_diagnostics_distinguish_limits_from_proven_infeasibility(monkeypatch, status, expected):
    from types import SimpleNamespace
    import training.flood_ner.cohort as cohort
    from test_flood_ner_revision import labeled_bundle, tiny_policy
    from test_flood_ner_cohort import SMALL
    records, _, _ = labeled_bundle()
    monkeypatch.setattr(cohort, 'milp', lambda *args, **kwargs:
                        SimpleNamespace(success=False, x=None, status=status, message='diagnostic fixture'))
    with pytest.raises(ValueError, match=expected):
        cohort._assign(records, cohort._groups(records), set(), SMALL, 200, 3, tiny_policy())


@pytest.mark.parametrize('seconds', [0, -1, 3601, True])
def test_invalid_solver_budget_rejected_before_writing(tmp_path, seconds):
    from training.flood_ner.cohort import build_cohort
    with pytest.raises(ValueError, match='time limit'):
        build_cohort([], [], [], tmp_path, tmp_path / 'output', selection_time_limit=seconds)
    assert not (tmp_path / 'output').exists()


def test_explicit_solver_budget_reaches_optimizer_without_relaxing_policy(monkeypatch):
    import training.flood_ner.cohort as cohort
    from test_flood_ner_revision import labeled_bundle, tiny_policy
    from test_flood_ner_cohort import SMALL
    records, _, _ = labeled_bundle()
    actual = cohort.milp
    seen = []
    def inspect(*args, **kwargs):
        seen.append(kwargs['options'])
        return actual(*args, **kwargs)
    monkeypatch.setattr(cohort, 'milp', inspect)
    assignment = cohort._assign(records, cohort._groups(records), set(), SMALL, 200, 3,
                                tiny_policy(), selection_time_limit=300)
    assert len(assignment) == sum(sum(counts.values()) for counts in SMALL.values())
    from training.flood_ner.policy import policy_report
    selected = [r.model_copy(update={'split': assignment[r.record_id]})
                for r in records if r.record_id in assignment]
    assert policy_report(selected, cohort._groups(selected), tiny_policy())['passed']
    assert seen == [{'time_limit': 300, 'mip_rel_gap': 0}]


@pytest.mark.parametrize('separator', ['-', '|'])
def test_philstar_unqualified_clock_remains_date_only(separator):
    header = f'December 16, 2017 {separator} 4:00pm'
    assert rendered_publication([header], 'Philstar') == (header, '2017-12-16')


def test_conflicting_rendered_publication_days_are_rejected():
    with pytest.raises(ValueError, match='conflicting'):
        rendered_publication(['December 16, 2017 | 4:00pm',
                              'December 17, 2017 - 12:00am'], 'Philstar')


def test_other_publisher_cannot_inherit_philstar_date_pattern():
    with pytest.raises(ValueError, match='not verified'):
        rendered_publication(['December 16, 2017 | 4:00pm'], 'GMA News')


@pytest.mark.parametrize('publisher_header', ['INQUIRER.net', 'Philippine Daily Inquirer'])
def test_inquirer_publication_uses_article_byline_day(publisher_header):
    header = f'{publisher_header} / 05:32 PM June 16, 2018'
    assert rendered_publication(['July 10, 2022', header], 'Inquirer') == (header, '2018-06-16')


def test_inquirer_conflicting_byline_dates_are_rejected():
    with pytest.raises(ValueError, match='conflicting'):
        rendered_publication(['INQUIRER.net / 05:32 PM June 16, 2018',
                              'INQUIRER.net / 05:32 PM June 17, 2018'], 'Inquirer')
