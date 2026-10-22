"""Constructed texts only. No private candidates, predictions or network."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner.annotation.schema import SourceCapture, text_hash
from training.flood_ner.export import corpus_tokenizer
from training.flood_ner.research_review import (
    FileBinding, GuardResults, REQUIRED_GATES, ReviewCandidate, ReviewError, SafeReviewStatus,
    SafeVerificationManifest, SelectionResult, build_status, compatible, export_review, file_hash, group_keys,
    run_guards, select_joint, validate_candidate, validate_reference, validate_safe_pair,
)
from training.flood_ner import research_review


class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nlp = corpus_tokenizer()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'source-review.json'
        self.path.write_text('{"constructed_review":true}', encoding='utf-8')
        self.binding = FileBinding(self.path, file_hash(self.path))

    def source(self, text='Sample City flooded.', key='a'):
        # Captured schema exercised with synthetic evidence, never a corpus fixture.
        return SourceCapture(source_id=key, url=f'https://example.org/{key}', publisher='Constructed publisher',
            text=text, text_sha256=text_hash(text), raw_sha256='a' * 64, capture_version='fixture-v1',
            published_at=datetime(2025, 1, 1, tzinfo=timezone.utc), article_group=key,
            event_group='event-' + key, syndication_group='syndication-' + key,
            reuse_terms='Constructed test only', extraction_method='constructed-test')

    def proposal(self, source=None, *, rid='r', language='english', start=0, end=None, entities=None):
        source = source or self.source()
        end = len(source.text) if end is None else end
        text = source.text[start:end]
        if entities is None:
            entities = [{'start': 0, 'end': 11, 'label': 'CITY', 'text': 'Sample City'}]
        return dict(record_id=rid, language=language, passage_start=start, passage_end=end,
            text=text, text_sha256=text_hash(text), source_text_sha256=source.text_sha256,
            source_raw_sha256=source.raw_sha256, expected_entities=entities,
            annotation_reference_complete=True, candidate_negative=not entities,
            annotator='constructed-annotator', reviewer='constructed-reviewer')

    def candidate(self, key='a', language='english', negative=False):
        text = f'Sample City flooded {key}.' if not negative else f'Rain continued {key}.'
        source = self.source(text, key)
        record = validate_reference(self.proposal(source, rid=key, language=language,
                        entities=[] if negative else None), source, self.nlp)
        return ReviewCandidate(record, {k: True for k in REQUIRED_GATES},
                               {k: (self.binding,) for k in REQUIRED_GATES})

    def status(self):
        row = self.candidate()
        result = select_joint([row], [row.record.record_id], self.nlp)
        return build_status(result, guards=run_guards({'fresh': lambda: None}),
                            accounting_verified=False, history_verified=False, validated_records=[row.record])

    def test_explicit_source_exact_unicode_locations(self):
        source = self.source('Élan City flooded.')
        p = self.proposal(source, entities=[{'start': 0, 'end': 9, 'text': 'Élan City', 'label': 'CITY'}])
        record = validate_reference(p, source, self.nlp)
        self.assertEqual(record.entities[0].end, 9)
        self.assertEqual(record.annotation_profile, 'location-only-v1')
        self.assertIsNone(record.split)

    def test_missing_null_and_incomplete_references_never_negatives(self):
        for value in ('missing', None, []):
            p = self.proposal(entities=[])
            if value == 'missing':
                p.pop('expected_entities')
            else:
                p['expected_entities'] = value
            if value == []:
                p['annotation_reference_complete'] = False
            with self.subTest(value=value), self.assertRaises(ReviewError):
                validate_reference(p, self.source(), self.nlp)

    def test_genuine_negative_requires_complete_empty_and_consistent_flags(self):
        source = self.source('Rain continued.')
        p = self.proposal(source, entities=[])
        self.assertEqual(validate_reference(p, source, self.nlp).entities, [])
        for updates in ({'candidate_negative': False}, {'is_negative': False}, {'candidate_negative': None}):
            with self.subTest(updates=updates), self.assertRaises(ReviewError):
                validate_reference({**p, **updates}, source, self.nlp)

    def test_first_occurrence_only_rejected(self):
        source = self.source('Sample City flooded. Sample City recovered.')
        with self.assertRaisesRegex(ReviewError, 'repeated'):
            validate_reference(self.proposal(source), source, self.nlp)

    def test_each_repeated_occurrence_has_explicit_span_and_type(self):
        source = self.source('Sample City flooded. Sample City recovered.')
        p = self.proposal(source)
        p['expected_entities'].append({'start': 21, 'end': 32, 'text': 'Sample City', 'label': 'LOCAL_AREA'})
        record = validate_reference(p, source, self.nlp)
        self.assertEqual([e.label for e in record.entities], ['CITY', 'LOCAL_AREA'])

    def test_ambiguous_occurrence_cannot_be_ignored(self):
        source = self.source('Sample City flooded. Sample City recovered.')
        omission = dict(start=21, end=32, text='Sample City', reason='ambiguous type')
        with self.assertRaisesRegex(ReviewError, 'held'):
            validate_reference(self.proposal(source), source, self.nlp, ignored_occurrences=[omission])

    def test_nonentity_omission_requires_bound_review(self):
        source = self.source('Sample City flooded. Sample City is a fictional product.')
        omission = dict(start=21, end=32, text='Sample City', reason='reviewed product name in constructed source',
                        decision='not_an_entity', evidence=(self.binding,))
        record = validate_reference(self.proposal(source), source, self.nlp, ignored_occurrences=[omission])
        self.assertEqual(len(record.entities), 1)

    def test_source_hash_passage_offsets_and_tokenizer_rejected(self):
        for updates in ({'source_raw_sha256': 'b' * 64}, {'source_text_sha256': 'b' * 64},
                        {'text_sha256': 'b' * 64}, {'passage_start': 1},
                        {'expected_entities': [{'start': 1, 'end': 6, 'text': 'ample', 'label': 'CITY'}]}):
            with self.subTest(updates=updates), self.assertRaises(ReviewError):
                validate_reference({**self.proposal(), **updates}, self.source(), self.nlp)

    def test_missing_raw_source_hash_remains_held(self):
        source = self.source().model_copy(update={'raw_sha256': None})
        with self.assertRaisesRegex(ReviewError, 'raw hash'):
            validate_reference(self.proposal(source), source, self.nlp)

    def test_schema_default_empty_entities_is_not_reviewed_negative(self):
        row = self.candidate(negative=True)
        payload = row.record.model_dump()
        payload.pop('entities')
        record = type(row.record).model_validate(payload)
        with self.assertRaisesRegex(ReviewError, 'missing reference'):
            validate_candidate(replace(row, record=record), self.nlp, frozenset())

    def test_non_location_label_and_overlapping_spans_rejected(self):
        for entities in ([{'start': 0, 'end': 11, 'text': 'Sample City', 'label': 'DEPTH'}],
                         [{'start': 0, 'end': 11, 'text': 'Sample City', 'label': 'CITY'},
                          {'start': 7, 'end': 11, 'text': 'City', 'label': 'CITY'}]):
            with self.subTest(entities=entities), self.assertRaises(ReviewError):
                validate_reference(self.proposal(entities=entities), self.source(), self.nlp)

    def test_each_eligibility_gate_required_before_selection(self):
        row = self.candidate()
        for gate in REQUIRED_GATES:
            for missing_evidence in (False, True):
                eligibility = dict(row.eligibility)
                evidence = dict(row.evidence)
                if missing_evidence:
                    evidence.pop(gate)
                else:
                    eligibility[gate] = False
                result = select_joint([replace(row, eligibility=eligibility, evidence=evidence)], ['a'], self.nlp)
                self.assertEqual(result.selected, ())
                self.assertIn('a', result.baseline_removed)

    def test_stale_eligibility_evidence_rejected(self):
        row = self.candidate()
        self.path.write_text('changed')
        with self.assertRaises(ReviewError):
            validate_candidate(row, self.nlp, frozenset())

    def test_unresolved_groups_and_outside_dates_rejected(self):
        for updates in ({'event_group': 'pending-review'}, {'syndication_group': None},
                        {'published_at': None}, {'published_at': datetime(2026, 10, 15, tzinfo=timezone.utc)}):
            row = self.candidate()
            row.record.source = row.record.source.model_copy(update=updates)
            with self.subTest(updates=updates), self.assertRaises(ReviewError):
                validate_candidate(row, self.nlp, frozenset())

    def test_fitted_exposure_and_history_groups_rejected(self):
        row = self.candidate()
        for key in group_keys(row.record):
            with self.subTest(key=key), self.assertRaises(ReviewError):
                validate_candidate(row, self.nlp, frozenset({key}))

    def test_held_and_nonresearch_members_rejected(self):
        row = self.candidate()
        self.assertFalse(select_joint([replace(row, holds=('held',))], ['a'], self.nlp).selected)
        row.record.split = 'test'
        self.assertFalse(select_joint([row], ['a'], self.nlp).selected)

    def test_duplicate_id_passage_and_missing_baseline_rejected(self):
        row = self.candidate()
        for rows, baseline in (([row, row], []), ([row], ['unknown'])):
            with self.assertRaises(ReviewError):
                select_joint(rows, baseline, self.nlp)
        other = replace(row, record=row.record.model_copy(update={'record_id': 'b'}))
        with self.assertRaises(ReviewError):
            compatible([row, other])

    def test_overlapping_passages_rejected(self):
        source = self.source('Sample City flooded. Sample City recovered.')
        a = self.proposal(source, rid='a', end=20)
        b = self.proposal(source, rid='b', start=12, entities=[{'start': 9, 'end': 20, 'text': 'Sample City', 'label': 'CITY'}])
        first, second = self.candidate('a'), self.candidate('b')
        first = replace(first, record=validate_reference(a, source, self.nlp))
        second = replace(second, record=validate_reference(b, source, self.nlp))
        with self.assertRaisesRegex(ReviewError, 'overlapping'):
            compatible([first, second])

    def test_same_article_different_capture_versions_rejected(self):
        a, b = self.candidate('a'), self.candidate('b')
        b.record.source.article_group = a.record.source.article_group
        with self.assertRaisesRegex(ReviewError, 'versions'):
            compatible([a, b])

    def test_four_nonoverlapping_windows_still_exceed_article_cap(self):
        source = self.source('First. Second. Third. Fourth.')
        rows = []
        for i, (start, end) in enumerate([(0, 6), (7, 14), (15, 21), (22, 29)]):
            # Four positives not necessary: article guard fires independently of negative quotas.
            text = source.text[start:end]
            p = self.proposal(source, rid=str(i), start=start, end=end,
                entities=[{'start': 0, 'end': len(text)-1, 'text': text[:-1], 'label': 'LOCAL_AREA'}])
            rows.append(replace(self.candidate(str(i)), record=validate_reference(p, source, self.nlp)))
        with self.assertRaisesRegex(ReviewError, 'cap'):
            compatible(rows)

    def test_mutually_exclusive_alternatives(self):
        a, b = self.candidate('a'), self.candidate('b')
        a = replace(a, alternatives=frozenset({'b'}))
        self.assertEqual(len(select_joint([a, b], [], self.nlp).selected), 1)

    def test_joint_selection_does_not_lose_later_compatible_witness(self):
        a, b, c = [self.candidate(k) for k in 'abc']
        a = replace(a, alternatives=frozenset({'b', 'c'}))
        result = select_joint([a, b, c], [], self.nlp)
        self.assertEqual({r.record.record_id for r in result.selected}, {'b', 'c'})

    def test_search_exhaustion_never_certifies_feasibility(self):
        with self.assertRaisesRegex(ReviewError, 'limit'):
            select_joint([self.candidate()], [], self.nlp, state_limit=1)

    def test_guard_counts_come_from_execution_and_failures_block(self):
        def fail():
            raise ValueError('constructed guard failure')
        guards = run_guards({'ok': lambda: None, 'fail': fail})
        self.assertEqual((guards.passed, guards.failed), (1, 1))
        with self.assertRaises(ReviewError):
            run_guards({})
        row = self.candidate()
        selection = select_joint([row], [], self.nlp)
        with self.assertRaisesRegex(ReviewError, 'executed'):
            build_status(selection, guards=GuardResults(27, 0), accounting_verified=True,
                         history_verified=True, validated_records=[row.record])
        result = build_status(selection, guards=guards, accounting_verified=True,
                              history_verified=True, validated_records=[row.record])
        self.assertFalse(result.ready_for_admission)
        self.assertIn('guards', result.blocker_codes)

    def test_incorrect_quotas_and_forged_readiness_rejected(self):
        data = self.status().model_dump()
        for updates in ({'test_sealed': True}, {'ready_for_training': True}, {'ready_for_admission': True},
                        {'coverage_complete': True}, {'conditional_test': 60}, {'guard_checks_passed': 0},
                        {'english_genuine_negative': 4}, {'english_positive': 28}, {'missing_taglish_positive': 0}):
            with self.subTest(updates=updates), self.assertRaises(ValidationError):
                SafeReviewStatus.model_validate({**data, **updates})

    def test_candidate_content_fields_rejected_by_safe_schema(self):
        data = self.status().model_dump()
        for key in ('candidate_ids', 'url', 'title', 'text', 'annotations', 'path', 'reference'):
            with self.subTest(key=key), self.assertRaises(ValidationError):
                SafeReviewStatus.model_validate({**data, key: 'constructed leak'})

    def test_status_requires_actual_validated_reference_members(self):
        row = self.candidate()
        selection = select_joint([row], [], self.nlp)
        with self.assertRaises(ReviewError):
            build_status(selection, guards=run_guards({'ok': lambda: None}), accounting_verified=False,
                         history_verified=False, validated_records=[])

    def test_fabricated_selection_and_postselection_mutation_rejected(self):
        row = self.candidate()
        selection = SelectionResult((row,), {}, {}, 27)
        for mutate in (False, True):
            if mutate:
                selection = select_joint([row], [], self.nlp)
                row.record.source.event_group = 'changed-after-review'
            with self.subTest(mutate=mutate), self.assertRaisesRegex(ReviewError, 'selection evidence'):
                build_status(selection, guards=run_guards({'ok': lambda: None}), accounting_verified=False,
                             history_verified=False, validated_records=[row.record])

    def test_direct_candidate_cannot_bypass_repeated_occurrence_review(self):
        row = self.candidate()
        row.record.text = row.record.source.text = 'Sample City flooded. Sample City recovered.'
        row.record.text_sha256 = row.record.source.text_sha256 = text_hash(row.record.text)
        row.record.passage_end = len(row.record.text)
        result = select_joint([row], ['a'], self.nlp)
        self.assertEqual(result.selected, ())
        self.assertIn('repeated', result.rejected['a'])

    def test_complete_selection_does_not_unlock_training_or_sealing(self):
        rows = []
        for language, positives, negatives in [('english', 27, 3), ('taglish', 27, 3)]:
            rows += [self.candidate(f'{language}-p{i}', language) for i in range(positives)]
            rows += [self.candidate(f'{language}-n{i}', language, True) for i in range(negatives)]
        selection = select_joint(rows, [r.record.record_id for r in rows], self.nlp)
        status = build_status(selection, guards=run_guards({'ok': lambda: None}), accounting_verified=False,
                              history_verified=False, validated_records=[r.record for r in rows])
        self.assertTrue(status.coverage_complete)
        self.assertFalse(status.ready_for_admission or status.test_sealed or status.ready_for_training)

    def test_export_always_rejected_without_creating_destination(self):
        destination = Path(self.temp.name) / 'test.spacy'
        with self.assertRaisesRegex(ReviewError, 'Review-only'):
            export_review([], destination)
        self.assertFalse(destination.exists())

    def test_safe_companion_is_allowlisted_and_bound_to_actual_status(self):
        status = self.status()
        status_bytes = status.model_dump_json().encode('utf-8')
        proof = {key: 0 for key in SafeVerificationManifest.model_fields}
        proof.update(schema_version='lanes-repaired-research-verification-v1', safe_for_parent=True,
            aggregate_status_sha256=hashlib.sha256(status_bytes).hexdigest(), private_output_manifest_sha256='c'*64,
            authorization_sha256='a'*64, review_module_sha256=file_hash(Path(research_review.__file__)),
            frozen_tokenizer_sha256='b'*64, historical_baseline=1, additional_unknown_exposure_count=None,
            original_v5_tool_receipts_verified=False, new_network_operations=0, accounting_verified=False,
            history_verified=False, test_sealed=False, admission_performed=False, export_performed=False,
            inference_performed=False, training_performed=False, upload_performed=False, push_performed=False,
            training_ready=False, human_gold=False, contains_source_text_urls_titles_entities_or_individual_labels=False,
            completed=True)
        for key in ('conditional_test', 'baseline_members_removed', 'complete_references_checked',
                    'guard_checks_passed', 'guard_checks_failed'):
            proof[key] = getattr(status, key)
        def check(data):
            return validate_safe_pair(status_bytes, json.dumps(data).encode(),
                                      authorization_sha256='a'*64, frozen_tokenizer_sha256='b'*64)
        self.assertEqual(check(proof)[0], status)
        for updates in ({'candidate_ids': ['private']}, {'conditional_test': 60},
                        {'aggregate_status_sha256': 'd'*64}, {'review_module_sha256': 'd'*64},
                        {'private_output_manifest_sha256': 'https://example.org/private'}):
            with self.subTest(updates=updates), self.assertRaises((ValueError, ReviewError)):
                check({**proof, **updates})


if __name__ == '__main__':
    unittest.main()
