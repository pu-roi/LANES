"""Evidence-linked Gemini resolutions of immutable NER output; no storage/network IO.

Resolved claims are a deterministic projection of a saved provider response. The
original neural graph remains unchanged and the parent run remains in history.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.news_audit import (AuditEvidenceSpan, AuditedAccess, AuditedDepth,
    AuditedPlace, AuditedStatus, AuditedTime, IndependentAuditResult, ProviderClaimAudit)
from app.schemas.news_ner_result import NerProjectedClaim
from app.services.news_claim_auditor import canonical_claim_sha256, _classify
from app.services.news_evidence_policy import has_flood_observation
from app.services.taglish_extraction_service import (extract_depth_from_text, CONDITION_SUBSIDED,
    FORECAST_PATTERNS, NEGATION_PATTERNS)
from .contracts import NativeInput, sha
from .fields import CLOCK, MONTHS, PHT, _dates

VERSION = 'native-gemini-resolution-v1'
MAX_TARGETS = 64


class ResolutionError(ValueError):
    def __init__(self, code: str, *, retryable: bool = False) -> None:
        self.code = code
        self.retryable = retryable
        self.request_count = 0
        super().__init__(code)


class ResolvedMention(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    target_id: str
    verdict: Literal['observed', 'unsupported', 'ambiguous']
    city: str | None
    barangay: str | None
    place_evidence: tuple[int, ...] = Field(max_length=12)
    status: Literal['active', 'rising', 'receding', 'subsided', 'forecast', 'negated', 'unclear']
    historical: bool
    contradictory: bool
    status_evidence: tuple[int, ...] = Field(max_length=12)
    time_role: Literal['observation', 'clearance', 'report', 'unknown']
    date_text: str | None
    clock_text: str | None
    contemporaneous: bool
    time_evidence: tuple[int, ...] = Field(max_length=12)
    depth_text: str | None
    depth_scope: Literal['individual', 'shared', 'range', 'unknown']
    depth_evidence: tuple[int, ...] = Field(max_length=12)
    access: Literal['passable_all', 'passable_with_caution', 'passable_unspecified', 'light_vehicle_closed', 'impassable_all', 'unknown']
    access_evidence: tuple[int, ...] = Field(max_length=12)
    road_section: str | None
    section_evidence: tuple[int, ...] = Field(max_length=12)


class ResolutionResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)
    results: tuple[ResolvedMention, ...] = Field(max_length=8)


def quote_options(text: str) -> list[dict]:
    """Stable source slices; the provider selects indexes, never writes offsets."""
    values = []
    for paragraph in re.finditer(r'[^\r\n]+', text):
        for start in range(paragraph.start(), paragraph.end(), 4000):
            end = min(paragraph.end(), start + 4000)
            values.append({'start': start, 'end': end, 'quote': text[start:end]})
    if len(values) > 256:
        raise ResolutionError('native_resolution_article_too_large')
    return values


def targets(result: object) -> list[dict]:
    values = [m.model_dump(mode='json') for m in result.native.graph.mentions
              if m.label in {'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY', 'CITY', 'PROVINCE'}]
    if len(values) > MAX_TARGETS:
        raise ResolutionError('native_resolution_target_limit')
    return values


def _spans(indexes: tuple[int, ...], options: list[dict]) -> tuple[AuditEvidenceSpan, ...]:
    if len(set(indexes)) != len(indexes) or any(i < 0 or i >= len(options) for i in indexes):
        raise ResolutionError('native_resolution_evidence_invalid')
    return tuple(AuditEvidenceSpan(**options[i]) for i in indexes)


def _contains(value: str | None, spans: tuple[AuditEvidenceSpan, ...]) -> bool:
    return bool(value and any(value in e.quote for e in spans))


def _source_date(raw: str, published: datetime | None) -> date | None:
    dates = _dates(raw)
    if len(dates) == 1:
        return next(iter(dates))
    if dates or published is None:
        return None
    day = published.astimezone(PHT).date()
    lowered = raw.strip().casefold()
    if lowered in {'today', 'ngayon'}:
        return day
    if lowered in {'yesterday', 'kahapon'}:
        return day - timedelta(days=1)
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    if lowered in weekdays:
        return day - timedelta(days=(day.weekday() - weekdays.index(lowered)) % 7)
    match = re.fullmatch(r'(' + '|'.join(MONTHS) + r')\.?\s+(\d{1,2})', lowered)
    if match:
        value = date(day.year, MONTHS[match[1]], int(match[2]))
        return value.replace(year=value.year - 1) if value > day + timedelta(days=1) else value
    return None


def resolve_time(row: ResolvedMention, source: NativeInput, spans: tuple[AuditEvidenceSpan, ...]) -> tuple[datetime | None, str, str | None]:
    """Publication fallback is explicit administration, never a measured onset."""
    if row.time_role not in {'observation', 'clearance'}:
        return None, 'unknown', None
    if row.status == 'subsided' and row.time_role != 'clearance':
        return None, 'unknown', None
    if row.status != 'subsided' and row.time_role != 'observation':
        return None, 'unknown', None
    quotes = ' '.join(e.quote for e in spans)
    if row.time_role=='observation' and CONDITION_SUBSIDED.search(quotes):
        return None, 'unknown', None
    pub = source.published_at
    if pub is not None and pub.utcoffset() is None:
        pub = None
    if row.date_text is not None and not _contains(row.date_text, spans):
        raise ResolutionError('native_resolution_date_evidence_missing')
    day = _source_date(row.date_text, pub) if row.date_text else (
        pub.astimezone(PHT).date() if pub and row.contemporaneous else None)
    explicit_dates = _dates(quotes)
    if explicit_dates and (len(explicit_dates)!=1 or day not in explicit_dates):
        return None, 'unknown', None
    if row.clock_text is not None:
        if not _contains(row.clock_text, spans):
            raise ResolutionError('native_resolution_clock_evidence_missing')
        matches = list(CLOCK.finditer(row.clock_text))
        if len(matches) != 1 or day is None:
            return None, 'unknown', None
        match = matches[0]
        hour, minute = int(match[1]), int(match[2] or 0)
        if not 1 <= hour <= 12 or not 0 <= minute < 60:
            return None, 'unknown', None
        # This service is restricted to the configured Philippine news sources.
        # An explicit incompatible zone must not silently become Manila time.
        if re.search(r'\b(?:UTC|GMT)\s*(?:[-+]\s*(?!0?8(?::?00)?\b)\d)|\b(?:EST|EDT|PST|PDT|JST)\b', quotes):
            return None, 'unknown', None
        observed = datetime.combine(day, datetime.min.time(), tzinfo=PHT).replace(
            hour=hour % 12 + (12 if match[3].lower() == 'p' else 0), minute=minute)
        return observed, 'source_clock_manila', row.clock_text
    # Do not substitute an article's publication clock for a past date or a
    # clearance. An article describing flooding today may use the agreed proxy.
    quotes = ' '.join(e.quote for e in spans)
    # A timestamp-free report can use publication as an administrative proxy.
    # Never conceal an uncited clock elsewhere, a past observation date, a
    # cleared update, or historical/conflicting provider evidence.
    if (row.time_role == 'observation' and row.status in {'active', 'rising'}
            and not row.historical and not row.contradictory and pub
            and (day is None or day == pub.astimezone(PHT).date())
            and not CLOCK.search(source.article_text)
            and not re.search(r'\b(?:yesterday|kahapon|last\s+(?:night|week|month|year))\b',
                source.article_text, re.I)
            and not any(d != pub.astimezone(PHT).date() for d in _dates(source.article_text))):
        return pub, 'publication_time_fallback', None
    if (row.time_role == 'observation' and row.contemporaneous and not row.historical
            and not row.contradictory and pub and day == pub.astimezone(PHT).date()
            and not CLOCK.search(quotes)
            and re.search(r'\b(?:today|ngayon)\b', quotes, re.I)):
        return pub, 'publication_time_fallback', row.date_text or re.search(r'\b(?:today|ngayon)\b',quotes,re.I).group()
    return None, 'unknown', None


def _access_supported(value: str, spans: tuple[AuditEvidenceSpan, ...]) -> bool:
    patterns = (
        ('impassable_all',r'(?:not\s+passable\s+(?:to|sa)\s+(?:all|any)(?:\s+(?:kinds?|types?)\s+of)?\s+vehicles?|impassable\s+to\s+all\s+vehicles|hindi\s+madaanan\s+ng\s+lahat\s+ng\s+sasakyan)'),
        ('light_vehicle_closed',r'(?:closed\s+to|not\s+passable\s+(?:to|sa)|impassable\s+to)\s+(?:light|small)\s+vehicles|hindi\s+madaanan\s+ng\s+maliliit\s+na\s+sasakyan'),
        ('passable_with_caution',r'passable\s+(?:with\s+caution|pero\s+mag-ingat)|madaanan\s+nang\s+may\s+pag-iingat'),
        ('passable_all',r'passable\s+to\s+all(?:\s+types?\s+of)?\s+vehicles|madaanan\s+ng\s+lahat\s+ng\s+sasakyan'),
        ('passable_unspecified',r'\bpassable\b'),
    )
    choices=set()
    for span in spans:
        if re.search(r'\b(?:not|never|no\s+longer)\s+passable\b|\bhindi\s+madaanan\b',span.quote,re.I):
            negative=next((name for name,pattern in patterns[:2] if re.search(pattern,span.quote,re.I)),None)
            choices.add(negative or 'unknown')
            continue
        for name,pattern in patterns:
            if re.search(pattern,span.quote,re.I):
                choices.add(name)
                break
    return choices=={value}


def apply_resolution(source: NativeInput, baseline: object, payload: dict, catalog: object,
                     expected_identity: dict) -> object:
    """Revalidate every provider fact and rebuild its derived claims without IO."""
    required = {'schema_version', 'identity', 'input_sha256', 'parent_run_id', 'parent_result_sha256', 'results'}
    from .scoped_resolution import VERSION as SCOPED_VERSION, CONTRACT, evaluate_rows
    from . import scoped_resolution_v3 as v3, scoped_resolution_v4 as v4
    response_version = expected_identity.get('response_version')
    if response_version == v3.VERSION:
        SCOPED_VERSION, CONTRACT, evaluate_rows = v3.VERSION, v3.CONTRACT, v3.evaluate_rows
    elif response_version == v4.VERSION:
        SCOPED_VERSION, CONTRACT, evaluate_rows = v4.VERSION, v4.CONTRACT, v4.evaluate_rows
    scoped = response_version == SCOPED_VERSION
    if scoped:
        required |= {'row_outcomes', 'source_layout_sha256'}
    if (set(payload) - {'transport'} != required or payload['schema_version'] != (SCOPED_VERSION if scoped else VERSION)
            or (scoped and expected_identity.get('evidence_contract') != CONTRACT)
            or payload['identity'] != expected_identity or payload['input_sha256'] != baseline.source.input_fingerprint
            or type(payload['parent_run_id']) is not int or payload['parent_run_id'] <= 0
            or not isinstance(payload['parent_result_sha256'], str)
            or re.fullmatch(r'[a-f0-9]{64}', payload['parent_result_sha256']) is None):
        raise ResolutionError('native_resolution_identity_mismatch')
    transport=payload.get('transport',[])
    if not isinstance(transport,list) or len(transport)>(MAX_TARGETS+3)//4:
        raise ResolutionError('native_resolution_transport_invalid')
    for record in transport:
        if (not isinstance(record,dict) or set(record)-{'request_id','actual_model','input_tokens','output_tokens','thinking_tokens'}
                or any(type(v)!=int or not 0<=v<=10_000_000 for k,v in record.items() if k.endswith('_tokens'))
                or any(not isinstance(v,str) or re.fullmatch(r'[A-Za-z0-9_./:-]{1,200}',v) is None
                    for k,v in record.items() if not k.endswith('_tokens'))):
            raise ResolutionError('native_resolution_transport_invalid')
    options = quote_options(source.article_text)
    candidates = {m['id']: m for m in targets(baseline)}
    rows = [ResolvedMention.model_validate_json(json.dumps(row), strict=True) for row in payload['results']]
    if len({r.target_id for r in rows}) != len(rows) or {r.target_id for r in rows} != set(candidates):
        raise ResolutionError('native_resolution_target_mismatch')
    result = baseline.model_copy(deep=True)
    claims, groups, audits = [], [], []
    if scoped:
        kwargs = {}
        if 'shared_time_review' in expected_identity:
            from app.services.news_tribune_replay import SHARED_TIME_REVIEW
            if response_version != v4.VERSION or expected_identity['shared_time_review'] != SHARED_TIME_REVIEW:
                raise ResolutionError('tribune_shared_time_review_required')
            kwargs['reviewed_time_context'] = True
        claims, groups, audits, outcomes, layout_sha = evaluate_rows(source, baseline, rows, catalog, **kwargs)
        if outcomes != payload['row_outcomes'] or layout_sha != payload['source_layout_sha256']:
            raise ResolutionError('native_resolution_outcomes_mismatch')
    else:
        claims, groups, audits = resolve_rows(source, baseline, rows, catalog)
    result.claims = claims
    accounting=[{'fact_id':fact.id,'group_ids':[g['group_id'] for g in groups if fact.id in g['fact_ids']],
        'disposition':'projected' if any(fact.id in g['fact_ids'] for g in groups) else 'unassigned',
        'reasons':[] if any(fact.id in g['fact_ids'] for g in groups) else ['not_used_by_verified_resolution']}
        for fact in baseline.native.graph.facts]
    result.projection = {**deepcopy(baseline.projection), 'groups':groups,
        'fact_accounting':accounting,'disposition':'projected' if claims else 'no_eligible_observations',
        'mentions_without_observation':[m['id'] for m in candidates.values()
            if not any(m['id'] in g['target_entity_ids'] for g in groups)]}
    result.provenance = {**result.provenance, 'llm_resolution':deepcopy(payload)}
    if scoped:
        result.projection['resolution_outcomes'] = deepcopy(outcomes)
    result.read_projection = None
    return result


def editorial_prefix(target: dict, text: str) -> bool:
    """Source-proven publisher rubric, never a replacement for a road name.

    Retain the neural ROAD label. Only the exact leading alert/update token,
    immediately followed by a colon, is editorial context in the scoped policy.
    'Flood Alert Road' and mentions elsewhere in an article do not qualify.
    """
    return (target['label']=='ROAD' and target['start']==len(text)-len(text.lstrip())
            and re.fullmatch(r'(?:FLOOD|WEATHER|TRAFFIC)\s+(?:ALERT|UPDATE|BULLETIN)',target['text'],re.I) is not None
            and re.match(r'\s*:',text[target['end']:]) is not None)


def resolve_rows(source: NativeInput, baseline: object, rows: list | tuple, catalog: object, *,
                 scoped_editorial_context: bool=False, reviewed_time_context: bool=False) -> tuple:
    """One canonical row validator for fail-fast batches and final recomputation."""
    options = quote_options(source.article_text)
    candidates = {m['id']: m for m in targets(baseline)}
    if len({r.target_id for r in rows}) != len(rows) or any(r.target_id not in candidates for r in rows):
        raise ResolutionError('native_resolution_target_mismatch')
    claims, groups, audits = [], [], []
    for row in rows:
        target = candidates[row.target_id]
        evidence = {name: _spans(getattr(row, name + '_evidence'), options)
                    for name in ('place', 'status', 'time', 'depth', 'access', 'section')}
        if row.verdict != 'observed':
            continue
        if row.contradictory or row.status in {'forecast', 'negated', 'unclear'}:
            continue
        place = evidence['place']
        if not any(e.start <= target['start'] < target['end'] <= e.end for e in place):
            raise ResolutionError('native_resolution_place_evidence_missing')
        if row.city is None or not _contains(row.city, place):
            continue  # An unresolved parent is retained as an explicit outcome.
        cities = catalog.city(row.city)
        if len(cities) != 1:
            continue
        city = cities[0]
        barangay = None
        if row.barangay:
            if not _contains(row.barangay, place):
                raise ResolutionError('native_resolution_parent_evidence_missing')
            matches = catalog.barangay(row.barangay,city.name)
            if len(matches) != 1:
                continue
            barangay = matches[0].name
        if not evidence['status'] or not any(has_flood_observation(e.quote) for e in evidence['status']):
            raise ResolutionError('native_resolution_status_evidence_missing')
        # Require the status to cite this target as well as any governing heading.
        if not any(target['text'].casefold() in e.quote.casefold() for e in evidence['status']):
            raise ResolutionError('native_resolution_status_target_missing')
        status_text = ' '.join(e.quote for e in evidence['status'])
        if row.status in {'active','rising'} and (CONDITION_SUBSIDED.search(status_text)
                or FORECAST_PATTERNS.search(status_text) or NEGATION_PATTERNS.search(status_text)):
            raise ResolutionError('native_resolution_status_conflict')
        for name in ('time','depth','access','section'):
            for quote in evidence[name]:
                if reviewed_time_context and name == 'time':
                    from app.services.news_tribune_replay import reviewed_clock_citation
                    if reviewed_clock_citation(source, row, target, quote):
                        continue
                if (target['text'].casefold() not in quote.quote.casefold()
                        and any(m['id']!=target['id'] and m['label']=='ROAD'
                            and not (scoped_editorial_context and editorial_prefix(m,source.article_text))
                            and m['text'].casefold() in quote.quote.casefold() for m in candidates.values())):
                    raise ResolutionError('native_resolution_fact_target_mismatch')
        observed, basis, raw_time = resolve_time(row, source, evidence['time'])
        reviewed_clock = False
        if reviewed_time_context:
            from app.services.news_tribune_replay import reviewed_clock_citation
            reviewed_clock = any(reviewed_clock_citation(source, row, target, q) for q in evidence['time'])
        local_area = None
        if reviewed_clock:
            basis = 'developer_reviewed_article_as_of_context'
            if target['text'] == 'Gov. Pascual Avenue' and row.road_section == 'Gov. Pascual Avenue in Sitio 6':
                local_area = 'Sitio 6'
        # Retain a supported calendar day even when no clock can be resolved.
        # This is existing JSON metadata, not an invented starting-time instant.
        calendar_day = observed.astimezone(PHT).date() if observed else None
        if calendar_day is None and row.date_text and row.time_role=='observation':
            time_quotes=' '.join(e.quote for e in evidence['time'])
            candidate_day=_source_date(row.date_text,source.published_at)
            explicit_days=_dates(time_quotes)
            if (candidate_day is not None and not CONDITION_SUBSIDED.search(time_quotes)
                    and (not explicit_days or explicit_days=={candidate_day})):
                calendar_day=candidate_day
        depth, canonical, depth_rule = None, None, None
        reasons = []
        if row.depth_text:
            if not _contains(row.depth_text, evidence['depth']):
                raise ResolutionError('native_resolution_depth_evidence_missing')
            if row.depth_scope=='individual' and not any(target['text'].casefold() in e.quote.casefold() for e in evidence['depth']):
                raise ResolutionError('native_resolution_depth_target_missing')
            depth = row.depth_text
            _, canonical, depth_rule, depth_reasons = extract_depth_from_text(depth)
            reasons.extend(depth_reasons)
            if row.depth_scope != 'individual':
                canonical = None
                reasons.append('depth_scalar_not_supported')
        if row.access != 'unknown' and not _access_supported(row.access,evidence['access']):
            raise ResolutionError('native_resolution_access_evidence_missing')
        if row.road_section and not _contains(row.road_section, evidence['section']):
            raise ResolutionError('native_resolution_section_evidence_missing')
        if observed is None:
            reasons.append('observation_time_not_resolved')
        if basis == 'publication_time_fallback':
            reasons.append(basis)
        spans = [e for values in evidence.values() for e in values]
        begin = min([target['start']] + [e.start for e in spans])
        end = max([target['end']] + [e.end for e in spans])
        if end - begin > 4000:
            # Keep full source evidence in the response; do not invent a narrow
            # operational evidence sentence by silently dropping its heading.
            continue
        claim = NerProjectedClaim(raw_place_name=target['text'], canonical_city=city.name,
            canonical_barangay=barangay, canonical_province=city.province, psgc_code=city.code,
            canonical_road=target['text'] if target['label'] == 'ROAD' else None,
            road_segment_raw=row.road_section, local_area_raw=local_area,
            place_type={'ROAD':'street','CITY':'city','BARANGAY':'barangay','LANDMARK':'landmark'}.get(target['label'],'unknown'),
            place_char_start=target['start'], place_char_end=target['end'],
            condition=row.status, is_historical=row.historical, road_passability=row.access,
            depth_raw=depth, depth_canonical=canonical, depth_rule=depth_rule,
            event_time_raw=raw_time, event_time_resolved=observed,
            event_time_kind='observation' if observed else 'unspecified',
            evidence_sentence=source.article_text[begin:end], evidence_sentence_offset=(begin,end),
            uncertainty_reasons=sorted(set(reasons)))
        index = len(claims)
        claims.append(claim)
        audit = ProviderClaimAudit(claim_sha256=canonical_claim_sha256(claim),
            place=AuditedPlace(confirmed=True,evidence=place,raw_place_name=claim.raw_place_name,
                canonical_city=claim.canonical_city,canonical_barangay=claim.canonical_barangay),
            status=AuditedStatus(confirmed=True,evidence=evidence['status'],classification=row.status,
                historical=row.historical,contradictory=False),
            time=AuditedTime(confirmed=observed is not None,evidence=evidence['time'],
                observed_at=observed.isoformat() if observed else None,kind=claim.event_time_kind),
            depth=AuditedDepth(confirmed=depth is not None,evidence=evidence['depth'],canonical=canonical,raw=depth,qualifiers=()),
            access=AuditedAccess(confirmed=row.access!='unknown',evidence=evidence['access'],classification=row.access))
        audits.append(audit.model_dump(mode='json'))
        selected_facts=set()
        for fact in baseline.native.graph.facts:
            dimension={'status':'status','time':'time','depth':'depth','access':'access'}.get(fact.kind)
            if dimension and any(f.start < q.end and q.start < f.end for f in fact.evidence for q in evidence[dimension]):
                expected_value={'status':row.status,'time':row.clock_text,'depth':row.depth_text,'access':row.access}[dimension]
                if fact.value==expected_value:
                    selected_facts.add(fact.id)
        groups.append({'group_id':'resolved-' + row.target_id,'target_entity_ids':[row.target_id],
            'relation_ids':[], 'fact_ids':sorted(selected_facts),'scope':'local','evidence':[],
            'evidence_storage':'native_graph','disposition':'projected','reasons':[], 'claim_index':index,
            'normalizations':{'resolution_target_id':row.target_id,'time':{'date_basis':basis,
                'resolved_at':observed.isoformat() if observed else None,
                'occurrence_date':calendar_day.isoformat() if calendar_day else None},'audit':audits[-1]}})
    return claims, groups, audits


def resolution_audit(context: object, result: object, index: int) -> IndependentAuditResult:
    payload = result.provenance['llm_resolution']
    group = next(g for g in result.projection['groups'] if g['claim_index'] == index)
    audit = ProviderClaimAudit.model_validate_json(json.dumps(group['normalizations']['audit']), strict=True)
    claim = result.claims[index]
    if audit.claim_sha256 != canonical_claim_sha256(claim):
        # Placement fields are added after resolution and are deliberately not
        # included in its provider request. Rebind only after saved recomputation.
        audit = audit.model_copy(update={'claim_sha256':canonical_claim_sha256(claim)})
    outcome, reason = _classify(audit, claim)
    identity = payload['identity']
    return IndependentAuditResult(outcome=outcome,reason_code=reason,provider=identity['provider'],model=identity['model'],
        prompt_version=identity['prompt_version'],response_version=identity['response_version'],input_sha256=context.input_fingerprint,
        claim_sha256=canonical_claim_sha256(claim),evidence=audit)
