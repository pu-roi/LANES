"""Raw-only CPU context worker; no references, model loading or external access."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time

BOOT=time.monotonic()

if not __package__:
    sys.path[:0]=[str(Path(__file__).resolve().parents[2]),'/app']

from training.flood_ner.context_gap_worker import NoNeural
from training.flood_ner.corrected_rules_worker import install_guards
from training.flood_ner.context_gap_audit import digest, require


def run(request: dict, output: Path) -> dict:
    require(set(request)=={'schema','rows','implementation'}and request['schema']=='lanes-context-association-worker-v38','exact raw request required')
    require(output.is_dir()and not any(output.iterdir()),'new empty worker output required')
    for name,h in request['implementation'].items():
        require(not Path(name).is_absolute()and '..'not in Path(name).parts and ':'not in name and '\\'not in name,'unsafe code binding')
        require(digest(Path('/code')/name)==h,'worker implementation changed')
    sys.meta_path.insert(0,NoNeural());install_guards()
    from training.flood_ner.context_association_v38 import extract
    from training.flood_ner.context_acceptance import validate_raw_input
    seen=set()
    for row in request['rows']:
        validate_raw_input(row);require(row['record_id']not in seen,'duplicate raw identity');seen.add(row['record_id'])
    require(len(seen)==262,'frozen 24 training and 238 fictional inputs required')
    cold=BOOT;durations=[]
    def deadline(*args):raise TimeoutError('context association input deadline')
    signal.signal(signal.SIGALRM,deadline)
    with(output/'ready.json').open('x',encoding='utf-8')as f:json.dump({'cold_worker_seconds':time.monotonic()-cold},f)
    with(output/'results.jsonl').open('x',encoding='utf-8',newline='\n')as stream:
        for i,row in enumerate(request['rows']):
            with(output/'heartbeat.tmp').open('x',encoding='utf-8')as hb:json.dump({'phase':'article','index':i},hb)
            os.replace(output/'heartbeat.tmp',output/'heartbeat.json')
            signal.setitimer(signal.ITIMER_REAL,30);started=time.monotonic()
            result=extract(row);durations.append(time.monotonic()-started)
            stream.write(json.dumps(result,ensure_ascii=False)+'\n');stream.flush();signal.setitimer(signal.ITIMER_REAL,0)
    require(not any(n.split('.')[0]in{'spacy','thinc','torch','tensorflow','transformers'}for n in sys.modules),'neural import occurred')
    return {'status':'completed','processed':len(seen),'row_seconds':durations,'network_database_blocked':True,
            'neural_libraries_loaded':False,'training_started':False}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--request',type=Path,required=True);parser.add_argument('--sha256',required=True);args=parser.parse_args();output=Path('/output')
    try:
        require(digest(args.request)==args.sha256,'stale worker request')
        result=run(json.loads(args.request.read_text(encoding='utf-8')),output)
        with(output/'status.json').open('x',encoding='utf-8')as f:json.dump(result,f)
    except BaseException as exc:
        import traceback
        with(output/'failure-traceback.txt').open('x',encoding='utf-8')as f:f.write(traceback.format_exc())
        with(output/'failure.json').open('x',encoding='utf-8')as f:json.dump({'status':'failed','error_type':type(exc).__name__},f)
        raise SystemExit(2)from exc


if __name__=='__main__':main()
