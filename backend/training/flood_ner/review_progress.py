"""Separate preserved candidate coverage from evidence clearance.

These are aggregate reporting contracts, never membership/admission operations.
Candidate coverage cannot authorize collection, sealing, exports or training.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CoverageCounts(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', frozen=True)
    english_positive: int = Field(ge=0, le=27)
    english_negative: int = Field(ge=0, le=3)
    taglish_positive: int = Field(ge=0, le=27)
    taglish_negative: int = Field(ge=0, le=3)

    @property
    def vector(self) -> tuple[int, int, int, int]:
        return (self.english_positive, self.english_negative,
                self.taglish_positive, self.taglish_negative)

    @property
    def total(self) -> int:
        return sum(self.vector)

    @property
    def unfilled_slots(self) -> int:
        return 60 - self.total


class ReviewProgress(BaseModel):
    """All three views must have explicit names; none is a training release."""
    model_config = ConfigDict(strict=True, extra='forbid', frozen=True)
    schema_version: Literal['lanes-review-progress-v1'] = 'lanes-review-progress-v1'
    archived_compatible_candidates: CoverageCounts
    protocol_conditional_candidates: CoverageCounts
    strict_evidence_eligible: CoverageCounts
    evidence_package_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    interpretation: Literal['candidate_coverage_is_not_admission'] = 'candidate_coverage_is_not_admission'
    reviewed_candidate_slots_unfilled: int = Field(ge=0, le=60)
    candidates_pending_protocol_clearance: int = Field(ge=0, le=60)
    conditional_candidates_pending_evidence: int = Field(ge=0, le=60)
    strict_eligibility_slots_unfilled: int = Field(ge=0, le=60)
    new_article_collection_requirement: None = None
    admitted_records: Literal[0] = 0
    test_sealed: Literal[False] = False
    ready_for_training: Literal[False] = False
    admission_performed: Literal[False] = False
    export_performed: Literal[False] = False
    network_operations: Literal[0] = 0

    @model_validator(mode='after')
    def reconcile_views(self) -> ReviewProgress:
        archived, conditional, strict = (self.archived_compatible_candidates,
                                        self.protocol_conditional_candidates,
                                        self.strict_evidence_eligible)
        if not all(a >= c >= s for a, c, s in zip(archived.vector, conditional.vector, strict.vector)):
            raise ValueError('clearance views must be nested for every language/polarity')
        if (self.reviewed_candidate_slots_unfilled != archived.unfilled_slots or
                self.candidates_pending_protocol_clearance != archived.total - conditional.total or
                self.conditional_candidates_pending_evidence != conditional.total - strict.total or
                self.strict_eligibility_slots_unfilled != strict.unfilled_slots):
            raise ValueError('stage-specific progress does not reconcile')
        return self


def build_progress(*, archived: CoverageCounts, conditional: CoverageCounts,
                   strict: CoverageCounts, evidence_package_sha256: str) -> ReviewProgress:
    """Use curator-verified aggregate measurements; never infer missing samples.

    The package digest binds the independently replayed private evidence. Its
    ledger and source identities remain isolated; this helper reports counts.
    """
    return ReviewProgress(
        archived_compatible_candidates=archived, protocol_conditional_candidates=conditional,
        strict_evidence_eligible=strict, evidence_package_sha256=evidence_package_sha256,
        reviewed_candidate_slots_unfilled=archived.unfilled_slots,
        candidates_pending_protocol_clearance=archived.total - conditional.total,
        conditional_candidates_pending_evidence=conditional.total - strict.total,
        strict_eligibility_slots_unfilled=strict.unfilled_slots,
    )
