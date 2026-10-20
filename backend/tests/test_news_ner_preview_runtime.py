"""Actual subprocess bounds and simulated owned Docker lifecycle faults."""
import asyncio
from contextlib import contextmanager
import json
from pathlib import Path
import sys

import pytest
from app.services.news_ner import runtime
from app.services.news_ner.bundle import MODEL_FILES, VOCAB_FILES, digest, verify_bundle
from app.services.news_ner.contract import IMAGE, object_sha


@pytest.mark.parametrize('mode', ['success','crash','timeout','malformed','cancel','cleanup_failure'])
def test_owned_cleanup_for_every_exit(tmp_path,monkeypatch,mode):
    path=tmp_path/'lease'
    actual_lease=runtime.lease
    monkeypatch.setattr(runtime,'lease',lambda _path,owner:actual_lease(path,owner))
    monkeypatch.setattr(runtime,'verify_bundle',lambda *_args:{})
    calls=[]
    owner={'name':None}
    started=asyncio.Event()
    async def command(args,payload=None,timeout=10):
        calls.append(args)
        if args[1:3]==['image','inspect']:return 0,(IMAGE+' linux amd64').encode(),b''
        if args[1]=='create':
            owner['name']=args[args.index('--name')+1]
            return 0,b'a'*64,b''
        if args[1]=='start':
            started.set()
            if mode=='cancel':await asyncio.Future()
            if mode=='timeout':raise TimeoutError()
            if mode=='crash':return 2,b'',b'private worker text'
            if mode=='malformed':return 0,b'{',b''
            code=json.loads(payload)['code']
            return 0,json.dumps({'provenance':{'code_sha256':object_sha(code)}}).encode(),b''
        if args[1]=='inspect':return 0,json.dumps({'lanes.ner-preview.owner':owner['name']}).encode(),b''
        if args[1]=='rm':return (1 if mode=='cleanup_failure' else 0),b'',b''
        if args[1]=='ps':return 0,b'',b''
        raise AssertionError(args)
    monkeypatch.setattr(runtime,'command',command)
    async def execute():
        task=asyncio.create_task(runtime.run_local({'text':'fictional'},tmp_path,'a'*64,'docker'))
        if mode=='cancel':
            await started.wait();task.cancel()
        if mode=='success':await task
        elif mode=='cancel':
            with pytest.raises(asyncio.CancelledError):await task
        else:
            with pytest.raises(runtime.PreviewError) as error:await task
            assert error.value.code=={'timeout':'preview_timeout','cleanup_failure':'preview_cleanup_unavailable'}.get(mode,'preview_worker_failed')
    asyncio.run(execute())
    assert any(a[1]=='rm' and a[-1]=='a'*64 for a in calls)
    assert path.read_bytes()==(owner['name'].encode() if mode=='cleanup_failure' else b'\0')
    assert not any(a[1:3]==['system','prune'] for a in calls)


def test_unavailable_assets_never_launch_worker(tmp_path,monkeypatch):
    async def forbidden(*args,**kwargs):raise AssertionError('Docker must not run')
    monkeypatch.setattr(runtime,'command',forbidden)
    with pytest.raises(runtime.PreviewError,match='preview_assets_unavailable'):
        asyncio.run(runtime.run_local({},tmp_path,'a'*64,'docker'))


def test_subprocess_output_limit_and_timeout():
    with pytest.raises(runtime.PreviewError,match='preview_worker_failed'):
        asyncio.run(runtime.command([sys.executable,'-c','import sys;sys.stdout.write("x"*9000000)']))
    with pytest.raises(TimeoutError):
        asyncio.run(runtime.command([sys.executable,'-c','import time;time.sleep(5)'],timeout=0.05))


def test_bundle_tamper_and_membership(tmp_path):
    files={}
    for name in {'model/'+n for n in MODEL_FILES}|{'base/vocab/'+n for n in VOCAB_FILES}:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'fictional')
        files[name]={'sha256':digest(path),'bytes':path.stat().st_size}
    value={'schema':'lanes-ner-inference-bundle-v1','model_manifest_sha256':'a'*64,'resource_manifest_sha256':'b'*64,'files':files}
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps(value),encoding='utf-8');sha=digest(manifest)
    assert verify_bundle(tmp_path,sha)==value
    (tmp_path/'unexpected').write_text('wrong',encoding='utf-8')
    with pytest.raises(ValueError,match='unexpected bundle files'):verify_bundle(tmp_path,sha)
    (tmp_path/'unexpected').unlink()
    (tmp_path/'model/config.cfg').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='bundle asset mismatch'):verify_bundle(tmp_path,sha)
