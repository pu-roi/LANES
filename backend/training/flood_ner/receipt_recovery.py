"""Offline, scoped extraction of original search receipts from LANES JSONL logs.

This module never executes logged code. Only direct search calls and a small,
literal-only search wrapper are admitted. Mixed command wrappers stay held:
copying their output could disclose annotations or unrelated conversations.
Extracted pairs establish recorded provenance, not acquisition completeness.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any


class RecoveryError(ValueError):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise RecoveryError(message)


@dataclass(frozen=True)
class SessionScope:
    path: Path
    sha256: str
    session_id: str
    checkout: str
    call_ids: tuple[str, ...]


def _literal(source: str) -> Any:
    """Parse JSON values with optional JS identifier keys, without eval."""
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[A-Za-z_$][\w$]*|-?\d+(?:\.\d+)?|[^\s]', source)
    index = 0

    def value() -> Any:
        nonlocal index
        _require(index < len(tokens), 'incomplete literal')
        token = tokens[index]
        index += 1
        if token == '{':
            result: dict[str, Any] = {}
            if index < len(tokens) and tokens[index] == '}':
                index += 1
                return result
            while True:
                _require(index < len(tokens), 'incomplete object')
                key = tokens[index]
                index += 1
                if key.startswith('"'):
                    key = json.loads(key)
                else:
                    _require(bool(re.fullmatch(r'[A-Za-z_$][\w$]*', key)), 'nonliteral key')
                _require(key not in result and index < len(tokens) and tokens[index] == ':',
                         'duplicate key or missing colon')
                index += 1
                result[key] = value()
                _require(index < len(tokens), 'incomplete object')
                sep = tokens[index]
                index += 1
                if sep == '}':
                    return result
                _require(sep == ',', 'nonliteral object')
        if token == '[':
            items: list[Any] = []
            if index < len(tokens) and tokens[index] == ']':
                index += 1
                return items
            while True:
                items.append(value())
                _require(index < len(tokens), 'incomplete array')
                sep = tokens[index]
                index += 1
                if sep == ']':
                    return items
                _require(sep == ',', 'nonliteral array')
        _require(token.startswith('"') or token in ('true', 'false', 'null') or
                 bool(re.fullmatch(r'-?\d+(?:\.\d+)?', token)), 'expression is not a literal')
        return json.loads(token)

    parsed = value()
    _require(index == len(tokens), 'trailing expression')
    return parsed


def search_request(payload: dict[str, Any]) -> dict[str, Any]:
    kind, name = payload.get('type'), payload.get('name')
    if kind == 'function_call' and name == 'web__run':
        request = json.loads(payload['arguments'])
    else:
        _require(kind == 'custom_tool_call' and name == 'exec', 'unapproved tool')
        source = payload.get('input', '')
        # No helper imports, model output, shell commands, mutation, or arbitrary JS.
        match = re.fullmatch(
            r'\s*(?:const|let)\s+(\w+)\s*=\s*await\s+tools\.web__run\((.*?)\);\s*'
            r'(?:store\("(?:\\.|[^"\\])*",\s*\1\);\s*)?text\(\1\);\s*', source, re.S)
        direct = re.fullmatch(r'\s*text\(await tools\.web__run\((.*)\)\);\s*', source, re.S)
        _require(match is not None or direct is not None, 'mixed or unsupported wrapper')
        request = _literal(match.group(2) if match else direct.group(1))
    _require(isinstance(request, dict) and set(request) <= {'search_query', 'response_length'},
             'search-only request required')
    queries = request.get('search_query')
    _require(isinstance(queries, list) and 1 <= len(queries) <= 4, 'missing search queries')
    for query in queries:
        _require(isinstance(query, dict) and set(query) <= {'q', 'domains', 'recency'} and
                 isinstance(query.get('q'), str) and bool(query['q']), 'unsupported search fields')
        _require(not re.search(r'(?i)(?:authorization|api[_-]?key|access[_-]?token|password)\s*[:=]', query['q']),
                 'possible secret in query')
    return request


def _response(payload: dict[str, Any], wrapped: bool) -> Any:
    output = payload.get('output')
    if not wrapped:
        _require(isinstance(output, (str, list, dict)), 'missing result')
        return output
    _require(isinstance(output, list) and bool(output), 'unsupported wrapper output')
    blocks = []
    for item in output:
        _require(isinstance(item, dict) and item.get('type') == 'text' and
                 isinstance(item.get('text'), str), 'nontext output')
        text = item['text']
        if re.fullmatch(r'Script completed\s+Wall time: [\d.]+ seconds\s*', text):
            continue
        blocks.append(item)
    _require(len(blocks) == 1, 'ambiguous or partial output blocks')
    return blocks


def recover(scope: SessionScope, output: Path) -> dict[str, Any]:
    """Write only explicitly scoped pairs, exclusively; never change input logs.

    Failure retains a new incomplete output directory for inspection. A missing,
    duplicate or interrupted record cannot become a verified receipt.
    """
    raw = scope.path.read_bytes()
    _require(digest(raw) == scope.sha256, 'session hash changed')
    _require(bool(scope.call_ids) and len(set(scope.call_ids)) == len(scope.call_ids), 'invalid call scope')
    _require(not output.exists(), 'new destination required')
    rows = []
    for number, line in enumerate(raw.splitlines(keepends=True), 1):
        _require(line.endswith(b'\n'), 'interrupted JSONL record')
        try:
            record = json.loads(line)
        except (ValueError, UnicodeError) as exc:
            raise RecoveryError('malformed JSONL record') from exc
        _require(isinstance(record, dict), 'invalid record')
        rows.append((number, line, record))
    metadata = [r['payload'] for _, _, r in rows if r.get('type') == 'session_meta']
    normalize = lambda value: str(value).replace('\\', '/').rstrip('/').casefold()
    _require(len(metadata) == 1 and metadata[0].get('id') == scope.session_id and
             normalize(metadata[0].get('cwd')) == normalize(scope.checkout), 'wrong session or checkout')
    output.mkdir()
    dispositions = []
    for index, call_id in enumerate(scope.call_ids, 1):
        matching = [(n, line, r) for n, line, r in rows if r.get('type') == 'response_item' and
                    isinstance(r.get('payload'), dict) and r['payload'].get('call_id') == call_id]
        calls = [x for x in matching if x[2]['payload'].get('type') in ('function_call', 'custom_tool_call')]
        results = [x for x in matching if x[2]['payload'].get('type') in ('function_call_output', 'custom_tool_call_output')]
        row: dict[str, Any] = {'call_id': call_id, 'disposition': 'hold'}
        if len(calls) != 1 or len(results) != 1:
            row['reason'] = 'missing_or_duplicate_pair'
        elif calls[0][0] >= results[0][0]:
            row['reason'] = 'result_precedes_request'
        else:
            try:
                call, result = calls[0][2]['payload'], results[0][2]['payload']
                request = search_request(call)
                expected_type = ('custom_tool_call_output' if call['type'] == 'custom_tool_call'
                                 else 'function_call_output')
                _require(result['type'] == expected_type, 'tool result type mismatch')
                _response(result, call['type'] == 'custom_tool_call')
                truncated = bool(re.search(r'(?i)(?:output (?:was )?truncated|original token count|'
                                           r'\[truncated\]|max_output_tokens)', json.dumps(result.get('output'))))
                name = f'pair-{index:03d}.jsonl'
                with (output / name).open('xb') as stream:
                    stream.write(calls[0][1] + results[0][1])
                row.update(disposition='hold' if truncated else 'recorded_pair',
                           reason='truncated_result' if truncated else 'original_scoped_records',
                           file=name, sha256=digest((output / name).read_bytes()),
                           request_sha256=digest(calls[0][1]), result_sha256=digest(results[0][1]),
                           request_line=calls[0][0], result_line=results[0][0],
                           query_count=len(request['search_query']))
            except (RecoveryError, ValueError, KeyError, TypeError) as exc:
                # Fixed categories only; exception messages must never echo source content.
                row['reason'] = 'unsupported_or_ambiguous_receipt'
        dispositions.append(row)
    manifest = {'schema': 'lanes-scoped-session-recovery-v1', 'source_sha256': scope.sha256,
                'session_id': scope.session_id, 'records': dispositions,
                'recorded_pairs': sum(x['disposition'] == 'recorded_pair' for x in dispositions),
                'holds': sum(x['disposition'] == 'hold' for x in dispositions),
                'accounting_verified': False, 'network_allowed': False}
    with (output / 'manifest.json').open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, sort_keys=True, indent=2)
        stream.write('\n')
    return manifest
