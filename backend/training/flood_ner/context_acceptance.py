"""Offline reference qualification only; never extraction, training or admission."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from training.flood_ner.annotation.schema import AnnotationRecord, PLACE_LABELS
from training.flood_ner.annotation.validation import validate_record
from training.flood_ner.annotation.context_review import contextual_semantic_errors

FAMILIES = ('row_measurements', 'separate_depth_shared_time', 'shared_depth',
            'ranges_qualifiers', 'scope_boundaries', 'forecast', 'negation',
            'historical_update', 'observation_onset', 'recession_clearance')


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def exact_occurrence(text: str, phrase: str, occurrence: int) -> dict:
    """The author must explicitly select an occurrence; never relocate a span."""
    require(type(occurrence) is int and occurrence >= 0 and bool(phrase), 'explicit occurrence required')
    hits = [m.start() for m in re.finditer(re.escape(phrase), text)]
    require(occurrence < len(hits), 'requested occurrence absent')
    start = hits[occurrence]
    return {'start': start, 'end': start + len(phrase), 'text': phrase}


def validate_revision(original: dict, proposed: dict, current: dict, tokenizer: Any) -> list[str]:
    errors = []
    for key in ('record_id', 'text', 'text_sha256', 'source', 'passage_start', 'passage_end', 'passage_language', 'split'):
        # Source admission metadata differs between old pilot and admitted records;
        # proposed source must remain byte-equivalent to its historical reference.
        if proposed.get(key) != original.get(key):
            errors.append('changed historical field: ' + key)
    if current.get('split') != 'train' or proposed.get('split') != 'train':
        errors.append('training-only references required; validation/holdout forbidden')
    for key in ('record_id', 'text', 'text_sha256', 'passage_start', 'passage_end', 'passage_language'):
        if proposed.get(key) != current.get(key):
            errors.append('current source-window mismatch: ' + key)
    for key in ('source_id', 'url', 'capture_version', 'text_sha256'):
        if proposed.get('source', {}).get(key) != current.get('source', {}).get(key):
            errors.append('current source mismatch: ' + key)
    places = [e for e in proposed.get('entities', []) if e.get('label') in PLACE_LABELS]
    if places != current.get('entities'):
        errors.append('current location references must be preserved exactly')
    try:
        record = AnnotationRecord.model_validate_json(json.dumps(proposed))
        if record.annotation_profile != 'context-rich-v1' or record.quality != 'silver':
            errors.append('context-rich silver proposal required')
        errors.extend(validate_record(record, tokenizer))
        errors.extend(e for fact in record.facts for e in contextual_semantic_errors(fact))
    except (ValueError, TypeError) as exc:
        errors.append('invalid reference schema: ' + type(exc).__name__)
    return errors


def literal_coverage(record: dict, exceptions: list[dict]) -> list[str]:
    """Require a disposition for repeats of each annotated contextual literal.

    This is a repeat guard, not an automatic completeness or geographic oracle.
    An enclosing same-label annotation covers a contained literal occurrence.
    """
    errors = []; text = record['text']; used = set()
    for exception in exceptions:
        if set(exception) != {'start', 'end', 'label', 'reason'} or not exception.get('reason'):
            return ['explicit source-bound repeat exception required']
        if not (type(exception['start']) is int and type(exception['end']) is int and
                0 <= exception['start'] < exception['end'] <= len(text) and exception['label'] in {'DEPTH', 'TIME'}):
            return ['invalid repeat exception span']
    contextual = [e for e in record['entities'] if e['label'] in {'DEPTH', 'TIME'}]
    for phrase, label in sorted({(e['text'], e['label']) for e in contextual}):
        for hit in re.finditer(re.escape(phrase), text):
            if any(e['label'] == label and e['start'] <= hit.start() and e['end'] >= hit.end() for e in contextual):
                continue
            matched = [i for i, x in enumerate(exceptions) if (x['start'], x['end'], x['label']) == (hit.start(), hit.end(), label)]
            if len(matched) != 1:
                errors.append('unreviewed repeated contextual occurrence')
            else:
                used.add(matched[0])
    if used != set(range(len(exceptions))):
        errors.append('unused or duplicated repeat exception')
    return errors


def validate_review(proposal: dict, review: dict) -> list[str]:
    errors = []
    if set(review) != {'record_id', 'proposal_sha256', 'disposition', 'completeness', 'unassigned_facts',
                       'repeat_exceptions', 'issues', 'evidence', 'drafting_basis'}:
        return ['exact source-review fields required']
    if review['record_id'] != proposal['record_id'] or review['proposal_sha256'] != object_sha(proposal):
        errors.append('stale review binding')
    required = {'locations', 'depth', 'time', 'status', 'access', 'associations'}
    if set(review['completeness']) != required or any(type(v) is not bool for v in review['completeness'].values()):
        errors.append('explicit field completeness required')
    if review['disposition'] not in {'retain_proposed', 'correct_proposed', 'hold'}:
        errors.append('invalid disposition')
    eligible = review['disposition'] != 'hold'
    if eligible and (not proposal['complete'] or proposal['review_status'] != 'accepted' or
                     not all(review['completeness'].values())):
        errors.append('incomplete references held; never negatives')
    if not eligible and (proposal['complete'] or proposal['review_status'] != 'unresolved' or not review['issues']):
        errors.append('holds require incomplete unresolved reference and issues')
    if not review['evidence'] or review['drafting_basis'] != 'source_and_historical_reference_only_not_blinded':
        errors.append('source-only drafting evidence required; prior exposure acknowledged')
    for evidence in review['evidence']:
        if (not isinstance(evidence, dict) or set(evidence) != {'source_sha256', 'passage_sha256', 'source_window', 'reviewed_extent'} or
                evidence['source_sha256'] != proposal['source']['text_sha256'] or
                evidence['passage_sha256'] != proposal['text_sha256'] or
                evidence['source_window'] != [proposal['passage_start'], proposal['passage_end']] or
                not (len(evidence['reviewed_extent']) == 2 and
                     0 <= evidence['reviewed_extent'][0] <= proposal['passage_start'] < proposal['passage_end'] <=
                     evidence['reviewed_extent'][1] <= len(proposal['source']['text']))):
            errors.append('source-bound review extent required')
    linked = {x['fact_id'] for x in proposal['relations']}
    unlinked = {f['id'] for f in proposal['facts']} - linked
    if set(review['unassigned_facts']) != unlinked or not all(review['unassigned_facts'].values()):
        errors.append('every unlinked fact needs an explicit scope disposition')
    errors.extend(literal_coverage(proposal, review['repeat_exceptions']))
    return errors


def validate_case(case: dict, tokenizer: Any) -> list[str]:
    errors = []
    if set(case) != {'case_id', 'family', 'language', 'contrast', 'record', 'expected', 'reason'}:
        return ['exact fictional case fields required']
    if case['family'] not in FAMILIES or case['language'] not in {'english', 'taglish'} or case['contrast'] not in {'supported', 'counterexample'}:
        errors.append('invalid fictional matrix member')
    try:
        r = AnnotationRecord.model_validate_json(json.dumps(case['record']))
        errors.extend(validate_record(r, tokenizer))
        if r.quality != 'constructed' or r.source.origin != 'constructed_fixture' or r.split is not None:
            errors.append('fixtures never corpus membership')
        if not r.complete or r.review_status != 'accepted' or r.passage_language != case['language']:
            errors.append('complete constructed reference required')
        errors.extend(e for f in r.facts for e in contextual_semantic_errors(f))
        expected = case['expected']
        if set(expected) != {'relations', 'unassigned_fact_ids', 'must_not_infer', 'absolute_instants'}:
            errors.append('explicit expected association contract required')
        if expected['relations'] != [x.model_dump(mode='json') for x in r.relations]:
            errors.append('expected relationship/reference disagreement')
        if set(expected['unassigned_fact_ids']) != {f.id for f in r.facts} - {x.fact_id for x in r.relations}:
            errors.append('unassigned fixture facts unaccounted')
        if expected['absolute_instants'] != [] or not expected['must_not_infer']:
            errors.append('no invented timestamp or unspecified inference boundary')
    except (TypeError, ValueError, KeyError):
        errors.append('invalid constructed reference')
    return errors


def validate_matrix(cases: list[dict], tokenizer: Any) -> list[str]:
    errors = []
    expected = Counter((f, l, c) for f in FAMILIES for l in ('english', 'taglish') for c in ('supported', 'counterexample'))
    actual = Counter((x['family'], x['language'], x['contrast']) for x in cases)
    if actual != expected or len({x['case_id'] for x in cases}) != 40:
        errors.append('exact unique forty-case matrix required')
    for case in cases:
        errors.extend(case['case_id'] + ': ' + e for e in validate_case(case, tokenizer))
    return errors


def validate_source_use(records: list[dict], receipts: list[dict]) -> None:
    by_id = {r['record_id']: r for r in receipts}
    require(len(by_id) == len(receipts) == len(records) and set(by_id) == {r['record_id'] for r in records},
            'exact unique source-use coverage required')
    for record in records:
        use = by_id[record['record_id']]
        require(use['verified'] is True and use['scope'] == 'private_owner_only_academic_training_evaluation' and
                use['text_sha256'] == record['text_sha256'] and use['source_sha256'] == record['source']['text_sha256'] and
                [use['start'], use['end']] == [record['passage_start'], record['passage_end']],
                'unsupported source-use expansion')


def validate_raw_input(value: dict) -> None:
    require(set(value) == {'record_id', 'text', 'text_sha256', 'publication', 'mentions'}, 'references and outputs forbidden')
    require(isinstance(value['record_id'], str) and re.fullmatch(r'[A-Za-z0-9_-]{1,90}', value['record_id']) is not None,
            'opaque identity required')
    text = value['text']
    require(isinstance(text, str) and len(text) <= 100000 and
            hashlib.sha256(text.encode('utf-8')).hexdigest() == value['text_sha256'], 'original text hash required')
    publication = value['publication']
    if publication is not None:
        from datetime import datetime
        require(set(publication) == {'value', 'basis'} and bool(publication['basis']), 'supported publication metadata required')
        require(datetime.fromisoformat(publication['value']).utcoffset() is not None, 'aware publication timestamp required')
    require(isinstance(value['mentions'], list), 'authenticated mention list required')
    previous = -1; ids = set()
    for m in value['mentions']:
        require(set(m) == {'id', 'start', 'end', 'text', 'label', 'provenance_sha256'} and m['label'] in PLACE_LABELS,
                'six location labels only')
        require(type(m['start']) is int and type(m['end']) is int and previous <= m['start'] < m['end'] <= len(text) and
                text[m['start']:m['end']] == m['text'], 'exact nonoverlapping mentions required')
        require(isinstance(m['id'], str) and m['id'] and m['id'] not in ids and
                isinstance(m['provenance_sha256'], str) and re.fullmatch('[a-f0-9]{64}', m['provenance_sha256']) is not None,
                'unique hash-bound mention required')
        ids.add(m['id']); previous = m['end']


def install_reference_guards() -> None:
    """Block I/O side effects and model/prediction access in qualification workers."""
    import importlib.abc
    from training.flood_ner.corrected_rules_worker import install_guards
    # spaCy's CLI dependency probes local socket availability while importing.
    # Deny every dispatch/DNS/bind/process event from the start; permit only
    # construction during import, then install the unchanged stricter guard.
    def bootstrap(event: str, args: tuple) -> None:
        if ((event.startswith('socket.') and event not in {'socket.__new__', 'socket.gethostname'}) or
                event in {'subprocess.Popen', 'os.system', 'os.posix_spawn'}):
            raise RuntimeError('reference bootstrap: network/process dispatch forbidden')
    sys.addaudithook(bootstrap)
    class NoDatabase(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> None:
            if fullname.split('.')[0] in {'psycopg','psycopg2','asyncpg','sqlite3','pymysql','MySQLdb'}:
                raise RuntimeError('reference bootstrap: database driver forbidden')
    sys.meta_path.insert(0, NoDatabase())
    def hook(event: str, args: tuple) -> None:
        if event == 'open' and isinstance(args[0], (str, bytes)):
            name = '/' + str(args[0]).replace('\\', '/').lower().lstrip('/')
            if any(token in name for token in ('/model/ner/', '/model/tok2vec/', '/model-best/', '/model-last/',
                                                '/predictions.', '/raw-predictions.', '/rules.jsonl', '/research-holdout',
                                                '/heldout-', '/successor-holdout-')):
                raise RuntimeError('reference qualification forbids model, predictions and holdout inputs')
    sys.addaudithook(hook)
    # Tokenizer/Vocab reconstruction remains allowed; pipeline loading, inference
    # and training entry points are unavailable in this dedicated process.
    import spacy
    from spacy.language import Language
    install_guards()
    def blocked(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError('reference qualification blocks model loading, inference and training')
    spacy.load = blocked
    for operation in ('initialize', 'update', 'begin_training', 'resume_training',
                      'from_disk', 'from_bytes', '__call__', 'pipe'):
        setattr(Language, operation, blocked)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    args.bundle = args.bundle.resolve()
    install_reference_guards()
    require(sha(args.bundle) == args.sha256, 'stale qualification bundle')
    bundle = json.loads(args.bundle.read_text(encoding='utf-8'))
    require(set(bundle) == {'files', 'implementation', 'tokenizer', 'vocab', 'tests'} , 'exact bundle required')
    require({str(args.bundle.parent / name) for name in ('references.json', 'fixtures.json', 'source-use.json', 'protocol.json')} <= set(bundle['files']),
            'all consumed reference inputs must be hash-bound')
    require(bundle['tokenizer'] in bundle['files'] and any(
        Path(name).parent == Path(bundle['vocab']) for name in bundle['files']), 'tokenizer and vocabulary bytes must be bound')
    for path, expected in {**bundle['files'], **bundle['implementation'], **bundle['tests']}.items():
        require(sha(Path(path)) == expected, 'stale qualification input')
    # Vocabulary/tokenizer reconstruction is allowed; no pipeline or weights loaded.
    from spacy.vocab import Vocab
    from spacy.tokenizer import Tokenizer
    vocab = Vocab().from_disk(bundle['vocab'])
    raw = Path(bundle['tokenizer']).read_bytes()
    tokenizer = Tokenizer(vocab).from_bytes(raw, exclude=['vocab'])
    require(tokenizer.to_bytes(exclude=['vocab']) == raw, 'tokenizer reconstruction mismatch')
    from types import SimpleNamespace
    nlp = SimpleNamespace(make_doc=tokenizer)
    payload = json.loads((args.bundle.parent / 'references.json').read_text(encoding='utf-8'))
    require(len(payload) == 26 and len({r['current']['record_id'] for r in payload}) == 26, '26 unique training dispositions required')
    validate_source_use([item['current'] for item in payload],
                        json.loads((args.bundle.parent / 'source-use.json').read_text(encoding='utf-8')))
    for item in payload:
        require(not validate_revision(item['original'], item['proposed'], item['current'], nlp), 'invalid contextual revision')
        require(not validate_review(item['proposed'], item['review']), 'invalid contextual review')
    cases = json.loads((args.bundle.parent / 'fixtures.json').read_text(encoding='utf-8'))
    require(not validate_matrix(cases, nlp), 'fictional acceptance matrix invalid')
    for path, expected in {**bundle['files'], **bundle['implementation'], **bundle['tests']}.items():
        require(sha(Path(path)) == expected, 'qualification input changed during verification')
    print(json.dumps({'status': 'qualified_reference_package', 'records': 26, 'fictional_cases': 40,
                      'dispositions': dict(Counter(r['review']['disposition'] for r in payload)),
                      'training_started': False, 'neural_inference': False, 'application_connected': False}))


if __name__ == '__main__':
    main()
