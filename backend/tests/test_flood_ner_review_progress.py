"""Constructed aggregate counts only; no private corpus text or identities."""
from pathlib import Path
import sys
import unittest

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner.review_progress import CoverageCounts, ReviewProgress, build_progress


def counts(en=0, en_negative=0, tag=0, tag_negative=0):
    return CoverageCounts(english_positive=en, english_negative=en_negative,
                          taglish_positive=tag, taglish_negative=tag_negative)


class ProgressTests(unittest.TestCase):
    def sample(self):
        return build_progress(archived=counts(20, 3, 18, 3), conditional=counts(20, 3, 16, 3),
                              strict=counts(10, 1, 5, 1), evidence_package_sha256='a' * 64)

    def test_pending_evidence_does_not_erase_saved_candidate_progress(self):
        report = self.sample()
        self.assertEqual(report.archived_compatible_candidates.total, 44)
        self.assertEqual(report.protocol_conditional_candidates.total, 42)
        self.assertEqual(report.strict_evidence_eligible.total, 17)
        self.assertEqual(report.reviewed_candidate_slots_unfilled, 16)
        self.assertEqual(report.conditional_candidates_pending_evidence, 25)
        self.assertIsNone(report.new_article_collection_requirement)

    def test_cannot_present_strict_deficit_as_candidate_collection_gap(self):
        data = self.sample().model_dump()
        data['reviewed_candidate_slots_unfilled'] = data['strict_eligibility_slots_unfilled']
        with self.assertRaises(ValidationError):
            ReviewProgress.model_validate(data)

    def test_clearance_counts_cannot_exceed_saved_counts(self):
        with self.assertRaises(ValidationError):
            build_progress(archived=counts(1), conditional=counts(2), strict=counts(),
                           evidence_package_sha256='a' * 64)

    def test_nesting_is_checked_per_language_and_polarity(self):
        with self.assertRaises(ValidationError):
            build_progress(archived=counts(10, 0, 10, 3), conditional=counts(5, 1, 5, 1),
                           strict=counts(), evidence_package_sha256='a' * 64)

    def test_pending_protocol_cannot_disappear_from_totals(self):
        data = self.sample().model_dump()
        data['candidates_pending_protocol_clearance'] = 0
        with self.assertRaises(ValidationError):
            ReviewProgress.model_validate(data)

    def test_even_complete_candidate_coverage_cannot_seal_or_train(self):
        full = counts(27, 3, 27, 3)
        report = build_progress(archived=full, conditional=full, strict=full,
                                evidence_package_sha256='a' * 64)
        self.assertEqual(report.reviewed_candidate_slots_unfilled, 0)
        self.assertFalse(report.test_sealed or report.ready_for_training)
        for field in ('test_sealed', 'ready_for_training', 'admission_performed', 'export_performed'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                ReviewProgress.model_validate({**report.model_dump(), field: True})

    def test_labels_urls_text_and_ids_do_not_fit_aggregate_output(self):
        for field in ('candidate_ids', 'urls', 'text', 'annotations', 'titles'):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                ReviewProgress.model_validate({**self.sample().model_dump(), field: 'constructed extra'})

    def test_unknown_references_are_not_an_invented_negative_count(self):
        with self.assertRaises(ValidationError):
            CoverageCounts(english_positive=1, english_negative=None, taglish_positive=1, taglish_negative=0)

    def test_language_and_polarity_quotas_are_preserved(self):
        for vector in ((28, 0, 0, 0), (0, 4, 0, 0), (0, 0, 28, 0), (0, 0, 0, 4)):
            with self.subTest(vector=vector), self.assertRaises(ValidationError):
                counts(*vector)

    def test_counts_and_evidence_digest_are_explicit(self):
        with self.assertRaises(ValidationError):
            build_progress(archived=counts(), conditional=counts(), strict=counts(),
                           evidence_package_sha256='missing evidence')
        with self.assertRaises(ValidationError):
            counts(en=True)


if __name__ == '__main__':
    unittest.main()
