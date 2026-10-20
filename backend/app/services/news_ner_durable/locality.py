"""Source-scoped administrative lookup; never chooses an ambiguous first match."""
from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType

from app.services.philippine_location_service import COMMON_ALIASES, PhilippineLocationService
from app.services.news_ner.context_association_v42 import segments


@dataclass(frozen=True)
class Entry:
    name: str
    city: str
    code: str
    region: str
    province: str


def name_key(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip().casefold())
    return COMMON_ALIASES.get(value, value).casefold()


class Catalog:
    def __init__(self, reference: PhilippineLocationService) -> None:
        if not reference._loaded or not reference.cities or not reference.barangays:
            raise ValueError("geography_unavailable")
        self.cities = MappingProxyType({key: tuple(sorted({Entry(r['name'], r['name'], r['psgc_code'], r['region'], r['province'])
            for r in rows}, key=lambda e:e.code)) for key, rows in reference.cities.items()})
        self.barangays = MappingProxyType({key: tuple(sorted({Entry(r['name'], r['city_municipality'], r['psgc_code'], r['region'], r['province'])
            for r in rows}, key=lambda e:e.code)) for key, rows in reference.barangays.items()})
        aliases = set(self.cities) | {a for a, b in COMMON_ALIASES.items() if b.casefold() in self.cities}
        self.city_pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(a) for a in sorted(aliases, key=lambda x:(-len(x),x))) + r")(?!\w)", re.I)

    def city(self, raw: str) -> tuple[Entry, ...]:
        return self.cities.get(name_key(raw), ())

    def barangay(self, raw: str, city: str) -> tuple[Entry, ...]:
        key = name_key(raw)
        short = re.sub(r"^(?:brgy\.?|barangay|bgy\.?)\s+", "", key)
        candidates = set(self.barangays.get(key, ()) + self.barangays.get(short, ()))
        return tuple(e for e in sorted(candidates, key=lambda e:e.code) if e.city == city)


def span(text: str, start: int, end: int) -> dict:
    return {"start": start, "end": end, "text": text[start:end]}


def _clause(text: str, mention: dict, mentions: list[dict], clause_segments: list[tuple[int,int]] | None=None) -> tuple[int, int]:
    bounds=segments(text,mentions) if clause_segments is None else clause_segments
    a,b = next(((a,b) for a,b in bounds if a <= mention['start'] < mention['end'] <= b), (mention['start'],mention['end']))
    boundaries = [(m.start(),m.end()) for m in re.finditer(r";|\b(?:whereas|meanwhile|samantala|habang)\b",text[a:b],re.I)]
    base=a
    for x,y in boundaries:
        if base+y <= mention['start']:a=base+y
        elif base+x >= mention['end']:
            b=base+x;break
    return a,b


def _heading(text: str, target: dict, graph: dict, catalog: Catalog) -> tuple[list[Entry], list[dict]]:
    """Only explicit administrative/list headings survive intervening list rows."""
    city: list[Entry] = []; evidence: list[dict] = []
    for match in re.finditer(r"[^\n]*(?:\n|$)",text[:target['start']]):
        if match.start()==match.end():continue
        line=match.group().strip();start=match.start();end=match.end()
        if not line:
            city=[];evidence=[];continue
        candidates=catalog.city(line.rstrip(':'))
        if candidates:
            city=list(candidates);evidence=[span(text,start,end-(1 if match.group().endswith('\n') else 0))];continue
        if re.fullmatch(r"(?:Brgy\.?|Barangay)\s+[^.!?:]+:?",line,re.I):
            continue
        # These are the unchanged graph's actual supported measured-list rows.
        row_targets=[m for m in graph['mentions'] if start <= m['start'] < m['end'] <= end and m['label'] in {'ROAD','LANDMARK','LOCAL_AREA','BARANGAY'}]
        measured=any(f['kind']=='depth' and any(start<=e['start']<e['end']<=end for e in f['evidence']) for f in graph['facts'])
        header=bool(re.search(r'\b(?:following|sumusunod|listed|below|listahan|talaan)\b',line,re.I)
                    and re.search(r'\b(?:flood\w*|baha|binaha)\b',line,re.I))
        if header or (row_targets and measured and re.search(r"[:–—-]",line) and not re.search(r"\b(?:meanwhile|samantala|update|later)\b",line,re.I)):
            continue
        city=[];evidence=[]
    return city,evidence


def resolve_locality(text: str, target: dict, graph: dict, catalog: Catalog,
                     *, clause_segments: list[tuple[int,int]] | None=None) -> dict:
    a,b=_clause(text,target,graph['mentions'],clause_segments);hits=[];evidence=[span(text,target['start'],target['end'])]
    for match in catalog.city_pattern.finditer(text,a,b):
        if any(m['label'] in {'ROAD','LANDMARK','LOCAL_AREA'} and m['start'] < match.end() and match.start() < m['end'] for m in graph['mentions']):
            continue
        # An opening dateline is not the affected site's administrative parent.
        tail=text[match.end():b]
        if match.start()==len(text)-len(text.lstrip()) and re.match(r"\s*(?:,\s*(?:Philippines|Pilipinas))?\s*(?:\([^)]*\))?\s*[—–-]",tail,re.I):
            continue
        hits.extend(catalog.city(match.group()));evidence.append(span(text,match.start(),match.end()))
    if target['label']=='CITY':hits=list(catalog.city(target['text']))
    if not hits:
        hits,heading=_heading(text,target,graph,catalog);evidence.extend(heading)
    unique={e.code:e for e in hits}
    result={"canonical_city":None,"canonical_barangay":None,"canonical_province":None,"psgc_code":None,
            "evidence":evidence,"reason":None}
    if len(unique)!=1:
        result['reason']='locality_ambiguous' if unique else 'locality_not_supported';return result
    city=next(iter(unique.values()))
    if city.region!='National Capital Region (NCR)':
        result['reason']='non_metro_locality';return result
    result.update(canonical_city=city.city,canonical_province=city.province or None,psgc_code=city.code)
    if target['label']=='BARANGAY':
        rows=catalog.barangay(target['text'],city.city)
        if len(rows)!=1:
            result.update(canonical_city=None,psgc_code=None,reason='barangay_parent_not_supported');return result
        result.update(canonical_barangay=rows[0].name,psgc_code=rows[0].code)
    else:
        names=[m for m in graph['mentions'] if m['label']=='BARANGAY' and a<=m['start']<m['end']<=b]
        rows={e.code:(e,m) for m in names for e in catalog.barangay(m['text'],city.city)}
        if len(rows)==1:
            row,m=next(iter(rows.values()));result['canonical_barangay']=row.name
            evidence.append(span(text,m['start'],m['end']))
    return result
