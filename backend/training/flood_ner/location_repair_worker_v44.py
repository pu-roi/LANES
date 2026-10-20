"""One isolated saved-mention study; no references, models or database modules."""
import hashlib
import importlib.abc
import json
from pathlib import Path
import signal
import sys

sys.path.insert(0, '/code')


class NoNeuralDatabase(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: object = None, target: object = None) -> None:
        if fullname.split('.')[0] in {'spacy', 'torch', 'transformers', 'sqlalchemy', 'psycopg', 'psycopg2', 'asyncpg'}:
            raise RuntimeError('neural/database modules prohibited')


def write(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as stream: json.dump(value, stream, ensure_ascii=False)


def run() -> None:
    path = Path('/input/request.json')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == sys.argv[1]
    request = json.loads(path.read_text(encoding='utf-8'))
    assert set(request) == {'schema', 'implementation', 'groups'} and request['schema'] == 'lanes-location-worker-v44'
    for name, digest in request['implementation'].items():
        assert not Path(name).is_absolute() and ':' not in name and '\\' not in name and '..' not in Path(name).parts
        assert hashlib.sha256((Path('/code')/name).read_bytes()).hexdigest() == digest
    sys.meta_path.insert(0, NoNeuralDatabase())
    from training.flood_ner.location_repair_v44 import propose, METHODS
    from news_ner.context_association_v42 import extract
    from news_ner.contract import validate_raw_input
    counts = {'training': 345, 'contexts': 24, 'article': 1, 'location_fixtures': 36,
              'existing': 238, 'temporal': 36, 'v41': 36, 'v42': 36, 'new': 36}
    assert set(request['groups']) == set(counts)
    for group, rows in request['groups'].items():
        assert len(rows) == len({r['record_id'] for r in rows}) == counts[group]
        for row in rows:
            assert set(row) == {'record_id', 'raw', 'control_mentions'}
            assert row['record_id'] == row['raw']['record_id']
            validate_raw_input(row['raw']); validate_raw_input({**row['raw'], 'mentions': row['control_mentions']})
    output = Path('/output'); assert not any(output.iterdir())
    write(output/'ready.json', {'status': 'ready', 'neural_inference': False})
    def deadline(*_args: object) -> None: raise TimeoutError('row deadline')
    signal.signal(signal.SIGALRM, deadline)
    processed = 0
    for group, rows in request['groups'].items():
        with (output/(group+'.jsonl')).open('x', encoding='utf-8') as stream:
            for row in rows:
                signal.setitimer(signal.ITIMER_REAL, 15)
                raw = row['raw']; control = {**raw, 'mentions': row['control_mentions']}
                result = {'record_id': row['record_id'], 'methods': {}}
                if group not in {'training', 'location_fixtures'}:
                    result['original'] = extract(raw); result['control'] = extract(control)
                for method in METHODS:
                    repair = propose({k: control[k] for k in ('record_id', 'text', 'mentions')}, method,
                                     neural_mentions=raw['mentions'])
                    value = {'repair': repair}
                    if group not in {'training', 'location_fixtures'}:
                        value['context'] = extract({**raw, 'mentions': repair['effective_mentions']})
                    result['methods'][method] = value
                signal.setitimer(signal.ITIMER_REAL, 0)
                stream.write(json.dumps(result, ensure_ascii=False)+'\n'); stream.flush(); processed += 1
    assert processed == 788
    assert not any(n.split('.')[0] in {'spacy', 'torch', 'sqlalchemy', 'psycopg'} for n in sys.modules)
    write(output/'status.json', {'status': 'completed', 'raw_records': processed, 'neural_inference': False,
                                 'database_access': False, 'methods': list(METHODS)})


if __name__ == '__main__':
    try: run()
    except BaseException as exc:
        write(Path('/output/failure.json'), {'error_type': type(exc).__name__})
        raise
