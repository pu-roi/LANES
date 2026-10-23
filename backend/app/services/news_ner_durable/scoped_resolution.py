"""Versioned, deterministic passage roles and row-local semantic outcomes.

Hints describe source layout, not new facts. No citations are inserted or repaired.
The original strict validator still decides whether a provider row is supported.
"""
from __future__ import annotations

import re

from .contracts import sha
from .fields import CLOCK, _dates
from .resolution import (ResolutionError, _access_supported, _contains, _spans,
                         quote_options, resolve_rows, resolve_time, targets, editorial_prefix)
from app.services.news_evidence_policy import has_flood_observation
from app.services.taglish_extraction_service import CONDITION_SUBSIDED, FORECAST_PATTERNS, NEGATION_PATTERNS

VERSION = 'native-gemini-resolution-v2'
CONTRACT = 'scoped-quote-options-v2'

INSTRUCTIONS = """
SCOPED EVIDENCE CONTRACT v2:
source_layout is deterministic navigation help, NOT proof that a fact applies to a road.
Every evidence array must independently cite all needed passages. No evidence is added by the backend.
place_evidence: cite target_passages for this EXACT occurrence plus its supported city/barangay.
status_evidence: cite this target AND affirmative flooding wording (e.g. the list introduction).
time_evidence: cite BOTH the date passage AND the clock passage AND this target when separate.
Returning date_text from the title but citing only an 'as of' clock heading will be rejected.
depth_evidence: cite this target and its governing depth text. Do not borrow a different list's heading.
access_evidence and section_evidence: cite the target-specific restriction or section, never another road's.
A standalone locality heading followed by roads supplies context, not an independent flooded location.
For such a context-only CITY, BARANGAY or PROVINCE target return unsupported; preserve its row.
An actual city/barangay-only flooding statement CAN be observed; it is not a context-only heading.
Repeated locality names have different source occurrences. Use the correct occurrence and list bounds.
Source layout hints never authorize transferring facts across cities, depth headings or later updates.
For example, with date in option 0, flooded-list introduction 1, city/clock heading 2,
depth heading 3, barangay heading 4 and a road in 5: place [2,4,5], status [1,5],
time [0,2,5], shared depth [3,5] can support that road IF the complete article confirms it.
Do not copy example indices; use this article's actual options. Unsupported facts stay unknown.
"""


def source_layout(text: str, candidates: list[dict]) -> dict:
    """Conservative heading recognition; narrative paragraphs remain unscoped.

    Only standalone, source-anchored locality headings with a subsequent bullet
    list are classified as context. Depth and city changes reset child headings.
    All date candidates remain alternatives: the provider must select and cite.
    """
    options = quote_options(text)
    occurrences = {m['id']: [i for i, q in enumerate(options)
                            if q['start'] <= m['start'] < m['end'] <= q['end']] for m in candidates}
    headings = {}
    depth_heads = set()
    for i, q in enumerate(options):
        line = q['quote'].strip()
        if (len(line) <= 120 and re.match(r'^[^\w]*(?:waist|tire|knee|half\s+knee|ankle|gutter)[ -]deep\b', line, re.I)):
            depth_heads.add(i)
        localities = [m for m in candidates if occurrences[m['id']] == [i]
                      and m['label'] in {'CITY', 'BARANGAY', 'PROVINCE'}]
        for m in localities:
            remainder = line.replace(m['text'], '', 1).strip(' \t:,-')
            # An optional '(as of ...)' clock is part of a locality heading.
            if remainder and not re.fullmatch(r'\(as of [^\n]+\)', remainder, re.I):
                continue
            following = [p['quote'].strip() for p in options[i+1:i+5]]
            if any(re.match(r'^[-•]\s*\S', p) for p in following):
                headings[i] = {'label':m['label'], 'target_id':m['id']}
                break
    date_options = [i for i, q in enumerate(options) if _dates(q['quote'])
                    or re.search(r'\b(today|yesterday|ngayon|kahapon)\b', q['quote'], re.I)]
    status_options = [i for i, q in enumerate(options) if has_flood_observation(q['quote'])]
    current_city = current_barangay = current_depth = current_clock = None
    scopes = {}
    for i, q in enumerate(options):
        heading = headings.get(i)
        if heading and heading['label'] in {'CITY', 'PROVINCE'}:
            current_city, current_barangay, current_depth, current_clock = i, None, None, None
        elif heading and heading['label'] == 'BARANGAY':
            current_barangay = i
        if i in depth_heads:
            current_depth, current_barangay = i, None
        if heading and CLOCK.search(q['quote']):
            current_clock = i
        # Narrative/clearance/update text ends inferred list scope. It is still
        # present in the full article and in the global evidence options.
        is_bullet = bool(re.match(r'^\s*[-•]\s*\S', q['quote']))
        if not (heading or i in depth_heads or is_bullet):
            current_city = current_barangay = current_depth = current_clock = None
        scopes[i] = {'city_heading':current_city, 'barangay_heading':current_barangay,
                     'depth_heading':current_depth, 'clock_heading':current_clock}
    rows = []
    for m in candidates:
        ids = occurrences[m['id']]
        local = scopes[ids[0]] if len(ids) == 1 else {}
        rows.append({'target_id':m['id'], 'target_passages':ids,
                     'context_only_heading':any(headings.get(i, {}).get('target_id') == m['id'] for i in ids),
                     'list_context':local})
    return {'schema_version':CONTRACT, 'targets':rows, 'date_candidates':date_options,
            'affirmative_status_candidates':status_options,
            'heading_passages':sorted(headings), 'depth_heading_passages':sorted(depth_heads)}


def evaluate_rows(source: object, baseline: object, rows: list | tuple, catalog: object, *,
                  _layout: dict | None = None, _require_city_heading: bool = False) -> tuple:
    """Hard reference failures abort; semantic failures retain explicit row outcomes.

    Independent checks collect simultaneous missing date/place/status evidence.
    Every accepted row also passes the unchanged canonical V1 fact validator.
    """
    options = quote_options(source.article_text)
    candidates = {m['id']:m for m in targets(baseline)}
    if len({r.target_id for r in rows}) != len(rows) or any(r.target_id not in candidates for r in rows):
        raise ResolutionError('native_resolution_target_mismatch')
    layout = source_layout(source.article_text, list(candidates.values())) if _layout is None else _layout
    scopes = {r['target_id']:r for r in layout['targets']}
    claims, groups, audits, outcomes = [], [], [], []
    for row in rows:
        evidence = {field:_spans(getattr(row, field+'_evidence'), options)
                    for field in ('place','status','time','depth','access','section')}
        issues = []
        def issue(field: str, code: str) -> None:
            value = {'field':field, 'code':code}
            if value not in issues:
                issues.append(value)
        target = candidates[row.target_id]
        scope = scopes[row.target_id]
        if row.verdict == 'observed':
            city_context = scope.get('city_context') if _require_city_heading else None
            if city_context:
                if city_context['option_index'] not in row.place_evidence:
                    issue('place_evidence','native_resolution_city_heading_missing')
                expected_city = catalog.city(city_context['exact_text'])
                actual_city = catalog.city(row.city) if row.city else []
                if len(expected_city)!=1 or len(actual_city)!=1 or expected_city[0].name!=actual_city[0].name:
                    issue('city','native_resolution_city_scope_mismatch')
            if editorial_prefix(target,source.article_text):
                issue('verdict', 'native_resolution_editorial_context')
            if scope['context_only_heading']:
                issue('verdict', 'native_resolution_context_heading')
            if not any(e.start <= target['start'] < target['end'] <= e.end for e in evidence['place']):
                issue('place_evidence', 'native_resolution_place_evidence_missing')
            if row.city is None or not _contains(row.city, evidence['place']):
                issue('place_evidence', 'native_resolution_city_evidence_missing')
            elif len(catalog.city(row.city)) != 1:
                issue('city', 'native_resolution_city_unresolved')
            if row.barangay and not _contains(row.barangay, evidence['place']):
                issue('place_evidence', 'native_resolution_parent_evidence_missing')
            elif row.barangay and row.city and len(catalog.city(row.city)) == 1:
                if len(catalog.barangay(row.barangay, catalog.city(row.city)[0].name)) != 1:
                    issue('barangay', 'native_resolution_barangay_unresolved')
            if not any(has_flood_observation(e.quote) for e in evidence['status']):
                issue('status_evidence', 'native_resolution_status_evidence_missing')
            if not any(target['text'].casefold() in e.quote.casefold() for e in evidence['status']):
                issue('status_evidence', 'native_resolution_status_target_missing')
            if row.contradictory or row.status in {'forecast','negated','unclear'}:
                issue('status', 'native_resolution_observation_not_supported')
            status_text = ' '.join(e.quote for e in evidence['status'])
            if row.status in {'active','rising'} and (CONDITION_SUBSIDED.search(status_text)
                    or FORECAST_PATTERNS.search(status_text) or NEGATION_PATTERNS.search(status_text)):
                issue('status_evidence', 'native_resolution_status_conflict')
            # Enforce recognized list boundaries rather than accepting a depth
            # or locality heading belonging to a neighboring list.
            for field, role, heading_ids, labels in (
                    ('place','city_heading',layout['heading_passages'],{'CITY','PROVINCE'}),
                    ('place','barangay_heading',layout['heading_passages'],{'BARANGAY'}),
                    ('depth','depth_heading',layout['depth_heading_passages'],None),
                    ('time','clock_heading',layout['heading_passages'],None)):
                expected = scope['list_context'].get(role)
                for i in getattr(row, field+'_evidence'):
                    relevant = (i in heading_ids and (labels is None or
                                any(m['label'] in labels and m['start']>=options[i]['start']
                                    and m['end']<=options[i]['end'] for m in candidates.values())))
                    if relevant and expected is not None and i != expected:
                        # A date-only city heading without a clock is not a
                        # competing observation clock.
                        if field != 'time' or CLOCK.search(options[i]['quote']):
                            issue(field+'_evidence', 'native_resolution_scope_mismatch')
            for field in ('status','time','depth','access','section'):
                for e in evidence[field]:
                    if (target['text'].casefold() not in e.quote.casefold()
                            and any(m['id']!=target['id'] and m['label']=='ROAD'
                                    and not editorial_prefix(m,source.article_text)
                                    and m['text'].casefold() in e.quote.casefold() for m in candidates.values())):
                        issue(field+'_evidence', 'native_resolution_fact_target_mismatch')
            # Check both date and clock even if the first check would fail.
            if row.date_text and not _contains(row.date_text, evidence['time']):
                issue('time_evidence', 'native_resolution_date_evidence_missing')
            if row.clock_text and not _contains(row.clock_text, evidence['time']):
                issue('time_evidence', 'native_resolution_clock_evidence_missing')
            try:
                resolve_time(row, source, evidence['time'])
            except ResolutionError as exc:
                issue('time_evidence', exc.code)
            if row.depth_text and not _contains(row.depth_text, evidence['depth']):
                issue('depth_evidence', 'native_resolution_depth_evidence_missing')
            if row.access != 'unknown' and not _access_supported(row.access, evidence['access']):
                issue('access_evidence', 'native_resolution_access_evidence_missing')
            if row.road_section and not _contains(row.road_section, evidence['section']):
                issue('section_evidence', 'native_resolution_section_evidence_missing')
        row_claims, row_groups, row_audits = [], [], []
        if not issues:
            try:
                row_claims, row_groups, row_audits = resolve_rows(source, baseline, [row], catalog,
                                                               scoped_editorial_context=True)
            except ResolutionError as exc:
                issue('row', exc.code)
        for group in row_groups:
            group['claim_index'] += len(claims)
        claims.extend(row_claims); groups.extend(row_groups); audits.extend(row_audits)
        outcomes.append({'target_id':row.target_id,
                         'outcome':'accepted' if row_claims else 'unresolved' if row.verdict=='observed' else row.verdict,
                         'issues':issues or ([] if row_claims or row.verdict!='observed' else
                                             [{'field':'row','code':'native_resolution_not_projectable'}])})
    return claims, groups, audits, outcomes, sha(layout)


def replay_scoped_batch(bundle: dict, expected_sha256: str, *, resolver: object,
                        source: object, baseline: object, parent_run_id: int,
                        parent_result_sha256: str) -> dict:
    """Replay against independently reconstructed/pinned parent assets, no IO.

    A response for V1 or any different full article, layout, parent or request
    cannot be adopted as V2. This returns diagnostics, never a saved correction.
    """
    import base64
    from app.services.news_gemini_receipts import replay_bundle, validate_batch
    reference_result = replay_bundle(bundle, expected_sha256, config=resolver.config)
    if resolver.identity.get('evidence_contract') != CONTRACT:
        raise ResolutionError('native_resolution_contract_invalid')
    packets = resolver.request_packets(source, baseline, parent_run_id=parent_run_id,
                                       parent_result_sha256=parent_result_sha256)
    intent = bundle['intent']
    if not any(p['payload']==intent['payload'] and p['context']==intent['context'] for p in packets):
        raise ResolutionError('native_resolution_replay_request_mismatch')
    if reference_result['status'] != 'evidence_references_passed':
        return reference_result
    rows, usage = validate_batch(intent['payload'], base64.b64decode(bundle['response']['body_base64']),resolver.config)
    _, _, _, outcomes, layout_sha = evaluate_rows(source,baseline,rows.results,resolver.catalog)
    return {'status':'row_outcomes_recorded','row_outcomes':outcomes,'source_layout_sha256':layout_sha,
            'usage':usage,'article_acceptance':'not_evaluated','provider_requests':0,'database_writes':0}
