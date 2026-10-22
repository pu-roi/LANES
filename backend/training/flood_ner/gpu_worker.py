"""Isolated constructed-only GPU execution and CPU portability replay."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import threading
import time
from typing import Any


def sibling(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rows(nlp: Any, cases: list[dict], sync: Any) -> tuple[list[dict], dict]:
    result = []
    timings = []
    for case in cases:
        nlp(case['text'])
    sync()
    for case in cases:
        start = time.perf_counter()
        doc = nlp(case['text'])
        sync()
        timings.append((time.perf_counter() - start) * 1000)
        if doc.text != case['text']:
            raise ValueError('constructed source text changed')
        result.append({'case_id': case['case_id'], 'text_sha256': hashlib.sha256(doc.text.encode('utf-8')).hexdigest(),
                       'entities': [{'start': e.start_char, 'end': e.end_char, 'label': e.label_, 'text': e.text} for e in doc.ents]})
    ordered = sorted(timings)
    return result, {'p50_ms': statistics.median(timings), 'p95_ms': ordered[int(.95 * (len(ordered) - 1))],
                    'warmup_calls': len(cases), 'measured_calls': len(cases), 'batch_size': 1}


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    mode = sys.argv[2]
    cases = request['cases']
    if sys.version_info[:2] != (3, 11) or platform.system() != 'Windows' or mode not in {'gpu', 'cpu'}:
        raise ValueError('explicit mode and isolated Windows Python 3.11 required')
    if len(cases) != 24 or any(c['origin'] != 'constructed_fixture' or c['quality'] != 'constructed'
                             or hashlib.sha256(c['text'].encode('utf-8')).hexdigest() != c['text_sha256'] for c in cases):
        raise ValueError('hash-bound constructed inputs required')
    # DLL search is limited to this isolated environment and this process.
    site = Path(sys.prefix) / 'Lib/site-packages'
    handles = []
    for directory in (site / 'torch/lib', site / 'nvidia/cuda_runtime/bin', site / 'nvidia/cuda_nvrtc/bin'):
        if directory.is_dir():
            handles.append(os.add_dll_directory(str(directory)))
    os.environ['CUDA_PATH'] = str(site / 'nvidia/cuda_runtime')
    import torch
    import spacy
    from spacy.training import Example
    from spacy.util import fix_random_seed
    if spacy.__version__ != '3.7.5':
        raise ValueError('pinned spaCy 3.7.5 required')
    torch.set_num_threads(2)
    fix_random_seed(42)
    result = {'mode': mode, 'python_version': platform.python_version(), 'spacy_version': spacy.__version__,
              'model_revision': request['model_revision'], 'torch_version': torch.__version__}
    sync = lambda: None
    if mode == 'gpu':
        import cupy as cp
        if not torch.cuda.is_available():
            raise ValueError('PyTorch CUDA is unavailable')
        torch.cuda.set_device(0)
        tensor = torch.arange(1024, device='cuda', dtype=torch.float32)
        if tensor.sum().item() != 523776:
            raise ValueError('Torch CUDA calculation differs')
        torch.cuda.synchronize()
        del tensor
        torch.cuda.empty_cache()
        if not spacy.require_gpu(0):
            raise ValueError('spaCy GPU selection failed')
        values = cp.arange(1024, dtype=cp.float32)
        if float(cp.sum(values).get()) != 523776:
            raise ValueError('CuPy CUDA kernel calculation differs')
        del values
        sync = cp.cuda.Stream.null.synchronize
        config = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(config):
            cp.show_config()
        result.update({'cupy_version': cp.__version__, 'cupy_config': config.getvalue(),
                       'cupy_kernel_passed': True, 'torch_cuda_passed': True, 'spacy_gpu_selected': True,
                       'torch_cuda_version': torch.version.cuda, 'gpu_name': torch.cuda.get_device_name(0),
                       'gpu_compute_capability': list(torch.cuda.get_device_capability(0))})
    else:
        spacy.require_cpu()
    start = time.perf_counter()
    nlp = spacy.load(request['model_dir'], exclude=['tagger', 'morphologizer', 'parser'])
    sync()
    load_ms = (time.perf_counter() - start) * 1000
    if nlp.meta['version'] != '0.1.0' or set(nlp.get_pipe('ner').labels) != {'LOC', 'ORG', 'PER'}:
        raise ValueError('pinned native model identity differs')
    result['baseline_predictions'], inference = rows(nlp, cases, sync)
    if mode == 'gpu':
        params = [node.get_param(name) for _, component in nlp.pipeline
                  for node in component.model.walk() for name in node.param_names if node.has_param(name)]
        gpu_params = [p for p in params if isinstance(p, cp.ndarray)]
        if not gpu_params:
            raise ValueError('model has no CUDA parameters')
        result['parameters_on_gpu'] = True
        result['parameter_arrays_on_gpu'] = len(gpu_params)
        result['parameter_arrays_on_cpu'] = len(params) - len(gpu_params)
        # Fresh six-class head, initialized separately; copy only the pinned
        # pretrained NER encoder. The input model and its coarse head stay on disk.
        encoder = nlp.get_pipe('ner').model.get_ref('tok2vec').to_bytes()
        config = deepcopy(nlp.config['components']['ner'])
        config.pop('factory')
        nlp.remove_pipe('ner')
        ner = nlp.add_pipe('ner', config=config)
        labels = sorted({p['label'] for c in cases for p in c['expected_places']})
        for label in labels:
            ner.add_label(label)
        sibling('model_tokenizer').apply_candidate(nlp.tokenizer)
        examples = []
        for case in cases:
            doc = nlp.make_doc(case['text'])
            entities = [(p['start'], p['end'], p['label']) for p in case['expected_places']]
            if any(doc.char_span(a, z, alignment_mode='strict') is None for a, z, _ in entities):
                raise ValueError('candidate tokenizer does not align a constructed training reference')
            examples.append(Example.from_dict(doc, {'entities': entities}))
        ner.initialize(lambda: examples, nlp=nlp)
        ner.model.get_ref('tok2vec').from_bytes(encoder)
        optimizer = nlp.resume_training()
        stop = threading.Event()
        samples = []
        def sample_memory() -> None:
            try:
                with cp.cuda.Device(0):
                    while not stop.is_set():
                        free, total = cp.cuda.runtime.memGetInfo()
                        samples.append({'device_used_bytes': total - free,
                                        'cupy_pool_reserved_bytes': cp.get_default_memory_pool().total_bytes()})
                        stop.wait(.01)
            except Exception as exc:
                samples.append({'error': str(exc)})
        sampler = threading.Thread(target=sample_memory, daemon=True)
        sampler.start()
        steps = []
        try:
            for batch in (1, 4, 8):
                losses = {}
                before = time.perf_counter()
                nlp.update(examples[:batch], sgd=optimizer, drop=0.0, losses=losses)
                sync()
                loss = float(losses['ner'])
                if not math.isfinite(loss):
                    raise ValueError('non-finite constructed training loss')
                steps.append({'batch_size': batch, 'elapsed_ms': (time.perf_counter() - before) * 1000,
                              'loss': loss, 'cupy_pool_reserved_bytes': cp.get_default_memory_pool().total_bytes(),
                              'cupy_pool_used_bytes': cp.get_default_memory_pool().used_bytes()})
        finally:
            stop.set()
            sampler.join(timeout=5)
        if not samples or any('error' in s for s in samples):
            raise ValueError('GPU memory sampler failed: ' + str(samples))
        result.update({'trial_labels': list(ner.labels), 'training_steps': steps,
                       'trial_initialization': 'fresh six-class NER head with copied pinned pretrained NER tok2vec encoder',
                       'sampled_peak_total_device_used_bytes': max(s['device_used_bytes'] for s in samples),
                       'sampled_peak_cupy_pool_reserved_bytes': max(s['cupy_pool_reserved_bytes'] for s in samples),
                       'memory_samples': len(samples), 'memory_sample_interval_ms': 10,
                       'memory_caveat': 'sampled device usage includes other processes; CuPy pool figures are reserved allocations, not exact peak live tensors'})
        result['trial_predictions'], trial_inference = rows(nlp, cases, sync)
        nlp.to_disk(request['trial_model'])
    else:
        nlp = spacy.load(request['trial_model'])
        result['trial_predictions'], trial_inference = rows(nlp, cases, sync)
    result['resources'] = {'load_ms': load_ms, 'native_inference': inference, 'trial_inference': trial_inference,
                           'peak_working_set_bytes': sibling('preflight_worker').peak_working_set()}
    result['packages'] = dict(sorted((d.metadata['Name'], d.version) for d in importlib.metadata.distributions()))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
