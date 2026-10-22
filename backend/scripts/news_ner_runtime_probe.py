"""Private local qualification entry point; never imported by the news scheduler."""
from __future__ import annotations

import asyncio
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import sys
import time
import types

sys.path.insert(0, '/app')
from app.services.news_ner_runtime.protocol import HEADROOM_BYTES, code_bindings
from app.services.news_ner_runtime.supervisor import Session


def write(path: Path, value: object) -> None:
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False)
        stream.flush()


def memory() -> dict:
    base = Path('/sys/fs/cgroup')
    return {name: int((base / name).read_text()) for name in ('memory.current', 'memory.peak')}


def normal_import_baseline() -> dict:
    """Import the actual news CLI with a fake storage module; never construct an engine."""
    import socket
    from sqlalchemy.orm import DeclarativeBase
    def prohibited(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError('storage_or_network_access_prohibited')
    class Base(DeclarativeBase):
        pass
    fake = types.ModuleType('app.core.database')
    fake.Base = Base
    fake.SessionLocal = fake.get_db = prohibited
    fake.engine = None
    sys.modules['app.core.database'] = fake
    socket.create_connection = prohibited
    socket.socket.connect = prohibited
    socket.socket.connect_ex = prohibited
    import sqlalchemy
    sqlalchemy.create_engine = prohibited
    import scripts.run_news_discovery  # Import only: main() is never called.
    hashes = {}
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename and filename.endswith('.py') and filename.startswith('/app/'):
            name = filename.removeprefix('/app/')
            hashes[name] = hashlib.sha256(Path(filename).read_bytes()).hexdigest()
    return {'rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
            'memory': memory(), 'imported_source_hashes': hashes, 'storage': 'fake', 'connections': 0}


async def qualify() -> None:
    output = Path('/output')
    baseline = normal_import_baseline()
    write(output / 'baseline.json', baseline)
    freeze = json.loads(Path('/input/request.json').read_text())
    rows = json.loads(Path('/input/workload.json').read_text())['rows']
    assert code_bindings(Path('/app/app/services')) == freeze['code']
    session = Session(freeze['bundle_sha256'], freeze['code'])
    timings = {'passage': [], 'article': [], 'reviewed': [], 'stress': []}
    try:
        cold_start = time.monotonic()
        ready = await session.start()
        cold = time.monotonic() - cold_start
        write(output / 'ready.json', {**ready, 'supervisor_cold_seconds': cold})
        assert cold <= 60
        with (output / 'responses.jsonl').open('x') as stream:
            for index, row in enumerate(rows):
                write(output / f'begin-{index:04d}.json', {'index': index, 'kind': row['kind']})
                request = {key: row[key] for key in ('record_id', 'text', 'text_sha256', 'publication')}
                started = time.monotonic()
                result = await session.request(request, timeout=60 if row['kind'] == 'stress' else 30)
                elapsed = time.monotonic() - started
                timings[row['kind']].append(elapsed)
                stream.write(json.dumps({'record_id': row['record_id'], 'elapsed_seconds': elapsed,
                                         'memory': memory(), 'result': result}, ensure_ascii=False) + '\n')
                stream.flush()
                assert memory()['memory.peak'] < HEADROOM_BYTES
        await session.close()
        write(output / 'measurements.json', {'timings': timings, 'memory': memory(), 'cold_seconds': cold,
              'cleanup_seconds': session.cleanup_seconds, 'child_exit': session.proc.returncode,
              'supervisor_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
              'packages': sorted((d.metadata['Name'], d.version) for d in importlib.metadata.distributions()),
              'session_seconds': time.monotonic() - session.started})
    except BaseException as exc:
        await session.close()
        write(output / 'failure.json', {'error_type': type(exc).__name__, 'state': session.state,
              'child_exit': session.proc.returncode if session.proc else None, 'memory': memory(),
              'completed_counts': {k: len(v) for k, v in timings.items()}, 'cleanup_seconds': session.cleanup_seconds})
        raise


if __name__ == '__main__':
    try:
        if sys.argv[1:] == ['--baseline-only']:
            write(Path('/output/baseline-preflight.json'), normal_import_baseline())
        else:
            asyncio.run(qualify())
    except BaseException as exc:
        # All detailed material remains in private mounted receipts.
        print(json.dumps({'status': 'failed', 'error_type': type(exc).__name__}))
        sys.exit(2)
