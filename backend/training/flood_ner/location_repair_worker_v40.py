"""Single guarded Linux study. Raw inputs only; no references or neural inference."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

BOOT = time.monotonic()
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def run(request: dict, output: Path) -> None:
    from training.flood_ner.context_gap_worker import NoNeural
    from training.flood_ner.corrected_rules_worker import install_guards
    from training.flood_ner.context_gap_audit import digest
    if set(request) != {'schema', 'training_rows', 'context_rows', 'location_rows', 'temporal_rows', 'existing_rows', 'implementation'} or request['schema'] != 'lanes-location-study-v40':
        raise ValueError('exact raw request required')
    if not output.is_dir() or any(output.iterdir()):
        raise ValueError('fresh empty worker destination required')
    for name, sha in request['implementation'].items():
        if name.startswith('/') or '..' in Path(name).parts or ':' in name or '\\' in name:
            raise ValueError('unsafe code path')
        if digest(Path('/code') / name) != sha:
            raise ValueError('worker code differs')
    sys.meta_path.insert(0, NoNeural()); install_guards()
    from training.flood_ner.location_repair_v40 import propose, validate, METHODS
    from training.flood_ner.context_association_v38 import extract
    from training.flood_ner.context_acceptance import validate_raw_input
    groups = [('training_rows', 345), ('context_rows', 24), ('location_rows', 36),
              ('temporal_rows', 36), ('existing_rows', 238)]
    for key, count in groups:
        rows = request[key]
        if len(rows) != count or len({r['record_id'] for r in rows}) != count:
            raise ValueError('frozen raw group accounting differs')
        for row in rows:
            (validate if key in {'training_rows', 'location_rows'} else validate_raw_input)(row)
    def deadline(*args):
        raise TimeoutError('study row deadline')
    signal.signal(signal.SIGALRM, deadline)
    with (output / 'ready.json').open('x', encoding='utf-8') as f:
        json.dump({'cold_worker_seconds': time.monotonic()-BOOT}, f)
    processed = 0
    for key, _ in groups:
        with (output / (key + '.jsonl')).open('x', encoding='utf-8', newline='\n') as f:
            for row in request[key]:
                with (output / 'heartbeat.tmp').open('x', encoding='utf-8') as hb:
                    json.dump({'phase': 'article', 'index': processed}, hb)
                os.replace(output / 'heartbeat.tmp', output / 'heartbeat.json')
                signal.setitimer(signal.ITIMER_REAL, 10)
                result = {'record_id': row['record_id']}
                if key == 'temporal_rows':
                    result['output'] = extract(row)
                else:
                    result['methods'] = {}
                    for method in METHODS:
                        repair = propose({k: row[k] for k in ('record_id', 'text', 'mentions')}, method)
                        value = {'repair': repair}
                        if key in {'context_rows', 'existing_rows'}:
                            candidate = deepcopy(row); candidate['mentions'] = repair['effective_mentions']
                            value['context'] = extract(candidate)
                        result['methods'][method] = value
                    if key == 'existing_rows':
                        result['baseline'] = extract(row)
                signal.setitimer(signal.ITIMER_REAL, 0)
                f.write(json.dumps(result, ensure_ascii=False) + '\n'); f.flush(); processed += 1
    with (output / 'status.json').open('x', encoding='utf-8') as f:
        json.dump({'status': 'completed', 'processed': processed, 'neural_libraries_loaded': False,
                   'network_database_blocked': True, 'training_started': False, 'application_connected': False}, f)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', type=Path, required=True); p.add_argument('--sha256', required=True)
    args = p.parse_args(); destination = Path('/output')
    try:
        import hashlib
        raw = args.request.read_bytes()
        if hashlib.sha256(raw).hexdigest() != args.sha256:
            raise ValueError('request hash differs')
        run(json.loads(raw), destination)
    except BaseException as exc:
        with (destination / 'failure.json').open('x', encoding='utf-8') as f:
            json.dump({'error_type': type(exc).__name__, 'traceback': traceback.format_exc()}, f)
        raise
