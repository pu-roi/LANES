"""Context-only raw cached-view worker; no location recognition or references."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback

BOOT=time.monotonic()
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
VIEWS=('original','transport_asset','shared_locality','explicit_road','combined')


def run(request: dict, output: Path) -> None:
    from training.flood_ner.context_gap_worker import NoNeural
    from training.flood_ner.corrected_rules_worker import install_guards
    if set(request)!={'schema','implementation','context_rows','existing_rows','temporal_rows','new_rows'}or request['schema']!='lanes-context-repair-worker-v41':
        raise ValueError('exact raw cached-view request required')
    if not output.is_dir()or any(output.iterdir()):raise ValueError('fresh empty output required')
    for n,h in request['implementation'].items():
        if n.startswith('/')or ':'in n or '\\'in n or '..'in Path(n).parts:raise ValueError('unsafe code path')
        if hashlib.sha256((Path('/code')/n).read_bytes()).hexdigest()!=h:raise ValueError('worker code changed')
    sys.meta_path.insert(0,NoNeural());install_guards()
    from training.flood_ner.context_association_v41 import extract
    from training.flood_ner.context_association_v38 import extract as baseline
    from training.flood_ner.context_acceptance import validate_raw_input
    for key,count in [('context_rows',24),('existing_rows',238),('temporal_rows',36),('new_rows',36)]:
        rows=request[key]
        if len(rows)!=count or len({r['record_id']for r in rows})!=count:raise ValueError('raw workload differs')
        for row in rows:
            if key in {'context_rows','existing_rows'}:
                if set(row)!={'record_id','views'}or set(row['views'])!=set(VIEWS):raise ValueError('exact cached views required')
                for raw in row['views'].values():
                    validate_raw_input(raw)
                    if raw['record_id']!=row['record_id']:raise ValueError('cached identity differs')
            else:validate_raw_input(row)
    def deadline(*args):raise TimeoutError('context row deadline')
    signal.signal(signal.SIGALRM,deadline)
    with(output/'ready.json').open('x',encoding='utf-8')as f:json.dump({'cold_worker_seconds':time.monotonic()-BOOT},f)
    processed=0
    for key in ('context_rows','existing_rows','temporal_rows','new_rows'):
        with(output/(key+'.jsonl')).open('x',encoding='utf-8',newline='\n')as f:
            for row in request[key]:
                with(output/'heartbeat.tmp').open('x',encoding='utf-8')as hb:json.dump({'phase':'article','index':processed},hb)
                os.replace(output/'heartbeat.tmp',output/'heartbeat.json');signal.setitimer(signal.ITIMER_REAL,10)
                value={'record_id':row['record_id']}
                if key in {'context_rows','existing_rows'}:value['views']={name:extract(raw)for name,raw in row['views'].items()}
                else:
                    value['output']=extract(row)
                    if key=='new_rows':value['baseline']=baseline(row)
                signal.setitimer(signal.ITIMER_REAL,0)
                f.write(json.dumps(value,ensure_ascii=False)+'\n');f.flush();processed+=1
    with(output/'status.json').open('x',encoding='utf-8')as f:
        json.dump({'status':'completed','processed':processed,'neural_libraries_loaded':False,
                   'network_database_blocked':True,'location_recognition_rerun':False},f)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--sha256',required=True)
    a=p.parse_args()
    try:
        data=a.request.read_bytes()
        if hashlib.sha256(data).hexdigest()!=a.sha256:raise ValueError('request hash differs')
        run(json.loads(data),Path('/output'))
    except BaseException as exc:
        with Path('/output/failure.json').open('x',encoding='utf-8')as f:json.dump({'type':type(exc).__name__,'traceback':traceback.format_exc()},f)
        raise
