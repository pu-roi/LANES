"""Conservative source-bound depth, access and clock normalization."""
from __future__ import annotations

from calendar import month_abbr, month_name
from datetime import date, datetime, timedelta, timezone
from math import isfinite
import re

from app.services.taglish_extraction_service import extract_depth_from_text
from .contracts import NativeInput

PHT=timezone(timedelta(hours=8))
CLOCK=re.compile(r"(?<!\w)(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?(?!\w)",re.I)
MONTHS={v.casefold():i for i in range(1,13) for v in (month_abbr[i],month_name[i])}
MONTH=re.compile(r"\b("+'|'.join(MONTHS)+r")\s+(\d{1,2}),?\s+(\d{4})\b",re.I)


def _dates(text: str) -> set[date]:
    result=set()
    for m in re.finditer(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)",text):result.add(date(*(int(i) for i in m.groups())))
    for m in MONTH.finditer(text):result.add(date(int(m[3]),MONTHS[m[1].casefold()],int(m[2])))
    return result


def time_fields(facts: list[dict], source: NativeInput, graph: dict) -> tuple[dict, dict, list[str]]:
    times=[f for f in facts if f['kind']=='time'];byrole={r:[f for f in times if f['temporal_role']==r] for r in ('observation','report','unspecified')}
    role=next((r for r,fs in byrole.items() if fs), 'unspecified');selected=byrole[role]
    evidence=[e for f in selected for e in f['evidence']]
    values=list(dict.fromkeys(f['value'] for f in selected if f['value']))
    ids={i for f in selected for i in f['entity_ids']}
    expressions=[e for e in graph['expressions'] if e['id'] in ids]
    raw=source.article_text[min(e['start'] for e in expressions):max(e['end'] for e in expressions)] if expressions else None
    result={'event_time_raw':raw,'event_time_resolved':None,'event_time_kind':role}
    details={'fact_ids':[f['id'] for f in selected],'evidence':evidence,'date_basis':None,'resolved_at':None,
             'other_role_fact_ids':[f['id'] for f in times if f not in selected]}
    reasons=[]
    if role!='observation':return result,details,['observation_time_not_resolved']
    # The date, clock and timezone must govern these exact observation facts.
    context='\n'.join(e['text'] for e in evidence)
    try:
        clocks={(int(m[1]),int(m[2] or 0),m[3].lower()) for value in values for m in CLOCK.finditer(value)}
        dates=_dates(context)
        heading_zone=bool(re.search(r'\ball\s+times\s+(?:(?:are|shown)\s+)?(?:in\s+)?PHT\b',context,re.I))
        clock_zones=[]
        for expression in expressions:
            for match in CLOCK.finditer(expression['text']):
                suffix=source.article_text[expression['start']+match.end():expression['start']+match.end()+24]
                supported=bool(re.match(r'^\s*[,\(]?\s*(?:PHT\b|UTC\s*\+\s*08(?::?00)?(?![:\d])\b)',suffix,re.I))
                other=bool(re.match(r'^\s*[,\(]?\s*(?:UTC|GMT|[A-Z]{2,4}(?=\)))\b',suffix))
                clock_zones.append(supported or heading_zone and not other)
        if len(clocks)!=1 or not clock_zones or not all(clock_zones):raise ValueError('unsupported_clock')
        h,minute,period=next(iter(clocks))
        if not 1<=h<=12 or not 0<=minute<=59:raise ValueError('invalid_clock')
        relative=set(m.group().casefold() for m in re.finditer(r"\b(?:today|yesterday)\b",context,re.I))
        if relative:
            if len(relative)!=1 or not source.publication_evidence.timezone_known or source.published_at is None:
                raise ValueError('unknown_relative_date')
            day=source.published_at.astimezone(PHT).date()-timedelta(days='yesterday' in relative)
            if dates and dates!={day}:raise ValueError('conflicting_dates')
            dates={day};details['date_basis']='publisher_feed_relative_date'
        else:details['date_basis']='explicit_body_date'
        if len(dates)!=1:raise ValueError('unsupported_date')
        observed=datetime.combine(next(iter(dates)),datetime.min.time(),tzinfo=PHT).replace(hour=h%12+(12 if period=='p' else 0),minute=minute)
        result['event_time_resolved']=observed;details['resolved_at']=observed.isoformat()
    except (ValueError,OverflowError):reasons.append('observation_time_not_resolved')
    return result,details,reasons


def depth_fields(facts: list[dict], graph: dict, text: str) -> tuple[dict, dict, list[str]]:
    depths=[f for f in facts if f['kind']=='depth'];expressions={e['id']:e for e in graph['expressions']}
    result={'depth_raw':None,'depth_canonical':None,'depth_rule':None,'depth_meters':None,'depth_inches':None,'depth_formatted':None}
    details={'fact_ids':[f['id'] for f in depths],'selected_fact_id':None,'evidence':[]}
    if not depths:return result,details,[]
    raw=list(dict.fromkeys(f['value'] for f in depths if f['value']))
    result['depth_raw']=raw[0] if len(raw)==1 else None
    unsafe=any(f['depth_scope'] not in ('point',) or f['uncertainty'] or 'relative_gauge' in f['qualifiers'] for f in depths)
    quantitative=[f for f in depths if f['value'] and re.search(r'\d|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|isa|dalawa|tatlo|apat|lima|anim|pito|walo|siyam|dalawampu)\b',f['value'],re.I)]
    candidates=quantitative or depths
    if unsafe or len({f['value'] for f in candidates})!=1:
        return result,details,['depth_scalar_not_supported']
    selected=candidates[0]
    # A verbal/numeric pair is not evidence that two distinct occurrences agree.
    if len(depths)>1 and len(raw)>1:
        spans=[expressions[i] for f in depths for i in f['entity_ids'] if i in expressions]
        spans=sorted(spans,key=lambda e:e['start'])
        if len(spans)!=2 or len(quantitative)!=1 or not re.fullmatch(r'\s*[,(/]?\s*',text[spans[0]['end']:spans[1]['start']]):
            return result,details,['depth_scalar_not_supported']
    phrase=selected['value'] or ''
    parsed,canonical,rule,reasons=extract_depth_from_text(phrase)
    if parsed is None:return result,details,['depth_scalar_not_supported']
    # Keep source qualifiers even when the older parser recognizes a shorter span.
    result.update(depth_raw=phrase,depth_canonical=canonical,depth_rule=rule)
    if 'approximate' in selected['qualifiers'] and 'approximate_depth' not in reasons:reasons.append('approximate_depth')
    details.update(selected_fact_id=selected['id'],evidence=selected['evidence'])
    number=re.fullmatch(r'\s*(?:(?:about|around|approximately|roughly|almost|nearly|halos)\s+)?(\d+(?:\.\d+)?)\s*(cm|centimeters?|m|meters?|inches?|inch|in|feet|foot|ft)\s*',phrase,re.I)
    if number:
        value=float(number[1]);unit=number[2].casefold()
        meters=value/100 if unit.startswith('c') else value if unit in ('m','meter','meters') else value*.3048 if unit in ('feet','foot','ft') else value*.0254
        if not all(isfinite(n) for n in (value,meters,meters/.0254)):
            result['depth_canonical']=None;reasons.append('depth_scalar_not_supported')
        else:result.update(depth_meters=meters,depth_inches=meters/.0254)
    return result,details,reasons


def access_fields(facts: list[dict]) -> tuple[str, dict, list[str]]:
    access=[f for f in facts if f['kind']=='access'];values={f['value'] for f in access}
    details={'fact_ids':[f['id'] for f in access],'evidence':[e for f in access for e in f['evidence']]}
    supported={'passable_all','passable_unspecified','light_vehicle_closed','impassable_all'}
    if len(values)!=1 or not values<=supported:return 'unknown',details,['access_not_supported'] if values else []
    value=next(iter(values));text=' '.join(q for f in access for q in f['qualifiers'])
    if value=='passable_unspecified':
        if re.search(r'\b(?:to|for|sa|ng)\b',text,re.I):
            return 'unknown',details,['access_vehicle_scope_not_supported']
        if re.search(r'caution|mag-ingat|pag-iingat',text,re.I):value='passable_with_caution'
        else:
            # v42 can retain only the bare word "passable". Qualify an exact
            # adjacent caution modifier, without altering the native fact.
            occurrences={}
            for fact in access:
                for quote in fact['evidence']:
                    for qualifier in fact['qualifiers']:
                        for hit in re.finditer(re.escape(qualifier),quote['text'],re.I):
                            occurrences[(quote['start']+hit.start(),quote['start']+hit.end())]=(quote,hit)
            if len(occurrences)==1:
                (a,b),(quote,hit)=next(iter(occurrences.items()))
                caution=re.match(r'\s+(?:with\s+caution|pero\s+mag-ingat|nang\s+may\s+pag-iingat)\b',quote['text'][hit.end():],re.I)
                if caution:
                    value='passable_with_caution'
                    details['source_modifier_evidence']={'start':a,'end':b+caution.end(),
                        'text':quote['text'][hit.start():hit.end()+caution.end()]}
            elif occurrences:return 'unknown',details,['access_modifier_ambiguous']
    if any(f['uncertainty'] for f in access):return 'unknown',details,['access_not_supported']
    return value,details,[]
