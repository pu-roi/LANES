"""Single isolated v42 context comparison. Raw text/cached mentions only."""
import hashlib
import importlib.abc
import json
from pathlib import Path
import signal
import sys

sys.path.insert(0,'/code')


class NoNeuralDatabase(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname: str,path: object=None,target: object=None) -> None:
        if fullname.split('.')[0] in {'spacy','torch','transformers','sqlalchemy','psycopg','psycopg2','asyncpg'}:
            raise RuntimeError('neural/database modules prohibited')


def write(path: Path,value: object) -> None:
    with path.open('x',encoding='utf-8')as stream:json.dump(value,stream,ensure_ascii=False)


def run() -> None:
    request_path=Path('/input/request.json')
    assert hashlib.sha256(request_path.read_bytes()).hexdigest()==sys.argv[1]
    request=json.loads(request_path.read_text(encoding='utf-8'))
    assert set(request)=={'schema','implementation','groups'}and request['schema']=='lanes-context-worker-v42'
    for name,sha in request['implementation'].items():
        assert not Path(name).is_absolute()and ':'not in name and '\\'not in name and '..'not in Path(name).parts
        assert hashlib.sha256((Path('/code')/name).read_bytes()).hexdigest()==sha
    output=Path('/output');assert not any(output.iterdir())
    sys.meta_path.insert(0,NoNeuralDatabase())
    from news_ner.context_association_v42 import extract
    from news_ner.contract import validate_raw_input
    counts={'context_rows':24,'existing_rows':238,'temporal_rows':36,'old_regressions':36,'new_regressions':36,'article_rows':1}
    assert set(request['groups'])==set(counts)
    for key,count in counts.items():
        rows=request['groups'][key]
        assert len(rows)==len({r['record_id']for r in rows})==count
        for row in rows:
            if 'views'in row:
                assert set(row)=={'record_id','views'}and set(row['views'])=={'original','transport_asset','shared_locality','explicit_road','combined'}
                for raw in row['views'].values():validate_raw_input(raw)
            else:validate_raw_input(row)
    def deadline(*_args: object) -> None:raise TimeoutError('context deadline')
    signal.signal(signal.SIGALRM,deadline)
    write(output/'ready.json',{'status':'ready','neural':False})
    processed=0;graphs=0
    for key,rows in request['groups'].items():
        with (output/(key+'.jsonl')).open('x',encoding='utf-8')as stream:
            for row in rows:
                signal.setitimer(signal.ITIMER_REAL,10)
                if 'views'in row:
                    result={'record_id':row['record_id'],'views':{view:extract(raw)for view,raw in row['views'].items()}}
                    graphs+=5
                else:
                    result={'record_id':row['record_id'],'output':extract(row)};graphs+=1
                signal.setitimer(signal.ITIMER_REAL,0)
                stream.write(json.dumps(result,ensure_ascii=False)+'\n');stream.flush();processed+=1
    assert processed==371 and graphs==1419
    assert not any(n.split('.')[0]in{'spacy','torch','sqlalchemy','psycopg'}for n in sys.modules)
    write(output/'status.json',{'status':'completed','raw_records':processed,'graphs':graphs,'neural_inference':False,'database_access':False})


if __name__=='__main__':
    try:run()
    except BaseException as exc:
        write(Path('/output/failure.json'),{'error_type':type(exc).__name__})
        raise
