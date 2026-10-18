"""Offline checks for explicitly extracted original evidence fragments.

No Gemini export format or backend completeness guarantee is assumed. A pair of
unchanged fragments can support later isolated provenance review; these checks
never certify acquisition accounting, independence, or release readiness.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Iterable
from urllib.parse import urlsplit


class EvidenceError(ValueError):
    pass


def file_sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


@dataclass(frozen=True)
class EvidenceFragment:
    path: Path
    sha256: str
    origin: Path
    origin_sha256: str
    start_byte: int
    end_byte: int

    def verify(self) -> None:
        if not all(isinstance(x, str) and re.fullmatch('[a-f0-9]{64}', x)
                   for x in (self.sha256, self.origin_sha256)):
            raise EvidenceError('invalid fragment binding')
        if (type(self.start_byte) is not int or type(self.end_byte) is not int or
                not 0 <= self.start_byte < self.end_byte <= self.origin.stat().st_size):
            raise EvidenceError('invalid exact byte range')
        if self.path.resolve() == self.origin.resolve():
            raise EvidenceError('whole origin is not an extracted fragment')
        if self.start_byte == 0 and self.end_byte == self.origin.stat().st_size:
            raise EvidenceError('whole origin disclosure prohibited')
        if file_sha256(self.origin) != self.origin_sha256 or file_sha256(self.path) != self.sha256:
            raise EvidenceError('stale evidence binding')
        value = self.path.read_bytes()
        with self.origin.open('rb') as stream:
            stream.seek(self.start_byte)
            original = stream.read(self.end_byte - self.start_byte)
        if value != original or not value.strip():
            raise EvidenceError('fragment differs from original bytes')


@dataclass(frozen=True)
class ReceiptClaim:
    expected_index: int
    query: EvidenceFragment
    result: EvidenceFragment
    record_kind: str
    completeness: str
    timestamps_present: bool
    pair_link_reviewed: bool


@dataclass(frozen=True)
class ReceiptAssessment:
    expected_index: int
    disposition: str
    reason: str
    accounting_verified: bool = False
    history_verified: bool = False
    ready_for_admission: bool = False
    ready_for_training: bool = False
    test_sealed: bool = False


def assess_receipts(expected_query_hashes: tuple[str, ...],
                    claims: Iterable[ReceiptClaim]) -> tuple[ReceiptAssessment, ...]:
    """Match exact query fragments without interpreting whole conversations.

    record_kind and completeness are review claims, not facts inferred from a
    model's wording. Even a matching native pair remains pending verification
    of origin, result completeness, publisher requests and cumulative accounting.
    """
    if not expected_query_hashes or not all(isinstance(x, str) and re.fullmatch('[a-f0-9]{64}', x)
                                           for x in expected_query_hashes):
        raise EvidenceError('expected fingerprints required')
    groups: dict[int, list[ReceiptClaim]] = {i: [] for i in range(len(expected_query_hashes))}
    for claim in claims:
        if type(claim.expected_index) is not int or claim.expected_index not in groups:
            raise EvidenceError('unmatched evidence scope')
        if (type(claim.timestamps_present) is not bool or type(claim.pair_link_reviewed) is not bool or
                claim.record_kind not in {'native_tool_record', 'conversation_summary', 'citation_list',
                                          'regenerated', 'unknown'} or
                claim.completeness not in {'claimed_complete', 'partial', 'truncated', 'unknown'}):
            raise EvidenceError('unsupported receipt determination')
        groups[claim.expected_index].append(claim)
    results: list[ReceiptAssessment] = []
    used_result_fragments: set[tuple[str, int, int]] = set()
    repeated_fragments: set[tuple[str, int, int]] = set()
    for grouped in groups.values():
        for claim in grouped:
            identity = (claim.result.origin_sha256, claim.result.start_byte, claim.result.end_byte)
            if identity in used_result_fragments:
                repeated_fragments.add(identity)
            used_result_fragments.add(identity)
    for index, grouped in groups.items():
        reason = 'missing_original_pair'
        disposition = 'hold'
        if len(grouped) > 1:
            reason = 'duplicate_or_ambiguous_pair'
        elif grouped:
            claim = grouped[0]
            identity = (claim.result.origin_sha256, claim.result.start_byte, claim.result.end_byte)
            try:
                claim.query.verify()
                claim.result.verify()
                if claim.query.sha256 != expected_query_hashes[index]:
                    reason = 'query_fingerprint_mismatch'
                elif identity in repeated_fragments:
                    reason = 'reused_result_fragment'
                elif claim.record_kind != 'native_tool_record':
                    reason = 'not_an_original_tool_record'
                elif claim.completeness != 'claimed_complete':
                    reason = 'incomplete_or_unknown_result'
                elif not claim.timestamps_present or not claim.pair_link_reviewed:
                    reason = 'missing_timing_or_pair_link'
                else:
                    disposition = 'pending_provenance_review'
                    reason = 'exact_fragments_only_not_accounting_clearance'
            except (EvidenceError, OSError):
                reason = 'invalid_or_stale_fragment'
        results.append(ReceiptAssessment(index, disposition, reason))
    return tuple(results)


def raw_identity_union(batches: Iterable[Iterable[str]]) -> tuple[str, ...]:
    """Keep mobile/query/fragment/raw aliases distinct; never canonicalize/refund."""
    identities: set[str] = set()
    for batch in batches:
        if isinstance(batch, (str, bytes)):
            raise EvidenceError('explicit identity batches required')
        for value in batch:
            if not isinstance(value, str) or not value or value != value.strip():
                raise EvidenceError('malformed raw identity')
            try:
                parsed = urlsplit(value)
                valid = parsed.scheme in {'http', 'https'} and parsed.hostname and not (parsed.username or parsed.password)
            except ValueError:
                valid = False
            if not valid or re.search(r'\s', value):
                raise EvidenceError('malformed raw identity')
            identities.add(value)
    return tuple(sorted(identities))
