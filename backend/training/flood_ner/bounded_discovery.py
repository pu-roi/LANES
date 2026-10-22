"""Explicit, isolated research discovery; never imported by production ingestion.

GDELT ArtList's MAXRECORDS is a provider contract, not a local slice. A successful
one-record response precedes larger requests. A provider violation is retained
and halts the session; this client cannot make a dishonest provider compliant.
All journals/responses contain private acquisition evidence. Use ignored output.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx

ENDPOINT = 'https://api.gdeltproject.org/api/v2/doc/doc'
URL_LIMIT = 300
ATTEMPT_LIMIT = 100
MAX_RECORDS = 5
MAX_BYTES = 4 * 1024 * 1024
QUIET_SECONDS = 30
MAX_WAIT_SECONDS = 60
USER_AGENT = 'LANES-NER-Research/1.0'
RECEIPT_HEADERS = frozenset({
    'retry-after', 'date', 'age', 'cache-control', 'content-type',
    'ratelimit', 'ratelimit-policy', 'ratelimit-limit', 'ratelimit-remaining', 'ratelimit-reset',
    'x-ratelimit-limit', 'x-ratelimit-remaining', 'x-ratelimit-reset',
})
ARTICLE_FIELDS = frozenset({'url', 'url_mobile', 'title', 'seendate', 'socialimage',
                            'domain', 'language', 'sourcecountry'})
URL_PATTERN = re.compile(r'https?://[^\s<>"\x27\\]+', re.I)


class BoundaryError(RuntimeError):
    """Evidence/budget/provider boundary failed; collection must stop."""


class DeferredRequest(BoundaryError):
    """No request sent; the supported deadline is too far in the future."""

    def __init__(self, earliest_utc: str) -> None:
        self.earliest_utc = earliest_utc
        super().__init__('No request sent; earliest permitted time ' + earliest_utc)


def _encode(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise BoundaryError('Duplicate JSON member')
        result[key] = value
    return result


def _urls(value: Any) -> list[str]:
    found: list[str] = []
    def walk(item: Any) -> None:
        if isinstance(item, str):
            found.extend(match.group() for match in URL_PATTERN.finditer(item))
        elif isinstance(item, dict):
            for key, child in item.items():
                walk(key); walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
    walk(value)
    return list(dict.fromkeys(found))


def _public_url(value: str) -> str:
    if any(c.isspace() or ord(c)<32 for c in value):
        raise BoundaryError('URL contains whitespace/control characters')
    parts = urlsplit(value)
    if parts.scheme not in {'http', 'https'} or not parts.hostname or parts.username or parts.password:
        raise BoundaryError('Expected a public HTTP(S) URL without credentials')
    return value


def _utc(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError('Timezone required')
        return result.astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise BoundaryError('Invalid UTC retry deadline') from exc


def _retry_deadline(value: str | None, received_at: datetime) -> str | None:
    if value is None:
        return None
    try:
        value = value.strip()
        if value.isascii() and value.isdecimal():
            deadline = received_at + timedelta(seconds=int(value))
        else:
            deadline = parsedate_to_datetime(value)
            if deadline.tzinfo is None:
                raise ValueError('Timezone required')
        return deadline.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError) as exc:
        raise BoundaryError('Malformed Retry-After; manual reconciliation required') from exc


def _registry(directory: Path) -> Path:
    return next((p for p in directory.resolve().parents if p.name == 'artifacts'), directory.resolve().parent)


class _PacingGate:
    """Persistent completion-based cooldown; exclusive across research sessions.

    A crashed outbound request stays in flight. Neither a restart nor another
    session silently resets that uncertainty. This does not control other hosts
    or unrelated programs sharing an egress IP.
    """

    def __init__(self, directory: Path, clock: Any, sleep: Any) -> None:
        self.directory = directory
        self.journal = directory / '.gdelt-pacing.jsonl'
        self.lock = directory / '.gdelt-pacing.lock'
        self.clock, self.sleep = clock, sleep
        self.events: list[dict[str, Any]] = []

    def _append(self, kind: str, **data: Any) -> None:
        event = {'kind': kind, 'created_at': self.clock().isoformat(), 'data': data,
                 'previous_sha256': self.events[-1]['sha256'] if self.events else '0' * 64}
        event['sha256'] = hashlib.sha256(_encode(event)).hexdigest()
        with self.journal.open('ab') as stream:
            stream.write(_encode(event) + b'\n'); stream.flush(); os.fsync(stream.fileno())
        self.events.append(event)

    def __enter__(self) -> _PacingGate:
        try:
            self.handle = self.lock.open('xb')
        except FileExistsError as exc:
            raise BoundaryError('Shared discovery pacing gate is busy; no automatic retry') from exc
        try:
            if self.journal.exists():
                raw = self.journal.read_bytes()
                if not raw or not raw.endswith(b'\n'):
                    raise BoundaryError('Interrupted/empty pacing journal; preserve and reconcile')
                previous = '0' * 64
                for line in raw.splitlines():
                    event = json.loads(line, object_pairs_hook=_pairs)
                    digest = event.pop('sha256')
                    if event['previous_sha256'] != previous or hashlib.sha256(_encode(event)).hexdigest() != digest:
                        raise BoundaryError('Pacing journal hash mismatch')
                    if event['kind'] not in {'initialize', 'started', 'completed'}:
                        raise BoundaryError('Unknown pacing state')
                    event['sha256'] = digest
                    self.events.append(event); previous = digest
            else:
                self._append('initialize', next_allowed_utc=(self.clock() + timedelta(seconds=QUIET_SECONDS)).isoformat())
            last = self.events[-1]
            if self.clock() < _utc(last['created_at']):
                raise BoundaryError('Clock moved backwards; pacing needs reconciliation')
            if last['kind'] == 'started' or last['data'].get('timing_invalid'):
                raise BoundaryError('Unresolved interrupted request or retry timing')
            return self
        except BaseException:
            self.__exit__()
            raise

    def wait(self, provider_deadline: str | None = None) -> None:
        deadlines = [self.events[-1]['data']['next_allowed_utc']]
        if provider_deadline:
            deadlines.append(provider_deadline)
        earliest = max(_utc(value) for value in deadlines)
        delay = max(0.0, (earliest - self.clock()).total_seconds())
        if delay > MAX_WAIT_SECONDS:
            raise DeferredRequest(earliest.isoformat())
        # On Python 3.12/Windows, monotonic() can use the 15.625 ms
        # GetTickCount64 clock. A sub-millisecond comparison can falsely reject
        # an elapsed sleep. Use the high-resolution monotonic performance clock
        # and wait out any remaining wall-clock quantum, with a bounded total.
        started = time.perf_counter()
        while True:
            elapsed = time.perf_counter() - started
            remaining = max(0.0, (earliest - self.clock()).total_seconds())
            if self.sleep is time.sleep:
                remaining = max(remaining, delay - elapsed)
            if elapsed > MAX_WAIT_SECONDS or remaining > MAX_WAIT_SECONDS - elapsed:
                raise DeferredRequest(earliest.isoformat())
            if remaining <= 0:
                return
            self.sleep(max(.001, remaining))

    def start(self, request_id: str) -> None:
        self._append('started', request_id=request_id)

    def complete(self, provider_deadline: str | None, timing_invalid: bool) -> None:
        deadlines = [self.clock() + timedelta(seconds=QUIET_SECONDS)]
        if provider_deadline:
            deadlines.append(_utc(provider_deadline))
        self._append('completed', next_allowed_utc=max(deadlines).isoformat(), timing_invalid=timing_invalid)

    def __exit__(self, *args: Any) -> None:
        self.handle.close()
        self.lock.unlink()


@dataclass(frozen=True)
class DiscoveryBatch:
    request_id: str
    articles: tuple[dict[str, str], ...]
    observed_urls: tuple[str, ...]
    response_sha256: str


class Session:
    """Single-writer hash-chained budget journal. Opening never clears a hold."""

    @classmethod
    def create(cls, directory: Path, baseline_urls: list[str], *, baseline_attempts: int = 66) -> Session:
        if len(baseline_urls) != len(set(baseline_urls)):
            raise BoundaryError('Baseline raw URLs must be unique; aliases remain separate')
        for url in baseline_urls:
            _public_url(url)
        if not 0 <= len(baseline_urls) <= URL_LIMIT or not 0 <= baseline_attempts <= ATTEMPT_LIMIT:
            raise BoundaryError('Invalid inherited budget')
        directory.mkdir(parents=False, exist_ok=False)
        (directory / 'journal.jsonl').touch(exist_ok=False)
        session = cls(directory, _creating=True)
        session._append('initialize', {'baseline_urls': baseline_urls, 'baseline_attempts': baseline_attempts,
            'url_limit': URL_LIMIT, 'attempt_limit': ATTEMPT_LIMIT, 'historical_breach_preserved': True})
        return session

    @classmethod
    def continue_after_rate_limit(
        cls, directory: Path, predecessor: Path, *, expected_journal_sha256: str,
        expected_exposed_urls: int, expected_attempts: int, expected_reserved_slots: int,
        reconciliation_sha256: str, not_before_utc: str | None = None,
    ) -> Session:
        """Claim one explicit retry without editing/refunding the predecessor.

        The permanent sibling claim survives interruption. A failed initialization
        requires review rather than another claim; this never clears stale claims.
        No caller-provided URL baseline is accepted. Old undecided reservations
        remain charged separately from new pending requests.
        """
        directory, predecessor = Path(directory).resolve(), Path(predecessor).resolve()
        if directory.exists() or directory == predecessor or predecessor in directory.parents:
            raise BoundaryError('New continuation directory outside predecessor required')
        if not directory.parent.is_dir():
            raise BoundaryError('Continuation parent directory must exist')
        if not re.fullmatch(r'[0-9a-f]{64}', reconciliation_sha256):
            raise BoundaryError('Hash-bound curator reconciliation required')
        source = predecessor / 'journal.jsonl'
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != expected_journal_sha256:
            raise BoundaryError('Stale or altered predecessor journal')
        with cls(predecessor) as prior:
            if prior.events[0]['data'].get('predecessor'):
                raise BoundaryError('Only one controlled retry; no continuation chain')
            if not prior.halted or len(prior.pending) != 1 or prior.events[-1]['kind'] != 'request_failed':
                raise BoundaryError('Expected one reconciled failed rate-limit request')
            evidence = prior.events[-1]['data'].get('evidence') or {}
            if evidence.get('status_code') != 429 or evidence.get('incomplete'):
                raise BoundaryError('Complete HTTP 429 receipt required')
            prior._verify_receipts()
            state = prior.status()
            if (state['exposed_urls'], state['capture_attempts'], state['reserved_url_slots']) != (
                expected_exposed_urls, expected_attempts, expected_reserved_slots
            ) or not state['active_budget_pass']:
                raise BoundaryError('Stale predecessor budget expectations')
            deadlines = [d for d in [evidence.get('retry_not_before_utc'), not_before_utc] if d]
            if evidence.get('retry_after_parse_error'):
                raise BoundaryError('Unresolved provider retry deadline')
            deadline = max((_utc(d) for d in deadlines), default=None)
            if deadline and datetime.now(timezone.utc) < deadline:
                raise BoundaryError('Retry not permitted before ' + deadline.isoformat())
            initial = {
                'baseline_urls': sorted(prior.seen), 'baseline_attempts': prior.attempts,
                'url_limit': URL_LIMIT, 'attempt_limit': ATTEMPT_LIMIT,
                'historical_breach_preserved': True,
                'inherited_reserved_slots': state['reserved_url_slots'],
                'inherited_pending_requests': state['pending_requests'],
                'predecessor': {'directory': str(predecessor), 'journal_sha256': digest,
                                'reconciliation_sha256': reconciliation_sha256},
                'retry_not_before_utc': deadline.isoformat() if deadline else None,
            }
            if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                raise BoundaryError('Predecessor changed while reconciling')
            # Same predecessor always maps to one persistent claim, across outputs.
            # Keep the claim outside preserved curator packages (whose journal
            # normally lives in an acquisition/ subdirectory).
            registry = _registry(predecessor)
            claim = registry / ('.controlled-retry-' + digest + '.claim.json')
            try:
                with claim.open('xb') as stream:
                    stream.write(_encode({'journal_sha256': digest, 'destination': str(directory),
                                          'reconciliation_sha256': reconciliation_sha256}))
                    stream.flush(); os.fsync(stream.fileno())
            except FileExistsError as exc:
                raise BoundaryError('Predecessor continuation already claimed; preserve claim') from exc
        directory.mkdir(exist_ok=False)
        (directory / 'journal.jsonl').touch(exist_ok=False)
        session = cls(directory, _creating=True)
        session._append('initialize', initial)
        return session

    def _verify_receipts(self) -> None:
        for event in self.events:
            receipt = event['data'].get('evidence') or {}
            for key, digest_key in [('file', 'sha256'), ('headers_file', 'headers_sha256')]:
                if not receipt.get(key):
                    continue
                name = receipt[key]
                if Path(name).name != name or '/' in name or '\\' in name:
                    raise BoundaryError('Unsafe predecessor receipt path')
                raw = (self.directory / name).read_bytes()
                if hashlib.sha256(raw).hexdigest() != receipt[digest_key]:
                    raise BoundaryError('Predecessor receipt hash mismatch')
                if key == 'file' and len(raw) != receipt['bytes']:
                    raise BoundaryError('Predecessor receipt size mismatch')

    @classmethod
    def final_diagnostic(
        cls, directory: Path, predecessor: Path, *, expected_journal_sha256: str,
        reconciliation_sha256: str,
    ) -> Session:
        """Separate explicit final authorization, not another ordinary retry chain.

        Import the exact current 204/4/66 checkpoint. One persistent claim covers
        every launch/output of this authorization; it never enables collection.
        """
        directory, predecessor = Path(directory).resolve(), Path(predecessor).resolve()
        if directory.exists() or directory == predecessor or predecessor in directory.parents or not directory.parent.is_dir():
            raise BoundaryError('New diagnostic output outside predecessor required')
        if not re.fullmatch(r'[0-9a-f]{64}', reconciliation_sha256):
            raise BoundaryError('Hash-bound diagnostic reconciliation required')
        source = predecessor / 'journal.jsonl'
        if hashlib.sha256(source.read_bytes()).hexdigest() != expected_journal_sha256:
            raise BoundaryError('Stale diagnostic predecessor')
        with cls(predecessor) as prior:
            prior._verify_receipts()
            if prior.events[0]['data'].get('final_diagnostic') or not prior.halted:
                raise BoundaryError('Not an eligible pre-diagnostic checkpoint')
            state = prior.status()
            if (state['exposed_urls'], state['reserved_url_slots'], state['capture_attempts']) != (204, 4, 66):
                raise BoundaryError('Final diagnostic requires the exact 204/4/66 checkpoint')
            evidence = prior.events[-1]['data'].get('evidence') or {}
            if prior.events[-1]['kind'] != 'request_failed' or evidence.get('status_code') != 429 or evidence.get('incomplete'):
                raise BoundaryError('Complete latest HTTP 429 receipt required')
            if evidence.get('retry_after_parse_error'):
                raise BoundaryError('Unresolved predecessor retry timing')
            deadline = evidence.get('retry_not_before_utc')
            if deadline and (_utc(deadline) - datetime.now(timezone.utc)).total_seconds() > MAX_WAIT_SECONDS:
                raise DeferredRequest(deadline)
            initial = {'baseline_urls': sorted(prior.seen), 'baseline_attempts': prior.attempts,
                       'url_limit': URL_LIMIT, 'attempt_limit': ATTEMPT_LIMIT,
                       'historical_breach_preserved': True,
                       'inherited_reserved_slots': 4, 'inherited_pending_requests': state['pending_requests'],
                       'final_diagnostic': True, 'retry_not_before_utc': deadline,
                       'predecessor': {'directory': str(predecessor), 'journal_sha256': expected_journal_sha256,
                                       'reconciliation_sha256': reconciliation_sha256}}
            if hashlib.sha256(source.read_bytes()).hexdigest() != expected_journal_sha256:
                raise BoundaryError('Diagnostic predecessor changed')
            claim = _registry(predecessor) / '.gdelt-final-diagnostic-20261017-v1.claim.json'
            try:
                with claim.open('xb') as stream:
                    stream.write(_encode({'authorization': 'one-final-diagnostic-20261017-v1',
                                          'predecessor': initial['predecessor'], 'destination': str(directory)}))
                    stream.flush(); os.fsync(stream.fileno())
            except FileExistsError as exc:
                raise BoundaryError('Final diagnostic already claimed; preserve claim') from exc
        directory.mkdir(exist_ok=False)
        (directory / 'journal.jsonl').touch(exist_ok=False)
        session = cls(directory, _creating=True)
        session._append('initialize', initial)
        session._final_live_grant = True
        return session

    def __init__(self, directory: Path, *, _creating: bool = False) -> None:
        self.directory = Path(directory)
        self.journal = self.directory / 'journal.jsonl'
        self.lock = self.directory / 'writer.lock'
        self._closed = False
        self._owner = threading.get_ident()
        self._nonce = uuid.uuid4().hex
        self._clock = lambda: datetime.now(timezone.utc)
        self._sleep = time.sleep
        self._test_transport: httpx.MockTransport | None = None
        # Only the newly authorized factory result may begin the one operation.
        # Reopening an initialize-only diagnostic must not resurrect permission
        # after a preflight failure or an interrupted process.
        self._final_live_grant = False
        if not self.journal.is_file():
            raise BoundaryError('Existing journal required; use Session.create for new output')
        try:
            with self.lock.open('x', encoding='ascii') as stream:
                stream.write(self._nonce); stream.flush(); os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise BoundaryError('Writer lock exists; never remove a stale lock automatically') from exc
        try:
            self._load(allow_empty=_creating)
        except BaseException:
            self.close()
            raise

    def __enter__(self) -> Session:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        if not self._closed:
            if self.lock.exists() and self.lock.read_text(encoding='ascii') == self._nonce:
                self.lock.unlink()
            self._closed = True

    def _load(self, *, allow_empty: bool = False) -> None:
        raw = self.journal.read_bytes()
        if raw and not raw.endswith(b'\n'):
            raise BoundaryError('Interrupted journal append; preserve evidence and stop')
        self.events: list[dict[str, Any]] = []
        previous = '0' * 64
        for index, line in enumerate(raw.splitlines()):
            event = json.loads(line.decode('utf-8'), object_pairs_hook=_pairs)
            digest = event.pop('sha256')
            if event['index'] != index or event['previous_sha256'] != previous or hashlib.sha256(_encode(event)).hexdigest() != digest:
                raise BoundaryError('Journal hash chain mismatch')
            event['sha256'] = digest
            self.events.append(event); previous = digest
        if not self.events:
            if not allow_empty:raise BoundaryError('Empty existing journal cannot reset inherited history')
        else:
            if self.events[0]['kind']!='initialize' or sum(e['kind']=='initialize' for e in self.events)!=1:
                raise BoundaryError('Journal requires exactly one initial baseline')
            initial=self.events[0]['data']
            if initial['url_limit']!=URL_LIMIT or initial['attempt_limit']!=ATTEMPT_LIMIT:
                raise BoundaryError('Journal ceilings differ from authorized constants')
            if len(initial['baseline_urls'])!=len(set(initial['baseline_urls'])) or not 0<=initial['baseline_attempts']<=ATTEMPT_LIMIT:
                raise BoundaryError('Invalid journal baseline')
            reserved = initial.get('inherited_reserved_slots', 0)
            inherited_count = initial.get('inherited_pending_requests', 0)
            if type(reserved) is not int or reserved < 0 or type(inherited_count) is not int or inherited_count < 0:
                raise BoundaryError('Invalid inherited reservation')
            if len(initial['baseline_urls']) + reserved > URL_LIMIT:
                raise BoundaryError('Inherited exposure exceeds ceiling')
            if (reserved or inherited_count) and not initial.get('predecessor'):
                raise BoundaryError('Inherited reservations require a predecessor')
            if any(e['kind'] not in {'initialize','discovery_reserved','capture_reserved','discovery_completed','capture_completed','request_failed'} for e in self.events):
                raise BoundaryError('Unknown journal event')
        self._replay()

    def _replay(self) -> None:
        self.seen: set[str] = set()
        self.attempts = 0
        self.pending: dict[str, int] = {}
        self.verified = False
        self.halted = False
        self.inherited_reserved = 0
        self.inherited_pending = 0
        self.retry_not_before = None
        self.final_only = False
        self.discovery_requests = 0
        for event in self.events:
            kind, data = event['kind'], event['data']
            if kind == 'initialize':
                self.seen.update(data['baseline_urls']); self.attempts = data['baseline_attempts']
                self.inherited_reserved = data.get('inherited_reserved_slots', 0)
                self.inherited_pending = data.get('inherited_pending_requests', 0)
                self.retry_not_before = data.get('retry_not_before_utc')
                self.final_only = data.get('final_diagnostic', False)
            elif kind in {'discovery_reserved', 'capture_reserved'}:
                self.pending[data['request_id']] = data['slots']
                if kind == 'discovery_reserved':
                    self.discovery_requests += 1
                if kind == 'capture_reserved':
                    self.seen.add(data['url']); self.attempts += 1
            elif kind in {'discovery_completed', 'capture_completed'}:
                self.seen.update(data['observed_urls']); self.pending.pop(data['request_id'])
                self.verified = self.verified or data.get('probe_verified', False)
            elif kind == 'request_failed':
                added = len(set(data['observed_urls']) - self.seen)
                self.seen.update(data['observed_urls'])
                self.pending[data['request_id']] = max(0, self.pending[data['request_id']] - added)
                self.halted = True

    def _append(self, kind: str, data: dict[str, Any]) -> None:
        if self._closed or threading.get_ident() != self._owner:
            raise BoundaryError('Session is closed or accessed by a different writer')
        event = {'index': len(self.events), 'previous_sha256': self.events[-1]['sha256'] if self.events else '0' * 64,
            'created_at': datetime.now(timezone.utc).isoformat(), 'kind': kind, 'data': data}
        event['sha256'] = hashlib.sha256(_encode(event)).hexdigest()
        with self.journal.open('ab') as stream:
            stream.write(_encode(event) + b'\n'); stream.flush(); os.fsync(stream.fileno())
        self.events.append(event); self._replay()

    def status(self) -> dict[str, Any]:
        reserved = sum(self.pending.values()) + self.inherited_reserved
        return {'exposed_urls': len(self.seen), 'capture_attempts': self.attempts,
            'reserved_url_slots': reserved, 'remaining_url_slots': URL_LIMIT-len(self.seen)-reserved,
            'remaining_capture_attempts': ATTEMPT_LIMIT-self.attempts,
            'active_budget_pass': len(self.seen)+reserved <= URL_LIMIT and self.attempts <= ATTEMPT_LIMIT,
            'pending_requests': len(self.pending) + self.inherited_pending,
            'inherited_reserved_url_slots': self.inherited_reserved,
            'final_diagnostic': self.final_only, 'discovery_requests': self.discovery_requests,
            'halted': self.halted, 'provider_verified': self.verified}

    def _ready(self) -> None:
        if self._closed or self.halted or self.pending:
            raise BoundaryError('Closed, halted or unreconciled pending session')
        if self.final_only and (self.discovery_requests or not self._final_live_grant):
            raise BoundaryError('Final diagnostic allowance already consumed')

    def _save(self, request_id: str, raw: bytes) -> tuple[str, str]:
        path = self.directory / (request_id + '.response.bin')
        with path.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        return path.name, hashlib.sha256(raw).hexdigest()

    def _failure(self, request_id: str, reason: str, observed: list[str], evidence: dict[str, Any] | None = None) -> None:
        self._append('request_failed', {'request_id': request_id, 'reason': reason,
            'observed_urls': observed, 'evidence': evidence})

    def _discovery_client(self) -> httpx.Client:
        if self._test_transport is not None and not isinstance(self._test_transport, httpx.MockTransport):
            raise BoundaryError('Only MockTransport may replace the owned transport in tests')
        return httpx.Client(
            transport=self._test_transport or httpx.HTTPTransport(retries=0, verify=True),
            headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'},
            timeout=30, follow_redirects=False,
        )

    def _header_evidence(self, response: httpx.Response, request_id: str) -> dict[str, Any]:
        received = self._clock()
        allowed = {name: response.headers.get_list(name) for name in RECEIPT_HEADERS if name in response.headers}
        values = allowed.get('retry-after', [])
        evidence: dict[str, Any] = {'status_code': response.status_code,
            'headers_received_at_utc': received.isoformat(), 'retry_after_present': bool(values),
            'retry_after_values': values, 'retry_not_before_utc': None,
            'observed_header_urls': _urls(allowed)}
        if values:
            try:
                if len(set(value.strip() for value in values)) != 1:
                    raise BoundaryError('Contradictory Retry-After values')
                evidence['retry_not_before_utc'] = _retry_deadline(values[0], received)
                evidence['retry_after'] = values[0]
            except BoundaryError:
                evidence['retry_after_parse_error'] = True
        receipt = {**evidence, 'response_headers': allowed,
                   'request_headers': {'user-agent': USER_AGENT, 'accept': 'application/json'}}
        path = self.directory / (request_id + '.headers.json')
        raw = _encode(receipt)
        with path.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        evidence.update(headers_file=path.name, headers_sha256=hashlib.sha256(raw).hexdigest())
        return evidence

    def discover(self, *, query: str, start: str, end: str, max_records: int = 1) -> DiscoveryBatch:
        self._ready()
        if self.final_only:
            self._final_live_grant = False
        if type(max_records) is not int or not 1 <= max_records <= MAX_RECORDS:
            raise BoundaryError('Request one to five records only')
        if self.final_only and max_records != 1:
            raise BoundaryError('Final diagnostic permits one record only')
        if not self.verified and max_records != 1:
            raise BoundaryError('A nonempty successful one-record probe is required')
        # Fixed initial discovery subset. Publisher date evidence is checked separately.
        try:
            first=datetime.strptime(start,'%Y%m%d%H%M%S'); last=datetime.strptime(end,'%Y%m%d%H%M%S')
        except ValueError as exc:
            raise BoundaryError('Invalid query timestamps') from exc
        if not datetime(2026,8,1) <= first < last <= datetime(2026,10,14,15,59,59):
            raise BoundaryError('Discovery outside the authorized initial subset')
        if not query.strip() or not re.search(r'\bdomain(?:is)?:gmanetwork\.com(?:\s|$)',query):
            raise BoundaryError('Initial discovery requires GMA domain restriction')
        slots = 3 * max_records
        if slots > self.status()['remaining_url_slots']:
            raise BoundaryError('Insufficient allowance for worst-case response exposure')
        params = {'query': query, 'mode': 'artlist', 'format': 'json', 'maxrecords': str(max_records),
            'startdatetime': start, 'enddatetime': end, 'sort': 'hybridrel'}
        with _PacingGate(_registry(self.directory), self._clock, self._sleep) as gate:
            gate.wait(self.retry_not_before)
            with self._discovery_client() as client:
                return self._perform_discovery(client, gate, params, slots, max_records)

    def _perform_discovery(self, client: httpx.Client, gate: _PacingGate,
                           params: dict[str, str], slots: int, max_records: int) -> DiscoveryBatch:
        request_id = uuid.uuid4().hex
        self._append('discovery_reserved', {'request_id':request_id,'slots':slots,'max_records':max_records,'parameters':params})
        gate.start(request_id)
        raw=bytearray(); observed: list[str]=[]; evidence: dict[str,Any] | None=None
        try:
            with client.stream('GET',ENDPOINT,params=params,follow_redirects=False) as response:
                # Persist safe headers/status before streaming any body bytes.
                evidence = self._header_evidence(response, request_id)
                header_urls = evidence['observed_header_urls'] + [
                    urljoin(str(response.url),u) for u in response.headers.get_list('location')]
                observed = list(header_urls)
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw)>MAX_BYTES:
                        raise BoundaryError('Response exceeds byte limit; no truncation admitted')
                filename,digest=self._save(request_id,bytes(raw))
                evidence.update(file=filename, sha256=digest, bytes=len(raw),
                                completed_at_utc=self._clock().isoformat())
                observed += _urls(bytes(raw).decode('utf-8',errors='replace'))
                if evidence.get('retry_after_parse_error'):
                    raise BoundaryError('Malformed or contradictory Retry-After; stop for reconciliation')
                # Preserve evidence/URL debit even for malformed responses and redirects.
                if response.status_code!=200:
                    raise BoundaryError('Discovery HTTP status/redirect rejected; no automatic retry')
                if 'json' not in response.headers.get('content-type','').lower():
                    raise BoundaryError('Expected JSON content type')
                payload=json.loads(bytes(raw).decode('utf-8'),object_pairs_hook=_pairs)
                observed=header_urls + _urls(payload)
                if not isinstance(payload,dict) or set(payload)!={'articles'} or not isinstance(payload['articles'],list):
                    raise BoundaryError('Unexpected discovery envelope')
                articles=payload['articles']
                if len(articles)>max_records:
                    raise BoundaryError('Provider ignored requested record ceiling')
                for article in articles:
                    if not isinstance(article,dict) or set(article)-ARTICLE_FIELDS or not all(isinstance(v,str) for v in article.values()):
                        raise BoundaryError('Unexpected discovery article fields/types')
                    _public_url(article.get('url',''))
                    for field in ['url_mobile','socialimage']:
                        if article.get(field):_public_url(article[field])
                if len(set(observed)-self.seen)>slots:
                    raise BoundaryError('Provider response exceeds reserved URL exposure')
                self._append('discovery_completed', {'request_id':request_id,'observed_urls':observed,
                    'record_count':len(articles),'probe_verified':max_records==1 and len(articles)==1,'evidence':evidence})
                gate.complete(evidence.get('retry_not_before_utc'), False)
                return DiscoveryBatch(request_id,tuple(articles),tuple(observed),digest)
        except Exception as exc:
            if not evidence or not evidence.get('file'):
                filename,digest=self._save(request_id,bytes(raw))
                evidence = {**(evidence or {}), 'file':filename, 'sha256':digest,
                            'bytes':len(raw), 'incomplete':True, 'completed_at_utc':self._clock().isoformat()}
                observed += _urls(bytes(raw).decode('utf-8',errors='replace'))
            self._failure(request_id,type(exc).__name__+': '+str(exc)[:250],list(dict.fromkeys(observed)),evidence)
            gate.complete(evidence.get('retry_not_before_utc'), evidence.get('retry_after_parse_error', False))
            raise BoundaryError('Discovery stopped; inspect the private journal/response evidence') from exc

    def article_client(self, transport: httpx.BaseTransport | None = None) -> httpx.Client:
        if self.final_only:
            raise BoundaryError('Final diagnostic never permits publisher requests')
        return httpx.Client(transport=_ArticleTransport(self,transport or httpx.HTTPTransport(retries=0)),
                            follow_redirects=False,timeout=30)


class _ArticleTransport(httpx.BaseTransport):
    """Accounts each article GET, including capture_source's redirect loop."""
    def __init__(self, session: Session, transport: httpx.BaseTransport) -> None:
        self.session=session;self.transport=transport

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        session=self.session;session._ready()
        url=_public_url(str(request.url));parts=urlsplit(url)
        if request.method!='GET' or parts.hostname not in {'gmanetwork.com','www.gmanetwork.com'} or not parts.path.startswith('/news/'):
            raise BoundaryError('Article request outside authorized GMA news route')
        if url not in session.seen:
            raise BoundaryError('Register through discovery/direct evidence before article capture')
        if session.attempts>=ATTEMPT_LIMIT or session.status()['remaining_url_slots']<1:
            raise BoundaryError('Article attempt/possible redirect allowance exhausted')
        request_id=uuid.uuid4().hex
        session._append('capture_reserved',{'request_id':request_id,'url':url,'slots':1})
        raw=bytearray(); evidence: dict[str,Any] | None=None; observed: list[str]=[]
        try:
            response=self.transport.handle_request(request)
            try:
                # Mirror capture_source's decoded HTTP body; prevent double decoding
                # when returning the evidence through the ordinary HTTPX client.
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw)>MAX_BYTES:raise BoundaryError('Article response exceeds byte limit')
                filename,digest=session._save(request_id,bytes(raw))
                evidence={'file':filename,'sha256':digest,'status_code':response.status_code,'bytes':len(raw)}
                observed=list(dict.fromkeys(urljoin(url,v) for v in response.headers.get_list('location')))
                if len(set(observed)-session.seen)>1:
                    raise BoundaryError('Unexpected multiple redirect URL exposures')
                session._append('capture_completed',{'request_id':request_id,'observed_urls':observed,'evidence':evidence})
                headers=[(k,v) for k,v in response.headers.multi_items() if k.lower() not in {'content-encoding','content-length'}]
                return httpx.Response(response.status_code,headers=headers,content=bytes(raw),request=request)
            finally:
                response.close()
        except Exception as exc:
            if evidence is None and raw:
                filename,digest=session._save(request_id,bytes(raw));evidence={'file':filename,'sha256':digest,'incomplete':True}
            session._failure(request_id,type(exc).__name__,observed,evidence)
            raise BoundaryError('Article request failed; attempt retained and session halted') from exc

    def close(self) -> None:
        self.transport.close()
