"""Read-only source inventory for a general historical news batch."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirm-database', required=True)
    parser.add_argument('--provenance', type=Path, action='append', required=True)
    parser.add_argument('--provenance-sha256', action='append', required=True)
    parser.add_argument('--source-register', type=Path, required=True)
    parser.add_argument('--source-register-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--captures', type=Path, action='append', default=[], help='Embedded full-source JSONL; annotations are ignored')
    parser.add_argument('--captures-sha256', action='append', default=[])
    args = parser.parse_args()
    from sqlalchemy import create_engine
    from app.core.config import settings
    from app.services.news_ner_durable.contracts import sha
    from app.services.news_history_seed_inventory import seed_inventory, training_sources, complete_training_captures
    from app.services.news_historical_preparation import PreparationError, save_private_package
    root = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if not output.is_relative_to(root/'data') or output == root/'data':
        raise PreparationError('private_data_output_required')
    import subprocess
    if subprocess.run(['git','check-ignore','--quiet','--',str(output)], cwd=root).returncode:
        raise PreparationError('ignored_output_required')
    if len(args.provenance) != len(args.provenance_sha256):
        raise PreparationError('historical_training_metadata_binding_required')
    def pinned(path: Path, digest: str) -> list[dict]:
        import hashlib
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise PreparationError('historical_training_metadata_changed')
        value = json.loads(raw)
        if not isinstance(value, list):
            raise PreparationError('historical_training_metadata_invalid')
        return value
    metadata = [row for path, digest in zip(args.provenance,args.provenance_sha256,strict=True) for row in pinned(path,digest)]
    training = training_sources(metadata,pinned(args.source_register,args.source_register_sha256))
    if len(args.captures) != len(args.captures_sha256):
        raise PreparationError('historical_training_capture_binding_required')
    captures = {}
    for path, digest in zip(args.captures,args.captures_sha256,strict=True):
        import hashlib
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise PreparationError('historical_training_capture_changed')
        captures.update(complete_training_captures([json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()],training))
    # Later training revisions can contain corrected source hashes absent from
    # the older register. Their own complete, hash-bound capture resolves them.
    from app.services.news_history_seed_inventory import canonical_source_url
    for source in training:
        captured = captures.get(source['source_sha256'])
        if captured and 'canonical_url' not in source:
            source.update(source_id=captured['source_id'], canonical_url=canonical_source_url(captured['url']),
                publisher=captured['publisher'], capture_version=captured['capture_version'],
                publication_date=captured.get('published_at'), outcome='training_source_identified')
    engine = create_engine(settings.DATABASE_URL, connect_args={'connect_timeout':8})
    try:
        inventory = seed_inventory(engine,args.confirm_database,training)
    finally:
        engine.dispose()
    for source in inventory['training_sources']:
        source['complete_training_capture_available'] = source['source_sha256'] in captures
    documents = {'inventory.json':inventory,'selection.json':inventory['selection'],
        'training-captures.json':{'schema_version':'news-history-training-captures-v1','captures':captures}}
    save_private_package(output,documents)
    print(json.dumps({'read_only':True,'saved_articles':len(inventory['saved_articles']),
        'training_source_hashes':len({s['source_sha256'] for s in training}),
        'training_needing_capture':sum(s['outcome']=='full_training_capture_registration_required' for s in inventory['training_sources']),
        'unresolved_training_sources':sum(s['outcome']=='training_source_capture_unresolved' for s in training),
        'selection_sha256':sha(inventory['selection'])}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
