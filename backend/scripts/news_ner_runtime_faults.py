"""Real subprocess containment checks using only fictional messages, never a model."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import signal
import sys
import time

sys.path.insert(0, '/app')
from app.services.news_ner_runtime.supervisor import Session, RuntimeFailure

FAKE = '''import json,sys,time,os
sys.path.insert(0,"/app")
from app.services.news_ner_runtime.isolation import install
isolation=install()
mode=sys.argv[-1] if len(sys.argv)>1 else "normal"
start=json.loads(sys.stdin.readline())
print(json.dumps({"state":"ready","runtime":"lanes-ner-subprocess-v1","isolation":isolation}),flush=True)
message=json.loads(sys.stdin.readline())
if message.get("state")=="shutdown":
 print('{"state":"shutdown"}',flush=True)
else:
 if message["request"]["text"]=="crash":os._exit(23)
 if message["request"]["text"]=="malformed":print("invalid",flush=True);sys.exit(0)
 if message["request"]["text"]=="oversize":print("x"*(8*1024**2+100),flush=True);sys.exit(0)
 time.sleep(60)
'''


async def run() -> dict:
    worker = Path('/tmp/fictional_worker.py')
    worker.write_text(FAKE)
    results = {}
    for mode in ('timeout', 'crash', 'malformed', 'oversize', 'cancellation', 'concurrency', 'shutdown'):
        session = Session('fictional', {}, worker=worker)
        ready = await session.start()
        assert ready['isolation']['raw_socket_denied']
        if mode != 'shutdown':
            import hashlib
            text = mode if mode in ('crash', 'malformed', 'oversize') else 'fictional'
            request = {'record_id': mode, 'text': text, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'publication': None}
            task = asyncio.create_task(session.request(request, timeout=.1 if mode == 'timeout' else 30))
            if mode in ('cancellation', 'concurrency'):
                await asyncio.sleep(.05)
                if mode == 'concurrency':
                    try:
                        await session.request(request)
                    except RuntimeFailure as exc:
                        assert str(exc) == 'concurrent_request'
                    else:
                        raise AssertionError('concurrent_request_accepted')
                task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                assert mode in ('cancellation', 'concurrency')
            except RuntimeFailure as exc:
                assert str(exc) == ('deadline' if mode == 'timeout' else 'invalid_worker_message' if mode in ('malformed', 'oversize') else 'worker_exit')
            else:
                raise AssertionError('expected_failure_missing')
        await session.close()
        assert session.proc.returncode is not None and session.cleanup_seconds <= 5
        results[mode] = {'exit': session.proc.returncode, 'cleanup_seconds': session.cleanup_seconds, 'reaped': True}
    # A real abrupt parent death; fixture child installs PDEATHSIG before readiness.
    parent = await asyncio.create_subprocess_exec(sys.executable, '-I', '-B', '-c',
        'import subprocess,sys,time; p=subprocess.Popen([sys.executable,"-I","-B","/tmp/fictional_worker.py"],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True); p.stdin.write("{}\\n"); p.stdin.flush(); p.stdout.readline(); print(p.pid,flush=True); time.sleep(60)',
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    child_pid = int(await parent.stdout.readline())
    parent.kill(); await parent.wait()
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        stat = Path(f'/proc/{child_pid}/stat')
        if not stat.exists() or stat.read_text().split()[2] == 'Z':
            break
        await asyncio.sleep(.02)
    else:
        raise AssertionError('orphan_survived')
    # PID 1 / --init reaps the adopted child; observe disappearance too.
    while Path(f'/proc/{child_pid}').exists() and time.monotonic() < deadline:
        await asyncio.sleep(.02)
    assert not Path(f'/proc/{child_pid}').exists()
    results['parent_death'] = {'terminated_and_reaped': True}
    return results


if __name__ == '__main__':
    print(json.dumps(asyncio.run(run())))
