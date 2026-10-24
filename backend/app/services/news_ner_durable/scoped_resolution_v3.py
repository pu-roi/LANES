"""Source-anchored locality scope for bullet and plain-text flood lists."""
from __future__ import annotations

import re

from .resolution import quote_options
from .fields import CLOCK, _dates
from .scoped_resolution import evaluate_rows as evaluate_v2
from app.services.news_evidence_policy import has_flood_observation
from app.services.taglish_extraction_service import CONDITION_SUBSIDED, FORECAST_PATTERNS, NEGATION_PATTERNS

VERSION = 'native-gemini-resolution-v3'
CONTRACT = 'scoped-quote-options-v3'
INSTRUCTIONS = """
SCOPED EVIDENCE CONTRACT v3:
The full article and original quote_options remain authoritative. Source layout records
standalone headings and their bounded bullet OR plain-text road-list members.
For an observed target with city_context, copy city_context.exact_text into city and
include city_context.option_index AND every target_passages index in place_evidence.
For example, a Malabon heading governs its following roads until the next city or
unrelated paragraph. A missing bullet does not remove this relationship. Never borrow
a later city's heading. Do not return city=null when the supplied exact city heading
clearly governs this road. If conflicting, return ambiguous instead of guessing.
CITY/BARANGAY/PROVINCE headings are context, not separate flood incidents. Pump-operation
narrative alone is not a dated road-list observation. Keep every requested target row.
Cite target plus affirmative flooding/list introduction for status; exact source date
plus target clock for time; the target's own depth/access/section for those fields.
Copy city and barangay spellings from source, not canonical catalog names. Passage IDs
are option_index values, never character offsets. Unsupported facts remain unknown.
Do not add citations, facts or locations absent from the supplied article.
"""


def source_layout(text: str, candidates: list[dict]) -> dict:
    options = quote_options(text)
    occurrences = {m['id']:[i for i,q in enumerate(options)
        if q['start'] <= m['start'] < m['end'] <= q['end']] for m in candidates}
    bare = {}
    for i,q in enumerate(options):
        for m in candidates:
            if occurrences[m['id']] != [i] or m['label'] not in {'CITY','BARANGAY','PROVINCE'}:
                continue
            remainder = q['quote'].strip().replace(m['text'],'',1).strip(' \t:,-')
            if not remainder or re.fullmatch(r'\(as of [^\n]+\)',remainder,re.I):
                bare[i] = {'label':m['label'],'target_id':m['id'],'text':m['text']}
                break
    depth_heads = {i for i,q in enumerate(options) if re.fullmatch(
        r'[^\w]*(?:waist|tire|knee|half\s+knee|ankle|gutter)[ -]deep(?:\s*\([^\n]{1,60}\))?\s*[.:]?',
        q['quote'].strip(),re.I)}

    def entry(i: int) -> bool:
        line = options[i]['quote']
        if (CONDITION_SUBSIDED.search(line) or FORECAST_PATTERNS.search(line) or NEGATION_PATTERNS.search(line)
                or re.match(r'\s*(?:updated?\b|refresh\b|correction\b)',line,re.I)):
            return False
        road = any(occurrences[m['id']] == [i] and (m['label']=='ROAD' or
            (m['label']=='LANDMARK' and re.search(r'\b(?:highway|road|street|avenue|boulevard|blvd\.?|ave\.?)\b',m['text'],re.I)))
            for m in candidates)
        return road and (bool(re.match(r'^\s*[-•]\s*\S',line)) or has_flood_observation(line))

    headings = {}
    for i,h in bare.items():
        for j in range(i+1,min(i+6,len(options))):
            if entry(j):
                headings[i] = h
                break
            if j in depth_heads or (j in bare and bare[j]['label']=='BARANGAY'):
                continue
            break
    city = barangay = depth = clock = None
    scopes = {}
    for i,q in enumerate(options):
        h = bare.get(i)
        if h and h['label'] in {'CITY','PROVINCE'}:
            city = i if i in headings and h['label']=='CITY' else None
            barangay = depth = clock = None
        elif h and h['label']=='BARANGAY':
            barangay = i if i in headings else None
        elif i in depth_heads:
            depth,barangay = i,None
        elif not entry(i):
            city = barangay = depth = clock = None
        if i in headings and CLOCK.search(q['quote']):
            clock = i
        scopes[i] = dict(city_heading=city,barangay_heading=barangay,depth_heading=depth,clock_heading=clock)
    rows = []
    for m in candidates:
        ids = occurrences[m['id']]
        scope = scopes[ids[0]] if len(ids)==1 else {}
        city_id = scope.get('city_heading')
        rows.append({'target_id':m['id'],'target_passages':ids,'list_context':scope,
            'context_only_heading':any(headings.get(i,{}).get('target_id')==m['id'] for i in ids),
            'city_context':None if city_id is None else {'option_index':city_id,'exact_text':bare[city_id]['text']}})
    return {'schema_version':CONTRACT,'targets':rows,'heading_passages':sorted(headings),
        'depth_heading_passages':sorted(depth_heads),
        'date_candidates':[i for i,q in enumerate(options) if _dates(q['quote']) or re.search(r'\b(today|yesterday|ngayon|kahapon)\b',q['quote'],re.I)],
        'affirmative_status_candidates':[i for i,q in enumerate(options) if has_flood_observation(q['quote'])]}


def evaluate_rows(source: object, baseline: object, rows: list | tuple, catalog: object, *,
                  reviewed_time_context: bool = False) -> tuple:
    from .resolution import targets
    return evaluate_v2(source,baseline,rows,catalog,
        _layout=source_layout(source.article_text,targets(baseline)),_require_city_heading=True,
        reviewed_time_context=reviewed_time_context)
