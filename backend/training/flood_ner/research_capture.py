"""Receipt-preserving research transport. No CLI or automatic collection route.

The v8 repair authorization is review-only and cannot create this session.
Live use requires a separate hash-bound grant and a verified preflight. Tests
inject MockTransport and temporary claim roots; production ingestion never uses it.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import threading
from typing import Any, Callable
from urllib.parse import urljoin, urlsplit

import httpx

from .annotation.schema import SourceCapture, text_hash
from .research_review import FileBinding, ReviewError, file_hash, require
from .sources import CaptureParser, MAX_CAPTURE_BYTES, known_datetime

USER_AGENT = 'LANES-NER-Research/1.0'
URL_PATTERN = re.compile(r'https?://[^\s<>"\x27,]+', re.I)
SAFE_HEADERS = frozenset({'date', 'content-type', 'content-length', 'retry-after', 'age', 'cache-control'})


def exclusive_bytes(path: Path, value: bytes) -> None:
    with path.open('xb') as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def exclusive_json(path: Path, value: Any) -> None:
    exclusive_bytes(path, (json.dumps(value, sort_keys=True, ensure_ascii=False) + '\n').encode('utf-8'))


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def read_journal(path: Path) -> list[dict[str, Any]]:
    rows, previous = [], '0' * 64
    for raw in path.read_bytes().splitlines(keepends=True):
        require(raw.endswith(b'\n'), 'interrupted journal append')
        row = json.loads(raw)
        payload = {k: v for k, v in row.items() if k != 'sha256'}
        require(row['sequence'] == len(rows) + 1 and row['previous_sha256'] == previous and
                row['sha256'] == hashlib.sha256(_canonical(payload)).hexdigest(), 'journal hash chain changed')
        rows.append(row)
        previous = row['sha256']
    return rows


def _binding(raw: dict[str, str]) -> FileBinding:
    binding = FileBinding(Path(raw['path']), raw['sha256'])
    binding.verify()
    return binding


def verify_preflight(authorization: FileBinding, preflight: FileBinding) -> tuple[dict[str, Any], dict[str, Any]]:
    authorization.verify()
    preflight.verify()
    grant = json.loads(authorization.path.read_text(encoding='utf-8'))
    proof = json.loads(preflight.path.read_text(encoding='utf-8'))
    require(grant.get('schema') == 'lanes-research-capture-grant-v1' and grant.get('network_allowed') is True,
            'separate network authorization required; review-only scope cannot dispatch')
    require(proof.get('schema') == 'lanes-research-capture-preflight-v1' and
            proof.get('authorization_sha256') == authorization.sha256, 'preflight authorization mismatch')
    evidence = {key: value for key, value in proof.items() if key != 'authorization_sha256'}
    require(grant.get('preflight_evidence_sha256') == hashlib.sha256(_canonical(evidence)).hexdigest(),
            'authorization does not bind this exact preflight evidence')
    # Legacy journal formats stay frozen: the scoped independent replay decides
    # semantics; dispatch must still verify the exact journal bytes it reviewed.
    predecessor = _binding(proof['predecessor_journal'])
    replay = _binding(proof['predecessor_replay'])
    replay_result = json.loads(replay.path.read_text(encoding='utf-8'))
    require(replay_result.get('journal_sha256') == predecessor.sha256 and
            replay_result.get('accounting_verified') is True and
            replay_result.get('original_receipts_verified') is True and
            replay_result.get('unquantified_exposure') is False and
            replay_result.get('interrupted_request') is False,
            'verified journal replay absent')
    require(proof.get('implementation_sha256') == file_hash(Path(__file__)), 'implementation not qualified')
    require(proof.get('accounting_verified') is True and proof.get('original_receipts_verified') is True and
            proof.get('unquantified_exposure') is False and proof.get('interrupted_request') is False,
            'predecessor accounting unresolved')
    tests = _binding(proof['test_results'])
    result = json.loads(tests.path.read_text(encoding='utf-8'))
    require(result.get('implementation_sha256') == proof['implementation_sha256'] and
            type(result.get('passed')) is int and result['passed'] > 0 and
            type(result.get('failed')) is int and result['failed'] == 0,
            'passing matching implementation tests required')
    _binding(result['test_source'])
    receipts = proof.get('original_receipts')
    require(isinstance(receipts, list) and bool(receipts), 'original receipt bindings absent')
    for receipt in receipts:
        _binding(receipt)
    require(replay_result.get('original_receipt_sha256') == [receipt['sha256'] for receipt in receipts],
            'replay receipt scope mismatch')
    identities = proof.get('raw_identities')
    require(isinstance(identities, list) and len(identities) == len(set(identities)) and
            all(isinstance(x, str) and bool(x) for x in identities), 'invalid identity union')
    for key in ('uncertain_slots', 'publisher_attempts'):
        require(type(proof.get(key)) is int and proof[key] >= 0, 'invalid inherited accounting')
    require(replay_result.get('raw_identity_union_sha256') == hashlib.sha256(_canonical(sorted(identities))).hexdigest()
            and all(type(replay_result.get(k)) is int and replay_result[k] == proof[k]
                    for k in ('uncertain_slots', 'publisher_attempts')), 'stale replay baseline')
    for key in ('url_ceiling', 'publisher_ceiling', 'task_request_limit', 'alias_reservation'):
        require(type(grant.get(key)) is int and grant[key] > 0, 'invalid grant limit')
    require(len(identities) + proof['uncertain_slots'] <= grant['url_ceiling'] and
            proof['publisher_attempts'] <= grant['publisher_ceiling'], 'exhausted inherited baseline')
    return grant, proof


def header_identities(url: str, headers: httpx.Headers) -> tuple[set[str], dict[str, list[str]], bool]:
    values = {name: headers.get_list(name) for name in ('location', 'content-location', 'link', 'refresh') if name in headers}
    found, malformed = set(), False
    for name, items in values.items():
        for value in items:
            absolute = URL_PATTERN.findall(value)
            found.update(absolute)
            if name in {'location', 'content-location'}:
                try:
                    resolved = urljoin(url, value)
                    parts = urlsplit(resolved)
                    bad = (not value.strip() or len(absolute) > 1 or bool(re.search(r'[\s,]', value.strip())) or
                           parts.scheme not in {'http', 'https'} or not parts.hostname or
                           bool(parts.username or parts.password))
                except ValueError:
                    # Retain raw values and regex identities even for malformed IPv6/authority syntax.
                    bad = True
                malformed = malformed or bad
                if not bad:
                    found.add(resolved)
    return found, values, malformed


def parse_capture(url: str, capture_id: str, raw: bytes, encoding: str) -> tuple[SourceCapture, set[str]]:
    from datetime import datetime, timezone
    parser = CaptureParser()
    parser.feed(raw.decode(encoding, errors='strict'))
    parser.close()
    metadata = parser.article_metadata()
    text, method = parser.text(), 'html-visible-article-main-v1'
    body = metadata.get('articleBody')
    if isinstance(body, str) and body.strip():
        if '<' in body and '>' in body:
            body_parser = CaptureParser()
            body_parser.feed('<article>' + body + '</article>')
            body_parser.close()
            text = body_parser.text()
        else:
            text = body
        method = 'jsonld-article-body-v1'
    require(bool(text.strip()), 'empty captured source')
    publication, basis = parser.publication_value()
    raw_hash = hashlib.sha256(raw).hexdigest()
    source = SourceCapture(
        source_id=capture_id, url=url, publisher='GMA News Online', title=parser.headline(), text=text,
        text_sha256=text_hash(text), raw_sha256=raw_hash, capture_version=raw_hash,
        published_at=known_datetime(publication), captured_at=datetime.now(timezone.utc), publication_basis=basis,
        article_group=url, event_group='pending-isolated-source-review', reuse_terms='Pending exact-source review',
        extraction_method=method,
    )
    aliases = {urljoin(url, x) for x in (parser.canonical_url, parser.meta.get('og:url')) if isinstance(x, str) and x}
    return source, aliases


class ResearchCaptureSession:
    """One exclusive, non-reopenable authorization; any failed request halts it."""

    def __init__(self, directory: Path, authorization: FileBinding, preflight: FileBinding, *,
                 claim_root: Path, _test_transport: httpx.BaseTransport | None = None) -> None:
        grant, proof = verify_preflight(authorization, preflight)
        require(not directory.exists(), 'new output directory required')
        require(grant.get('claim_root') == str(claim_root.resolve()), 'authorization claim location mismatch')
        claim_root.mkdir(parents=True, exist_ok=True)
        exclusive_json(claim_root / (authorization.sha256 + '.claim.json'), {'authorization_sha256': authorization.sha256})
        directory.mkdir()
        self.directory, self.authorization, self.preflight = directory, authorization, preflight
        self.grant, self.proof = grant, proof
        self.raw = set(proof['raw_identities'])
        self.pending = proof['uncertain_slots']
        self.attempts, self.dispatched = proof['publisher_attempts'], 0
        self.halted, self.closed = False, False
        self.visited: set[str] = set()
        self._lock = threading.Lock()
        self._transport = _test_transport
        self._journal_hash: str | None = None
        self._append('initialized', {'authorization_sha256': authorization.sha256, 'preflight_sha256': preflight.sha256})

    def _append(self, kind: str, data: dict[str, Any]) -> None:
        path = self.directory / 'journal.jsonl'
        if path.exists():
            require(file_hash(path) == self._journal_hash, 'journal changed by another writer')
            rows = read_journal(path)
        else:
            require(self._journal_hash is None, 'journal removed')
            rows = []
        event = {'sequence': len(rows) + 1, 'previous_sha256': rows[-1]['sha256'] if rows else '0' * 64,
                 'kind': kind, 'data': data}
        event['sha256'] = hashlib.sha256(_canonical(event)).hexdigest()
        with path.open('ab') as stream:
            stream.write(_canonical(event) + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        self._journal_hash = file_hash(path)

    def capture(self, url: str, capture_id: str, source_review: FileBinding, *,
                _parser: Callable[..., tuple[SourceCapture, set[str]]] | None = None) -> dict[str, Any]:
        require(self._lock.acquire(blocking=False), 'concurrent writer')
        try:
            require(_parser is None or self._transport is not None, 'parser injection is test-only')
            return self._capture(url, capture_id, source_review, _parser or parse_capture)
        finally:
            self._lock.release()

    def _capture(self, url: str, capture_id: str, source_review: FileBinding,
                 parser: Callable[..., tuple[SourceCapture, set[str]]]) -> dict[str, Any]:
        require(not self.halted and not self.closed, 'session stopped')
        verify_preflight(self.authorization, self.preflight)
        source_review.verify()
        review = json.loads(source_review.path.read_text(encoding='utf-8'))
        require(review.get('url') == url and review.get('eligible') is True and bool(review.get('evidence')),
                'exact-source use/history review absent')
        for binding in review['evidence']:
            _binding(binding)
        parts = urlsplit(url)
        require(parts.scheme == 'https' and parts.hostname in {'gmanetwork.com', 'www.gmanetwork.com'} and
                parts.path.startswith('/news/') and not parts.username and not parts.password and
                parts.port in {None, 443} and not parts.fragment, 'unsupported publisher identity')
        require(url in self.raw and url not in self.visited, 'unregistered identity or retry')
        require(bool(re.fullmatch(r'[A-Za-z0-9_-]{1,64}', capture_id)), 'invalid receipt identity')
        require(not any(self.directory.glob(capture_id + '.*')), 'receipt identity already used')
        reserve = self.grant['alias_reservation']
        require(len(self.raw) + self.pending + reserve <= self.grant['url_ceiling'] and
                self.attempts < self.grant['publisher_ceiling'] and self.dispatched < self.grant['task_request_limit'],
                'allowance exhausted')
        self._append('publisher_dispatched', {'url': url, 'capture_id': capture_id, 'alias_reservation': reserve})
        self.visited.add(url)
        self.attempts += 1
        self.dispatched += 1
        self.pending += reserve
        raw, source, failure = bytearray(), None, None
        received: set[str] = set()
        try:
            transport = self._transport or httpx.HTTPTransport(retries=0, verify=True, trust_env=False)
            with httpx.Client(transport=transport, timeout=30, follow_redirects=False, trust_env=False,
                              headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml'}) as client:
                with client.stream('GET', url, follow_redirects=False) as response:
                    aliases, identity_headers, malformed = header_identities(url, response.headers)
                    received.update(aliases)
                    exclusive_json(self.directory / f'{capture_id}.headers.json', {
                        'status': response.status_code, 'identity_headers': identity_headers,
                        'headers': {k: v for k, v in response.headers.items() if k.lower() in SAFE_HEADERS},
                        'malformed': malformed, 'before_body': True,
                    })
                    self._append('headers_received', {'capture_id': capture_id, 'aliases': sorted(received)})
                    require(not malformed, 'malformed identity header')
                    require(len(received - self.raw) <= reserve, 'header alias overrun')
                    require(response.status_code == 200, 'publisher HTTP failure or redirect')
                    require(response.headers.get('content-type', '').split(';')[0].strip().lower() in
                            {'text/html', 'application/xhtml+xml'}, 'unexpected response type')
                    for chunk in response.iter_bytes():
                        raw.extend(chunk)
                        require(len(raw) <= MAX_CAPTURE_BYTES, 'capture size limit')
                    source, aliases = parser(url, capture_id, bytes(raw), response.encoding or 'utf-8')
                    require(isinstance(source, SourceCapture) and source.url == url and source.source_id == capture_id,
                            'parser source identity mismatch')
                    require(source.raw_sha256 == hashlib.sha256(raw).hexdigest(), 'parser raw hash mismatch')
                    received.update(aliases)
                    require(len(received - self.raw) <= reserve, 'body alias overrun')
                    exclusive_json(self.directory / f'{capture_id}.source.json', source.model_dump(mode='json'))
        except Exception as exc:
            failure = type(exc).__name__
            self.halted = True
        finally:
            self.raw.update(received)
            try:
                exclusive_bytes(self.directory / f'{capture_id}.raw.html', bytes(raw))
                remaining = self.pending - reserve if failure is None else self.pending
                self._append('publisher_accounted', {'capture_id': capture_id, 'success': failure is None,
                    'failure_kind': failure, 'received_identities': sorted(received),
                    'raw_sha256': hashlib.sha256(raw).hexdigest(), 'bytes_received': len(raw),
                    'attempts': self.attempts, 'pending_slots': remaining, 'halted': self.halted})
                self.pending = remaining
            except Exception:
                self.halted = True
                raise
        return {'success': failure is None, 'failure_kind': failure, 'halted': self.halted}

    def close(self) -> None:
        require(self._lock.acquire(blocking=False), 'concurrent writer')
        try:
            require(not self.closed, 'session already closed')
            self._append('closed', {'halted': self.halted, 'attempts': self.attempts})
            self.closed = True
        finally:
            self._lock.release()
