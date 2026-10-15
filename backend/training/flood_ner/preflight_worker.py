"""Standalone isolated child; reads constructed requests and emits JSON only."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import statistics
import sys
import time


def peak_working_set() -> int:
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD),
                  *[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);psapi=ctypes.WinDLL('psapi',use_last_error=True)
    kernel.GetCurrentProcess.restype=wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    info=Counters();info.cb=ctypes.sizeof(info)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(info),info.cb):raise ctypes.WinError(ctypes.get_last_error())
    return int(info.PeakWorkingSetSize)


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    request=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    if sys.version_info[:2]!=(3,11) or platform.system()!='Windows':raise ValueError('preflight requires isolated Windows CPython3.11')
    if any(c.get('origin')!='constructed_fixture' or c.get('quality')!='constructed' for c in request['cases']):raise ValueError('constructed provenance required')
    import spacy
    import torch
    if spacy.__version__!='3.7.5' or torch.version.cuda is not None:raise ValueError('spaCy3.7.5/CPU torch required')
    torch.set_num_threads(2);torch.manual_seed(0);spacy.require_cpu()
    before=time.perf_counter();nlp=spacy.load(request['model_dir'],exclude=['tagger','morphologizer','parser']);load_ms=(time.perf_counter()-before)*1000
    if nlp.meta.get('version')!='0.1.0' or set(nlp.get_pipe('ner').labels)!={'LOC','ORG','PER'}:raise ValueError('model identity/NER labels differ')
    for case in request['cases']:nlp(case['text'])
    latencies=[];results=[];signatures={};identical=True
    for repeat in range(10):
        for case in request['cases']:
            start=time.perf_counter();doc=nlp(case['text']);latencies.append((time.perf_counter()-start)*1000)
            if doc.text!=case['text']:raise ValueError('model changed source text')
            entities=[{'start':e.start_char,'end':e.end_char,'label':e.label_,'text':e.text} for e in doc.ents]
            signature=json.dumps(entities,sort_keys=True)
            if repeat and signatures[case['case_id']]!=signature:identical=False
            if not repeat:
                signatures[case['case_id']]=signature
                results.append({'case_id':case['case_id'],'text_sha256':hashlib.sha256(doc.text.encode('utf-8')).hexdigest(),
                                'tokens':[{'start':t.idx,'end':t.idx+len(t.text),'text':t.text} for t in doc],
                                'entities':entities,'reference_alignment':[{'start':p['start'],'end':p['end'],'label':p['label'],'aligned':doc.char_span(p['start'],p['end'],alignment_mode='strict') is not None} for p in case['expected_places']]})
    ordered=sorted(latencies)
    result={'schema_version':'lanes-model-preflight-result-v1','python_version':platform.python_version(),'spacy_version':spacy.__version__,
            'model_revision':request['model_revision'],'model_version':nlp.meta['version'],'cpu_only':True,
            'repeated_predictions_identical':identical,'pipeline':nlp.pipe_names,'cases':results,
            'packages':dict(sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions())),
            'resources':{'load_ms':load_ms,'p50_ms':statistics.median(latencies),'p95_ms':ordered[int(.95*(len(ordered)-1))],
                         'peak_working_set_bytes':peak_working_set(),'warmup_passes':1,'measured_passes':10,'measured_calls':len(latencies),'batch_size':1,'threads':2}}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))


if __name__=='__main__':main()
