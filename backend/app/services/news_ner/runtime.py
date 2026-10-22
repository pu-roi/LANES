"""Local Docker controller with owned cleanup and a cross-process lease."""
import asyncio
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import uuid
from typing import BinaryIO, Iterator

from .bundle import digest, verify_bundle
from .contract import IMAGE, MAX_OUTPUT_BYTES, object_sha


class PreviewError(Exception):
    def __init__(self, status: int, code: str) -> None:
        self.status = status
        self.code = code
        super().__init__(code)


@contextmanager
def lease(path: Path, owner: str) -> Iterator[BinaryIO]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        if path.stat().st_size == 0:
            stream.write(b'\0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise PreviewError(429, 'preview_busy') from exc
        try:
            stream.seek(0)
            if stream.read() != b'\0':
                raise PreviewError(503, 'preview_cleanup_unavailable')
            stream.seek(0)
            stream.truncate()
            stream.write(owner.encode('ascii'))
            stream.flush()
            yield stream
        finally:
            if os.name == 'nt':
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


async def command(args: list[str], payload: bytes | None = None, timeout: float = 10) -> tuple[int, bytes, bytes]:
    process = await asyncio.create_subprocess_exec(*args,
        stdin=asyncio.subprocess.PIPE if payload is not None else asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    async def bounded(stream: asyncio.StreamReader, maximum: int) -> bytes:
        chunks = []
        count = 0
        while chunk := await stream.read(65536):
            count += len(chunk)
            if count > maximum:
                raise PreviewError(502, 'preview_worker_failed')
            chunks.append(chunk)
        return b''.join(chunks)

    async def write() -> None:
        if payload is not None:
            try:
                process.stdin.write(payload)
                await process.stdin.drain()
            except (BrokenPipeError, ConnectionResetError):
                pass  # Exit status and response below still reject failure.
            finally:
                process.stdin.close()

    tasks = [asyncio.create_task(bounded(process.stdout, MAX_OUTPUT_BYTES)),
             asyncio.create_task(bounded(process.stderr, 65536)), asyncio.create_task(write())]
    try:
        async with asyncio.timeout(timeout):
            out, err, _ = await asyncio.gather(*tasks)
            return await process.wait(), out, err
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if process.returncode is None:
            process.kill()
        # Drain even if the process already exited: a paused pipe can keep a
        # Windows subprocess transport alive after an output-limit error.
        async def discard(stream: asyncio.StreamReader) -> None:
            while await stream.read(65536):
                pass
        await asyncio.gather(discard(process.stdout), discard(process.stderr))
        await process.wait()


def container_args(docker: str, name: str, bundle: Path, package: Path) -> list[str]:
    args = [docker, 'create', '--name', name, '--interactive', '--label', 'lanes.ner-preview.owner=' + name,
        '--network', 'none', '--cpus', '2', '--memory', '4g', '--memory-swap', '4g',
        '--pids-limit', '128', '--read-only', '--restart=no', '--cap-drop=ALL',
        '--security-opt=no-new-privileges', '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m',
        '--entrypoint', 'python', '--pull=never']
    for source, target in ((bundle, '/assets'), (package, '/code/news_ner')):
        if ',' in str(source):
            raise PreviewError(503, 'preview_runtime_unavailable')
        args += ['--mount', f'type=bind,source={source},target={target},readonly']
    for value in ('PYTHONDONTWRITEBYTECODE=1', 'CUDA_VISIBLE_DEVICES=', 'OMP_NUM_THREADS=1', 'OPENBLAS_NUM_THREADS=1', 'MKL_NUM_THREADS=1'):
        args += ['--env', value]
    return args + [IMAGE, '-I', '-B', '/code/news_ner/worker.py']


async def run_local(raw: dict, bundle: Path, bundle_sha: str, docker: str) -> dict:
    package = Path(__file__).resolve().parent
    lock = Path(__file__).resolve().parents[3] / 'runtime_data/ner_preview/owner.lock'
    name = 'lanes-ner-preview-' + uuid.uuid4().hex
    try:
        verify_bundle(bundle, bundle_sha)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PreviewError(503, 'preview_assets_unavailable') from exc
    code = {p.name: digest(p) for p in package.iterdir() if p.is_file() and p.suffix == '.py'}
    code['promotion.json'] = digest(package / 'promotion.json')
    payload = json.dumps({**raw, 'bundle_sha256': bundle_sha, 'code': code}, ensure_ascii=False).encode('utf-8')
    with lease(lock, name) as owner:
        container_id: str | None = None
        try:
            async with asyncio.timeout(90):
                rc, image, _ = await command([docker, 'image', 'inspect', IMAGE, '--format', '{{.Id}} {{.Os}} {{.Architecture}}'])
                if rc or image.decode().strip() != IMAGE + ' linux amd64':
                    raise PreviewError(503, 'preview_runtime_unavailable')
                rc, output, _ = await command(container_args(docker, name, bundle, package))
                if rc or not re.fullmatch(rb'[a-f0-9]{64}\s*', output):
                    raise PreviewError(503, 'preview_runtime_unavailable')
                container_id = output.decode('ascii').strip()
                rc, output, _ = await command([docker, 'start', '--attach', '--interactive', name], payload, timeout=90)
                if rc:
                    raise PreviewError(502, 'preview_worker_failed')
                value = json.loads(output)
                if value.get('provenance', {}).get('code_sha256') != object_sha(code):
                    raise PreviewError(502, 'preview_worker_failed')
                return value
        except TimeoutError as exc:
            raise PreviewError(504, 'preview_timeout') from exc
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise PreviewError(502, 'preview_worker_failed') from exc
        finally:
            # Finish cleanup even when the HTTP task was cancelled. A poisoned
            # lease remains on disk unless removal is positively verified.
            async def cleanup() -> None:
                target = container_id or name
                rc, state, _ = await command([docker, 'inspect', '--format', '{{json .Config.Labels}}', target])
                if rc:
                    # A failed inspect cannot prove absence, so query names.
                    rc, names, _ = await command([docker, 'ps', '-a', '--filter', 'name=^/' + name + '$', '--format', '{{.Names}}'])
                    if rc or names.strip():
                        raise PreviewError(503, 'preview_cleanup_unavailable')
                else:
                    if json.loads(state).get('lanes.ner-preview.owner') != name:
                        raise PreviewError(503, 'preview_cleanup_unavailable')
                    rc, _, _ = await command([docker, 'rm', '--force', target])
                    if rc:
                        raise PreviewError(503, 'preview_cleanup_unavailable')
                    rc, names, _ = await command([docker, 'ps', '-a', '--filter', 'name=^/' + name + '$', '--format', '{{.Names}}'])
                    if rc or names.strip():
                        raise PreviewError(503, 'preview_cleanup_unavailable')
                owner.seek(0)
                owner.truncate()
                owner.write(b'\0')
                owner.flush()
            async def bounded_cleanup() -> None:
                async with asyncio.timeout(10):
                    await cleanup()
            task = asyncio.create_task(bounded_cleanup())
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                await task
                raise
            except (OSError, ValueError, TimeoutError) as exc:
                raise PreviewError(503, 'preview_cleanup_unavailable') from exc
