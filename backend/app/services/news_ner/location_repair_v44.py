"""Offline source-delimited junction proposals; original neural spans are immutable."""
from __future__ import annotations

from copy import deepcopy
import re

from .location_repair_v40 import object_sha, validate

VERSION = 'lanes-location-repair-v44'
FAMILIES = ('missing_junction', 'boundary_replacement', 'junction_type')
METHODS = (*FAMILIES, 'combined')
CONNECTOR = re.compile(r'\s+(?:cor\.?|corner(?:\s+of)?|kanto\s+ng)\s+', re.I)
INTRO = re.compile(r'^(?:(?:at|sa|on|along)\s+)?(?:the\s+)?(?P<kind>intersection\s+of|junction\s+of|interseksiyon\s+ng|kanto\s+ng)\s+', re.I)
PREP = re.compile(r'^(?:(?:at|sa|on|along)\s+)', re.I)
DELIMITER = re.compile(r'\s+[-–—]\s+|\s*:\s*|\s*,\s*(?=(?:flood|baha|binaha|lubog|knee|waist|\d)\b)', re.I)
UNSAFE = re.compile(r'\b(?:company|corporation|association|committee|kompanya|samahan|project|proyekto|proposed|planned|caption|quote|named|called|office|barangay|brgy|city|province|lungsod|lalawigan)\b', re.I)
TOKEN = re.compile(r"[^\W\d_]+(?:[.'’\-][^\W\d_]+)*\.?", re.UNICODE)


def _name_supported(name: str) -> bool:
    words = name.split()
    return (1 <= len(words) <= 8 and not UNSAFE.search(name)
            and not (len(words) == 1 and (name.isupper() or re.fullmatch(r'Road|Street|Avenue|Daan|Kalsada', name)))
            and all(TOKEN.fullmatch(w) and w[0].isupper() for w in words)
            and any(len(re.sub(r'\W', '', w)) > 2 for w in words))


def junction_spans(text: str) -> list[dict]:
    """Only complete line-local explicit junction subjects; no measurement inference."""
    rows = []
    offset = 0
    for line in text.splitlines(keepends=True):
        clean = line.rstrip('\r\n')
        # A decorative marker is not part of the name or its evidence boundaries.
        left = len(clean) - len(clean.lstrip(' \t🌧☔•'))
        subject = clean[left:]
        delim = DELIMITER.search(subject)
        if delim:
            subject = subject[:delim.start()]
        subject = subject.rstrip(' \t')
        start = offset + left
        intro = INTRO.match(subject)
        if intro:
            start += intro.end(); subject = subject[intro.end():]
            connectors = list(re.finditer(r'\s+(?:and|at|&)\s+', subject, re.I))
        else:
            prep = PREP.match(subject)
            if prep:
                start += prep.end(); subject = subject[prep.end():]
            connectors = list(CONNECTOR.finditer(subject))
        if len(connectors) == 1:
            connector = connectors[0]
            parts = [(0, connector.start()), (connector.end(), len(subject))]
            names = []
            for a, b in parts:
                while a < b and subject[a].isspace(): a += 1
                while b > a and subject[b-1].isspace(): b -= 1
                names.append({'start': start+a, 'end': start+b, 'text': subject[a:b]})
            rows.append({'names': names, 'supported': all(_name_supported(n['text']) for n in names),
                         'evidence': {'start': offset+left, 'end': offset+len(clean), 'text': clean[left:]}})
        offset += len(line)
    return rows


def propose(value: dict, method: str = 'combined', *, neural_mentions: list[dict] | None = None) -> dict:
    """Compose on a saved control; replacements exist only in the effective view."""
    validate(value)
    if method not in METHODS:
        raise ValueError('unknown predeclared method')
    original = deepcopy(value['mentions'] if neural_mentions is None else neural_mentions)
    validate({**value, 'mentions': original})
    control = deepcopy(value['mentions'])
    enabled = set(FAMILIES) if method == 'combined' else {method}
    offers: list[dict] = []; abstentions: list[dict] = []
    for row in junction_spans(value['text']):
        if not row['supported']:
            abstentions.append({'reason': 'incomplete, abbreviated, numbered or ambiguous junction name', 'evidence': row['evidence']})
            continue
        for target in row['names']:
            a, b = target['start'], target['end']
            overlaps = [m for m in control if max(a, m['start']) < min(b, m['end'])]
            before = overlaps[0] if len(overlaps) == 1 else None
            exact = before is not None and (before['start'], before['end']) == (a, b)
            family = None
            if not overlaps:
                family = 'missing_junction'
            elif len(overlaps) > 1:
                abstentions.append({'reason': 'multiple overlapping control mentions', 'evidence': row['evidence']}); continue
            elif exact:
                if before['label'] == 'ROAD': continue
                if before['label'] in {'LANDMARK', 'LOCAL_AREA'}:
                    abstentions.append({'reason': 'compatible but uncertain place sense retained', 'evidence': row['evidence']}); continue
                family = 'junction_type'
            else:
                # Resize only a single existing ROAD contained within this name,
                # or a name followed solely by an explicit junction connector.
                contained = a <= before['start'] < before['end'] <= b
                over = before['start'] == a and before['end'] > b and bool(re.fullmatch(
                    r'\s+(?:cor\.?|corner(?:\s+of)?|kanto\s+ng)\s*', value['text'][b:before['end']], re.I))
                if before['label'] != 'ROAD' or not (contained or over):
                    abstentions.append({'reason': 'unsupported boundary or type conflict', 'evidence': row['evidence']}); continue
                family = 'boundary_replacement'
            if family not in enabled: continue
            proposal = {**target, 'label': 'ROAD', 'family': family,
                        'action': {'missing_junction': 'add', 'boundary_replacement': 'replace', 'junction_type': 'retag'}[family],
                        'original_mention_id': before['id'] if before else None,
                        'evidence': deepcopy(row['evidence']), 'origin': 'rule_proposal_not_neural', 'implementation': VERSION}
            proposal['provenance_sha256'] = object_sha(proposal)
            if proposal not in offers: offers.append(proposal)
    rejected: set[int] = set()
    for i, a in enumerate(offers):
        for j, b in enumerate(offers[:i]):
            if (max(a['start'], b['start']) < min(a['end'], b['end']) or
                    a['original_mention_id'] is not None and a['original_mention_id'] == b['original_mention_id']):
                rejected.update((i, j))
    accepted = [p for i, p in enumerate(offers) if i not in rejected]
    for i in sorted(rejected):
        abstentions.append({'reason': 'conflicting proposals; no precedence', 'evidence': offers[i]['evidence']})
    replacements = {p['original_mention_id']: p for p in accepted if p['original_mention_id']}
    effective = []
    for m in control:
        if m['id'] not in replacements: effective.append(deepcopy(m)); continue
        p = replacements[m['id']]
        effective.append({'id': m['id'], **{k: p[k] for k in ('start', 'end', 'text', 'label', 'provenance_sha256')}})
    for p in accepted:
        if p['action'] == 'add':
            effective.append({'id': 'v44-'+p['provenance_sha256'][:24],
                              **{k: p[k] for k in ('start', 'end', 'text', 'label', 'provenance_sha256')}})
    effective.sort(key=lambda m: (m['start'], m['end']))
    validate({**value, 'mentions': effective})
    return {'schema': VERSION, 'record_id': value['record_id'], 'method': method,
            'text_sha256': object_text_sha(value['text']), 'neural_mentions': original,
            'control_mentions': control, 'effective_mentions': effective, 'proposals': accepted, 'abstentions': abstentions}


def object_text_sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
