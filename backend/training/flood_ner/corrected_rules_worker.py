"""Offline raw-text-only rules subprocess; no reference or development capability."""
from __future__ import annotations

import hashlib
import ast
import importlib.abc
import json
from pathlib import Path, PurePosixPath
import sys


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rules_code_files(root):
    """Resolve application imports including Python's implicit package initializers."""
    root = Path(root)
    backend = root / 'backend'
    pending = ['training.flood_ner.rules_baseline', 'app.services.taglish_extraction_service']
    done, files = set(), {}
    while pending:
        name = pending.pop()
        if name in done:
            continue
        done.add(name)
        base = backend / name.replace('.', '/')
        path = base.with_suffix('.py')
        if not path.is_file():
            path = base / '__init__.py'
        if not path.is_file():
            continue
        files[path.relative_to(root).as_posix()] = digest(path)
        parts = name.split('.')
        for i in range(1, len(parts)):
            pending.append('.'.join(parts[:i]))
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node, ast.Import):
                pending.extend(a.name for a in node.names if a.name.startswith(('app.', 'training.flood_ner.')))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                if node.level:
                    package = parts if path.name == '__init__.py' else parts[:-1]
                    module = '.'.join(package[:len(package) - node.level + 1] + ([module] if module else []))
                if module.startswith(('app.', 'training.flood_ner.')):
                    pending.append(module)
                    pending.extend(module + '.' + a.name for a in node.names if a.name != '*')
    return dict(sorted(files.items()))


def install_guards():
    """Install before any application/SQLAlchemy imports; deny DB drivers too."""
    def audit(event, args):
        if event in {'socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo',
                     'socket.gethostbyname', 'socket.gethostbyaddr', 'socket.sendto',
                     'subprocess.Popen', 'os.system', 'os.posix_spawn'}:
            raise RuntimeError('offline worker: network/process access forbidden')
    sys.addaudithook(audit)
    class NoDatabase(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in {'psycopg', 'psycopg2', 'asyncpg', 'sqlite3', 'pymysql', 'MySQLdb'} or fullname in {'app.database', 'app.db'}:
                raise RuntimeError('offline worker: database access forbidden')
    sys.meta_path.insert(0, NoDatabase())
    # Block SQLAlchemy's public connection entry points if used by dependencies.
    import sqlalchemy
    def forbidden(*args, **kwargs):
        raise RuntimeError('offline worker: database access forbidden')
    class OfflineEngine:
        """Permit import-time engine declarations without constructing a driver."""
        connect = raw_connection = execute = begin = forbidden
    def inert_engine(*args, **kwargs):
        return OfflineEngine()
    sqlalchemy.create_engine = inert_engine
    import sqlalchemy.engine.create
    sqlalchemy.engine.create.create_engine = inert_engine
    from sqlalchemy.engine import Engine, Connection
    Engine.connect = Engine.raw_connection = Connection.execute = forbidden
    from sqlalchemy.orm import Session
    Session.execute = Session.connection = Session.get_bind = forbidden
    try:
        from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection
        AsyncEngine.connect = AsyncEngine.raw_connection = AsyncConnection.execute = forbidden
    except ImportError:
        pass


def checked_request(request):
    require(set(request) == {'schema', 'root', 'runtime', 'files', 'rows'}, 'raw-only rules envelope required')
    require(request['schema'] == 'lanes-corrected-rules-request-v1', 'wrong rules request')
    runtime = request['runtime']
    require(set(runtime) == {'python', 'sha256', 'version'} and runtime['version'] == '3.12.14'
            and sys.version.split()[0] == runtime['version']
            and Path(sys.executable).resolve() == Path(runtime['python']).resolve()
            and digest(sys.executable) == runtime['sha256'], 'rules runtime changed')
    root = Path(request['root']).resolve()
    files = request['files']
    require(isinstance(files, dict) and 'backend/training/flood_ner/corrected_rules_worker.py' in files
            and 'backend/training/flood_ner/rules_baseline.py' in files, 'bound rules code required')
    for name, sha in files.items():
        relative = PurePosixPath(name)
        require(not relative.is_absolute() and '..' not in relative.parts and ':' not in name and '\\' not in name,
                'unsafe rules binding')
        path = root.joinpath(*relative.parts)
        require(path.resolve().is_relative_to(root) and not any(p.is_symlink() or getattr(p, 'is_junction', lambda: False)()
                for p in (path, *path.parents)) and digest(path) == sha, 'rules code/assets changed')
    rows = request['rows']
    require(isinstance(rows, list) and bool(rows) and all(isinstance(r, dict) and set(r) == {'record_id', 'text'}
            and isinstance(r['record_id'], str) and r['record_id'] and isinstance(r['text'], str) and r['text'] for r in rows),
            'rules receive exact raw text and opaque IDs only')
    require(len({r['record_id'] for r in rows}) == len(rows), 'duplicate rules identity')
    return root, rows


def run(request):
    install_guards()
    root, rows = checked_request(request)
    sys.path.insert(0, str(root / 'backend'))
    from training.flood_ner.rules_baseline import predict_mentions, specification
    # The independently recomputed closure must be included in the bound request.
    require(all(request['files'].get(k) == v for k, v in specification(root)['files'].items()), 'incomplete rules closure')
    require(all(request['files'].get(k) == v for k, v in rules_code_files(root).items()), 'incomplete application/package closure')
    predictions = {r['record_id']: [(e['start'], e['end'], e['label']) for e in predict_mentions(r['text'])['spans']] for r in rows}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if path.suffix == '.py' and any(path.is_relative_to(root / 'backend' / package) for package in ('app', 'training')):
                relative = path.relative_to(root).as_posix()
                require(request['files'].get(relative) == digest(path), 'unbound imported application source')
    return {'schema': 'lanes-corrected-rules-response-v1', 'predictions': predictions,
            'python_version': sys.version.split()[0], 'network_database_blocked': True}


def main():
    try:
        request = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
        result = run(request)
        print(json.dumps(result, ensure_ascii=False))
    except BaseException:
        import traceback
        if len(sys.argv) > 1:
            destination = Path(sys.argv[1]).resolve().parent / 'private-failure-traceback.txt'
            with destination.open('x', encoding='utf-8') as stream:
                stream.write(traceback.format_exc())
        # Exceptions may embed candidate content: diagnostics stay generic.
        print(json.dumps({'state': 'failed', 'error': 'rules worker failed'}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
