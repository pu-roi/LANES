"""Constructed disclosure flags and temporary synthetic evidence only."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner.exposure_review import ExposureScope, review_exposure
from training.flood_ner.research_review import FileBinding, ReviewError, file_hash


class ExposureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.grant = dict(schema='lanes-latest-candidate-reuse-review-v1',
                          proposal_protocol_clarification={'effective_for': 'constructed proposal only'})
        self.grant.update({k: False for k in ('network_allowed', 'collection_allowed', 'admission_allowed',
                                             'seal_allowed', 'export_allowed', 'training_allowed')})
        self.auth = self.write('auth.json', self.grant)
        self.evidence = self.write('disclosure-review.json', {'constructed_scope_review': True})

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding='utf-8')
        return FileBinding(path, file_hash(path))

    def scope(self, **changes):
        data = dict(observed_fields=frozenset({'source_identity', 'selected_role', 'aggregate_counts'}),
                    reviewed_scope_complete=True, observed_fitting_or_tuning=False, global_history_complete=False)
        return ExposureScope(**{**data, **changes})

    def decide(self, scope=None, **changes):
        return review_exposure(scope or self.scope(), authorization=changes.get('authorization', self.auth),
                               evidence=changes.get('evidence', (self.evidence,)))

    def test_identity_only_disclosure_can_be_a_conditional_proposal(self):
        result = self.decide()
        self.assertEqual(result.decision, 'conditional_metadata_only')
        self.assertTrue(result.metadata_visibility_recorded)
        self.assertFalse(result.exhaustive_history_verified or result.certifies_freshness)

    def test_all_substantive_exposure_categories_remain_held(self):
        for field in ('passage_text', 'individual_reference', 'predictions', 'scores'):
            with self.subTest(field=field):
                result = self.decide(self.scope(observed_fields=frozenset({field, 'source_identity'})))
                self.assertEqual((result.decision, result.reason), ('hold', 'substantive_disclosure'))

    def test_fitting_or_tuning_remains_held_even_if_metadata_only(self):
        self.assertEqual(self.decide(self.scope(observed_fitting_or_tuning=True)).reason, 'observed_fitting_or_tuning')

    def test_incomplete_and_empty_disclosure_scope_are_held(self):
        for changes in ({'reviewed_scope_complete': False}, {'observed_fields': frozenset()}):
            with self.subTest(changes=changes):
                self.assertEqual(self.decide(self.scope(**changes)).reason, 'unknown_scope')

    def test_unknown_history_never_disappears_or_unlocks_training(self):
        result = self.decide()
        self.assertFalse(result.exhaustive_history_verified or result.ready_for_training or result.test_sealed)
        self.assertFalse(result.clears_other_eligibility_gates or result.historical_quarantine_rewritten)
        self.assertFalse(result.source_identity_blind_claim)

    def test_no_bound_evidence_or_stale_evidence_rejected(self):
        with self.assertRaises(ReviewError):
            self.decide(evidence=())
        self.evidence.path.write_text('changed')
        with self.assertRaises(ReviewError):
            self.decide()

    def test_unapproved_or_stale_authorization_rejected(self):
        self.auth.path.write_text('{}')
        with self.assertRaises(ReviewError):
            self.decide()
        self.grant['schema'] = 'unapproved'
        with self.assertRaises(ReviewError):
            self.decide(authorization=self.write('new-auth.json', self.grant))

    def test_grant_for_live_or_release_work_is_not_this_review_scope(self):
        self.grant['training_allowed'] = True
        with self.assertRaises(ReviewError):
            self.decide(authorization=self.write('other-scope.json', self.grant))

    def test_free_text_ids_and_coercions_are_not_accepted(self):
        for changes in ({'observed_fitting_or_tuning': 'false'}, {'candidate_id': 'constructed'},
                        {'observed_fields': frozenset({'unknown_field'})}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                self.scope(**changes)


if __name__ == '__main__':
    unittest.main()
