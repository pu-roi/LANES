"""One-shot, six-known-lead publisher capture. Never used by ingestion or GDELT.

Private evidence and receipts stay in the ignored research artifacts directory.
The trusted curator supplies a hash-bound, source-only input envelope. This
module verifies its bindings; it does not adjudicate source/history eligibility.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx

from .annotation.schema import SourceCapture
from .sources import MAX_CAPTURE_BYTES, capture_source

URL_LIMIT = 306
ATTEMPT_LIMIT = 100
TASK_LIMIT = 6
USER_AGENT = 'LANES-NER-Research/1.0'
HEADER_ALLOWLIST = frozenset({'location', 'date', 'age', 'cache-control',
                             'content-type', 'retry-after', 'ratelimit', 'ratelimit-policy',
                             'ratelimit-limit', 'ratelimit-remaining', 'ratelimit-reset',
                             'x-ratelimit-limit', 'x-ratelimit-remaining', 'x-ratelimit-reset'})


class CaptureBoundaryError(RuntimeError):
    """A failed preflight/receipt never authorizes an automatic retry."""


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _write(path: Path, value: Any) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def _bound_file(binding: dict[str, str]) -> Path:
    path = Path(binding['path'])
    if not path.is_absolute() or not path.is_file() or file_hash(path) != binding['sha256']:
        raise CaptureBoundaryError('Stale or missing evidence binding')
    return path


def _lead_url(value: str) -> bool:
    parts = urlsplit(value)
    return (parts.scheme == 'https' and parts.hostname in {'www.gmanetwork.com', 'gmanetwork.com'}
            and parts.path.startswith('/news/') and not parts.username and not parts.password
            and parts.port in {None, 443} and not parts.fragment)


def verify_journal(path: Path) -> dict[str, Any]:
    """Verify a completed or interrupted append-only chain without modifying it."""
    previous = '0' * 64
    count = 0
    for line in path.read_bytes().splitlines(keepends=True):
        if not line.endswith(b'\n'):
            raise CaptureBoundaryError('Interrupted journal append')
        event = json.loads(line)
        digest = event.pop('sha256')
        raw = json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
        if (event['sequence'] != count + 1 or event['previous_sha256'] != previous
                or hashlib.sha256(raw).hexdigest() != digest):
            raise CaptureBoundaryError('Journal integrity failure')
        previous = digest
        count += 1
    if not count:
        raise CaptureBoundaryError('Empty journal')
    return {'events': count, 'last_event_sha256': previous, 'journal_sha256': file_hash(path)}


@dataclass(frozen=True)
class CaptureResult:
    lead_index: int
    status: str
    capture: SourceCapture | None = None
    error_kind: str | None = None


class SixLeadSession:
    """Own the client; one immutable authorization, one GET per eligible index.

    No resume or reopen operation exists. A permanent checkout-shared claim
    prevents relaunching the same six-lead authorization in another directory.
    Underscored transport/claim arguments exist only for offline unit fixtures.
    """

    @classmethod
    def create(cls, directory: Path, evidence: Path, *, expected_sha256: str,
               _test_transport: httpx.BaseTransport | None = None,
               _test_claim_root: Path | None = None) -> SixLeadSession:
        evidence = evidence.resolve()
        if file_hash(evidence) != expected_sha256:
            raise CaptureBoundaryError('Input envelope hash mismatch')
        data = json.loads(evidence.read_text(encoding='utf-8'))
        if data.get('schema') != 'lanes-six-known-leads-input-v1':
            raise CaptureBoundaryError('Unsupported input envelope')
        urls, leads = data['baseline_urls'], data['leads']
        if (not isinstance(urls, list) or any(not isinstance(u, str) or not u for u in urls)
                or len(urls) != 296 or len(set(urls)) != 296
                or not isinstance(leads, list) or len(leads) != TASK_LIMIT):
            raise CaptureBoundaryError('Stale identity or lead baseline')
        if (any(not isinstance(lead, dict) or type(lead.get('eligible')) is not bool
                or not isinstance(lead.get('url'), str) or lead['url'] not in urls
                or not _lead_url(lead['url']) for lead in leads)
                or len({lead['url'] for lead in leads}) != TASK_LIMIT):
            raise CaptureBoundaryError('Invalid, substituted or duplicate known lead')
        predecessor = _bound_file(data['predecessor_aggregate'])
        previous = json.loads(predecessor.read_text(encoding='utf-8'))
        if (previous.get('cumulative_actual_exposed_urls') != 296
                or previous.get('legacy_uncertain_url_slots') != 4
                or previous.get('cumulative_capture_attempts') != 74
                or previous.get('ready') is not False or previous.get('sealed') is not False):
            raise CaptureBoundaryError('Stale predecessor counters or boundary')
        if not data.get('bindings'):
            raise CaptureBoundaryError('Missing source-only evidence bindings')
        for binding in data['bindings']:
            _bound_file(binding)
        directory = directory.resolve()
        if directory.exists():
            raise CaptureBoundaryError('A new output directory is required')
        claim_root = _test_claim_root or Path(__file__).parent / 'artifacts/known-lead-capture-claims'
        claim_root.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(json.dumps([data['predecessor_aggregate']['sha256'],
                                        sorted(lead['url'] for lead in leads)]).encode()).hexdigest()
        try:
            _write(claim_root / (key + '.claim.json'), {'evidence_sha256': expected_sha256,
                                                      'prospective_url_limit': URL_LIMIT})
        except FileExistsError as exc:
            raise CaptureBoundaryError('Authorization already claimed; preserve it for review') from exc
        directory.mkdir()
        _write(directory / 'input-binding.json', data)
        self = cls.__new__(cls)
        self.directory, self.evidence, self.expected_hash, self.data = directory, evidence, expected_sha256, data
        self.seen = set(urls)
        self.leads = leads
        self.pending: dict[str, int] = {}
        self.used: set[int] = set()
        self.requests = 0
        self.halted = self.batch_held = self.closed = False
        self.sequence, self.last_hash = 0, '0' * 64
        self._lock = threading.Lock()
        self._active_url: str | None = None
        self._sent = False
        inner = _test_transport or httpx.HTTPTransport(verify=True, retries=0, trust_env=False)
        self._client = httpx.Client(transport=_PublisherTransport(self, inner), timeout=30,
                                   follow_redirects=False, trust_env=False,
                                   headers={'User-Agent': USER_AGENT, 'Accept': 'text/html'})
        self._append('initialize', {'input_sha256': expected_sha256, 'baseline_actual': 296,
                                   'legacy_uncertain_slots': 4, 'baseline_attempts': 74,
                                   'url_limit': URL_LIMIT, 'task_request_limit': TASK_LIMIT})
        return self

    def _append(self, kind: str, data: dict[str, Any]) -> None:
        event = {'sequence': self.sequence + 1, 'previous_sha256': self.last_hash,
                 'kind': kind, 'data': data}
        raw = json.dumps(event, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
        digest = hashlib.sha256(raw).hexdigest()
        with (self.directory / 'journal.jsonl').open('ab') as stream:
            stream.write(json.dumps({**event, 'sha256': digest}, sort_keys=True,
                                    ensure_ascii=False).encode() + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        self.sequence += 1
        self.last_hash = digest

    def status(self) -> dict[str, Any]:
        pending = 4 + sum(self.pending.values())
        return {'actual_url_identities': len(self.seen), 'legacy_uncertain_slots': 4,
                'new_uncertain_slots': sum(self.pending.values()), 'possible_exposure': len(self.seen) + pending,
                'remaining_url_slots': URL_LIMIT - len(self.seen) - pending,
                'task_requests': self.requests, 'cumulative_attempts': 74 + self.requests,
                'halted': self.halted, 'batch_held': self.batch_held}

    def capture(self, lead_index: int) -> CaptureResult:
        if not self._lock.acquire(blocking=False):
            raise CaptureBoundaryError('Concurrent capture writer rejected')
        try:
            if self.closed or self.halted:
                raise CaptureBoundaryError('Session closed or halted; no continuation')
            chain = verify_journal(self.directory / 'journal.jsonl')
            if chain['events'] != self.sequence or chain['last_event_sha256'] != self.last_hash:
                raise CaptureBoundaryError('Journal changed since the previous operation')
            if type(lead_index) is not int or not 0 <= lead_index < TASK_LIMIT or lead_index in self.used:
                raise CaptureBoundaryError('Unknown or already processed lead')
            if file_hash(self.evidence) != self.expected_hash:
                raise CaptureBoundaryError('Input changed after authorization')
            _bound_file(self.data['predecessor_aggregate'])
            for binding in self.data['bindings']:
                _bound_file(binding)
            self.used.add(lead_index)
            lead = self.leads[lead_index]
            if not lead['eligible']:
                self._append('skipped', {'lead_index': lead_index, 'reason_code': lead.get('reason_code', 'held')})
                return CaptureResult(lead_index, 'skipped_preflight_hold')
            self._active_url, self._sent = lead['url'], False
            try:
                source = capture_source(lead['url'], f'known-lead-{lead_index + 1}', 'GMA Network',
                                        'unknown', 'pending-isolated-source-review', self._client,
                                        self.directory / 'captures')
                result = CaptureResult(lead_index, 'captured_pending_review', source)
            except Exception as exc:
                result = CaptureResult(lead_index, 'held_capture_failure', error_kind=type(exc).__name__)
            finally:
                self._active_url = None
            self._append('outcome', {'lead_index': lead_index, 'status': result.status,
                                     'error_kind': result.error_kind, 'accounting': self.status()})
            return result
        finally:
            self._lock.release()

    def close(self) -> None:
        if not self.closed:
            self._client.close()
            self.closed = True

    def __enter__(self) -> SixLeadSession:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class _PublisherTransport(httpx.BaseTransport):
    def __init__(self, session: SixLeadSession, inner: httpx.BaseTransport) -> None:
        self.session, self.inner = session, inner

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        s = self.session
        if (s.closed or s.halted or s._sent or request.method != 'GET'
                or str(request.url) != s._active_url):
            raise CaptureBoundaryError('Follow-up or unauthorized request blocked before dispatch')
        if s.requests >= TASK_LIMIT or 74 + s.requests >= ATTEMPT_LIMIT or s.status()['remaining_url_slots'] < 1:
            raise CaptureBoundaryError('Request or possible-alias allowance exhausted')
        s._sent = True
        s.requests += 1
        key = f'request-{s.requests:02d}'
        s.pending[key] = 1
        s._append('reserved', {'request_id': key, 'url': str(request.url), 'alias_slots': 1})
        raw = bytearray()
        response: httpx.Response | None = None
        try:
            response = self.inner.handle_request(request)
            headers = {name: response.headers.get_list(name) for name in HEADER_ALLOWLIST if name in response.headers}
            locations = response.headers.get_list('location')
            _write(s.directory / (key + '.headers.json'), {
                'status_code': response.status_code,
                'headers_received_at_utc': datetime.now(timezone.utc).isoformat(),
                'headers': headers, 'raw_location_values': locations,
                'retry_after_present': 'retry-after' in headers})
            aliases = []
            malformed = False
            for value in locations:
                absolute_tokens = re.findall(r'https?://[^\s,<>]+', value, re.I)
                if any(c.isspace() for c in value):
                    candidates = value.split()
                    malformed = True
                elif len(absolute_tokens) > 1:
                    candidates = absolute_tokens
                    malformed = True
                else:
                    candidates = [value]
                for candidate in candidates:
                    try:
                        resolved = urljoin(str(request.url), candidate)
                        parts = urlsplit(resolved)
                        valid = (parts.scheme in {'http', 'https'} and bool(parts.hostname)
                                 and not parts.username and not parts.password)
                    except ValueError:
                        resolved, valid = candidate, False
                    malformed |= (not valid or not value.strip() or any(ord(c) < 32 for c in value))
                    aliases.append({'raw': value, 'resolved': resolved})
            observed = {alias['resolved'] for alias in aliases}
            new = observed - s.seen
            s.seen.update(observed)
            s.pending[key] = max(0, 1 - len(new))
            _write(s.directory / (key + '.aliases.json'), {'raw_aliases': aliases})
            s._append('headers', {'request_id': key, 'status_code': response.status_code,
                                   'observed_urls': sorted(observed), 'new_identity_count': len(new)})
            if len(observed) > 1 or malformed or s.status()['possible_exposure'] > URL_LIMIT:
                s.batch_held = s.halted = True
                raise CaptureBoundaryError('Redirect identity contract violation; entire batch held')
            for chunk in response.iter_bytes():
                raw.extend(chunk)
                if len(raw) > MAX_CAPTURE_BYTES:
                    raise CaptureBoundaryError('Body limit exceeded; partial evidence retained')
            with (s.directory / (key + '.body')).open('xb') as stream:
                stream.write(raw)
            s.pending.pop(key)
            s._append('body_complete', {'request_id': key, 'body_sha256': hashlib.sha256(raw).hexdigest(),
                                        'bytes': len(raw)})
            if response.status_code in {401, 403, 429}:
                s.halted = True
            returned = [(k, v) for k, v in response.headers.multi_items()
                        if k.lower() not in {'content-length', 'content-encoding', 'set-cookie'}]
            return httpx.Response(response.status_code, headers=returned, content=bytes(raw), request=request)
        except Exception as exc:
            s.halted = True
            partial = s.directory / (key + '.partial.body')
            with partial.open('xb') as stream:
                stream.write(raw)
            s._append('interrupted_or_rejected', {'request_id': key, 'error_kind': type(exc).__name__,
                                                  'partial_sha256': hashlib.sha256(raw).hexdigest(),
                                                  'accounting': s.status()})
            raise CaptureBoundaryError('Request failed; receipts/reservations retained') from exc
        finally:
            if response is not None:
                response.close()

    def close(self) -> None:
        self.inner.close()
