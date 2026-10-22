"""Evidence guards for AI contextual review, separate from runtime parsing."""
from __future__ import annotations

import re

from .schema import Fact, Span


def reviewed_access_fact(fact_id: str, evidence: Span) -> Fact:
    """Interpret one explicitly selected access phrase, without assigning a place.

    Callers must supply the source-exact phrase and review its target separately.
    Unsupported or mixed statements require review rather than a guessed rule.
    """
    text = evidence.text.strip().rstrip('.;')
    match = re.fullmatch(r'(not\s+)?passable(?:\s+to\s+(.+?))?(?:\s*\((?:NPATV|PATV)\))?', text, re.I)
    if match is None:
        raise ValueError('access review requires one explicit passable/not-passable phrase')
    negative, vehicles = bool(match[1]), (match[2] or '').casefold()
    if re.search(r'\bpassable\b|[;.!?]', vehicles):
        raise ValueError('mixed access statements require separate source review')
    all_vehicles = bool(re.fullmatch(r'all(?:\s+types?\s+of)?\s+vehicles', vehicles))
    light_vehicles = bool(re.fullmatch(r'light\s+vehicles', vehicles))
    if negative:
        value = 'impassable_all' if all_vehicles else 'light_vehicle_closed' if light_vehicles else 'unknown'
    else:
        value = 'passable_all' if all_vehicles else 'passable_unspecified'
    return Fact(id=fact_id, kind='access', value=value, evidence=[evidence],
                qualifiers=['Vehicle restriction retained in exact source phrase; place association requires separate review.'],
                uncertainty=['Reported closure; vehicle scope unspecified.'] if negative and value == 'unknown' else [])


def contextual_semantic_errors(fact: Fact) -> list[str]:
    """Reject explicit self-contradictions; broad source semantics still need review."""
    errors: list[str] = []
    if fact.kind == 'access':
        # Only a complete isolated phrase establishes this guard's scope.
        # A whole passage can contain different access rules for several roads.
        for evidence in fact.evidence:
            try:
                expected = reviewed_access_fact(fact.id, evidence)
            except ValueError:
                continue
            if expected.value != fact.value:
                errors.append(f'fact {fact.id}: access value contradicts explicit reviewed phrase')
    if fact.kind == 'time' and fact.temporal_role in {'onset', 'clearance'}:
        for qualifier in fact.qualifiers:
            if re.search(r'\bnot\s+(?:a\s+)?flood\s+(?:onset|clearance)\b', qualifier, re.I):
                errors.append(f'fact {fact.id}: flood temporal role contradicts non-flood qualifier')
                break
    return errors
