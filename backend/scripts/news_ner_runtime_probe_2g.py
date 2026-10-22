"""One explicitly authorized 2-GiB qualification; frozen inference runtime unchanged."""
from __future__ import annotations

import asyncio
import importlib.metadata
import json
from pathlib import Path
import resource
import sys
import time

sys.path[:0] = ['/app', '/app/scripts']
from news_ner_runtime_probe import memory, normal_import_baseline, write
from app.services.news_ner.contract import require
from app.services.news_ner_runtime.protocol import code_bindings
from app.services.news_ner_runtime.supervisor import Session

HEADROOM_BYTES = 1792 * 1024**2


async def qualify() -> None:
    output = Path('/output')
    write(output / 'baseline.json', normal_import_baseline())
    request = json.loads(Path('/input/request.json').read_text())
    rows = json.loads(Path('/input/workload.json').read_text())['rows']
    require(code_bindings(Path('/app/app/services')) == request['code'], 'runtime_code_changed')
    session = Session(request['bundle_sha256'], request['code'])
    timings = {kind: [] for kind in ('passage', 'article', 'reviewed', 'stress')}
    try:
        started = time.monotonic()
        ready = await session.start()
        cold = time.monotonic() - started
        write(output / 'ready.json', {**ready, 'supervisor_cold_seconds': cold})
        require(cold <= 60, 'cold_deadline')
        with (output / 'responses.jsonl').open('x') as stream:
            for index, row in enumerate(rows):
                write(output / f'begin-{index:04d}.json', {'index': index, 'kind': row['kind']})
                started = time.monotonic()
                result = await session.request({k: row[k] for k in ('record_id', 'text', 'text_sha256', 'publication')},
                                               timeout=60 if row['kind'] == 'stress' else 30)
                elapsed = time.monotonic() - started
                timings[row['kind']].append(elapsed)
                stream.write(json.dumps({'record_id': row['record_id'], 'elapsed_seconds': elapsed,
                                         'memory': memory(), 'result': result}, ensure_ascii=False) + '\n')
                stream.flush()
                require(memory()['memory.peak'] < HEADROOM_BYTES, 'memory_headroom')
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
        asyncio.run(qualify())
    except BaseException as exc:
        print(json.dumps({'status': 'failed', 'error_type': type(exc).__name__}))
        sys.exit(2)
