"""spaCy registry callbacks for the pinned six-class encoder-transfer recipe.

Load this file with spaCy --code when using the generated configuration.
Callbacks initialize weights only. They never perform optimizer updates.
"""
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

import spacy
from spacy.tokenizer import Tokenizer
from spacy.util import registry
from spacy.vocab import Vocab

LABELS = ('BARANGAY', 'CITY', 'LANDMARK', 'LOCAL_AREA', 'PROVINCE', 'ROAD')
ARTIFACTS = Path(__file__).resolve().parent / 'artifacts'


def better_checkpoint(score: float, step: int, best_score: float, best_step: int | None) -> bool:
    if type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError('finite development entity F1 in [0,1] required')
    if type(step) is not int or step < 0:
        raise ValueError('nonnegative optimizer step required')
    return best_step is None or score > best_score or (score == best_score and step < best_step)


@registry.callbacks('lanes.capture_training_step.v1')
def capture_step() -> Callable:
    def before(nlp: Any, info: dict) -> None:
        nlp.meta['lanes_training_step'] = info['step']
    return before


@registry.callbacks('lanes.select_earliest_dev_checkpoint.v1')
def select_checkpoint(output: str) -> Callable:
    destination = Path(output).absolute()
    if (not destination.resolve().is_relative_to(ARTIFACTS.resolve()) or destination.exists()
            or any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                   for p in (destination, *destination.parents))):
        raise ValueError('selection output must be a new artifact path without symlinks/junctions')
    best_score, best_step = float('-inf'), None
    def before(nlp: Any) -> Any:
        nonlocal best_score, best_step
        score = nlp.meta['performance']['ents_f']
        step = nlp.meta['lanes_training_step']
        if better_checkpoint(score, step, best_score, best_step):
            # This callback is only invoked by the later, explicitly started trainer.
            # Its selected checkpoint is authoritative; spaCy's built-in model-best
            # overwrites ties and therefore does not implement the frozen contract.
            destination.mkdir(parents=True, exist_ok=True)
            nlp.to_disk(destination / 'model')
            (destination / 'selection.json').write_text(json.dumps({
                'partition': 'dev', 'metric': 'strict six-class entity micro F1',
                'score': score, 'step': step, 'tie_break': 'earlier checkpoint step',
                'model': 'model'}, sort_keys=True, indent=2) + '\n', encoding='utf-8')
            best_score, best_step = score, step
        return nlp
    return before


def verified_model(model_manifest: str, manifest_sha256: str) -> Path:
    path = Path(model_manifest)
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest_sha256:
        raise ValueError('pinned model manifest changed')
    value = json.loads(path.read_text(encoding='utf-8'))
    if (value.get('revision') != '51a40433059d8a2c25b98a48eca854f8789a491a'
            or value.get('version') != '0.1.0' or value.get('model') != 'tl_calamancy_md'
            or value.get('download_complete') is not True or len(value.get('files', [])) != 23):
        raise ValueError('unsupported pretrained model')
    model = Path(value['model_dir']).resolve()
    seen = set()
    for entry in value['files']:
        p = (model / entry['path']).resolve()
        if (not p.is_relative_to(model) or not p.is_file() or p.stat().st_size != entry['bytes']
                or hashlib.sha256(p.read_bytes()).hexdigest() != entry['sha256'] or entry['path'] in seen):
            raise ValueError('pretrained model file identity changed')
        seen.add(entry['path'])
    if {p.relative_to(model).as_posix() for p in model.rglob('*') if p.is_file()} != seen:
        raise ValueError('unmanifested pretrained model file')
    return model


@registry.tokenizers('lanes.qualified_tokenizer.v1')
def qualified_tokenizer(model_manifest: str, manifest_sha256: str,
                        tokenizer_file: str, tokenizer_sha256: str) -> Callable:
    def create(nlp: Any) -> Tokenizer:
        if spacy.__version__ != '3.7.5':
            raise ValueError('spaCy 3.7.5 required')
        model = verified_model(model_manifest, manifest_sha256)
        data = Path(tokenizer_file).read_bytes()
        if hashlib.sha256(data).hexdigest() != tokenizer_sha256:
            raise ValueError('qualified tokenizer bytes changed')
        nlp.vocab = Vocab().from_disk(model / 'vocab')
        tokenizer = Tokenizer(nlp.vocab).from_bytes(data, exclude=['vocab'])
        if tokenizer.to_bytes(exclude=['vocab']) != data:
            raise ValueError('qualified tokenizer serialization differs')
        return tokenizer
    return create


@registry.callbacks('lanes.add_location_labels.v1')
def location_labels() -> Callable:
    def before(nlp: Any) -> Any:
        if nlp.pipe_names != ['ner']:
            raise ValueError('six-class experiment must contain only the independent NER component')
        ner = nlp.get_pipe('ner')
        for label in LABELS:
            ner.add_label(label)
        if set(ner.labels) != set(LABELS):
            raise ValueError('unexpected existing coarse/surplus labels')
        return nlp
    return before


@registry.callbacks('lanes.restore_ner_encoder.v1')
def restore_encoder(model_manifest: str, manifest_sha256: str) -> Callable:
    def after(nlp: Any) -> Any:
        model = verified_model(model_manifest, manifest_sha256)
        source = spacy.load(model, exclude=['tok2vec', 'tagger', 'morphologizer', 'parser'])
        if set(source.get_pipe('ner').labels) != {'LOC', 'ORG', 'PER'}:
            raise ValueError('native NER head identity differs')
        data = source.get_pipe('ner').model.get_ref('tok2vec').to_bytes()
        encoder = nlp.get_pipe('ner').model.get_ref('tok2vec')
        encoder.from_bytes(data)
        if encoder.to_bytes() != data:
            raise ValueError('pretrained encoder transfer differs')
        nlp.meta['lanes_initialization'] = {
            'method': 'fresh six-class NER head; copied pinned pretrained NER encoder; pinned static vocabulary',
            'encoder_sha256': hashlib.sha256(data).hexdigest(), 'optimizer_updates': 0}
        return nlp
    return after
