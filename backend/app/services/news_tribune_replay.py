"""Zero-provider replay; crossing roads can become source-bound context only.

V1 retains its original crossing-only behavior. V2 repairs reviewed source
context under the exact Tribune body hash, without transferring a clock.
Original provider responses remain immutable and separately authenticated.
"""
from __future__ import annotations

import base64
from copy import deepcopy
import json
import re
from typing import Any

from app.services.news_ner_durable.contracts import sha
from app.services.news_gemini_receipts import replay_bundle, validate_batch
from app.services.news_tribune_pilot import require

VERSION = 'tribune-crossing-context-replay-v1'
CONTEXT_VERSION = 'tribune-source-context-replay-v2'


def source_context(rows: list, document: dict, semantic: dict) -> tuple[list, list[dict], dict]:
    """Repair exact reviewed citations/locality roles, never invent facts/time.

    This adoption applies only to the already reviewed, complete Tribune body.
    Its opening Thursday-afternoon report governs the following flooding
    paragraph; the intervening Boni clock is not a shared time heading.
    """
    import hashlib
    from app.services.news_tribune_pilot import BODY
    from app.services.news_ner_durable.resolution import quote_options
    body = document['evidence_text']
    require(hashlib.sha256(body.encode()).hexdigest() == BODY, 'tribune_context_source_changed')
    options = quote_options(body)
    by_target = {t['id']: t for t in document['targets']}
    effective, proof = [], []
    reviewed = deepcopy(semantic)
    for row in rows:
        target = by_target[row.target_id]
        changes, fixed = {}, set()
        # The provider already selected the exact weekday, but omitted its
        # source citation. Include both the introduction and target paragraph.
        if (row.verdict == 'observed' and row.status == 'active'
                and row.date_text == 'Thursday' and row.clock_text is None
                and not row.time_evidence and row.time_role == 'observation'
                and target['text'] in {'Quirino Avenue', 'Guazon Street', 'Gov. Pascual Avenue'}
                and options[2]['start'] <= target['start'] < target['end'] <= options[2]['end']
                and row.place_evidence == (2,) and row.status_evidence == (2,)):
            changes.update(time_evidence=(0, 2), contemporaneous=False)
            fixed.add('native_resolution_date_evidence_missing')
        # A sitio qualifier stays in road_section/source evidence, not in the
        # canonical barangay slot. It supplies no replacement barangay.
        if (target['label'] == 'ROAD' and row.barangay == 'Sitio 6' and row.city == 'Malabon City'
                and row.place_evidence == (2,) and 'in Sitio 6' in options[2]['quote']):
            changes['barangay'] = None
            fixed.add('native_resolution_barangay_unresolved')
        # These exact occurrences qualify the named road in one clause. They
        # are not independent sitio-wide or city-wide flooding statements.
        qualifier = re.search(r'in Sitio 6, Malabon City', options[2]['quote'])
        if (qualifier and target['label'] in {'LOCAL_AREA','CITY'}
                and target['text'] in {'Sitio 6','Malabon City'}
                and options[2]['start'] + qualifier.start() <= target['start'] < target['end']
                <= options[2]['start'] + qualifier.end() and row.place_evidence == (2,)):
            changes['verdict'] = 'unsupported'
        changed = row.model_copy(update=changes) if changes else row
        effective.append(changed)
        if changes:
            proof.append(dict(target_id=row.target_id, reason='source_context_repair',
                changed_fields=sorted(changes), original_row_sha256=sha(row.model_dump(mode='json')),
                effective_row_sha256=sha(changed.model_dump(mode='json')), clock_transferred=False))
            for outcome in reviewed['row_outcomes']:
                if outcome['target_id'] == row.target_id:
                    outcome['issues'] = [i for i in outcome['issues'] if i['code'] not in fixed]
                    if not outcome['issues'] and row.verdict == 'observed':
                        outcome['outcome'] = 'accepted'
    return effective, proof, reviewed


def crossing_context(rows: list, targets: list[dict], semantic: dict, *, partial_depth: bool = False) -> tuple[list, list[dict]]:
    """Suppress only an accepted secondary road inside one exact intersection."""
    by_target = {t['id']:t for t in targets}
    accepted = {o['target_id'] for o in semantic.get('row_outcomes',[]) if o['outcome']=='accepted' and not o['issues']}
    changed, receipts = list(rows), []
    equal = ('city','barangay','status','date_text','clock_text','time_role','depth_text','depth_scope',
        'access','historical','contradictory','road_section','place_evidence','status_evidence',
        'time_evidence','depth_evidence','access_evidence','section_evidence')
    for index, child in enumerate(rows):
        target = by_target[child.target_id]
        if child.target_id not in accepted or target['label'] != 'ROAD' or child.verdict != 'observed':
            continue
        owners = []
        for owner in rows:
            parent = by_target[owner.target_id]
            if owner.target_id == child.target_id or parent['label'] != 'ROAD' or owner.target_id not in accepted:
                continue
            pattern = re.escape(parent['text']) + r'\s+(?:at\s+the\s+)?(?:corner\s+of|corner|near|at)\s+' + re.escape(target['text'])
            fields = equal if not (partial_depth and child.depth_text is None) else tuple(
                k for k in equal if k not in {'depth_text','depth_scope','depth_evidence'})
            if (owner.verdict == 'observed' and owner.road_section and re.fullmatch(pattern,owner.road_section,re.I)
                    and all(getattr(owner,k) == getattr(child,k) for k in fields)):
                owners.append(owner)
        if len(owners) == 1:
            changed[index] = child.model_copy(update={'verdict':'unsupported'})
            receipts.append(dict(target_id=child.target_id, owner_target_id=owners[0].target_id,
                reason='crossing_road_context', original_row_sha256=sha(child.model_dump(mode='json')),
                effective_row_sha256=sha(changed[index].model_dump(mode='json'))))
    return changed, receipts


class TribuneReplayBatchPlan:
    def __init__(self, manifest: dict, *, cache_loader: Any = None) -> None:
        require(manifest.get('schema_version') in {VERSION, CONTEXT_VERSION}
            and manifest.get('generation_requests_allowed') == 0
            and manifest.get('batch_sizes') == [4,4,4,3]
            and len(manifest.get('bundle_sha256s',[])) == 4, 'tribune_replay_manifest_invalid')
        self.manifest = deepcopy(manifest)
        self.pin = sha(manifest)
        self.cache_loader = cache_loader

    @property
    def identity(self) -> str:
        require(sha(self.manifest) == self.pin,'tribune_replay_manifest_changed')
        return self.pin

    def batches(self, candidates: list[dict]) -> list[list[dict]]:
        self.identity
        require(sha(candidates) == self.manifest['targets_sha256'], 'tribune_replay_targets_changed')
        return [candidates[i:i+4] for i in range(0,len(candidates),4)]

    def adopt(self, index: int, payload: dict, context: dict, config: Any, journal: Any) -> tuple:
        self.identity
        require(index in range(4) and self.cache_loader is not None and journal is not None,
            'tribune_replay_cache_required')
        bundle = self.cache_loader(index)
        require(sha(bundle) == self.manifest['bundle_sha256s'][index], 'tribune_replay_bundle_changed')
        require(replay_bundle(bundle,sha(bundle),config=config)['status']=='evidence_references_passed',
            'tribune_replay_response_invalid')
        intent, semantic = bundle['intent'], bundle['semantic']
        require(intent['payload'] == payload and intent['context'] == context
            and semantic.get('request_identity') == intent['request_identity']
            and semantic.get('schema_version') == 'news-gemini-batch-semantic-v2'
            and semantic.get('stage') == 'row_outcomes_recorded', 'tribune_replay_request_changed')
        parsed, usage = validate_batch(payload,base64.b64decode(bundle['response']['body_base64']),config)
        document = json.loads(payload['contents'][0]['parts'][0]['text'])
        targets = document['targets']
        rows, normalizations = parsed.results, []
        current = semantic
        contextual = self.manifest['schema_version'] == CONTEXT_VERSION
        if contextual:
            rows, normalizations, current = source_context(rows, document, semantic)
        rows, crossing = crossing_context(rows, targets, current, partial_depth=contextual)
        normalizations += crossing
        key=sha(dict(request_sha256=sha(payload),context=context))
        journal.store.put(key+'/adoption.json',dict(schema_version=self.manifest['schema_version'],
            original_bundle_sha256=sha(bundle),original_response_unchanged=True,
            normalizations=normalizations,generation_requests=0,token_count_requests=0))
        return parsed.model_copy(update={'results':tuple(rows)}), usage


class ZeroProviderBudget:
    def reserve(self, *args: Any, **kwargs: Any) -> str:
        require(False, 'tribune_replay_provider_forbidden')

    def stop(self, reason: str) -> None:
        """Replay failures cannot mutate the already stopped paid ledger."""
        return None
