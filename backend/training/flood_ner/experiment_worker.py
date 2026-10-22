"""GPU initialization readiness only; no predictions or optimizer updates."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys

POLICY = {'batch_size': 8, 'dropout': 0.1, 'learning_rate': 0.001,
          'max_epochs': 30, 'max_steps': 1000, 'eval_frequency': 35, 'patience': 175}


def build_config(request: dict, seed: int):
    import spacy
    from spacy.util import load_config

    if type(seed) is not int or seed not in (0, 1, 2):
        raise ValueError('frozen seed must be 0, 1 or 2')
    config = spacy.blank('tl').config
    pinned = load_config(Path(request['model_dir']) / 'config.cfg')
    config['paths'].update(train=str(Path(request['export']) / 'train.spacy'),
                           dev=str(Path(request['export']) / 'dev.spacy'),
                           vectors=None, init_tok2vec=None)
    config['system']['seed'] = seed
    config['nlp'].update(pipeline=['ner'], batch_size=8, disabled=[])
    config['nlp']['tokenizer'] = {
        '@tokenizers': 'lanes.qualified_tokenizer.v1',
        'model_manifest': request['model_manifest'], 'manifest_sha256': request['model_manifest_sha256'],
        'tokenizer_file': str(Path(request['export']) / 'tokenizer.bin'),
        'tokenizer_sha256': request['tokenizer_sha256']}
    config['components'] = {'ner': deepcopy(pinned['components']['ner'])}
    config['training'].update(dropout=POLICY['dropout'], max_epochs=POLICY['max_epochs'],
                              max_steps=POLICY['max_steps'], eval_frequency=POLICY['eval_frequency'],
                              patience=POLICY['patience'], frozen_components=[], annotating_components=[],
                              score_weights={'ents_f': 1.0, 'ents_p': 0.0, 'ents_r': 0.0, 'ents_per_type': None})
    config['training']['batcher'] = {'@batchers': 'spacy.batch_by_sequence.v1', 'size': 8, 'get_length': None}
    config['training']['optimizer']['learn_rate'] = POLICY['learning_rate']
    config['training']['before_update'] = {'@callbacks': 'lanes.capture_training_step.v1'}
    config['training']['before_to_disk'] = {
        '@callbacks': 'lanes.select_earliest_dev_checkpoint.v1',
        'output': str(Path(request['future_training_root']) / ('seed-' + str(seed)) / 'selected-checkpoint')}
    config['initialize'].update(vectors=None, init_tok2vec=None,
        before_init={'@callbacks': 'lanes.add_location_labels.v1'},
        after_init={'@callbacks': 'lanes.restore_ner_encoder.v1',
                    'model_manifest': request['model_manifest'], 'manifest_sha256': request['model_manifest_sha256']})
    if 'test.spacy' in config.to_str():
        raise ValueError('test corpus must not enter training configuration')
    return config


def parameter_devices(model, gpu_type: type, cpu_type: type) -> dict:
    # spaCy's pinned TransitionBasedParser.v2 intentionally computes its upper
    # classifier on CPU (spacy/ml/models/parser.py). Encoder/lower stay on GPU.
    upper = {id(node) for node in model.get_ref('upper').walk()}
    counts = {'gpu': 0, 'cpu_upper': 0}
    for node in model.walk():
        for name in node.param_names:
            if not node.has_param(name):
                continue
            value = node.get_param(name)
            key, expected = ('cpu_upper', cpu_type) if id(node) in upper else ('gpu', gpu_type)
            if not isinstance(value, expected):
                raise ValueError('NER parameter device differs from pinned architecture')
            counts[key] += 1
    if not all(counts.values()):
        raise ValueError('expected GPU encoder/lower and CPU upper classifier parameters')
    return counts


def main() -> None:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    if sys.version_info[:2] != (3, 11) or request.get('operation') != 'initialize_only':
        raise ValueError('isolated Python 3.11 initialization-only request required')
    site = Path(sys.prefix) / 'Lib/site-packages'
    handles = [os.add_dll_directory(str(p)) for p in
               (site / 'torch/lib', site / 'nvidia/cuda_runtime/bin', site / 'nvidia/cuda_nvrtc/bin') if p.is_dir()]
    os.environ['CUDA_PATH'] = str(site / 'nvidia/cuda_runtime')
    import spacy
    import cupy as cp
    import torch
    import numpy as np
    from spacy.training.initialize import init_nlp
    from spacy.util import load_config

    if spacy.__version__ != '3.7.5' or not torch.cuda.is_available() or not spacy.require_gpu(0):
        raise ValueError('existing qualified spaCy GPU runtime unavailable')
    torch.set_num_threads(2)
    module_path = Path(__file__).with_name('experiment_registry.py')
    spec = importlib.util.spec_from_file_location('lanes_experiment_registry', module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    results = []
    for seed in (0, 1, 2):
        config = build_config(request, seed)
        path = Path(request['output']) / ('train-seed-' + str(seed) + '.cfg')
        path.write_text(config.to_str(), encoding='utf-8')
        loaded = load_config(path)
        nlp = init_nlp(loaded, use_gpu=0)
        if nlp.pipe_names != ['ner'] or set(nlp.get_pipe('ner').labels) != set(module.LABELS):
            raise ValueError('six-class initialized pipeline differs')
        if hashlib.sha256(nlp.tokenizer.to_bytes(exclude=['vocab'])).hexdigest() != request['tokenizer_sha256']:
            raise ValueError('training tokenizer differs from qualified export')
        devices = parameter_devices(nlp.get_pipe('ner').model, cp.ndarray, np.ndarray)
        initialized = nlp.meta['lanes_initialization']
        if initialized['optimizer_updates'] != 0:
            raise ValueError('unexpected optimizer update')
        results.append({'seed': seed, 'config_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'labels': list(nlp.get_pipe('ner').labels), 'pipeline': nlp.pipe_names,
                        'gpu_parameter_arrays': devices['gpu'],
                        'cpu_upper_parameter_arrays': devices['cpu_upper'], 'initialization': initialized,
                        'tokenizer_sha256': request['tokenizer_sha256'],
                        'configuration_loaded': True, 'optimizer_updates': 0})
        del nlp
        cp.get_default_memory_pool().free_all_blocks()
    print(json.dumps({'state': 'passed', 'operation': 'initialize_only', 'seeds': results,
                      'python_version': platform.python_version(), 'spacy_version': spacy.__version__,
                      'gpu_name': torch.cuda.get_device_name(0), 'optimizer_updates': 0,
                      'model_predictions_performed': False, 'training_performed': False,
                      'test_corpus_read': False, 'training_policy': POLICY}, sort_keys=True))


if __name__ == '__main__':
    main()
