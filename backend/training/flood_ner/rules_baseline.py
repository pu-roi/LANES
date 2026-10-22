"""Frozen mention-rule adapter, independent of annotations and flood claims."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Any

TYPE_TO_LABEL = {'street': 'ROAD', 'landmark': 'LANDMARK', 'barangay': 'BARANGAY',
                 'city': 'CITY', 'province': 'PROVINCE'}


def adapt_mentions(text: str, mentions: list[dict[str, Any]]) -> dict[str, Any]:
    spans: set[tuple[int, int, str]] = set()
    diagnostics: list[dict[str, Any]] = []
    for item in mentions:
        start, end, kind = item.get('char_start'), item.get('char_end'), item.get('place_type')
        reason = None
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
            reason = 'invalid_original_character_offsets'
        elif text[start:end] != item.get('raw_place_name'):
            reason = 'raw_name_does_not_match_original_slice'
        elif kind not in TYPE_TO_LABEL:
            reason = 'unsupported_emitted_type'
        if reason:
            diagnostics.append({'start': start, 'end': end, 'emitted_type': kind, 'reason': reason})
        else:
            spans.add((start, end, TYPE_TO_LABEL[kind]))
    return {'spans': [{'start': a, 'end': z, 'label': label} for a, z, label in sorted(spans)],
            'diagnostics': diagnostics}


def predict_mentions(text: str) -> dict[str, Any]:
    """Mention recognition only; no claims, geocoding, publication or labels as input."""
    from app.services.taglish_extraction_service import find_place_mentions, split_sentences_with_offsets
    mentions = []
    for sentence, start, end in split_sentences_with_offsets(text):
        if text[start:end] != sentence:
            raise ValueError('rules sentence offsets do not reproduce original text')
        mentions.extend(find_place_mentions(sentence, start, scoped_list_depth=False))
    return adapt_mentions(text, mentions)


def specification(root: Path) -> dict[str, Any]:
    """Hash local transitive app imports and the unchanged gazetteer assets."""
    pending = ['app.services.taglish_extraction_service']
    modules: dict[str, str] = {}
    while pending:
        name = pending.pop()
        path = root / 'backend' / (name.replace('.', '/') + '.py')
        if name in modules or not path.is_file():
            continue
        modules[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('app.'):
                pending.append(node.module)
            elif isinstance(node, ast.Import):
                pending.extend(a.name for a in node.names if a.name.startswith('app.'))
    files = {'backend/' + name.replace('.', '/') + '.py': sha for name, sha in modules.items()}
    for name in ['data/philippines_psgc_reference.csv', 'data/pasig_barangay_reference.csv',
                 'data/flooded_areas_pasig_clean.csv',
                 'backend/training/flood_ner/rules_baseline.py']:
        path = root / name
        if not path.is_file():
            raise ValueError('required rules baseline asset missing: ' + name)
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'schema_version': 'lanes-rule-mention-baseline-v1', 'state': 'mapping_frozen',
            'entry_point': 'training.flood_ner.rules_baseline.predict_mentions',
            'component': 'existing sentence splitter and find_place_mentions; not the full flood-claim pipeline',
            'type_to_label': TYPE_TO_LABEL, 'unsupported_types': ['unknown'],
            'unavailable_output_labels': ['LOCAL_AREA'],
            'locality_policy': 'Legacy landmark emissions remain LANDMARK, including numbered localities; no reference-driven relabeling.',
            'offset_convention': 'Zero-based, end-exclusive original Python Unicode character indices, never byte or normalized offsets.',
            'invalid_offsets': 'Retain diagnostic; never search reference text to repair offsets.',
            'duplicates': 'Deduplicate identical start/end/label only; retain overlaps and conflicting labels.',
            'label_source': 'Emitted type only; no annotations, inference from reference labels or gazetteer tuning.',
            'scope': 'All returned place mentions, including non-flood mentions; no reference-based filtering.',
            'files': dict(sorted(files.items()))}
