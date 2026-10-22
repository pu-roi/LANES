"""Conservative training-study proposals; text/opaque ID/original spans only."""
from __future__ import annotations

from copy import deepcopy
import re

from training.flood_ner.context_safeguards import evidence, require, validate_predictions

RULES = {
    'terminal_descriptor': {'family': 'trimming', 'scope': 'Trim separable terminal Intersection/Junction after an explicit road name.'},
    'traffic_direction': {'family': 'trimming', 'scope': 'Trim a terminal traffic qualifier after an explicit road name.'},
    'explicit_crossing': {'family': 'splitting', 'scope': 'Split one explicit cor./corner connector with two complete road names.'},
}
TOKEN = r"(?:[A-ZÀ-ÖØ-Þ0-9][\w.’'-]*|de|del|la|na|of|the|and)"
SUFFIX = r'(?:Road|Street|Avenue|Boulevard|Highway|Lane|Drive|Rd\.|St\.|Ave\.?|Blvd\.?)'
ROAD_NAME = re.compile(TOKEN + r'(?:[ \t]+' + TOKEN + r'){0,11}[ \t]+' + SUFFIX)
NUMBERED = re.compile(r'(?:Road|Route|Highway)[ \t]+[0-9]+[A-Z]?(?:-[A-Z0-9]+)?')
CONNECTOR = re.compile(r'[ \t]+(?P<cue>cor\.?|corner)[ \t]+', re.I)
DESCRIPTOR = re.compile(r'[ \t]+(?:Intersection|Junction)$', re.I)
DIRECTION = r'(?:northbound|southbound|eastbound|westbound|NB|SB|EB|WB)(?:/(?:northbound|southbound|eastbound|westbound|NB|SB|EB|WB))?'
TRAFFIC = re.compile(r'[ \t]+(?:' + DIRECTION + r'|\(' + DIRECTION + r'\))$', re.I)
NAMED = re.compile(r'\b(?:named|called|pinangalanang|pangalan)\s*$', re.I)


def explicit_road(raw):
    return bool((ROAD_NAME.fullmatch(raw) or NUMBERED.fullmatch(raw)) and not CONNECTOR.search(raw))


def proposals(text, start, end, enabled):
    raw = text[start:end]; candidates = []; holds = []
    named = bool(NAMED.search(text[max(0, start - 50):start]))
    def consider(rule, children, supported, reason):
        if rule not in enabled: return
        if supported and not named:
            candidates.append({'rule_id': rule, 'children': children, 'reason': reason,
                               'evidence': evidence(text, start, end)})
        else:
            holds.append({'rule_id': rule, 'reason': 'ambiguous name, compound or incomplete textual road cues',
                          'evidence': evidence(text, start, end)})
    for rule, pattern in [('terminal_descriptor', DESCRIPTOR), ('traffic_direction', TRAFFIC)]:
        match = pattern.search(raw)
        if match:
            core = raw[:match.start()]
            consider(rule, [[start, start + len(core), 'ROAD']], explicit_road(core),
                     'explicit road name followed by a separate terminal descriptor/traffic qualifier')
    connectors = list(CONNECTOR.finditer(raw))
    if connectors:
        cue = connectors[0]; left, right = raw[:cue.start()], raw[cue.end():]
        supported = len(connectors) == 1 and explicit_road(left) and explicit_road(right)
        # Title-case Corner can be integral to a name; no geographic lookup resolves it here.
        supported &= cue['cue'] == cue['cue'].lower() or cue['cue'] == cue['cue'].upper()
        consider('explicit_crossing', [[start, start + len(left), 'ROAD'], [start + cue.end(), end, 'ROAD']],
                 supported, 'one explicit crossing connector between two complete road names')
    return candidates, holds


def resolve(original, candidates, holds):
    choices = {tuple(tuple(s) for s in c['children']) for c in candidates}
    abstained = bool(holds) or len(choices) > 1
    children = [list(s) for s in original] if abstained or not candidates else [list(s) for s in next(iter(choices))]
    action = 'keep' if children == [list(s) for s in original] else 'split' if len(children) > 1 else 'trim'
    return children, action, abstained


def check_output(text, originals, decisions, shadow):
    validate_predictions(text, originals); validate_predictions(text, shadow)
    require(len(originals) == len(decisions), 'decision roster mismatch')
    flattened = []
    for old, decision in zip(originals, decisions):
        require(decision['original'] == list(old) and decision['action'] in ('keep', 'trim', 'split'), 'invalid original/action')
        children = decision['children']
        require(children and all(old[0] <= c[0] < c[1] <= old[1] and c[2] == old[2] for c in children),
                'prefix expansion, retag or detached addition forbidden')
        if old[2] != 'ROAD' or decision['action'] == 'keep': require(children == [list(old)], 'unchanged entity modified')
        if decision['action'] == 'trim': require(len(children) == 1 and children != [list(old)], 'invalid trim')
        if decision['action'] == 'split': require(len(children) == 2 and children[0][1] <= children[1][0], 'invalid split')
        flattened.extend(children)
    require(flattened == shadow, 'shadow/decisions differ')


def propose(record_id, text, predictions, *, enabled=None):
    require(isinstance(record_id, str) and record_id, 'opaque ID required')
    original = deepcopy(predictions); spans = validate_predictions(text, predictions)
    enabled = set(RULES) if enabled is None else set(enabled)
    require(enabled <= set(RULES), 'unknown boundary rule')
    decisions = []; shadow = []
    for start, end, label in spans:
        candidates, holds = proposals(text, start, end, enabled) if label == 'ROAD' else ([], [])
        children, action, abstained = resolve([[start, end, label]], candidates, holds)
        decisions.append({'original': [start, end, label], 'children': children, 'action': action,
            'abstained': abstained, 'rule_ids': sorted({c['rule_id'] for c in candidates + holds}),
            'evidence': [c['evidence'] for c in candidates + holds], 'rule_evidence': candidates + holds,
            'reason': 'ambiguous/conflicting proposals; preserve original' if abstained else
                      'supported contained boundary proposal' if candidates else 'no supported boundary cue; preserve original'})
        shadow.extend(children)
    check_output(text, predictions, decisions, shadow)
    require(predictions == original, 'original predictions mutated')
    return {'record_id': record_id, 'decisions': decisions, 'shadow': shadow}


def raw_record(value, *, enabled=None):
    require(isinstance(value, dict) and set(value) == {'record_id', 'text', 'prediction'},
            'only opaque ID, unchanged text and original predictions accepted')
    return propose(value['record_id'], value['text'], value['prediction'], enabled=enabled)
