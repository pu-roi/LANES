"""Constructed evidence fragments only; no Gemini chats or private sources."""
from dataclasses import replace
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from training.flood_ner.receipt_evidence import (
    EvidenceError, EvidenceFragment, ReceiptClaim, assess_receipts, raw_identity_union,
)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.query = b'constructed query'
        self.result = b'constructed original result'
        self.origin = self.root / 'native-origin.txt'
        self.origin.write_bytes(b'private prefix\n' + self.query + b'\n' + self.result + b'\nprivate suffix')
        self.query_fragment = self.fragment('query', self.query)
        self.result_fragment = self.fragment('result', self.result)
        self.claim = ReceiptClaim(0, self.query_fragment, self.result_fragment,
                                  'native_tool_record', 'claimed_complete', True, True)
        self.expected = (hashlib.sha256(self.query).hexdigest(),)

    def fragment(self, name, value):
        raw = self.origin.read_bytes()
        path = self.root / (name + '.txt')
        path.write_bytes(value)
        start = raw.index(value)
        return EvidenceFragment(path, hashlib.sha256(value).hexdigest(), self.origin,
                                hashlib.sha256(raw).hexdigest(), start, start + len(value))

    def assess(self, claim=None):
        return assess_receipts(self.expected, [claim or self.claim])[0]

    def test_matching_exact_fragments_never_unlock_any_gate(self):
        result = self.assess()
        self.assertEqual(result.disposition, 'pending_provenance_review')
        for name in ('accounting_verified', 'history_verified', 'ready_for_admission',
                     'ready_for_training', 'test_sealed'):
            self.assertFalse(getattr(result, name))

    def test_missing_all_eleven_returns_eleven_holds(self):
        rows = assess_receipts(self.expected * 11, [])
        self.assertEqual(len(rows), 11)
        self.assertTrue(all(x.disposition == 'hold' and x.reason == 'missing_original_pair' for x in rows))

    def test_exact_query_fingerprint_required(self):
        rows = assess_receipts(('0' * 64,), [self.claim])
        self.assertEqual(rows[0].reason, 'query_fingerprint_mismatch')

    def test_stale_origin_and_fragment_bindings_remain_held(self):
        self.query_fragment.path.write_bytes(b'changed')
        self.assertEqual(self.assess().reason, 'invalid_or_stale_fragment')
        self.query_fragment.path.write_bytes(self.query)
        self.origin.write_bytes(self.origin.read_bytes() + b'changed')
        self.assertEqual(self.assess().reason, 'invalid_or_stale_fragment')

    def test_forged_range_cannot_bind_rewritten_text(self):
        claim = replace(self.claim, query=replace(self.query_fragment, start_byte=0,
                                                 end_byte=len(self.query)))
        self.assertEqual(self.assess(claim).reason, 'invalid_or_stale_fragment')

    def test_summary_citations_regeneration_and_unknown_are_not_originals(self):
        for kind in ('conversation_summary', 'citation_list', 'regenerated', 'unknown'):
            with self.subTest(kind=kind):
                result = self.assess(replace(self.claim, record_kind=kind))
                self.assertEqual(result.reason, 'not_an_original_tool_record')
                self.assertFalse(result.accounting_verified)

    def test_partial_truncated_and_unknown_results_remain_held(self):
        for completeness in ('partial', 'truncated', 'unknown'):
            with self.subTest(completeness=completeness):
                self.assertEqual(self.assess(replace(self.claim, completeness=completeness)).reason,
                                 'incomplete_or_unknown_result')

    def test_duplicate_claims_and_reused_result_fragments_are_held(self):
        rows = assess_receipts(self.expected, [self.claim, self.claim])
        self.assertEqual(rows[0].reason, 'duplicate_or_ambiguous_pair')
        rows = assess_receipts(self.expected * 2, [self.claim, replace(self.claim, expected_index=1)])
        self.assertTrue(all(x.reason == 'reused_result_fragment' for x in rows))

    def test_missing_timestamps_or_pair_links_are_held(self):
        for field in ('timestamps_present', 'pair_link_reviewed'):
            with self.subTest(field=field):
                self.assertEqual(self.assess(replace(self.claim, **{field: False})).reason,
                                 'missing_timing_or_pair_link')

    def test_unmatched_claims_and_coerced_review_flags_rejected(self):
        for change in ({'expected_index': 1}, {'expected_index': True}, {'timestamps_present': 'true'},
                       {'record_kind': 'a model said original'}, {'completeness': 'complete'}):
            with self.subTest(change=change), self.assertRaises(EvidenceError):
                self.assess(replace(self.claim, **change))

    def test_whole_origin_cannot_be_passed_as_isolated_fragment(self):
        raw = self.origin.read_bytes()
        path = self.root / 'whole-copy.txt'
        path.write_bytes(raw)
        h = hashlib.sha256(raw).hexdigest()
        fragment = EvidenceFragment(path, h, self.origin, h, 0, len(raw))
        with self.assertRaises(EvidenceError):
            fragment.verify()
        with self.assertRaises(EvidenceError):
            replace(fragment, path=self.origin).verify()

    def test_assessment_outputs_contain_only_fixed_dispositions(self):
        result = self.assess()
        rendered = repr(result)
        self.assertNotIn(self.query.decode(), rendered)
        self.assertNotIn(self.result.decode(), rendered)
        self.assertNotIn(str(self.origin), rendered)

    def test_alias_union_keeps_raw_variants_without_double_counting_identicals(self):
        a = 'https://example.test/story'
        values = raw_identity_union([[a, a, a + '?mobile=1'], ['https://m.example.test/story', a + '#part']])
        self.assertEqual(len(values), 4)
        self.assertIn(a + '?mobile=1', values)

    def test_identity_union_rejects_implicit_batches_or_credentials(self):
        for batches in (['https://example.test/story'], [[' https://example.test/story']],
                        [['https://user:secret@example.test/story']], [['not-a-url']], [[None]]):
            with self.subTest(batches=batches), self.assertRaises(EvidenceError):
                raw_identity_union(batches)


if __name__ == '__main__':
    unittest.main()
