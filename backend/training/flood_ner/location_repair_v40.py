"""Offline, source-only location proposals; never changes the neural model."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
from typing import Any

VERSION = 'lanes-location-repair-v40'
FAMILIES = ('transport_asset', 'shared_locality', 'explicit_road')
METHODS = (*FAMILIES, 'combined')
LABELS = frozenset({'ROAD', 'LANDMARK', 'LOCAL_AREA', 'CITY', 'BARANGAY', 'PROVINCE'})
# Names must be complete bounded phrases, not suffix matches inside other names.
WORD = r"[A-ZÀ-Ý][\wÀ-ÿ]*(?:[.'’\-][\wÀ-ÿ]+)*\.?"
NAME = rf'{WORD}(?:[ \t]+{WORD}){{0,7}}'
ASSET = re.compile(rf'(?<![\w’\-])(?P<name>{NAME}[ \t]+(?:tunnel|underpass|overpass|bridge|station))\b')
ROAD = re.compile(rf'{NAME}[ \t]+(?:Road|Street|Avenue|Highway|Boulevard|Lane|Drive|Rd\.|St\.|Ave\.)')
LOCAL_LIST = re.compile(r'\b(?P<head>Puroks?|Sitios?)[ \t]+(?P<first>\d+[A-Za-z]?)(?P<tail>(?:[ \t]*(?:,|and|at|&)[ \t]*\d+[A-Za-z]?){1,10})\b', re.I)
ITEM = re.compile(r'(?:,|\band\b|\bat\b|&)[ \t]*(?P<item>\d+[A-Za-z]?)', re.I)
ORG = re.compile(r'\b(?:company|corporation|association|committee|board|project|proposal|planned|proposed|named|called|caption|label|sign|quote)\b', re.I)
BOUNDARY_BEFORE = re.compile(r'(?:^|[\n:;.!?]|\b(?:at|near|inside|outside|along|the|sa|ang|malapit\s+sa))[ \t]*$', re.I)
BOUNDARY_AFTER = re.compile(r'^(?:[ \t]*(?:NB/SB|NB|SB|northbound|southbound))?(?:[ \t]*(?::|;|,|\.|$)|[ \t]+(?:was|is|had|flooded|has|remains|binaha|ay|ang|lubog)\b)', re.I)


def object_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def validate(value: dict) -> None:
    if not isinstance(value, dict) or set(value) != {'record_id', 'text', 'mentions'}:
        raise ValueError('opaque identity, unchanged text and original mentions only')
    if not isinstance(value['record_id'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,90}', value['record_id']):
        raise ValueError('invalid opaque identity')
    text = value['text']
    if not isinstance(text, str) or len(text) > 100000 or not isinstance(value['mentions'], list):
        raise ValueError('bounded text and explicit mention list required')
    end = 0
    ids = set()
    for m in value['mentions']:
        if not isinstance(m, dict) or set(m) != {'id', 'start', 'end', 'text', 'label', 'provenance_sha256'}:
            raise ValueError('exact original mention fields required')
        if (type(m['start']) is not int or type(m['end']) is not int or
                not 0 <= end <= m['start'] < m['end'] <= len(text) or
                text[m['start']:m['end']] != m['text'] or m['label'] not in LABELS):
            raise ValueError('invalid label, original Unicode slice or overlap')
        if (not isinstance(m['id'], str) or not m['id'] or m['id'] in ids or
                not isinstance(m['provenance_sha256'], str) or
                not re.fullmatch('[a-f0-9]{64}', m['provenance_sha256'])):
            raise ValueError('unique identity and provenance required')
        ids.add(m['id']); end = m['end']


def propose(value: dict, method: str = 'combined') -> dict:
    """A separate effective mention view with explicit rule provenance; no I/O."""
    validate(value)
    if method not in METHODS:
        raise ValueError('unknown predeclared method')
    enabled = set(FAMILIES) if method == 'combined' else {method}
    text = value['text']; original = deepcopy(value['mentions'])
    proposals: list[dict] = []; abstentions: list[dict] = []

    def evidence(a: int, b: int) -> dict:
        return {'start': a, 'end': b, 'text': text[a:b]}

    def blocked(family: str, start: int, end: int, reason: str) -> None:
        abstentions.append({'family': family, 'evidence': evidence(start, end), 'reason': reason})

    def offer(family: str, start: int, end: int, label: str, before: dict | None, proof: dict) -> None:
        proposal = {'family': family, 'action': 'retag' if before else 'add',
                    'start': start, 'end': end, 'text': text[start:end], 'label': label,
                    'original_mention_id': before['id'] if before else None, 'evidence': proof,
                    'origin': 'rule_proposal_not_neural', 'implementation': VERSION}
        proposal['provenance_sha256'] = object_sha(proposal)
        proposals.append(proposal)

    if 'transport_asset' in enabled:
        for hit in ASSET.finditer(text):
            a, b = hit.span('name')
            prefix = re.match(r'(?:At|Near|Inside|Outside|Along|Sa)[ \t]+', text[a:b])
            if prefix:
                a += prefix.end()
            left = text[max(0, a-80):a]; right = text[b:min(len(text), b+100)]
            # Check the entire local clause for nonphysical/caption/project use.
            lo = max(text.rfind(c, 0, a) for c in ('\n', '.', ';', ':')) + 1
            hi = min((i for c in ('\n', '.', ';') if (i := text.find(c, b)) >= 0), default=len(text))
            if not BOUNDARY_BEFORE.search(left) or not BOUNDARY_AFTER.search(right) or ORG.search(text[lo:hi]):
                blocked('transport_asset', a, b, 'complete physical name boundaries or sense uncertain'); continue
            overlaps = [m for m in original if max(a, m['start']) < min(b, m['end'])]
            if overlaps:
                if not any((m['start'], m['end'], m['label']) == (a, b, 'LANDMARK') for m in overlaps):
                    blocked('transport_asset', a, b, 'overlaps an original mention; no resize or replacement')
                continue
            offer('transport_asset', a, b, 'LANDMARK', None, evidence(lo, hi))
    if 'shared_locality' in enabled:
        for hit in LOCAL_LIST.finditer(text):
            after = text[hit.end():hit.end()+30]
            if re.match(r'[ \t]+(?:residents|families|houses|people|pamilya|bahay|tao)\b', after, re.I):
                blocked('shared_locality', hit.start(), hit.end(), 'count rather than locality list'); continue
            # Require a recognized designator-bearing first member; context alone
            # cannot create the continuation or repair an unrelated occurrence.
            first_a, first_b = hit.start('head'), hit.end('first')
            anchor = [m for m in original if (m['start'], m['end'], m['label']) == (first_a, first_b, 'LOCAL_AREA')]
            if len(anchor) != 1:
                blocked('shared_locality', hit.start(), hit.end(), 'no exact local-area anchor'); continue
            for item in ITEM.finditer(hit.group('tail')):
                a = hit.start('tail') + item.start('item'); b = hit.start('tail') + item.end('item')
                matching = [m for m in original if (m['start'], m['end']) == (a, b)]
                if len(matching) != 1:
                    blocked('shared_locality', a, b, 'no original exact continuation span'); continue
                if matching[0]['label'] != 'LOCAL_AREA':
                    offer('shared_locality', a, b, 'LOCAL_AREA', matching[0], evidence(hit.start(), hit.end()))
    if 'explicit_road' in enabled:
        for m in original:
            if m['label'] == 'ROAD' or not ROAD.fullmatch(m['text']):
                continue
            a, b = m['start'], m['end']; before = text[max(0, a-75):a]; after = text[b:b+75]
            lo = max(text.rfind(c, 0, a) for c in ('\n', '.', ';', ':')) + 1
            hi = min((i for c in ('\n', '.', ';') if (i := text.find(c, b)) >= 0), default=len(text))
            if (not BOUNDARY_BEFORE.search(before) or not BOUNDARY_AFTER.search(after) or
                    ORG.search(text[lo:hi])):
                blocked('explicit_road', a, b, 'name boundary or physical-road sense uncertain'); continue
            offer('explicit_road', a, b, 'ROAD', m, evidence(lo, hi))

    rejected: set[int] = set()
    for i, a in enumerate(proposals):
        for j, b in enumerate(proposals[:i]):
            if max(a['start'], b['start']) < min(a['end'], b['end']):
                rejected.update((i, j))
    accepted = [p for i, p in enumerate(proposals) if i not in rejected]
    for i in sorted(rejected):
        p = proposals[i]; blocked(p['family'], p['start'], p['end'], 'conflicting proposed spans; abstain')
    replacements = {p['original_mention_id']: p for p in accepted if p['action'] == 'retag'}
    effective = deepcopy(original)
    for m in effective:
        if m['id'] in replacements:
            p = replacements[m['id']]; m.update(label=p['label'], provenance_sha256=p['provenance_sha256'])
    for p in accepted:
        if p['action'] == 'add':
            identity = 'rule-' + p['provenance_sha256'][:24]
            if any(m['id'] == identity for m in effective):
                raise ValueError('proposed identity collision')
            effective.append({'id': identity, **{k: p[k] for k in ('start', 'end', 'text', 'label', 'provenance_sha256')}})
    effective.sort(key=lambda m: (m['start'], m['end']))
    validate({**value, 'mentions': effective})
    return {'schema': VERSION, 'record_id': value['record_id'], 'method': method,
            'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'neural_mentions': original, 'effective_mentions': effective,
            'proposals': accepted, 'abstentions': abstentions}
