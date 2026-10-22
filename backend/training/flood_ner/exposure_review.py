"""Scoped disclosure review for a conditional research proposal, never release.

Source metadata visibility and passage/reference use are distinct observations.
This helper cannot clear historical overlap, source-use, annotation or freshness.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .research_review import FileBinding, require

DisclosureField = Literal['source_identity', 'title', 'selected_role', 'aggregate_counts',
                          'passage_text', 'individual_reference', 'predictions', 'scores']
SUBSTANTIVE = frozenset({'passage_text', 'individual_reference', 'predictions', 'scores'})


class ExposureScope(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    observed_fields: frozenset[DisclosureField]
    reviewed_scope_complete: bool
    observed_fitting_or_tuning: bool
    # Missing complete acquisition history is separately recorded and blocks
    # readiness; reviewed disclosures never certify exhaustive non-exposure.
    global_history_complete: bool


class ExposureDisposition(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    schema_version: Literal['lanes-exposure-proposal-decision-v1'] = 'lanes-exposure-proposal-decision-v1'
    decision: Literal['conditional_metadata_only', 'hold']
    reason: Literal['metadata_only_reviewed', 'unknown_scope', 'substantive_disclosure', 'observed_fitting_or_tuning']
    metadata_visibility_recorded: bool
    exhaustive_history_verified: bool
    historical_quarantine_rewritten: Literal[False] = False
    source_identity_blind_claim: Literal[False] = False
    clears_other_eligibility_gates: Literal[False] = False
    certifies_freshness: Literal[False] = False
    test_sealed: Literal[False] = False
    ready_for_training: Literal[False] = False


def review_exposure(scope: ExposureScope, *, authorization: FileBinding,
                    evidence: tuple[FileBinding, ...]) -> ExposureDisposition:
    """Apply only the hash-bound metadata amendment to the reviewed disclosures.

    Bindings identify private reviewed snapshots/decisions; no candidate identity
    or source content enters the returned disposition. Membership still requires
    all unchanged reference, source-use, language, date and grouping checks.
    """
    authorization.verify()
    grant = json.loads(authorization.path.read_text(encoding='utf-8'))
    require(grant.get('schema') == 'lanes-latest-candidate-reuse-review-v1' and
            isinstance(grant.get('proposal_protocol_clarification'), dict), 'scoped proposal amendment absent')
    require(all(grant.get(k) is False for k in ('network_allowed', 'collection_allowed',
                'admission_allowed', 'seal_allowed', 'export_allowed', 'training_allowed')),
            'review-only scope required')
    require(bool(evidence), 'disclosure evidence bindings absent')
    for binding in evidence:
        binding.verify()
    if scope.observed_fitting_or_tuning:
        reason = 'observed_fitting_or_tuning'
    elif scope.observed_fields & SUBSTANTIVE:
        reason = 'substantive_disclosure'
    elif not scope.reviewed_scope_complete or not scope.observed_fields:
        reason = 'unknown_scope'
    else:
        reason = 'metadata_only_reviewed'
    return ExposureDisposition(
        decision='conditional_metadata_only' if reason == 'metadata_only_reviewed' else 'hold',
        reason=reason,
        metadata_visibility_recorded=bool(scope.observed_fields - SUBSTANTIVE),
        exhaustive_history_verified=scope.global_history_complete,
    )
