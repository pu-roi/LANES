"""One guarded raw-text rules pass. No neural libraries, references or source fetches."""
from __future__ import annotations

import argparse
import importlib.abc
import json
import os
from pathlib import Path
import signal
import sys
import time

if not __package__:
    sys.path[:0]=[str(Path(__file__).resolve().parents[2]),'/app']
from training.flood_ner import context_gap_audit as audit
from training.flood_ner.corrected_rules_worker import install_guards


class NoNeural(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0]in{'spacy','thinc','torch','tensorflow','transformers'}:
            raise RuntimeError('context gap worker forbids neural model/library loading')


def run(request: dict, output: Path) -> dict:
    cold=time.monotonic()
    require=audit.require
    require(set(request)=={'schema','rows','implementation','files'} and request['schema']=='lanes-context-gap-worker-v32',
            'exact raw request required')
    audit.validate_raw(request['rows'])
    require(output.is_dir()and not any(output.iterdir()),'new empty output required')
    require(set(request['implementation'])=={'training/__init__.py','training/flood_ner/__init__.py',
            'training/flood_ner/context_gap_audit.py','training/flood_ner/context_gap_worker.py',
            'training/flood_ner/corrected_rules_worker.py'}, 'exact scoped implementation required')
    for name,sha in request['implementation'].items():
        require(audit.digest(Path('/code')/name)==sha,'worker implementation mismatch')
    for name,sha in request['files'].items():
        require(not Path(name).is_absolute()and '..'not in Path(name).parts and ':'not in name and '\\'not in name,
                'unsafe rules source binding')
        source=Path('/data')/name[len('runtime_data/'):] if name.startswith('runtime_data/')else Path('/app')/name
        require(audit.digest(source)==sha,'rules source/asset mismatch')
    sys.meta_path.insert(0,NoNeural());install_guards()
    from app.schemas.news_extraction import NewsArticleExtractorInput
    from app.services.taglish_extraction_service import extract_taglish_flood_facts
    from datetime import datetime
    from app.core.database import engine
    require(type(engine).__name__=='OfflineEngine','inert declaration facade required')
    def deadline(*args):raise TimeoutError('context audit passage deadline')
    signal.signal(signal.SIGALRM,deadline)
    with (output/'ready.json').open('x',encoding='utf-8')as stream:
        json.dump({'cold_worker_seconds':time.monotonic()-cold},stream)
    durations=[]
    with (output/'rules.jsonl').open('x',encoding='utf-8',newline='\n')as stream:
        for i,row in enumerate(request['rows']):
            with (output/'heartbeat.tmp').open('x',encoding='utf-8')as hb:json.dump({'phase':'article','index':i},hb)
            os.replace(output/'heartbeat.tmp',output/'heartbeat.json')
            signal.setitimer(signal.ITIMER_REAL,10);started=time.monotonic()
            text=row['text'];leading=len(text)-len(text.lstrip())
            value=NewsArticleExtractorInput(article_id=i,canonical_url='',publisher='',title='',excerpt='',article_text=text,
                published_at=datetime.fromisoformat(row['published_at'])if row['published_at']else None)
            parsed=extract_taglish_flood_facts(value);claims=[]
            for claim in parsed.claims:
                raw=claim.model_dump(mode='json')
                keep=('raw_place_name','place_char_start','place_char_end','place_type','depth_raw','depth_canonical',
                      'depth_meters','event_time_raw','event_time_resolved','event_time_kind','condition','is_forecast',
                      'is_negated','is_historical','road_passability','uncertainty_reasons','evidence_sentence','evidence_sentence_offset')
                c={k:raw[k]for k in keep}
                c['place_char_start']+=leading;c['place_char_end']+=leading
                c['evidence_sentence_offset']=[x+leading for x in c['evidence_sentence_offset']]
                a,b=c['place_char_start'],c['place_char_end'];sa,sb=c['evidence_sentence_offset']
                c['place_source_exact']=0<=a<b<=len(text)and text[a:b]==c['raw_place_name']
                c['sentence_source_exact']=0<=sa<sb<=len(text)and text[sa:sb]==c['evidence_sentence']
                c['depth_span_candidates']=audit.phrase_candidates(text,c['depth_raw'],[sa,sb])if c['sentence_source_exact']else[]
                c['time_span_candidates']=audit.phrase_candidates(text,c['event_time_raw'],[sa,sb])if c['sentence_source_exact']else[]
                claims.append(c)
            durations.append(time.monotonic()-started)
            result={'record_id':row['record_id'],'text_sha256':row['text_sha256'],'status':'completed',
                    'leading_strip_offset':leading,'text_was_normalized':False,'claims':claims}
            stream.write(json.dumps(result,ensure_ascii=False)+'\n');stream.flush();signal.setitimer(signal.ITIMER_REAL,0)
    require(not any(n.split('.')[0]in{'spacy','thinc','torch','tensorflow','transformers'}for n in sys.modules), 'neural import occurred')
    return {'status':'completed','processed':len(request['rows']),'row_seconds':durations,
            'neural_libraries_loaded':False,'training_started':False,'network_database_blocked':True}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--sha256',required=True);args=parser.parse_args();output=Path('/output')
    try:
        audit.require(audit.digest(args.request)==args.sha256,'stale worker request')
        result=run(json.loads(args.request.read_text(encoding='utf-8')),output)
        with (output/'status.json').open('x',encoding='utf-8')as stream:json.dump(result,stream)
    except BaseException as exc:
        import traceback
        with (output/'failure-traceback.txt').open('x',encoding='utf-8')as stream:stream.write(traceback.format_exc())
        with (output/'failure.json').open('x',encoding='utf-8')as stream:json.dump({'status':'failed','error_type':type(exc).__name__},stream)
        raise SystemExit(2)from exc


if __name__=='__main__':main()
