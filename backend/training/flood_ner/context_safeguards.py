"""Text-only shadow proposals. No references, resources or model dependencies."""
from __future__ import annotations

from copy import deepcopy
import re

LABELS = frozenset({'ROAD', 'LANDMARK', 'LOCAL_AREA', 'BARANGAY', 'CITY', 'PROVINCE'})
RULES = {
    'agency_actor': {'family': 'organization_role', 'action': 'drop',
        'scope': 'A named agency in explicit reporting/warning actor syntax; physical context vetoes.'},
    'attribution_role': {'family': 'organization_role', 'action': 'drop',
        'scope': 'PIO in explicit professional apposition or a bounded quoted-unit attribution.'},
    'named_asset': {'family': 'road_facility', 'action': 'retag',
        'scope': 'Integral named-road suffix, or named physical-facility suffix with physical context.'},
    'explicit_barangay': {'family': 'administrative_locality', 'action': 'retag',
        'scope': 'Complete predicted span starts with barangay/brgy and has a named or numbered identifier.'},
    'explicit_locality': {'family': 'administrative_locality', 'action': 'retag',
        'scope': 'Complete predicted span starts with sitio/purok and has an integral identifier.'},
    'shared_identifier': {'family': 'administrative_locality', 'action': 'retag',
        'scope': 'Later exact one-token/numeric item in a bounded explicit barangay/sitio/purok list.'},
}
NAME = r"[A-ZÀ-ÖØ-Þ][\w’'-]*"
IDENT = r"(?:[0-9]+[A-Za-z]?(?:-[A-Za-z0-9]+)?|" + NAME + r")"
ORG = re.compile(r'\b(?:Department|Office|Bureau)\s+(?:of|for)\s+' + NAME +
    r'(?:[ \t]+(?:' + NAME + r'|of|and|the|for)){0,7}')
REPORT_AFTER = re.compile(r'^\s+(?:said|reported|announced|warned)\b', re.I)
REPORT_BEFORE = re.compile(r'(?:nagpaalala|nagbabala|iniulat)(?:\s+naman)?\s+(?:ang|ng)\s*$', re.I)
ROAD = re.compile(r'^.+\s(?:Road|Street|Avenue|Boulevard|Highway|Lane|Drive|Rd\.|St\.|Ave\.|Blvd\.)$')
ASSET = re.compile(r'^.+\s(?:Bridge|Underpass|Tunnel|Terminal|Market|Hospital|School|Center|Centre|Mall|Station|Hall)$')
PHYSICAL = re.compile(r'\b(?:at|near|beside|inside|outside|reached|covered|flooded|repaired|closed|'
    r'building|headquarters|binaha|nilinis|lubog|nasa|malapit|katabi)\b', re.I)
ORG_TAIL = re.compile(r'^\s+(?:board|committee|association|company|said|reported|announced)\b', re.I)
ADMIN = re.compile(r'^(?:Barangays?|Brgys?\.?)(?:\s+ng)?\s+\S', re.I)
LOCAL = re.compile(r'^(?:Sitios?|Puroks?)\s+\S', re.I)
LIST_HEAD = re.compile(r'\b(?P<head>Barangays?|Brgys?\.?|Sitios?|Puroks?)[ \t]+(?P<first>' + IDENT + r')')
NEXT_ITEM = re.compile(r'(?:[ \t]*,[ \t]*(?:(?:and|at)[ \t]+)?|[ \t]+(?:and|at)[ \t]+)(?P<item>' + IDENT + r')')
COUNT_TAIL = re.compile(r'^\s+(?:families|people|residents|vehicles|hours|minutes|children|pamilya|tao|bata)\b', re.I)


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def validate_predictions(text, predictions):
    require(isinstance(text, str) and bool(text) and isinstance(predictions, list), 'text and explicit predictions required')
    spans = []
    for span in predictions:
        require(isinstance(span, (list, tuple)) and len(span) == 3 and type(span[0]) is int
                and type(span[1]) is int and 0 <= span[0] < span[1] <= len(text)
                and span[2] in LABELS, 'invalid original Unicode span/type')
        spans.append(tuple(span))
    require(len(set(spans)) == len(spans), 'duplicate prediction')
    ordered = sorted(spans)
    require(all(a[1] <= b[0] for a, b in zip(ordered, ordered[1:])), 'overlapping predictions')
    return spans


def evidence(text, start, end):
    require(0 <= start < end <= len(text), 'invalid evidence offset')
    return {'start': start, 'end': end, 'text': text[start:end]}


def clause_window(text, start, end):
    left = max(text.rfind(c, 0, start) for c in ('\n', ';', '!', '?')) + 1
    right = min((pos for c in ('\n', ';', '!', '?') if (pos := text.find(c, end)) >= 0), default=len(text))
    return max(left, start - 100), min(right, end + 100)


def shared_items(text):
    result = []
    for head in LIST_HEAD.finditer(text):
        cursor = head.end(); items = []
        while len(items) < 12:
            item = NEXT_ITEM.match(text, cursor)
            if not item:
                break
            items.append(item); cursor = item.end()
        if not items:
            continue
        label = 'BARANGAY' if head['head'].lower().startswith(('barangay', 'brgy')) else 'LOCAL_AREA'
        blocked = bool(COUNT_TAIL.match(text[cursor:])) or bool(NEXT_ITEM.match(text, cursor))
        # Multiword entries or a different designator cannot establish a one-token continuation.
        blocked |= bool(re.match(r'[ \t]+' + NAME, text[cursor:]))
        for item in items:
            result.append({'start': item.start('item'), 'end': item.end('item'), 'label': label,
                'blocked': blocked, 'evidence': evidence(text, head.start(), cursor)})
    return result


def propose(record_id, text, predictions, *, enabled=None):
    """One pass over original spans. References/labels other than predictions are not inputs."""
    require(isinstance(record_id, str) and bool(record_id), 'opaque record ID required')
    original = deepcopy(predictions); spans = validate_predictions(text, predictions)
    enabled = set(RULES) if enabled is None else set(enabled)
    require(enabled <= set(RULES), 'unknown rule ID')
    lists = shared_items(text)
    decisions, shadow = [], []
    for ordinal, (start, end, label) in enumerate(spans):
        raw = text[start:end]; lo, hi = clause_window(text, start, end)
        before, after = text[lo:start], text[end:hi]
        cues, blocked = [], []
        def cue(rule_id, target, proof):
            if rule_id in enabled:
                cues.append({'rule_id': rule_id, 'target': target, 'evidence': proof})
        def abstain(rule_id, reason):
            if rule_id in enabled:
                blocked.append({'rule_id': rule_id, 'reason': reason, 'evidence': evidence(text, start, end)})
        road = bool(ROAD.fullmatch(raw))
        facility = bool(ASSET.fullmatch(raw))
        physical = bool(PHYSICAL.search(before[-55:] + ' ' + raw + ' ' + after[:35]))
        named_building = bool(re.search(r'building (?:named|na pinangalanang)\s*$', before, re.I))
        for org in ORG.finditer(text, lo, hi):
            if not org.start() <= start < end <= org.end():
                continue
            acting = bool(REPORT_AFTER.match(text[org.end():hi]) or REPORT_BEFORE.search(text[lo:org.start()]))
            if named_building:
                continue  # Explicit fictional/real text can establish a physical name without geography lookup.
            if acting and not physical:
                cue('agency_actor', None, evidence(text, lo, hi))
            else:
                abstain('agency_actor', 'organizational sense lacks an unambiguous actor cue or conflicts with physical context')
        if re.fullmatch('PIO', raw):
            professional = bool(re.search(r'\b(?:Officer|Captain|Spokesperson|Opisyal)\b', before, re.I)
                                and re.search(r',\s*$', before) and re.match(r'\s*[,;]', after))
            attribution = bool(re.search(r'[,"”]\s*' + NAME + r'\s*$', before) and re.match(r'\s*[.,]', after))
            if (professional or attribution) and not physical:
                cue('attribution_role', None, evidence(text, lo, hi))
            else:
                abstain('attribution_role', 'role acronym without decisive attribution context')
        if road:
            cue('named_asset', 'ROAD', evidence(text, start, end))
        elif facility:
            if physical and not ORG_TAIL.match(after):
                cue('named_asset', 'LANDMARK', evidence(text, lo, hi))
            else:
                abstain('named_asset', 'facility-shaped name without decisive physical context')
        if ADMIN.match(raw):
            identifier = re.sub(r'^(?:Barangays?|Brgys?\.?)(?:\s+ng)?\s+', '', raw, flags=re.I)
            if re.match(IDENT, identifier):
                cue('explicit_barangay', 'BARANGAY', evidence(text, start, end))
        elif re.fullmatch(r'(?:Barangays?|Brgys?\.?)', raw, re.I):
            abstain('explicit_barangay', 'barangay designator lacks an identifier')
        if LOCAL.match(raw):
            identifier = re.sub(r'^(?:Sitios?|Puroks?)\s+', '', raw, flags=re.I)
            if re.match(IDENT, identifier):
                cue('explicit_locality', 'LOCAL_AREA', evidence(text, start, end))
        elif re.fullmatch(r'(?:Sitios?|Puroks?)', raw, re.I):
            abstain('explicit_locality', 'locality designator lacks an identifier')
        for item in lists:
            if item['start'] == start and item['end'] == end:
                if item['blocked']:
                    abstain('shared_identifier', 'list continuation conflicts with count or multiword context')
                else:
                    cue('shared_identifier', item['label'], item['evidence'])
        targets = {item['target'] for item in cues}
        # A decisive cue cannot resolve a conflicting or explicitly ambiguous cue.
        ambiguous = bool(blocked) or len(targets) > 1
        target = label if ambiguous or not cues else next(iter(targets))
        action = 'drop' if target is None else 'retag' if target != label else 'keep'
        row = {'prediction_index': ordinal, 'start': start, 'end': end, 'original_label': label,
               'proposed_label': target, 'action': action, 'abstained': ambiguous,
               'rule_ids': sorted({item['rule_id'] for item in cues + blocked}),
               'evidence': [item['evidence'] for item in cues + blocked],
               'rule_evidence': cues + blocked,
               'reason': 'conflicting/ambiguous cues; preserve original' if ambiguous else
                         'explicit text cue' if cues else 'no supported rule; preserve original'}
        decisions.append(row)
        if target is not None:
            shadow.append([start, end, target])
    require(predictions == original, 'input predictions mutated')
    validate_predictions(text, shadow)
    return {'record_id': record_id, 'decisions': decisions, 'shadow': shadow}


def raw_record(value, *, enabled=None):
    require(isinstance(value, dict) and set(value) == {'record_id', 'text', 'prediction'},
            'decision input accepts only opaque ID, text and predictions')
    return propose(value['record_id'], value['text'], value['prediction'], enabled=enabled)
