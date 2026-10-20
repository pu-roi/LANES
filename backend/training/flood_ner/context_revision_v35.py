"""Source-only contextual proposal validation; no extractor or model execution."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

if not __package__:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

from training.flood_ner.context_acceptance import object_sha, validate_revision
from training.flood_ner.annotation.schema import PLACE_LABELS

PRESERVED = ('record_id', 'text', 'text_sha256', 'source', 'passage_start',
             'passage_end', 'passage_language', 'split')


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def proposal_errors(original: dict, proposed: dict, current: dict,
                    review: dict, tokenizer: Any) -> list[str]:
    """Validate separately proposed contextual edits, never alter inputs."""
    errors = validate_revision(original, proposed, current, tokenizer)
    if review.get('record_id') != proposed.get('record_id'):
        errors.append('review identity mismatch')
    if review.get('proposal_sha256') != object_sha(proposed):
        errors.append('stale proposal hash')
    if review.get('disposition') not in {'retain_proposed', 'correct_proposed', 'hold'}:
        errors.append('explicit disposition required')
    if proposed.get('complete') is True and review.get('disposition') == 'hold':
        errors.append('held reference cannot claim completeness')
    if review.get('disposition') != 'hold':
        if proposed.get('complete') is not True or proposed.get('review_status') != 'accepted':
            errors.append('incomplete reference must remain held')
        if set(review.get('completeness', {})) != {'locations','depth','time','status','access','associations'}:
            errors.append('complete field accounting required')
        elif not all(v is True for v in review['completeness'].values()):
            errors.append('eligible reference has incomplete fields')
    unassigned = {f['id'] for f in proposed.get('facts', [])} - {
        r['fact_id'] for r in proposed.get('relations', [])}
    if set(review.get('unassigned_facts', {})) != unassigned or any(
            not isinstance(v, str) or not v for v in review.get('unassigned_facts', {}).values()):
        errors.append('unassigned facts need explicit dispositions')
    if [e for e in proposed.get('entities', []) if e['label'] in PLACE_LABELS] != current.get('entities'):
        errors.append('location annotations changed')
    return errors


def field_changes(original: Any, proposed: Any, path: str = '') -> list[dict]:
    """Exact structural change ledger; array changes remain explicit whole values."""
    if type(original) is not type(proposed):
        return [{'path':path, 'original':deepcopy(original), 'proposed':deepcopy(proposed)}]
    if isinstance(original, dict):
        changes = []
        for key in sorted(set(original) | set(proposed)):
            pointer = path+'/'+key.replace('~','~0').replace('/','~1')
            if key not in original or key not in proposed:
                changes.append({'path':pointer, 'original_present':key in original,
                    'proposed_present':key in proposed, 'original':deepcopy(original.get(key)),
                    'proposed':deepcopy(proposed.get(key))})
            else:
                changes.extend(field_changes(original[key], proposed[key], pointer))
        return changes
    if original != proposed:
        return [{'path':path, 'original':deepcopy(original), 'proposed':deepcopy(proposed)}]
    return []


def join_reviews(prior: list[dict], revised: list[dict]) -> list[tuple[dict, dict]]:
    old = {r['proposed']['record_id']:r for r in prior}
    new = {r['proposed']['record_id']:r for r in revised}
    if len(old) != len(prior) or len(new) != len(revised) or set(old) != set(new) or len(old) != 24:
        raise ValueError('exact unique 24 reviewed counterparts required')
    pairs = []
    for rid, before in old.items():
        after = new[rid]
        if after['original'] != before['proposed']:
            raise ValueError('original proposal changed during review')
        if any(after['proposed'].get(k) != before['proposed'].get(k) for k in PRESERVED):
            raise ValueError('historical text/identity/source/partition changed')
        pairs.append((before, after))
    return pairs


def verify_frozen_files(folder: Path, files: dict) -> None:
    """Exact file bindings only; never accept manifest self-hash placeholders."""
    base = folder.resolve()
    for name, item in files.items():
        file = (folder/name).resolve()
        if not file.is_relative_to(base) or file == base or file.is_symlink():
            raise ValueError('unsafe reference file binding')
        if file.stat().st_size != item['bytes'] or digest(file) != item['sha256']:
            raise ValueError('stale frozen reference evidence')


def source_summary(record: dict) -> dict:
    """Source integrity and raw support only, never a reference-derived prediction."""
    text = record['text']; source = record['source']
    if hashlib.sha256(text.encode()).hexdigest() != record['text_sha256']:
        raise ValueError('stale passage text')
    if hashlib.sha256(source['text'].encode()).hexdigest() != source['text_sha256']:
        raise ValueError('stale source text')
    if source['text'][record['passage_start']:record['passage_end']] != text:
        raise ValueError('non-exact source window')
    return {'record_id':record['record_id'], 'source_sha256':source['text_sha256'],
        'text_sha256':record['text_sha256'], 'language':record['passage_language'],
        'reference_sha256':object_sha(record), 'complete':record['complete']}


def main() -> None:
    """Read-only tokenizer/schema qualification from an exact hash-bound bundle."""
    import argparse
    from collections import Counter
    from types import SimpleNamespace
    from training.flood_ner.context_acceptance import install_reference_guards, require
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    args=parser.parse_args()
    require(digest(args.bundle)==args.sha256,'stale reference qualification bundle')
    bundle=json.loads(args.bundle.read_text(encoding='utf-8'))
    require(set(bundle)=={'schema','files','prior','revised','source_use','tokenizer','vocab'},'exact source-only bundle required')
    require(bundle['schema']=='lanes-context-revision-qualification-v35','wrong qualification scope')
    for name in (bundle['prior'],bundle['revised'],bundle['source_use'],bundle['tokenizer']):
        require(name in bundle['files'],'unbound qualification input')
    for name, expected in bundle['files'].items():
        lowered='/'+str(name).replace('\\','/').lower()
        require(not any(w in lowered for w in ('/raw-predictions','/predictions','/rules.jsonl','/research-holdout','/model-best/','/model-last/')),
                'non-reference inputs forbidden')
        require(digest(Path(name))==expected,'stale qualification source')
    install_reference_guards()
    from spacy.tokenizer import Tokenizer
    from spacy.vocab import Vocab
    raw=Path(bundle['tokenizer']).read_bytes()
    tokenizer=Tokenizer(Vocab().from_disk(bundle['vocab'])).from_bytes(raw,exclude=['vocab'])
    require(tokenizer.to_bytes(exclude=['vocab'])==raw,'frozen tokenizer reconstruction differs')
    prior=json.loads(Path(bundle['prior']).read_text(encoding='utf-8'))
    revised=json.loads(Path(bundle['revised']).read_text(encoding='utf-8'))
    uses={u['record_id']:u for u in json.loads(Path(bundle['source_use']).read_text(encoding='utf-8'))}
    pairs=join_reviews(prior,revised);errors=[]
    for before,after in pairs:
        proposed=after['proposed'];source_summary(proposed)
        original=before['proposed'];current=before['current'];use=uses.get(current['record_id'],{})
        require(use.get('verified')is True and use.get('scope')=='private_owner_only_academic_training_evaluation'
            and use.get('text_sha256')==current['text_sha256']
            and use.get('source_sha256')==current['source']['text_sha256']
            and [use.get('start'),use.get('end')]==[current['passage_start'],current['passage_end']],
            'unsupported source-use expansion')
        errors.extend(proposed['record_id']+': '+e for e in proposal_errors(original,proposed,current,after['review'],SimpleNamespace(make_doc=tokenizer)))
    require(not errors,'reference qualification failed: '+'; '.join(errors))
    for name,expected in bundle['files'].items():
        require(digest(Path(name))==expected,'reference evidence changed during qualification')
    print(json.dumps({'status':'qualified_reference_revision','records':len(pairs),
        'dispositions':dict(Counter(r['review']['disposition']for r in revised)),
        'tokenizer_reconstruction_verified':True,'neural_inference':False,
        'training_started':False,'application_connected':False}))


if __name__=='__main__':
    main()
