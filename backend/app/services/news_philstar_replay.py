"""Authenticated Philstar response reuse; never dispatch or rewrite evidence."""
from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
import re

from app.services.news_gemini_receipts import replay_bundle, validate_batch
from app.services.news_ner_durable.contracts import sha
from app.services.news_philstar_pilot import BODY, require

VERSION = 'philstar-retained-response-replay-v1'


def source_rows(rows: tuple, document: dict, context_ids: list[str]) -> tuple[tuple, list[dict]]:
    """Record source-bound conservative corrections; preserve provider originals."""
    from app.services.news_ner_durable.resolution import quote_options
    body = document['evidence_text']
    require(hashlib.sha256(body.encode()).hexdigest() == BODY, 'philstar_replay_source_changed')
    options = quote_options(body)
    targets = {t['id']: t for t in document['targets']}
    caption_end = body.index('MANILA, Philippines')
    changed, proof = [], []
    for row in rows:
        target = targets[row.target_id]
        updates, reason = {}, None
        if row.verdict == 'observed' and target['end'] <= caption_end:
            updates, reason = {'verdict': 'unsupported'}, 'photo_caption_only'
        elif row.target_id in context_ids and row.verdict == 'observed':
            updates, reason = {'verdict': 'unsupported'}, 'intersection_crossing_context'
        elif row.verdict == 'observed' and row.access == 'passable_unspecified':
            # A directly cited caution heading is a stronger restriction than
            # the provider's generic passable classification, never all-vehicle access.
            if any(re.fullmatch(r'Passable with caution', options[i]['quote'].strip(), re.I)
                   for i in row.access_evidence):
                updates, reason = {'access': 'passable_with_caution'}, 'retain_cited_caution_heading'
        if row.verdict == 'observed' and 'verdict' not in updates and row.road_section == target['text']:
            # A provider's shortened road name cannot erase an intersection
            # explicitly present in this target's own cited source line.
            own = [i for i, q in enumerate(options)
                   if q['start'] <= target['start'] < target['end'] <= q['end']
                   and i in row.section_evidence]
            if len(own) == 1:
                section = re.split(r'\s+-\s+', options[own[0]]['quote'], maxsplit=1)[0].strip()
                if re.search(r'\s+cor\.?\s+', section, re.I) and target['text'] in section:
                    updates['road_section'] = section
                    reason = 'retain_full_reported_intersection'
        value = row.model_copy(update=updates) if updates else row
        changed.append(value)
        if updates:
            proof.append(dict(target_id=row.target_id, reason=reason,
                original_row_sha256=sha(row.model_dump(mode='json')),
                effective_row_sha256=sha(value.model_dump(mode='json')), changed_fields=sorted(updates)))
    return tuple(changed), proof


class PhilstarReplayBatchPlan:
    def __init__(self, manifest: dict, *, cache_loader: object = None) -> None:
        sizes = manifest.get('batch_sizes', [])
        require(manifest.get('schema_version') == VERSION
                and manifest.get('generation_requests_allowed') == 0
                and manifest.get('source_version_id') == 573
                and manifest.get('body_sha256') == BODY
                and bool(sizes) and all(type(n) is int and 1 <= n <= 4 for n in sizes)
                and len(manifest.get('bundle_sha256s', [])) == len(sizes),
                'philstar_replay_manifest_invalid')
        self.manifest, self.pin, self.cache_loader = deepcopy(manifest), sha(manifest), cache_loader

    @property
    def identity(self) -> str:
        require(sha(self.manifest) == self.pin, 'philstar_replay_manifest_changed')
        return self.pin

    def batches(self, candidates: list[dict]) -> list[list[dict]]:
        self.identity
        require(sha(candidates) == self.manifest['targets_sha256']
                and len(candidates) == sum(self.manifest['batch_sizes']), 'philstar_replay_targets_changed')
        result, offset = [], 0
        for size in self.manifest['batch_sizes']:
            result.append(candidates[offset:offset + size]); offset += size
        return result

    def adopt(self, index: int, payload: dict, context: dict, config: object, journal: object) -> tuple:
        self.identity
        require(index in range(len(self.manifest['batch_sizes'])) and self.cache_loader is not None
                and journal is not None, 'philstar_replay_cache_required')
        bundle = self.cache_loader(index)
        require(sha(bundle) == self.manifest['bundle_sha256s'][index], 'philstar_replay_bundle_changed')
        check = replay_bundle(bundle, sha(bundle), config=config)
        require(check['status'] == 'evidence_references_passed'
                and bundle['intent']['payload'] == payload and bundle['intent']['context'] == context,
                'philstar_replay_request_changed')
        document = json.loads(payload['contents'][0]['parts'][0]['text'])
        require(hashlib.sha256(document['evidence_text'].encode()).hexdigest() == BODY,
                'philstar_replay_source_changed')
        parsed, usage = validate_batch(payload, base64.b64decode(bundle['response']['body_base64']), config)
        rows, normalizations = source_rows(parsed.results, document, self.manifest.get('context_target_ids', []))
        key = sha(dict(request_sha256=sha(payload), context=context))
        journal.store.put(key+'/adoption.json', dict(schema_version=VERSION,
            original_bundle_sha256=sha(bundle), original_response_unchanged=True,
            normalizations=normalizations,
            generation_requests=0, token_count_requests=0))
        return parsed.model_copy(update={'results': rows}), usage


class ZeroProviderBudget:
    def reserve(self, *args: object, **kwargs: object) -> str:
        require(False, 'philstar_replay_provider_forbidden')

    def stop(self, reason: str) -> None:
        return None
