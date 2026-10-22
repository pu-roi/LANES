"""Fixed-reference qualification only; no extraction, inference or label revisions."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from . import context_review_v37 as previous
from .annotation.schema import AnnotationRecord
from .annotation.validation import validate_record


def qualify(bundle: dict) -> dict:
    if set(bundle)!={'files','predecessor_bundle','fixtures','implementation_sha256'}:
        raise ValueError('exact fixed-reference qualification bundle required')
    if bundle['implementation_sha256']!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise ValueError('stale qualification implementation')
    for key in ('predecessor_bundle','fixtures'):
        if bundle[key] not in bundle['files']:raise ValueError('unbound qualification input')
    for name, sha in bundle['files'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=sha:raise ValueError('stale qualified input')
    prior=json.loads(Path(bundle['predecessor_bundle']).read_text(encoding='utf-8'))
    result=previous.qualify(prior)
    cases=json.loads(Path(bundle['fixtures']).read_text(encoding='utf-8'))
    old=json.loads(Path(prior['fixtures']).read_text(encoding='utf-8'))
    if len(cases)!=238 or len({c['case_id'] for c in cases})!=238 or cases[:208]!=old:
        raise ValueError('exact 208 preserved plus 30 new fictional cases required')
    from spacy.tokenizer import Tokenizer
    from spacy.vocab import Vocab
    raw=Path(prior['tokenizer']).read_bytes()
    tokenizer=Tokenizer(Vocab().from_disk(prior['vocab'])).from_bytes(raw,exclude=['vocab'])
    if tokenizer.to_bytes(exclude=['vocab'])!=raw:raise ValueError('tokenizer reconstruction differs')
    for case in cases:
        r=AnnotationRecord.model_validate_json(json.dumps(case['record']))
        if r.quality!='constructed' or r.split is not None:raise ValueError('fixtures cannot be members')
        errors=validate_record(r,SimpleNamespace(make_doc=tokenizer))
        if errors:raise ValueError('fixture qualification failed: '+'; '.join(errors))
    return {**result,'fixtures':238,'references_unchanged':True}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--sha256',required=True)
    a=p.parse_args()
    if hashlib.sha256(a.bundle.read_bytes()).hexdigest()!=a.sha256:raise ValueError('stale bundle')
    print(json.dumps(qualify(json.loads(a.bundle.read_text(encoding='utf-8')))))
